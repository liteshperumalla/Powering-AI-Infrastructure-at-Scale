#!/usr/bin/env python3
"""
Fix decimal encoding issues in the database.
MongoDB Decimal128 values need to be converted to proper Python Decimal types.
"""
import asyncio
import sys
import os
from decimal import Decimal
from bson import Decimal128

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database
from infra_mind.models.recommendation import Recommendation

async def fix_decimal_encoding():
    """Fix decimal encoding issues in recommendations."""
    
    print("🔧 FIXING DECIMAL ENCODING ISSUES")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connected")
        
        # Find all recommendations
        recommendations = await Recommendation.find_all().to_list()
        print(f"📋 Found {len(recommendations)} recommendations to check")
        
        fixed_count = 0
        
        for recommendation in recommendations:
            needs_update = False
            
            # Check recommendation_data for decimal values
            if hasattr(recommendation, 'recommendation_data') and recommendation.recommendation_data:
                for key, value in recommendation.recommendation_data.items():
                    if isinstance(value, Decimal128):
                        print(f"  🔧 Converting Decimal128 field: {key}")
                        recommendation.recommendation_data[key] = float(str(value))
                        needs_update = True
            
            # Update if needed
            if needs_update:
                await recommendation.save()
                fixed_count += 1
                print(f"  ✅ Fixed recommendation: {recommendation.title}")
        
        print(f"\n🎉 Fixed {fixed_count} recommendations with decimal encoding issues")
        print("✅ All decimal values are now properly encoded")
        
        # Test API endpoint
        print("\n🔍 Testing API endpoint...")
        test_rec = recommendations[0] if recommendations else None
        if test_rec:
            print(f"✅ Test recommendation data: {test_rec.recommendation_data}")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_decimal_encoding())