"""
Direct authentication service that bypasses Pydantic model validation.

This service handles user authentication using direct MongoDB operations.
"""

import os
import jwt
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-in-production-12345678901234567890")
ALGORITHM = "HS256"

security = HTTPBearer()

class DirectAuthService:
    """Direct database operations for authentication."""
    
    def __init__(self):
        self.mongo_uri = os.getenv("INFRA_MIND_MONGODB_URL", 
                                  "mongodb://admin:password@localhost:27017/infra_mind?authSource=admin")
    
    async def get_database_connection(self):
        """Get database connection."""
        client = AsyncIOMotorClient(self.mongo_uri)
        db = client.get_database("infra_mind")
        return client, db
    
    def verify_token(self, token: str) -> dict:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                SECRET_KEY, 
                algorithms=[ALGORITHM],
                audience="infra-mind-api",
                issuer="infra-mind"
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def get_user_by_id_direct(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using direct database query."""
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
    
    async def get_current_user_direct(
        self, 
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ) -> Dict[str, Any]:
        """Get current user using direct database operations."""
        # Verify token
        payload = self.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Get user directly from database
        user = await self.get_user_by_id_direct(user_id)
        
        if not user or not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Return user data as dict instead of Pydantic model
        return {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": user.get("role", "user"),
            "is_active": user.get("is_active", True)
        }


# Global instance
direct_auth_service = DirectAuthService()

# Dependency function
async def get_current_user_direct(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Dependency function to get current user without Pydantic models."""
    return await direct_auth_service.get_current_user_direct(credentials)