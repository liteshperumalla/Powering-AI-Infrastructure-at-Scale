#!/usr/bin/env python3
"""
Check reports and data accuracy issues.
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def check_reports_and_data():
    client = AsyncIOMotorClient('mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    db = client.get_database('infra_mind')
    
    print('🔍 CHECKING REPORTS AND DATA ACCURACY')
    print('=' * 60)
    
    # Check reports collection
    reports = await db.reports.find({}).to_list(length=None)
    print(f'📄 Total reports in database: {len(reports)}')
    
    if reports:
        for report in reports:
            print(f'  Report: {report.get("title", "Unknown")}')
            print(f'    Assessment ID: {report.get("assessment_id", "None")}')
            print(f'    User ID: {report.get("user_id", "None")}')
            print(f'    Status: {report.get("status", "Unknown")}')
            print(f'    Created: {report.get("created_at", "Unknown")}')
            print()
    else:
        print('  ❌ No reports found in database!')
    
    # Check main user
    main_user = await db.users.find_one({'email': 'liteshperumalla@gmail.com'})
    main_user_id = str(main_user['_id'])
    print(f'👤 Main user ID: {main_user_id}')
    
    # Check assessments and their detailed data
    assessments = await db.assessments.find({'user_id': main_user_id}).to_list(length=None)
    print(f'\n📋 ASSESSMENT DATA ACCURACY CHECK:')
    print(f'Found {len(assessments)} assessments')
    
    for i, assessment in enumerate(assessments, 1):
        print(f'\n📊 Assessment {i}: {assessment.get("title", "Unknown")}')
        print(f'  ID: {assessment["_id"]}')
        print(f'  Status: {assessment.get("status", "unknown")}')
        print(f'  Progress: {assessment.get("completion_percentage", 0)}%')
        
        # Check if assessment has business/technical requirements
        bus_req = assessment.get('business_requirements', {})
        tech_req = assessment.get('technical_requirements', {})
        print(f'  Business Req: {"Yes" if bus_req else "No"} ({len(str(bus_req))} chars)')
        print(f'  Technical Req: {"Yes" if tech_req else "No"} ({len(str(tech_req))} chars)')
        
        # Check recommendations for this assessment
        recs = await db.recommendations.find({'assessment_id': str(assessment['_id'])}).to_list(length=None)
        print(f'  Recommendations: {len(recs)}')
        
        for j, rec in enumerate(recs, 1):
            print(f'    {j}. {rec.get("title", "Unknown")} ({rec.get("agent_name", "Unknown agent")})')
            
            # Check if recommendation has actual data vs mock data
            cost_estimates = rec.get('cost_estimates', {})
            recommendation_data = rec.get('recommendation_data', {})
            
            if cost_estimates:
                monthly_cost = cost_estimates.get('monthly_cost', 0)
                print(f'       💰 Monthly Cost: ${monthly_cost}')
                
                if 'cost_breakdown' in cost_estimates:
                    breakdown = cost_estimates['cost_breakdown']
                    print(f'       📊 Cost Breakdown: Compute=${breakdown.get("compute", 0)}, Storage=${breakdown.get("storage", 0)}, Network=${breakdown.get("networking", 0)}')
            
            if recommendation_data:
                provider = recommendation_data.get('provider', 'Unknown')
                region = recommendation_data.get('region', 'Unknown')
                print(f'       ☁️ Provider: {provider}, Region: {region}')
    
    # Check for any mock data patterns
    print(f'\n🧪 MOCK DATA DETECTION:')
    all_recs = await db.recommendations.find({}).to_list(length=None)
    
    mock_indicators = []
    for rec in all_recs:
        title = rec.get('title', '')
        description = rec.get('description', '')
        
        # Check for typical mock data patterns
        if 'example' in title.lower() or 'test' in title.lower() or 'mock' in title.lower():
            mock_indicators.append(f'Title contains mock keywords: {title}')
        
        if 'lorem ipsum' in description.lower() or 'placeholder' in description.lower():
            mock_indicators.append(f'Description has placeholder text: {title}')
        
        # Check if costs are suspiciously round numbers (common in mock data)
        cost_estimates = rec.get('cost_estimates', {})
        if cost_estimates:
            monthly_cost = cost_estimates.get('monthly_cost', 0)
            if monthly_cost in [1000, 2000, 5000, 10000]:  # Common mock values
                mock_indicators.append(f'Suspiciously round cost ({monthly_cost}): {title}')
    
    if mock_indicators:
        print('⚠️ Potential mock data detected:')
        for indicator in mock_indicators:
            print(f'  • {indicator}')
    else:
        print('✅ No obvious mock data patterns detected')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_reports_and_data())