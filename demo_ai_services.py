#!/usr/bin/env python3
"""
AI Services Comparison Demo.

This script demonstrates how to compare AI/ML services across multiple cloud providers.
"""

import asyncio
import os
from dotenv import load_dotenv
from src.infra_mind.cloud import CloudProvider, UnifiedCloudClient


async def demo_ai_services_comparison():
    """Demonstrate AI/ML services comparison capabilities."""
    print("🤖 AI/ML Services Comparison Demo")
    print("=" * 50)
    print("This demo compares AI/ML services across AWS, Azure, and Google Cloud Platform.")
    print()

    # Load environment variables
    load_dotenv()

    # Initialize the unified cloud client
    client = UnifiedCloudClient(
        aws_region="us-east-1",
        azure_region="eastus",
        gcp_region="us-central1",
        # AWS credentials can be provided here or via environment variables
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        # Azure credentials
        azure_subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
        azure_client_id=os.getenv("AZURE_CLIENT_ID"),
        azure_client_secret=os.getenv("AZURE_CLIENT_SECRET"),
        # GCP credentials
        gcp_project_id=os.getenv("GCP_PROJECT_ID"),
        gcp_service_account_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    )

    print("🔍 Fetching AI/ML services from all providers...")
    print()

    # Get AI services from each provider
    aws_services = []
    azure_services = []
    gcp_services = []

    try:
        aws_result = await client.get_ai_services(provider=CloudProvider.AWS)
        if CloudProvider.AWS in aws_result:
            aws_services = aws_result[CloudProvider.AWS].services
    except Exception as e:
        print(f"❌ Error getting AWS AI services: {e}")

    try:
        azure_result = await client.get_ai_services(provider=CloudProvider.AZURE)
        if CloudProvider.AZURE in azure_result:
            azure_services = azure_result[CloudProvider.AZURE].services
    except Exception as e:
        print(f"❌ Error getting Azure AI services: {e}")

    try:
        gcp_result = await client.get_ai_services(provider=CloudProvider.GCP)
        if CloudProvider.GCP in gcp_result:
            gcp_services = gcp_result[CloudProvider.GCP].services
    except Exception as e:
        print(f"❌ Error getting GCP AI services: {e}")

    print("🔍 Provider AI/ML Services Summary:")
    print("-" * 40)
    print(f"AWS: {len(aws_services)} AI/ML services")
    print(f"Azure: {len(azure_services)} AI/ML services")
    print(f"GCP: {len(gcp_services)} AI/ML services")

    # Show sample services from each provider
    print("\n🤖 Sample AI/ML Services by Provider:")
    print("-" * 40)

    if aws_services:
        print("\n🟠 AWS AI/ML Services (Sample):")
        for service in aws_services[:5]:  # Show first 5 services
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.service_name}: {price_info}")
            print(f"    {service.description}")

    if azure_services:
        print("\n🔵 Azure AI/ML Services (Sample):")
        for service in azure_services[:5]:  # Show first 5 services
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.service_name}: {price_info}")
            print(f"    {service.description}")

    if gcp_services:
        print("\n🟢 GCP AI/ML Services (Sample):")
        for service in gcp_services[:5]:  # Show first 5 services
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.service_name}: {price_info}")
            print(f"    {service.description}")

    # Compare specific service types
    print("\n🔄 Service Type Comparison:")
    print("-" * 40)

    # Text generation models
    print("\n📝 Text Generation Models:")
    text_gen_services = []
    
    for service in aws_services:
        if "text" in service.service_name.lower() or "gpt" in service.service_name.lower() or "claude" in service.service_name.lower():
            text_gen_services.append(service)
    
    for service in azure_services:
        if "gpt" in service.service_name.lower() or "text" in service.service_name.lower():
            text_gen_services.append(service)
    
    for service in gcp_services:
        if "text" in service.service_name.lower() or "bison" in service.service_name.lower():
            text_gen_services.append(service)
    
    if text_gen_services:
        for service in text_gen_services[:3]:  # Show top 3
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.provider.name}: {service.service_name} - {price_info}")

    # Computer vision services
    print("\n👁️ Computer Vision Services:")
    vision_services = []
    
    for service in aws_services + azure_services + gcp_services:
        if any(keyword in service.service_name.lower() for keyword in ["vision", "rekognition", "computer", "image"]):
            vision_services.append(service)
    
    if vision_services:
        for service in vision_services[:3]:  # Show top 3
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.provider.name}: {service.service_name} - {price_info}")

    # Speech services
    print("\n🎤 Speech Services:")
    speech_services = []
    
    for service in aws_services + azure_services + gcp_services:
        if any(keyword in service.service_name.lower() for keyword in ["speech", "polly", "text-to-speech", "voice"]):
            speech_services.append(service)
    
    if speech_services:
        for service in speech_services[:3]:  # Show top 3
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.provider.name}: {service.service_name} - {price_info}")

    # ML Training services
    print("\n🏋️ ML Training Services:")
    training_services = []
    
    for service in aws_services + azure_services + gcp_services:
        if any(keyword in service.service_name.lower() for keyword in ["training", "sagemaker", "automl", "vertex"]):
            training_services.append(service)
    
    if training_services:
        for service in training_services[:3]:  # Show top 3
            price_info = f"${service.hourly_price:.4f}/{service.pricing_unit}" if service.hourly_price else "Pricing varies"
            print(f"  • {service.provider.name}: {service.service_name} - {price_info}")

    # Find cheapest services by category
    print("\n💰 Most Cost-Effective Options:")
    print("-" * 40)

    all_services = aws_services + azure_services + gcp_services
    
    # Group by service type and find cheapest
    service_categories = {
        "Text Generation": ["text", "gpt", "claude", "bison"],
        "Computer Vision": ["vision", "rekognition", "computer", "image"],
        "Speech Processing": ["speech", "polly", "text-to-speech"],
        "ML Training": ["training", "sagemaker", "automl", "vertex"]
    }
    
    for category, keywords in service_categories.items():
        category_services = [
            s for s in all_services 
            if any(keyword in s.service_name.lower() for keyword in keywords) 
            and s.hourly_price is not None
        ]
        
        if category_services:
            cheapest = min(category_services, key=lambda x: x.hourly_price)
            print(f"{category}: {cheapest.provider.name} {cheapest.service_name} - ${cheapest.hourly_price:.4f}/{cheapest.pricing_unit}")

    print("\n✅ AI/ML Services Comparison Complete!")
    print("=" * 50)
    print("Key Insights:")
    print("• Each cloud provider offers unique AI/ML services with different pricing models")
    print("• AWS Bedrock provides access to multiple foundation models")
    print("• Azure OpenAI offers enterprise-grade GPT models")
    print("• GCP Vertex AI provides comprehensive ML platform capabilities")
    print("• Consider your specific use case, compliance needs, and existing infrastructure")
    print("• Pricing varies significantly between providers and service types")


if __name__ == "__main__":
    asyncio.run(demo_ai_services_comparison())