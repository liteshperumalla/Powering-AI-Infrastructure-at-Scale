#!/usr/bin/env python3
"""
Debug script to examine assessment data persistence issue.
"""

import asyncio
import aiohttp
import json

# Use the token from registration
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGE3YzNkNzgzODViMDA2NTU1YWJhOTgiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJmdWxsX25hbWUiOiJUZXN0IFVzZXIiLCJleHAiOjE3NTU4MjY5MTEsImlhdCI6MTc1NTgyNTExMSwiaXNzIjoiaW5mcmEtbWluZCIsImF1ZCI6ImluZnJhLW1pbmQtYXBpIiwidG9rZW5fdHlwZSI6ImFjY2VzcyIsImp0aSI6Im9TN2hjQVVnQWdiSUs1NjVBLWduYnp1MDBZMWRfY2ZsenMwWFg1UmNhRzQifQ.S-kqxj7Igm9UFTfuo8yqRJLKx5gFLSLWB_EV0QyDqc8"

# Simple test data with enhanced fields explicitly in business_requirements
DEBUG_ASSESSMENT_DATA = {
    "title": "Debug Enhanced Fields Test",
    "description": "Testing enhanced field persistence specifically",
    "business_goal": "Debug enhanced fields storage",
    "business_requirements": {
        # Core fields
        "company_size": "medium",
        "industry": "technology",
        
        # Enhanced fields - explicitly in business_requirements
        "company_name": "TestCorp Enhanced",
        "geographic_regions": ["North America", "Europe"],
        "customer_base_size": "enterprise",
        "revenue_model": "subscription",
        "growth_stage": "series-b",
        "key_competitors": "TestCompetitor1, TestCompetitor2",
        "mission_critical_systems": ["System1", "System2", "System3"],
        
        # Other standard fields
        "business_goals": ["scalability", "cost_optimization"],
        "compliance_requirements": ["SOC2", "GDPR"]
    },
    "technical_requirements": {
        # Core fields
        "workload_types": ["web_application", "machine_learning"],
        
        # Enhanced fields - explicitly in technical_requirements
        "current_cloud_providers": ["AWS", "Google Cloud"],
        "current_services": ["EC2", "RDS", "GKE"],
        "technical_team_size": 15,
        "infrastructure_age": "recent",
        "current_architecture": "microservices",
        "ai_use_cases": ["NLP", "Computer Vision"],
        "current_ai_maturity": "advanced",
        "expected_data_volume": "100TB",
        "data_types": ["Text", "Images"],
        "current_user_load": "50000_concurrent",
        "expected_growth_rate": "100%_annually",
        "budget_flexibility": "high",
        "total_budget_range": "500k_1m"
    },
    "priority": "high",
    "tags": ["debug_test", "enhanced_fields"],
    "source": "debug_enhanced_form"
}

async def debug_assessment_creation():
    """Create assessment and examine what gets stored."""
    print("🔍 DEBUGGING ENHANCED FIELD PERSISTENCE")
    print("=" * 60)
    
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    base_url = "http://localhost:8000"
    
    async with aiohttp.ClientSession() as session:
        print("📤 STEP 1: Sending assessment data...")
        print(f"📊 Business Requirements Keys: {list(DEBUG_ASSESSMENT_DATA['business_requirements'].keys())}")
        print(f"🏗️  Technical Requirements Keys: {list(DEBUG_ASSESSMENT_DATA['technical_requirements'].keys())}")
        print(f"📝 Company Name in Payload: {DEBUG_ASSESSMENT_DATA['business_requirements'].get('company_name')}")
        print(f"🌍 Geographic Regions in Payload: {DEBUG_ASSESSMENT_DATA['business_requirements'].get('geographic_regions')}")
        
        try:
            async with session.post(
                f"{base_url}/api/v1/assessments/",
                json=DEBUG_ASSESSMENT_DATA,
                headers=headers
            ) as response:
                
                if response.status == 201:
                    assessment_data = await response.json()
                    assessment_id = assessment_data.get("id")
                    
                    print(f"\n✅ Assessment Created: {assessment_id}")
                    
                    # Immediately retrieve it
                    print(f"\n📥 STEP 2: Retrieving assessment data...")
                    
                    async with session.get(
                        f"{base_url}/api/v1/assessments/{assessment_id}",
                        headers=headers
                    ) as get_response:
                        
                        if get_response.status == 200:
                            retrieved_data = await get_response.json()
                            
                            print(f"\n📊 RETRIEVED BUSINESS REQUIREMENTS:")
                            bus_req = retrieved_data.get('business_requirements', {})
                            print(f"   Keys: {list(bus_req.keys())}")
                            
                            # Check for enhanced fields
                            enhanced_business_fields = [
                                'company_name', 'geographic_regions', 'customer_base_size',
                                'revenue_model', 'growth_stage', 'key_competitors', 'mission_critical_systems'
                            ]
                            
                            for field in enhanced_business_fields:
                                value = bus_req.get(field, 'MISSING')
                                print(f"   {field}: {value}")
                            
                            print(f"\n🏗️  RETRIEVED TECHNICAL REQUIREMENTS:")
                            tech_req = retrieved_data.get('technical_requirements', {})
                            print(f"   Keys: {list(tech_req.keys())}")
                            
                            # Check for enhanced fields
                            enhanced_technical_fields = [
                                'current_cloud_providers', 'current_services', 'technical_team_size',
                                'infrastructure_age', 'current_architecture', 'ai_use_cases',
                                'current_ai_maturity', 'expected_data_volume', 'current_user_load',
                                'budget_flexibility', 'total_budget_range'
                            ]
                            
                            for field in enhanced_technical_fields:
                                value = tech_req.get(field, 'MISSING')
                                print(f"   {field}: {value}")
                            
                            # Raw JSON dump for analysis
                            print(f"\n📄 RAW BUSINESS_REQUIREMENTS JSON:")
                            print(json.dumps(bus_req, indent=2))
                            
                            return assessment_id
                        
                        else:
                            print(f"❌ Failed to retrieve: {get_response.status}")
                            error_text = await get_response.text()
                            print(f"Error: {error_text}")
                            return None
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create assessment: {response.status}")
                    print(f"Error: {error_text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

async def main():
    """Main debug function."""
    assessment_id = await debug_assessment_creation()
    
    print(f"\n" + "=" * 60)
    if assessment_id:
        print(f"✅ Debug complete - Assessment ID: {assessment_id}")
        print(f"🔗 Check API docs: http://localhost:8000/docs")
    else:
        print(f"❌ Debug failed - check logs above")

if __name__ == "__main__":
    asyncio.run(main())