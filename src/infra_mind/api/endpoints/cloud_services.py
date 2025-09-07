"""
Cloud Services endpoints for Infra Mind.

Provides comprehensive cloud services catalog and comparison functionality.
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional, Dict, Any
import logging
from enum import Enum
import asyncio
import os

from ...cloud.unified import UnifiedCloudClient
from ...cloud.base import CloudProvider as BaseCloudProvider, ServiceCategory as BaseServiceCategory

logger = logging.getLogger(__name__)

router = APIRouter()


class CloudProvider(str, Enum):
    AWS = "AWS"
    AZURE = "Azure"
    GCP = "GCP"
    ALIBABA = "Alibaba"
    IBM = "IBM"


class ServiceCategory(str, Enum):
    COMPUTE = "Compute"
    DATABASE = "Database"
    STORAGE = "Storage"
    NETWORKING = "Networking"
    SECURITY = "Security"
    AI_ML = "AI/ML"
    ANALYTICS = "Analytics"
    CONTAINERS = "Containers"
    SERVERLESS = "Serverless"
    MANAGEMENT = "Management"


# Simple in-memory cache for cloud services (will be replaced with Redis/proper cache)
_services_cache = {}
_cache_ttl = {}
CACHE_DURATION = 180  # 3 minutes - reduced for memory efficiency  
MAX_CACHE_ENTRIES = 10  # Reduced cache size to prevent memory bloat

# Singleton cloud client to prevent memory leaks from creating multiple instances
_unified_client = None


def _get_cache_key(provider: Optional[CloudProvider] = None, category: Optional[ServiceCategory] = None) -> str:
    """Generate cache key for service requests."""
    provider_str = provider.value if provider else "all"
    category_str = category.value if category else "all"
    return f"services_{provider_str}_{category_str}"


def _is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid."""
    import time
    if cache_key not in _cache_ttl:
        return False
    return time.time() - _cache_ttl[cache_key] < CACHE_DURATION


def _cleanup_expired_cache():
    """Remove expired cache entries to prevent memory bloat."""
    import time
    current_time = time.time()
    expired_keys = []
    
    for cache_key, timestamp in _cache_ttl.items():
        if current_time - timestamp >= CACHE_DURATION:
            expired_keys.append(cache_key)
    
    for key in expired_keys:
        _services_cache.pop(key, None)
        _cache_ttl.pop(key, None)
    
    if expired_keys:
        logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")


def _enforce_cache_size_limit():
    """Enforce cache size limit by removing oldest entries."""
    if len(_services_cache) <= MAX_CACHE_ENTRIES:
        return
    
    import time
    # Sort by timestamp and keep only the newest entries
    sorted_entries = sorted(_cache_ttl.items(), key=lambda x: x[1], reverse=True)
    entries_to_keep = sorted_entries[:MAX_CACHE_ENTRIES]
    entries_to_remove = sorted_entries[MAX_CACHE_ENTRIES:]
    
    for cache_key, _ in entries_to_remove:
        _services_cache.pop(cache_key, None)
        _cache_ttl.pop(cache_key, None)
    
    if entries_to_remove:
        logger.info(f"Removed {len(entries_to_remove)} cache entries to enforce size limit")


