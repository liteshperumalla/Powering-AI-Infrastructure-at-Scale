#!/usr/bin/env python3
"""
Drop and clean up problematic data that's causing API errors.
"""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database
from infra_mind.models.recommendation import ServiceRecommendation

async def clean_problematic_data():
    """Clean up problematic ServiceRecommendation data that's causing API errors."""
    
    print("🔧 CLEANING PROBLEMATIC DATA")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connected")
        
        # Check for ServiceRecommendation documents
        service_recs = await ServiceRecommendation.find_all().to_list()
        print(f"📋 Found {len(service_recs)} ServiceRecommendation documents")
        
        if service_recs:
            print("🗑️ Deleting all ServiceRecommendation documents (they have Decimal128 issues)")
            result = await ServiceRecommendation.delete_all()
            print(f"✅ Deleted {result.deleted_count} ServiceRecommendation documents")
        
        # Verify cleanup
        remaining = await ServiceRecommendation.find_all().to_list()
        print(f"📊 Remaining ServiceRecommendation documents: {len(remaining)}")
        
        print("\n🎉 Data cleanup completed!")
        print("✅ API should now work properly")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clean_problematic_data())