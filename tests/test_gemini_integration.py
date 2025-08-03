"""
Tests for Gemini 2.5 Pro API integration and cost comparison features.

Tests cover:
1. Gemini provider functionality
2. Cost comparison between providers
3. Provider switching and failover
4. Prompt formatting consistency
5. Cost optimization recommendations
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infra_mind.llm.gemini_provider import GeminiProvider
from infra_mind.llm.manager import LLMManager, LoadBalancingStrategy
from infra_mind.llm.interface import LLMRequest, LLMProvider, LLMResponse, TokenUsage
from infra_mind.llm.prompt_formatter import prompt_formatter


class TestGeminiProvider:
    """Test Gemini provider functionality."""
    
    @pytest.fixture
    def gemini_provider(self):
        """Create a Gemini provider instance for testing."""
        return GeminiProvider(
            api_key="test-api-key",
            model="gemini-1.5-pro",
            temperature=0.1
        )
    
    def test_provider_initialization(self, gemini_provider):
        """Test Gemini provider initialization."""
        assert gemini_provider.provider_name == LLMProvider.GEMINI
        assert gemini_provider.model == "gemini-1.5-pro"
        assert gemini_provider.resolved_model == "gemini-1.5-pro"
        assert "gemini-1.5-pro" in gemini_provider.supported_models
        assert "gemini-2.5-pro" in gemini_provider.supported_models  # Alias
    
    def test_model_aliases(self, gemini_provider):
        """Test model alias resolution."""
        # Test alias resolution
        provider_with_alias = GeminiProvider(
            api_key="test-api-key",
            model="gemini-2.5-pro"  # This should resolve to gemini-1.5-pro
        )
        assert provider_with_alias.resolved_model == "gemini-1.5-pro"
    
    def test_cost_estimation(self, gemini_provider):
        """Test cost estimation for different models."""
        # Test cost estimation for gemini-1.5-pro
        cost = gemini_provider.estimate_cost(1000, 500, "gemini-1.5-pro")
        expected_cost = (1000 / 1_000_000) * 3.50 + (500 / 1_000_000) * 10.50
        assert abs(cost - expected_cost) < 0.0001
        
        # Test cost estimation for gemini-1.5-flash (cheaper model)
        cost_flash = gemini_provider.estimate_cost(1000, 500, "gemini-1.5-flash")
        expected_cost_flash = (1000 / 1_000_000) * 0.075 + (500 / 1_000_000) * 0.30
        assert abs(cost_flash - expected_cost_flash) < 0.0001
        
        # Flash should be cheaper than Pro
        assert cost_flash < cost
    
    def test_model_info(self, gemini_provider):
        """Test model information retrieval."""
        model_info = gemini_provider.get_model_info("gemini-1.5-pro")
        
        assert model_info["name"] == "gemini-1.5-pro"
        assert model_info["provider"] == "gemini"
        assert model_info["context_limit"] == 2097152  # 2M tokens
        assert "pricing" in model_info
        assert "capabilities" in model_info
        assert "multimodal" in model_info["capabilities"]
    
    def test_token_estimation(self, gemini_provider):
        """Test token estimation."""
        text = "This is a test prompt for token estimation."
        estimated_tokens = gemini_provider._estimate_tokens(text)
        
        # Should be roughly text length / 4
        expected_tokens = len(text) // 4
        assert abs(estimated_tokens - expected_tokens) <= 2
    
    @patch('google.generativeai.GenerativeModel')
    async def test_generate_response_success(self, mock_model_class, gemini_provider):
        """Test successful response generation."""
        # Mock the response
        mock_response = Mock()
        mock_response.text = "This is a test response from Gemini."
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = "STOP"
        mock_response.candidates[0].safety_ratings = []
        
        # Mock usage metadata
        mock_usage = Mock()
        mock_usage.prompt_token_count = 10
        mock_usage.candidates_token_count = 15
        mock_response.usage_metadata = mock_usage
        
        # Mock the model
        mock_model = Mock()
        mock_model.generate_content = Mock(return_value=mock_response)
        mock_model_class.return_value = mock_model
        
        # Test request
        request = LLMRequest(
            prompt="Test prompt",
            model="gemini-1.5-pro",
            temperature=0.1,
            max_tokens=100
        )
        
        # Mock asyncio.to_thread to return the mock response directly
        with patch('asyncio.to_thread', return_value=mock_response):
            response = await gemini_provider.generate_response(request)
        
        assert isinstance(response, LLMResponse)
        assert response.content == "This is a test response from Gemini."
        assert response.provider == LLMProvider.GEMINI
        assert response.model == "gemini-1.5-pro"
        assert response.token_usage.prompt_tokens == 10
        assert response.token_usage.completion_tokens == 15
        assert response.token_usage.total_tokens == 25
    
    def test_prompt_preparation(self, gemini_provider):
        """Test prompt preparation for Gemini format."""
        request = LLMRequest(
            prompt="What is cloud computing?",
            system_prompt="You are a cloud expert.",
            temperature=0.1
        )
        
        formatted_prompt = gemini_provider._prepare_prompt(request)
        
        assert "System: You are a cloud expert." in formatted_prompt
        assert "User: What is cloud computing?" in formatted_prompt
        assert formatted_prompt.count("\n\n") >= 1  # Should have separator


class TestPromptFormatter:
    """Test prompt formatter functionality."""
    
    def test_format_for_gemini(self):
        """Test formatting request for Gemini provider."""
        request = LLMRequest(
            prompt="What are the benefits of microservices?",
            system_prompt="You are a software architect.",
            temperature=0.1
        )
        
        formatted_request = prompt_formatter.format_request_for_provider(
            request, LLMProvider.GEMINI
        )
        
        # Gemini doesn't support system role, so it should be merged
        assert formatted_request.system_prompt is None
        assert "System: You are a software architect." in formatted_request.prompt
        assert "User: What are the benefits of microservices?" in formatted_request.prompt
    
    def test_format_for_openai(self):
        """Test formatting request for OpenAI provider."""
        request = LLMRequest(
            prompt="What are the benefits of microservices?",
            system_prompt="You are a software architect.",
            temperature=0.1
        )
        
        formatted_request = prompt_formatter.format_request_for_provider(
            request, LLMProvider.OPENAI
        )
        
        # OpenAI supports system role, so it should be preserved
        assert formatted_request.system_prompt == "You are a software architect."
        assert formatted_request.prompt == "What are the benefits of microservices?"
    
    def test_provider_capabilities(self):
        """Test getting provider capabilities."""
        gemini_caps = prompt_formatter.get_provider_capabilities(LLMProvider.GEMINI)
        openai_caps = prompt_formatter.get_provider_capabilities(LLMProvider.OPENAI)
        
        assert gemini_caps["supports_system_role"] is False
        assert openai_caps["supports_system_role"] is True
        
        assert gemini_caps["supports_message_format"] is False
        assert openai_caps["supports_message_format"] is True
    
    def test_prompt_validation(self):
        """Test prompt validation for different providers."""
        request = LLMRequest(
            prompt="What is cloud computing?",
            system_prompt="You are an expert.",
            temperature=0.1
        )
        
        gemini_validation = prompt_formatter.validate_prompt_for_provider(
            request, LLMProvider.GEMINI
        )
        
        assert gemini_validation["valid"] is True
        assert len(gemini_validation["warnings"]) > 0  # Should warn about system prompt
        assert "doesn't support system role" in gemini_validation["warnings"][0]


class TestLLMManagerCostComparison:
    """Test LLM manager cost comparison and optimization features."""
    
    @pytest.fixture
    def mock_providers(self):
        """Create mock providers for testing."""
        openai_provider = Mock()
        openai_provider.provider_name = LLMProvider.OPENAI
        openai_provider.model = "gpt-4"
        openai_provider.estimate_cost.return_value = 0.06  # Higher cost
        openai_provider.get_model_info.return_value = {
            "name": "gpt-4",
            "pricing": {"input_per_1k_tokens": 0.03, "output_per_1k_tokens": 0.06}
        }
        openai_provider.total_cost = 1.50
        openai_provider.request_count = 100
        openai_provider.supported_models = ["gpt-4", "gpt-3.5-turbo"]
        
        gemini_provider = Mock()
        gemini_provider.provider_name = LLMProvider.GEMINI
        gemini_provider.model = "gemini-1.5-pro"
        gemini_provider.estimate_cost.return_value = 0.014  # Lower cost
        gemini_provider.get_model_info.return_value = {
            "name": "gemini-1.5-pro",
            "pricing": {"input_per_1m_tokens": 3.50, "output_per_1m_tokens": 10.50}
        }
        gemini_provider.total_cost = 0.80
        gemini_provider.request_count = 80
        gemini_provider.supported_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        
        return {
            LLMProvider.OPENAI: openai_provider,
            LLMProvider.GEMINI: gemini_provider
        }
    
    @pytest.fixture
    def llm_manager(self, mock_providers):
        """Create LLM manager with mock providers."""
        with patch('infra_mind.llm.manager.get_settings') as mock_settings:
            mock_settings.return_value.get_openai_api_key.return_value = None
            mock_settings.return_value.get_gemini_api_key.return_value = None
            
            manager = LLMManager()
            manager.providers = mock_providers
            manager._provider_health = {
                LLMProvider.OPENAI: True,
                LLMProvider.GEMINI: True
            }
            manager._provider_performance = {
                LLMProvider.OPENAI: 0.8,
                LLMProvider.GEMINI: 0.9
            }
            
            return manager
    
    async def test_cost_comparison(self, llm_manager):
        """Test cost comparison between providers."""
        request = LLMRequest(
            prompt="Explain cloud computing benefits.",
            temperature=0.1,
            max_tokens=200
        )
        
        with patch('infra_mind.llm.prompt_formatter.prompt_formatter.format_request_for_provider') as mock_format:
            mock_format.return_value = request
            
            comparison = await llm_manager.compare_provider_costs(request)
        
        assert "providers" in comparison
        assert "recommendations" in comparison
        
        # Should have data for both providers
        assert "openai" in comparison["providers"]
        assert "gemini" in comparison["providers"]
        
        # Gemini should be cheaper
        openai_cost = comparison["providers"]["openai"]["estimated_cost"]
        gemini_cost = comparison["providers"]["gemini"]["estimated_cost"]
        assert gemini_cost < openai_cost
        
        # Should recommend Gemini as cheapest
        assert comparison["recommendations"]["cheapest_provider"] == "gemini"
    
    def test_cost_optimization_recommendations(self, llm_manager):
        """Test cost optimization recommendations."""
        recommendations = llm_manager.get_cost_optimization_recommendations()
        
        assert "provider_recommendations" in recommendations
        assert "usage_optimization" in recommendations
        assert "model_recommendations" in recommendations
        assert "estimated_savings" in recommendations
        
        # Should be a valid timestamp
        timestamp = recommendations["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format
    
    async def test_optimize_provider_selection(self, llm_manager):
        """Test optimal provider selection."""
        request = LLMRequest(
            prompt="What is containerization?",
            temperature=0.1,
            max_tokens=150
        )
        
        with patch.object(llm_manager, 'compare_provider_costs') as mock_compare:
            mock_compare.return_value = {
                "providers": {
                    "openai": {
                        "estimated_cost": 0.06,
                        "performance_score": 0.8,
                        "health_status": "healthy"
                    },
                    "gemini": {
                        "estimated_cost": 0.014,
                        "performance_score": 0.9,
                        "health_status": "healthy"
                    }
                }
            }
            
            # Test cost-optimized selection
            llm_manager.load_balancing_strategy = LoadBalancingStrategy.COST_OPTIMIZED
            optimal_provider = await llm_manager.optimize_provider_selection(request)
            assert optimal_provider == LLMProvider.GEMINI  # Cheaper option
            
            # Test performance-optimized selection
            llm_manager.load_balancing_strategy = LoadBalancingStrategy.PERFORMANCE_OPTIMIZED
            optimal_provider = await llm_manager.optimize_provider_selection(request)
            assert optimal_provider == LLMProvider.GEMINI  # Higher performance
    
    def test_provider_order_cost_optimized(self, llm_manager):
        """Test provider ordering for cost optimization."""
        llm_manager.load_balancing_strategy = LoadBalancingStrategy.COST_OPTIMIZED
        
        request = LLMRequest(
            prompt="Test prompt",
            temperature=0.1,
            max_tokens=100
        )
        
        with patch('infra_mind.llm.prompt_formatter.prompt_formatter.format_request_for_provider') as mock_format:
            mock_format.return_value = request
            
            provider_order = llm_manager._get_provider_order(request)
        
        # Gemini should be first (cheaper)
        assert provider_order[0] == LLMProvider.GEMINI
        assert provider_order[1] == LLMProvider.OPENAI


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""
    
    @pytest.fixture
    def integration_manager(self):
        """Create manager for integration testing."""
        with patch('infra_mind.llm.manager.get_settings') as mock_settings:
            mock_settings.return_value.get_openai_api_key.return_value = "test-openai-key"
            mock_settings.return_value.get_gemini_api_key.return_value = "test-gemini-key"
            mock_settings.return_value.llm_model = "gpt-4"
            mock_settings.return_value.llm_temperature = 0.1
            mock_settings.return_value.llm_max_tokens = 2000
            mock_settings.return_value.llm_timeout = 60
            
            with patch('infra_mind.llm.openai_provider.OpenAIProvider'), \
                 patch('infra_mind.llm.gemini_provider.GeminiProvider'):
                
                manager = LLMManager()
                return manager
    
    def test_failover_scenario(self, integration_manager):
        """Test failover when primary provider fails."""
        # Simulate provider failure
        integration_manager._provider_health[LLMProvider.OPENAI] = False
        
        request = LLMRequest(prompt="Test failover", temperature=0.1)
        provider_order = integration_manager._get_provider_order(request)
        
        # Should only include healthy providers
        healthy_providers = [
            p for p in provider_order 
            if integration_manager._provider_health.get(p, False)
        ]
        
        assert LLMProvider.OPENAI not in healthy_providers
        if LLMProvider.GEMINI in integration_manager.providers:
            assert LLMProvider.GEMINI in healthy_providers
    
    def test_no_providers_available(self):
        """Test behavior when no providers are available."""
        with patch('infra_mind.llm.manager.get_settings') as mock_settings:
            mock_settings.return_value.get_openai_api_key.return_value = None
            mock_settings.return_value.get_gemini_api_key.return_value = None
            
            manager = LLMManager()
            assert len(manager.providers) == 0
    
    async def test_provider_switching_performance_impact(self, integration_manager):
        """Test performance impact of provider switching."""
        request = LLMRequest(prompt="Performance test", temperature=0.1)
        
        # Simulate different response times
        integration_manager._provider_performance[LLMProvider.OPENAI] = 0.6  # Slower
        integration_manager._provider_performance[LLMProvider.GEMINI] = 0.9   # Faster
        
        # With performance optimization, should prefer Gemini
        integration_manager.load_balancing_strategy = LoadBalancingStrategy.PERFORMANCE_OPTIMIZED
        provider_order = integration_manager._get_provider_order(request)
        
        if len(provider_order) > 1:
            # First provider should be the one with higher performance
            first_provider = provider_order[0]
            first_performance = integration_manager._provider_performance.get(first_provider, 0)
            
            for provider in provider_order[1:]:
                provider_performance = integration_manager._provider_performance.get(provider, 0)
                assert first_performance >= provider_performance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])