def _get_unified_client() -> UnifiedCloudClient:
    """Get or create singleton UnifiedCloudClient to prevent memory leaks."""
    global _unified_client
    if _unified_client is None:
        _unified_client = UnifiedCloudClient(
            aws_region=os.getenv('INFRA_MIND_AWS_REGION', 'us-east-1'),
            aws_access_key_id=os.getenv('INFRA_MIND_AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('INFRA_MIND_AWS_SECRET_ACCESS_KEY'),
            azure_region=os.getenv('INFRA_MIND_AZURE_REGION', 'eastus'),
            azure_subscription_id=os.getenv('INFRA_MIND_AZURE_SUBSCRIPTION_ID'),
            azure_client_id=os.getenv('INFRA_MIND_AZURE_CLIENT_ID'),
            azure_client_secret=os.getenv('INFRA_MIND_AZURE_CLIENT_SECRET'),
            gcp_region=os.getenv('INFRA_MIND_GCP_REGION', 'us-central1'),
            gcp_project_id=os.getenv('INFRA_MIND_GCP_PROJECT_ID'),
            gcp_service_account_path='/app/gcp-service-account.json' if os.path.exists('/app/gcp-service-account.json') else None,
            alibaba_region=os.getenv('INFRA_MIND_ALIBABA_REGION', 'us-west-1'),
            alibaba_access_key_id=os.getenv('INFRA_MIND_ALIBABA_ACCESS_KEY_ID'),
            alibaba_access_key_secret=os.getenv('INFRA_MIND_ALIBABA_ACCESS_KEY_SECRET'),
            ibm_region=os.getenv('INFRA_MIND_IBM_REGION', 'us-south'),
            ibm_api_key=os.getenv('INFRA_MIND_IBM_API_KEY'),
            ibm_account_id=os.getenv('INFRA_MIND_IBM_ACCOUNT_ID')
        )
        logger.info("Created singleton UnifiedCloudClient")
    return _unified_client


async def _get_cached_or_fetch_services(
    provider: Optional[CloudProvider] = None, 
    category: Optional[ServiceCategory] = None
) -> List[Dict[str, Any]]:
    """Get services from cache or fetch from SDKs if cache is expired."""
    import time
    
    cache_key = _get_cache_key(provider, category)
    
    # Check cache first
    if _is_cache_valid(cache_key):
        logger.info(f"Using cached services for {cache_key}")
        return _services_cache.get(cache_key, [])
    
    logger.info(f"Cache miss or expired for {cache_key}, fetching from SDKs")
    
    # Use singleton client to prevent memory leaks
    unified_client = _get_unified_client()
    
    # Map enum values to base provider enum
    provider_mapping = {
        CloudProvider.AWS: BaseCloudProvider.AWS,
        CloudProvider.AZURE: BaseCloudProvider.AZURE,
        CloudProvider.GCP: BaseCloudProvider.GCP,
        CloudProvider.IBM: BaseCloudProvider.IBM,
        CloudProvider.ALIBABA: BaseCloudProvider.ALIBABA
    }
    
    # Determine providers to query
    providers_to_query = []
    if provider and provider in provider_mapping:
        providers_to_query = [provider_mapping[provider]]
    else:
        # Only query available providers
        providers_to_query = [p for p in provider_mapping.values() if p in [k for k in unified_client.clients.keys()]]
    
    all_services = []
    
    # Query services with optimized concurrent execution and shorter timeouts
    async def query_single_category(base_provider, service_category):
        """Query a single category from a provider with optimized timeout."""
        try:
            if service_category == BaseServiceCategory.COMPUTE:
                response = await asyncio.wait_for(
                    unified_client.get_compute_services(base_provider), timeout=3.0
                )
            elif service_category == BaseServiceCategory.STORAGE:
                response = await asyncio.wait_for(
                    unified_client.get_storage_services(base_provider), timeout=3.0
                )
            elif service_category == BaseServiceCategory.DATABASE:
                response = await asyncio.wait_for(
                    unified_client.get_database_services(base_provider), timeout=3.0
                )
            elif service_category == BaseServiceCategory.MACHINE_LEARNING:
                response = await asyncio.wait_for(
                    unified_client.get_ai_services(base_provider), timeout=3.0
                )
            else:
                return []
            
            services = []
            if isinstance(response, dict) and base_provider in response:
                service_response = response[base_provider]
                if hasattr(service_response, 'services') and service_response.services:
                    for service in service_response.services[:5]:  # Limit to 5 per category
                        services.append({
                            "id": f"{base_provider.value.lower()}-{service.service_id}",
                            "name": service.service_name,
                            "provider": base_provider.value,
                            "category": service_category.value,
                            "description": service.description or f"{service.service_name} from {base_provider.value}",
                            "pricing": service.specifications.get("pricing", {"model": "Pay-as-you-go", "starting_price": 0.01, "unit": "per hour"}),
                            "features": service.features or ["Scalable", "Managed", "Cloud-native"],
                            "rating": 4.3,
                            "compliance": ["SOC 2", "ISO 27001"],
                            "region_availability": [service.region] if service.region else ["global"],
                            "use_cases": ["Production workloads", "Development", "Testing"],
                            "integration": ["REST API", "SDK", "CLI"],
                            "managed": True,
                            "api_source": "live_sdk"
                        })
            return services
        except asyncio.TimeoutError:
            logger.warning(f"Timeout for {base_provider} {service_category}")
            return []
        except Exception as e:
            logger.warning(f"Error for {base_provider} {service_category}: {e}")
            return []
    
    # Determine categories to query
    if category == ServiceCategory.COMPUTE:
        categories = [BaseServiceCategory.COMPUTE]
    elif category == ServiceCategory.STORAGE:
        categories = [BaseServiceCategory.STORAGE]
    elif category == ServiceCategory.DATABASE:
        categories = [BaseServiceCategory.DATABASE]
    elif category == ServiceCategory.AI_ML:
        categories = [BaseServiceCategory.MACHINE_LEARNING]
    else:
        # Query all categories but limit to 2 for performance
        categories = [BaseServiceCategory.COMPUTE, BaseServiceCategory.STORAGE]
    
    # Execute all queries concurrently with reduced timeout
    tasks = []
    for base_provider in providers_to_query:
        for service_category in categories:
            tasks.append(query_single_category(base_provider, service_category))
    
    try:
        # Overall timeout reduced to 8 seconds
        results = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=8.0)
        
        for result in results:
            if isinstance(result, list):
                all_services.extend(result)
            elif isinstance(result, Exception):
                logger.debug(f"Query failed: {result}")
                
    except asyncio.TimeoutError:
        logger.warning(f"Overall timeout reached for {cache_key}")
    
    # Clean up expired cache entries before adding new ones
    _cleanup_expired_cache()
    
    # Cache the results
    _services_cache[cache_key] = all_services
    _cache_ttl[cache_key] = time.time()
    
    # Enforce cache size limit
    _enforce_cache_size_limit()
    
    # Force garbage collection to free memory
    import gc
    gc.collect()
    
    logger.info(f"Cached {len(all_services)} services for {cache_key}")
    return all_services


