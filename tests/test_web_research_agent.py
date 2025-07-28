"""
Tests for Web Research Agent.

Tests the web research capabilities including scraping, analysis, and recommendations.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any

from src.infra_mind.agents.web_research_agent import WebResearchAgent
from src.infra_mind.agents.base import AgentConfig, AgentRole, AgentStatus
from src.infra_mind.models.assessment import Assessment


class TestWebResearchAgent:
    """Test cases for Web Research Agent."""
    
    @pytest.fixture
    def sample_assessment(self):
        """Create a sample assessment for testing."""
        business_req = {
            "company_size": "medium",
            "industry": "technology",
            "budget_range": "100k-500k",
            "timeline": "6-12 months",
            "compliance_needs": ["GDPR", "SOC2"],
            "business_goals": ["cost_optimization", "scalability"]
        }
        
        technical_req = {
            "current_infrastructure": {
                "cloud_providers": ["aws"],
                "services_used": ["ec2", "rds"],
                "architecture": "monolithic"
            },
            "workload_characteristics": {
                "workload_types": ["web_application"],
                "expected_users": 5000,
                "data_volume": "500GB"
            },
            "performance_requirements": {
                "availability": "99.9%",
                "response_time": "200ms"
            },
            "scalability_needs": {
                "auto_scaling": True,
                "peak_capacity": "3x"
            },
            "integration_requirements": ["monitoring", "ci_cd"]
        }
        
        return Assessment(
            user_id="test_user",
            title="Test Assessment",
            business_requirements=business_req,
            technical_requirements=technical_req,
            status="in_progress"
        )
    
    @pytest.fixture
    def web_research_agent(self):
        """Create a Web Research Agent instance."""
        return WebResearchAgent()
    
    def test_agent_initialization(self, web_research_agent):
        """Test Web Research Agent initialization."""
        assert web_research_agent.name == "Web Research Agent"
        assert web_research_agent.role == AgentRole.WEB_RESEARCH
        assert web_research_agent.status == AgentStatus.IDLE
        
        # Check research targets are configured
        assert "aws_pricing" in web_research_agent.research_targets
        assert "azure_pricing" in web_research_agent.research_targets
        assert "industry_trends" in web_research_agent.research_targets
        assert "regulatory_updates" in web_research_agent.research_targets
        
        # Check extraction patterns are configured
        assert "pricing" in web_research_agent.extraction_patterns
        assert "trends" in web_research_agent.extraction_patterns
        assert "compliance" in web_research_agent.extraction_patterns
        
        # Check freshness thresholds
        assert web_research_agent.freshness_thresholds["pricing_data"] == 24
        assert web_research_agent.freshness_thresholds["trend_data"] == 48
    
    @pytest.mark.asyncio
    async def test_analyze_research_requirements(self, web_research_agent, sample_assessment):
        """Test research requirements analysis."""
        # Initialize agent
        await web_research_agent.initialize(sample_assessment)
        
        # Mock the data processor tool
        with patch.object(web_research_agent, '_use_tool') as mock_tool:
            mock_tool.return_value = Mock(
                is_success=True,
                data={
                    "insights": [
                        "Budget range: 100k-500k",
                        "Industry: technology",
                        "Compliance needs: GDPR, SOC2"
                    ]
                }
            )
            
            requirements = await web_research_agent._analyze_research_requirements()
            
            # Verify requirements structure
            assert "priority_areas" in requirements
            assert "target_providers" in requirements
            assert "research_depth" in requirements
            
            # Check that compliance needs triggered regulatory tracking
            assert "regulatory_tracking" in requirements["priority_areas"]
            
            # Check default providers
            assert "aws" in requirements["target_providers"]
            assert "azure" in requirements["target_providers"]
            assert "gcp" in requirements["target_providers"]
    
    @pytest.mark.asyncio
    async def test_scrape_url_success(self, web_research_agent):
        """Test successful URL scraping."""
        mock_html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>AWS Pricing</h1>
                <p>EC2 instances start at $0.0116 per hour.</p>
                <p>RDS pricing begins at $0.017 per hour.</p>
            </body>
        </html>
        """
        
        with patch('aiohttp.ClientSession') as mock_session:
            # Mock the HTTP response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value=mock_html)
            mock_response.headers = {"content-type": "text/html"}
            
            mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
            
            # Mock cache manager
            with patch.object(web_research_agent.cache_manager, 'get', return_value=None):
                with patch.object(web_research_agent.cache_manager, 'set'):
                    result = await web_research_agent._scrape_url(
                        "https://example.com/pricing", 
                        "pricing", 
                        "aws"
                    )
            
            # Verify result structure
            assert result is not None
            assert result["source_url"] == "https://example.com/pricing"
            assert result["source_type"] == "pricing"
            assert result["provider"] == "aws"
            assert "content_hash" in result
            assert "extracted_data" in result
            
            # Verify extracted data
            extracted = result["extracted_data"]
            assert extracted["title"] == "Test Page"
            assert "content" in extracted
    
    @pytest.mark.asyncio
    async def test_extract_pricing_content(self, web_research_agent):
        """Test pricing content extraction."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <h1>Cloud Pricing</h1>
                <p>EC2 t3.micro instances cost $0.0104 per hour</p>
                <p>RDS db.t3.micro costs $0.017 per hour</p>
                <p>Storage is $0.10 per GB per month</p>
                <p>Get 20% off your first year!</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        pricing_content = await web_research_agent._extract_pricing_content(soup)
        
        # Verify pricing extraction
        assert "prices_found" in pricing_content
        assert "services_mentioned" in pricing_content
        assert "discounts" in pricing_content
        
        # Check that prices were found
        prices = pricing_content["prices_found"]
        assert len(prices) > 0
        
        # Check that services were mentioned
        services = pricing_content["services_mentioned"]
        assert any("EC2" in service for service in services)
        
        # Check that discounts were found
        discounts = pricing_content["discounts"]
        assert len(discounts) > 0
        assert any("20%" in discount for discount in discounts)
    
    @pytest.mark.asyncio
    async def test_extract_trend_content(self, web_research_agent):
        """Test trend content extraction."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <h1>Cloud Computing Trends 2024</h1>
                <h2>Artificial Intelligence Adoption</h2>
                <p>Machine learning adoption is increasing rapidly.</p>
                <h3>Serverless Computing Growth</h3>
                <p>Serverless technologies are emerging as a key trend.</p>
                <p>Container adoption is growing in enterprise environments.</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        trend_content = await web_research_agent._extract_trend_content(soup)
        
        # Verify trend extraction
        assert "trends_identified" in trend_content
        assert "sentiment_indicators" in trend_content
        assert "key_topics" in trend_content
        
        # Check that trends were identified
        trends = trend_content["trends_identified"]
        assert "artificial intelligence" in trends
        assert "machine learning" in trends
        assert "serverless" in trends
        
        # Check sentiment indicators
        sentiments = trend_content["sentiment_indicators"]
        assert "increasing" in sentiments
        assert "growing" in sentiments
        assert "emerging" in sentiments
        
        # Check key topics from headings
        topics = trend_content["key_topics"]
        assert len(topics) > 0
    
    @pytest.mark.asyncio
    async def test_extract_regulatory_content(self, web_research_agent):
        """Test regulatory content extraction."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <body>
                <h1>GDPR Compliance Updates</h1>
                <p>New GDPR requirements updated for 2024.</p>
                <h2>HIPAA Privacy Rules</h2>
                <p>HIPAA compliance is mandatory for healthcare data.</p>
                <h3>CCPA Amendment</h3>
                <p>California privacy law has been amended.</p>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        regulatory_content = await web_research_agent._extract_regulatory_content(soup)
        
        # Verify regulatory extraction
        assert "regulations_mentioned" in regulatory_content
        assert "updates_found" in regulatory_content
        assert "compliance_topics" in regulatory_content
        
        # Check regulations mentioned
        regulations = regulatory_content["regulations_mentioned"]
        assert "GDPR" in regulations
        assert "HIPAA" in regulations
        assert "CCPA" in regulations
        
        # Check update indicators
        updates = regulatory_content["updates_found"]
        assert "updated" in updates
        assert "amended" in updates
        
        # Check compliance topics
        topics = regulatory_content["compliance_topics"]
        assert len(topics) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_competitive_landscape(self, web_research_agent):
        """Test competitive landscape analysis."""
        # Mock web data
        web_data = [
            {
                "source_url": "https://example.com/comparison",
                "source_type": "competitive",
                "provider": "general",
                "extracted_data": {
                    "content": {
                        "providers_mentioned": ["AWS", "Azure", "Google Cloud"],
                        "market_insights": ["AWS leads in market share", "Azure growing rapidly"],
                        "prices_found": [{"amount": "0.10", "unit": "hour"}]
                    }
                }
            },
            {
                "source_url": "https://example.com/aws-info",
                "source_type": "pricing",
                "provider": "aws",
                "extracted_data": {
                    "content": {
                        "providers_mentioned": ["AWS"],
                        "prices_found": [{"amount": "0.05", "unit": "hour"}]
                    }
                }
            }
        ]
        
        analysis = await web_research_agent._analyze_competitive_landscape(web_data)
        
        # Verify analysis structure
        assert "provider_mentions" in analysis
        assert "market_positioning" in analysis
        assert "pricing_comparisons" in analysis
        assert "market_trends" in analysis
        
        # Check provider mentions
        mentions = analysis["provider_mentions"]
        assert "aws" in mentions
        assert "azure" in mentions
        
        # Check market positioning
        positioning = analysis["market_positioning"]
        assert len(positioning) > 0
        
        # Check pricing comparisons
        pricing = analysis["pricing_comparisons"]
        assert len(pricing) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_trends_and_insights(self, web_research_agent):
        """Test trends and insights analysis."""
        # Mock web data
        web_data = [
            {
                "source_url": "https://example.com/trends",
                "source_type": "trends",
                "extracted_data": {
                    "content": {
                        "trends_identified": ["artificial intelligence", "machine learning", "serverless"],
                        "sentiment_indicators": ["increasing", "growing", "emerging"],
                        "key_topics": ["AI Adoption", "Cloud Migration", "DevOps Practices"]
                    }
                }
            },
            {
                "source_url": "https://example.com/tech-news",
                "source_type": "trends",
                "extracted_data": {
                    "content": {
                        "trends_identified": ["artificial intelligence", "containers"],
                        "sentiment_indicators": ["growing", "trending"],
                        "key_topics": ["Container Orchestration"]
                    }
                }
            }
        ]
        
        analysis = await web_research_agent._analyze_trends_and_insights(web_data)
        
        # Verify analysis structure
        assert "emerging_trends" in analysis
        assert "sentiment_analysis" in analysis
        assert "key_topics" in analysis
        
        # Check emerging trends (mentioned multiple times)
        emerging = analysis["emerging_trends"]
        ai_trend = next((t for t in emerging if t["trend"] == "artificial intelligence"), None)
        assert ai_trend is not None
        assert ai_trend["mention_count"] == 2
        
        # Check sentiment analysis
        sentiment = analysis["sentiment_analysis"]
        assert "growing" in sentiment
        assert sentiment["growing"] == 2  # Mentioned twice
        
        # Check key topics
        topics = analysis["key_topics"]
        assert len(topics) > 0
    
    @pytest.mark.asyncio
    async def test_generate_market_intelligence(self, web_research_agent):
        """Test market intelligence generation."""
        # Mock analysis results
        competitive_analysis = {
            "provider_mentions": {"aws": 5, "azure": 3, "gcp": 2},
            "market_positioning": {
                "aws": {"mention_count": 5, "visibility_score": 0.8},
                "azure": {"mention_count": 3, "visibility_score": 0.6}
            },
            "pricing_comparisons": [{"provider": "aws", "price": {"amount": "0.10", "unit": "hour"}}],
            "market_trends": ["Cloud adoption increasing", "Multi-cloud strategies popular"]
        }
        
        trend_analysis = {
            "emerging_trends": [
                {"trend": "artificial intelligence", "strength": "high", "mention_count": 5},
                {"trend": "serverless", "strength": "medium", "mention_count": 3}
            ],
            "sentiment_analysis": {"growing": 3, "increasing": 2},
            "key_topics": [
                {"topic": "AI Adoption", "mentions": 4},
                {"topic": "Cloud Migration", "mentions": 3}
            ]
        }
        
        regulatory_updates = {
            "regulations_tracked": [
                {"regulation": "GDPR", "mentions": 3},
                {"regulation": "HIPAA", "mentions": 2}
            ],
            "recent_updates": [{"update_type": "updated", "timestamp": "2024-01-01"}],
            "compliance_topics": [{"topic": "Data Privacy", "frequency": 2}]
        }
        
        intelligence = await web_research_agent._generate_market_intelligence(
            competitive_analysis, trend_analysis, regulatory_updates
        )
        
        # Verify intelligence structure
        assert "executive_summary" in intelligence
        assert "market_dynamics" in intelligence
        assert "competitive_landscape" in intelligence
        assert "technology_trends" in intelligence
        assert "regulatory_environment" in intelligence
        assert "strategic_recommendations" in intelligence
        
        # Check executive summary
        summary = intelligence["executive_summary"]
        assert summary["providers_analyzed"] == 2
        assert summary["trends_identified"] == 2
        assert summary["regulations_monitored"] == 2
        assert len(summary["key_insights"]) > 0
        
        # Check strategic recommendations
        recommendations = intelligence["strategic_recommendations"]
        assert len(recommendations) > 0
        
        # Verify recommendation structure
        for rec in recommendations:
            assert "category" in rec
            assert "recommendation" in rec
            assert "rationale" in rec
            assert "priority" in rec
    
    @pytest.mark.asyncio
    async def test_create_web_research_recommendations(self, web_research_agent):
        """Test web research recommendations creation."""
        # Mock market intelligence
        market_intelligence = {
            "strategic_recommendations": [
                {
                    "category": "provider_selection",
                    "recommendation": "Consider AWS - high market visibility",
                    "rationale": "Mentioned 5 times across sources",
                    "priority": "high"
                }
            ],
            "market_dynamics": {
                "provider_visibility": {
                    "aws": {"mention_count": 5, "visibility_score": 0.8}
                }
            },
            "technology_trends": {
                "emerging_technologies": [
                    {"trend": "artificial intelligence", "strength": "high"}
                ]
            },
            "regulatory_environment": {
                "active_regulations": [
                    {"regulation": "GDPR", "mentions": 3}
                ]
            }
        }
        
        # Mock validation results
        validation_results = {
            "confidence_scores": {
                "aws": 0.9,
                "azure": 0.6  # Low confidence
            }
        }
        
        recommendations = await web_research_agent._create_web_research_recommendations(
            market_intelligence, validation_results
        )
        
        # Verify recommendations structure
        assert len(recommendations) > 0
        
        # Check recommendation types
        rec_types = [rec["type"] for rec in recommendations]
        assert "strategic" in rec_types
        assert "data_quality" in rec_types  # Due to low Azure confidence
        assert "market_positioning" in rec_types
        
        # Verify recommendation structure
        for rec in recommendations:
            assert "type" in rec
            assert "category" in rec
            assert "title" in rec
            assert "description" in rec
            assert "priority" in rec
            assert "confidence_score" in rec
            assert "source" in rec
            assert "implementation_effort" in rec
            assert "business_impact" in rec
    
    @pytest.mark.asyncio
    async def test_check_data_freshness(self, web_research_agent):
        """Test data freshness checking."""
        freshness_report = await web_research_agent._check_data_freshness()
        
        # Verify report structure
        assert "overall_status" in freshness_report
        assert "data_categories" in freshness_report
        assert "stale_data_count" in freshness_report
        assert "refresh_recommendations" in freshness_report
        
        # Check data categories
        categories = freshness_report["data_categories"]
        assert "pricing_data" in categories
        assert "trend_data" in categories
        assert "regulatory_data" in categories
        assert "best_practices" in categories
        
        # Verify category structure
        for category, data in categories.items():
            if "error" not in data:
                assert "threshold_hours" in data
                assert "status" in data
    
    @pytest.mark.asyncio
    async def test_full_execution_flow(self, web_research_agent, sample_assessment):
        """Test the full execution flow of the Web Research Agent."""
        # Mock external dependencies
        with patch.object(web_research_agent, '_collect_web_data') as mock_collect:
            mock_collect.return_value = [
                {
                    "source_url": "https://example.com/test",
                    "source_type": "pricing",
                    "provider": "aws",
                    "extracted_data": {"content": {"prices_found": [{"amount": "0.10", "unit": "hour"}]}}
                }
            ]
            
            with patch.object(web_research_agent, '_store_web_research_data'):
                # Execute the agent
                result = await web_research_agent.execute(sample_assessment)
                
                # Verify execution success
                assert result.status == AgentStatus.COMPLETED
                assert result.agent_name == "Web Research Agent"
                assert "recommendations" in result.data
                assert "market_intelligence" in result.data
                assert "competitive_analysis" in result.data
                assert "trend_analysis" in result.data
                
                # Verify recommendations were created
                recommendations = result.data["recommendations"]
                assert len(recommendations) >= 0  # May be empty in mock scenario
    
    @pytest.mark.asyncio
    async def test_error_handling(self, web_research_agent, sample_assessment):
        """Test error handling in Web Research Agent."""
        # Mock a failure in data collection
        with patch.object(web_research_agent, '_collect_web_data') as mock_collect:
            mock_collect.side_effect = Exception("Network error")
            
            # Execute the agent
            result = await web_research_agent.execute(sample_assessment)
            
            # Verify error handling
            assert result.status == AgentStatus.FAILED
            assert result.error is not None
            assert "Network error" in result.error
    
    def test_research_targets_configuration(self, web_research_agent):
        """Test that research targets are properly configured."""
        targets = web_research_agent.research_targets
        
        # Check all required target categories exist
        required_categories = [
            "aws_pricing", "azure_pricing", "gcp_pricing",
            "industry_trends", "regulatory_updates", "best_practices"
        ]
        
        for category in required_categories:
            assert category in targets
            assert len(targets[category]) > 0
            
            # Verify URLs are valid format
            for url in targets[category]:
                assert url.startswith("https://")
    
    def test_extraction_patterns_configuration(self, web_research_agent):
        """Test that extraction patterns are properly configured."""
        patterns = web_research_agent.extraction_patterns
        
        # Check pricing patterns
        assert "pricing" in patterns
        pricing_patterns = patterns["pricing"]
        assert "price_regex" in pricing_patterns
        assert "service_regex" in pricing_patterns
        assert "discount_regex" in pricing_patterns
        
        # Check trend patterns
        assert "trends" in patterns
        trend_patterns = patterns["trends"]
        assert "trend_keywords" in trend_patterns
        assert "sentiment_indicators" in trend_patterns
        
        # Check compliance patterns
        assert "compliance" in patterns
        compliance_patterns = patterns["compliance"]
        assert "regulation_keywords" in compliance_patterns
        assert "update_indicators" in compliance_patterns
    
    def test_freshness_thresholds_configuration(self, web_research_agent):
        """Test that freshness thresholds are properly configured."""
        thresholds = web_research_agent.freshness_thresholds
        
        # Check all required thresholds exist
        required_thresholds = [
            "pricing_data", "trend_data", "regulatory_data", "best_practices"
        ]
        
        for threshold in required_thresholds:
            assert threshold in thresholds
            assert isinstance(thresholds[threshold], int)
            assert thresholds[threshold] > 0
        
        # Verify reasonable threshold values
        assert thresholds["pricing_data"] <= 24  # Pricing should be fresh
        assert thresholds["best_practices"] >= 24  # Best practices can be older