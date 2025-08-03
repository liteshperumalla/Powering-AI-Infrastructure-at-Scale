"""
Tests for OpenAI LLM integration.

Comprehensive tests for real OpenAI API integration including
token usage tracking, cost monitoring, and response validation.
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone

from src.infra_mind.llm.interface import (
    LLMRequest, 
    LLMResponse, 
    TokenUsage, 
    LLMProvider,
    LLMError,
    LLMAuthenticationError,
    LLMRateLimitError
)
from src.infra_mind.llm.openai_provider import OpenAIProvider
from src.infra_mind.llm.manager import LLMManager
from src.infra_mind.llm.cost_tracker import CostTracker
from src.infra_mind.llm.response_validator import ResponseValidator


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""
    
    @pytest.fixture
    def mock_api_key(self):
        """Mock API key for testing."""
        return "sk-test-key-12345"
    
    @pytest.fixture
    def openai_provider(self, mock_api_key):
        """Create OpenAI provider instance for testing."""
        return OpenAIProvider(api_key=mock_api_key, model="gpt-3.5-turbo")
    
    def test_provider_initialization(self, openai_provider):
        """Test provider initialization."""
        assert openai_provider.provider_name == LLMProvider.OPENAI
        assert openai_provider.model == "gpt-3.5-turbo"
        assert "gpt-3.5-turbo" in openai_provider.supported_models
        assert openai_provider.total_tokens_used == 0
        assert openai_provider.total_cost == 0.0
    
    def test_cost_estimation(self, openai_provider):
        """Test cost estimation for different models."""
        # Test GPT-3.5-turbo pricing
        cost = openai_provider.estimate_cost(1000, 500, "gpt-3.5-turbo")
        expected_cost = (1000 / 1000 * 0.0015) + (500 / 1000 * 0.002)
        assert abs(cost - expected_cost) < 0.0001
        
        # Test GPT-4 pricing
        cost = openai_provider.estimate_cost(1000, 500, "gpt-4")
        expected_cost = (1000 / 1000 * 0.03) + (500 / 1000 * 0.06)
        assert abs(cost - expected_cost) < 0.0001
    
    def test_model_info(self, openai_provider):
        """Test model information retrieval."""
        model_info = openai_provider.get_model_info("gpt-3.5-turbo")
        
        assert model_info["name"] == "gpt-3.5-turbo"
        assert model_info["provider"] == "openai"
        assert "context_limit" in model_info
        assert "pricing" in model_info
        assert model_info["pricing"]["currency"] == "USD"
    
    @pytest.mark.asyncio
    async def test_api_key_validation_mock(self, openai_provider):
        """Test API key validation with mocked response."""
        with patch.object(openai_provider.client.chat.completions, 'create') as mock_create:
            # Mock successful response
            mock_create.return_value = Mock()
            
            is_valid = await openai_provider.validate_api_key()
            assert is_valid is True
            
            # Mock authentication error
            mock_create.side_effect = Exception("authentication failed")
            is_valid = await openai_provider.validate_api_key()
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_generate_response_mock(self, openai_provider):
        """Test response generation with mocked OpenAI API."""
        # Mock OpenAI response
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "This is a test response."
        mock_completion.choices[0].finish_reason = "stop"
        mock_completion.usage = Mock()
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 5
        mock_completion.usage.total_tokens = 15
        
        with patch.object(openai_provider.client.chat.completions, 'create') as mock_create:
            mock_create.return_value = mock_completion
            
            request = LLMRequest(
                prompt="Test prompt",
                model="gpt-3.5-turbo",
                temperature=0.7,
                max_tokens=100
            )
            
            response = await openai_provider.generate_response(request)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "This is a test response."
            assert response.model == "gpt-3.5-turbo"
            assert response.provider == LLMProvider.OPENAI
            assert response.token_usage.total_tokens == 15
            assert response.token_usage.estimated_cost > 0
            assert response.is_valid
    
    @pytest.mark.asyncio
    async def test_error_handling(self, openai_provider):
        """Test error handling for different API errors."""
        request = LLMRequest(prompt="Test prompt", model="gpt-3.5-turbo")
        
        with patch.object(openai_provider.client.chat.completions, 'create') as mock_create:
            # Test authentication error
            mock_create.side_effect = Exception("authentication failed")
            
            with pytest.raises(LLMAuthenticationError):
                await openai_provider.generate_response(request)
            
            # Test rate limit error
            mock_create.side_effect = Exception("rate_limit exceeded")
            
            with pytest.raises(LLMRateLimitError):
                await openai_provider.generate_response(request)
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, openai_provider):
        """Test retry mechanism with exponential backoff."""
        request = LLMRequest(prompt="Test prompt", model="gpt-3.5-turbo")
        
        # Mock successful response after retries
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.content = "Success after retry"
        mock_completion.choices[0].finish_reason = "stop"
        mock_completion.usage = Mock()
        mock_completion.usage.prompt_tokens = 10
        mock_completion.usage.completion_tokens = 5
        mock_completion.usage.total_tokens = 15
        
        with patch.object(openai_provider.client.chat.completions, 'create') as mock_create:
            # Fail first two attempts, succeed on third
            mock_create.side_effect = [
                Exception("temporary error"),
                Exception("temporary error"),
                mock_completion
            ]
            
            response = await openai_provider.generate_response(request)
            
            assert response.content == "Success after retry"
            assert mock_create.call_count == 3
    
    def test_usage_statistics(self, openai_provider):
        """Test usage statistics tracking."""
        # Simulate some usage
        openai_provider._total_tokens_used = 1000
        openai_provider._total_cost = 0.05
        openai_provider._request_count = 5
        
        stats = openai_provider.get_usage_stats()
        
        assert stats["provider"] == "openai"
        assert stats["total_requests"] == 5
        assert stats["total_tokens"] == 1000
        assert stats["total_cost"] == 0.05
        assert stats["average_tokens_per_request"] == 200.0
        assert stats["average_cost_per_request"] == 0.01


class TestLLMManager:
    """Test LLM manager functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock()
        settings.get_openai_api_key.return_value = "sk-test-key"
        settings.llm_model = "gpt-3.5-turbo"
        settings.llm_temperature = 0.7
        settings.llm_max_tokens = 2000
        settings.llm_timeout = 60
        return settings
    
    @pytest.fixture
    def llm_manager(self, mock_settings):
        """Create LLM manager for testing."""
        with patch('src.infra_mind.llm.manager.get_settings', return_value=mock_settings):
            return LLMManager()
    
    def test_manager_initialization(self, llm_manager):
        """Test LLM manager initialization."""
        assert isinstance(llm_manager.cost_tracker, CostTracker)
        assert isinstance(llm_manager.response_validator, ResponseValidator)
        assert len(llm_manager.providers) > 0  # Should have OpenAI provider
    
    @pytest.mark.asyncio
    async def test_generate_response_with_validation(self, llm_manager):
        """Test response generation with validation."""
        # Mock provider response
        mock_response = LLMResponse(
            content="This is a comprehensive test response with good structure.",
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            token_usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=15,
                total_tokens=25,
                estimated_cost=0.001,
                model="gpt-3.5-turbo",
                provider=LLMProvider.OPENAI
            ),
            response_time=1.5
        )
        
        # Mock the provider's generate_response method
        for provider in llm_manager.providers.values():
            provider.generate_response = AsyncMock(return_value=mock_response)
        
        request = LLMRequest(
            prompt="Generate a test response",
            model="gpt-3.5-turbo"
        )
        
        response = await llm_manager.generate_response(request, agent_name="test_agent")
        
        assert response.content == mock_response.content
        assert "validation" in response.metadata
        assert response.metadata["validation"]["is_valid"]
    
    @pytest.mark.asyncio
    async def test_provider_failover(self, llm_manager):
        """Test failover between providers."""
        request = LLMRequest(prompt="Test failover", model="gpt-3.5-turbo")
        
        # Mock first provider to fail, second to succeed
        providers = list(llm_manager.providers.values())
        if len(providers) >= 1:
            providers[0].generate_response = AsyncMock(side_effect=Exception("Provider 1 failed"))
            
            # If we only have one provider, the test will expect an error
            if len(providers) == 1:
                with pytest.raises(LLMError):
                    await llm_manager.generate_response(request)
            else:
                # Mock second provider success
                mock_response = LLMResponse(
                    content="Failover success",
                    model="gpt-3.5-turbo",
                    provider=LLMProvider.OPENAI,
                    token_usage=TokenUsage(10, 5, 15, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
                    response_time=1.0
                )
                providers[1].generate_response = AsyncMock(return_value=mock_response)
                
                response = await llm_manager.generate_response(request)
                assert response.content == "Failover success"
    
    def test_provider_statistics(self, llm_manager):
        """Test provider statistics collection."""
        stats = llm_manager.get_provider_stats()
        
        assert "total_providers" in stats
        assert "healthy_providers" in stats
        assert "load_balancing_strategy" in stats
        assert "providers" in stats
        
        for provider_stats in stats["providers"].values():
            assert "type" in provider_stats
            assert "healthy" in provider_stats
            assert "performance_score" in provider_stats
            assert "usage" in provider_stats


class TestCostTracker:
    """Test cost tracking functionality."""
    
    @pytest.fixture
    def cost_tracker(self):
        """Create cost tracker for testing."""
        return CostTracker()
    
    def test_usage_tracking(self, cost_tracker):
        """Test usage tracking."""
        token_usage = TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost=0.005,
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI
        )
        
        cost_tracker.track_usage(token_usage, "test_agent", "req_123")
        
        assert len(cost_tracker.cost_entries) == 1
        entry = cost_tracker.cost_entries[0]
        assert entry.agent_name == "test_agent"
        assert entry.total_tokens == 150
        assert entry.cost == 0.005
    
    def test_cost_summary(self, cost_tracker):
        """Test cost summary generation."""
        # Add some test data
        for i in range(5):
            token_usage = TokenUsage(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
                estimated_cost=0.005,
                model="gpt-3.5-turbo",
                provider=LLMProvider.OPENAI
            )
            cost_tracker.track_usage(token_usage, f"agent_{i}", f"req_{i}")
        
        summary = cost_tracker.get_cost_summary("daily")
        
        assert summary.total_cost == 0.025  # 5 * 0.005
        assert summary.total_tokens == 750  # 5 * 150
        assert summary.total_requests == 5
        assert "openai" in summary.provider_breakdown
    
    def test_optimization_recommendations(self, cost_tracker):
        """Test cost optimization recommendations."""
        # Add high-cost usage data
        for i in range(10):
            token_usage = TokenUsage(
                prompt_tokens=2000,
                completion_tokens=1000,
                total_tokens=3000,
                estimated_cost=0.1,  # High cost
                model="gpt-4",  # Expensive model
                provider=LLMProvider.OPENAI
            )
            cost_tracker.track_usage(token_usage, "expensive_agent", f"req_{i}")
        
        recommendations = cost_tracker.get_cost_optimization_recommendations()
        
        assert len(recommendations) > 0
        # Should recommend model optimization due to expensive GPT-4 usage
        model_rec = next((r for r in recommendations if r["type"] == "model_optimization"), None)
        assert model_rec is not None


