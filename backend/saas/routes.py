"""
SaaS API Routes - Stripe, Subscriptions, BYOAK
"""
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorClient
import jwt

from emergentintegrations.payments.stripe.checkout import (
    StripeCheckout, CheckoutSessionRequest, CheckoutSessionResponse, CheckoutStatusResponse
)

from .plans import PLANS, get_plan, get_all_plans
from .models import (
    CreateCheckoutRequest, CheckoutResponse, BillingPortalRequest, BillingPortalResponse,
    UserApiKeysUpdate, UserApiKeysResponse, SubscriptionResponse, SubscriptionUsage
)
from .subscription_service import SubscriptionService, ApiKeyService

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'seo-automation-secret-key-2024')
JWT_ALGORITHM = "HS256"

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

# Security
security = HTTPBearer()

async def get_current_user_saas(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Auth dependency for SaaS routes"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        db = get_db()
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

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
async def get_subscription(user: dict = Depends(get_current_user_saas)):
    """Get current user's subscription"""
    db = get_db()
    service = SubscriptionService(db)
    sub = await service.get_or_create_subscription(user["id"])
    return SubscriptionResponse(**sub)

@saas_router.get("/subscription/usage", response_model=SubscriptionUsage)
async def get_usage(user: dict = Depends(get_current_user_saas)):
    """Get subscription usage statistics"""
    db = get_db()
    service = SubscriptionService(db)
    return await service.get_usage_stats(user["id"])


# ============ STRIPE CHECKOUT ROUTES ============

@saas_router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout_session(request: CreateCheckoutRequest, http_request: Request, 
                                   user: dict = Depends(get_current_user_saas)):
    """Create Stripe checkout session for subscription"""
    db = get_db()
    plan = get_plan(request.plan)
    if not plan or request.plan == "free":
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    # Determine price based on billing period
    is_annual = request.billing_period == "annual"
    amount = plan["price_annual_eur"] if is_annual else plan["price_eur"]
    
    # Build URLs
    origin = request.origin_url.rstrip("/")
    success_url = f"{origin}/app/billing?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin}/pricing"
    
    # Initialize Stripe
    webhook_url = f"{str(http_request.base_url).rstrip('/')}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
    
    # Create checkout session
    checkout_request = CheckoutSessionRequest(
        amount=float(amount),
        currency="eur",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={
            "user_id": user["id"],
            "user_email": user["email"],
            "plan": request.plan,
            "plan_name": plan["name"],
            "billing_period": request.billing_period
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
            "billing_period": request.billing_period,
            "amount": float(amount),
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
async def get_checkout_status(session_id: str, user: dict = Depends(get_current_user_saas)):
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


# ============ BILLING PORTAL ============

@saas_router.post("/billing-portal", response_model=BillingPortalResponse)
async def create_billing_portal(request: BillingPortalRequest, user: dict = Depends(get_current_user_saas)):
    """Create Stripe billing portal session for subscription management"""
    db = get_db()
    
    # Get user's subscription
    sub = await db.subscriptions.find_one({"user_id": user["id"]}, {"_id": 0})
    if not sub or not sub.get("stripe_customer_id"):
        raise HTTPException(status_code=400, detail="Nu ai o subscripție activă cu Stripe")
    
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    import stripe
    stripe.api_key = stripe_api_key
    
    try:
        session = stripe.billing_portal.Session.create(
            customer=sub["stripe_customer_id"],
            return_url=f"{request.origin_url}/app/billing"
        )
        return BillingPortalResponse(url=session.url)
    except Exception as e:
        logging.error(f"[STRIPE] Billing portal error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create billing portal: {str(e)}")


# ============ ANALYTICS ROUTES ============

@saas_router.get("/analytics/overview")
async def get_analytics_overview(user: dict = Depends(get_current_user_saas)):
    """Get analytics overview for dashboard"""
    db = get_db()
    from datetime import timedelta
    
    # Get date ranges
    now = datetime.now(timezone.utc)
    thirty_days_ago = now - timedelta(days=30)
    seven_days_ago = now - timedelta(days=7)
    
    # Get subscription
    sub = await db.subscriptions.find_one({"user_id": user["id"]}, {"_id": 0})
    
    # Count articles
    total_articles = await db.articles.count_documents({"user_id": user["id"]})
    articles_this_month = await db.articles.count_documents({
        "user_id": user["id"],
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    })
    articles_this_week = await db.articles.count_documents({
        "user_id": user["id"],
        "created_at": {"$gte": seven_days_ago.isoformat()}
    })
    
    # Count published articles
    published_articles = await db.articles.count_documents({
        "user_id": user["id"],
        "status": "published"
    })
    
    # Count sites
    total_sites = await db.wordpress_configs.count_documents({"user_id": user["id"]})
    
    # Count keywords
    total_keywords = await db.keywords.count_documents({"user_id": user["id"]})
    
    # Count backlinks
    total_backlinks = await db.backlinks.count_documents({"user_id": user["id"]})
    
    # Get scheduled articles
    scheduled_articles = await db.articles.count_documents({
        "user_id": user["id"],
        "status": "scheduled"
    })
    
    # Calculate cost per article (based on plan)
    plan_cost = {
        "free": 0, "starter": 19, "pro": 49, "agency": 99, "enterprise": 199
    }.get(sub.get("plan", "free"), 0)
    
    cost_per_article = 0
    if articles_this_month > 0 and plan_cost > 0:
        cost_per_article = round(plan_cost / articles_this_month, 2)
    
    # Estimate value (average article worth ~€5-20 in SEO value)
    estimated_value = total_articles * 12  # €12 average estimated value per article
    roi_percentage = 0
    if plan_cost > 0:
        monthly_value = articles_this_month * 12
        roi_percentage = round(((monthly_value - plan_cost) / plan_cost) * 100, 1) if plan_cost > 0 else 0
    
    return {
        "articles": {
            "total": total_articles,
            "this_month": articles_this_month,
            "this_week": articles_this_week,
            "published": published_articles,
            "scheduled": scheduled_articles
        },
        "sites": {
            "total": total_sites,
            "limit": sub.get("sites_limit", 1) if sub else 1
        },
        "keywords": {
            "total": total_keywords
        },
        "backlinks": {
            "total": total_backlinks
        },
        "financial": {
            "plan_cost": plan_cost,
            "cost_per_article": cost_per_article,
            "estimated_value": estimated_value,
            "roi_percentage": roi_percentage
        },
        "subscription": {
            "plan": sub.get("plan", "free") if sub else "free",
            "status": sub.get("status", "expired") if sub else "expired",
            "articles_used": sub.get("articles_used_this_month", 0) if sub else 0,
            "articles_limit": sub.get("articles_limit", 0) if sub else 0
        }
    }


# ============ BYOAK ROUTES ============

@saas_router.get("/api-keys", response_model=UserApiKeysResponse)
async def get_api_keys(user: dict = Depends(get_current_user_saas)):
    """Get user's API keys status (not the actual keys)"""
    db = get_db()
    service = ApiKeyService(db)
    return await service.get_user_keys(user["id"])

@saas_router.put("/api-keys", response_model=UserApiKeysResponse)
async def update_api_keys(keys: UserApiKeysUpdate, user: dict = Depends(get_current_user_saas)):
    """Update user's API keys"""
    db = get_db()
    service = ApiKeyService(db)
    return await service.update_keys(
        user_id=user["id"],
        openai_key=keys.openai_key,
        gemini_key=keys.gemini_key,
        resend_key=keys.resend_key,
        sendgrid_key=keys.sendgrid_key,
        pexels_key=keys.pexels_key,
        facebook_app_id=keys.facebook_app_id,
        facebook_app_secret=keys.facebook_app_secret,
        linkedin_client_id=keys.linkedin_client_id,
        linkedin_client_secret=keys.linkedin_client_secret
    )

@saas_router.post("/api-keys/validate")
async def validate_api_key(key_type: str, key: str, user: dict = Depends(get_current_user_saas)):
    """Validate an API key"""
    db = get_db()
    service = ApiKeyService(db)
    is_valid = await service.validate_key(key_type, key)
    return {"valid": is_valid, "key_type": key_type}


# ============ INVOICE ROUTES ============

from .invoice_service import invoice_generator
from .models import InvoiceResponse
from fastapi.responses import Response

@saas_router.get("/invoices")
async def get_invoices(user: dict = Depends(get_current_user_saas)):
    """Get all invoices for user"""
    db = get_db()
    invoices = await db.invoices.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return invoices

@saas_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, user: dict = Depends(get_current_user_saas)):
    """Get a specific invoice"""
    db = get_db()
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@saas_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, user: dict = Depends(get_current_user_saas)):
    """Download invoice as PDF"""
    db = get_db()
    
    # Get invoice
    invoice = await db.invoices.find_one(
        {"id": invoice_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # Get user info
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    
    # Generate PDF
    invoice_data = {
        "invoice_number": invoice["invoice_number"],
        "date": invoice["created_at"],
        "customer_name": user_data.get("name", "Client"),
        "customer_email": user_data.get("email", ""),
        "plan_name": invoice["plan_name"],
        "billing_period": invoice.get("billing_period", "monthly"),
        "amount": invoice["amount"],
        "currency": invoice.get("currency", "EUR")
    }
    
    pdf_bytes = invoice_generator.generate_invoice(invoice_data)
    
    if not pdf_bytes:
        raise HTTPException(status_code=500, detail="PDF generation not available")
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=factura-{invoice['invoice_number']}.pdf"
        }
    )

@saas_router.post("/invoices/generate")
async def generate_invoice_for_transaction(
    transaction_id: str,
    user: dict = Depends(get_current_user_saas)
):
    """Generate invoice for a paid transaction"""
    db = get_db()
    
    # Get transaction
    transaction = await db.payment_transactions.find_one(
        {"id": transaction_id, "user_id": user["id"], "status": "paid"},
        {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Paid transaction not found")
    
    # Check if invoice already exists
    existing = await db.invoices.find_one(
        {"user_id": user["id"], "metadata.transaction_id": transaction_id},
        {"_id": 0}
    )
    if existing:
        return existing
    
    # Get user info
    user_data = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    
    # Create invoice
    invoice_data = {
        "plan_name": transaction.get("metadata", {}).get("plan_name", transaction.get("plan")),
        "billing_period": transaction.get("billing_period", "monthly"),
        "amount": transaction["amount"],
        "currency": transaction.get("currency", "EUR"),
        "customer_name": user_data.get("name"),
        "customer_email": user_data.get("email")
    }
    
    invoice = await invoice_generator.save_invoice(db, user["id"], invoice_data)
    
    # Link invoice to transaction
    await db.invoices.update_one(
        {"id": invoice["id"]},
        {"$set": {"metadata": {"transaction_id": transaction_id}}}
    )
    
    return invoice



# ============ PUBLIC CONTENT ROUTES ============

@saas_router.get("/content/{page_id}")
async def get_public_content(page_id: str):
    """Get public page content (no auth required)"""
    db = get_db()
    
    if page_id not in ["contact", "terms", "privacy"]:
        raise HTTPException(status_code=404, detail="Page not found")
    
    content = await db.page_content.find_one({"page_id": page_id}, {"_id": 0})
    
    if not content:
        # Return default content
        defaults = {
            "contact": {
                "email": "support@seoautomation.ro",
                "phone": "+40 721 234 567",
                "address": "Bucuresti, Romania",
                "hours": "Luni - Vineri, 9:00 - 18:00"
            },
            "terms": {"last_updated": "Martie 2026"},
            "privacy": {"last_updated": "Martie 2026"}
        }
        return {"page_id": page_id, "content": defaults.get(page_id, {})}
    
    return content
