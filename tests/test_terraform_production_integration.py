"""
Production integration tests for Terraform API integration.

These tests work with real Terraform Cloud and Registry APIs to verify
production-ready functionality. They require valid credentials and can
create/delete real resources in development workspaces.

Environment Variables Required:
    INFRA_MIND_TERRAFORM_TOKEN: Terraform Cloud API token
    INFRA_MIND_TERRAFORM_ORG: Terraform Cloud organization name

Usage:
    # Run with real credentials (development only)
    export INFRA_MIND_TERRAFORM_TOKEN="your-token"
    export INFRA_MIND_TERRAFORM_ORG="your-org"
    python -m pytest tests/test_terraform_production_integration.py -v
"""

import pytest
import asyncio
import os
import time
from datetime import datetime
from typing import Dict, Any, List

from src.infra_mind.cloud.terraform import (
    TerraformClient, TerraformCloudClient, TerraformRegistryClient
)
from src.infra_mind.cloud.base import (
    CloudProvider, ServiceCategory, CloudServiceError,
    AuthenticationError, RateLimitError
)


class TestTerraformRegistryProduction:
    """Test Terraform Registry API with real API calls."""
    
    @pytest.fixture
    def registry_client(self):
        """Create a real Terraform Registry client."""
        return TerraformRegistryClient()
    
    @pytest.mark.asyncio
    async def test_get_real_providers(self, registry_client):
        """Test getting real providers from Terraform Registry."""
        try:
            result = await registry_client.get_providers(limit=10)
            
            assert "providers" in result
            assert result["total_count"] > 0
            assert len(result["providers"]) <= 10
            
            # Verify provider structure
            for provider in result["providers"]:
                assert "namespace" in provider
                assert "name" in provider
                assert "full_name" in provider
                assert "downloads" in provider
                assert isinstance(provider["downloads"], int)
                
            print(f"✅ Retrieved {result['total_count']} providers from registry")
            
        except RateLimitError:
            pytest.skip("Registry API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"Registry API test failed: {e}")
        finally:
            await registry_client.close()
    
    @pytest.mark.asyncio
    async def test_get_hashicorp_providers(self, registry_client):
        """Test getting HashiCorp providers with detailed information."""
        try:
            result = await registry_client.get_providers(namespace="hashicorp")
            
            assert "providers" in result
            assert result["namespace"] == "hashicorp"
            
            # Look for any HashiCorp providers (the specific ones may not be in namespace response)
            provider_names = [p["name"] for p in result["providers"]]
            
            # Just verify we got some providers from HashiCorp namespace
            assert len(provider_names) > 0, "Expected to find some HashiCorp providers"
            
            # Verify they're all from hashicorp namespace
            for provider in result["providers"]:
                assert provider["namespace"] == "hashicorp", f"Expected hashicorp namespace, got {provider['namespace']}"
            
            # Check for version information in detailed providers
            for provider in result["providers"]:
                if provider.get("versions"):
                    assert isinstance(provider["versions"], list)
                    if provider["versions"]:
                        assert "version" in provider["versions"][0]
                        
            print(f"✅ Retrieved {len(result['providers'])} HashiCorp providers")
            
        except RateLimitError:
            pytest.skip("Registry API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"HashiCorp providers test failed: {e}")
        finally:
            await registry_client.close()
    
    @pytest.mark.asyncio
    async def test_get_aws_modules(self, registry_client):
        """Test getting AWS modules with enhanced filtering."""
        try:
            result = await registry_client.get_modules(
                provider="aws", 
                limit=20, 
                verified_only=True
            )
            
            assert "modules" in result
            assert result["provider"] == "aws"
            assert result["verified_only"] is True
            
            # Verify all returned modules are verified
            for module in result["modules"]:
                assert module["verified"] is True
                assert module["provider"] == "aws"
                assert "category" in module
                assert "popularity_score" in module
                assert isinstance(module["popularity_score"], float)
                
            print(f"✅ Retrieved {len(result['modules'])} verified AWS modules")
            
        except RateLimitError:
            pytest.skip("Registry API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"AWS modules test failed: {e}")
        finally:
            await registry_client.close()
    
    @pytest.mark.asyncio
    async def test_get_compute_modules_real(self, registry_client):
        """Test getting real compute modules across providers."""
        try:
            result = await registry_client.get_compute_modules()
            
            assert result.service_category == ServiceCategory.COMPUTE
            assert len(result.services) > 0
            
            # Verify we have modules from multiple providers
            providers = set(service.provider for service in result.services)
            assert len(providers) >= 2, "Expected modules from multiple cloud providers"
            
            # Verify service structure
            for service in result.services[:5]:  # Check first 5
                assert service.category == ServiceCategory.COMPUTE
                assert service.provider in [CloudProvider.AWS, CloudProvider.AZURE, CloudProvider.GCP]
                assert "terraform_module" in service.service_id
                assert "infrastructure_as_code" in service.features
                
            print(f"✅ Retrieved {len(result.services)} compute modules from {len(providers)} providers")
            
        except RateLimitError:
            pytest.skip("Registry API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"Compute modules test failed: {e}")
        finally:
            await registry_client.close()
    
    @pytest.mark.asyncio
    async def test_module_search(self, registry_client):
        """Test module search functionality."""
        try:
            # Search for VPC modules
            result = await registry_client.get_modules(
                search="vpc",
                limit=10,
                verified_only=True
            )
            
            assert "modules" in result
            assert result["search"] == "vpc"
            
            # Verify search results contain VPC-related modules
            vpc_modules = [m for m in result["modules"] if "vpc" in m["name"].lower() or "vpc" in m["description"].lower()]
            assert len(vpc_modules) > 0, "Expected to find VPC-related modules"
            
            print(f"✅ Found {len(vpc_modules)} VPC modules out of {len(result['modules'])} search results")
            
        except RateLimitError:
            pytest.skip("Registry API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"Module search test failed: {e}")
        finally:
            await registry_client.close()


class TestTerraformCloudProduction:
    """Test Terraform Cloud API with real API calls (requires credentials)."""
    
    @pytest.fixture
    def cloud_client(self):
        """Create a real Terraform Cloud client."""
        token = os.getenv('INFRA_MIND_TERRAFORM_TOKEN')
        org = os.getenv('INFRA_MIND_TERRAFORM_ORG')
        
        if not token or not org:
            pytest.skip("Terraform Cloud credentials not provided - set INFRA_MIND_TERRAFORM_TOKEN and INFRA_MIND_TERRAFORM_ORG")
        
        return TerraformCloudClient(token, org)
    
    @pytest.mark.asyncio
    async def test_list_workspaces(self, cloud_client):
        """Test listing real workspaces."""
        try:
            workspaces = await cloud_client.list_workspaces()
            
            assert isinstance(workspaces, list)
            
            # Verify workspace structure if any exist
            for workspace in workspaces:
                assert "id" in workspace
                assert "name" in workspace
                assert "terraform_version" in workspace
                assert "created_at" in workspace
                
            print(f"✅ Listed {len(workspaces)} workspaces")
            
        except AuthenticationError:
            pytest.fail("Authentication failed - check INFRA_MIND_TERRAFORM_TOKEN")
        except Exception as e:
            pytest.fail(f"List workspaces test failed: {e}")
        finally:
            await cloud_client.close()
    
    @pytest.mark.asyncio
    async def test_create_and_delete_workspace(self, cloud_client):
        """Test creating and deleting a test workspace."""
        workspace_id = None
        try:
            # Create test workspace
            workspace_config = {
                "name": f"infra-mind-test-{int(time.time())}",
                "description": "Test workspace for InfraMind integration testing",
                "terraform_version": "1.5.0",
                "auto_apply": False
            }
            
            workspace = await cloud_client.create_workspace(workspace_config)
            workspace_id = workspace["id"]
            
            assert workspace["name"] == workspace_config["name"]
            assert workspace["description"] == workspace_config["description"]
            assert workspace["terraform_version"] == workspace_config["terraform_version"]
            
            print(f"✅ Created test workspace: {workspace['name']} (ID: {workspace_id})")
            
            # Test workspace deletion
            deleted = await cloud_client.delete_workspace(workspace_id)
            assert deleted is True
            
            print(f"✅ Deleted test workspace: {workspace_id}")
            workspace_id = None  # Mark as cleaned up
            
        except AuthenticationError:
            pytest.fail("Authentication failed - check INFRA_MIND_TERRAFORM_TOKEN")
        except Exception as e:
            pytest.fail(f"Workspace create/delete test failed: {e}")
        finally:
            # Cleanup: delete workspace if it still exists
            if workspace_id:
                try:
                    await cloud_client.delete_workspace(workspace_id)
                    print(f"🧹 Cleaned up workspace: {workspace_id}")
                except Exception as cleanup_error:
                    print(f"⚠️  Failed to cleanup workspace {workspace_id}: {cleanup_error}")
            
            await cloud_client.close()
    
    @pytest.mark.asyncio
    async def test_run_plan_with_minimal_config(self, cloud_client):
        """Test running a plan with minimal Terraform configuration."""
        workspace_id = None
        try:
            # Create test workspace
            workspace_config = {
                "name": f"infra-mind-plan-test-{int(time.time())}",
                "description": "Test workspace for plan execution",
                "terraform_version": "1.5.0",
                "auto_apply": False
            }
            
            workspace = await cloud_client.create_workspace(workspace_config)
            workspace_id = workspace["id"]
            
            print(f"✅ Created test workspace for plan: {workspace['name']}")
            
            # Run a plan with minimal configuration
            plan_config = {
                "message": "InfraMind integration test plan",
                "is_destroy": False,
                "speculative": True  # Speculative plan doesn't affect real infrastructure
            }
            
            plan_result = await cloud_client.run_plan(workspace_id, plan_config)
            
            assert "run_id" in plan_result
            assert plan_result["workspace_id"] == workspace_id
            assert plan_result["speculative"] is True
            assert "plan_url" in plan_result
            
            print(f"✅ Plan executed successfully: {plan_result['run_id']}")
            print(f"   Status: {plan_result['status']}")
            print(f"   Plan URL: {plan_result['plan_url']}")
            
            # Check if cost estimation is available
            if plan_result.get("cost_estimation"):
                cost_data = plan_result["cost_estimation"]
                if cost_data.get("monthly_cost"):
                    print(f"   Monthly Cost: ${cost_data['monthly_cost']} {cost_data.get('currency', 'USD')}")
                else:
                    print("   Cost estimation not available (expected for minimal config)")
            
        except AuthenticationError:
            pytest.fail("Authentication failed - check INFRA_MIND_TERRAFORM_TOKEN")
        except Exception as e:
            pytest.fail(f"Plan execution test failed: {e}")
        finally:
            # Cleanup
            if workspace_id:
                try:
                    await cloud_client.delete_workspace(workspace_id)
                    print(f"🧹 Cleaned up workspace: {workspace_id}")
                except Exception as cleanup_error:
                    print(f"⚠️  Failed to cleanup workspace {workspace_id}: {cleanup_error}")
            
            await cloud_client.close()
    
    @pytest.mark.asyncio
    async def test_cost_estimation_query(self, cloud_client):
        """Test direct cost estimation query."""
        try:
            # Test with a non-existent run ID (should handle gracefully)
            cost_result = await cloud_client.get_cost_estimation("run-nonexistent-test")
            
            # Should return a result indicating cost estimation is not available
            assert "cost_estimate" in cost_result
            assert cost_result["cost_estimate"] is None
            assert "run_id" in cost_result
            
            print("✅ Cost estimation query handled gracefully for non-existent run")
            
        except AuthenticationError:
            pytest.fail("Authentication failed - check INFRA_MIND_TERRAFORM_TOKEN")
        except Exception as e:
            pytest.fail(f"Cost estimation test failed: {e}")
        finally:
            await cloud_client.close()


class TestTerraformUnifiedClientProduction:
    """Test the unified Terraform client with real APIs."""
    
    @pytest.fixture
    def terraform_client(self):
        """Create a unified Terraform client."""
        token = os.getenv('INFRA_MIND_TERRAFORM_TOKEN')
        org = os.getenv('INFRA_MIND_TERRAFORM_ORG')
        
        return TerraformClient(token, org)
    
    @pytest.mark.asyncio
    async def test_unified_compute_services(self, terraform_client):
        """Test getting compute services through unified client."""
        try:
            result = await terraform_client.get_compute_services()
            
            assert result.service_category == ServiceCategory.COMPUTE
            assert len(result.services) > 0
            
            # Verify caching behavior
            start_time = time.time()
            result2 = await terraform_client.get_compute_services()
            cache_time = time.time() - start_time
            
            assert len(result2.services) == len(result.services)
            assert cache_time < 1.0  # Should be much faster due to caching
            
            print(f"✅ Retrieved {len(result.services)} compute services")
            print(f"   Cache performance: {cache_time:.3f}s for second call")
            
        except RateLimitError:
            pytest.skip("API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"Unified compute services test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_unified_providers_and_modules(self, terraform_client):
        """Test getting providers and modules through unified client."""
        try:
            # Test providers
            providers = await terraform_client.get_providers(namespace="hashicorp")
            assert "providers" in providers
            assert providers["namespace"] == "hashicorp"
            
            # Test modules
            modules = await terraform_client.get_modules(provider="aws", limit=10)
            assert "modules" in modules
            assert modules["provider"] == "aws"
            assert len(modules["modules"]) <= 10
            
            print(f"✅ Retrieved {providers['total_count']} HashiCorp providers")
            print(f"✅ Retrieved {modules['total_count']} AWS modules")
            
        except RateLimitError:
            pytest.skip("API rate limit reached - test skipped")
        except Exception as e:
            pytest.fail(f"Unified providers/modules test failed: {e}")
    
    @pytest.mark.asyncio
    async def test_unified_cost_estimation(self, terraform_client):
        """Test cost estimation through unified client."""
        token = os.getenv('INFRA_MIND_TERRAFORM_TOKEN')
        
        if not token:
            pytest.skip("Terraform Cloud token not provided - skipping cost estimation test")
        
        try:
            # Test with non-existent run (should handle gracefully)
            cost_data = await terraform_client.get_service_pricing("run-test-123")
            
            assert "cost_estimate" in cost_data or "error" in cost_data
            
            print("✅ Cost estimation query completed through unified client")
            
        except AuthenticationError:
            pytest.fail("Authentication failed - check INFRA_MIND_TERRAFORM_TOKEN")
        except Exception as e:
            pytest.fail(f"Unified cost estimation test failed: {e}")


class TestTerraformProductionWorkflow:
    """Test complete production workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_infrastructure_assessment_workflow(self):
        """Test a complete workflow simulating infrastructure assessment."""
        token = os.getenv('INFRA_MIND_TERRAFORM_TOKEN')
        org = os.getenv('INFRA_MIND_TERRAFORM_ORG')
        
        if not token or not org:
            pytest.skip("Terraform Cloud credentials not provided")
        
        client = TerraformClient(token, org)
        workspace_id = None
        
        try:
            print("🚀 Starting complete infrastructure assessment workflow...")
            
            # Step 1: Get available providers and modules
            print("📋 Step 1: Gathering Terraform ecosystem information...")
            
            providers = await client.get_providers(namespace="hashicorp")
            aws_modules = await client.get_modules(provider="aws", verified_only=True, limit=5)
            compute_services = await client.get_compute_services()
            
            assert providers["total_count"] > 0
            assert len(aws_modules["modules"]) > 0
            assert len(compute_services.services) > 0
            
            print(f"   ✅ Found {providers['total_count']} HashiCorp providers")
            print(f"   ✅ Found {len(aws_modules['modules'])} verified AWS modules")
            print(f"   ✅ Found {len(compute_services.services)} compute services")
            
            # Step 2: Create a workspace for assessment
            print("🏗️  Step 2: Creating assessment workspace...")
            
            workspace_config = {
                "name": f"infra-mind-assessment-{int(time.time())}",
                "description": "InfraMind infrastructure assessment workspace",
                "terraform_version": "1.5.0",
                "auto_apply": False
            }
            
            workspace = await client.create_workspace(workspace_config)
            workspace_id = workspace["id"]
            
            print(f"   ✅ Created workspace: {workspace['name']} (ID: {workspace_id})")
            
            # Step 3: Run a speculative plan for cost estimation
            print("💰 Step 3: Running cost estimation plan...")
            
            plan_config = {
                "message": "InfraMind infrastructure assessment plan",
                "speculative": True,
                "is_destroy": False
            }
            
            plan_result = await client.run_plan(workspace_id, plan_config)
            
            assert plan_result["run_id"]
            assert plan_result["workspace_id"] == workspace_id
            
            print(f"   ✅ Plan executed: {plan_result['run_id']}")
            print(f"   📊 Status: {plan_result['status']}")
            print(f"   🔗 Plan URL: {plan_result['plan_url']}")
            
            # Step 4: Analyze results
            print("📊 Step 4: Analyzing assessment results...")
            
            assessment_results = {
                "providers_available": providers["total_count"],
                "modules_available": len(aws_modules["modules"]),
                "compute_options": len(compute_services.services),
                "workspace_created": workspace["name"],
                "plan_executed": plan_result["run_id"],
                "cost_estimation_available": bool(plan_result.get("cost_estimation", {}).get("monthly_cost")),
                "assessment_timestamp": datetime.now().isoformat()
            }
            
            print("   ✅ Assessment completed successfully!")
            print(f"   📈 Results: {assessment_results}")
            
            # Verify workflow completeness
            assert assessment_results["providers_available"] > 0
            assert assessment_results["modules_available"] > 0
            assert assessment_results["compute_options"] > 0
            assert assessment_results["workspace_created"]
            assert assessment_results["plan_executed"]
            
            print("🎉 Complete infrastructure assessment workflow successful!")
            
        except Exception as e:
            pytest.fail(f"Complete workflow test failed: {e}")
        finally:
            # Cleanup
            if workspace_id:
                try:
                    await client.cloud_client.delete_workspace(workspace_id)
                    print(f"🧹 Cleaned up assessment workspace: {workspace_id}")
                except Exception as cleanup_error:
                    print(f"⚠️  Failed to cleanup workspace {workspace_id}: {cleanup_error}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "-s"])