class TestResponseValidator:
    """Test response validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create response validator for testing."""
        return ResponseValidator()
    
    def test_basic_validation(self, validator):
        """Test basic response validation."""
        # Valid response
        response = LLMResponse(
            content="This is a well-structured response with complete sentences. It provides valuable information.",
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            token_usage=TokenUsage(10, 20, 30, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
            response_time=1.0
        )
        
        result = validator.validate_response(response)
        
        assert result.is_valid
        assert result.quality_score > 0.5
        assert not result.has_errors
    
    def test_empty_response_validation(self, validator):
        """Test validation of empty response."""
        response = LLMResponse(
            content="",
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            token_usage=TokenUsage(10, 0, 10, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
            response_time=1.0
        )
        
        result = validator.validate_response(response)
        
        assert not result.is_valid
        assert result.has_errors
        assert any(issue.severity.value == "critical" for issue in result.issues)
    
    def test_business_logic_validation(self, validator):
        """Test business logic validation for different agents."""
        # CTO agent response without business terms
        response = LLMResponse(
            content="Technical implementation details without business context.",
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            token_usage=TokenUsage(10, 15, 25, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
            response_time=1.0
        )
        
        result = validator.validate_response(
            response,
            context={"agent_name": "CTO Agent"}
        )
        
        # Should have warning about lack of business terms
        business_warnings = [
            issue for issue in result.issues 
            if issue.category == "business_logic"
        ]
        assert len(business_warnings) > 0
    
    def test_custom_validator(self, validator):
        """Test custom validation rules."""
        def custom_rule(content: str):
            if "forbidden_word" in content.lower():
                from src.infra_mind.llm.response_validator import ValidationIssue, ValidationSeverity
                return ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="custom",
                    message="Contains forbidden word",
                    suggestion="Remove forbidden content"
                )
            return None
        
        validator.add_custom_validator(custom_rule)
        
        response = LLMResponse(
            content="This response contains a forbidden_word that should be flagged.",
            model="gpt-3.5-turbo",
            provider=LLMProvider.OPENAI,
            token_usage=TokenUsage(10, 15, 25, 0.001, "gpt-3.5-turbo", LLMProvider.OPENAI),
            response_time=1.0
        )
        
        result = validator.validate_response(response)
        
        custom_issues = [issue for issue in result.issues if issue.category == "custom"]
        assert len(custom_issues) == 1
        assert custom_issues[0].message == "Contains forbidden word"


@pytest.mark.integration
class TestRealOpenAIIntegration:
    """
    Integration tests with real OpenAI API.
    
    These tests require a valid OpenAI API key and will make real API calls.
    They should be run sparingly and only when testing the actual integration.
    """
    
    @pytest.fixture
    def real_api_key(self):
        """Get real API key from environment."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set - skipping real API tests")
        return api_key
    
    @pytest.fixture
    def real_provider(self, real_api_key):
        """Create provider with real API key."""
        return OpenAIProvider(api_key=real_api_key, model="gpt-3.5-turbo")
    
    @pytest.mark.asyncio
    async def test_real_api_key_validation(self, real_provider):
        """Test API key validation with real API."""
        is_valid = await real_provider.validate_api_key()
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_real_response_generation(self, real_provider):
        """Test response generation with real API."""
        request = LLMRequest(
            prompt="Say 'Hello, World!' in exactly those words.",
            model="gpt-3.5-turbo",
            temperature=0.0,
            max_tokens=10
        )
        
        response = await real_provider.generate_response(request)
        
        assert isinstance(response, LLMResponse)
        assert response.is_valid
        assert len(response.content) > 0
        assert response.token_usage.total_tokens > 0
        assert response.token_usage.estimated_cost > 0
        assert response.response_time > 0
        
        # Verify cost calculation
        expected_cost = real_provider.estimate_cost(
            response.token_usage.prompt_tokens,
            response.token_usage.completion_tokens,
            response.model
        )
        assert abs(response.token_usage.estimated_cost - expected_cost) < 0.0001
    
    @pytest.mark.asyncio
    async def test_real_model_availability(self, real_provider):
        """Test model availability with real API."""
        models = await real_provider.get_available_models()
        
        assert len(models) > 0
        assert any(model["name"] == "gpt-3.5-turbo" for model in models)
    
    @pytest.mark.asyncio
    async def test_real_connection_test(self, real_provider):
        """Test connection diagnostics with real API."""
        test_results = await real_provider.test_connection()
        
        assert test_results["provider"] == "openai"
        assert test_results["overall_status"] == "healthy"
        assert test_results["tests"]["api_key_validation"]["status"] == "pass"
        assert test_results["tests"]["generation_test"]["status"] == "pass"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])