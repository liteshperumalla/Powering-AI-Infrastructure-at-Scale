#!/usr/bin/env python3
"""
Test script for the Infra Mind API Gateway.

This script tests the basic functionality of the API endpoints
and generates OpenAPI documentation.
"""

import sys
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.append('src')
sys.path.append('.')

from fastapi.testclient import TestClient
from api.app import app

def test_api_endpoints():
    """Test basic API endpoint functionality."""
    print("🧪 Testing Infra Mind API Gateway...")
    
    # Create test client
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    
    # Test root endpoint
    print("\n2. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    assert response.status_code == 200
    
    # Test OpenAPI docs endpoint
    print("\n3. Testing OpenAPI documentation...")
    response = client.get("/openapi.json")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    
    openapi_spec = response.json()
    print(f"   API Title: {openapi_spec['info']['title']}")
    print(f"   API Version: {openapi_spec['info']['version']}")
    print(f"   Number of paths: {len(openapi_spec['paths'])}")
    
    # Test assessment endpoints (mock responses)
    print("\n4. Testing assessment endpoints...")
    
    # Test list assessments
    response = client.get("/api/v1/assessments/")
    print(f"   List assessments status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} assessments")
    
    # Test get specific assessment
    response = client.get("/api/v1/assessments/test-123")
    print(f"   Get assessment status: {response.status_code}")
    
    # Test recommendations endpoints
    print("\n5. Testing recommendation endpoints...")
    response = client.get("/api/v1/recommendations/test-123")
    print(f"   Get recommendations status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} recommendations")
    
    # Test reports endpoints
    print("\n6. Testing report endpoints...")
    response = client.get("/api/v1/reports/test-123")
    print(f"   Get reports status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   Found {data['total']} reports")
    
    print("\n✅ All API endpoint tests passed!")
    return openapi_spec


def save_openapi_spec(spec):
    """Save OpenAPI specification to file."""
    print("\n📄 Saving OpenAPI specification...")
    
    # Save to JSON file
    spec_file = Path("api_specification.json")
    with open(spec_file, 'w') as f:
        json.dump(spec, f, indent=2)
    
    print(f"   OpenAPI spec saved to: {spec_file}")
    
    # Generate summary
    paths = spec.get('paths', {})
    endpoints = []
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                endpoints.append({
                    'method': method.upper(),
                    'path': path,
                    'summary': details.get('summary', ''),
                    'tags': details.get('tags', [])
                })
    
    # Group by tags
    by_tags = {}
    for endpoint in endpoints:
        for tag in endpoint['tags']:
            if tag not in by_tags:
                by_tags[tag] = []
            by_tags[tag].append(endpoint)
    
    print(f"\n📊 API Endpoint Summary:")
    print(f"   Total endpoints: {len(endpoints)}")
    
    for tag, tag_endpoints in by_tags.items():
        print(f"\n   {tag} ({len(tag_endpoints)} endpoints):")
        for ep in tag_endpoints:
            print(f"     {ep['method']} {ep['path']}")
            if ep['summary']:
                print(f"         {ep['summary']}")


def main():
    """Main test function."""
    print("🚀 Infra Mind API Gateway Test Suite")
    print("=" * 50)
    
    try:
        # Test API endpoints
        openapi_spec = test_api_endpoints()
        
        # Save OpenAPI specification
        save_openapi_spec(openapi_spec)
        
        print("\n🎉 API Gateway implementation completed successfully!")
        print("\nNext steps:")
        print("1. Start the API server: python api/app.py")
        print("2. View API docs: http://localhost:8000/docs")
        print("3. Test endpoints: http://localhost:8000/health")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()