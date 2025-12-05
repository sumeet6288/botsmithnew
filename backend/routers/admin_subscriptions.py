from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import os

router = APIRouter(prefix="/admin/subscriptions", tags=["admin-subscriptions"])

# MongoDB setup
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'chatbase_db')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]
users_collection = db.users
subscriptions_collection = db.subscriptions
plans_collection = db.plans

# Request Models
class ExtendSubscriptionRequest(BaseModel):
    days: int = Field(description="Number of days to extend subscription", gt=0)

class ChangePlanRequest(BaseModel):
    plan_id: str = Field(description="New plan ID")

class LifetimeAccessRequest(BaseModel):
    grant_lifetime: bool = Field(description="Grant or revoke lifetime access")

@router.get("/{user_id}")
async def get_user_subscription_details(user_id: str):
    """
    Get detailed subscription information for a user
    """
    try:
        # Get user from database (using 'id' field)
        user = await users_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get subscription (using 'user_id' field which stores the user's id)
        subscription = await subscriptions_collection.find_one({"user_id": user_id})
        if not subscription:
            # Create default subscription if not exists
            subscription = {
                "user_id": user_id,
                "plan_id": user.get("plan_id", "free"),
                "status": "active",
                "started_at": datetime.utcnow(),
                "expires_at": None,
                "auto_renew": False,
                "lifetime_access": user.get("lifetime_access", False),
                "usage": {}
            }
            await subscriptions_collection.insert_one(subscription)
        
        # Get plan details
        plan_id = subscription.get("plan_id", user.get("plan_id", "free"))
        plan = await plans_collection.find_one({"id": plan_id})
        
        if not plan:
            plan = {
                "id": "free",
                "name": "Free",
                "price": 0.0,
                "description": "Free plan"
            }
        
        # Calculate days remaining
        days_remaining = None
        expires_at = subscription.get("expires_at")
        lifetime_access = subscription.get("lifetime_access", user.get("lifetime_access", False))
        
        if lifetime_access:
            days_remaining = "Lifetime"
        elif expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            days_remaining = (expires_at - datetime.utcnow()).days
            if days_remaining < 0:
                days_remaining = 0
        
        # Convert ObjectIds to strings
        if "_id" in subscription:
            subscription["_id"] = str(subscription["_id"])
        if "_id" in plan:
            plan["_id"] = str(plan["_id"])
        if "_id" in user:
            user["_id"] = str(user["_id"])
        
        return {
            "user": {
                "user_id": user.get("id"),  # Use 'id' field from user document
                "name": user.get("name"),
                "email": user.get("email"),
                "created_at": user.get("created_at")
            },
            "subscription": {
                **subscription,
                "days_remaining": days_remaining
            },
            "plan": plan
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subscription: {str(e)}")

@router.put("/{user_id}/extend")
async def extend_subscription(
    user_id: str,
    request: ExtendSubscriptionRequest
):
    """
    Extend user's subscription by specified number of days
    """
    try:
        # Get subscription
        subscription = await subscriptions_collection.find_one({"user_id": user_id})
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription not found")
        
        # Check if user has lifetime access
        if subscription.get("lifetime_access", False):
            raise HTTPException(status_code=400, detail="User has lifetime access, cannot extend")
        
        # Extend subscription
        current_expiry = subscription.get("expires_at")
        if current_expiry:
            if isinstance(current_expiry, str):
                current_expiry = datetime.fromisoformat(current_expiry.replace('Z', '+00:00'))
            # If already expired or about to expire, extend from now
            if current_expiry < datetime.utcnow():
                new_expiry = datetime.utcnow() + timedelta(days=request.days)
            else:
                new_expiry = current_expiry + timedelta(days=request.days)
        else:
            # No expiry set, extend from now
            new_expiry = datetime.utcnow() + timedelta(days=request.days)
        
        # Update subscription
        result = await subscriptions_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "expires_at": new_expiry,
                    "status": "active",
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Also update user document
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "subscription_expires_at": new_expiry,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to extend subscription")
        
        return {
            "message": f"Subscription extended by {request.days} days",
            "new_expiry": new_expiry.isoformat(),
            "days_added": request.days
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extending subscription: {str(e)}")

@router.post("/{user_id}/renew")
async def renew_user_subscription(user_id: str):
    """
    Renew user's subscription for another 30 days
    """
    try:
        return await extend_subscription(
            user_id,
            ExtendSubscriptionRequest(days=30)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error renewing subscription: {str(e)}")

@router.put("/{user_id}/lifetime")
async def toggle_lifetime_access(
    user_id: str,
    request: LifetimeAccessRequest
):
    """
    Grant or revoke lifetime access for a user
    """
    try:
        # Update subscription
        update_data = {
            "lifetime_access": request.grant_lifetime,
            "status": "active" if request.grant_lifetime else "active",
            "updated_at": datetime.utcnow()
        }
        
        # If granting lifetime, remove expiry date
        if request.grant_lifetime:
            update_data["expires_at"] = None
        
        result = await subscriptions_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        # Also update user document
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "lifetime_access": request.grant_lifetime,
                    "subscription_expires_at": None if request.grant_lifetime else datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            # Try to create subscription if it doesn't exist
            subscription = {
                "user_id": user_id,
                "plan_id": "enterprise",
                "status": "active",
                "started_at": datetime.utcnow(),
                "expires_at": None,
                "lifetime_access": request.grant_lifetime,
                "auto_renew": False,
                "usage": {}
            }
            await subscriptions_collection.insert_one(subscription)
        
        action = "granted" if request.grant_lifetime else "revoked"
        return {
            "message": f"Lifetime access {action} successfully",
            "lifetime_access": request.grant_lifetime
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating lifetime access: {str(e)}")

@router.put("/{user_id}/plan")
async def change_user_plan(
    user_id: str,
    request: ChangePlanRequest
):
    """
    Change user's subscription plan
    """
    try:
        # Verify plan exists
        plan = await plans_collection.find_one({"id": request.plan_id})
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        # Update subscription
        result = await subscriptions_collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "plan_id": request.plan_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Also update user document
        await users_collection.update_one(
            {"id": user_id},
            {
                "$set": {
                    "plan_id": request.plan_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            # Try to create subscription if it doesn't exist
            subscription = {
                "user_id": user_id,
                "plan_id": request.plan_id,
                "status": "active",
                "started_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=30) if request.plan_id != "free" else None,
                "lifetime_access": False,
                "auto_renew": True,
                "usage": {}
            }
            await subscriptions_collection.insert_one(subscription)
        
        return {
            "message": f"Plan changed to {plan['name']} successfully",
            "plan": {
                "id": plan["id"],
                "name": plan["name"],
                "price": plan["price"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error changing plan: {str(e)}")

@router.get("/plans")
async def get_all_plans():
    """
    Get all available plans for admin to choose from
    """
    try:
        plans = await plans_collection.find({"is_active": True}).to_list(100)
        
        # Convert ObjectIds to strings
        for plan in plans:
            if "_id" in plan:
                plan["_id"] = str(plan["_id"])
        
        return {"plans": plans}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching plans: {str(e)}")
