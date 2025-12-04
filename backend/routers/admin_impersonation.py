from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import jwt
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/impersonation", tags=["Admin Impersonation"])

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGO_URL", "mongodb://localhost:27017"))
db = client[os.getenv("DB_NAME", "chatbase_db")]

SECRET_KEY = os.getenv("SECRET_KEY", "chatbase-secret-key-change-in-production-2024")
ALGORITHM = "HS256"

class ImpersonationResponse(BaseModel):
    success: bool
    impersonation_token: str
    user_id: str
    user_email: str
    expires_in: int
    impersonation_url: str

@router.post("/generate-token/{user_id}", response_model=ImpersonationResponse)
async def generate_impersonation_token(
    user_id: str,
    # current_admin: dict = Depends(get_current_user)  # In production, verify admin role
):
    """
    Generate an impersonation token that allows admin to log in as a specific user.
    Token is valid for 1 hour.
    """
    try:
        # Get user details - try both user_id and id fields
        user = await db.users.find_one({"$or": [{"user_id": user_id}, {"id": user_id}]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if admin is trying to impersonate (in production, verify admin role)
        # if current_admin.get("role") != "admin":
        #     raise HTTPException(status_code=403, detail="Only admins can impersonate users")
        
        # Create impersonation token (valid for 1 hour)
        expiration = datetime.utcnow() + timedelta(hours=1)
        # Use whichever ID field exists
        actual_user_id = user.get("user_id") or user.get("id")
        token_data = {
            "user_id": actual_user_id,
            "id": actual_user_id,  # Support both field names
            "email": user["email"],
            "name": user.get("name", "User"),
            "role": user.get("role", "user"),
            "impersonated": True,  # Flag to indicate this is an impersonation session
            "exp": expiration
        }
        
        # Generate JWT token
        impersonation_token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        
        # Log the impersonation attempt
        logger.info(f"Admin impersonation token generated for user {user_id} ({user['email']})")
        
        # Create impersonation URL
        impersonation_url = f"/admin-login?token={impersonation_token}"
        
        return ImpersonationResponse(
            success=True,
            impersonation_token=impersonation_token,
            user_id=user_id,
            user_email=user["email"],
            expires_in=3600,  # 1 hour in seconds
            impersonation_url=impersonation_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating impersonation token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate impersonation token: {str(e)}")

@router.post("/verify-token")
async def verify_impersonation_token(token: str):
    """
    Verify an impersonation token and return user data.
    """
    try:
        # Decode and verify token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Check if token is expired
        exp_timestamp = payload.get("exp")
        if exp_timestamp and datetime.utcnow().timestamp() > exp_timestamp:
            raise HTTPException(status_code=401, detail="Impersonation token has expired")
        
        # Verify this is an impersonation token
        if not payload.get("impersonated"):
            raise HTTPException(status_code=403, detail="Invalid impersonation token")
        
        # Get fresh user data from database
        user = await db.users.find_one({"user_id": payload["user_id"]})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Remove sensitive fields
        user.pop("password", None)
        user.pop("_id", None)
        
        return {
            "success": True,
            "user": user,
            "impersonated": True,
            "message": "You are logged in as this user (Admin Impersonation Mode)"
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Impersonation token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid impersonation token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying impersonation token: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to verify token: {str(e)}")
