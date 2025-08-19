#!/usr/bin/env python3
"""
Test script to verify LLM configuration and API connectivity.
"""

import asyncio
import os
import logging
from src.infra_mind.llm.manager import LLMManager
from src.infra_mind.llm.interface import LLMRequest
from src.infra_mind.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_configuration():
    """Test LLM configuration and connectivity."""
    
    logger.info("🧪 Testing LLM configuration...")
    
    # Get configuration
    settings = get_settings()
    
    # Check API keys
    logger.info("🔑 Checking API key configuration:")
    
    openai_key = settings.openai_api_key
    if openai_key:
        key_preview = f"{str(openai_key)[:10]}...{str(openai_key)[-4:]}" if len(str(openai_key)) > 14 else "***"
        logger.info(f"  ✅ OpenAI API Key: {key_preview}")
    else:
        logger.error("  ❌ OpenAI API Key: Not configured")
    
    gemini_key = settings.gemini_api_key
    if gemini_key:
        key_preview = f"{str(gemini_key)[:10]}...{str(gemini_key)[-4:]}" if len(str(gemini_key)) > 14 else "***"
        logger.info(f"  ✅ Gemini API Key: {key_preview}")
    else:
        logger.info("  ⚠️  Gemini API Key: Not configured (optional)")
    
    anthropic_key = settings.anthropic_api_key
    if anthropic_key:
        key_preview = f"{str(anthropic_key)[:10]}...{str(anthropic_key)[-4:]}" if len(str(anthropic_key)) > 14 else "***"
        logger.info(f"  ✅ Anthropic API Key: {key_preview}")
    else:
        logger.info("  ⚠️  Anthropic API Key: Not configured (optional)")
    
    # Check LLM provider configuration
    logger.info(f"🤖 LLM Provider: {settings.llm_provider}")
    logger.info(f"🎯 LLM Model: {settings.llm_model}")
    logger.info(f"🌡️  Temperature: {getattr(settings, 'llm_temperature', 0.1)}")
    
    # Check Azure OpenAI configuration
    if settings.llm_provider == "azure_openai":
        azure_creds = settings.get_azure_openai_credentials()
        logger.info(f"🏢 Azure OpenAI Endpoint: {azure_creds['endpoint']}")
        logger.info(f"🚀 Azure OpenAI Deployment: {azure_creds['deployment']}")
        logger.info(f"📅 Azure OpenAI API Version: {azure_creds['api_version']}")
    
    # Test LLM Manager initialization
    try:
        logger.info("⚙️  Initializing LLM Manager...")
        llm_manager = LLMManager()
        logger.info("✅ LLM Manager initialized successfully")
        
        # Test a simple request
        if openai_key or (settings.llm_provider == "azure_openai" and settings.get_azure_openai_api_key()):
            logger.info("🚀 Testing LLM API call...")
            
            test_request = LLMRequest(
                prompt="Hello! Please respond with just 'API_TEST_SUCCESS' if you can see this message.",
                model=settings.llm_model,
                temperature=0.1,
                max_tokens=50
            )
            
            try:
                response = await llm_manager.generate_response(test_request)
                
                if response and response.content:
                    logger.info(f"✅ LLM API call successful!")
                    logger.info(f"📝 Response: {response.content[:100]}...")
                    logger.info(f"💰 Cost: ${response.cost:.4f}")
                    logger.info(f"🏷️  Provider: {response.provider}")
                    return True
                else:
                    logger.error("❌ LLM API call returned empty response")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ LLM API call failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
        else:
            logger.warning("⚠️  Skipping API test - no OpenAI key configured")
            return False
            
    except Exception as e:
        logger.error(f"❌ LLM Manager initialization failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_llm_configuration())
    if success:
        print("🎉 LLM configuration test PASSED! Agents should now be able to generate recommendations.")
    else:
        print("💥 LLM configuration test FAILED! Check API keys and configuration.")