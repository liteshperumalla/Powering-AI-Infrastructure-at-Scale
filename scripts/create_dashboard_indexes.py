#!/usr/bin/env python3
"""
Create MongoDB Indexes for Dashboard Performance.

This script creates all necessary indexes for optimized dashboard queries.
Run this once during deployment to ensure fast dashboard performance.

Usage:
    python scripts/create_dashboard_indexes.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger


async def create_indexes():
    """Create all dashboard-related indexes."""

    # Connect to MongoDB
    mongo_uri = os.getenv(
        "INFRA_MIND_MONGODB_URL",
        "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    )

    logger.info(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database("infra_mind")

    try:
        # Test connection
        await db.command('ping')
        logger.info("✅ Connected to MongoDB")

        # ============================================
        # ASSESSMENTS COLLECTION
        # ============================================
        logger.info("\n📊 Creating indexes for 'assessments' collection...")

        assessments = db.assessments

        # Index 1: User ID + Created At (for recent assessments)
        await assessments.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_user_created"
        )
        logger.info("✅ Created: idx_user_created")

        # Index 2: User ID + Status (for filtering by status)
        await assessments.create_index(
            [("user_id", 1), ("status", 1)],
            name="idx_user_status"
        )
        logger.info("✅ Created: idx_user_status")

        # Index 3: User ID + Completion Percentage (for sorting)
        await assessments.create_index(
            [("user_id", 1), ("completion_percentage", -1)],
            name="idx_user_completion"
        )
        logger.info("✅ Created: idx_user_completion")

        # Index 4: User ID + Updated At (for recent activity)
        await assessments.create_index(
            [("user_id", 1), ("updated_at", -1)],
            name="idx_user_updated"
        )
        logger.info("✅ Created: idx_user_updated")

        # Index 5: Created At (for global recent assessments)
        await assessments.create_index(
            [("created_at", -1)],
            name="idx_created_desc"
        )
        logger.info("✅ Created: idx_created_desc")

        # ============================================
        # RECOMMENDATIONS COLLECTION
        # ============================================
        logger.info("\n📊 Creating indexes for 'recommendations' collection...")

        recommendations = db.recommendations

        # Index 1: User ID + Created At
        await recommendations.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_user_created"
        )
        logger.info("✅ Created: idx_user_created")

        # Index 2: User ID + Priority (for filtering high priority)
        await recommendations.create_index(
            [("user_id", 1), ("priority", 1)],
            name="idx_user_priority"
        )
        logger.info("✅ Created: idx_user_priority")

        # Index 3: User ID + Category (for category breakdown)
        await recommendations.create_index(
            [("user_id", 1), ("category", 1)],
            name="idx_user_category"
        )
        logger.info("✅ Created: idx_user_category")

        # Index 4: User ID + Confidence Score (for top recommendations)
        await recommendations.create_index(
            [("user_id", 1), ("confidence_score", -1)],
            name="idx_user_confidence"
        )
        logger.info("✅ Created: idx_user_confidence")

        # Index 5: Assessment ID (for recommendations by assessment)
        await recommendations.create_index(
            [("assessment_id", 1)],
            name="idx_assessment"
        )
        logger.info("✅ Created: idx_assessment")

        # Index 6: User ID + Estimated Cost Savings (for ROI analysis)
        await recommendations.create_index(
            [("user_id", 1), ("estimated_cost_savings", -1)],
            name="idx_user_savings"
        )
        logger.info("✅ Created: idx_user_savings")

        # ============================================
        # REPORTS COLLECTION
        # ============================================
        logger.info("\n📊 Creating indexes for 'reports' collection...")

        reports = db.reports

        # Index 1: User ID + Created At
        await reports.create_index(
            [("user_id", 1), ("created_at", -1)],
            name="idx_user_created"
        )
        logger.info("✅ Created: idx_user_created")

        # Index 2: User ID + Report Type + Status
        await reports.create_index(
            [("user_id", 1), ("report_type", 1), ("status", 1)],
            name="idx_user_type_status"
        )
        logger.info("✅ Created: idx_user_type_status")

        # Index 3: Assessment ID (for reports by assessment)
        await reports.create_index(
            [("assessment_id", 1)],
            name="idx_assessment"
        )
        logger.info("✅ Created: idx_assessment")

        # Index 4: User ID + Status (for filtering)
        await reports.create_index(
            [("user_id", 1), ("status", 1)],
            name="idx_user_status"
        )
        logger.info("✅ Created: idx_user_status")

        # ============================================
        # USERS COLLECTION
        # ============================================
        logger.info("\n📊 Creating indexes for 'users' collection...")

        users = db.users

        # Index 1: Email (unique, for authentication)
        await users.create_index(
            [("email", 1)],
            unique=True,
            name="idx_email_unique"
        )
        logger.info("✅ Created: idx_email_unique")

        # Index 2: Created At (for user growth metrics)
        await users.create_index(
            [("created_at", -1)],
            name="idx_created_desc"
        )
        logger.info("✅ Created: idx_created_desc")

        # ============================================
        # RECOMMENDATION_INTERACTIONS COLLECTION (ML)
        # ============================================
        logger.info("\n📊 Creating indexes for 'recommendation_interactions' collection...")

        interactions = db.recommendation_interactions

        # Index 1: User ID + Timestamp (for user history)
        await interactions.create_index(
            [("user_id", 1), ("timestamp", -1)],
            name="idx_user_timestamp"
        )
        logger.info("✅ Created: idx_user_timestamp")

        # Index 2: Recommendation ID (for recommendation stats)
        await interactions.create_index(
            [("recommendation_id", 1)],
            name="idx_recommendation"
        )
        logger.info("✅ Created: idx_recommendation")

        # Index 3: Interaction Type (for analytics)
        await interactions.create_index(
            [("interaction_type", 1), ("timestamp", -1)],
            name="idx_type_timestamp"
        )
        logger.info("✅ Created: idx_type_timestamp")

        # Index 4: Created At + Label (for ML training data)
        await interactions.create_index(
            [("created_at", -1), ("label", -1)],
            name="idx_training_data"
        )
        logger.info("✅ Created: idx_training_data")

        # ============================================
        # VERIFY ALL INDEXES
        # ============================================
        logger.info("\n🔍 Verifying indexes...")

        collections = {
            "assessments": assessments,
            "recommendations": recommendations,
            "reports": reports,
            "users": users,
            "recommendation_interactions": interactions
        }

        total_indexes = 0
        for name, collection in collections.items():
            indexes = await collection.index_information()
            count = len(indexes)
            total_indexes += count
            logger.info(f"✅ {name}: {count} indexes")

        logger.info(f"\n🎉 Total indexes created: {total_indexes}")
        logger.info("✅ All indexes created successfully!")

        # ============================================
        # PERFORMANCE RECOMMENDATIONS
        # ============================================
        logger.info("\n💡 Performance Recommendations:")
        logger.info("1. Monitor slow queries: db.setProfilingLevel(1, {slowms: 100})")
        logger.info("2. Check index usage: db.assessments.aggregate([{$indexStats:{}}])")
        logger.info("3. Optimize queries to use covered indexes when possible")
        logger.info("4. Consider sharding for collections > 100GB")

        return True

    except Exception as e:
        logger.error(f"❌ Error creating indexes: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

    finally:
        client.close()
        logger.info("\n🔌 Disconnected from MongoDB")


async def drop_and_recreate_indexes():
    """Drop existing indexes and recreate (use with caution!)."""
    logger.warning("⚠️  This will drop and recreate all indexes!")
    logger.warning("⚠️  Use only if you need to rebuild indexes from scratch")

    # Connect to MongoDB
    mongo_uri = os.getenv(
        "INFRA_MIND_MONGODB_URL",
        "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin"
    )

    client = AsyncIOMotorClient(mongo_uri)
    db = client.get_database("infra_mind")

    try:
        collections = ["assessments", "recommendations", "reports", "users", "recommendation_interactions"]

        for coll_name in collections:
            collection = db[coll_name]

            # Get existing indexes
            indexes = await collection.index_information()

            # Drop all except _id index
            for index_name in indexes:
                if index_name != "_id_":
                    await collection.drop_index(index_name)
                    logger.info(f"🗑️  Dropped: {coll_name}.{index_name}")

        logger.info("\n✅ All indexes dropped. Now recreating...")

        # Recreate indexes
        await create_indexes()

    finally:
        client.close()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Create MongoDB indexes for dashboard performance"
    )
    parser.add_argument(
        "--drop-and-recreate",
        action="store_true",
        help="Drop existing indexes and recreate (CAUTION!)"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("MongoDB Index Creation Script")
    logger.info("=" * 60)
    logger.info("")

    if args.drop_and_recreate:
        logger.warning("⚠️  DROP AND RECREATE MODE")
        confirm = input("Are you sure? Type 'yes' to continue: ")
        if confirm.lower() != 'yes':
            logger.info("❌ Aborted")
            return

        success = asyncio.run(drop_and_recreate_indexes())
    else:
        success = asyncio.run(create_indexes())

    if success:
        logger.info("\n✅ SUCCESS! Indexes are ready for production.")
        logger.info("📈 Dashboard queries will now be significantly faster.")
        sys.exit(0)
    else:
        logger.error("\n❌ FAILED! Check errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
