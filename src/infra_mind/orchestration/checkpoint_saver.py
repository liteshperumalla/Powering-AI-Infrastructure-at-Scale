"""
Production checkpoint saver for LangGraph workflows using MongoDB.

Provides persistent state storage for workflow checkpoints and recovery.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple, Iterator
import json
import pickle
import base64

from langgraph.checkpoint.base import BaseCheckpointSaver, Checkpoint, CheckpointMetadata
from langchain_core.runnables import RunnableConfig

from ..core.database import get_database
import logging

logger = logging.getLogger(__name__)


class MongoCheckpointSaver(BaseCheckpointSaver):
    """
    MongoDB-based checkpoint saver for LangGraph workflows.
    
    Provides persistent storage and recovery of workflow states
    for production reliability and fault tolerance.
    """
    
    def __init__(self, collection_name: str = "workflow_checkpoints"):
        """
        Initialize MongoDB checkpoint saver.
        
        Args:
            collection_name: Name of MongoDB collection for checkpoints
        """
        self.collection_name = collection_name
        self._db = None
        self._collection = None
        logger.info(f"MongoDB checkpoint saver initialized with collection: {collection_name}")
    
    async def _get_collection(self):
        """Get MongoDB collection, initializing if needed."""
        if self._collection is None:
            self._db = await get_database()
            self._collection = self._db[self.collection_name]
            
            # Create indexes for efficient queries
            await self._collection.create_index([
                ("thread_id", 1),
                ("checkpoint_id", 1)
            ], unique=True)
            
            await self._collection.create_index([
                ("thread_id", 1),
                ("created_at", -1)
            ])
            
            logger.info(f"MongoDB collection initialized: {self.collection_name}")
        
        return self._collection
    
    def _serialize_checkpoint(self, checkpoint: Checkpoint) -> Dict[str, Any]:
        """Serialize checkpoint for MongoDB storage."""
        try:
            # Convert checkpoint to serializable format
            serialized = {
                "v": checkpoint.v,
                "ts": checkpoint.ts,
                "channel_values": {},
                "channel_versions": checkpoint.channel_versions,
                "versions_seen": checkpoint.versions_seen,
                "pending_sends": []
            }
            
            # Serialize channel values
            for key, value in checkpoint.channel_values.items():
                try:
                    # Try JSON serialization first
                    json.dumps(value)
                    serialized["channel_values"][key] = {
                        "type": "json",
                        "data": value
                    }
                except (TypeError, ValueError):
                    # Fall back to pickle for complex objects
                    pickled_data = pickle.dumps(value)
                    encoded_data = base64.b64encode(pickled_data).decode('utf-8')
                    serialized["channel_values"][key] = {
                        "type": "pickle",
                        "data": encoded_data
                    }
            
            # Serialize pending sends
            for send in checkpoint.pending_sends:
                try:
                    serialized["pending_sends"].append({
                        "type": "json",
                        "data": send
                    })
                except (TypeError, ValueError):
                    pickled_data = pickle.dumps(send)
                    encoded_data = base64.b64encode(pickled_data).decode('utf-8')
                    serialized["pending_sends"].append({
                        "type": "pickle",
                        "data": encoded_data
                    })
            
            return serialized
            
        except Exception as e:
            logger.error(f"Error serializing checkpoint: {str(e)}")
            raise
    
    def _deserialize_checkpoint(self, data: Dict[str, Any]) -> Checkpoint:
        """Deserialize checkpoint from MongoDB storage."""
        try:
            # Deserialize channel values
            channel_values = {}
            for key, value_data in data["channel_values"].items():
                if value_data["type"] == "json":
                    channel_values[key] = value_data["data"]
                elif value_data["type"] == "pickle":
                    encoded_data = value_data["data"]
                    pickled_data = base64.b64decode(encoded_data.encode('utf-8'))
                    channel_values[key] = pickle.loads(pickled_data)
            
            # Deserialize pending sends
            pending_sends = []
            for send_data in data["pending_sends"]:
                if send_data["type"] == "json":
                    pending_sends.append(send_data["data"])
                elif send_data["type"] == "pickle":
                    encoded_data = send_data["data"]
                    pickled_data = base64.b64decode(encoded_data.encode('utf-8'))
                    pending_sends.append(pickle.loads(pickled_data))
            
            return Checkpoint(
                v=data["v"],
                ts=data["ts"],
                channel_values=channel_values,
                channel_versions=data["channel_versions"],
                versions_seen=data["versions_seen"],
                pending_sends=pending_sends
            )
            
        except Exception as e:
            logger.error(f"Error deserializing checkpoint: {str(e)}")
            raise
    
    async def aget_tuple(self, config: RunnableConfig) -> Optional[Tuple[Checkpoint, CheckpointMetadata]]:
        """
        Get checkpoint tuple for a given configuration.
        
        Args:
            config: Runnable configuration
            
        Returns:
            Checkpoint tuple or None if not found
        """
        try:
            collection = await self._get_collection()
            thread_id = config["configurable"]["thread_id"]
            checkpoint_id = config["configurable"].get("checkpoint_id")
            
            # Build query
            query = {"thread_id": thread_id}
            if checkpoint_id:
                query["checkpoint_id"] = checkpoint_id
            
            # Find the most recent checkpoint
            doc = await collection.find_one(
                query,
                sort=[("created_at", -1)]
            )
            
            if not doc:
                return None
            
            # Deserialize checkpoint
            checkpoint = self._deserialize_checkpoint(doc["checkpoint_data"])
            
            # Create metadata
            metadata = CheckpointMetadata(
                source="database",
                step=doc.get("step", -1),
                writes=doc.get("writes", {}),
                parents=doc.get("parents", {})
            )
            
            logger.debug(f"Retrieved checkpoint for thread {thread_id}")
            return (checkpoint, metadata)
            
        except Exception as e:
            logger.error(f"Error retrieving checkpoint: {str(e)}")
            return None
    
    async def aput(self, 
                  config: RunnableConfig, 
                  checkpoint: Checkpoint, 
                  metadata: CheckpointMetadata) -> RunnableConfig:
        """
        Store checkpoint with metadata.
        
        Args:
            config: Runnable configuration
            checkpoint: Checkpoint to store
            metadata: Checkpoint metadata
            
        Returns:
            Updated configuration
        """
        try:
            collection = await self._get_collection()
            thread_id = config["configurable"]["thread_id"]
            checkpoint_id = f"{thread_id}_{checkpoint.ts}"
            
            # Serialize checkpoint
            checkpoint_data = self._serialize_checkpoint(checkpoint)
            
            # Create document
            doc = {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
                "checkpoint_data": checkpoint_data,
                "metadata": {
                    "source": metadata.source,
                    "step": metadata.step,
                    "writes": metadata.writes,
                    "parents": metadata.parents
                },
                "created_at": datetime.now(timezone.utc),
                "ts": checkpoint.ts
            }
            
            # Store checkpoint
            await collection.replace_one(
                {
                    "thread_id": thread_id,
                    "checkpoint_id": checkpoint_id
                },
                doc,
                upsert=True
            )
            
            # Update config with checkpoint ID
            updated_config = config.copy()
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id
            
            logger.debug(f"Stored checkpoint {checkpoint_id} for thread {thread_id}")
            return updated_config
            
        except Exception as e:
            logger.error(f"Error storing checkpoint: {str(e)}")
            raise
    
    async def alist(self, 
                   config: RunnableConfig, 
                   limit: Optional[int] = 10,
                   before: Optional[RunnableConfig] = None) -> List[Tuple[Checkpoint, CheckpointMetadata]]:
        """
        List checkpoints for a thread.
        
        Args:
            config: Runnable configuration
            limit: Maximum number of checkpoints to return
            before: Return checkpoints before this configuration
            
        Returns:
            List of checkpoint tuples
        """
        try:
            collection = await self._get_collection()
            thread_id = config["configurable"]["thread_id"]
            
            # Build query
            query = {"thread_id": thread_id}
            
            if before:
                before_ts = before["configurable"].get("checkpoint_ts")
                if before_ts:
                    query["ts"] = {"$lt": before_ts}
            
            # Find checkpoints
            cursor = collection.find(query).sort([("created_at", -1)])
            
            if limit:
                cursor = cursor.limit(limit)
            
            checkpoints = []
            async for doc in cursor:
                try:
                    # Deserialize checkpoint
                    checkpoint = self._deserialize_checkpoint(doc["checkpoint_data"])
                    
                    # Create metadata
                    metadata_data = doc.get("metadata", {})
                    metadata = CheckpointMetadata(
                        source=metadata_data.get("source", "database"),
                        step=metadata_data.get("step", -1),
                        writes=metadata_data.get("writes", {}),
                        parents=metadata_data.get("parents", {})
                    )
                    
                    checkpoints.append((checkpoint, metadata))
                    
                except Exception as e:
                    logger.warning(f"Error deserializing checkpoint {doc.get('checkpoint_id')}: {str(e)}")
                    continue
            
            logger.debug(f"Retrieved {len(checkpoints)} checkpoints for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error listing checkpoints: {str(e)}")
            return []
    
    async def cleanup_old_checkpoints(self, max_age_hours: int = 168) -> int:
        """
        Clean up old checkpoints.
        
        Args:
            max_age_hours: Maximum age in hours (default: 1 week)
            
        Returns:
            Number of checkpoints cleaned up
        """
        try:
            collection = await self._get_collection()
            cutoff_time = datetime.now(timezone.utc).timestamp() - (max_age_hours * 3600)
            
            # Delete old checkpoints
            result = await collection.delete_many({
                "created_at": {"$lt": datetime.fromtimestamp(cutoff_time, timezone.utc)}
            })
            
            cleaned_count = result.deleted_count
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old checkpoints")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up checkpoints: {str(e)}")
            return 0
    
    async def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get execution history for a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of checkpoint history entries
        """
        try:
            collection = await self._get_collection()
            
            cursor = collection.find(
                {"thread_id": thread_id},
                {
                    "checkpoint_id": 1,
                    "created_at": 1,
                    "ts": 1,
                    "metadata.step": 1,
                    "metadata.writes": 1
                }
            ).sort([("created_at", 1)])
            
            history = []
            async for doc in cursor:
                history.append({
                    "checkpoint_id": doc["checkpoint_id"],
                    "created_at": doc["created_at"].isoformat(),
                    "ts": doc["ts"],
                    "step": doc.get("metadata", {}).get("step", -1),
                    "writes": doc.get("metadata", {}).get("writes", {})
                })
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting thread history: {str(e)}")
            return []
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint saver statistics."""
        try:
            collection = await self._get_collection()
            
            # Count total checkpoints
            total_checkpoints = await collection.count_documents({})
            
            # Count unique threads
            unique_threads = len(await collection.distinct("thread_id"))
            
            # Get oldest and newest checkpoints
            oldest = await collection.find_one({}, sort=[("created_at", 1)])
            newest = await collection.find_one({}, sort=[("created_at", -1)])
            
            return {
                "total_checkpoints": total_checkpoints,
                "unique_threads": unique_threads,
                "oldest_checkpoint": oldest["created_at"].isoformat() if oldest else None,
                "newest_checkpoint": newest["created_at"].isoformat() if newest else None,
                "collection_name": self.collection_name
            }
            
        except Exception as e:
            logger.error(f"Error getting checkpoint stats: {str(e)}")
            return {
                "error": str(e),
                "collection_name": self.collection_name
            }


class RedisCheckpointSaver(BaseCheckpointSaver):
    """
    Redis-based checkpoint saver for high-performance scenarios.
    
    Provides fast checkpoint storage and retrieval using Redis
    for workflows that require low-latency state management.
    """
    
    def __init__(self, key_prefix: str = "langgraph:checkpoint"):
        """
        Initialize Redis checkpoint saver.
        
        Args:
            key_prefix: Redis key prefix for checkpoints
        """
        self.key_prefix = key_prefix
        self._redis = None
        logger.info(f"Redis checkpoint saver initialized with prefix: {key_prefix}")
    
    async def _get_redis(self):
        """Get Redis connection, initializing if needed."""
        if self._redis is None:
            from ..core.cache import get_cache_manager
            cache_manager = get_cache_manager()
            self._redis = cache_manager.redis
            logger.info("Redis connection initialized for checkpoint saver")
        
        return self._redis
    
    def _get_checkpoint_key(self, thread_id: str, checkpoint_id: Optional[str] = None) -> str:
        """Generate Redis key for checkpoint."""
        if checkpoint_id:
            return f"{self.key_prefix}:{thread_id}:{checkpoint_id}"
        else:
            return f"{self.key_prefix}:{thread_id}:latest"
    
    def _get_thread_key(self, thread_id: str) -> str:
        """Generate Redis key for thread checkpoint list."""
        return f"{self.key_prefix}:thread:{thread_id}"
    
    async def aget_tuple(self, config: RunnableConfig) -> Optional[Tuple[Checkpoint, CheckpointMetadata]]:
        """Get checkpoint tuple from Redis."""
        try:
            redis = await self._get_redis()
            thread_id = config["configurable"]["thread_id"]
            checkpoint_id = config["configurable"].get("checkpoint_id")
            
            # Get checkpoint data
            key = self._get_checkpoint_key(thread_id, checkpoint_id)
            data = await redis.get(key)
            
            if not data:
                return None
            
            # Deserialize
            checkpoint_data = json.loads(data)
            
            # Reconstruct checkpoint
            checkpoint = Checkpoint(
                v=checkpoint_data["v"],
                ts=checkpoint_data["ts"],
                channel_values=checkpoint_data["channel_values"],
                channel_versions=checkpoint_data["channel_versions"],
                versions_seen=checkpoint_data["versions_seen"],
                pending_sends=checkpoint_data["pending_sends"]
            )
            
            # Create metadata
            metadata = CheckpointMetadata(
                source="redis",
                step=checkpoint_data.get("step", -1),
                writes=checkpoint_data.get("writes", {}),
                parents=checkpoint_data.get("parents", {})
            )
            
            logger.debug(f"Retrieved checkpoint from Redis for thread {thread_id}")
            return (checkpoint, metadata)
            
        except Exception as e:
            logger.error(f"Error retrieving checkpoint from Redis: {str(e)}")
            return None
    
    async def aput(self, 
                  config: RunnableConfig, 
                  checkpoint: Checkpoint, 
                  metadata: CheckpointMetadata) -> RunnableConfig:
        """Store checkpoint in Redis."""
        try:
            redis = await self._get_redis()
            thread_id = config["configurable"]["thread_id"]
            checkpoint_id = f"{thread_id}_{checkpoint.ts}"
            
            # Serialize checkpoint
            checkpoint_data = {
                "v": checkpoint.v,
                "ts": checkpoint.ts,
                "channel_values": checkpoint.channel_values,
                "channel_versions": checkpoint.channel_versions,
                "versions_seen": checkpoint.versions_seen,
                "pending_sends": checkpoint.pending_sends,
                "step": metadata.step,
                "writes": metadata.writes,
                "parents": metadata.parents,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store checkpoint
            key = self._get_checkpoint_key(thread_id, checkpoint_id)
            await redis.setex(
                key,
                86400,  # 24 hours TTL
                json.dumps(checkpoint_data, default=str)
            )
            
            # Update latest checkpoint
            latest_key = self._get_checkpoint_key(thread_id)
            await redis.setex(
                latest_key,
                86400,
                json.dumps(checkpoint_data, default=str)
            )
            
            # Add to thread checkpoint list
            thread_key = self._get_thread_key(thread_id)
            await redis.lpush(thread_key, checkpoint_id)
            await redis.expire(thread_key, 86400)
            
            # Update config
            updated_config = config.copy()
            updated_config["configurable"]["checkpoint_id"] = checkpoint_id
            
            logger.debug(f"Stored checkpoint in Redis: {checkpoint_id}")
            return updated_config
            
        except Exception as e:
            logger.error(f"Error storing checkpoint in Redis: {str(e)}")
            raise
    
    async def alist(self, 
                   config: RunnableConfig, 
                   limit: Optional[int] = 10,
                   before: Optional[RunnableConfig] = None) -> List[Tuple[Checkpoint, CheckpointMetadata]]:
        """List checkpoints from Redis."""
        try:
            redis = await self._get_redis()
            thread_id = config["configurable"]["thread_id"]
            
            # Get checkpoint IDs for thread
            thread_key = self._get_thread_key(thread_id)
            checkpoint_ids = await redis.lrange(thread_key, 0, limit or 10)
            
            checkpoints = []
            for checkpoint_id in checkpoint_ids:
                try:
                    key = self._get_checkpoint_key(thread_id, checkpoint_id.decode())
                    data = await redis.get(key)
                    
                    if data:
                        checkpoint_data = json.loads(data)
                        
                        # Reconstruct checkpoint
                        checkpoint = Checkpoint(
                            v=checkpoint_data["v"],
                            ts=checkpoint_data["ts"],
                            channel_values=checkpoint_data["channel_values"],
                            channel_versions=checkpoint_data["channel_versions"],
                            versions_seen=checkpoint_data["versions_seen"],
                            pending_sends=checkpoint_data["pending_sends"]
                        )
                        
                        # Create metadata
                        metadata = CheckpointMetadata(
                            source="redis",
                            step=checkpoint_data.get("step", -1),
                            writes=checkpoint_data.get("writes", {}),
                            parents=checkpoint_data.get("parents", {})
                        )
                        
                        checkpoints.append((checkpoint, metadata))
                        
                except Exception as e:
                    logger.warning(f"Error deserializing checkpoint {checkpoint_id}: {str(e)}")
                    continue
            
            logger.debug(f"Retrieved {len(checkpoints)} checkpoints from Redis for thread {thread_id}")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Error listing checkpoints from Redis: {str(e)}")
            return []