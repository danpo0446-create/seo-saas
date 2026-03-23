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
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    resend_key: Optional[str] = None
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None


def encrypt_platform_key(key: str) -> str:
    """Simple encryption for platform keys"""
    import base64
    return base64.b64encode(key.encode()).decode()


def decrypt_platform_key(encrypted: str) -> str:
    """Decrypt platform key"""
    import base64
    try:
        return base64.b64decode(encrypted.encode()).decode()
    except Exception:
        return encrypted


@admin_router.get("/platform-settings")
async def get_platform_settings(admin: dict = Depends(get_admin_user)):
    """Get platform settings status"""
    db = get_db()
    
    settings = await db.platform_settings.find_one({"id": "main"}, {"_id": 0})
    
    return {
        "has_stripe_secret_key": bool(settings.get("stripe_secret_key") or settings.get("stripe_key")) if settings else False,
        "has_stripe_publishable_key": bool(settings.get("stripe_publishable_key")) if settings else False,
        "has_resend_key": bool(settings.get("resend_key")) if settings else False,
        "has_google_client_id": bool(settings.get("google_client_id")) if settings else False,
        "has_google_client_secret": bool(settings.get("google_client_secret")) if settings else False
    }


@admin_router.put("/platform-settings")
async def update_platform_settings(data: PlatformSettingsUpdate, admin: dict = Depends(get_admin_user)):
    """Update platform API keys"""
    db = get_db()
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if data.stripe_secret_key:
        if not (data.stripe_secret_key.startswith("sk_") or data.stripe_secret_key.startswith("rk_")):
            raise HTTPException(status_code=400, detail="Secret Key Stripe trebuie să înceapă cu 'sk_' sau 'rk_'")
        update_data["stripe_secret_key"] = encrypt_platform_key(data.stripe_secret_key)
    
    if data.stripe_publishable_key:
        if not data.stripe_publishable_key.startswith("pk_"):
            raise HTTPException(status_code=400, detail="Publishable Key Stripe trebuie să înceapă cu 'pk_'")
        update_data["stripe_publishable_key"] = encrypt_platform_key(data.stripe_publishable_key)
    
    if data.resend_key:
        if not data.resend_key.startswith("re_"):
            raise HTTPException(status_code=400, detail="Cheia Resend trebuie să înceapă cu 're_'")
        update_data["resend_key"] = encrypt_platform_key(data.resend_key)
    
    if data.google_client_id:
        update_data["google_client_id"] = encrypt_platform_key(data.google_client_id)
    
    if data.google_client_secret:
        update_data["google_client_secret"] = encrypt_platform_key(data.google_client_secret)
    
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


class ResetUserPasswordRequest(BaseModel):
    new_password: str


@admin_router.post("/users/{user_id}/reset-password")
async def reset_user_password(user_id: str, data: ResetUserPasswordRequest, admin: dict = Depends(get_admin_user)):
    """Admin can manually reset a user's password"""
    import bcrypt
    db = get_db()
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola trebuie să aibă minim 6 caractere")
    
    # Check user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    
    # Don't allow resetting other admin passwords
    if user.get("role") == "admin" and user_id != admin["id"]:
        raise HTTPException(status_code=403, detail="Nu poți reseta parola altui administrator")
    
    # Hash and save new password
    new_hashed = bcrypt.hashpw(data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"password": new_hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Create audit notification
    await db.admin_notifications.insert_one({
        "id": str(uuid.uuid4()),
        "type": "password_reset",
        "title": "Parolă resetată",
        "message": f"Parola utilizatorului {user.get('email')} a fost resetată manual",
        "admin_id": admin["id"],
        "admin_email": admin["email"],
        "target_user_id": user_id,
        "target_user_email": user.get("email"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "read": False
    })
    
    logging.info(f"[ADMIN] Password reset for user {user_id} ({user.get('email')}) by {admin['email']}")
    return {"message": f"Parola pentru {user.get('email')} a fost resetată cu succes"}


# ============ NOTIFICATIONS ============

@admin_router.get("/notifications")
async def get_admin_notifications(
    limit: int = 50,
    unread_only: bool = False,
    admin: dict = Depends(get_admin_user)
):
    """Get admin notifications for audit trail"""
    db = get_db()
    
    query = {}
    if unread_only:
        query["read"] = False
    
    notifications = await db.admin_notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    unread_count = await db.admin_notifications.count_documents({"read": False})
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@admin_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, admin: dict = Depends(get_admin_user)):
    """Mark a notification as read"""
    db = get_db()
    
    await db.admin_notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Notificare marcată ca citită"}


@admin_router.post("/notifications/read-all")
async def mark_all_notifications_read(admin: dict = Depends(get_admin_user)):
    """Mark all notifications as read"""
    db = get_db()
    
    await db.admin_notifications.update_many(
        {"read": False},
        {"$set": {"read": True, "read_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Toate notificările au fost marcate ca citite"}


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
