#!/usr/bin/env python3
"""
Debug what data the frontend might be showing vs what's actually in the database
"""
import asyncio
import os
from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def debug_dashboard_data():
    print('🔍 Debugging dashboard data vs database...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    await init_beanie(
        database=database,
        document_models=[User, Assessment, Recommendation, Report]
    )
    print('✅ Connected to database')
    
    # Check all assessments in the database
    all_assessments = await Assessment.find().to_list()
    print(f'\n📋 ALL ASSESSMENTS IN DATABASE ({len(all_assessments)}):')
    
    for assessment in all_assessments:
        user = await User.find_one(User.id == assessment.user_id)
        user_email = user.email if user else "Unknown user"
        
        recs_count = await Recommendation.find(Recommendation.assessment_id == str(assessment.id)).count()
        reports_count = await Report.find(Report.assessment_id == str(assessment.id)).count()
        
        print(f'\n   📋 Title: {assessment.title}')
        print(f'      🆔 ID: {assessment.id}')
        print(f'      👤 User: {user_email}')
        print(f'      📊 Status: {assessment.status}')
        print(f'      📈 Progress: {assessment.completion_percentage}%')
        print(f'      💡 Recommendations: {recs_count}')
        print(f'      📄 Reports: {reports_count}')
        print(f'      📅 Created: {assessment.created_at}')
    
    # Check specifically for "Fixed Frontend Test Assessment"
    fixed_assessment = await Assessment.find_one(Assessment.title == "Fixed Frontend Test Assessment")
    if fixed_assessment:
        print(f'\n🎯 FOUND "Fixed Frontend Test Assessment":')
        user = await User.find_one(User.id == fixed_assessment.user_id)
        print(f'   🆔 ID: {fixed_assessment.id}')
        print(f'   👤 User: {user.email if user else "Unknown"}')
        print(f'   📊 Status: {fixed_assessment.status}')
        print(f'   📈 Progress: {fixed_assessment.completion_percentage}%')
        print(f'   📅 Created: {fixed_assessment.created_at}')
    else:
        print(f'\n✅ "Fixed Frontend Test Assessment" not found in database')
    
    # Check what the frontend API would return for liteshperumalla@gmail.com
    litesh_user = await User.find_one(User.email == 'liteshperumalla@gmail.com')
    if litesh_user:
        litesh_assessments = await Assessment.find(Assessment.user_id == str(litesh_user.id)).to_list()
        print(f'\n👤 ASSESSMENTS FOR liteshperumalla@gmail.com ({len(litesh_assessments)}):')
        for assessment in litesh_assessments:
            print(f'   📋 {assessment.title} - {assessment.status} ({assessment.completion_percentage}%)')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(debug_dashboard_data())