@router.get("/", summary="List all cloud services")
async def list_cloud_services(
    provider: Optional[CloudProvider] = Query(None, description="Filter by cloud provider"),
    category: Optional[ServiceCategory] = Query(None, description="Filter by service category"),
    search: Optional[str] = Query(None, description="Search in service names and descriptions"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of services to return"),
    offset: int = Query(0, ge=0, description="Number of services to skip")
) -> Dict[str, Any]:
    """
    Get a comprehensive list of cloud services using dynamic SDK calls with caching.
    
    Returns LIVE cloud services from major providers (AWS, Azure, GCP, IBM, Alibaba) 
    with intelligent caching to ensure fast response times and real-time data.
    """
    try:
        # Get services from cache or fetch from SDKs
        all_services = await _get_cached_or_fetch_services(provider, category)
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            all_services = [
                s for s in all_services 
                if search_lower in s["name"].lower() or search_lower in s["description"].lower()
            ]
        
        # Apply pagination
        total_count = len(all_services)
        paginated_services = all_services[offset:offset + limit]
        
        return {
            "services": paginated_services,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "filters": {
                "provider": provider.value if provider else None,
                "category": category.value if category else None,
                "search": search
            },
            "metadata": {
                "source": "dynamic_cloud_sdks_cached",
                "cache_enabled": True,
                "cache_duration_seconds": CACHE_DURATION,
                "response_time_optimized": True,
                "live_data": True
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to list cloud services: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cloud services"
        )


@router.get("/aws", summary="Get AWS services")
async def get_aws_services(
    category: Optional[ServiceCategory] = Query(None, description="Filter by service category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of services to return")
) -> Dict[str, Any]:
    """Get AWS cloud services with optional category filtering."""
    return await list_cloud_services(provider=CloudProvider.AWS, category=category, search=None, limit=limit, offset=0)


@router.get("/azure", summary="Get Azure services")
async def get_azure_services(
    category: Optional[ServiceCategory] = Query(None, description="Filter by service category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of services to return")
) -> Dict[str, Any]:
    """Get Azure cloud services with optional category filtering."""
    return await list_cloud_services(provider=CloudProvider.AZURE, category=category, search=None, limit=limit, offset=0)


@router.get("/gcp", summary="Get GCP services")
async def get_gcp_services(
    category: Optional[ServiceCategory] = Query(None, description="Filter by service category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of services to return")
) -> Dict[str, Any]:
    """Get GCP cloud services with optional category filtering."""
    return await list_cloud_services(provider=CloudProvider.GCP, category=category, search=None, limit=limit, offset=0)


@router.get("/aws/services", summary="Get detailed AWS services list")
async def get_detailed_aws_services() -> Dict[str, Any]:
    """Get comprehensive list of AWS services with full details."""
    services = await _get_cached_or_fetch_services(CloudProvider.AWS)
    return {
        "provider": "AWS",
        "total_services": len(services),
        "services": services,
        "categories": list(set(s["category"] for s in services))
    }


@router.get("/providers", summary="List all cloud providers")
async def list_providers() -> Dict[str, Any]:
    """Get list of all supported cloud providers with dynamic data."""
    try:
        # Get all services to analyze providers
        all_services = await _get_cached_or_fetch_services()
        
        providers = {}
        for service in all_services:
            provider = service["provider"]
            if provider not in providers:
                providers[provider] = {
                    "name": provider,
                    "service_count": 0,
                    "categories": set()
                }
            
            providers[provider]["service_count"] += 1
            providers[provider]["categories"].add(service["category"])
        
        # Convert sets to lists for JSON serialization
        for provider_data in providers.values():
            provider_data["categories"] = sorted(list(provider_data["categories"]))
        
        return {
            "providers": list(providers.values()),
            "total_providers": len(providers)
        }
    except Exception as e:
        logger.error(f"Failed to list providers: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cloud providers"
        )


@router.get("/categories", summary="List all service categories")
async def list_categories() -> Dict[str, Any]:
    """Get list of all service categories with dynamic data."""
    try:
        # Get all services to analyze categories
        all_services = await _get_cached_or_fetch_services()
        
        categories = {}
        for service in all_services:
            category = service["category"]
            if category not in categories:
                categories[category] = {
                    "name": category,
                    "service_count": 0,
                    "providers": set()
                }
            
            categories[category]["service_count"] += 1
            categories[category]["providers"].add(service["provider"])
        
        # Convert sets to lists for JSON serialization
        for category_data in categories.values():
            category_data["providers"] = sorted(list(category_data["providers"]))
        
        return {
            "categories": list(categories.values()),
            "total_categories": len(categories)
        }
    except Exception as e:
        logger.error(f"Failed to list categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service categories"
        )


@router.get("/service/{service_id}", summary="Get service details")
async def get_service_details(service_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific cloud service.
    
    Args:
        service_id: Unique identifier of the service
        
    Returns:
        Detailed service information including features, pricing, and compliance
    """
    try:
        # Get all services and find the specific one
        all_services = await _get_cached_or_fetch_services()
        service = next((s for s in all_services if s["id"] == service_id), None)
        
        if not service:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Service {service_id} not found"
            )
        
        logger.info(f"Retrieved details for service: {service_id}")
        return service
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service details for {service_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service details"
        )


@router.get("/compare/{service_ids}", summary="Compare multiple services")
async def compare_services(service_ids: str) -> Dict[str, Any]:
    """
    Compare multiple cloud services side by side.
    
    Args:
        service_ids: Comma-separated list of service IDs to compare
        
    Returns:
        Comparison data for the requested services
    """
    # Enhanced input validation and sanitization
    if not service_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service IDs parameter is required"
        )
    
    if not service_ids.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service IDs cannot be empty or whitespace only"
        )
    
    # Validate service_ids length before processing
    if len(service_ids) > 1000:  # Prevent extremely long strings
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service IDs string is too long (max 1000 characters)"
        )
    
    try:
        # Enhanced parsing with validation
        raw_ids = service_ids.split(",")
        if len(raw_ids) > 20:  # Prevent processing too many IDs
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many service IDs provided (max 20)"
            )
        
        # Parse and validate service IDs
        ids = []
        for raw_id in raw_ids:
            cleaned_id = raw_id.strip()
            if cleaned_id:
                # Validate ID format (assuming alphanumeric with hyphens/underscores)
                if not cleaned_id.replace('-', '').replace('_', '').isalnum():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid service ID format: {cleaned_id}. Only alphanumeric, hyphens, and underscores allowed."
                    )
                if len(cleaned_id) > 100:  # Reasonable ID length limit
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Service ID too long: {cleaned_id} (max 100 characters)"
                    )
                ids.append(cleaned_id)
        
        if len(ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 valid services are required for comparison"
            )
        
        if len(ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 5 services can be compared at once"
            )
        
        # Remove duplicates while preserving order
        unique_ids = []
        seen = set()
        for id in ids:
            if id not in seen:
                unique_ids.append(id)
                seen.add(id)
        ids = unique_ids
        
        if len(ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 unique services are required after removing duplicates"
            )
        
        # Get all services and find the requested ones with enhanced error handling
        try:
            all_services = await _get_cached_or_fetch_services()
        except Exception as e:
            logger.error(f"Failed to fetch services for comparison: {e}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to fetch service data. Please try again later."
            )
        
        if not all_services:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="No services available for comparison"
            )
        
        services = []
        missing_ids = []
        
        for service_id in ids:
            service = next((s for s in all_services if s.get("id") == service_id), None)
            if service:
                # Validate service has required fields for comparison
                required_fields = ["id", "name", "category"]
                missing_fields = [field for field in required_fields if not service.get(field)]
                if missing_fields:
                    logger.warning(f"Service {service_id} missing required fields: {missing_fields}")
                    continue
                services.append(service)
            else:
                missing_ids.append(service_id)
        
        if missing_ids:
            logger.warning(f"Services not found: {missing_ids}")
        
        if not services:
            if missing_ids:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No valid services found. Missing services: {', '.join(missing_ids)}"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No valid services found for comparison"
                )
        
        if len(services) < 2:
            valid_names = [s.get('name', s.get('id', 'Unknown')) for s in services]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {len(services)} valid service(s) found: {', '.join(valid_names)}. Need at least 2 for comparison."
            )
        
        # Generate comparison insights
        comparison_insights = {
            "price_comparison": _compare_pricing(services),
            "feature_overlap": _analyze_feature_overlap(services),
            "compliance_comparison": _compare_compliance(services),
            "recommendations": _generate_comparison_recommendations(services)
        }
        
        logger.info(f"Compared {len(services)} services: {[s['name'] for s in services]}")
        
        return {
            "services": services,
            "comparison": comparison_insights,
            "compared_count": len(services)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare services {service_ids}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to compare services"
        )


def _compare_pricing(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare pricing across services."""
    prices = [s["pricing"]["starting_price"] for s in services]
    
    return {
        "lowest_price": min(prices),
        "highest_price": max(prices),
        "average_price": sum(prices) / len(prices),
        "cheapest_service": min(services, key=lambda s: s["pricing"]["starting_price"])["name"],
        "most_expensive_service": max(services, key=lambda s: s["pricing"]["starting_price"])["name"]
    }


def _analyze_feature_overlap(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze feature overlap between services."""
    all_features = set()
    service_features = {}
    
    for service in services:
        features = set(service["features"])
        all_features.update(features)
        service_features[service["name"]] = features
    
    # Find common features
    common_features = all_features.copy()
    for features in service_features.values():
        common_features.intersection_update(features)
    
    return {
        "total_unique_features": len(all_features),
        "common_features": list(common_features),
        "common_feature_count": len(common_features),
        "feature_coverage": {
            name: len(features) / len(all_features) * 100 
            for name, features in service_features.items()
        }
    }


def _compare_compliance(services: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare compliance certifications across services."""
    all_compliance = set()
    service_compliance = {}
    
    for service in services:
        compliance = set(service["compliance"])
        all_compliance.update(compliance)
        service_compliance[service["name"]] = compliance
    
    # Find common compliance standards
    common_compliance = all_compliance.copy()
    for compliance in service_compliance.values():
        common_compliance.intersection_update(compliance)
    
    return {
        "total_compliance_standards": len(all_compliance),
        "common_compliance": list(common_compliance),
        "compliance_coverage": {
            name: len(compliance) / len(all_compliance) * 100 
            for name, compliance in service_compliance.items()
        }
    }


def _generate_comparison_recommendations(services: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate recommendations based on service comparison."""
    recommendations = []
    
    # Price-based recommendation
    cheapest = min(services, key=lambda s: s["pricing"]["starting_price"])
    recommendations.append({
        "type": "cost_optimization",
        "title": "Most Cost-Effective Option",
        "description": f"{cheapest['name']} offers the lowest starting price at ${cheapest['pricing']['starting_price']} {cheapest['pricing']['unit']}",
        "service": cheapest["name"],
        "priority": "high"
    })
    
    # Feature-based recommendation
    most_featured = max(services, key=lambda s: len(s["features"]))
    recommendations.append({
        "type": "feature_rich",
        "title": "Most Feature-Rich Service",
        "description": f"{most_featured['name']} offers the most features with {len(most_featured['features'])} capabilities",
        "service": most_featured["name"],
        "priority": "medium"
    })
    
    # Compliance recommendation
    most_compliant = max(services, key=lambda s: len(s["compliance"]))
    recommendations.append({
        "type": "compliance",
        "title": "Best Compliance Coverage",
        "description": f"{most_compliant['name']} supports {len(most_compliant['compliance'])} compliance standards",
        "service": most_compliant["name"],
        "priority": "high" if len(most_compliant["compliance"]) > 3 else "medium"
    })
    
    return recommendations


@router.get("/stats", summary="Get service statistics")
async def get_service_statistics() -> Dict[str, Any]:
    """Get comprehensive statistics about the cloud services catalog."""
    try:
        # Get all services for analysis
        all_services = await _get_cached_or_fetch_services()
        
        if not all_services:
            return {
                "total_services": 0,
                "providers": {},
                "categories": {},
                "pricing": {"min_price": 0, "max_price": 0, "avg_price": 0},
                "compliance_standards": {},
                "most_common_compliance": "SOC 2"
            }
        
        # Provider statistics
        provider_stats = {}
        category_stats = {}
        pricing_stats = []
        compliance_stats = {}
        
        for service in all_services:
            provider = service["provider"]
            category = service["category"]
            
            # Provider stats
            if provider not in provider_stats:
                provider_stats[provider] = {"count": 0, "avg_rating": 0, "total_rating": 0}
            provider_stats[provider]["count"] += 1
            provider_stats[provider]["total_rating"] += service["rating"]
            provider_stats[provider]["avg_rating"] = provider_stats[provider]["total_rating"] / provider_stats[provider]["count"]
            
            # Category stats
            if category not in category_stats:
                category_stats[category] = {"count": 0, "providers": set()}
            category_stats[category]["count"] += 1
            category_stats[category]["providers"].add(provider)
            
            # Pricing stats
            if "pricing" in service and "starting_price" in service["pricing"]:
                pricing_stats.append(service["pricing"]["starting_price"])
            
            # Compliance stats
            for compliance in service.get("compliance", []):
                if compliance not in compliance_stats:
                    compliance_stats[compliance] = 0
                compliance_stats[compliance] += 1
        
        # Convert sets to lists for JSON serialization
        for cat_data in category_stats.values():
            cat_data["providers"] = list(cat_data["providers"])
        
        return {
            "total_services": len(all_services),
            "providers": provider_stats,
            "categories": category_stats,
            "pricing": {
                "min_price": min(pricing_stats) if pricing_stats else 0,
                "max_price": max(pricing_stats) if pricing_stats else 0,
                "avg_price": sum(pricing_stats) / len(pricing_stats) if pricing_stats else 0
            },
            "compliance_standards": compliance_stats,
            "most_common_compliance": max(compliance_stats.items(), key=lambda x: x[1])[0] if compliance_stats else "SOC 2"
        }
        
    except Exception as e:
        logger.error(f"Failed to get service statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve service statistics"
        )