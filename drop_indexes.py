#!/usr/bin/env python3
"""
Drop problematic unique indexes that are causing duplicate key errors
"""
import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def drop_indexes():
    print('🗂️ Dropping problematic unique indexes...')
    
    MONGODB_URL = os.getenv('INFRA_MIND_MONGODB_URL', 'mongodb://admin:password@localhost:27017/infra_mind?authSource=admin')
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client.get_database()
    
    try:
        # Drop the problematic unique indexes
        recommendations_collection = database.get_collection('recommendations')
        reports_collection = database.get_collection('reports')
        
        # List current indexes
        rec_indexes = await recommendations_collection.list_indexes().to_list(length=None)
        print('Current recommendation indexes:', [idx['name'] for idx in rec_indexes])
        
        report_indexes = await reports_collection.list_indexes().to_list(length=None)  
        print('Current report indexes:', [idx['name'] for idx in report_indexes])
        
        # Drop problematic indexes if they exist
        try:
            await recommendations_collection.drop_index('idx_recommendations_id_unique')
            print('✅ Dropped idx_recommendations_id_unique')
        except Exception as e:
            print(f'⚠️ Could not drop idx_recommendations_id_unique: {e}')
            
        try:
            await reports_collection.drop_index('idx_reports_id_unique')
            print('✅ Dropped idx_reports_id_unique')
        except Exception as e:
            print(f'⚠️ Could not drop idx_reports_id_unique: {e}')
        
        # List indexes after dropping
        rec_indexes = await recommendations_collection.list_indexes().to_list(length=None)
        print('Remaining recommendation indexes:', [idx['name'] for idx in rec_indexes])
        
        report_indexes = await reports_collection.list_indexes().to_list(length=None)
        print('Remaining report indexes:', [idx['name'] for idx in report_indexes])
        
    except Exception as e:
        print(f'❌ Error: {e}')
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(drop_indexes())