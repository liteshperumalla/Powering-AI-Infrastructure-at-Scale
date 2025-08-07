#!/usr/bin/env python3
"""
Check user status and available users
"""
import asyncio
import os
from src.infra_mind.models.user import User
from src.infra_mind.models.assessment import Assessment
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

async def check_user_status():
    print('👥 Checking user status...')
    
    # Connect to database
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    await init_beanie(
        database=database,
        document_models=[User, Assessment]
    )
    print('✅ Connected to database')
    
    # Find all users
    users = await User.find().to_list()
    print(f'👥 Found {len(users)} total users:')
    
    for user in users:
        # Count assessments for each user
        assessment_count = await Assessment.find(Assessment.user_id == str(user.id)).count()
        
        print(f'   📧 {user.email}')
        print(f'      👤 Name: {user.full_name}')
        print(f'      🆔 ID: {user.id}')
        print(f'      📋 Assessments: {assessment_count}')
        print(f'      ✅ Active: {user.is_active}')
        print(f'      🔐 Role: {user.role}')
        print()
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_user_status())