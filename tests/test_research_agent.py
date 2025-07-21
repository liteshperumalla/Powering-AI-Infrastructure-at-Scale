"""
Tests for Research Agent.

Tests the Research Agent's data collection, analysis, and validation capabilities.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.infra_mind.agents.research_agent import ResearchAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestResearchAgent:
    """Test suite for Research Agent."""
    
    @pytest.fixture
    def research_agent(self):
        """Create a Research Agent instance for testing."""
        config = AgentConfig(
            name="Test Research Agent",
            role=AgentRole.RESEARCH,
            tools_enabled=["cloud_api", "data_processor", "calculator"],
            custom_config={
                "focus_areas": [
                    "data_collection",
                    "pricing_analysis",
                    "trend_analysis",
                    "benchmark_collection",
                    "market_intelligence"
                ],
                "data_sources": [
                    "aws_pricing_api",
                    "azure_retail_api",
                    "gcp_billing_api"
                ]
            }
        )
        return ResearchAgent(config)
    
    @pytest.fixture
    def mock_assessment(self):
        """Create a mock assessment for testing."""
        return Mock(spec=Assessment, **{
            'dict.return_value': {
                'business_requirements': {
                    'company_size': 'medium',
                    'industry': 'technology',
                    'budget_range': '$50k-100k',
                    'primary_goals': ['cost_optimization', 'scalability']
                },
                'technical_requirements': {
                    'workload_types': ['web_application', 'ai_ml'],
                    'expected_users': 5000,
                    'performance_requirements': {'response_time': '< 200ms'}
                },
                'compliance_requirements': {
                    'regulations': ['GDPR']
                }
            }
        })
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, research_agent):
        """Test Research Agent initialization."""
        assert research_agent.name == "Test Research Agent"
        assert research_agent.role == AgentRole.RESEARCH
        assert research_agent.status == AgentStatus.IDLE
        assert "data_collection" in research_agent.config.custom_config["focus_areas"]
        assert "aws_pricing_api" in research_agent.config.custom_config["data_sources"]
    
    @pytest.mark.asyncio
    async def test_analyze_data_requirements(self, research_agent, mock_assessment):
        """Test data requirements analysis."""
        research_agent.current_assessment = mock_assessment
        
        # Mock the data processor tool
        with patch.object(research_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = Mock(is_success=True, data={'analysis': 'complete'})
            
            requirements = await research_agent._analyze_data_requirements()
            
            assert 'workload_analysis' in requirements
            assert 'required_services' in requirements
            assert 'pricing_requirements' in requirements
            assert 'benchmark_requirements' in requirements
            
            # Check workload analysis
            workload_analysis = requirements['workload_analysis']
            assert workload_analysis['types'] == ['web_application', 'ai_ml']
            assert workload_analysis['expected_users'] == 5000
            assert workload_analysis['budget_range'] == '$50k-100k'
            
            # Check required services
            required_services = requirements['required_services']
            assert 'compute' in required_services
            assert 'storage' in required_services
            assert 'database' in required_services
            assert 'ai_ml' in required_services
    
    @pytest.mark.asyncio
    async def test_collect_realtime_data(self, research_agent):
        """Test real-time data collection."""
        requirements = {
            'collection_scope': {
                'providers': ['aws', 'azure'],
                'regions': ['us-east-1', 'eastus'],
                'service_categories': ['compute', 'storage']
            },
            'required_services': ['compute', 'storage']
        }
        
        # Mock provider data collection
        with patch.object(research_agent, '_collect_provider_data') as mock_collect:
            mock_collect.side_effect = [
                {
                    'provider': 'aws',
                    'services': {'compute': {'services': []}},
                    'pricing_data': {'compute': {'pricing': []}},
                    'data_completeness': 0.8
                },
                {
                    'provider': 'azure',
                    'services': {'compute': {'services': []}},
                    'pricing_data': {'compute': {'pricing': []}},
                    'data_completeness': 0.7
                }
            ]
            
            collected_data = await research_agent._collect_realtime_data(requirements)
            
            assert 'providers' in collected_data
            assert 'collection_metadata' in collected_data
            assert 'aws' in collected_data['providers']
            assert 'azure' in collected_data['providers']
            assert collected_data['collection_metadata']['successful_collections'] == 2
            assert collected_data['collection_metadata']['failed_collections'] == 0
    
    @pytest.mark.asyncio
    async def test_validate_data_quality(self, research_agent):
        """Test data quality validation."""
        collected_data = {
            'providers': {
                'aws': {
                    'provider': 'aws',
                    'services': {'compute': {'services': [{'name': 'EC2'}]}},
                    'pricing_data': {'compute': {'pricing': [{'hourly_price': 0.10}]}},
                    'data_completeness': 0.9,
                    'collection_timestamp': datetime.now(timezone.utc).isoformat()
                },
                'azure': {
                    'provider': 'azure',
                    'services': {'compute': {'services': [{'name': 'VM'}]}},
                    'pricing_data': {'compute': {'pricing': [{'hourly_price': 0.12}]}},
                    'data_completeness': 0.8,
                    'collection_timestamp': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
                }
            }
        }
        
        validation_results = await research_agent._validate_data_quality(collected_data)
        
        assert 'overall_quality' in validation_results
        assert 'freshness_check' in validation_results
        assert 'completeness_check' in validation_results
        assert 'consistency_check' in validation_results
        assert 'accuracy_check' in validation_results
        assert 'quality_score' in validation_results
        
        # Check freshness scores
        assert 'aws' in validation_results['freshness_check']
        assert 'azure' in validation_results['freshness_check']
        
        # AWS should have better freshness (more recent)
        aws_freshness = validation_results['freshness_check']['aws']['score']
        azure_freshness = validation_results['freshness_check']['azure']['score']
        assert aws_freshness >= azure_freshness
    
    @pytest.mark.asyncio
    async def test_perform_trend_analysis(self, research_agent):
        """Test trend analysis functionality."""
        collected_data = {
            'providers': {
                'aws': {
                    'services': {
                        'compute': {
                            'services': [
                                {'name': 'EC2 t3.medium', 'hourly_price': 0.0416}
                            ]
                        }
                    },
                    'pricing_data': {
                        'compute': {
                            'pricing': [
                                {'service_name': 'EC2 t3.medium', 'hourly_price': 0.0416}
                            ]
                        }
                    }
                },
                'azure': {
                    'services': {
                        'compute': {
                            'services': [
                                {'name': 'VM Standard_B2s', 'hourly_price': 0.0496}
                            ]
                        }
                    },
                    'pricing_data': {
                        'compute': {
                            'pricing': [
                                {'service_name': 'VM Standard_B2s', 'hourly_price': 0.0496}
                            ]
                        }
                    }
                }
            }
        }
        
        trend_analysis = await research_agent._perform_trend_analysis(collected_data)
        
        assert 'pricing_trends' in trend_analysis
        assert 'service_trends' in trend_analysis
        assert 'market_insights' in trend_analysis
        assert 'emerging_patterns' in trend_analysis
        
        # Check pricing trends
        pricing_trends = trend_analysis['pricing_trends']
        assert 'cost_leaders' in pricing_trends
        assert 'price_ranges' in pricing_trends
    
    @pytest.mark.asyncio
    async def test_collect_benchmark_data(self, research_agent):
        """Test benchmark data collection."""
        requirements = {
            'workload_analysis': {
                'types': ['web_application', 'ai_ml'],
                'expected_users': 5000
            }
        }
        
        benchmark_data = await research_agent._collect_benchmark_data(requirements)
        
        assert 'performance_benchmarks' in benchmark_data
        assert 'cost_benchmarks' in benchmark_data
        assert 'industry_benchmarks' in benchmark_data
        
        # Check performance benchmarks
        performance_benchmarks = benchmark_data['performance_benchmarks']
        assert 'web_application' in performance_benchmarks
        assert 'ai_ml' in performance_benchmarks
        
        # Check web application benchmarks
        web_benchmarks = performance_benchmarks['web_application']
        assert 'response_time_ms' in web_benchmarks
        assert 'throughput_rps' in web_benchmarks
        
        # Check AI/ML benchmarks
        ai_benchmarks = performance_benchmarks['ai_ml']
        assert 'training_time_hours' in ai_benchmarks
        assert 'inference_latency_ms' in ai_benchmarks
    
    @pytest.mark.asyncio
    async def test_data_freshness_validation(self, research_agent):
        """Test data freshness validation with different timestamps."""
        # Fresh data (1 hour old)
        fresh_data = {
            'collection_timestamp': (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        }
        
        # Stale data (25 hours old)
        stale_data = {
            'collection_timestamp': (datetime.now(timezone.utc) - timedelta(hours=25)).isoformat()
        }
        
        # Very stale data (50 hours old)
        very_stale_data = {
            'collection_timestamp': (datetime.now(timezone.utc) - timedelta(hours=50)).isoformat()
        }
        
        fresh_score, fresh_warning = research_agent._check_data_freshness_detailed(fresh_data)
        stale_score, stale_warning = research_agent._check_data_freshness_detailed(stale_data)
        very_stale_score, very_stale_warning = research_agent._check_data_freshness_detailed(very_stale_data)
        
        # Fresh data should have high score and no warning
        assert fresh_score >= 0.9
        assert fresh_warning is None
        
        # Stale data should have lower score and warning
        assert stale_score < fresh_score
        assert stale_warning is not None
        assert "hours old" in stale_warning
        
        # Very stale data should have lowest score and warning
        assert very_stale_score < stale_score
        assert very_stale_warning is not None
        assert "refresh recommended" in very_stale_warning
    
    @pytest.mark.asyncio
    async def test_data_accuracy_validation(self, research_agent):
        """Test data accuracy validation."""
        # Valid data
        valid_data = {
            'services': {
                'compute': {
                    'services': [
                        {
                            'name': 'Valid Service',
                            'specifications': {
                                'vcpus': 2,
                                'memory_gb': 4
                            }
                        }
                    ]
                }
            },
            'pricing_data': {
                'compute': {
                    'pricing': [
                        {
                            'service_name': 'Valid Service',
                            'hourly_price': 0.10
                        }
                    ]
                }
            }
        }
        
        # Invalid data
        invalid_data = {
            'services': {
                'compute': {
                    'services': [
                        {
                            'name': 'Invalid Service',
                            'specifications': {
                                'vcpus': -1,  # Invalid
                                'memory_gb': 0   # Invalid
                            }
                        }
                    ]
                }
            },
            'pricing_data': {
                'compute': {
                    'pricing': [
                        {
                            'service_name': 'Invalid Service',
                            'hourly_price': -5.0  # Invalid negative price
                        }
                    ]
                }
            }
        }
        
        valid_accuracy = research_agent._check_data_accuracy(valid_data)
        invalid_accuracy = research_agent._check_data_accuracy(invalid_data)
        
        # Valid data should have high accuracy score
        assert valid_accuracy['score'] >= 0.9
        assert len(valid_accuracy['issues']) == 0
        
        # Invalid data should have lower accuracy score and issues
        assert invalid_accuracy['score'] < valid_accuracy['score']
        assert len(invalid_accuracy['issues']) > 0
        assert any("Negative pricing" in issue for issue in invalid_accuracy['issues'])
        assert any("Invalid vCPU" in issue for issue in invalid_accuracy['issues'])
    
    @pytest.mark.asyncio
    async def test_full_execution_workflow(self, research_agent, mock_assessment):
        """Test the complete Research Agent execution workflow."""
        # Mock all the tools and external dependencies
        with patch.object(research_agent, '_use_tool') as mock_tool, \
             patch('src.infra_mind.agents.research_agent.UnifiedCloudClient') as mock_cloud_client:
            
            # Mock tool responses
            mock_tool.return_value = Mock(is_success=True, data={'analysis': 'complete'})
            
            # Mock cloud client
            mock_client_instance = Mock()
            mock_client_instance.get_available_providers.return_value = []
            mock_cloud_client.return_value = mock_client_instance
            
            # Execute the agent
            result = await research_agent.execute(mock_assessment)
            
            assert result.status == AgentStatus.COMPLETED
            assert result.agent_name == "Test Research Agent"
            assert 'data' in result.to_dict()
            
            # Check result structure
            result_data = result.data
            assert 'data_requirements' in result_data
            assert 'collected_data' in result_data
            assert 'data_validation' in result_data
            assert 'trend_analysis' in result_data
            assert 'benchmark_data' in result_data
            assert 'research_insights' in result_data
    
    def test_determine_required_services(self, research_agent):
        """Test service requirement determination."""
        # Web application workload
        web_services = research_agent._determine_required_services(['web_application'])
        assert 'compute' in web_services
        assert 'storage' in web_services
        assert 'database' in web_services
        assert 'networking' in web_services
        
        # AI/ML workload
        ai_services = research_agent._determine_required_services(['ai_ml'])
        assert 'compute' in ai_services
        assert 'storage' in ai_services
        assert 'ai_ml' in ai_services
        assert 'networking' in ai_services
        
        # Mixed workloads
        mixed_services = research_agent._determine_required_services(['web_application', 'ai_ml'])
        assert 'compute' in mixed_services
        assert 'storage' in mixed_services
        assert 'database' in mixed_services
        assert 'ai_ml' in mixed_services
        assert 'networking' in mixed_services
    
    def test_pricing_requirements_determination(self, research_agent):
        """Test pricing requirements determination."""
        # Low budget
        low_budget_req = research_agent._determine_pricing_requirements('$10k-50k', 1000)
        assert low_budget_req['budget_range'] == '$10k-50k'
        assert low_budget_req['budget_min'] == 10000
        assert low_budget_req['budget_max'] == 50000
        assert low_budget_req['pricing_focus'] == 'cost_optimization'
        
        # High budget
        high_budget_req = research_agent._determine_pricing_requirements('$100k+', 10000)
        assert high_budget_req['budget_range'] == '$100k+'
        assert high_budget_req['budget_min'] == 100000
        assert high_budget_req['budget_max'] == 500000
        assert high_budget_req['pricing_focus'] == 'performance_optimization'
    
    def test_data_completeness_calculation(self, research_agent):
        """Test data completeness calculation."""
        # Complete data
        complete_data = {
            'services': {
                'compute': {'services': [{'name': 'service1'}]},
                'storage': {'services': [{'name': 'service2'}]}
            },
            'pricing_data': {
                'compute': {'pricing': [{'price': 0.10}]},
                'storage': {'pricing': [{'price': 0.05}]}
            }
        }
        
        completeness = research_agent._calculate_data_completeness(
            complete_data, ['compute', 'storage']
        )
        assert completeness == 1.0
        
        # Partial data
        partial_data = {
            'services': {
                'compute': {'services': [{'name': 'service1'}]}
            },
            'pricing_data': {
                'compute': {'pricing': [{'price': 0.10}]}
            }
        }
        
        completeness = research_agent._calculate_data_completeness(
            partial_data, ['compute', 'storage']
        )
        assert completeness == 0.5
    
    def test_budget_range_parsing(self, research_agent):
        """Test budget range parsing."""
        # Test various budget ranges
        assert research_agent._parse_budget_range('$1k-10k') == (1000, 10000)
        assert research_agent._parse_budget_range('$10k-50k') == (10000, 50000)
        assert research_agent._parse_budget_range('$50k-100k') == (50000, 100000)
        assert research_agent._parse_budget_range('$100k+') == (100000, 500000)
        
        # Test unknown range (should return default)
        assert research_agent._parse_budget_range('unknown') == (10000, 50000)


if __name__ == '__main__':
    pytest.main([__file__])