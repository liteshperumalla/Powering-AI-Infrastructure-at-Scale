"""
Direct database share service that bypasses Pydantic model validation.

This service handles report sharing functionality using direct MongoDB operations
to avoid Pydantic validation issues with mixed data structures.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException, status
from loguru import logger
import uuid


class DirectShareService:
    """Direct database operations for sharing functionality."""
    
    def __init__(self):
        self.mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", 
                                  "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    
    async def get_database_connection(self):
        """Get database connection."""
        client = AsyncIOMotorClient(self.mongo_uri)
        db = client.get_database("infra_mind")
        return client, db
    
    async def resolve_user_email_to_id(self, email: str) -> Optional[str]:
        """Resolve user email to user ID."""
        client, db = await self.get_database_connection()
        try:
            user = await db.users.find_one({"email": email})
            if user:
                return str(user["_id"])
            return None
        finally:
            client.close()
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        client, db = await self.get_database_connection()
        try:
            try:
                user = await db.users.find_one({"_id": ObjectId(user_id)})
            except:
                # Try string ID if ObjectId fails
                user = await db.users.find_one({"user_id": user_id})
            return user
        finally:
            client.close()
    
    async def get_report_raw(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report document directly from database."""
        client, db = await self.get_database_connection()
        try:
            try:
                report = await db.reports.find_one({"_id": ObjectId(report_id)})
            except:
                # Try with report_id field if ObjectId fails
                report = await db.reports.find_one({"report_id": report_id})
            return report
        finally:
            client.close()
    
    async def share_report_direct(
        self, 
        report_id: str, 
        owner_id: str, 
        share_with_user_id: str, 
        permission: str = "view"
    ) -> bool:
        """Share report using direct database operations."""
        client, db = await self.get_database_connection()
        try:
            # Get the report
            report = await self.get_report_raw(report_id)
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report {report_id} not found"
                )
            
            # Check ownership
            report_user_id = str(report.get("user_id"))
            shared_with = report.get("shared_with", [])
            sharing_permissions = report.get("sharing_permissions", {})
            
            # Verify the current user has permission to share
            if not (report_user_id == owner_id or sharing_permissions.get(owner_id) == "admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to share this report"
                )
            
            # Update sharing information
            if share_with_user_id not in shared_with:
                shared_with.append(share_with_user_id)
            sharing_permissions[share_with_user_id] = permission
            
            # Update the report using direct query
            update_query = {"$set": {
                "shared_with": shared_with,
                "sharing_permissions": sharing_permissions,
                "updated_at": datetime.now(timezone.utc)
            }}
            
            # Try ObjectId first, then report_id field
            try:
                result = await db.reports.update_one(
                    {"_id": ObjectId(report_id)}, 
                    update_query
                )
            except:
                result = await db.reports.update_one(
                    {"report_id": report_id}, 
                    update_query
                )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found or could not be updated"
                )
            
            logger.info(f"Successfully shared report {report_id} with user {share_with_user_id} ({permission})")
            return True
            
        finally:
            client.close()
    
    async def create_public_link_direct(
        self, 
        report_id: str, 
        user_id: str
    ) -> str:
        """Create public link using direct database operations."""
        client, db = await self.get_database_connection()
        try:
            # Get the report
            report = await self.get_report_raw(report_id)
            if not report:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Report {report_id} not found"
                )
            
            # Check permissions
            report_user_id = str(report.get("user_id"))
            sharing_permissions = report.get("sharing_permissions", {})
            
            if not (report_user_id == user_id or sharing_permissions.get(user_id) == "admin"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have admin access to create public links for this report"
                )
            
            # Generate public token
            public_token = str(uuid.uuid4())
            
            # Update the report
            update_query = {"$set": {
                "is_public": True,
                "public_link_token": public_token,
                "updated_at": datetime.now(timezone.utc)
            }}
            
            # Try ObjectId first, then report_id field
            try:
                result = await db.reports.update_one(
                    {"_id": ObjectId(report_id)}, 
                    update_query
                )
            except:
                result = await db.reports.update_one(
                    {"report_id": report_id}, 
                    update_query
                )
            
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Report not found or could not be updated"
                )
            
            logger.info(f"Successfully created public link for report {report_id}")
            return public_token
            
        finally:
            client.close()


# Global instance
direct_share_service = DirectShareService()