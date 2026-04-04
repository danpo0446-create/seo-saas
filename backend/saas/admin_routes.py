"""
Admin API Routes - User management, statistics, content management
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
import jwt
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .plans import PLANS

# JWT Config - read from environment, same as server.py
JWT_SECRET = os.environ.get('JWT_SECRET', 'seo-automation-secret-key-2024')
JWT_ALGORITHM = "HS256"

# Database
_client = None
_db = None

def get_db():
    """Get database connection"""
    global _client, _db
    if _client is None:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        _client = AsyncIOMotorClient(mongo_url)
        _db = _client[os.environ.get('DB_NAME', 'seo_saas')]
    return _db

# Security
security = HTTPBearer()

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Auth dependency - requires admin role"""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        db = get_db()
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Nu ai permisiuni de administrator")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Router
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ============ STATS ROUTES ============

@admin_router.get("/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    """Get platform statistics for admin dashboard"""
    db = get_db()
    
    # Total users
    total_users = await db.users.count_documents({})
    
    # Active subscriptions (active or trialing)
    active_subscriptions = await db.subscriptions.count_documents({
        "status": {"$in": ["active", "trialing"]}
    })
    
    # Trial users
    trial_users = await db.subscriptions.count_documents({"status": "trialing"})
    
    # Total articles
    total_articles = await db.articles.count_documents({})
    
    # Total sites
    total_sites = await db.wordpress_configs.count_documents({})
    
    # Monthly revenue estimation (based on active paid subscriptions)
    plan_prices = {"starter": 19, "pro": 49, "agency": 99, "enterprise": 199}
    monthly_revenue = 0
    
    paid_subs = await db.subscriptions.find(
        {"status": "active"},
        {"plan": 1, "_id": 0}
    ).to_list(1000)
    
    for sub in paid_subs:
        plan = sub.get("plan", "starter")
        monthly_revenue += plan_prices.get(plan, 0)
    
    # Active today (users with activity in last 24h - based on last login or article creation)
    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
    active_today = await db.articles.distinct("user_id", {
        "created_at": {"$gte": yesterday.isoformat()}
    })
    
    # Subscription breakdown by plan
    plan_breakdown = {}
    for plan in ["starter", "pro", "agency", "enterprise"]:
        count = await db.subscriptions.count_documents({"plan": plan, "status": {"$in": ["active", "trialing"]}})
        plan_breakdown[plan] = count
    
    return {
        "total_users": total_users,
        "active_subscriptions": active_subscriptions,
        "trial_users": trial_users,
        "total_articles": total_articles,
        "total_sites": total_sites,
        "monthly_revenue": monthly_revenue,
        "active_today": len(active_today),
        "plan_breakdown": plan_breakdown
    }


# ============ USER MANAGEMENT ============

@admin_router.get("/users")
async def get_all_users(
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    admin: dict = Depends(get_admin_user)
):
    """Get all users with their subscription info"""
    db = get_db()
    
    # Build query
    query = {}
    if search:
        query["$or"] = [
            {"email": {"$regex": search, "$options": "i"}},
            {"name": {"$regex": search, "$options": "i"}}
        ]
    
    # Get users with pagination
    skip = (page - 1) * per_page
    users = await db.users.find(query, {"_id": 0, "password": 0}).skip(skip).limit(per_page).to_list(per_page)
    
    # Enrich with subscription data
    enriched_users = []
    for user in users:
        sub = await db.subscriptions.find_one({"user_id": user["id"]}, {"_id": 0})
        articles_count = await db.articles.count_documents({"user_id": user["id"]})
        sites_count = await db.wordpress_configs.count_documents({"user_id": user["id"]})
        
        enriched_users.append({
            **user,
            "plan": sub.get("plan", "free") if sub else "free",
            "subscription_status": sub.get("status", "expired") if sub else "expired",
            "articles_count": articles_count,
            "sites_count": sites_count,
            "trial_ends_at": sub.get("trial_ends_at") if sub else None,
            "current_period_end": sub.get("current_period_end") if sub else None
        })
    
    total = await db.users.count_documents(query)
    
    return enriched_users


@admin_router.get("/users/{user_id}")
async def get_user_details(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get detailed info for a specific user"""
    db = get_db()
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get subscription
    sub = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    
    # Get recent articles
    articles = await db.articles.find(
        {"user_id": user_id},
        {"_id": 0, "content": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Get payments
    payments = await db.payment_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "user": user,
        "subscription": sub,
        "recent_articles": articles,
        "sites": sites,
        "recent_payments": payments
    }


# ============ ADMIN ACTIONS ============

class UpdateUserRole(BaseModel):
    role: str  # "admin" or "user"

@admin_router.patch("/users/{user_id}/role")
async def update_user_role(user_id: str, data: UpdateUserRole, admin: dict = Depends(get_admin_user)):
    """Update user role (admin/user)"""
    db = get_db()
    
    if data.role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
    
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": data.role, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    logging.info(f"[ADMIN] User {admin['email']} changed role of {user_id} to {data.role}")
    return {"message": f"Role updated to {data.role}"}


class UpdateSubscription(BaseModel):
    plan: Optional[str] = None
    status: Optional[str] = None

@admin_router.patch("/users/{user_id}/subscription")
async def update_user_subscription(user_id: str, data: UpdateSubscription, admin: dict = Depends(get_admin_user)):
    """Update user subscription (plan or status)"""
    db = get_db()
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.plan:
        if data.plan not in PLANS:
            raise HTTPException(status_code=400, detail=f"Invalid plan. Must be one of: {list(PLANS.keys())}")
        plan_info = PLANS[data.plan]
        update_data["plan"] = data.plan
        update_data["sites_limit"] = plan_info["sites_limit"]
        update_data["articles_limit"] = plan_info["articles_limit"]
    
    if data.status:
        if data.status not in ["active", "trialing", "canceled", "expired"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        update_data["status"] = data.status
    
    result = await db.subscriptions.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    logging.info(f"[ADMIN] User {admin['email']} updated subscription for {user_id}: {update_data}")
    return {"message": "Subscription updated", "changes": update_data}


@admin_router.delete("/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_admin_user)):
    """Delete a user and all their data"""
    db = get_db()
    
    # Check user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Don't allow deleting yourself
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Nu te poți șterge pe tine însuți")
    
    # Don't allow deleting other admins
    if user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Nu poți șterge un alt administrator")
    
    # Delete all user data
    await db.users.delete_one({"id": user_id})
    await db.subscriptions.delete_one({"user_id": user_id})
    await db.articles.delete_many({"user_id": user_id})
    await db.wordpress_configs.delete_many({"user_id": user_id})
    await db.keywords.delete_many({"user_id": user_id})
    await db.calendar.delete_many({"user_id": user_id})
    await db.settings.delete_one({"user_id": user_id})
    await db.user_api_keys.delete_one({"user_id": user_id})
    await db.payment_transactions.delete_many({"user_id": user_id})
    await db.invoices.delete_many({"user_id": user_id})
    
    logging.info(f"[ADMIN] User {admin['email']} deleted user {user_id} ({user.get('email')})")
    return {"message": "User deleted successfully"}


# ============ CONTENT MANAGEMENT ============

class PageContent(BaseModel):
    page_id: str  # "contact", "terms", "privacy"
    content: dict  # Flexible content structure

@admin_router.get("/content")
async def get_all_page_content(admin: dict = Depends(get_admin_user)):
    """Get all editable page content"""
    db = get_db()
    
    content = await db.page_content.find({}, {"_id": 0}).to_list(100)
    
    # Return default content if none exists
    if not content:
        defaults = {
            "contact": {
                "email": "support@seoautomation.ro",
                "phone": "+40 721 234 567",
                "address": "București, România",
                "hours": "Luni - Vineri, 9:00 - 18:00"
            },
            "terms": {
                "last_updated": "Martie 2026"
            },
            "privacy": {
                "last_updated": "Martie 2026"
            }
        }
        return [{"page_id": k, "content": v} for k, v in defaults.items()]
    
    return content


@admin_router.put("/content/{page_id}")
async def update_page_content(page_id: str, data: dict, admin: dict = Depends(get_admin_user)):
    """Update editable page content"""
    db = get_db()
    
    if page_id not in ["contact", "terms", "privacy"]:
        raise HTTPException(status_code=400, detail="Invalid page_id")
    
    await db.page_content.update_one(
        {"page_id": page_id},
        {
            "$set": {
                "page_id": page_id,
                "content": data,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": admin["id"]
            }
        },
        upsert=True
    )
    
    logging.info(f"[ADMIN] User {admin['email']} updated content for page '{page_id}'")
    return {"message": f"Content for {page_id} updated"}


# ============ INITIALIZE ADMIN ============

@admin_router.post("/init-admin")
async def initialize_first_admin(email: str, secret_key: str):
    """Initialize the first admin user (one-time setup)"""
    db = get_db()
    
    # Verify secret key (use JWT_SECRET as verification)
    if secret_key != JWT_SECRET:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    # Check if any admin exists
    existing_admin = await db.users.find_one({"role": "admin"})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    # Find user by email
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Register first.")
    
    # Make user admin
    await db.users.update_one(
        {"email": email},
        {"$set": {"role": "admin", "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logging.info(f"[ADMIN] Initialized first admin: {email}")
    return {"message": f"User {email} is now admin"}



# ============ PLATFORM SETTINGS ============

class PlatformSettingsUpdate(BaseModel):
    stripe_key: Optional[str] = None
    resend_key: Optional[str] = None


def encrypt_platform_key(key: str) -> str:
    """Simple encryption for platform keys"""
    import base64
    return base64.b64encode(key.encode()).decode()


def decrypt_platform_key(encrypted: str) -> str:
    """Decrypt platform key"""
    import base64
    try:
        return base64.b64decode(encrypted.encode()).decode()
    except:
        return encrypted


@admin_router.get("/platform-settings")
async def get_platform_settings(admin: dict = Depends(get_admin_user)):
    """Get platform settings status"""
    db = get_db()
    
    settings = await db.platform_settings.find_one({"id": "main"}, {"_id": 0})
    
    return {
        "has_stripe_key": bool(settings.get("stripe_key")) if settings else False,
        "has_resend_key": bool(settings.get("resend_key")) if settings else False
    }


@admin_router.put("/platform-settings")
async def update_platform_settings(data: PlatformSettingsUpdate, admin: dict = Depends(get_admin_user)):
    """Update platform API keys"""
    db = get_db()
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.stripe_key:
        if not data.stripe_key.startswith("sk_"):
            raise HTTPException(status_code=400, detail="Cheia Stripe trebuie să înceapă cu 'sk_'")
        update_data["stripe_key"] = encrypt_platform_key(data.stripe_key)
    
    if data.resend_key:
        if not data.resend_key.startswith("re_"):
            raise HTTPException(status_code=400, detail="Cheia Resend trebuie să înceapă cu 're_'")
        update_data["resend_key"] = encrypt_platform_key(data.resend_key)
    
    await db.platform_settings.update_one(
        {"id": "main"},
        {"$set": {**update_data, "id": "main"}},
        upsert=True
    )
    
    logging.info(f"[ADMIN] Platform settings updated by {admin['email']}")
    return {"message": "Cheile au fost salvate"}


async def get_platform_key(key_name: str) -> Optional[str]:
    """Get decrypted platform key for use in services"""
    db = get_db()
    settings = await db.platform_settings.find_one({"id": "main"}, {"_id": 0})
    
    if not settings or not settings.get(key_name):
        return None
    
    return decrypt_platform_key(settings[key_name])



# ============ CHANGE PASSWORD ============

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@admin_router.put("/change-password")
async def change_admin_password(data: ChangePasswordRequest, admin: dict = Depends(get_admin_user)):
    """Change admin password"""
    import bcrypt
    db = get_db()
    
    # Get user with password
    user = await db.users.find_one({"id": admin["id"]})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    
    # Verify current password
    if not bcrypt.checkpw(data.current_password.encode('utf-8'), user["password"].encode('utf-8')):
        raise HTTPException(status_code=400, detail="Parola curentă este incorectă")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola nouă trebuie să aibă minim 6 caractere")
    
    # Hash and save new password
    new_hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    await db.users.update_one(
        {"id": admin["id"]},
        {"$set": {"password": new_hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logging.info(f"[ADMIN] Password changed for {admin['email']}")
    return {"message": "Parola a fost schimbată cu succes"}


# ============ ADMIN RESET USER PASSWORD ============

class ResetUserPasswordRequest(BaseModel):
    new_password: str


@admin_router.post("/users/{user_id}/reset-password")
async def admin_reset_user_password(user_id: str, data: ResetUserPasswordRequest, admin: dict = Depends(get_admin_user)):
    """Admin resets a user's password manually"""
    import bcrypt
    import asyncio
    db = get_db()
    
    # Find user
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    
    # Don't allow resetting another admin's password (optional protection)
    if user.get("role") == "admin" and user["id"] != admin["id"]:
        raise HTTPException(status_code=403, detail="Nu poți reseta parola unui alt administrator")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă minim 6 caractere")
    
    # Hash and save new password
    new_hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": new_hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logging.info(f"[ADMIN] Admin {admin['email']} reset password for user {user.get('email')}")
    
    # Send email notification to user (async, non-blocking)
    from .email_service import email_service
    asyncio.create_task(email_service.send_password_reset_by_admin(
        user.get('email'),
        user.get('name', 'Utilizator'),
        data.new_password
    ))
    
    return {"message": f"Parola pentru {user.get('email')} a fost resetată cu succes"}


# ============ EXTENDED STATISTICS ============

@admin_router.get("/stats/extended")
async def get_extended_stats(admin: dict = Depends(get_admin_user)):
    """Get extended platform statistics for admin dashboard"""
    db = get_db()
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # User registrations
    new_today = await db.users.count_documents({"created_at": {"$gte": today.isoformat()}})
    new_this_week = await db.users.count_documents({"created_at": {"$gte": week_ago.isoformat()}})
    new_this_month = await db.users.count_documents({"created_at": {"$gte": month_ago.isoformat()}})
    
    # User growth chart (last 30 days)
    user_growth = []
    for i in range(30):
        day = today - timedelta(days=i)
        day_end = day + timedelta(days=1)
        count = await db.users.count_documents({
            "created_at": {"$gte": day.isoformat(), "$lt": day_end.isoformat()}
        })
        user_growth.append({"date": day.strftime("%Y-%m-%d"), "registrations": count})
    user_growth.reverse()
    
    # Total articles this month
    articles_this_month = await db.articles.count_documents({
        "created_at": {"$gte": month_ago.isoformat()}
    })
    
    # Total backlink emails sent
    total_outreach_sent = await db.backlink_outreach.count_documents({"status": "sent"})
    total_outreach_responded = await db.backlink_outreach.count_documents({"status": "responded"})
    
    # Top 10 most active users
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users_by_articles = await db.articles.aggregate(pipeline).to_list(10)
    
    # Enrich with user names
    top_users = []
    for item in top_users_by_articles:
        user = await db.users.find_one({"id": item["_id"]}, {"_id": 0, "email": 1, "name": 1})
        if user:
            top_users.append({
                "user_id": item["_id"],
                "email": user.get("email", "Unknown"),
                "name": user.get("name", ""),
                "articles_count": item["count"]
            })
    
    # Usage by plan
    usage_by_plan = {}
    for plan in ["starter", "pro", "agency", "enterprise"]:
        subs = await db.subscriptions.find({"plan": plan, "status": {"$in": ["active", "trialing"]}}).to_list(1000)
        user_ids = [s["user_id"] for s in subs]
        articles = await db.articles.count_documents({"user_id": {"$in": user_ids}}) if user_ids else 0
        sites = await db.wordpress_configs.count_documents({"user_id": {"$in": user_ids}}) if user_ids else 0
        usage_by_plan[plan] = {
            "users": len(subs),
            "articles": articles,
            "sites": sites
        }
    
    # Revenue stats
    plan_prices = {"starter": 19, "pro": 49, "agency": 99, "enterprise": 199}
    annual_discount = 0.8  # 20% discount
    
    mrr = 0
    arr = 0
    
    paid_subs = await db.subscriptions.find(
        {"status": "active"},
        {"plan": 1, "billing_interval": 1, "_id": 0}
    ).to_list(1000)
    
    for sub in paid_subs:
        plan = sub.get("plan", "starter")
        price = plan_prices.get(plan, 0)
        is_annual = sub.get("billing_interval") == "year"
        
        if is_annual:
            monthly_equivalent = (price * 12 * annual_discount) / 12
            mrr += monthly_equivalent
        else:
            mrr += price
    
    arr = mrr * 12
    
    # Trial conversion rate
    total_trials_started = await db.subscriptions.count_documents({"trial_ends_at": {"$exists": True}})
    converted_trials = await db.subscriptions.count_documents({
        "trial_ends_at": {"$exists": True},
        "status": "active"
    })
    trial_conversion_rate = round((converted_trials / total_trials_started * 100), 1) if total_trials_started > 0 else 0
    
    # Churn (cancelled in last 30 days)
    churned = await db.subscriptions.count_documents({
        "status": "canceled",
        "updated_at": {"$gte": month_ago.isoformat()}
    })
    active_start_of_month = await db.subscriptions.count_documents({
        "status": {"$in": ["active", "canceled"]},
        "created_at": {"$lt": month_ago.isoformat()}
    })
    churn_rate = round((churned / active_start_of_month * 100), 1) if active_start_of_month > 0 else 0
    
    return {
        "registrations": {
            "today": new_today,
            "this_week": new_this_week,
            "this_month": new_this_month
        },
        "user_growth_chart": user_growth,
        "articles_this_month": articles_this_month,
        "backlinks": {
            "total_sent": total_outreach_sent,
            "total_responded": total_outreach_responded,
            "response_rate": round((total_outreach_responded / total_outreach_sent * 100), 1) if total_outreach_sent > 0 else 0
        },
        "top_users": top_users,
        "usage_by_plan": usage_by_plan,
        "revenue": {
            "mrr": round(mrr, 2),
            "arr": round(arr, 2),
            "trial_conversion_rate": trial_conversion_rate,
            "churn_rate": churn_rate
        }
    }


@admin_router.get("/users/{user_id}/full")
async def get_user_full_details(user_id: str, admin: dict = Depends(get_admin_user)):
    """Get complete details for a specific user including API keys status, GSC, etc."""
    db = get_db()
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Subscription
    sub = await db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
    
    # Sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # GSC connections
    gsc_connections = await db.gsc_connections.find(
        {"user_id": user_id},
        {"_id": 0, "access_token": 0, "refresh_token": 0}
    ).to_list(100)
    
    # API Keys status (don't expose actual keys)
    api_keys_doc = await db.user_api_keys.find_one({"user_id": user_id}, {"_id": 0})
    api_keys_status = {
        "openai": bool(api_keys_doc.get("openai_key")) if api_keys_doc else False,
        "gemini": bool(api_keys_doc.get("gemini_key")) if api_keys_doc else False,
        "resend": bool(api_keys_doc.get("resend_key")) if api_keys_doc else False,
        "sendgrid": bool(api_keys_doc.get("sendgrid_key")) if api_keys_doc else False,
        "pexels": bool(api_keys_doc.get("pexels_key")) if api_keys_doc else False,
        "facebook": bool(api_keys_doc.get("facebook_app_id")) if api_keys_doc else False,
        "linkedin": bool(api_keys_doc.get("linkedin_client_id")) if api_keys_doc else False
    }
    
    # Articles stats
    total_articles = await db.articles.count_documents({"user_id": user_id})
    month_ago = datetime.now(timezone.utc) - timedelta(days=30)
    articles_this_month = await db.articles.count_documents({
        "user_id": user_id,
        "created_at": {"$gte": month_ago.isoformat()}
    })
    published_articles = await db.articles.count_documents({"user_id": user_id, "status": "published"})
    
    # Backlink stats
    outreach_sent = await db.backlink_outreach.count_documents({"user_id": user_id, "status": "sent"})
    outreach_responded = await db.backlink_outreach.count_documents({"user_id": user_id, "status": "responded"})
    
    # Last activity - use find().sort().limit() instead of find_one().sort()
    last_article_cursor = db.articles.find(
        {"user_id": user_id},
        {"_id": 0, "created_at": 1}
    ).sort("created_at", -1).limit(1)
    last_article_list = await last_article_cursor.to_list(1)
    last_article = last_article_list[0] if last_article_list else None
    
    last_login = user.get("last_login")
    last_activity = last_article.get("created_at") if last_article else last_login
    
    # Recent articles
    recent_articles = await db.articles.find(
        {"user_id": user_id},
        {"_id": 0, "content": 0}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Payments
    payments = await db.payment_transactions.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Invoices
    invoices = await db.invoices.find(
        {"user_id": user_id},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "user": user,
        "subscription": sub,
        "sites": sites,
        "gsc_connections": gsc_connections,
        "api_keys_status": api_keys_status,
        "stats": {
            "total_articles": total_articles,
            "articles_this_month": articles_this_month,
            "published_articles": published_articles,
            "outreach_sent": outreach_sent,
            "outreach_responded": outreach_responded
        },
        "last_activity": last_activity,
        "recent_articles": recent_articles,
        "payments": payments,
        "invoices": invoices
    }


@admin_router.get("/system/health")
async def get_system_health(admin: dict = Depends(get_admin_user)):
    """Get system health status"""
    db = get_db()
    
    today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Users with missing API keys (have sites but no LLM key)
    users_with_sites = await db.wordpress_configs.distinct("user_id")
    users_missing_keys = []
    
    for uid in users_with_sites[:100]:  # Limit to 100
        api_keys = await db.user_api_keys.find_one({"user_id": uid})
        has_llm = api_keys and (api_keys.get("openai_key") or api_keys.get("gemini_key"))
        if not has_llm:
            user = await db.users.find_one({"id": uid}, {"_id": 0, "email": 1, "name": 1})
            if user:
                users_missing_keys.append({
                    "user_id": uid,
                    "email": user.get("email"),
                    "name": user.get("name")
                })
    
    # Failed jobs today (check notifications)
    failed_jobs = await db.notifications.count_documents({
        "type": "error",
        "created_at": {"$gte": today.isoformat()}
    })
    
    # Expired trials not converted
    expired_trials = await db.subscriptions.count_documents({
        "status": "expired",
        "trial_ends_at": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
    
    # Sites without niche configured
    sites_no_niche = await db.wordpress_configs.count_documents({
        "$or": [{"niche": {"$exists": False}}, {"niche": ""}, {"niche": None}]
    })
    
    return {
        "users_missing_api_keys": users_missing_keys[:20],
        "users_missing_api_keys_count": len(users_missing_keys),
        "failed_jobs_today": failed_jobs,
        "expired_trials_not_converted": expired_trials,
        "sites_without_niche": sites_no_niche
    }

