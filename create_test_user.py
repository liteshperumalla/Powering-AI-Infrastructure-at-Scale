#!/usr/bin/env python3
"""
Create a test user for login testing
"""

import asyncio
import os
import sys
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
import bcrypt

async def create_test_user():
    """Create a test user in the database"""
    
    # Database connection
    mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", 
                         "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database("infra_mind")
    
    try:
        # Check if users collection exists and has any users
        users_count = await db.users.count_documents({})
        print(f"📊 Current users in database: {users_count}")
        
        # Check if test user already exists
        test_email = "test@infra-mind.com"
        existing_user = await db.users.find_one({"email": test_email})
        
        if existing_user:
            print(f"✅ Test user already exists: {test_email}")
            print(f"   Full Name: {existing_user.get('full_name', 'Unknown')}")
            print(f"   Is Active: {existing_user.get('is_active', False)}")
        else:
            # Create test user
            test_password = "password123"
            hashed_password = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            test_user = {
                "email": test_email,
                "hashed_password": hashed_password,
                "full_name": "Test User",
                "company_name": "Infra Mind Test",
                "job_title": "Test Engineer",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "is_admin": False,
                "is_superuser": False,
                "preferred_cloud_providers": [],
                "notification_preferences": {
                    "email_reports": True,
                    "assessment_updates": True,
                    "security_alerts": True,
                    "marketing": False
                },
                "subscription": {
                    "plan": "premium",
                    "status": "active",
                    "started_at": datetime.utcnow(),
                    "features": ["unlimited_assessments", "advanced_analytics", "priority_support"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "last_active": datetime.utcnow(),
                "login_count": 0
            }
            
            result = await db.users.insert_one(test_user)
            print(f"✅ Created test user successfully!")
            print(f"   Email: {test_email}")
            print(f"   Password: {test_password}")
            print(f"   User ID: {result.inserted_id}")
        
        # Also check for an admin user and create if needed
        admin_email = "admin@infra-mind.com"
        existing_admin = await db.users.find_one({"email": admin_email})
        
        if not existing_admin:
            admin_password = "admin123"
            hashed_admin_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            admin_user = {
                "email": admin_email,
                "hashed_password": hashed_admin_password,
                "full_name": "Admin User",
                "company_name": "Infra Mind",
                "job_title": "System Administrator",
                "role": "admin",
                "is_active": True,
                "is_verified": True,
                "is_admin": True,
                "is_superuser": True,
                "preferred_cloud_providers": ["aws", "azure", "gcp"],
                "notification_preferences": {
                    "email_reports": True,
                    "assessment_updates": True,
                    "security_alerts": True,
                    "marketing": False
                },
                "subscription": {
                    "plan": "enterprise",
                    "status": "active",
                    "started_at": datetime.utcnow(),
                    "features": ["unlimited_assessments", "advanced_analytics", "priority_support", "api_access"]
                },
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "last_login": None,
                "last_active": datetime.utcnow(),
                "login_count": 0
            }
            
            result = await db.users.insert_one(admin_user)
            print(f"✅ Created admin user successfully!")
            print(f"   Email: {admin_email}")
            print(f"   Password: {admin_password}")
            print(f"   User ID: {result.inserted_id}")
        else:
            print(f"✅ Admin user already exists: {admin_email}")
        
        # Final count
        final_count = await db.users.count_documents({})
        print(f"\n📊 Total users in database: {final_count}")
        
        print(f"\n🔑 Login Credentials for Testing:")
        print(f"   Regular User: {test_email} / password123")
        print(f"   Admin User: {admin_email} / admin123")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(create_test_user())
