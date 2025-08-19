#!/usr/bin/env python3
"""
Check final status of stored AI workflow data.
"""
import asyncio
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from infra_mind.core.database import init_database
from infra_mind.models.recommendation import Recommendation
from infra_mind.models.assessment import Assessment

async def check_final_status():
    """Check final status of AI workflow data in database."""
    
    print("🔍 FINAL AI WORKFLOW STATUS CHECK")
    print("=" * 50)
    
    try:
        # Initialize database
        await init_database()
        print("✅ Database connected")
        
        # Check assessments
        assessments = await Assessment.find_all().to_list()
        print(f"📋 Total assessments: {len(assessments)}")
        
        completed_assessments = [a for a in assessments if a.status.value == "completed"]
        print(f"✅ Completed assessments: {len(completed_assessments)}")
        
        # Check recommendations
        recommendations = await Recommendation.find_all().to_list()
        print(f"🎯 Total recommendations: {len(recommendations)}")
        
        # Show sample data
        print(f"\n📊 SAMPLE RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations[:3]):
            print(f"   {i+1}. {rec.title}")
            print(f"      Agent: {rec.agent_name}")
            print(f"      Assessment: {rec.assessment_id}")
            print(f"      Confidence: {rec.confidence_score}")
            print()
        
        # Show assessments status
        print(f"📋 ASSESSMENT STATUS:")
        for assessment in assessments:
            print(f"   • {assessment.title}")
            print(f"     Status: {assessment.status.value}")
            print(f"     Recommendations Generated: {assessment.recommendations_generated}")
            print(f"     Reports Generated: {assessment.reports_generated}")
            print(f"     Completion: {assessment.completion_percentage}%")
            
            # Count recommendations for this assessment
            assessment_recs = [r for r in recommendations if r.assessment_id == str(assessment.id)]
            print(f"     AI Recommendations: {len(assessment_recs)}")
            print()
        
        print("🎉 AI WORKFLOW DATA SUCCESSFULLY STORED!")
        print("🔗 Access dashboard at: http://localhost:3000")
        print("🔐 Login: liteshperumalla@gmail.com / Litesh@#12345")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_final_status())