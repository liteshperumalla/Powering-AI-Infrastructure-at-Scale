#!/usr/bin/env python3
"""
Create missing database collections and indexes.

This script creates any missing collections that are expected by the system.
"""

import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from loguru import logger

# Database configuration
MONGODB_URL = os.getenv("INFRA_MIND_MONGODB_URL", "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")

async def create_missing_collections():
    """Create missing collections and their indexes."""
    logger.info("Creating missing collections...")
    
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGODB_URL)
        db = client.get_database("infra_mind")
        
        # Expected collections with their configurations
        expected_collections = {
            "workflows": {
                "indexes": [
                    [("workflow_id", 1)],
                    [("assessment_id", 1)],
                    [("status", 1)],
                    [("created_at", -1)]
                ],
                "description": "Workflow execution states and history"
            },
            "workflow_states": {
                "indexes": [
                    [("workflow_id", 1)],
                    [("assessment_id", 1)],
                    [("current_node", 1)],
                    [("created_at", -1)]
                ],
                "description": "Current workflow states"
            }
        }
        
        # Get existing collections
        existing_collections = await db.list_collection_names()
        
        created_count = 0
        
        for collection_name, config in expected_collections.items():
            if collection_name not in existing_collections:
                logger.info(f"Creating collection: {collection_name}")
                
                # Create the collection
                await db.create_collection(collection_name)
                
                # Create indexes
                if "indexes" in config:
                    for index_spec in config["indexes"]:
                        try:
                            await db[collection_name].create_index(index_spec)
                            logger.info(f"  Created index: {index_spec}")
                        except Exception as e:
                            logger.warning(f"  Failed to create index {index_spec}: {e}")
                
                # Add a sample document to establish schema
                sample_doc = None
                if collection_name == "workflows":
                    sample_doc = {
                        "workflow_id": "sample_workflow",
                        "assessment_id": "sample_assessment",
                        "workflow_type": "assessment_workflow",
                        "status": "completed",
                        "nodes": [],
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "completed_at": "2024-01-01T00:00:00Z",
                        "metadata": {
                            "sample": True,
                            "description": config["description"]
                        }
                    }
                elif collection_name == "workflow_states":
                    sample_doc = {
                        "workflow_id": "sample_workflow",
                        "assessment_id": "sample_assessment",
                        "current_node": "start",
                        "completed_nodes": [],
                        "shared_data": {},
                        "status": "completed",
                        "created_at": "2024-01-01T00:00:00Z",
                        "updated_at": "2024-01-01T00:00:00Z",
                        "metadata": {
                            "sample": True,
                            "description": config["description"]
                        }
                    }
                
                if sample_doc:
                    await db[collection_name].insert_one(sample_doc)
                    logger.info(f"  Inserted sample document")
                
                created_count += 1
                logger.success(f"✅ Created collection: {collection_name}")
            else:
                logger.info(f"Collection {collection_name} already exists")
        
        logger.success(f"Collection creation completed. Created {created_count} new collections.")
        client.close()
        return created_count
        
    except Exception as e:
        logger.error(f"Error creating collections: {e}")
        return -1

async def main():
    """Main function."""
    logger.info("Database Collection Creator - Creating missing collections")
    logger.info("=" * 60)
    
    created_count = await create_missing_collections()
    
    if created_count >= 0:
        logger.success(f"✅ Successfully created {created_count} collections")
        sys.exit(0)
    else:
        logger.error("❌ Failed to create collections")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())