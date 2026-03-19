"""
Subscription Service - handles subscription logic, limits, and billing
"""
import os
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from cryptography.fernet import Fernet
import base64
import hashlib

from .plans import PLANS, TRIAL_CONFIG, get_plan

# Generate a consistent encryption key from a secret
def get_encryption_key() -> bytes:
    secret = os.environ.get('JWT_SECRET', 'default-secret-key')
    key = hashlib.sha256(secret.encode()).digest()
    return base64.urlsafe_b64encode(key)

fernet = Fernet(get_encryption_key())

def encrypt_api_key(key: str) -> str:
    """Encrypt an API key for storage"""
    if not key:
        return ""
    return fernet.encrypt(key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    if not encrypted_key:
        return ""
    try:
        return fernet.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return ""

class SubscriptionService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def create_trial_subscription(self, user_id: str) -> Dict[str, Any]:
        """Create a trial subscription for a new user"""
        trial_end = datetime.now(timezone.utc) + timedelta(days=TRIAL_CONFIG["duration_days"])
        
        subscription = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "plan": "free",
            "status": "trialing",
            "stripe_customer_id": None,
            "stripe_subscription_id": None,
            "trial_ends_at": trial_end.isoformat(),
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": trial_end.isoformat(),
            "sites_limit": TRIAL_CONFIG["sites_limit"],
            "articles_limit": TRIAL_CONFIG["articles_limit"],
            "articles_used_this_month": 0,
            "sites_used": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": None
        }
        
        await self.db.subscriptions.insert_one(subscription)
        logging.info(f"[SUBSCRIPTION] Created trial for user {user_id}, ends {trial_end}")
        return subscription
    
    async def get_subscription(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user's subscription"""
        sub = await self.db.subscriptions.find_one({"user_id": user_id}, {"_id": 0})
        if sub:
            # Check if trial expired
            if sub.get("status") == "trialing" and sub.get("trial_ends_at"):
                trial_end = datetime.fromisoformat(sub["trial_ends_at"].replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > trial_end:
                    await self.db.subscriptions.update_one(
                        {"user_id": user_id},
                        {"$set": {"status": "expired", "updated_at": datetime.now(timezone.utc).isoformat()}}
                    )
                    sub["status"] = "expired"
        return sub
    
    async def get_or_create_subscription(self, user_id: str) -> Dict[str, Any]:
        """Get existing subscription or create trial"""
        sub = await self.get_subscription(user_id)
        if not sub:
            sub = await self.create_trial_subscription(user_id)
        return sub
    
    async def upgrade_subscription(self, user_id: str, plan: str, stripe_customer_id: str = None, 
                                   stripe_subscription_id: str = None) -> Dict[str, Any]:
        """Upgrade user's subscription to a paid plan"""
        plan_config = get_plan(plan)
        
        period_end = datetime.now(timezone.utc) + timedelta(days=30)
        
        update_data = {
            "plan": plan,
            "status": "active",
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_subscription_id,
            "trial_ends_at": None,
            "current_period_start": datetime.now(timezone.utc).isoformat(),
            "current_period_end": period_end.isoformat(),
            "sites_limit": plan_config["sites_limit"],
            "articles_limit": plan_config["articles_limit"],
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await self.db.subscriptions.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
        
        logging.info(f"[SUBSCRIPTION] Upgraded user {user_id} to {plan}")
        return await self.get_subscription(user_id)
    
    async def cancel_subscription(self, user_id: str) -> Dict[str, Any]:
        """Cancel subscription (will remain active until period end)"""
        await self.db.subscriptions.update_one(
            {"user_id": user_id},
            {"$set": {
                "status": "canceled",
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        logging.info(f"[SUBSCRIPTION] Canceled subscription for user {user_id}")
        return await self.get_subscription(user_id)
    
    async def check_site_limit(self, user_id: str) -> bool:
        """Check if user can add another site"""
        sub = await self.get_or_create_subscription(user_id)
        if sub["status"] not in ["active", "trialing"]:
            return False
        if sub["sites_limit"] == -1:  # Unlimited
            return True
        
        sites_count = await self.db.wordpress_configs.count_documents({"user_id": user_id})
        return sites_count < sub["sites_limit"]
    
    async def check_article_limit(self, user_id: str) -> bool:
        """Check if user can generate another article this month"""
        sub = await self.get_or_create_subscription(user_id)
        if sub["status"] not in ["active", "trialing"]:
            return False
        if sub["articles_limit"] == -1:  # Unlimited
            return True
        
        return sub.get("articles_used_this_month", 0) < sub["articles_limit"]
    
    async def increment_article_usage(self, user_id: str) -> None:
        """Increment article usage counter"""
        await self.db.subscriptions.update_one(
            {"user_id": user_id},
            {"$inc": {"articles_used_this_month": 1}}
        )
    
    async def reset_monthly_usage(self) -> None:
        """Reset all users' monthly article usage (called on 1st of month)"""
        await self.db.subscriptions.update_many(
            {},
            {"$set": {"articles_used_this_month": 0}}
        )
        logging.info("[SUBSCRIPTION] Reset monthly article usage for all users")
    
    async def get_usage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get usage statistics for a user"""
        sub = await self.get_or_create_subscription(user_id)
        plan_config = get_plan(sub["plan"])
        
        sites_count = await self.db.wordpress_configs.count_documents({"user_id": user_id})
        
        # Calculate days remaining for trial
        days_remaining = None
        if sub["status"] == "trialing" and sub.get("trial_ends_at"):
            trial_end = datetime.fromisoformat(sub["trial_ends_at"].replace("Z", "+00:00"))
            delta = trial_end - datetime.now(timezone.utc)
            days_remaining = max(0, delta.days)
        
        return {
            "plan": sub["plan"],
            "plan_name": plan_config["name"],
            "status": sub["status"],
            "sites_limit": sub["sites_limit"],
            "sites_used": sites_count,
            "articles_limit": sub["articles_limit"],
            "articles_used": sub.get("articles_used_this_month", 0),
            "trial_ends_at": sub.get("trial_ends_at"),
            "days_remaining": days_remaining,
            "can_add_site": await self.check_site_limit(user_id),
            "can_generate_article": await self.check_article_limit(user_id)
        }


class ApiKeyService:
    """Service for managing user's own API keys (BYOAK)"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
    
    async def get_user_keys(self, user_id: str) -> Dict[str, Any]:
        """Get user's API keys (masked)"""
        keys = await self.db.user_api_keys.find_one({"user_id": user_id}, {"_id": 0})
        if not keys:
            return {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "has_openai_key": False,
                "has_gemini_key": False,
                "has_resend_key": False,
                "has_pexels_key": False,
                "updated_at": None
            }
        
        return {
            "id": keys.get("id", str(uuid.uuid4())),
            "user_id": user_id,
            "has_openai_key": bool(keys.get("openai_key")),
            "has_gemini_key": bool(keys.get("gemini_key")),
            "has_resend_key": bool(keys.get("resend_key")),
            "has_pexels_key": bool(keys.get("pexels_key")),
            "updated_at": keys.get("updated_at")
        }
    
    async def update_keys(self, user_id: str, openai_key: str = None, gemini_key: str = None,
                          resend_key: str = None, pexels_key: str = None) -> Dict[str, Any]:
        """Update user's API keys"""
        existing = await self.db.user_api_keys.find_one({"user_id": user_id})
        
        update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
        
        if openai_key is not None:
            update_data["openai_key"] = encrypt_api_key(openai_key) if openai_key else ""
        if gemini_key is not None:
            update_data["gemini_key"] = encrypt_api_key(gemini_key) if gemini_key else ""
        if resend_key is not None:
            update_data["resend_key"] = encrypt_api_key(resend_key) if resend_key else ""
        if pexels_key is not None:
            update_data["pexels_key"] = encrypt_api_key(pexels_key) if pexels_key else ""
        
        if existing:
            await self.db.user_api_keys.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
        else:
            update_data["id"] = str(uuid.uuid4())
            update_data["user_id"] = user_id
            await self.db.user_api_keys.insert_one(update_data)
        
        logging.info(f"[BYOAK] Updated API keys for user {user_id}")
        return await self.get_user_keys(user_id)
    
    async def get_decrypted_key(self, user_id: str, key_type: str) -> Optional[str]:
        """Get a specific decrypted API key for a user"""
        keys = await self.db.user_api_keys.find_one({"user_id": user_id}, {"_id": 0})
        if not keys:
            return None
        
        key_map = {
            "openai": "openai_key",
            "gemini": "gemini_key",
            "resend": "resend_key",
            "pexels": "pexels_key"
        }
        
        field = key_map.get(key_type)
        if not field or not keys.get(field):
            return None
        
        return decrypt_api_key(keys[field])
    
    async def validate_key(self, key_type: str, key: str) -> bool:
        """Validate an API key by making a test request"""
        # Basic validation - check key format
        if not key or len(key) < 10:
            return False
        
        if key_type == "openai" and not key.startswith("sk-"):
            return False
        
        if key_type == "resend" and not key.startswith("re_"):
            return False
        
        # TODO: Add actual API validation calls
        return True
