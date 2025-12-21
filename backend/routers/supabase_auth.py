"""Supabase Authentication Routes for Google OAuth

This module provides endpoints for Supabase-based authentication including Google OAuth.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging

from supabase_config import (
    verify_supabase_token,
    get_user_from_token,
    is_supabase_enabled,
    SUPABASE_URL
)
from models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth/supabase", tags=["Supabase Auth"])

# Database will be injected
db = None

def init_router(database):
    """Initialize router with database connection."""
    global db
    db = database


class SupabaseAuthResponse(BaseModel):
    success: bool
    user: dict
    message: str


class SupabaseTokenRequest(BaseModel):
    token: str


@router.get("/status")
async def get_supabase_status():
    """
    Check if Supabase authentication is enabled and configured.
    """
    return {
        "enabled": is_supabase_enabled(),
        "supabase_url": SUPABASE_URL if is_supabase_enabled() else None,
        "message": "Supabase authentication is ready" if is_supabase_enabled() 
                   else "Supabase not configured. Set SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_JWT_SECRET in .env"
    }


@router.post("/verify", response_model=SupabaseAuthResponse)
async def verify_and_sync_user(request: SupabaseTokenRequest):
    """
    Verify Supabase JWT token and sync user to local database.
    
    This endpoint should be called after successful Google OAuth login via Supabase.
    It will:
    1. Verify the Supabase JWT token
    2. Extract user information
    3. Create or update user in local database
    4. Return user information
    """
    try:
        # Verify token and get user info
        user_info = get_user_from_token(request.token)
        
        users_collection = db["users"]
        
        # Check if user exists in local database
        existing_user = await users_collection.find_one({"email": user_info["email"]})
        
        if existing_user:
            # Update existing user with Supabase info
            await users_collection.update_one(
                {"email": user_info["email"]},
                {
                    "$set": {
                        "supabase_user_id": user_info["user_id"],
                        "oauth_provider": user_info["provider"],
                        "email_verified": user_info["email_verified"],
                        "last_login": user_info.get("last_sign_in_at"),
                    }
                }
            )
            user_dict = existing_user
        else:
            # Create new user from Google OAuth data
            new_user = {
                "email": user_info["email"],
                "supabase_user_id": user_info["user_id"],
                "oauth_provider": user_info["provider"],
                "email_verified": user_info["email_verified"],
                "full_name": user_info["user_metadata"].get("full_name", ""),
                "avatar_url": user_info["user_metadata"].get("avatar_url", ""),
                "plan_id": "free",  # Default to free plan
                "role": "user",
                "status": "active",
            }
            result = await users_collection.insert_one(new_user)
            new_user["_id"] = result.inserted_id
            user_dict = new_user
        
        return SupabaseAuthResponse(
            success=True,
            user={
                "id": str(user_dict["_id"]),
                "email": user_dict["email"],
                "full_name": user_dict.get("full_name", ""),
                "avatar_url": user_dict.get("avatar_url", ""),
                "plan_id": user_dict.get("plan_id", "free"),
            },
            message="User authenticated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Supabase authentication: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.get("/me")
async def get_current_user_from_supabase(
    authorization: Optional[str] = Header(None)
):
    """
    Get current user information from Supabase JWT token.
    
    Expects Authorization header: Bearer <token>
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authorization header provided"
        )
    
    try:
        # Extract token from "Bearer <token>" format
        token = authorization.replace("Bearer ", "")
        user_info = get_user_from_token(token)
        
        # Get user from local database
        users_collection = db["users"]
        user = await users_collection.find_one({"supabase_user_id": user_info["user_id"]})
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found in local database"
            )
        
        return {
            "id": str(user["_id"]),
            "email": user["email"],
            "full_name": user.get("full_name", ""),
            "avatar_url": user.get("avatar_url", ""),
            "plan_id": user.get("plan_id", "free"),
            "role": user.get("role", "user"),
            "status": user.get("status", "active"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )
