#!/usr/bin/env python3
"""
Clear all assessment data for a specific user (liteshperumalla@gmail.com)
"""
import asyncio
import os
from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from src.infra_mind.models.recommendation import Recommendation
from src.infra_mind.models.report import Report
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def clear_user_data():
    print('🧹 Clearing all data for liteshperumalla@gmail.com...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    await init_beanie(
        database=database,
        document_models=[User, Assessment, Recommendation, Report]
    )
    print('✅ Connected to database')
    
    # Find the user
    user = await User.find_one(User.email == 'liteshperumalla@gmail.com')
    if not user:
        print('❌ User liteshperumalla@gmail.com not found')
        return
    
    user_id = str(user.id)
    print(f'👤 Found user: {user.email} (ID: {user_id})')
    
    # Get all assessments for this user
    assessments = await Assessment.find(Assessment.user_id == user_id).to_list()
    print(f'📋 Found {len(assessments)} assessments to clear')
    
    # Clear all related data
    total_recommendations = 0
    total_reports = 0
    
    for assessment in assessments:
        assessment_id = str(assessment.id)
        print(f'   📋 Clearing assessment: {assessment.title} ({assessment_id})')
        
        # Count and delete recommendations
        recs = await Recommendation.find(Recommendation.assessment_id == assessment_id).to_list()
        await Recommendation.find(Recommendation.assessment_id == assessment_id).delete()
        total_recommendations += len(recs)
        
        # Count and delete reports
        reports = await Report.find(Report.assessment_id == assessment_id).to_list()
        await Report.find(Report.assessment_id == assessment_id).delete()
        total_reports += len(reports)
        
        print(f'      💡 Cleared {len(recs)} recommendations')
        print(f'      📄 Cleared {len(reports)} reports')
    
    # Delete all assessments
    await Assessment.find(Assessment.user_id == user_id).delete()
    
    print(f'\n✅ Successfully cleared all data for {user.email}:')
    print(f'   📋 Assessments: {len(assessments)}')
    print(f'   💡 Recommendations: {total_recommendations}')
    print(f'   📄 Reports: {total_reports}')
    print(f'\n🎯 User account remains active for fresh start from frontend')
    
    client.close()
    return {
        'user_email': user.email,
        'assessments_cleared': len(assessments),
        'recommendations_cleared': total_recommendations,
        'reports_cleared': total_reports
    }

if __name__ == "__main__":
    result = asyncio.run(clear_user_data())
    if result:
        print(f'\n🎉 CLEAN SLATE READY!')
        print(f'👤 User {result["user_email"]} can now start fresh from the frontend')
        print(f'🗑️ Total items cleared:')
        print(f'   • {result["assessments_cleared"]} assessments')
        print(f'   • {result["recommendations_cleared"]} recommendations') 
        print(f'   • {result["reports_cleared"]} reports')
        print(f'\n🔗 Ready to create new assessments at: http://localhost:3000')
    else:
        print('❌ Failed to clear user data')