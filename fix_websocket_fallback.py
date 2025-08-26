#!/usr/bin/env python3
"""
WebSocket fallback mechanism fix for assessment progress updates
"""

websocket_fallback_patch = '''
# Enhanced WebSocket broadcast function with fallback mechanism
async def broadcast_update(step: str, progress: float, message: str = ""):
    """Enhanced broadcast function with error handling and fallback"""
    try:
        # Primary: Try WebSocket broadcast
        if app_state and hasattr(app_state, 'broadcast_workflow_update'):
            update_data = {
                "assessment_id": str(assessment.id),
                "status": assessment.status,
                "current_step": step,
                "progress_percentage": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
                "agents_status": []
            }
            
            try:
                await app_state.broadcast_workflow_update(str(assessment.id), update_data)
                logger.debug(f"✅ WebSocket update sent - Step: {step}, Progress: {progress}%")
            except Exception as ws_error:
                logger.warning(f"⚠️ WebSocket broadcast failed: {ws_error}")
                
                # Fallback 1: Store update in database for polling
                try:
                    await store_progress_update_in_db(assessment.id, update_data)
                    logger.info(f"📊 Progress stored in DB as fallback - Step: {step}")
                except Exception as db_error:
                    logger.error(f"❌ Fallback DB storage failed: {db_error}")
                
                # Fallback 2: Update assessment record directly
                try:
                    assessment.progress = {
                        "current_step": step,
                        "progress_percentage": progress,
                        "message": message,
                        "last_update": datetime.utcnow(),
                        "websocket_failed": True
                    }
                    await assessment.save()
                    logger.info(f"💾 Assessment progress updated directly in DB")
                except Exception as save_error:
                    logger.error(f"❌ Direct assessment update failed: {save_error}")
        else:
            # No WebSocket available - use database polling fallback
            logger.info(f"🔄 No WebSocket - using DB polling fallback for {step}")
            await store_progress_update_in_db(assessment.id, {
                "current_step": step,
                "progress_percentage": progress,
                "message": message,
                "websocket_available": False
            })
            
    except Exception as e:
        logger.error(f"❌ Critical error in broadcast_update: {e}")
        # Emergency fallback - just update the assessment
        try:
            assessment.progress = {
                "current_step": step,
                "progress_percentage": progress,
                "message": f"Update failed, step: {step}",
                "emergency_fallback": True
            }
            assessment.progress_percentage = progress
            await assessment.save()
        except:
            pass  # Last resort - don't fail the workflow

async def store_progress_update_in_db(assessment_id, update_data):
    """Store progress update in database for polling fallback"""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", 
                             "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
        client = AsyncIOMotorClient(mongo_uri)
        db = client.get_database("infra_mind")
        
        # Store in assessment_progress collection for polling
        progress_doc = {
            "assessment_id": str(assessment_id),
            "timestamp": datetime.utcnow(),
            "progress_data": update_data,
            "type": "progress_update"
        }
        
        await db.assessment_progress.insert_one(progress_doc)
        
        # Clean up old progress updates (keep last 100 per assessment)
        old_updates = await db.assessment_progress.find({
            "assessment_id": str(assessment_id)
        }).sort("timestamp", -1).skip(100).to_list(length=None)
        
        if old_updates:
            old_ids = [doc["_id"] for doc in old_updates]
            await db.assessment_progress.delete_many({"_id": {"$in": old_ids}})
            
        client.close()
        
    except Exception as e:
        logger.error(f"Failed to store progress update in DB: {e}")
        raise
'''

print("📡 WebSocket fallback mechanism patch created")
print("This patch provides:")
print("  1. ✅ Primary WebSocket broadcast attempt")
print("  2. ✅ Database fallback for progress storage") 
print("  3. ✅ Direct assessment record update fallback")
print("  4. ✅ Emergency fallback to prevent workflow failures")
print("  5. ✅ Progress cleanup to prevent database bloat")