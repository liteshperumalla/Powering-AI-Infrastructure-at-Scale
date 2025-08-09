#!/usr/bin/env python3
"""
Test script to verify the actual reports API response format
"""

import asyncio
import aiohttp
import json
import os

API_BASE_URL = "http://localhost:8000/api/v1"

async def test_reports_api():
    """Test the reports API endpoints directly"""
    
    print("🔍 Testing Reports API")
    print("=" * 40)
    
    async with aiohttp.ClientSession() as session:
        try:
            # First, get all assessments to find report IDs
            print("\n1. Fetching assessments...")
            async with session.get(f"{API_BASE_URL}/assessments/") as response:
                if response.status == 200:
                    assessments_data = await response.json()
                    assessments = assessments_data.get('assessments', [])
                    print(f"✅ Found {len(assessments)} assessments")
                    
                    for i, assessment in enumerate(assessments):
                        print(f"  {i+1}. {assessment.get('title', 'No title')} - {assessment.get('status', 'Unknown')} - Progress: {assessment.get('progress_percentage', 0)}%")
                else:
                    print(f"❌ Failed to fetch assessments: {response.status}")
                    return
            
            # Test getting reports for each assessment
            print("\n2. Fetching reports for each assessment...")
            all_reports = []
            
            for assessment in assessments:
                assessment_id = assessment.get('id')
                if not assessment_id:
                    continue
                    
                print(f"\n   Testing reports for assessment: {assessment_id}")
                async with session.get(f"{API_BASE_URL}/reports/{assessment_id}") as response:
                    if response.status == 200:
                        reports_data = await response.json()
                        reports = reports_data.get('reports', [])
                        print(f"   ✅ Found {len(reports)} reports")
                        
                        for report in reports:
                            print(f"     - {report.get('id', 'No ID')}: {report.get('title', 'No title')} ({report.get('status', 'No status')})")
                            # Add assessment_id to report for frontend compatibility
                            report['assessmentId'] = assessment_id
                            all_reports.append(report)
                    else:
                        print(f"   ❌ Failed to fetch reports for assessment {assessment_id}: {response.status}")
            
            # Print detailed information about the reports structure
            print(f"\n3. Report Structure Analysis")
            print(f"   Total reports found: {len(all_reports)}")
            
            if all_reports:
                sample_report = all_reports[0]
                print(f"\n   Sample report structure:")
                print(json.dumps(sample_report, indent=2, default=str))
                
                print(f"\n   Report field mapping needed:")
                backend_fields = list(sample_report.keys())
                frontend_expected = ['id', 'title', 'assessmentId', 'generatedDate', 'status', 'sections', 
                                   'keyFindings', 'recommendations', 'estimatedSavings', 'complianceScore', 'exportFormats']
                
                print(f"   Backend fields: {backend_fields}")
                print(f"   Frontend expects: {frontend_expected}")
                
                # Check field mappings
                mappings = {
                    'generated_at': 'generatedDate',
                    'estimated_savings': 'estimatedSavings', 
                    'key_findings': 'keyFindings',
                    'compliance_score': 'complianceScore',
                    'export_formats': 'exportFormats'
                }
                
                missing_fields = []
                for field in frontend_expected:
                    backend_field = field
                    # Check if we need to map snake_case to camelCase
                    for backend_key, frontend_key in mappings.items():
                        if field == frontend_key and backend_key in sample_report:
                            backend_field = backend_key
                            break
                    
                    if backend_field not in sample_report and field not in sample_report:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"   ⚠️  Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ All required fields present")
            
        except Exception as e:
            print(f"❌ Error testing API: {str(e)}")

async def main():
    await test_reports_api()

if __name__ == "__main__":
    asyncio.run(main())