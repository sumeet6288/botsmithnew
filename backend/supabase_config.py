"""Supabase Configuration for Google OAuth Authentication

This module provides Supabase client configuration and JWT verification utilities.
For production use, set the environment variables in .env file.
"""

import os
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Check if Supabase is configured
SUPABASE_ENABLED = bool(SUPABASE_URL and SUPABASE_ANON_KEY and SUPABASE_JWT_SECRET)


def verify_supabase_token(token: str) -> Dict[str, Any]:
    """
    Verify Supabase JWT token.
    
    Args:
        token: JWT token from Supabase Auth
        
    Returns:
        Dict containing user information from token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not SUPABASE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Supabase authentication is not configured"
        )
    
    try:
        # Decode and verify JWT token
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated"
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Extract user information from Supabase JWT token.
    
    Args:
        token: JWT token from Supabase Auth
        
    Returns:
        Dict containing user_id, email, and other user metadata
    """
    payload = verify_supabase_token(token)
    
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "email_verified": payload.get("email_confirmed_at") is not None,
        "provider": payload.get("app_metadata", {}).get("provider", "email"),
        "user_metadata": payload.get("user_metadata", {}),
    }


def is_supabase_enabled() -> bool:
    """Check if Supabase authentication is properly configured."""
    return SUPABASE_ENABLED
