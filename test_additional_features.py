#!/usr/bin/env python3
"""
Test script for Additional Features endpoints.
Tests all additional features to ensure they work and generate data from assessments.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000/api"
ASSESSMENT_ID = "68dbf9e9047dde3cf58186dd"
JWT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI2OGRhMzM0MTdmMjY2YjRmODRhYjA0MzIiLCJlbWFpbCI6ImxpdGVzaHBlcnVtYWxsYUBnbWFpbC5jb20iLCJmdWxsX25hbWUiOiJMaXRlc2ggUGVydW1hbGxhIiwiZXhwIjoxNzU5MTYwNDgxLCJpYXQiOjE3NTkxMzE2ODEsImlzcyI6ImluZnJhLW1pbmQiLCJhdWQiOiJpbmZyYS1taW5kLWFwaSIsInRva2VuX3R5cGUiOiJhY2Nlc3MiLCJqdGkiOiJXSmZuUTlYbmpHZy1GNFdQOU9lMl8wbmNHeXRsSFBUVUctUVJRc3BpT0tnIn0.Jf9qyX25tcrz-SnpsexVoxdSiLhd5WCMeQvkLB3-2mE"

# Test endpoints for each additional feature - NEW UNIFIED API
ENDPOINTS_TO_TEST = {
    "Performance Monitoring": f"/v1/features/assessment/{ASSESSMENT_ID}/performance",
    "Compliance": f"/v1/features/assessment/{ASSESSMENT_ID}/compliance",
    "Experiments": f"/v1/features/assessment/{ASSESSMENT_ID}/experiments",
    "Quality Metrics": f"/v1/features/assessment/{ASSESSMENT_ID}/quality",
    "Approval Workflows": f"/v1/features/assessment/{ASSESSMENT_ID}/approvals",
    "Budget Forecasting": f"/v1/features/assessment/{ASSESSMENT_ID}/budget",
    "Executive Dashboard": f"/v1/features/assessment/{ASSESSMENT_ID}/executive",
    "Impact Analysis": f"/v1/features/assessment/{ASSESSMENT_ID}/impact",
    "Rollback Plans": f"/v1/features/assessment/{ASSESSMENT_ID}/rollback",
    "Vendor Lock-in Analysis": f"/v1/features/assessment/{ASSESSMENT_ID}/vendor-lockin",
    "All Features (Combined)": f"/v1/features/assessment/{ASSESSMENT_ID}/all-features"
}


async def test_endpoint(session: aiohttp.ClientSession, name: str, endpoint: str) -> Dict[str, Any]:
    """Test a single endpoint."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        async with session.get(url, headers=headers) as response:
            status = response.status

            if status == 200:
                data = await response.json()
                # Check if data is meaningful (not just empty structure)
                has_data = bool(data and len(str(data)) > 100)

                return {
                    "name": name,
                    "status": "✅ SUCCESS",
                    "http_code": status,
                    "has_data": has_data,
                    "data_size": len(str(data)),
                    "message": "Endpoint working" if has_data else "⚠️  Endpoint returns empty data"
                }
            elif status == 404:
                return {
                    "name": name,
                    "status": "❌ NOT FOUND",
                    "http_code": status,
                    "has_data": False,
                    "message": "Endpoint does not exist or route not configured"
                }
            elif status == 401 or status == 403:
                return {
                    "name": name,
                    "status": "❌ AUTH ERROR",
                    "http_code": status,
                    "has_data": False,
                    "message": "Authentication/Authorization failed"
                }
            else:
                text = await response.text()
                return {
                    "name": name,
                    "status": "❌ ERROR",
                    "http_code": status,
                    "has_data": False,
                    "message": f"HTTP {status}: {text[:200]}"
                }

    except aiohttp.ClientConnectorError:
        return {
            "name": name,
            "status": "❌ CONNECTION ERROR",
            "http_code": 0,
            "has_data": False,
            "message": "Cannot connect to API server"
        }
    except Exception as e:
        return {
            "name": name,
            "status": "❌ EXCEPTION",
            "http_code": 0,
            "has_data": False,
            "message": str(e)
        }


async def main():
    """Run all endpoint tests."""
    print("=" * 80)
    print("TESTING ADDITIONAL FEATURES ENDPOINTS")
    print("=" * 80)
    print(f"Base URL: {BASE_URL}")
    print(f"Assessment ID: {ASSESSMENT_ID}")
    print("=" * 80)
    print()

    async with aiohttp.ClientSession() as session:
        tasks = [
            test_endpoint(session, name, endpoint)
            for name, endpoint in ENDPOINTS_TO_TEST.items()
        ]

        results = await asyncio.gather(*tasks)

        # Print results
        success_count = 0
        has_data_count = 0

        for result in results:
            print(f"\n{result['name']}")
            print(f"  Status: {result['status']}")
            print(f"  HTTP Code: {result['http_code']}")
            print(f"  Has Data: {result['has_data']}")
            if result.get('data_size'):
                print(f"  Data Size: {result['data_size']} bytes")
            print(f"  Message: {result['message']}")

            if result['http_code'] == 200:
                success_count += 1
                if result['has_data']:
                    has_data_count += 1

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total Endpoints: {len(ENDPOINTS_TO_TEST)}")
        print(f"Successful (200): {success_count}")
        print(f"With Data: {has_data_count}")
        print(f"Failed: {len(ENDPOINTS_TO_TEST) - success_count}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
