"""Razorpay subscription and payment management routes."""
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging
import hmac
import hashlib
from services.razorpay_service import RazorpayService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["razorpay"])

# Database instance
_db = None

def init_router(db):
    """Initialize router with database instance."""
    global _db
    _db = db


class CreateSubscriptionRequest(BaseModel):
    """Request model for creating a subscription."""
    plan_id: str  # starter, professional, etc.
    user_id: str
    user_email: str
    user_name: Optional[str] = None
    contact: Optional[str] = None


class SubscriptionActionRequest(BaseModel):
    """Request model for subscription actions."""
    subscription_id: str


@router.post("/create-subscription")
async def create_subscription(request: CreateSubscriptionRequest):
    """
    Create a Razorpay subscription for a plan.
    
    Returns the subscription details and payment link.
    """
    try:
        # Get payment settings from database
        payment_settings = await _db.payment_settings.find_one({})
        
        if not payment_settings or not payment_settings.get('razorpay', {}).get('enabled'):
            raise HTTPException(
                status_code=400,
                detail="Razorpay payment gateway is not enabled. Please contact administrator."
            )
        
        # Get plan ID from payment settings
        plans_mapping = payment_settings.get('razorpay', {}).get('plans', {})
        razorpay_plan_id = plans_mapping.get(request.plan_id.lower())
        
        if not razorpay_plan_id:
            raise HTTPException(
                status_code=400,
                detail=f"Plan {request.plan_id} does not have a Razorpay plan ID configured in Payment Gateway settings. Please contact administrator."
            )
        
        # Create subscription
        service = RazorpayService()
        
        customer_data = {
            "user_id": request.user_id,
            "plan_name": request.plan_id,
            "email": request.user_email,
            "name": request.user_name or request.user_email.split('@')[0],
            "contact": request.contact
        }
        
        result = await service.create_subscription(
            plan_id=razorpay_plan_id,
            customer_data=customer_data
        )
        
        # Store subscription details in database
        subscription_data = {
            "subscription_id": result.get("id"),
            "user_id": request.user_id,
            "plan_id": request.plan_id,
            "razorpay_plan_id": razorpay_plan_id,
            "status": result.get("status"),
            "created_at": result.get("created_at"),
            "razorpay_data": result
        }
        
        await _db.razorpay_subscriptions.insert_one(subscription_data)
        
        return {
            "success": True,
            "subscription_id": result.get("id"),
            "short_url": result.get("short_url"),
            "status": result.get("status"),
            "data": result
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create subscription: {str(e)}"
        )


@router.post("/cancel-subscription")
async def cancel_subscription(request: SubscriptionActionRequest):
    """
    Cancel a Razorpay subscription.
    """
    try:
        service = RazorpayService()
        result = await service.cancel_subscription(request.subscription_id)
        
        # Update database
        await _db.razorpay_subscriptions.update_one(
            {"subscription_id": request.subscription_id},
            {"$set": {"status": "cancelled"}}
        )
        
        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error cancelling subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel subscription: {str(e)}"
        )


@router.post("/pause-subscription")
async def pause_subscription(request: SubscriptionActionRequest):
    """
    Pause a Razorpay subscription.
    """
    try:
        service = RazorpayService()
        result = await service.pause_subscription(request.subscription_id)
        
        # Update database
        await _db.razorpay_subscriptions.update_one(
            {"subscription_id": request.subscription_id},
            {"$set": {"status": "paused"}}
        )
        
        return {
            "success": True,
            "message": "Subscription paused successfully",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error pausing subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause subscription: {str(e)}"
        )


@router.post("/resume-subscription")
async def resume_subscription(request: SubscriptionActionRequest):
    """
    Resume a paused Razorpay subscription.
    """
    try:
        service = RazorpayService()
        result = await service.resume_subscription(request.subscription_id)
        
        # Update database
        await _db.razorpay_subscriptions.update_one(
            {"subscription_id": request.subscription_id},
            {"$set": {"status": "active"}}
        )
        
        return {
            "success": True,
            "message": "Subscription resumed successfully",
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error resuming subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume subscription: {str(e)}"
        )


@router.post("/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle Razorpay webhook events.
    """
    try:
        # Get webhook signature from headers
        signature = request.headers.get("X-Razorpay-Signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing signature")
        
        # Get webhook body
        body = await request.body()
        
        # Verify signature
        payment_settings = await _db.payment_settings.find_one({})
        webhook_secret = payment_settings.get('razorpay', {}).get('webhook_secret', '')
        
        expected_signature = hmac.new(
            webhook_secret.encode('utf-8'),
            body,
            hashlib.sha256
        ).hexdigest()
        
        if not hmac.compare_digest(signature, expected_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Parse webhook payload
        import json
        payload = json.loads(body.decode('utf-8'))
        
        event_type = payload.get('event')
        entity = payload.get('payload', {}).get('subscription', {}).get('entity', {})
        
        logger.info(f"Received Razorpay webhook: {event_type}")
        
        # Handle different event types
        if event_type == 'subscription.activated':
            # Update subscription status
            await _db.razorpay_subscriptions.update_one(
                {"subscription_id": entity.get('id')},
                {"$set": {"status": "active"}}
            )
            
        elif event_type == 'subscription.charged':
            # Handle successful payment
            logger.info(f"Subscription charged: {entity.get('id')}")
            
        elif event_type == 'subscription.cancelled':
            # Handle cancellation
            await _db.razorpay_subscriptions.update_one(
                {"subscription_id": entity.get('id')},
                {"$set": {"status": "cancelled"}}
            )
            
        elif event_type == 'subscription.paused':
            # Handle pause
            await _db.razorpay_subscriptions.update_one(
                {"subscription_id": entity.get('id')},
                {"$set": {"status": "paused"}}
            )
        
        return {"success": True, "message": "Webhook processed"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process webhook: {str(e)}"
        )


@router.get("/subscription/{subscription_id}")
async def get_subscription(subscription_id: str):
    """
    Get subscription details.
    """
    try:
        service = RazorpayService()
        result = await service.get_subscription(subscription_id)
        
        return {
            "success": True,
            "data": result
        }
    
    except Exception as e:
        logger.error(f"Error fetching subscription: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch subscription: {str(e)}"
        )
