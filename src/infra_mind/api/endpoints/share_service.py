"""
Direct database share service that bypasses Pydantic model validation.

This service handles report sharing functionality using direct MongoDB operations
to avoid Pydantic validation issues with mixed data structures.

Note: Refactored to use dependency injection - database passed via constructor.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from fastapi import HTTPException, status
from loguru import logger
import uuid


class DirectShareService:
    """
    Direct database operations for sharing functionality.

    Note: Now uses dependency injection - database passed in constructor.
    No more creating clients per method call!
    """

    def __init__(self, db):
        """
        Initialize with injected database.

        Args:
            db: Database instance from DatabaseDep dependency injection
        """
        self.db = db
    
    async def resolve_user_email_to_id(self, email: str) -> Optional[str]:
        """Resolve user email to user ID."""
        user = await self.db.users.find_one({"email": email})
        if user:
            return str(user["_id"])
        return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        try:
            user = await self.db.users.find_one({"_id": ObjectId(user_id)})
        except Exception as e:
            # Try string ID if ObjectId fails
            user = await self.db.users.find_one({"user_id": user_id})
        return user
    
    async def get_report_raw(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Get report document directly from database."""
        try:
            report = await self.db.reports.find_one({"_id": ObjectId(report_id)})
        except Exception as e:
            # Try with report_id field if ObjectId fails
            report = await self.db.reports.find_one({"report_id": report_id})
        return report
    
    async def share_report_direct(
        self,
        report_id: str,
        owner_id: str,
        share_with_user_id: str,
        permission: str = "view"
    ) -> bool:
        """Share report using direct database operations."""
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
            result = await self.db.reports.update_one(
                {"_id": ObjectId(report_id)},
                update_query
            )
        except Exception as e:
            result = await self.db.reports.update_one(
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
    
    async def create_public_link_direct(
        self,
        report_id: str,
        user_id: str
    ) -> str:
        """Create public link using direct database operations."""
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
            result = await self.db.reports.update_one(
                {"_id": ObjectId(report_id)},
                update_query
            )
        except Exception as e:
            result = await self.db.reports.update_one(
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


# NOTE: Global instance removed - now instantiated with DI in endpoints
# Example: service = DirectShareService(db)