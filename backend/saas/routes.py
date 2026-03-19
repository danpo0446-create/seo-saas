"""
SaaS API Routes - Stripe, Subscriptions, BYOAK
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse, CheckoutStatusResponse
)

from .plans import PLANS, get_plan, get_all_plans
from .models import (
    CreateCheckoutRequest, CheckoutResponse, BillingPortalRequest, BillingPortalResponse,
    UserApiKeysUpdate, UserApiKeysResponse, SubscriptionResponse, SubscriptionUsage
)
from .subscription_service import SubscriptionService, ApiKeyService
from auth import get_current_user

# Lazy database connection
_client = None
_db = None

def get_db():
    """Get database connection (lazy loading)"""
    global _client, _db
    if _client is None:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        _client = AsyncIOMotorClient(mongo_url)
        _db = _client[os.environ.get('DB_NAME', 'seo_saas')]
    return _db

# Router
saas_router = APIRouter(prefix="/api/saas", tags=["SaaS"])


# ============ PLANS ROUTES ============

@saas_router.get("/plans")
async def get_plans():
    """Get all available subscription plans"""
    plans = get_all_plans()
    # Remove internal fields
    public_plans = {}
    for plan_id, plan in plans.items():
        if plan_id != "free":
            public_plans[plan_id] = {
                "id": plan["id"],
                "name": plan["name"],
                "price_eur": plan["price_eur"],
                "sites_limit": plan["sites_limit"],
                "articles_limit": plan["articles_limit"],
                "features": plan["features"]
            }
    return public_plans


# ============ SUBSCRIPTION ROUTES ============

@saas_router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(user: dict = Depends(get_current_user)):
    """Get current user's subscription"""
    db = get_db()
    service = SubscriptionService(db)
    sub = await service.get_or_create_subscription(user["id"])
    return SubscriptionResponse(**sub)

@saas_router.get("/subscription/usage", response_model=SubscriptionUsage)
async def get_usage(user: dict = Depends(get_current_user)):
    """Get subscription usage statistics"""
    db = get_db()
    service = SubscriptionService(db)
    return await service.get_usage_stats(user["id"])


# ============ STRIPE CHECKOUT ROUTES ============

@saas_router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest, http_request: Request, 
                                   user: dict = Depends(get_current_user)):
    """Create Stripe checkout session for subscription"""
    db = get_db()
    plan = get_plan(request.plan)
    if not plan or request.plan == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Build URLs
    origin = request.origin_url.rstrip("/")
    success_url = f"{origin}/billing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/pricing"
    
    # Initialize Stripe
    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(plan["price_eur"]),
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["id"],
            "user_email": user["email"],
            "plan": request.plan,
            "plan_name": plan["name"]
        }
    )
    
    try:
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "session_id": session.session_id,
            "plan": request.plan,
            "amount": float(plan["price_eur"]),
            "currency": "eur",
            "status": "initiated",
            "payment_status": "pending",
            "metadata": {
                "plan_name": plan["name"],
                "user_email": user["email"]
            },
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        await db.payment_transactions.insert_one(transaction)
        
        logging.info(f"[STRIPE] Created checkout session {session.session_id} for user {user['id']}, plan {request.plan}")
        
        return CheckoutResponse(url=session.url, session_id=session.session_id)
    except Exception as e:
        logging.error(f"[STRIPE] Checkout error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create checkout: {str(e)}")

@saas_router.get("/checkout/status/{session_id}")
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user)):
    """Get checkout session status and update subscription if paid"""
    db = get_db()
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        status = await stripe_checkout.get_checkout_status(session_id)
        
        # Get the transaction
        transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        # Check if already processed
        if transaction.get("status") == "paid":
            return {
                "status": status.status,
                "payment_status": status.payment_status,
                "already_processed": True
            }
        
        # Update transaction status
        new_status = "paid" if status.payment_status == "paid" else status.status
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {
                "status": new_status,
                "payment_status": status.payment_status,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # If paid, upgrade subscription
        if status.payment_status == "paid" and transaction.get("status") != "paid":
            service = SubscriptionService(db)
            plan = transaction.get("plan", "starter")
            await service.upgrade_subscription(
                user_id=user["id"],
                plan=plan,
                stripe_customer_id=status.metadata.get("customer_id"),
                stripe_subscription_id=session_id
            )
            logging.info(f"[STRIPE] Payment successful, upgraded user {user['id']} to {plan}")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total,
            "currency": status.currency
        }
    except Exception as e:
        logging.error(f"[STRIPE] Status check error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


# ============ BYOAK ROUTES ============

@saas_router.get("/api-keys", response_model=UserApiKeysResponse)
async def get_api_keys(user: dict = Depends(get_current_user)):
    """Get user's API keys status (not the actual keys)"""
    db = get_db()
    service = ApiKeyService(db)
    return await service.get_user_keys(user["id"])

@saas_router.put("/api-keys", response_model=UserApiKeysResponse)
async def update_api_keys(keys: UserApiKeysUpdate, user: dict = Depends(get_current_user)):
    """Update user's API keys"""
    db = get_db()
    service = ApiKeyService(db)
    return await service.update_keys(
        user_id=user["id"],
        openai_key=keys.openai_key,
        gemini_key=keys.gemini_key,
        resend_key=keys.resend_key,
        pexels_key=keys.pexels_key
    )

@saas_router.post("/api-keys/validate")
async def validate_api_key(key_type: str, key: str, user: dict = Depends(get_current_user)):
    """Validate an API key"""
    db = get_db()
    service = ApiKeyService(db)
    is_valid = await service.validate_key(key_type, key)
    return {"valid": is_valid, "key_type": key_type}
