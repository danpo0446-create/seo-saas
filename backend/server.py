from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from emergentintegrations.llm.chat import LlmChat, UserMessage
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json
import resend
import httpx
import re
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
from dataclasses import dataclass
import markdown as md_converter

# Import refactored modules
from config import (
    MONGO_URL, DB_NAME, SECRET_KEY, RESEND_API_KEY, PEXELS_API_KEY,
    EMERGENT_LLM_KEY, SENDER_EMAIL, ROMANIA_TZ, NICHE_CATEGORIES,
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI,
    get_current_year, get_now_utc, get_now_romania
)
from models import (
    UserCreate, UserLogin, UserResponse,
    ArticleCreate, ArticleUpdate, ArticleResponse,
    KeywordResearch, KeywordResponse,
    CalendarEntry, CalendarResponse,
    BacklinkSite,
    WordPressConfig, WordPressConfigUpdate, WordPressConfigResponse,
    AutomationConfig, AutomationConfigResponse,
    SiteAutomationSettings, SiteAutomationSettingsResponse,
    Web2Site, Web2Link, Web2LinkResponse
)
from services.social_posting import (
    post_to_facebook_page, post_to_linkedin_company, auto_post_article_to_social,
    get_facebook_page_id, get_facebook_page_name, FACEBOOK_PAGES
)
from woocommerce_service import get_woocommerce_service, get_products_for_article, WooCommerceService
from google_trends_service import get_trending_topics_for_niche, score_keywords_by_trend, GoogleTrendsService

# Import SaaS modules
from saas.routes import saas_router
from saas.admin_routes import admin_router
from saas.subscription_service import SubscriptionService, ApiKeyService
from saas.plans import get_plan, PLANS

# Helper function to get user's API key (BYOAK first, then platform fallback for admin/test)
async def get_user_llm_key(user_id: str, is_admin: bool = False, user_email: str = ""):
    """Get LLM API key - prioritizes user's BYOAK keys. Platform fallback only for admin/test."""
    from saas.subscription_service import decrypt_api_key
    
    user_keys = await db.user_api_keys.find_one({"user_id": user_id})
    
    if user_keys:
        if user_keys.get("openai_key"):
            decrypted_key = decrypt_api_key(user_keys["openai_key"])
            if decrypted_key and decrypted_key.startswith("sk-"):
                return decrypted_key, "openai", "gpt-4o"
        if user_keys.get("gemini_key"):
            decrypted_key = decrypt_api_key(user_keys["gemini_key"])
            if decrypted_key:
                return decrypted_key, "gemini", "gemini-2.0-flash"
    
    # Fallback to platform key ONLY for admin or test users
    is_test_user = "test" in user_email.lower() if user_email else False
    if is_admin or is_test_user:
        platform_key = os.environ.get('EMERGENT_LLM_KEY')
        if platform_key:
            return platform_key, "openai", "gpt-4o"
    
    return None, None, None

# Helper function to get user's email API key (Resend or SendGrid)
async def get_user_email_key(user_id: str, is_admin: bool = False, user_email: str = ""):
    """Get email API key - prioritizes user's BYOAK keys. Platform fallback only for admin/test."""
    from saas.subscription_service import decrypt_api_key
    
    user_keys = await db.user_api_keys.find_one({"user_id": user_id})
    
    if user_keys:
        if user_keys.get("resend_key"):
            decrypted_key = decrypt_api_key(user_keys["resend_key"])
            if decrypted_key and decrypted_key.startswith("re_"):
                return decrypted_key, "resend"
        if user_keys.get("sendgrid_key"):
            decrypted_key = decrypt_api_key(user_keys["sendgrid_key"])
            if decrypted_key:
                return decrypted_key, "sendgrid"
    
    # Fallback to platform key ONLY for admin or test users
    is_test_user = "test" in user_email.lower() if user_email else False
    if is_admin or is_test_user:
        if RESEND_API_KEY:
            return RESEND_API_KEY, "resend"
    
    return None, None


# Helper function to get user's Pexels API key
async def get_user_pexels_key(user_id: str, is_admin: bool = False, user_email: str = ""):
    """Get Pexels API key - prioritizes user's BYOAK key."""
    from saas.subscription_service import decrypt_api_key
    
    user_keys = await db.user_api_keys.find_one({"user_id": user_id})
    
    if user_keys and user_keys.get("pexels_key"):
        decrypted_key = decrypt_api_key(user_keys["pexels_key"])
        if decrypted_key:
            return decrypted_key
    
    # Fallback for admin/test
    is_test_user = "test" in user_email.lower() if user_email else False
    if is_admin or is_test_user:
        return PEXELS_API_KEY
    
    return None


# Compatibility layer for old chat() function
@dataclass
class Message:
    role: str
    content: str

async def chat(api_key: str, messages: list, model: str = "gpt-4o", session_id: str = None):
    """Compatibility function for old chat API"""
    llm_chat = LlmChat(
        api_key=api_key,
        system_message="You are a helpful AI assistant."
    )
    # Determine provider based on model
    if "gpt" in model.lower():
        llm_chat = llm_chat.with_model("openai", model)
    elif "gemini" in model.lower():
        llm_chat = llm_chat.with_model("gemini", model)
    else:
        llm_chat = llm_chat.with_model("openai", model)
    
    # Convert messages to UserMessage format and send
    for msg in messages:
        if hasattr(msg, 'content'):
            response = await llm_chat.send_message(UserMessage(text=msg.content))
            return response.text if hasattr(response, 'text') else str(response)
    return ""

# Timezone for Romania
ROMANIA_TZ = pytz.timezone('Europe/Bucharest')

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'seo-automation-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Google OAuth Config
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', '')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', '')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Email Config (Resend)
RESEND_API_KEY = os.environ.get('RESEND_API_KEY', '')
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
if RESEND_API_KEY:
    resend.api_key = RESEND_API_KEY

# Image API Config - Pexels (free, unlimited)
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY', 'Jqp2tzXMnPVp7WVV07Jw4ugiliAFQLRN3tmcSoDKOrfDtlY2WAbs7kDT')

# GSC Cache
gsc_cache = {}
GSC_CACHE_TTL = 300  # 5 minutes

# General API Cache for frequently accessed data
api_cache = {}
API_CACHE_TTL = 60  # 1 minute for general data

# Topics Log Helper Functions
async def log_topic_used(site_id: str, topic: str, score: int = 0):
    """Log a topic as used for cooldown tracking"""
    await db.topics_log.insert_one({
        "site_id": site_id,
        "topic": topic.lower(),
        "used_at": datetime.now(timezone.utc).isoformat(),
        "score": score
    })
    logging.info(f"[TOPICS_LOG] Logged topic '{topic}' for site {site_id}")

async def get_topics_in_cooldown(site_id: str, days: int = 30) -> List[str]:
    """Get topics used in the last N days for a site"""
    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    topics = await db.topics_log.find({
        "site_id": site_id,
        "used_at": {"$gte": cutoff_date}
    }, {"_id": 0, "topic": 1}).to_list(1000)
    return [t["topic"] for t in topics]

async def is_topic_similar(topic: str, existing_topics: List[str], threshold: float = 0.6) -> bool:
    """Check if a topic is semantically similar to existing topics (simple word overlap)"""
    topic_words = set(topic.lower().split())
    for existing in existing_topics:
        existing_words = set(existing.lower().split())
        if len(topic_words) == 0 or len(existing_words) == 0:
            continue
        # Jaccard similarity
        intersection = len(topic_words & existing_words)
        union = len(topic_words | existing_words)
        similarity = intersection / union if union > 0 else 0
        if similarity >= threshold:
            return True
    return False

async def send_job_failure_alert(job_name: str, error_message: str, site_name: str = ""):
    """Send alert email when a scheduled job fails"""
    if not RESEND_API_KEY:
        logging.warning(f"[ALERT] Cannot send job failure alert - no Resend API key")
        return
    
    try:
        # Get all admin users (users with sites configured)
        admin_emails = await db.users.distinct("email")
        if not admin_emails:
            return
        
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #ef4444; color: white; padding: 20px; text-align: center;">
                <h1>⚠️ Job Failure Alert</h1>
            </div>
            <div style="padding: 20px; background: #f9fafb;">
                <h2 style="color: #1f2937;">Job: {job_name}</h2>
                {f'<p><strong>Site:</strong> {site_name}</p>' if site_name else ''}
                <p><strong>Error:</strong></p>
                <pre style="background: #1f2937; color: #f87171; padding: 15px; border-radius: 8px; overflow-x: auto;">{error_message}</pre>
                <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
                <p style="color: #6b7280; font-size: 12px;">This is an automated alert from SEO Automation Platform.</p>
            </div>
        </div>
        """
        
        resend.Emails.send({
            "from": f"SEO Automation <{SENDER_EMAIL}>",
            "to": admin_emails[:5],  # Max 5 recipients
            "subject": f"🚨 Job Failed: {job_name}",
            "html": email_html
        })
        logging.info(f"[ALERT] Sent job failure alert for {job_name} to {len(admin_emails)} recipients")
    except Exception as e:
        logging.error(f"[ALERT] Failed to send job failure alert: {e}")

# Scheduler for automated tasks - using Romania timezone
scheduler = AsyncIOScheduler(timezone=ROMANIA_TZ)

# Create the main app
app = FastAPI(title="SEO Automation Platform")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    created_at: str
    role: Optional[str] = "user"

class ArticleCreate(BaseModel):
    title: str
    keywords: List[str]
    niche: str
    tone: str = "professional"
    length: str = "medium"
    site_id: Optional[str] = None

class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None

class ArticleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    content: str
    keywords: List[str]
    niche: str
    status: str
    created_at: str
    user_id: str
    seo_score: int
    word_count: int
    site_id: Optional[str] = None

class KeywordResearch(BaseModel):
    niche: str
    seed_keywords: Optional[List[str]] = []
    site_id: Optional[str] = None

class KeywordResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    keyword: str
    volume: int
    difficulty: int
    cpc: float
    trend: str
    site_id: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None

class CalendarEntry(BaseModel):
    title: str
    keywords: List[str]
    scheduled_date: str
    status: str = "planned"
    site_id: Optional[str] = None

class CalendarResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    keywords: List[str]
    scheduled_date: str
    status: str
    article_id: Optional[str] = None
    user_id: str
    site_id: Optional[str] = None

class BacklinkSite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    domain: str
    da: int
    pa: int
    category: str
    status: str
    price: float

class WordPressConfig(BaseModel):
    site_url: str
    site_name: str = ""
    username: str
    app_password: str
    niche: str = ""
    notification_email: str = ""
    article_language: str = "ro"  # ro = română, en = engleză
    tone: str = ""  # Tonul articolelor: "cald, empatic", "profesional", etc.

class WordPressConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    site_url: str
    site_name: str
    username: str
    connected: bool
    user_id: str
    niche: str = ""
    notification_email: str = ""
    facebook_connected: bool = False
    linkedin_connected: bool = False
    auto_keywords: List[str] = []
    article_language: str = "ro"
    tone: str = ""  # Tonul articolelor

class AutomationConfig(BaseModel):
    enabled: bool = False
    generation_hour: int = 8
    article_length: str = "medium"
    categories: List[str] = []

class AutomationConfigResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    enabled: bool
    generation_hour: int
    article_length: str
    categories: List[str]
    last_generation: Optional[str] = None
    next_site_index: int = 0

# Site-specific automation settings
class SiteAutomationSettings(BaseModel):
    site_id: str
    mode: str = "manual"  # "manual" or "automatic"
    enabled: bool = False
    paused: bool = False  # Temporary pause
    generation_hour: int = 9
    frequency: str = "daily"  # "daily", "every_2_days", "every_3_days", "weekly"
    article_length: str = "medium"  # "short", "medium", "long"
    publish_mode: str = "draft"  # "draft" or "publish"
    email_notification: bool = True  # Send email when article generated
    include_product_links: bool = False
    product_links_source: str = ""  # URL or keyword for product search
    max_product_links: int = 3

class SiteAutomationSettingsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    site_id: str
    user_id: str
    mode: str
    enabled: bool
    paused: bool
    generation_hour: int
    frequency: str
    article_length: str
    publish_mode: str
    email_notification: bool
    include_product_links: bool
    product_links_source: str
    max_product_links: int
    last_generation: Optional[str] = None
    next_generation: Optional[str] = None
    articles_generated: int = 0

class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    email_notifications: Optional[bool] = True
    outreach_position: Optional[str] = None
    outreach_phone: Optional[str] = None
    outreach_email: Optional[str] = None

class SettingsResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    company_name: str
    logo_url: str
    primary_color: str
    email_notifications: bool
    user_id: str
    outreach_position: str = ""
    outreach_phone: str = ""
    outreach_email: str = ""

class ArticleTemplateCreate(BaseModel):
    name: str
    description: str
    default_tone: str = "professional"
    default_length: str = "medium"
    prompt_template: str
    keywords_hint: Optional[str] = ""

class ArticleTemplateResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    description: str
    default_tone: str
    default_length: str
    prompt_template: str
    keywords_hint: str
    user_id: str
    created_at: str

# ============ EMAIL HELPER ============

async def send_notification_email(to_email: str, subject: str, html_content: str):
    """Send email notification using Resend"""
    if not RESEND_API_KEY:
        logging.warning("RESEND_API_KEY not configured, skipping email")
        return None
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        result = await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Email sent to {to_email}: {result.get('id')}")
        return result
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")
        return None

def create_article_published_email(article_title: str, article_url: str, company_name: str):
    """Create HTML email for article published notification"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body style="font-family: Arial, sans-serif; background-color: #050505; color: #EDEDED; padding: 40px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #0A0A0A; border-radius: 12px; padding: 32px; border: 1px solid #262626;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="width: 48px; height: 48px; background-color: #00E676; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center;">
                    <span style="font-size: 24px;">⚡</span>
                </div>
            </div>
            <h1 style="color: #00E676; font-size: 24px; margin-bottom: 16px; text-align: center;">Articol Publicat!</h1>
            <p style="color: #A1A1AA; font-size: 16px; line-height: 1.6; margin-bottom: 24px; text-align: center;">
                Articolul tău a fost publicat cu succes pe WordPress.
            </p>
            <div style="background-color: #171717; border-radius: 8px; padding: 20px; margin-bottom: 24px;">
                <h2 style="color: #EDEDED; font-size: 18px; margin: 0 0 8px 0;">{article_title}</h2>
                {f'<a href="{article_url}" style="color: #00E676; text-decoration: none; font-size: 14px;">Vizualizează articolul →</a>' if article_url else ''}
            </div>
            <p style="color: #A1A1AA; font-size: 12px; text-align: center; margin-top: 32px;">
                Trimis de {company_name}
            </p>
        </div>
    </body>
    </html>
    """

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=dict)
async def register(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password": hash_password(user.password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Create default settings
    settings_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "company_name": "My SEO Agency",
        "logo_url": "",
        "primary_color": "#00E676",
        "email_notifications": True
    }
    await db.settings.insert_one(settings_doc)
    
    # Create trial subscription for new user
    subscription_service = SubscriptionService(db)
    await subscription_service.create_trial_subscription(user_id)
    
    # Send welcome email (async, non-blocking)
    from saas.email_service import email_service
    asyncio.create_task(email_service.send_welcome_email(user.email, user.name))
    
    token = create_token(user_id)
    return {"token": token, "user": {"id": user_id, "email": user.email, "name": user.name, "role": "user"}}

@api_router.post("/auth/login", response_model=dict)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user["id"])
    return {"token": token, "user": {"id": user["id"], "email": user["email"], "name": user["name"], "role": user.get("role", "user")}}

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
        role=user.get("role", "user")
    )


class ForgotPasswordRequest(BaseModel):
    email: str


@api_router.post("/auth/forgot-password")
async def forgot_password(data: ForgotPasswordRequest):
    """Send password reset email"""
    import secrets
    
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration
    if not user:
        return {"message": "Dacă există un cont cu acest email, vei primi instrucțiuni."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    
    # Save token to database
    await db.password_resets.update_one(
        {"user_id": user["id"]},
        {"$set": {
            "user_id": user["id"],
            "token": reset_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    # Try to send email if Resend is configured
    try:
        from saas.email_service import email_service
        # For now, just log the reset link
        logging.info(f"[AUTH] Password reset requested for {data.email}, token: {reset_token}")
    except Exception as e:
        logging.warning(f"[AUTH] Could not send reset email: {e}")
    
    return {"message": "Dacă există un cont cu acest email, vei primi instrucțiuni."}


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@api_router.put("/auth/change-password")
async def change_user_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """Change password for logged-in user"""
    # Get user with password from DB
    user_doc = await db.users.find_one({"id": user["id"]})
    if not user_doc:
        raise HTTPException(status_code=404, detail="Utilizator negăsit")
    
    # Verify current password
    if not verify_password(data.current_password, user_doc["password"]):
        raise HTTPException(status_code=400, detail="Parola curentă este incorectă")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parola nouă trebuie să aibă minim 6 caractere")
    
    # Hash and save new password
    new_hashed = hash_password(data.new_password)
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"password": new_hashed, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    logging.info(f"[AUTH] Password changed for user {user['email']}")
    
    # Send email notification (async, non-blocking)
    from saas.email_service import email_service
    asyncio.create_task(email_service.send_password_changed(user['email'], user.get('name', 'Utilizator')))
    
    return {"message": "Parola a fost schimbată cu succes"}


# ============ ARTICLES ROUTES ============

import re

def convert_markdown_to_html(content: str) -> str:
    """Convert any markdown in content to proper HTML"""
    # First check if content has markdown patterns
    has_markdown = bool(
        re.search(r'(?m)^#{1,6}\s', content) or  # Headers like # ## ###
        re.search(r'\*\*[^*]+\*\*', content) or  # Bold **text**
        re.search(r'\*[^*]+\*', content) or      # Italic *text*
        re.search(r'(?m)^[-*+]\s', content) or   # Unordered lists
        re.search(r'(?m)^\d+\.\s', content)      # Ordered lists
    )
    
    if has_markdown:
        # Convert markdown to HTML
        html_content = md_converter.markdown(content, extensions=['tables', 'fenced_code'])
        return html_content
    
    return content

def clean_html_content(content: str) -> str:
    """Remove DOCTYPE, html, head, body tags, convert markdown, and keep only content"""
    # First convert any markdown to HTML
    content = convert_markdown_to_html(content)
    
    # Remove DOCTYPE
    content = re.sub(r'<!DOCTYPE[^>]*>', '', content, flags=re.IGNORECASE)
    # Remove html tags
    content = re.sub(r'</?html[^>]*>', '', content, flags=re.IGNORECASE)
    # Remove head section entirely
    content = re.sub(r'<head>.*?</head>', '', content, flags=re.IGNORECASE | re.DOTALL)
    # Remove body tags but keep content
    content = re.sub(r'</?body[^>]*>', '', content, flags=re.IGNORECASE)
    # Remove meta tags
    content = re.sub(r'<meta[^>]*/?>', '', content, flags=re.IGNORECASE)
    # Remove title tags
    content = re.sub(r'</?title[^>]*>', '', content, flags=re.IGNORECASE)
    # Remove style tags
    content = re.sub(r'<style>.*?</style>', '', content, flags=re.IGNORECASE | re.DOTALL)
    # Clean up extra whitespace
    content = re.sub(r'\n\s*\n', '\n\n', content)
    
    # Replace old years with current year
    current_year = datetime.now().year
    content = re.sub(r'\b202[0-5]\b', str(current_year), content)
    
    return content.strip()

@api_router.post("/articles/generate", response_model=ArticleResponse)
async def generate_article(article: ArticleCreate, user: dict = Depends(get_current_user)):
    # Check subscription limits
    subscription_service = SubscriptionService(db)
    can_generate = await subscription_service.check_article_limit(user["id"])
    if not can_generate:
        usage = await subscription_service.get_usage_stats(user["id"])
        raise HTTPException(
            status_code=402, 
            detail=f"Ai atins limita de {usage['articles_limit']} articole/lună pentru planul {usage['plan_name']}. Upgradează pentru mai multe articole."
        )
    
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        if not api_key:
            raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API pentru a adăuga una.")
        
        length_words = {"short": 500, "medium": 1000, "long": 2000}
        target_words = length_words.get(article.length, 1000)
        
        # ===== WOOCOMMERCE INTEGRATION =====
        products_section = ""
        products_count = 0
        
        if article.site_id:
            site = await db.wordpress_configs.find_one(
                {"id": article.site_id, "user_id": user["id"]},
                {"_id": 0, "site_url": 1, "wc_consumer_key": 1, "wc_consumer_secret": 1}
            )
            
            if site and site.get("wc_consumer_key") and site.get("wc_consumer_secret"):
                try:
                    wc = get_woocommerce_service(
                        site.get("site_url"),
                        site.get("wc_consumer_key"),
                        site.get("wc_consumer_secret")
                    )
                    if wc:
                        products = wc.get_products(per_page=8)
                        products_count = len(products)
                        
                        if products:
                            products_list = []
                            for p in products:
                                price_info = f"{p['price']} RON"
                                if p.get('on_sale') and p.get('regular_price'):
                                    price_info = f"REDUCERE: {p['sale_price']} RON (era {p['regular_price']} RON)"
                                products_list.append(f"- {p['name']}: {price_info} - URL: {p['url']}")
                            
                            products_section = f"""

PRODUSE DIN MAGAZIN (include linkuri către acestea NATURAL în articol):
{chr(10).join(products_list)}

IMPORTANT: Integrează 3-5 linkuri către produse NATURAL în text folosind <a href="URL" target="_blank">nume</a>
"""
                except Exception as wc_err:
                    logging.warning(f"[ARTICLE] WooCommerce error: {wc_err}")
        
        chat = LlmChat(
            api_key=api_key,
            system_message=f"""Ești un expert în scriere de conținut SEO. Scrii NUMAI în limba ROMÂNĂ.
            Folosești DOAR tag-uri HTML pentru conținut: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
            NU folosești: <!DOCTYPE>, <html>, <head>, <body>, <meta>, <title>, <style>
            NU folosești markdown. Doar tag-uri HTML de conținut.
            Scrii articole LUNGI și DETALIATE de minimum {target_words} cuvinte."""
        ).with_model(model_provider, model_name)
        
        prompt = f"""Scrie un articol SEO LUNG și DETALIAT în limba ROMÂNĂ.

TITLU: {article.title}
CUVINTE-CHEIE: {', '.join(article.keywords)}
NIȘĂ: {article.niche}
TON: {article.tone}
LUNGIME MINIMĂ: {target_words} cuvinte
{products_section}
INSTRUCȚIUNI STRICTE:
1. Scrie DOAR în limba ROMÂNĂ
2. Folosește DOAR: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
3. NU include DOCTYPE, html, head, body, meta, style
4. Scrie paragrafe LUNGI și DETALIATE (minim 4-5 propoziții per paragraf)
5. Include cel puțin 8 secțiuni cu <h2>
6. Fiecare secțiune să aibă minim 3 paragrafe
7. Dacă ai primit produse, include 3-5 linkuri către ele NATURAL în text

STRUCTURĂ:
<h2>Introducere</h2>
<p>3 paragrafe de introducere...</p>

<h2>Secțiunea 1</h2>
<p>3 paragrafe detaliate...</p>
... (continuă cu 7+ secțiuni)

<h2>Concluzie</h2>
<p>2 paragrafe de concluzie...</p>

Scrie articolul COMPLET acum (minimum {target_words} cuvinte):"""

        user_message = UserMessage(text=prompt)
        content = await chat.send_message(user_message)
        
        # Clean HTML
        content = clean_html_content(content)
        
        word_count = len(re.findall(r'\b\w+\b', content))
        
        # If too short, request continuation multiple times until we reach target
        attempts = 0
        while word_count < target_words * 0.85 and attempts < 3:
            attempts += 1
            words_needed = target_words - word_count
            continuation_prompt = f"""Continuă articolul. Mai trebuie {words_needed} cuvinte.

Adaugă {max(3, words_needed // 200)} secțiuni noi cu <h2> pe tema "{article.title}".
Fiecare secțiune să aibă 3-4 paragrafe LUNGI.
Folosește DOAR: <h2>, <h3>, <p>, <ul>, <li>, <strong>
Scrie în ROMÂNĂ. Fii FOARTE DETALIAT.

Continuă ACUM:"""
            
            user_message2 = UserMessage(text=continuation_prompt)
            continuation = await chat.send_message(user_message2)
            continuation = clean_html_content(continuation)
            content = content + "\n\n" + continuation
            word_count = len(re.findall(r'\b\w+\b', content))
            logging.info(f"Article continuation {attempts}: now {word_count} words")
        
        seo_score = min(95, 70 + len(article.keywords) * 5)
        
        article_id = str(uuid.uuid4())
        article_doc = {
            "id": article_id,
            "title": article.title,
            "content": content,
            "keywords": article.keywords,
            "niche": article.niche,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user["id"],
            "seo_score": seo_score,
            "word_count": word_count,
            "site_id": article.site_id,
            "has_product_links": products_count > 0,
            "products_count": products_count
        }
        await db.articles.insert_one(article_doc)
        
        # Increment article usage for subscription
        await subscription_service.increment_article_usage(user["id"])
        
        return ArticleResponse(**article_doc)
    except Exception as e:
        logging.error(f"Article generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate article: {str(e)}")

@api_router.post("/articles/{article_id}/regenerate", response_model=ArticleResponse)
async def regenerate_article(article_id: str, user: dict = Depends(get_current_user)):
    """Regenerate an existing article with HTML format"""
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        if not api_key:
            raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
        
        keywords = article.get("keywords", [])
        niche = article.get("niche", "general")
        target_words = max(article.get("word_count", 1000), 1000)
        
        chat = LlmChat(
            api_key=api_key,
            system_message=f"""Ești un expert în scriere de conținut SEO. Scrii NUMAI în limba ROMÂNĂ.
            Folosești DOAR tag-uri HTML pentru conținut: <h2>, <h3>, <p>, <ul>, <li>, <strong>
            NU folosești: <!DOCTYPE>, <html>, <head>, <body>, <meta>, <title>, <style>
            NU folosești markdown. Doar tag-uri HTML de conținut.
            Scrii articole LUNGI și DETALIATE de minimum {target_words} cuvinte."""
        ).with_model(model_provider, model_name)
        
        prompt = f"""Scrie un articol SEO LUNG și DETALIAT în limba ROMÂNĂ.

TITLU: {article['title']}
CUVINTE-CHEIE: {', '.join(keywords)}
NIȘĂ: {niche}
LUNGIME MINIMĂ: {target_words} cuvinte

INSTRUCȚIUNI STRICTE:
1. Scrie DOAR în limba ROMÂNĂ
2. Folosește DOAR: <h2>, <h3>, <p>, <ul>, <li>, <strong>
3. NU include DOCTYPE, html, head, body, meta, style
4. Scrie paragrafe LUNGI și DETALIATE (minim 4-5 propoziții per paragraf)
5. Include cel puțin 8 secțiuni cu <h2>
6. Fiecare secțiune să aibă minim 3 paragrafe

Scrie articolul COMPLET acum (minimum {target_words} cuvinte):"""

        user_message = UserMessage(text=prompt)
        content = await chat.send_message(user_message)
        
        # Clean HTML
        content = clean_html_content(content)
        
        word_count = len(re.findall(r'\b\w+\b', content))
        
        # If too short, request continuation
        if word_count < target_words * 0.8:
            continuation_prompt = f"""Continuă articolul de mai sus. Mai ai nevoie de încă {target_words - word_count} cuvinte.
            
Adaugă încă 4-5 secțiuni noi cu <h2> pe tema "{article['title']}".
Folosește DOAR: <h2>, <h3>, <p>, <ul>, <li>, <strong>
Scrie în ROMÂNĂ. Fii DETALIAT.

Continuă:"""
            
            user_message2 = UserMessage(text=continuation_prompt)
            continuation = await chat.send_message(user_message2)
            continuation = clean_html_content(continuation)
            content = content + "\n\n" + continuation
            word_count = len(re.findall(r'\b\w+\b', content))
        
        seo_score = min(95, 70 + len(keywords) * 5)
        
        # Update the article
        await db.articles.update_one(
            {"id": article_id, "user_id": user["id"]},
            {"$set": {
                "content": content,
                "word_count": word_count,
                "seo_score": seo_score,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        updated_article = await db.articles.find_one({"id": article_id}, {"_id": 0})
        return ArticleResponse(**updated_article)
    except Exception as e:
        logging.error(f"Article regeneration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to regenerate article: {str(e)}")

@api_router.get("/articles", response_model=List[ArticleResponse])
async def get_articles(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
        logging.info(f"[ARTICLES] Filtering by site_id: {site_id}")
    else:
        logging.info(f"[ARTICLES] No site_id filter, returning all articles")
    articles = await db.articles.find(query, {"_id": 0}).to_list(1000)
    logging.info(f"[ARTICLES] Returning {len(articles)} articles")
    return [ArticleResponse(**a) for a in articles]

@api_router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleResponse(**article)

@api_router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, updates: ArticleUpdate, user: dict = Depends(get_current_user)):
    """Update article title, content, keywords or status"""
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = {}
    if updates.title is not None:
        update_data["title"] = updates.title
    if updates.content is not None:
        update_data["content"] = updates.content
        update_data["word_count"] = len(updates.content.split())
    if updates.keywords is not None:
        update_data["keywords"] = updates.keywords
    if updates.status is not None:
        update_data["status"] = updates.status
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.articles.update_one(
            {"id": article_id, "user_id": user["id"]},
            {"$set": update_data}
        )
    
    updated_article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return ArticleResponse(**updated_article)

@api_router.patch("/articles/{article_id}/status")
async def update_article_status(article_id: str, status: str, user: dict = Depends(get_current_user)):
    result = await db.articles.update_one(
        {"id": article_id, "user_id": user["id"]},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Status updated"}

@api_router.delete("/articles/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    result = await db.articles.delete_one({"id": article_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted"}

# ============ KEYWORDS ROUTES ============

@api_router.post("/keywords/research", response_model=List[KeywordResponse])
async def research_keywords(research: KeywordResearch, user: dict = Depends(get_current_user)):
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        
        if not api_key:
            raise HTTPException(status_code=400, detail="Nu ai configurat o cheie API (OpenAI sau Gemini). Mergi la Chei API pentru a adăuga una.")
        
        chat = LlmChat(
            api_key=api_key,
            system_message="""You are an SEO keyword research expert. Generate realistic keyword suggestions with estimated metrics.
            Return ONLY a JSON array with keywords in this exact format, no other text:
            [{"keyword": "example keyword", "volume": 1000, "difficulty": 45, "cpc": 1.50, "trend": "up"}]"""
        ).with_model(model_provider, model_name)
        
        seed_str = ', '.join(research.seed_keywords) if research.seed_keywords else 'general terms'
        prompt = f"""Generate 10 SEO keywords for the niche: {research.niche}
Seed keywords to consider: {seed_str}

Return ONLY a valid JSON array with these fields for each keyword:
- keyword: the keyword phrase
- volume: monthly search volume (100-50000)
- difficulty: SEO difficulty score (1-100)
- cpc: cost per click in USD (0.10-10.00)
- trend: either "up", "down", or "stable"

JSON array only, no explanation:"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        import json
        try:
            # Clean the response
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            keywords_data = json.loads(clean_response)
        except json.JSONDecodeError:
            # Fallback keywords
            keywords_data = [
                {"keyword": f"{research.niche} tips", "volume": 5000, "difficulty": 35, "cpc": 1.20, "trend": "up"},
                {"keyword": f"best {research.niche}", "volume": 8000, "difficulty": 45, "cpc": 2.50, "trend": "up"},
                {"keyword": f"{research.niche} guide", "volume": 3000, "difficulty": 30, "cpc": 0.90, "trend": "stable"},
                {"keyword": f"{research.niche} for beginners", "volume": 4500, "difficulty": 25, "cpc": 1.10, "trend": "up"},
                {"keyword": f"how to {research.niche}", "volume": 6000, "difficulty": 40, "cpc": 1.80, "trend": "stable"},
            ]
        
        keywords = []
        for kw in keywords_data[:10]:
            keyword_doc = {
                "id": str(uuid.uuid4()),
                "keyword": kw.get("keyword", ""),
                "volume": kw.get("volume", 1000),
                "difficulty": kw.get("difficulty", 50),
                "cpc": kw.get("cpc", 1.0),
                "trend": kw.get("trend", "stable"),
                "user_id": user["id"],
                "niche": research.niche,
                "site_id": research.site_id
            }
            await db.keywords.insert_one(keyword_doc)
            keywords.append(KeywordResponse(**keyword_doc))
        
        return keywords
    except Exception as e:
        logging.error(f"Keyword research error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to research keywords: {str(e)}")

@api_router.get("/keywords", response_model=List[KeywordResponse])
async def get_keywords(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    keywords = await db.keywords.find(query, {"_id": 0}).to_list(1000)
    return [KeywordResponse(**k) for k in keywords]

@api_router.delete("/keywords/{keyword_id}")
async def delete_keyword(keyword_id: str, user: dict = Depends(get_current_user)):
    result = await db.keywords.delete_one({"id": keyword_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return {"message": "Keyword deleted"}

# ============ GOOGLE TRENDS ROUTES ============

@api_router.get("/trends/trending")
async def get_trending_searches(user: dict = Depends(get_current_user)):
    """Get current trending searches in Romania"""
    try:
        trends = GoogleTrendsService()
        trending = trends.get_trending_searches()
        return {"trending": trending, "count": len(trending)}
    except Exception as e:
        logging.error(f"[TRENDS] Error: {e}")
        return {"trending": [], "count": 0, "error": str(e)}

@api_router.get("/trends/niche/{niche}")
async def get_trends_for_niche(niche: str, user: dict = Depends(get_current_user)):
    """Get trending topics relevant to a specific niche"""
    try:
        result = get_trending_topics_for_niche(niche)
        return result
    except Exception as e:
        logging.error(f"[TRENDS] Error for niche '{niche}': {e}")
        return {"niche": niche, "error": str(e), "topic_ideas": []}

@api_router.post("/trends/score-keywords")
async def score_keywords(keywords: List[str], user: dict = Depends(get_current_user)):
    """Score keywords by their trending interest"""
    try:
        if not keywords:
            return {"scored_keywords": []}
        scored = score_keywords_by_trend(keywords[:20])  # Limit to 20
        return {"scored_keywords": scored}
    except Exception as e:
        logging.error(f"[TRENDS] Error scoring keywords: {e}")
        return {"scored_keywords": [], "error": str(e)}

@api_router.get("/trends/related/{keyword}")
async def get_related_queries(keyword: str, user: dict = Depends(get_current_user)):
    """Get related queries for a keyword"""
    try:
        trends = GoogleTrendsService()
        related = trends.get_related_queries(keyword)
        suggestions = trends.get_suggestions(keyword)
        return {
            "keyword": keyword,
            "top_queries": related.get("top", []),
            "rising_queries": related.get("rising", []),
            "suggestions": suggestions
        }
    except Exception as e:
        logging.error(f"[TRENDS] Error for keyword '{keyword}': {e}")
        return {"keyword": keyword, "error": str(e)}

# ============ REPORTS ROUTES ============

@api_router.get("/reports/weekly")
async def get_weekly_report(user: dict = Depends(get_current_user)):
    """Get weekly performance report"""
    user_id = user["id"]
    
    # Get user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate stats for last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Get all articles from last 7 days
    recent_articles = await db.articles.find({
        "user_id": user_id,
        "created_at": {"$gte": seven_days_ago.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    # Count by article type
    article_types_count = {}
    for art in recent_articles:
        art_type = art.get("article_type", "general")
        article_types_count[art_type] = article_types_count.get(art_type, 0) + 1
    
    # Count with product links
    with_products = sum(1 for a in recent_articles if a.get("has_product_links"))
    
    # Count with trending keywords
    with_trending = sum(1 for a in recent_articles if a.get("has_trending_keywords"))
    
    # Published count
    published = sum(1 for a in recent_articles if a.get("status") == "published")
    
    # Draft count
    drafts = sum(1 for a in recent_articles if a.get("status") == "draft")
    
    # Average SEO score
    seo_scores = [a.get("seo_score", 0) for a in recent_articles if a.get("seo_score")]
    avg_seo_score = round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0
    
    # Average word count
    word_counts = [a.get("word_count", 0) for a in recent_articles if a.get("word_count")]
    avg_word_count = round(sum(word_counts) / len(word_counts)) if word_counts else 0
    
    # Stats per site
    sites_stats = []
    for site in sites:
        site_articles = [a for a in recent_articles if a.get("site_id") == site["id"]]
        site_published = sum(1 for a in site_articles if a.get("status") == "published")
        site_drafts = sum(1 for a in site_articles if a.get("status") == "draft")
        sites_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name") or site.get("site_url"),
            "articles_generated": len(site_articles),
            "articles_published": site_published,
            "articles_draft": site_drafts
        })
    
    # Daily breakdown
    daily_stats = {}
    for art in recent_articles:
        created = art.get("created_at", "")[:10]  # Get date part
        if created not in daily_stats:
            daily_stats[created] = {"generated": 0, "published": 0}
        daily_stats[created]["generated"] += 1
        if art.get("status") == "published":
            daily_stats[created]["published"] += 1
    
    return {
        "period": {
            "start": seven_days_ago.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "days": 7
        },
        "summary": {
            "total_articles": len(recent_articles),
            "published": published,
            "drafts": drafts,
            "with_product_links": with_products,
            "with_trending_keywords": with_trending,
            "avg_seo_score": avg_seo_score,
            "avg_word_count": avg_word_count
        },
        "article_types": article_types_count,
        "sites_stats": sites_stats,
        "daily_stats": daily_stats
    }

@api_router.get("/reports/monthly")
async def get_monthly_report(user: dict = Depends(get_current_user)):
    """Get monthly performance report"""
    user_id = user["id"]
    
    # Get user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate stats for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get all articles from last 30 days
    recent_articles = await db.articles.find({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    # Count by article type
    article_types_count = {}
    for art in recent_articles:
        art_type = art.get("article_type", "general")
        article_types_count[art_type] = article_types_count.get(art_type, 0) + 1
    
    # Counts
    with_products = sum(1 for a in recent_articles if a.get("has_product_links"))
    with_trending = sum(1 for a in recent_articles if a.get("has_trending_keywords"))
    published = sum(1 for a in recent_articles if a.get("status") == "published")
    drafts = sum(1 for a in recent_articles if a.get("status") == "draft")
    auto_generated = sum(1 for a in recent_articles if a.get("auto_generated"))
    
    # Averages
    seo_scores = [a.get("seo_score", 0) for a in recent_articles if a.get("seo_score")]
    avg_seo_score = round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0
    word_counts = [a.get("word_count", 0) for a in recent_articles if a.get("word_count")]
    avg_word_count = round(sum(word_counts) / len(word_counts)) if word_counts else 0
    
    # Outreach stats
    outreach_sent = await db.backlink_outreach.count_documents({
        "user_id": user_id,
        "status": "sent"
    })
    outreach_pending = await db.backlink_outreach.count_documents({
        "user_id": user_id,
        "status": "pending_approval"
    })
    
    # Stats per site
    sites_stats = []
    for site in sites:
        site_articles = [a for a in recent_articles if a.get("site_id") == site["id"]]
        site_published = sum(1 for a in site_articles if a.get("status") == "published")
        sites_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name") or site.get("site_url"),
            "articles_generated": len(site_articles),
            "articles_published": site_published
        })
    
    # Weekly breakdown
    weekly_stats = {}
    for art in recent_articles:
        created = art.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                week_num = dt.isocalendar()[1]
                week_key = f"Săpt. {week_num}"
                if week_key not in weekly_stats:
                    weekly_stats[week_key] = {"generated": 0, "published": 0}
                weekly_stats[week_key]["generated"] += 1
                if art.get("status") == "published":
                    weekly_stats[week_key]["published"] += 1
            except:
                pass
    
    return {
        "period": {
            "start": thirty_days_ago.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "days": 30
        },
        "summary": {
            "total_articles": len(recent_articles),
            "auto_generated": auto_generated,
            "published": published,
            "drafts": drafts,
            "with_product_links": with_products,
            "with_trending_keywords": with_trending,
            "avg_seo_score": avg_seo_score,
            "avg_word_count": avg_word_count
        },
        "outreach": {
            "emails_sent": outreach_sent,
            "pending_approval": outreach_pending
        },
        "article_types": article_types_count,
        "sites_stats": sites_stats,
        "weekly_stats": weekly_stats
    }

# ============ CALENDAR ROUTES ============

@api_router.post("/calendar", response_model=CalendarResponse)
async def create_calendar_entry(entry: CalendarEntry, user: dict = Depends(get_current_user)):
    entry_id = str(uuid.uuid4())
    entry_doc = {
        "id": entry_id,
        "title": entry.title,
        "keywords": entry.keywords,
        "scheduled_date": entry.scheduled_date,
        "status": entry.status,
        "article_id": None,
        "user_id": user["id"],
        "site_id": entry.site_id
    }
    await db.calendar.insert_one(entry_doc)
    return CalendarResponse(**entry_doc)

@api_router.get("/calendar", response_model=List[CalendarResponse])
async def get_calendar(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    entries = await db.calendar.find(query, {"_id": 0}).to_list(1000)
    return [CalendarResponse(**e) for e in entries]

@api_router.patch("/calendar/{entry_id}")
async def update_calendar_entry(entry_id: str, entry: CalendarEntry, user: dict = Depends(get_current_user)):
    update_data = entry.model_dump(exclude_unset=True)
    result = await db.calendar.update_one(
        {"id": entry_id, "user_id": user["id"]},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry updated"}

@api_router.delete("/calendar/{entry_id}")
async def delete_calendar_entry(entry_id: str, user: dict = Depends(get_current_user)):
    result = await db.calendar.delete_one({"id": entry_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}

@api_router.post("/calendar/generate-90-days")
async def generate_90_day_calendar(niche: str, site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        if not api_key:
            raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
        
        chat = LlmChat(
            api_key=api_key,
            system_message="""You are an SEO content strategist. Generate editorial calendar entries.
            Return ONLY a JSON array, no other text."""
        ).with_model(model_provider, model_name)
        
        prompt = f"""Generate 30 article topics for a 90-day editorial calendar for the niche: {niche}
        
Return ONLY a valid JSON array with objects containing:
- title: article title
- keywords: array of 3-5 target keywords

Example format:
[{{"title": "Article Title", "keywords": ["kw1", "kw2", "kw3"]}}]

Generate 30 diverse, SEO-friendly topics. JSON array only:"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        import json
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            topics = json.loads(clean_response)
        except json.JSONDecodeError:
            topics = [{"title": f"{niche} Topic {i+1}", "keywords": [niche, "tips", "guide"]} for i in range(30)]
        
        entries = []
        base_date = datetime.now(timezone.utc)
        
        for i, topic in enumerate(topics[:30]):
            scheduled_date = base_date + timedelta(days=i * 3)
            entry_doc = {
                "id": str(uuid.uuid4()),
                "title": topic.get("title", f"Article {i+1}"),
                "keywords": topic.get("keywords", [niche]),
                "scheduled_date": scheduled_date.strftime("%Y-%m-%d"),
                "status": "planned",
                "article_id": None,
                "user_id": user["id"],
                "site_id": site_id
            }
            await db.calendar.insert_one(entry_doc)
            entries.append(CalendarResponse(**entry_doc))
        
        return entries
    except Exception as e:
        logging.error(f"Calendar generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate calendar: {str(e)}")

# ============ BACKLINKS ROUTES ============

@api_router.get("/backlinks/generate/{niche}")
async def generate_backlinks_for_niche(niche: str, user: dict = Depends(get_current_user)):
    """Generate AI-powered backlink suggestions for a specific niche"""
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        if not api_key:
            raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
        
        chat = LlmChat(
            api_key=api_key,
            system_message="""You are an SEO expert specializing in backlink research. Generate realistic backlink opportunities.
            Return ONLY a JSON array with backlink sites, no other text."""
        ).with_model(model_provider, model_name)
        
        prompt = f"""Generate 30 realistic backlink opportunities for the niche: {niche}

Return ONLY a valid JSON array with these fields for each site:
- domain: realistic domain name relevant to the niche (use real-looking domains like "maritimejobs.org", "seafarerworld.com", etc.)
- da: domain authority score (20-80)
- pa: page authority score (15-75)
- category: category that fits the niche
- type: type of backlink opportunity (Guest Post, Directory, Forum, Blog Comment, Resource Page, Partnership)
- price: estimated cost in USD (0 for free, or 25-500 for paid)
- contact_info: how to contact (email pattern or "Contact Form")

Make the domains realistic and relevant to "{niche}". Mix free and paid opportunities.
JSON array only:"""

        user_message = UserMessage(text=prompt)
        response = await chat.send_message(user_message)
        
        try:
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            backlinks_data = json.loads(clean_response)
        except json.JSONDecodeError:
            # Fallback
            backlinks_data = [
                {"domain": f"{niche.lower().replace(' ', '')}-blog.com", "da": 45, "pa": 40, "category": niche, "type": "Guest Post", "price": 50, "contact_info": "Contact Form"},
                {"domain": f"{niche.lower().replace(' ', '')}-directory.org", "da": 35, "pa": 30, "category": niche, "type": "Directory", "price": 0, "contact_info": "Free submission"},
            ]
        
        # Save to database with niche tag
        saved_backlinks = []
        for bl in backlinks_data[:30]:
            backlink_doc = {
                "id": str(uuid.uuid4()),
                "domain": bl.get("domain", ""),
                "da": bl.get("da", 30),
                "pa": bl.get("pa", 25),
                "category": bl.get("category", niche),
                "type": bl.get("type", "Guest Post"),
                "status": "available",
                "price": bl.get("price", 0),
                "contact_info": bl.get("contact_info", "Contact Form"),
                "niche": niche,
                "user_id": user["id"]
            }
            await db.niche_backlinks.insert_one(backlink_doc)
            # Remove _id before adding to response
            backlink_doc.pop("_id", None)
            saved_backlinks.append(backlink_doc)
        
        return saved_backlinks
    except Exception as e:
        logging.error(f"Backlink generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate backlinks: {str(e)}")

@api_router.get("/backlinks/niche/{niche}")
async def get_backlinks_by_niche(niche: str, user: dict = Depends(get_current_user)):
    """Get saved backlinks for a specific niche"""
    backlinks = await db.niche_backlinks.find({"niche": niche, "user_id": user["id"]}, {"_id": 0}).to_list(100)
    return backlinks

@api_router.get("/backlinks", response_model=List[BacklinkSite])
async def get_backlink_sites():
    sites = await db.backlink_sites.find({}, {"_id": 0}).to_list(1000)
    if not sites:
        # Seed with demo data
        categories = ["Technology", "Business", "Health", "Finance", "Marketing", "Education", "Lifestyle", "News"]
        demo_sites = []
        for i in range(300):
            site = {
                "id": str(uuid.uuid4()),
                "domain": f"site{i+1}.example.com",
                "da": 20 + (i % 60),
                "pa": 15 + (i % 55),
                "category": categories[i % len(categories)],
                "status": "available",
                "price": round(10 + (i % 90) * 1.5, 2)
            }
            demo_sites.append(site)
        await db.backlink_sites.insert_many(demo_sites)
        sites = demo_sites
    return [BacklinkSite(**s) for s in sites]

@api_router.post("/backlinks/request/{site_id}")
async def request_backlink(site_id: str, user: dict = Depends(get_current_user)):
    site = await db.backlink_sites.find_one({"id": site_id}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    request_doc = {
        "id": str(uuid.uuid4()),
        "site_id": site_id,
        "domain": site["domain"],
        "user_id": user["id"],
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.backlink_requests.insert_one(request_doc)
    return {"message": "Backlink request submitted", "request_id": request_doc["id"]}

@api_router.get("/backlinks/requests")
async def get_backlink_requests(user: dict = Depends(get_current_user)):
    requests = await db.backlink_requests.find({"user_id": user["id"]}, {"_id": 0}).to_list(1000)
    return requests

# ============ BACKLINK OUTREACH SYSTEM ============

@api_router.post("/backlinks/outreach/prepare")
async def prepare_backlink_outreach(
    backlink_id: str,
    site_id: str,
    user: dict = Depends(get_current_user)
):
    """Prepare outreach email by finding relevant article and generating email"""
    
    # Get the backlink site info
    backlink = await db.niche_backlinks.find_one(
        {"id": backlink_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not backlink:
        raise HTTPException(status_code=404, detail="Backlink not found")
    
    # Get user's WordPress site
    wp_site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0, "app_password": 0}
    )
    if not wp_site:
        raise HTTPException(status_code=404, detail="WordPress site not found")
    
    # Get user's articles for this site
    articles = await db.articles.find(
        {"user_id": user["id"], "site_id": site_id, "status": "published"},
        {"_id": 0, "id": 1, "title": 1, "keywords": 1, "summary": 1, "wordpress_url": 1}
    ).sort("created_at", -1).to_list(20)
    
    if not articles:
        # Try to get any article from any site
        articles = await db.articles.find(
            {"user_id": user["id"], "status": "published"},
            {"_id": 0, "id": 1, "title": 1, "keywords": 1, "summary": 1, "wordpress_url": 1, "site_id": 1}
        ).sort("created_at", -1).to_list(20)
    
    if not articles:
        raise HTTPException(status_code=404, detail="No published articles found")
    
    # Use AI to find the most relevant article
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        # Just pick the first article if no AI
        best_article = articles[0]
    else:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            articles_summary = "\n".join([
                f"- ID: {a['id']}, Title: {a['title']}, Keywords: {a.get('keywords', 'N/A')}"
                for a in articles[:10]
            ])
            
            match_response = await chat(
                api_key=llm_api_key,
                messages=[Message(role="user", content=f"""
                    Find the most relevant article for outreach to this website:
                    Target site: {backlink['domain']}
                    Target niche/category: {backlink.get('category', backlink.get('niche', 'General'))}
                    Target site type: {backlink.get('type', 'General')}
                    
                    Available articles:
                    {articles_summary}
                    
                    Return ONLY the article ID that is most relevant. Just the ID, nothing else.
                """)],
                model="gpt-4o",
                session_id=f"match-{uuid.uuid4()}"
            )
            
            best_article_id = match_response.strip()
            best_article = next((a for a in articles if a['id'] == best_article_id), articles[0])
        except Exception as e:
            logging.error(f"AI matching failed: {e}")
            best_article = articles[0]
    
    # Generate personalized outreach email
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        # Get user info for signature
        user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0, "name": 1, "email": 1})
        user_name = user_doc.get("name", "Administrator") if user_doc else "Administrator"
        
        # Site contact info - use site settings or defaults
        site_email = wp_site.get("contact_email", "martechassistance@gmail.com")
        site_website = wp_site.get("site_url", "https://martechassistance.com")
        site_phone = wp_site.get("contact_phone", "0721578660")
        site_name = wp_site.get("site_name", "Martech Assistance")
        
        # Detect target site language based on domain
        target_domain = backlink['domain'].lower()
        if target_domain.endswith('.ro'):
            target_language = "Romanian"
        elif any(target_domain.endswith(ext) for ext in ['.com', '.org', '.net', '.io', '.co', '.uk', '.us']):
            target_language = "English"
        else:
            target_language = "English"  # Default to English for unknown
        
        # My site is in Romanian
        my_site_language = "Romanian"
        
        email_response = await chat(
            api_key=llm_api_key,
            messages=[Message(role="user", content=f"""
                Generate a professional outreach email for requesting a backlink.
                
                IMPORTANT LANGUAGE RULES:
                - Target website ({backlink['domain']}) language: {target_language}
                - My website language: {my_site_language} (Romanian)
                - Write the ENTIRE email in: {target_language}
                
                Target website: {backlink['domain']}
                Target website type: {backlink.get('type', 'General')}
                Contact email: {backlink.get('contact_info', 'N/A')}
                
                My website: {site_website}
                My niche: {wp_site.get('niche', 'General')}
                My company: {site_name}
                
                Article to promote (written in Romanian):
                - Title: {best_article['title']}
                - URL: {best_article.get('wordpress_url', site_website)}
                - Keywords: {best_article.get('keywords', 'N/A')}
                
                SIGNATURE INFO (MUST include at the end):
                - Name: {user_name}
                - Position: Administrator
                - Company: {site_name}
                - Email: {site_email}
                - Website: {site_website}
                - Phone: {site_phone}
                
                CRITICAL INSTRUCTIONS:
                1. Write the ENTIRE email in {target_language}
                2. Include a brief summary of the article content translated into {target_language} (2-3 sentences)
                3. If target language is English but article is Romanian, mention that the article is valuable for Romanian-speaking audience
                4. Has a catchy subject line in {target_language}
                5. Introduces yourself briefly
                6. Mentions why your article would be valuable for their readers
                7. Includes the article link naturally (ONLY ONCE, do not duplicate)
                8. Has a clear call to action
                9. Is polite and not pushy
                10. MUST include full signature with name, company, email, website and phone at the end
                
                Format the response as JSON:
                {{"subject": "...", "body": "...", "language": "{target_language}"}}
            """)],
            model="gpt-4o",
            session_id=f"outreach-{uuid.uuid4()}"
        )
        
        # Parse email response
        clean_email = email_response.strip()
        if clean_email.startswith("```"):
            clean_email = clean_email.split("```")[1]
            if clean_email.startswith("json"):
                clean_email = clean_email[4:]
        
        email_data = json.loads(clean_email)
        
    except Exception as e:
        logging.error(f"Email generation failed: {e}")
        email_data = {
            "subject": f"Content Collaboration Opportunity - {best_article['title']}",
            "body": f"""Hi,

I came across your website {backlink['domain']} and I think our content could be valuable for your audience.

I recently published an article titled "{best_article['title']}" that covers topics relevant to your readers.

You can check it out here: {best_article.get('wordpress_url', site_website)}

Would you be interested in featuring it or collaborating in some way?

Best regards,

{user_name}
Administrator
{site_name}
Email: {site_email}
Website: {site_website}
Phone: {site_phone}"""
        }
    
    # Save the outreach draft
    outreach_id = str(uuid.uuid4())
    outreach_doc = {
        "id": outreach_id,
        "user_id": user["id"],
        "backlink_id": backlink_id,
        "backlink_domain": backlink['domain'],
        "site_id": site_id,
        "article_id": best_article['id'],
        "article_title": best_article['title'],
        "article_url": best_article.get('wordpress_url', ''),
        "contact_email": backlink.get('contact_info', ''),
        "email_subject": email_data['subject'],
        "email_body": email_data['body'],
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.backlink_outreach.insert_one(outreach_doc)
    
    return {
        "id": outreach_id,
        "backlink": backlink,
        "article": best_article,
        "email": email_data,
        "contact_email": backlink.get('contact_info', '')
    }

@api_router.get("/backlinks/outreach")
async def get_outreach_list(user: dict = Depends(get_current_user)):
    """Get all outreach drafts and sent emails"""
    outreach = await db.backlink_outreach.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return outreach

@api_router.post("/backlinks/outreach/{outreach_id}/send")
async def send_outreach_email(
    outreach_id: str,
    user: dict = Depends(get_current_user)
):
    """Send the outreach email"""
    
    outreach = await db.backlink_outreach.find_one(
        {"id": outreach_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")
    
    if not outreach.get('contact_email'):
        raise HTTPException(status_code=400, detail="No contact email available")
    
    # Get user's email API key (BYOAK)
    email_key, email_provider = await get_user_email_key(user["id"], user.get("role") == "admin")
    
    if not email_key:
        raise HTTPException(status_code=400, detail="Nu ai configurat o cheie API pentru email (Resend sau SendGrid). Mergi la Chei API pentru a adăuga una.")
    
    # Get user info for sender name
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    sender_name = user_doc.get('name', 'SEO Team') if user_doc else 'SEO Team'
    
    try:
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            {outreach['email_body'].replace(chr(10), '<br>')}
        </div>
        """
        
        if email_provider == "resend":
            import resend as resend_lib
            resend_lib.api_key = email_key
            resend_lib.Emails.send({
                "from": f"{sender_name} <{SENDER_EMAIL}>",
                "to": [outreach['contact_email']],
                "subject": outreach['email_subject'],
                "html": email_html
            })
        elif email_provider == "sendgrid":
            import sendgrid
            from sendgrid.helpers.mail import Mail, Email, To, Content
            sg = sendgrid.SendGridAPIClient(api_key=email_key)
            message = Mail(
                from_email=Email(SENDER_EMAIL, sender_name),
                to_emails=To(outreach['contact_email']),
                subject=outreach['email_subject'],
                html_content=Content("text/html", email_html)
            )
            sg.send(message)
        
        # Update status
        await db.backlink_outreach.update_one(
            {"id": outreach_id},
            {"$set": {
                "status": "sent",
                "sent_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True, "message": f"Email sent to {outreach['contact_email']}"}
        
    except Exception as e:
        logging.error(f"Failed to send outreach email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@api_router.put("/backlinks/outreach/{outreach_id}")
async def update_outreach(
    outreach_id: str,
    subject: str = None,
    body: str = None,
    user: dict = Depends(get_current_user)
):
    """Update outreach email before sending"""
    
    update_data = {}
    if subject:
        update_data["email_subject"] = subject
    if body:
        update_data["email_body"] = body
    
    if update_data:
        await db.backlink_outreach.update_one(
            {"id": outreach_id, "user_id": user["id"]},
            {"$set": update_data}
        )
    
    return {"success": True}

@api_router.post("/backlinks/outreach/{outreach_id}/mark-responded")
async def mark_outreach_responded(
    outreach_id: str,
    response_type: str = "positive",  # positive, negative, no_response
    user: dict = Depends(get_current_user)
):
    """Mark outreach as responded"""
    
    await db.backlink_outreach.update_one(
        {"id": outreach_id, "user_id": user["id"]},
        {"$set": {
            "status": "responded",
            "response_type": response_type,
            "responded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True}

@api_router.delete("/backlinks/outreach/{outreach_id}")
async def delete_outreach(
    outreach_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete an outreach draft"""
    
    await db.backlink_outreach.delete_one(
        {"id": outreach_id, "user_id": user["id"]}
    )
    
    return {"success": True}

@api_router.get("/backlinks/outreach/pending")
async def get_pending_outreach(user: dict = Depends(get_current_user)):
    """Get outreach emails pending approval"""
    outreach = await db.backlink_outreach.find(
        {"user_id": user["id"], "status": "pending_approval"},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return outreach

@api_router.post("/backlinks/outreach/{outreach_id}/approve")
async def approve_outreach_email(
    outreach_id: str,
    user: dict = Depends(get_current_user)
):
    """Approve and send an outreach email"""
    
    outreach = await db.backlink_outreach.find_one(
        {"id": outreach_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not outreach:
        raise HTTPException(status_code=404, detail="Outreach not found")
    
    if not outreach.get('contact_email'):
        raise HTTPException(status_code=400, detail="No contact email available")
    
    # Get user info for sender name
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    sender_name = user_doc.get('name', 'SEO Team') if user_doc else 'SEO Team'
    
    # Send email using Resend
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    try:
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            {outreach['email_body'].replace(chr(10), '<br>')}
        </div>
        """
        
        resend.Emails.send({
            "from": f"{sender_name} <{SENDER_EMAIL}>",
            "to": [outreach['contact_email']],
            "subject": outreach['email_subject'],
            "html": email_html
        })
        
        # Update status to sent
        await db.backlink_outreach.update_one(
            {"id": outreach_id},
            {"$set": {
                "status": "sent",
                "approved_at": datetime.now(timezone.utc).isoformat(),
                "sent_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        logging.info(f"[OUTREACH] Email sent to {outreach['contact_email']} for {outreach['backlink_domain']}")
        return {"success": True, "message": f"Email sent to {outreach['contact_email']}"}
        
    except Exception as e:
        logging.error(f"[OUTREACH] Failed to send email: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")

@api_router.post("/backlinks/outreach/{outreach_id}/reject")
async def reject_outreach_email(
    outreach_id: str,
    user: dict = Depends(get_current_user)
):
    """Reject/skip an outreach email"""
    
    await db.backlink_outreach.update_one(
        {"id": outreach_id, "user_id": user["id"]},
        {"$set": {
            "status": "rejected",
            "rejected_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True}

@api_router.post("/backlinks/outreach/approve-all")
async def approve_all_outreach(user: dict = Depends(get_current_user)):
    """Approve and send all pending outreach emails"""
    
    pending = await db.backlink_outreach.find(
        {"user_id": user["id"], "status": "pending_approval"},
        {"_id": 0}
    ).to_list(100)
    
    if not pending:
        return {"success": True, "sent": 0, "message": "No pending emails"}
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    sender_name = user_doc.get('name', 'SEO Team') if user_doc else 'SEO Team'
    
    sent_count = 0
    for outreach in pending:
        if not outreach.get('contact_email'):
            continue
        
        try:
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                {outreach['email_body'].replace(chr(10), '<br>')}
            </div>
            """
            
            resend.Emails.send({
                "from": f"{sender_name} <{SENDER_EMAIL}>",
                "to": [outreach['contact_email']],
                "subject": outreach['email_subject'],
                "html": email_html
            })
            
            await db.backlink_outreach.update_one(
                {"id": outreach["id"]},
                {"$set": {
                    "status": "sent",
                    "approved_at": datetime.now(timezone.utc).isoformat(),
                    "sent_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            sent_count += 1
            
        except Exception as e:
            logging.error(f"[OUTREACH] Failed to send to {outreach.get('contact_email')}: {e}")
    
    return {"success": True, "sent": sent_count, "total": len(pending)}

@api_router.get("/backlinks/outreach/stats")
async def get_outreach_stats(user: dict = Depends(get_current_user)):
    """Get outreach statistics"""
    
    pending = await db.backlink_outreach.count_documents({
        "user_id": user["id"], "status": "pending_approval"
    })
    
    sent = await db.backlink_outreach.count_documents({
        "user_id": user["id"], "status": "sent"
    })
    
    responded = await db.backlink_outreach.count_documents({
        "user_id": user["id"], "status": "responded"
    })
    
    rejected = await db.backlink_outreach.count_documents({
        "user_id": user["id"], "status": "rejected"
    })
    
    return {
        "pending_approval": pending,
        "sent": sent,
        "responded": responded,
        "rejected": rejected,
        "total": pending + sent + responded + rejected
    }


# ============ BACKLINK AUTOMATION STATUS ============

@api_router.get("/backlinks/automation-status")
async def get_backlink_automation_status(user: dict = Depends(get_current_user)):
    """Get backlink automation status for all sites"""
    
    # Get user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "site_name": 1, "site_url": 1, "niche": 1}
    ).to_list(100)
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_ago = today_start - timedelta(days=7)
    
    sites_status = []
    total_emails_today = 0
    total_emails_7_days = 0
    last_outreach = None
    
    for site in sites:
        site_id = site.get("id")
        niche = site.get("niche", "")
        
        # Emails sent today for this site
        emails_today = await db.backlink_outreach.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "status": "sent",
            "sent_at": {"$gte": today_start.isoformat()}
        })
        
        # Emails sent yesterday
        emails_yesterday = await db.backlink_outreach.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "status": "sent",
            "sent_at": {"$gte": yesterday_start.isoformat(), "$lt": today_start.isoformat()}
        })
        
        # Emails sent last 7 days
        emails_7_days = await db.backlink_outreach.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "status": "sent",
            "sent_at": {"$gte": week_ago.isoformat()}
        })
        
        # Total FREE opportunities for this niche
        free_opportunities = await db.niche_backlinks.count_documents({
            "user_id": user["id"],
            "niche": niche,
            "$or": [
                {"is_free": True},
                {"price": "Free"},
                {"price": 0},
                {"price": {"$regex": "free", "$options": "i"}}
            ]
        })
        
        # Responses received
        responses = await db.backlink_outreach.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "status": "responded"
        })
        
        # New opportunities found today
        new_opportunities = await db.niche_backlinks.count_documents({
            "user_id": user["id"],
            "niche": niche,
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        # Last outreach for this site
        last_site_outreach = await db.backlink_outreach.find_one(
            {"user_id": user["id"], "site_id": site_id, "status": "sent"},
            {"_id": 0, "sent_at": 1},
            sort=[("sent_at", -1)]
        )
        
        if last_site_outreach and last_site_outreach.get("sent_at"):
            if not last_outreach or last_site_outreach["sent_at"] > last_outreach:
                last_outreach = last_site_outreach["sent_at"]
        
        total_emails_today += emails_today
        total_emails_7_days += emails_7_days
        
        sites_status.append({
            "site_id": site_id,
            "site_name": site.get("site_name") or site.get("site_url", "Unknown"),
            "niche": niche,
            "emails_sent_today": emails_today,
            "emails_sent_yesterday": emails_yesterday,
            "emails_sent_7_days": emails_7_days,
            "remaining_today": max(0, 15 - emails_today),
            "total_free_opportunities": free_opportunities,
            "responses_received": responses,
            "new_opportunities_today": new_opportunities
        })
    
    return {
        "sites": sites_status,
        "total_emails_today": total_emails_today,
        "total_emails_7_days": total_emails_7_days,
        "last_outreach": last_outreach,
        "next_run": "12:30 (ora României)",
        "max_emails_per_site_per_day": 15
    }


# ============ WEB 2.0 BACKLINK SYSTEM ============

class Web2Config(BaseModel):
    platform: str  # medium, blogger, wordpress_com, tumblr, linkedin
    username: str = ""
    api_key: str = ""
    blog_url: str = ""

@api_router.get("/web2/platforms")
async def get_web2_platforms(user: dict = Depends(get_current_user)):
    """Get configured Web 2.0 platforms"""
    platforms = await db.web2_configs.find(
        {"user_id": user["id"]},
        {"_id": 0, "api_key": 0}
    ).to_list(20)
    return platforms

@api_router.post("/web2/configure")
async def configure_web2_platform(
    config: Web2Config,
    user: dict = Depends(get_current_user)
):
    """Configure a Web 2.0 platform for auto-posting"""
    
    existing = await db.web2_configs.find_one({
        "user_id": user["id"],
        "platform": config.platform
    })
    
    config_doc = {
        "user_id": user["id"],
        "platform": config.platform,
        "username": config.username,
        "api_key": config.api_key,
        "blog_url": config.blog_url,
        "enabled": True,
        "posts_count": 0,
        "configured_at": datetime.now(timezone.utc).isoformat()
    }
    
    if existing:
        await db.web2_configs.update_one(
            {"user_id": user["id"], "platform": config.platform},
            {"$set": config_doc}
        )
    else:
        config_doc["id"] = str(uuid.uuid4())
        await db.web2_configs.insert_one(config_doc)
    
    return {"success": True, "platform": config.platform}

@api_router.post("/web2/generate-post/{article_id}")
async def generate_web2_post(
    article_id: str,
    platform: str,
    user: dict = Depends(get_current_user)
):
    """Generate a Web 2.0 post for an article (for manual copy-paste)"""
    
    article = await db.articles.find_one(
        {"id": article_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Get the WordPress site for this article
    site = await db.wordpress_configs.find_one(
        {"id": article.get("site_id"), "user_id": user["id"]},
        {"_id": 0, "app_password": 0}
    )
    
    original_url = article.get("wordpress_url", site.get("site_url") if site else "")
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        
        platform_instructions = {
            "medium": "Write a Medium article (800-1000 words) with engaging storytelling, use headers (##), include a compelling hook, and naturally link to the original article.",
            "blogger": "Write a Blogger post (500-700 words) with SEO-friendly structure, use H2 and H3 tags, include the link prominently.",
            "linkedin": "Write a LinkedIn article (400-600 words) with professional tone, use bullet points, include statistics if relevant, and a clear CTA to read the full article.",
            "tumblr": "Write a Tumblr post (300-400 words) with casual, engaging tone, use relevant tags suggestions, include the link.",
            "pinterest": "Write a Pinterest pin description (150-200 words) with keywords, include the link, and suggest 5-10 relevant hashtags."
        }
        
        instruction = platform_instructions.get(platform, platform_instructions["medium"])
        
        response = await chat(
            api_key=llm_api_key,
            messages=[Message(role="user", content=f"""
                Create a {platform} post based on this article:
                
                Title: {article['title']}
                Summary: {article.get('summary', '')}
                Keywords: {article.get('keywords', '')}
                Original URL: {original_url}
                
                Instructions: {instruction}
                
                Return as JSON:
                {{
                    "title": "catchy title for {platform}",
                    "content": "the full post content with the link included",
                    "tags": ["tag1", "tag2", "tag3"],
                    "meta_description": "SEO description"
                }}
            """)],
            model="gpt-4o",
            session_id=f"web2-{uuid.uuid4()}"
        )
        
        # Parse response
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        
        post_data = json.loads(clean_response)
        
        # Save the generated post
        post_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "article_id": article_id,
            "platform": platform,
            "title": post_data.get("title", article["title"]),
            "content": post_data.get("content", ""),
            "tags": post_data.get("tags", []),
            "meta_description": post_data.get("meta_description", ""),
            "original_url": original_url,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.web2_posts.insert_one(post_doc)
        
        return {
            "id": post_doc["id"],
            "platform": platform,
            "title": post_data.get("title"),
            "content": post_data.get("content"),
            "tags": post_data.get("tags"),
            "original_url": original_url
        }
        
    except Exception as e:
        logging.error(f"Error generating Web 2.0 post: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/web2/posts")
async def get_web2_posts(user: dict = Depends(get_current_user)):
    """Get all generated Web 2.0 posts"""
    posts = await db.web2_posts.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return posts

@api_router.post("/web2/posts/{post_id}/mark-published")
async def mark_web2_post_published(
    post_id: str,
    published_url: str = "",
    user: dict = Depends(get_current_user)
):
    """Mark a Web 2.0 post as published"""
    
    await db.web2_posts.update_one(
        {"id": post_id, "user_id": user["id"]},
        {"$set": {
            "status": "published",
            "published_url": published_url,
            "published_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True}

@api_router.delete("/web2/posts/{post_id}")
async def delete_web2_post(
    post_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a Web 2.0 post"""
    await db.web2_posts.delete_one({"id": post_id, "user_id": user["id"]})
    return {"success": True}

# Manual triggers for scheduled tasks
@api_router.post("/backlinks/search-opportunities")
async def trigger_backlink_search(user: dict = Depends(get_current_user)):
    """Manually trigger backlink opportunity search"""
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    # Get user's niches
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]},
        {"_id": 0, "niche": 1}
    ).to_list(100)
    
    niches = list(set([s.get("niche") for s in sites if s.get("niche")]))
    
    if not niches:
        raise HTTPException(status_code=400, detail="No niches configured")
    
    total_found = 0
    
    for niche in niches:
        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage
            
            existing = await db.niche_backlinks.find(
                {"niche": niche, "user_id": user["id"]},
                {"_id": 0, "domain": 1}
            ).to_list(500)
            existing_domains = [b["domain"] for b in existing]
            
            response = await chat(
                api_key=llm_api_key,
                messages=[Message(role="user", content=f"""
                    Find 10 NEW free backlink opportunities for the niche: {niche}
                    
                    Focus on FREE opportunities only:
                    - Free guest posting sites that accept contributions
                    - Blogs with dofollow comments
                    - Free business directories
                    - Resource pages accepting submissions
                    - Forums allowing signature links
                    
                    EXCLUDE these domains: {', '.join(existing_domains[:30])}
                    
                    Return as JSON array:
                    [{{
                        "domain": "example.com",
                        "type": "Guest Post|Blog Comment|Directory|Resource Page|Forum",
                        "da": 40,
                        "pa": 35,
                        "price": 0,
                        "contact_info": "email or contact URL",
                        "category": "specific category"
                    }}]
                """)],
                model="gpt-4o",
                session_id=f"manual-search-{uuid.uuid4()}"
            )
            
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            
            new_backlinks = json.loads(clean_response)
            
            for bl in new_backlinks:
                if bl.get("domain") and bl["domain"] not in existing_domains:
                    backlink_doc = {
                        "id": str(uuid.uuid4()),
                        "user_id": user["id"],
                        "niche": niche,
                        "domain": bl.get("domain", ""),
                        "type": bl.get("type", "Directory"),
                        "da": bl.get("da", 30),
                        "pa": bl.get("pa", 30),
                        "price": 0,
                        "contact_info": bl.get("contact_info", ""),
                        "category": bl.get("category", niche),
                        "auto_discovered": True,
                        "discovered_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.niche_backlinks.insert_one(backlink_doc)
                    total_found += 1
                    
        except Exception as e:
            logging.error(f"Error in manual search for {niche}: {e}")
    
    return {"success": True, "new_opportunities": total_found}

@api_router.get("/backlinks/diagnostic")
async def backlinks_diagnostic(user: dict = Depends(get_current_user)):
    """Diagnostic endpoint to check why backlinks aren't generated for some sites"""
    user_id = user["id"]
    
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "niche": 1, "site_url": 1, "site_name": 1}
    ).to_list(100)
    
    diagnostic = []
    for site in sites:
        site_id = site.get("id")
        site_name = site.get("site_name") or site.get("site_url", "Unknown")
        niche = site.get("niche")
        
        # Check articles
        articles_count = await db.articles.count_documents({"user_id": user_id, "site_id": site_id, "status": "published"})
        
        # Check existing backlinks
        backlinks_count = await db.niche_backlinks.count_documents({"site_id": site_id, "user_id": user_id})
        
        # Check pending outreach emails
        outreach_count = await db.backlink_outreach.count_documents({"site_id": site_id, "user_id": user_id, "status": "pending_approval"})
        
        diagnostic.append({
            "site_name": site_name,
            "site_id": site_id,
            "niche": niche or "LIPSĂ - NU SE VOR GENERA BACKLINKS!",
            "published_articles": articles_count,
            "backlinks_found": backlinks_count,
            "pending_emails": outreach_count,
            "status": "OK" if niche and (articles_count > 0 or outreach_count > 0) else "PROBLEMĂ"
        })
    
    return {"sites": diagnostic, "total_sites": len(sites)}

class SiteSearchRequest(BaseModel):
    site_id: str

@api_router.post("/backlinks/search-opportunities-for-site")
async def search_opportunities_for_single_site(request: SiteSearchRequest, user: dict = Depends(get_current_user)):
    """Search backlinks and generate outreach emails for a SINGLE site only"""
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    user_id = user["id"]
    site_id = request.site_id
    
    # Get the specific site
    site_info = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user_id},
        {"_id": 0, "id": 1, "niche": 1, "site_url": 1, "site_name": 1}
    )
    
    if not site_info:
        raise HTTPException(status_code=404, detail="Site not found")
    
    niche = site_info.get("niche")
    site_name = site_info.get("site_name") or site_info.get("site_url", "Unknown")
    
    if not niche:
        raise HTTPException(status_code=400, detail=f"Site-ul {site_name} nu are nișă definită")
    
    # Get user info for outreach emails
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    user_name = user_doc.get("name", "SEO Team") if user_doc else "SEO Team"
    user_email = user_doc.get("email", "") if user_doc else ""
    
    if user_email == "danpo0446@gmail.com":
        outreach_position = "Administrator"
        outreach_phone = "0721578660"
        outreach_email = user_email
    else:
        user_settings = await db.settings.find_one({"user_id": user_id}, {"_id": 0})
        outreach_position = user_settings.get("outreach_position", "Administrator") if user_settings else "Administrator"
        outreach_phone = user_settings.get("outreach_phone", "") if user_settings else ""
        outreach_email = user_settings.get("outreach_email", user_email) if user_settings else user_email
    
    logging.info(f"[BACKLINKS-SINGLE] Processing site: {site_name}, niche: {niche}")
    
    try:
        # Get existing domains to avoid duplicates
        existing = await db.niche_backlinks.find(
            {"site_id": site_id, "user_id": user_id},
            {"_id": 0, "domain": 1}
        ).to_list(500)
        existing_domains = [b["domain"] for b in existing]
        
        # Search for new opportunities
        response = await chat(
            api_key=llm_api_key,
            messages=[Message(role="user", content=f"""
                Find 10 NEW free backlink opportunities for the niche: {niche}
                
                Focus on FREE opportunities:
                - Free guest posting sites
                - Blogs with dofollow comments
                - Free business directories
                - Resource pages accepting submissions
                - Forums allowing signature links
                
                EXCLUDE: {', '.join(existing_domains[:30])}
                
                Return ONLY a valid JSON array, nothing else. No markdown, no explanation.
                Example format:
                [{{"domain": "example.com", "type": "Guest Post", "da": 40, "pa": 35, "price": 0, "contact_info": "contact@example.com", "category": "parenting"}}]
            """)],
            model="gpt-4o",
            session_id=f"single-site-search-{uuid.uuid4()}"
        )
        
        logging.info(f"[BACKLINKS-SINGLE] LLM response for {site_name}: {response[:200] if response else 'EMPTY'}...")
        
        if not response or not response.strip():
            return {"backlinks_found": 0, "emails_generated": 0, "error": "LLM returned empty response"}
        
        clean_response = response.strip()
        
        # Handle various response formats
        if clean_response.startswith("```"):
            parts = clean_response.split("```")
            if len(parts) >= 2:
                clean_response = parts[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
                clean_response = clean_response.strip()
        
        # Try to find JSON array in response
        if not clean_response.startswith("["):
            start_idx = clean_response.find("[")
            end_idx = clean_response.rfind("]")
            if start_idx != -1 and end_idx != -1:
                clean_response = clean_response[start_idx:end_idx+1]
        
        try:
            new_backlinks = json.loads(clean_response)
        except json.JSONDecodeError as je:
            logging.error(f"[BACKLINKS-SINGLE] JSON parse error: {je}")
            return {"backlinks_found": 0, "emails_generated": 0, "error": f"Invalid JSON from LLM"}
        
        if not isinstance(new_backlinks, list):
            new_backlinks = []
        
        # Get best article for this site
        best_article = await db.articles.find_one(
            {"user_id": user_id, "site_id": site_id, "status": "published"},
            {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "wp_post_url": 1}
        )
        if not best_article:
            best_article = await db.articles.find_one(
                {"user_id": user_id, "status": "published"},
                {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "wp_post_url": 1}
            )
        if not best_article:
            best_article = {
                "id": f"placeholder-{site_id}",
                "title": f"Articole pe {site_name}",
                "wp_post_url": site_info.get("site_url", ""),
                "wordpress_url": site_info.get("site_url", "")
            }
        
        site_backlinks = 0
        site_emails = 0
        
        for bl in new_backlinks:
            if bl.get("domain") and bl["domain"] not in existing_domains:
                backlink_id = str(uuid.uuid4())
                backlink_doc = {
                    "id": backlink_id,
                    "user_id": user_id,
                    "niche": niche,
                    "site_id": site_id,
                    "domain": bl.get("domain", ""),
                    "type": bl.get("type", "Directory"),
                    "da": bl.get("da", 30),
                    "pa": bl.get("pa", 30),
                    "price": 0,
                    "contact_info": bl.get("contact_info", ""),
                    "category": bl.get("category", niche),
                    "auto_discovered": True,
                    "discovered_at": datetime.now(timezone.utc).isoformat()
                }
                await db.niche_backlinks.insert_one(backlink_doc)
                site_backlinks += 1
                existing_domains.append(bl["domain"])
                
                # Generate outreach email
                contact_info = bl.get("contact_info", "")
                try:
                    target_domain = bl.get('domain', '').lower()
                    target_language = "ROMÂNĂ" if target_domain.endswith('.ro') else "ENGLEZĂ (English)"
                    
                    article_url = best_article.get('wp_post_url') or best_article.get('wordpress_url') or site_info.get('site_url', '')
                    
                    email_response = await chat(
                        api_key=llm_api_key,
                        messages=[Message(role="user", content=f"""
                            Generează email profesional de outreach pentru backlink în {target_language}.
                            
                            Expeditor: {user_name}, {outreach_position}
                            Email: {outreach_email}, Tel: {outreach_phone}
                            Website: {site_info.get('site_url', '')}
                            
                            Site țintă: {bl.get('domain')} ({bl.get('type')})
                            
                            Articol de promovat: {best_article.get('title', '')}
                            URL articol: {article_url}
                            
                            Scrie întregul email în {target_language}. Nu folosi placeholdere.
                            Format: {{"subject": "...", "body": "..."}}
                        """)],
                        model="gpt-4o",
                        session_id=f"outreach-single-{uuid.uuid4()}"
                    )
                    
                    clean_email = email_response.strip()
                    if clean_email.startswith("```"):
                        parts = clean_email.split("```")
                        if len(parts) >= 2:
                            clean_email = parts[1]
                            if clean_email.startswith("json"):
                                clean_email = clean_email[4:]
                            clean_email = clean_email.strip()
                    
                    email_data = json.loads(clean_email)
                    
                    outreach_doc = {
                        "id": str(uuid.uuid4()),
                        "user_id": user_id,
                        "backlink_id": backlink_id,
                        "backlink_domain": bl.get("domain", ""),
                        "site_id": site_id,
                        "article_id": best_article.get("id"),
                        "article_title": best_article.get("title", ""),
                        "article_url": article_url,
                        "contact_email": contact_info if "@" in contact_info else f"TBD - check {bl.get('domain', '')}",
                        "email_subject": email_data.get("subject", ""),
                        "email_body": email_data.get("body", ""),
                        "status": "pending_approval",
                        "auto_generated": True,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.backlink_outreach.insert_one(outreach_doc)
                    site_emails += 1
                except Exception as email_err:
                    logging.error(f"[BACKLINKS-SINGLE] Error generating email for {bl.get('domain')}: {email_err}")
        
        logging.info(f"[BACKLINKS-SINGLE] Site {site_name}: {site_backlinks} backlinks saved, {site_emails} emails generated")
        
        return {
            "success": True,
            "site_name": site_name,
            "backlinks_found": site_backlinks,
            "emails_generated": site_emails
        }
        
    except Exception as e:
        logging.error(f"[BACKLINKS-SINGLE] Error for {site_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/backlinks/search-opportunities-with-emails")
async def trigger_full_backlink_search(user: dict = Depends(get_current_user)):
    """Manually trigger backlink search + auto-generate outreach emails for ALL user's sites"""
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        raise HTTPException(status_code=500, detail="LLM not configured")
    
    user_id = user["id"]
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    user_name = user_doc.get("name", "SEO Team") if user_doc else "SEO Team"
    user_email = user_doc.get("email", "") if user_doc else ""
    
    # Get outreach settings
    if user_email == "danpo0446@gmail.com":
        outreach_position = "Administrator"
        outreach_phone = "0721578660"
        outreach_email = user_email
    else:
        user_settings = await db.settings.find_one({"user_id": user_id}, {"_id": 0})
        outreach_position = user_settings.get("outreach_position", "Administrator") if user_settings else "Administrator"
        outreach_phone = user_settings.get("outreach_phone", "") if user_settings else ""
        outreach_email = user_settings.get("outreach_email", user_email) if user_settings else user_email
    
    # Get ALL user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "niche": 1, "site_url": 1, "site_name": 1}
    ).to_list(100)
    
    if not sites:
        raise HTTPException(status_code=400, detail="No sites configured")
    
    total_backlinks = 0
    total_emails = 0
    sites_processed = []
    
    for site_info in sites:
        niche = site_info.get("niche")
        site_id = site_info.get("id")
        site_name = site_info.get("site_name") or site_info.get("site_url", "Unknown")
        
        if not niche:
            logging.warning(f"[BACKLINKS] Site {site_name} skipped - NO NICHE defined!")
            sites_processed.append({
                "site": site_name,
                "niche": None,
                "error": "Nișă nedefinită - configurează nișa în setările site-ului"
            })
            continue
        
        logging.info(f"[BACKLINKS] Processing site: {site_name}, niche: {niche}")
        
        try:
            # Get existing domains to avoid duplicates - PER SITE, not per niche
            existing = await db.niche_backlinks.find(
                {"site_id": site_id, "user_id": user_id},
                {"_id": 0, "domain": 1}
            ).to_list(500)
            existing_domains = [b["domain"] for b in existing]
            
            # Search for new opportunities
            response = await chat(
                api_key=llm_api_key,
                messages=[Message(role="user", content=f"""
                    Find 10 NEW free backlink opportunities for the niche: {niche}
                    
                    Focus on FREE opportunities:
                    - Free guest posting sites
                    - Blogs with dofollow comments
                    - Free business directories
                    - Resource pages accepting submissions
                    - Forums allowing signature links
                    
                    EXCLUDE: {', '.join(existing_domains[:30])}
                    
                    Return ONLY a valid JSON array, nothing else. No markdown, no explanation.
                    Example format:
                    [{{"domain": "example.com", "type": "Guest Post", "da": 40, "pa": 35, "price": 0, "contact_info": "contact@example.com", "category": "parenting"}}]
                """)],
                model="gpt-4o",
                session_id=f"full-search-{uuid.uuid4()}"
            )
            
            logging.info(f"[BACKLINKS] LLM response for {site_name}: {response[:200] if response else 'EMPTY'}...")
            
            if not response or not response.strip():
                logging.error(f"[BACKLINKS] Empty response from LLM for {site_name}")
                sites_processed.append({
                    "site": site_name,
                    "niche": niche,
                    "error": "LLM returned empty response"
                })
                continue
            
            clean_response = response.strip()
            
            # Handle various response formats
            if clean_response.startswith("```"):
                parts = clean_response.split("```")
                if len(parts) >= 2:
                    clean_response = parts[1]
                    if clean_response.startswith("json"):
                        clean_response = clean_response[4:]
                    clean_response = clean_response.strip()
            
            # Try to find JSON array in response
            if not clean_response.startswith("["):
                # Try to extract JSON from text
                start_idx = clean_response.find("[")
                end_idx = clean_response.rfind("]")
                if start_idx != -1 and end_idx != -1:
                    clean_response = clean_response[start_idx:end_idx+1]
            
            try:
                new_backlinks = json.loads(clean_response)
            except json.JSONDecodeError as je:
                logging.error(f"[BACKLINKS] JSON parse error for {site_name}: {je}. Response: {clean_response[:300]}")
                sites_processed.append({
                    "site": site_name,
                    "niche": niche,
                    "error": f"Invalid JSON from LLM: {str(je)}"
                })
                continue
            
            if not isinstance(new_backlinks, list):
                logging.error(f"[BACKLINKS] LLM did not return a list for {site_name}")
                new_backlinks = []
            
            # Get best article for this site
            best_article = await db.articles.find_one(
                {"user_id": user_id, "site_id": site_id, "status": "published"},
                {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "wp_post_url": 1}
            )
            if not best_article:
                # Try any published article from user
                best_article = await db.articles.find_one(
                    {"user_id": user_id, "status": "published"},
                    {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "wp_post_url": 1}
                )
            if not best_article:
                # Create a placeholder article using site homepage
                best_article = {
                    "id": f"placeholder-{site_id}",
                    "title": f"Articole pe {site_name}",
                    "wp_post_url": site_info.get("site_url", ""),
                    "wordpress_url": site_info.get("site_url", "")
                }
                logging.info(f"[BACKLINKS] Site {site_name}: no published articles, using site homepage as placeholder")
            
            site_backlinks = 0
            site_emails = 0
            skipped_no_email = 0
            skipped_no_article = 0
            
            logging.info(f"[BACKLINKS] Site {site_name}: found {len(new_backlinks)} potential backlinks, best_article={best_article is not None}")
            
            for bl in new_backlinks:
                if bl.get("domain") and bl["domain"] not in existing_domains:
                    backlink_id = str(uuid.uuid4())
                    backlink_doc = {
                        "id": backlink_id,
                        "user_id": user_id,
                        "niche": niche,
                        "site_id": site_id,
                        "domain": bl.get("domain", ""),
                        "type": bl.get("type", "Directory"),
                        "da": bl.get("da", 30),
                        "pa": bl.get("pa", 30),
                        "price": 0,
                        "contact_info": bl.get("contact_info", ""),
                        "category": bl.get("category", niche),
                        "auto_discovered": True,
                        "discovered_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.niche_backlinks.insert_one(backlink_doc)
                    site_backlinks += 1
                    existing_domains.append(bl["domain"])
                    
                    # Generate outreach email - now generates even without contact email (will need manual lookup)
                    contact_info = bl.get("contact_info", "")
                    
                    # Generate email for all backlinks
                    try:
                        target_domain = bl.get('domain', '').lower()
                        target_language = "ROMÂNĂ" if target_domain.endswith('.ro') else "ENGLEZĂ (English)"
                        
                        article_url = best_article.get('wp_post_url') or best_article.get('wordpress_url') or site_info.get('site_url', '')
                        
                        email_response = await chat(
                            api_key=llm_api_key,
                            messages=[Message(role="user", content=f"""
                                Generează email profesional de outreach pentru backlink în {target_language}.
                                
                                Expeditor: {user_name}, {outreach_position}
                                Email: {outreach_email}, Tel: {outreach_phone}
                                Website: {site_info.get('site_url', '')}
                                
                                Site țintă: {bl.get('domain')} ({bl.get('type')})
                                
                                Articol de promovat: {best_article.get('title', '')}
                                URL articol: {article_url}
                                
                                Scrie întregul email în {target_language}. Nu folosi placeholdere.
                                Format: {{"subject": "...", "body": "..."}}
                            """)],
                            model="gpt-4o",
                            session_id=f"outreach-gen-{uuid.uuid4()}"
                        )
                        
                        clean_email = email_response.strip()
                        if clean_email.startswith("```"):
                            clean_email = clean_email.split("```")[1]
                            if clean_email.startswith("json"):
                                clean_email = clean_email[4:]
                        
                        email_data = json.loads(clean_email)
                        
                        outreach_doc = {
                            "id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "backlink_id": backlink_id,
                            "backlink_domain": bl.get("domain", ""),
                            "site_id": site_id,
                            "article_id": best_article.get("id"),
                            "article_title": best_article.get("title", ""),
                            "article_url": article_url,
                            "contact_email": contact_info if "@" in contact_info else f"TBD - check {bl.get('domain', '')}",
                            "email_subject": email_data.get("subject", ""),
                            "email_body": email_data.get("body", ""),
                            "status": "pending_approval",
                            "auto_generated": True,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.backlink_outreach.insert_one(outreach_doc)
                        site_emails += 1
                    except Exception as email_err:
                        logging.error(f"Error generating email for {bl.get('domain')}: {email_err}")
            
            logging.info(f"[BACKLINKS] Site {site_name}: {site_backlinks} backlinks saved, {site_emails} emails generated, {skipped_no_article} skipped (no article)")
            
            total_backlinks += site_backlinks
            total_emails += site_emails
            sites_processed.append({
                "site": site_name,
                "niche": niche,
                "backlinks_found": site_backlinks,
                "emails_generated": site_emails,
                "skipped_no_article": skipped_no_article
            })
            
        except Exception as e:
            logging.error(f"Error in full search for {niche}: {e}")
            sites_processed.append({
                "site": site_name,
                "niche": niche,
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_backlinks": total_backlinks,
        "total_emails": total_emails,
        "sites_processed": sites_processed
    }

@api_router.post("/reports/send-monthly")
async def trigger_monthly_report(user: dict = Depends(get_current_user)):
    """Manually trigger monthly SEO report for current user"""
    
    if not RESEND_API_KEY:
        raise HTTPException(status_code=500, detail="Email service not configured")
    
    user_doc = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not user_doc or not user_doc.get("email"):
        raise HTTPException(status_code=400, detail="User email not found")
    
    # ... send report logic (simplified version)
    try:
        sites = await db.wordpress_configs.find(
            {"user_id": user["id"]},
            {"_id": 0, "app_password": 0}
        ).to_list(100)
        
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        
        articles_count = await db.articles.count_documents({
            "user_id": user["id"],
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        })
        
        auto_articles = await db.articles.count_documents({
            "user_id": user["id"],
            "auto_generated": True,
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        })
        
        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #00E676;">📊 Raport SEO - Ultimele 30 zile</h1>
            <p>Articole generate: <strong>{articles_count}</strong></p>
            <p>Articole automate: <strong>{auto_articles}</strong></p>
            <p>Site-uri active: <strong>{len(sites)}</strong></p>
        </div>
        """
        
        resend.Emails.send({
            "from": f"SEO Automation <{SENDER_EMAIL}>",
            "to": [user_doc["email"]],
            "subject": f"📊 Raport SEO - {articles_count} articole generate",
            "html": email_html
        })
        
        return {"success": True, "sent_to": user_doc["email"]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ============ WORDPRESS ROUTES ============

@api_router.post("/wordpress/connect", response_model=WordPressConfigResponse)
async def connect_wordpress(config: WordPressConfig, user: dict = Depends(get_current_user)):
    # Check if site already exists for this user
    existing = await db.wordpress_configs.find_one({
        "user_id": user["id"], 
        "site_url": config.site_url
    })
    if existing:
        raise HTTPException(status_code=400, detail="Site-ul este deja conectat")
    
    config_id = str(uuid.uuid4())
    site_name = config.site_name or config.site_url.replace("https://", "").replace("http://", "").split("/")[0]
    config_doc = {
        "id": config_id,
        "site_url": config.site_url,
        "site_name": site_name,
        "username": config.username,
        "app_password": config.app_password,
        "niche": config.niche,
        "notification_email": config.notification_email,
        "connected": True,
        "user_id": user["id"]
    }
    
    await db.wordpress_configs.insert_one(config_doc)
    
    return WordPressConfigResponse(
        id=config_id,
        site_url=config.site_url,
        site_name=site_name,
        username=config.username,
        connected=True,
        user_id=user["id"],
        niche=config.niche,
        notification_email=config.notification_email
    )

@api_router.get("/wordpress/sites", response_model=List[WordPressConfigResponse])
async def get_wordpress_sites(user: dict = Depends(get_current_user)):
    """Get all WordPress sites for user"""
    configs = await db.wordpress_configs.find({"user_id": user["id"]}, {"_id": 0, "app_password": 0}).to_list(100)
    return [WordPressConfigResponse(**c) for c in configs]

@api_router.get("/wordpress/config", response_model=Optional[WordPressConfigResponse])
async def get_wordpress_config(user: dict = Depends(get_current_user)):
    config = await db.wordpress_configs.find_one({"user_id": user["id"]}, {"_id": 0, "app_password": 0})
    if not config:
        return None
    return WordPressConfigResponse(**config)

@api_router.delete("/wordpress/site/{site_id}")
async def delete_wordpress_site(site_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific WordPress site"""
    result = await db.wordpress_configs.delete_one({"id": site_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"message": "Site deleted"}

@api_router.patch("/wordpress/site/{site_id}")
async def update_wordpress_site(site_id: str, update_data: dict, user: dict = Depends(get_current_user)):
    """Update a WordPress site configuration"""
    # Check if site exists
    existing = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]})
    if not existing:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Only allow updating specific fields
    allowed_fields = ["site_name", "username", "app_password", "niche", "wc_consumer_key", "wc_consumer_secret", "tone", "notification_email", "article_language"]
    update_dict = {k: v for k, v in update_data.items() if k in allowed_fields}
    
    if not update_dict:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$set": update_dict}
    )
    
    return {"message": "Site updated successfully"}

# ===== WOOCOMMERCE INTEGRATION =====

class WooCommerceCredentials(BaseModel):
    consumer_key: str
    consumer_secret: str

@api_router.post("/wordpress/site/{site_id}/woocommerce")
async def save_woocommerce_credentials(site_id: str, credentials: WooCommerceCredentials, user: dict = Depends(get_current_user)):
    """Save WooCommerce API credentials for a site"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$set": {
            "wc_consumer_key": credentials.consumer_key,
            "wc_consumer_secret": credentials.consumer_secret
        }}
    )
    
    return {"message": "WooCommerce credentials saved successfully"}

@api_router.get("/wordpress/site/{site_id}/woocommerce/test")
async def test_woocommerce_connection(site_id: str, user: dict = Depends(get_current_user)):
    """Test WooCommerce API connection and return sample products"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0, "site_url": 1, "wc_consumer_key": 1, "wc_consumer_secret": 1, "site_name": 1}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    if not site.get("wc_consumer_key") or not site.get("wc_consumer_secret"):
        raise HTTPException(status_code=400, detail="WooCommerce credentials not configured for this site")
    
    wc = get_woocommerce_service(
        site.get("site_url"),
        site.get("wc_consumer_key"),
        site.get("wc_consumer_secret")
    )
    
    if not wc:
        raise HTTPException(status_code=500, detail="Failed to create WooCommerce service")
    
    # Test by fetching products
    products = wc.get_products(per_page=5)
    categories = wc.get_categories()
    
    return {
        "success": True,
        "site_name": site.get("site_name"),
        "products_count": len(products),
        "categories_count": len(categories),
        "sample_products": products[:3],
        "categories": categories[:10]
    }

@api_router.get("/wordpress/site/{site_id}/woocommerce/products")
async def get_woocommerce_products(
    site_id: str, 
    limit: int = 20,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user)
):
    """Get products from WooCommerce store"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0, "site_url": 1, "wc_consumer_key": 1, "wc_consumer_secret": 1}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    if not site.get("wc_consumer_key"):
        raise HTTPException(status_code=400, detail="WooCommerce not configured for this site")
    
    wc = get_woocommerce_service(
        site.get("site_url"),
        site.get("wc_consumer_key"),
        site.get("wc_consumer_secret")
    )
    
    products = wc.get_products(per_page=limit, category=category)
    
    return {"products": products, "total": len(products)}

# Mapping of site domains to Romanian niches
SITE_NICHES_ROMANIAN = {
    "seamanshelp": "Cariere maritime, navigație și viața la bord",
    "jobsonsea": "Joburi maritime, recrutare echipaje și cariere offshore",
    "bestbuybabys": "Produse și sfaturi pentru bebeluși, copii și părinți",
    "azurelady": "Modă feminină elegantă și stil",
    "storeforladies": "Lenjerie intimă și îmbrăcăminte feminină",
}

# WooCommerce credentials for e-commerce sites
WOOCOMMERCE_CREDENTIALS = {
    "bestbuybabys": {
        "consumer_key": "ck_29e07f80088cc8c11bcec10eac91d94c9f8e1deb",
        "consumer_secret": "cs_18ff95bf4e5fcabb6f59a89e92c21d138bdb8970"
    },
    "azurelady": {
        "consumer_key": "ck_c257c7d884e00c2fb312f3c4be835271d24771a6",
        "consumer_secret": "cs_833e2e7690210c96d3e963cba86780f460cd3b1d"
    },
    "storeforladies": {
        "consumer_key": "ck_165ba01862983b4f7c83e7651a70a70a976d52ba",
        "consumer_secret": "cs_eb120aed84ede7e92bacc9f227ba53342c3c8f8f"
    }
}

@api_router.post("/wordpress/migrate-niches-romanian")
async def migrate_niches_to_romanian(user: dict = Depends(get_current_user)):
    """Migrate all site niches to Romanian versions"""
    sites = await db.wordpress_configs.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    updated = []
    for site in sites:
        site_url = site.get("site_url", "").lower()
        site_id = site.get("id")
        
        # Find matching Romanian niche
        new_niche = None
        for domain_key, romanian_niche in SITE_NICHES_ROMANIAN.items():
            if domain_key in site_url:
                new_niche = romanian_niche
                break
        
        if new_niche:
            await db.wordpress_configs.update_one(
                {"id": site_id, "user_id": user["id"]},
                {"$set": {"niche": new_niche}}
            )
            updated.append({"site": site.get("site_name", site_url), "new_niche": new_niche})
            logging.info(f"[MIGRATE] Updated niche for {site_url} to: {new_niche}")
    
    return {"message": f"Updated {len(updated)} sites", "updates": updated}

@api_router.post("/wordpress/site/{site_id}/generate-keywords")
async def generate_site_keywords(site_id: str, user: dict = Depends(get_current_user)):
    """Generate SEO keywords automatically for a site based on its niche and sync to main keywords"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
    if not api_key:
        raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
    
    niche = site.get("niche", "general")
    site_name = site.get("site_name", site.get("site_url", ""))
    
    chat = LlmChat(
        api_key=api_key,
        system_message="Ești un expert SEO. Generezi cuvinte cheie relevante în limba ROMÂNĂ."
    ).with_model(model_provider, model_name)
    
    prompt = f"""Generează 20 de cuvinte cheie SEO relevante pentru un site cu:
Nume: {site_name}
Nișă/Descriere: {niche}

Cuvintele cheie trebuie să fie:
- Relevante pentru nișa site-ului
- O combinație de cuvinte cheie scurte și long-tail
- Optimizate pentru căutări Google în România
- În limba română

Returnează EXACT în acest format JSON:
{{"keywords": ["keyword1", "keyword2", "keyword3", ...]}}

Doar JSON, fără explicații:"""

    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    try:
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        data = json.loads(clean_response)
        keywords = data.get("keywords", [])
    except:
        # Fallback keywords based on niche
        keywords = [niche, f"ghid {niche}", f"sfaturi {niche}", f"cele mai bune {niche}", f"{niche} 2026"]
    
    # Save keywords to site config
    await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$set": {"auto_keywords": keywords, "keywords_generated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Sync to main keywords collection
    synced_count = 0
    for kw in keywords:
        # Check if keyword already exists for this site
        existing = await db.keywords.find_one({
            "keyword": kw,
            "user_id": user["id"],
            "site_id": site_id
        })
        
        if not existing:
            keyword_doc = {
                "id": str(uuid.uuid4()),
                "keyword": kw,
                "volume": 1000,  # Default estimated volume
                "difficulty": 50,  # Default difficulty
                "cpc": 1.0,  # Default CPC
                "trend": "stable",
                "user_id": user["id"],
                "niche": niche,
                "site_id": site_id,
                "source": "ai_generated",  # Mark as AI generated
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.keywords.insert_one(keyword_doc)
            synced_count += 1
    
    logging.info(f"[KEYWORDS] Generated and synced {synced_count} new keywords for site {site_id}")
    
    return {"success": True, "keywords": keywords, "count": len(keywords), "synced_to_main": synced_count}

@api_router.get("/wordpress/site/{site_id}/keywords")
async def get_site_keywords(site_id: str, user: dict = Depends(get_current_user)):
    """Get keywords for a site"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]}, 
        {"_id": 0, "auto_keywords": 1, "keywords_generated_at": 1, "site_name": 1}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return {
        "site_name": site.get("site_name"),
        "keywords": site.get("auto_keywords", []),
        "generated_at": site.get("keywords_generated_at")
    }

@api_router.put("/wordpress/site/{site_id}/keywords")
async def update_site_keywords(site_id: str, request: dict, user: dict = Depends(get_current_user)):
    """Update keywords for a site manually and sync to main keywords collection"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    keywords = request.get("keywords", [])
    niche = site.get("niche", "general")
    
    # Save to wordpress_configs
    await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$set": {"auto_keywords": keywords, "keywords_updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Sync to main keywords collection
    synced_count = 0
    for kw in keywords:
        # Check if keyword already exists for this site
        existing = await db.keywords.find_one({
            "keyword": kw,
            "user_id": user["id"],
            "site_id": site_id
        })
        
        if not existing:
            keyword_doc = {
                "id": str(uuid.uuid4()),
                "keyword": kw,
                "volume": 1000,  # Default estimated volume
                "difficulty": 50,  # Default difficulty
                "cpc": 1.0,  # Default CPC
                "trend": "stable",
                "user_id": user["id"],
                "niche": niche,
                "site_id": site_id,
                "source": "site_config",  # Mark as synced from site config
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.keywords.insert_one(keyword_doc)
            synced_count += 1
    
    logging.info(f"[KEYWORDS] Synced {synced_count} new keywords to main collection for site {site_id}")
    
    return {"success": True, "keywords": keywords, "synced_to_main": synced_count}

@api_router.post("/keywords/sync-all-from-sites")
async def sync_all_keywords_from_sites(user: dict = Depends(get_current_user)):
    """Sync all keywords from all WordPress sites to main keywords collection"""
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "niche": 1, "auto_keywords": 1}
    ).to_list(100)
    
    total_synced = 0
    
    for site in sites:
        site_id = site.get("id")
        niche = site.get("niche", "general")
        keywords = site.get("auto_keywords", [])
        
        for kw in keywords:
            # Check if keyword already exists for this site
            existing = await db.keywords.find_one({
                "keyword": kw,
                "user_id": user["id"],
                "site_id": site_id
            })
            
            if not existing:
                keyword_doc = {
                    "id": str(uuid.uuid4()),
                    "keyword": kw,
                    "volume": 1000,
                    "difficulty": 50,
                    "cpc": 1.0,
                    "trend": "stable",
                    "user_id": user["id"],
                    "niche": niche,
                    "site_id": site_id,
                    "source": "bulk_sync",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.keywords.insert_one(keyword_doc)
                total_synced += 1
    
    logging.info(f"[KEYWORDS] Bulk synced {total_synced} keywords from sites to main collection for user {user['id']}")
    
    return {"success": True, "synced_count": total_synced, "sites_processed": len(sites)}

@api_router.post("/wordpress/publish/{article_id}")
async def publish_to_wordpress(article_id: str, site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    # Get specific site or first available
    if site_id:
        config = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]}, {"_id": 0})
    else:
        config = await db.wordpress_configs.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not config:
        raise HTTPException(status_code=400, detail="WordPress not connected")
    
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    import requests
    import base64
    
    try:
        credentials = f"{config['username']}:{config['app_password']}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        
        # Get niche and determine category
        niche = config.get("niche", article.get("niche", "general")).lower()
        categories = NICHE_CATEGORIES.get(niche, NICHE_CATEGORIES["default"])
        
        # Get or create categories in WordPress
        logging.info(f"Getting categories for niche: {niche}")
        category_map = await get_or_create_wp_categories(config, categories)
        logging.info(f"Category map: {category_map}")
        
        # Determine which category to use (rotate based on article count)
        site_article_count = await db.articles.count_documents({
            "site_id": config.get("id"),
            "status": "published"
        })
        selected_category = categories[site_article_count % len(categories)]
        category_id = category_map.get(selected_category)
        logging.info(f"Selected category: {selected_category}, ID: {category_id}")
        
        # Fetch images for article - pass article_id for uniqueness
        keywords = article.get("keywords", [])
        logging.info(f"Fetching images for keywords: {keywords}, niche: {niche}")
        
        # Get user's Pexels key (BYOAK) or use platform key
        pexels_key = await get_user_pexels_key(user["id"], user.get("role") == "admin")
        if not pexels_key:
            pexels_key = PEXELS_API_KEY  # Fallback to platform key for images
        
        images = await fetch_images_for_article(keywords, niche, count=6, article_id=article_id, pexels_key=pexels_key)
        logging.info(f"Fetched {len(images)} images")
        
        # Fetch and upload images
        featured_image_id = None
        content_image_urls = []
        
        if images:
            logging.info(f"Uploading {len(images)} Pexels images to WordPress...")
            
            # Upload featured image (first one)
            featured_id, featured_url = await upload_image_url_to_wp(
                config, 
                images[0]["url"], 
                f"{article['title'][:30].replace(' ', '-')}-featured"
            )
            featured_image_id = featured_id
            logging.info(f"Featured image uploaded, ID: {featured_image_id}")
            
            # Upload content images (rest)
            for i, img in enumerate(images[1:], 1):
                img_id, img_url = await upload_image_url_to_wp(
                    config,
                    img.get("url_medium", img["url"]),
                    f"{article['title'][:20].replace(' ', '-')}-img-{i}"
                )
                if img_url:
                    content_image_urls.append(img_url)
                    logging.info(f"Content image {i} uploaded")
        
        # Insert images into content
        content_with_images = insert_images_into_content(article["content"], images[1:], content_image_urls)
        logging.info(f"Content with {len(content_image_urls)} images inserted")
        
        # Prepare post data
        post_data = {
            "title": article["title"],
            "content": content_with_images,
            "status": "publish"
        }
        
        if category_id:
            post_data["categories"] = [category_id]
        
        if featured_image_id:
            post_data["featured_media"] = featured_image_id
        
        logging.info(f"Publishing to WordPress: {config['site_url']}")
        response = requests.post(
            f"{config['site_url']}/wp-json/wp/v2/posts",
            headers=headers,
            json=post_data,
            timeout=60
        )
        
        wp_post_url = ""
        if response.status_code in [200, 201]:
            wp_data = response.json()
            wp_post_id = wp_data.get("id")
            wp_post_url = wp_data.get("link", "")
            
            await db.articles.update_one(
                {"id": article_id},
                {"$set": {
                    "status": "published",
                    "wp_post_id": wp_post_id,
                    "wp_post_url": wp_post_url,
                    "wp_category": selected_category,
                    "has_images": len(images) > 0,
                    "images_count": len(content_image_urls) + (1 if featured_image_id else 0),
                    "published_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Send email notification if enabled
            settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
            if settings and settings.get("email_notifications", True):
                company_name = settings.get("company_name", "SEO Automation")
                email_html = create_article_published_email(article["title"], wp_post_url, company_name)
                await send_notification_email(
                    user["email"],
                    f"✅ Articol publicat: {article['title']}",
                    email_html
                )
            
            # POST TO SOCIAL MEDIA (Facebook, LinkedIn)
            logging.info(f"[SOCIAL] Starting social media posting for article: {article['title']}")
            try:
                # Update article with wordpress_url for social posting
                article_with_url = {**article, "wordpress_url": wp_post_url, "images": images}
                social_result = await auto_post_article_to_social(db, article_with_url, config, user["id"])
                logging.info(f"[SOCIAL] Social posting result: {social_result}")
            except Exception as social_error:
                logging.error(f"[SOCIAL] Error posting to social media: {social_error}")
            
            return {
                "message": "Article published to WordPress with Pexels images",
                "wp_post_id": wp_post_id,
                "wp_post_url": wp_post_url,
                "category": selected_category,
                "images_added": len(content_image_urls) + (1 if featured_image_id else 0)
            }
        else:
            raise HTTPException(status_code=400, detail=f"WordPress API error: {response.text}")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to WordPress: {str(e)}")

@api_router.delete("/wordpress/disconnect")
async def disconnect_wordpress(user: dict = Depends(get_current_user)):
    await db.wordpress_configs.delete_many({"user_id": user["id"]})
    return {"message": "WordPress disconnected"}

# ============ GOOGLE SEARCH CONSOLE OAUTH ============

def create_gsc_oauth_flow():
    """Create OAuth flow for Google Search Console"""
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        return None
    
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [GOOGLE_REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI
    return flow

@api_router.get("/search-console/auth-url")
async def get_gsc_auth_url(user: dict = Depends(get_current_user)):
    """Get Google Search Console OAuth authorization URL"""
    flow = create_gsc_oauth_flow()
    if not flow:
        raise HTTPException(status_code=400, detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env")
    
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent"
    )
    
    # Store state for verification
    await db.gsc_states.update_one(
        {"user_id": user["id"]},
        {"$set": {"state": state, "created_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    return {"authorization_url": authorization_url, "state": state}

@api_router.get("/search-console/callback")
async def gsc_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Google Search Console OAuth callback"""
    # Find user by state
    state_doc = await db.gsc_states.find_one({"state": state})
    if not state_doc:
        raise HTTPException(status_code=400, detail="Invalid state")
    
    user_id = state_doc["user_id"]
    
    flow = create_gsc_oauth_flow()
    if not flow:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    
    try:
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Store credentials
        await db.gsc_credentials.update_one(
            {"user_id": user_id},
            {"$set": {
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                "connected": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )
        
        # Clean up state
        await db.gsc_states.delete_one({"state": state})
        
        # Redirect to frontend
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard?gsc_connected=true")
    except Exception as e:
        logging.error(f"GSC OAuth error: {str(e)}")
        return RedirectResponse(url=f"{FRONTEND_URL}/dashboard?gsc_error=true")

@api_router.get("/search-console/status")
async def get_gsc_status(user: dict = Depends(get_current_user)):
    """Check if user has connected Google Search Console"""
    creds = await db.gsc_credentials.find_one({"user_id": user["id"]}, {"_id": 0})
    if creds and creds.get("connected"):
        return {"connected": True, "updated_at": creds.get("updated_at")}
    return {"connected": False}

@api_router.delete("/search-console/disconnect")
async def disconnect_gsc(user: dict = Depends(get_current_user)):
    """Disconnect Google Search Console"""
    await db.gsc_credentials.delete_many({"user_id": user["id"]})
    return {"message": "Google Search Console disconnected"}

async def get_gsc_service(user_id: str):
    """Get authenticated Google Search Console service"""
    creds_doc = await db.gsc_credentials.find_one({"user_id": user_id})
    if not creds_doc or not creds_doc.get("access_token"):
        return None
    
    credentials = Credentials(
        token=creds_doc["access_token"],
        refresh_token=creds_doc.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET
    )
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
            # Update stored token
            await db.gsc_credentials.update_one(
                {"user_id": user_id},
                {"$set": {
                    "access_token": credentials.token,
                    "token_expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
        except Exception as e:
            logging.error(f"Token refresh failed: {str(e)}")
            return None
    
    return build("searchconsole", "v1", credentials=credentials)

@api_router.get("/search-console/sites")
async def get_gsc_sites(user: dict = Depends(get_current_user)):
    """Get list of sites from Google Search Console - prioritized by type"""
    service = await get_gsc_service(user["id"])
    if not service:
        raise HTTPException(status_code=400, detail="Google Search Console not connected")
    
    try:
        results = service.sites().list().execute()
        sites = results.get("siteEntry", [])
        
        # Build list with priority:
        # 1. HTTPS without www - most common for comparison
        # 2. HTTPS with www
        # 3. Domain properties (sc-domain:)
        # 4. HTTP
        site_list = []
        for s in sites:
            url = s.get("siteUrl", "")
            priority = 4  # default lowest
            if url.startswith("https://") and "www." not in url:
                priority = 1
            elif url.startswith("https://"):
                priority = 2
            elif url.startswith("sc-domain:"):
                priority = 3
            site_list.append({
                "url": url,
                "permission": s.get("permissionLevel"),
                "priority": priority
            })
        
        # Sort by priority
        site_list.sort(key=lambda x: x["priority"])
        
        # Remove priority field before returning
        for s in site_list:
            del s["priority"]
        
        logging.info(f"[GSC] Returning {len(site_list)} sites, first: {site_list[0]['url'] if site_list else 'none'}")
        
        return {"sites": site_list}
    except Exception as e:
        logging.error(f"GSC sites error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sites: {str(e)}")

@api_router.get("/search-console/stats")
async def get_search_console_stats(user: dict = Depends(get_current_user), site_url: Optional[str] = None, days: int = 28):
    """Get Google Search Console stats - with caching for performance"""
    
    # Skip cache for now to debug data issues
    # TODO: Re-enable cache after data issues are resolved
    
    service = await get_gsc_service(user["id"])
    
    if service and site_url:
        try:
            # GSC has 2-3 day data delay, so don't include the last 3 days
            end_date = datetime.now(timezone.utc).date() - timedelta(days=3)
            start_date = end_date - timedelta(days=days)
            
            logging.info(f"[GSC] Fetching FRESH data for site: {site_url}, period: {start_date} to {end_date}")
            logging.info(f"[GSC] Exact URL being queried: '{site_url}' (length: {len(site_url)})")
            
            # Get overall stats
            overall_response = service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": []
                }
            ).execute()
            
            overall = overall_response.get("rows", [{}])[0] if overall_response.get("rows") else {}
            
            logging.info(f"[GSC] Raw API response for '{site_url}': clicks={overall.get('clicks', 0)}, impressions={overall.get('impressions', 0)}, ctr={overall.get('ctr', 0)}, position={overall.get('position', 0)}")
            logging.info(f"[GSC] Date range requested: {start_date.isoformat()} to {end_date.isoformat()}")
            
            # Get daily traffic data
            daily_response = service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": ["date"],
                    "rowLimit": 500
                }
            ).execute()
            
            daily_traffic = []
            for row in daily_response.get("rows", []):
                if row.get("keys"):
                    daily_traffic.append({
                        "date": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0)
                    })
            
            # Sort by date
            daily_traffic.sort(key=lambda x: x["date"])
            
            # DON'T fill missing days with 0 - GSC data has a 2-3 day delay
            # Just sort the data we have from GSC
            if daily_traffic:
                daily_traffic.sort(key=lambda x: x["date"])
            
            # Get top queries
            queries_response = service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": ["query"],
                    "rowLimit": 10
                }
            ).execute()
            
            top_queries = []
            for row in queries_response.get("rows", []):
                if row.get("keys"):
                    top_queries.append({
                        "query": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0),
                        "ctr": round(row.get("ctr", 0) * 100, 2),
                        "position": round(row.get("position", 0), 1)
                    })
            
            # Get top pages
            pages_response = service.searchanalytics().query(
                siteUrl=site_url,
                body={
                    "startDate": start_date.isoformat(),
                    "endDate": end_date.isoformat(),
                    "dimensions": ["page"],
                    "rowLimit": 10
                }
            ).execute()
            
            top_pages = []
            for row in pages_response.get("rows", []):
                if row.get("keys"):
                    top_pages.append({
                        "page": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": row.get("impressions", 0)
                    })
            
            result_data = {
                "connected": True,
                "site_url": site_url,
                "period_days": days,
                "clicks": overall.get("clicks", 0),
                "impressions": overall.get("impressions", 0),
                "ctr": round(overall.get("ctr", 0) * 100, 2),
                "position": round(overall.get("position", 0), 1),
                "daily_traffic": daily_traffic,
                "top_queries": top_queries,
                "top_pages": top_pages
            }
            
            # Cache disabled for debugging
            # gsc_cache[cache_key] = (result_data, datetime.now(timezone.utc))
            
            return result_data
        except Exception as e:
            logging.error(f"GSC stats error for site {site_url}: {str(e)}")
            logging.exception("Full GSC traceback:")
            # Fall back to mock data
    
    # Mock data when not connected - LOG THIS
    logging.warning(f"[GSC] Returning MOCK data - GSC not connected or error occurred")
    import random
    return {
        "connected": False,
        "clicks": random.randint(1000, 5000),
        "impressions": random.randint(10000, 50000),
        "ctr": round(random.uniform(2.0, 8.0), 2),
        "position": round(random.uniform(5.0, 25.0), 1),
        "daily_traffic": [],
        "top_queries": [
            {"query": "seo tips", "clicks": random.randint(100, 500), "impressions": random.randint(1000, 5000)},
            {"query": "content marketing", "clicks": random.randint(80, 400), "impressions": random.randint(800, 4000)},
            {"query": "keyword research", "clicks": random.randint(60, 300), "impressions": random.randint(600, 3000)},
            {"query": "backlink building", "clicks": random.randint(50, 250), "impressions": random.randint(500, 2500)},
            {"query": "seo automation", "clicks": random.randint(40, 200), "impressions": random.randint(400, 2000)},
        ],
        "top_pages": [
            {"page": "/blog/seo-guide", "clicks": random.randint(200, 800)},
            {"page": "/blog/content-tips", "clicks": random.randint(150, 600)},
            {"page": "/blog/keyword-tools", "clicks": random.randint(100, 400)},
        ]
    }

@api_router.get("/search-console/opportunities")
async def get_gsc_opportunities(user: dict = Depends(get_current_user), site_url: Optional[str] = None):
    """Get GSC optimization opportunities - queries with position 5-20 and CTR < 3%"""
    service = await get_gsc_service(user["id"])
    
    if not service or not site_url:
        return {"opportunities": [], "connected": False}
    
    try:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=28)
        
        # Get queries with detailed metrics
        queries_response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query"],
                "rowLimit": 500
            }
        ).execute()
        
        opportunities = []
        for row in queries_response.get("rows", []):
            if row.get("keys"):
                position = row.get("position", 0)
                ctr = row.get("ctr", 0) * 100
                impressions = row.get("impressions", 0)
                
                # Filter: position 5-20, CTR < 3%, minimum impressions
                if 5 <= position <= 20 and ctr < 3 and impressions >= 10:
                    opportunities.append({
                        "query": row["keys"][0],
                        "clicks": row.get("clicks", 0),
                        "impressions": impressions,
                        "ctr": round(ctr, 2),
                        "position": round(position, 1),
                        "opportunity_score": round((20 - position) * (3 - ctr) * (impressions / 100), 1)
                    })
        
        # Sort by opportunity score
        opportunities.sort(key=lambda x: x["opportunity_score"], reverse=True)
        
        logging.info(f"[GSC] Found {len(opportunities)} optimization opportunities for {site_url}")
        
        return {
            "opportunities": opportunities[:20],  # Top 20
            "connected": True,
            "total_found": len(opportunities)
        }
    except Exception as e:
        logging.error(f"GSC opportunities error: {str(e)}")
        return {"opportunities": [], "connected": False, "error": str(e)}

async def get_gsc_opportunities_for_scoring(user_id: str, site_url: str) -> List[dict]:
    """Get GSC opportunities for use in topic scoring algorithm"""
    service = await get_gsc_service(user_id)
    
    if not service or not site_url:
        return []
    
    try:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=28)
        
        queries_response = service.searchanalytics().query(
            siteUrl=site_url,
            body={
                "startDate": start_date.isoformat(),
                "endDate": end_date.isoformat(),
                "dimensions": ["query"],
                "rowLimit": 200
            }
        ).execute()
        
        opportunities = []
        for row in queries_response.get("rows", []):
            if row.get("keys"):
                position = row.get("position", 0)
                ctr = row.get("ctr", 0) * 100
                
                if 5 <= position <= 20 and ctr < 3:
                    opportunities.append(row["keys"][0].lower())
        
        return opportunities
    except Exception as e:
        logging.warning(f"[GSC] Could not fetch opportunities for scoring: {e}")
        return []

# ============ SOCIAL MEDIA INTEGRATION ROUTES ============

from config import FACEBOOK_APP_ID, FACEBOOK_APP_SECRET, LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, APP_URL
# Facebook OAuth endpoints
@api_router.get("/social/facebook/auth-url/{site_id}")
async def get_facebook_auth_url(site_id: str, user: dict = Depends(get_current_user)):
    """Get Facebook OAuth URL for a specific site"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    page_id = get_facebook_page_id(site_url)
    page_name = get_facebook_page_name(site_url)
    
    if not page_id:
        raise HTTPException(status_code=400, detail="No Facebook page configured for this site")
    
    # Store state for callback
    state = f"{user['id']}:{site_id}"
    
    redirect_uri = APP_URL + '/api/social/facebook/callback'
    
    # Facebook OAuth URL with page permissions
    auth_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?"
        f"client_id={FACEBOOK_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope=pages_manage_posts,pages_read_engagement,pages_show_list"
    )
    
    return {
        "authorization_url": auth_url,
        "page_id": page_id,
        "page_name": page_name
    }

@api_router.get("/social/facebook/callback")
async def facebook_oauth_callback(code: str = Query(...), state: str = Query(...)):
    """Handle Facebook OAuth callback"""
    try:
        user_id, site_id = state.split(":")
    except:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    redirect_uri = APP_URL + '/api/social/facebook/callback'
    
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.get(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                params={
                    "client_id": FACEBOOK_APP_ID,
                    "client_secret": FACEBOOK_APP_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code
                }
            )
            
            if token_response.status_code != 200:
                logging.error(f"Facebook token error: {token_response.text}")
                return RedirectResponse(url=f"/wordpress?error=facebook_token_error")
            
            token_data = token_response.json()
            user_access_token = token_data.get("access_token")
            
            # Get long-lived token
            long_token_response = await client.get(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": FACEBOOK_APP_ID,
                    "client_secret": FACEBOOK_APP_SECRET,
                    "fb_exchange_token": user_access_token
                }
            )
            
            if long_token_response.status_code == 200:
                long_token_data = long_token_response.json()
                user_access_token = long_token_data.get("access_token", user_access_token)
            
            # Get page access token
            pages_response = await client.get(
                "https://graph.facebook.com/v19.0/me/accounts",
                params={"access_token": user_access_token}
            )
            
            if pages_response.status_code != 200:
                logging.error(f"Facebook pages error: {pages_response.text}")
                return RedirectResponse(url=f"/wordpress?error=facebook_pages_error")
            
            pages_data = pages_response.json()
            pages = pages_data.get("data", [])
            
            # Find the page for this site
            site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user_id})
            if not site:
                return RedirectResponse(url=f"/wordpress?error=site_not_found")
            
            site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            expected_page_id = get_facebook_page_id(site_url)
            
            page_token = None
            for page in pages:
                if page.get("id") == expected_page_id:
                    page_token = page.get("access_token")
                    break
            
            if not page_token:
                # Use first available page token if exact match not found
                if pages:
                    page_token = pages[0].get("access_token")
                    logging.warning(f"Using first available page token for site {site_id}")
            
            if page_token:
                # Save page token to site config
                await db.wordpress_configs.update_one(
                    {"id": site_id, "user_id": user_id},
                    {"$set": {
                        "facebook_page_token": page_token,
                        "facebook_connected": True,
                        "facebook_connected_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logging.info(f"Facebook connected for site {site_id}")
                
                # ALSO save tokens for ALL other sites of this user that have matching pages
                logging.info(f"[FACEBOOK] Found {len(pages)} pages in user account. Checking all sites...")
                
                # Get ALL sites for this user
                all_user_sites = await db.wordpress_configs.find(
                    {"user_id": user_id},
                    {"_id": 0, "id": 1, "site_url": 1, "site_name": 1}
                ).to_list(100)
                
                logging.info(f"[FACEBOOK] User has {len(all_user_sites)} sites configured")
                
                for page in pages:
                    page_id = page.get("id")
                    page_access_token = page.get("access_token")
                    page_name = page.get("name", "")
                    
                    if not page_id or not page_access_token:
                        continue
                    
                    logging.info(f"[FACEBOOK] Processing page: {page_name} (ID: {page_id})")
                    
                    # Find which site URL this page belongs to by checking FACEBOOK_PAGES mapping
                    for site_domain, fb_info in FACEBOOK_PAGES.items():
                        if fb_info.get("page_id") == page_id:
                            logging.info(f"[FACEBOOK] Page {page_name} matches domain {site_domain}")
                            
                            # Find the site with this domain
                            for user_site in all_user_sites:
                                user_site_url = user_site.get("site_url", "").lower()
                                # Check if domain is in site URL
                                if site_domain.lower() in user_site_url:
                                    target_site_id = user_site.get("id")
                                    if target_site_id != site_id:  # Don't update the current site again
                                        await db.wordpress_configs.update_one(
                                            {"id": target_site_id, "user_id": user_id},
                                            {"$set": {
                                                "facebook_page_token": page_access_token,
                                                "facebook_connected": True,
                                                "facebook_connected_at": datetime.now(timezone.utc).isoformat()
                                            }}
                                        )
                                        logging.info(f"[FACEBOOK] ✓ Connected page '{page_name}' to site {user_site.get('site_name', target_site_id)}")
                                    break
                
                return RedirectResponse(url=f"/wordpress?success=facebook_connected")
            else:
                return RedirectResponse(url=f"/wordpress?error=no_page_access")
            
    except Exception as e:
        logging.error(f"Facebook callback error: {str(e)}")
        return RedirectResponse(url=f"/wordpress?error=facebook_error")

@api_router.get("/social/linkedin/auth-url/{site_id}")
async def get_linkedin_auth_url(site_id: str, user: dict = Depends(get_current_user)):
    """Get LinkedIn OAuth URL for a specific site (only for seamanshelp)"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    
    if "seamanshelp" not in site_url:
        raise HTTPException(status_code=400, detail="LinkedIn is only configured for seamanshelp.com")
    
    state = f"{user['id']}:{site_id}"
    redirect_uri = APP_URL + '/api/social/linkedin/callback'
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization?"
        f"response_type=code"
        f"&client_id={LINKEDIN_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&scope=openid%20profile%20w_member_social"
    )
    
    return {"authorization_url": auth_url}

@api_router.get("/social/linkedin/callback")
async def linkedin_oauth_callback(
    code: str = Query(None), 
    state: str = Query(None),
    error: str = Query(None),
    error_description: str = Query(None)
):
    """Handle LinkedIn OAuth callback - now uses personal profile posting"""
    # Handle errors from LinkedIn
    if error:
        logging.error(f"LinkedIn OAuth error: {error} - {error_description}")
        return RedirectResponse(url=f"/wordpress?error=linkedin_{error}")
    
    if not code or not state:
        return RedirectResponse(url=f"/wordpress?error=linkedin_missing_params")
    
    try:
        user_id, site_id = state.split(":")
    except:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    redirect_uri = APP_URL + '/api/social/linkedin/callback'
    
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for access token
            token_response = await client.post(
                "https://www.linkedin.com/oauth/v2/accessToken",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": LINKEDIN_CLIENT_ID,
                    "client_secret": LINKEDIN_CLIENT_SECRET
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if token_response.status_code != 200:
                logging.error(f"LinkedIn token error: {token_response.text}")
                return RedirectResponse(url=f"/wordpress?error=linkedin_token_error")
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            # Get user's personal profile info (using openid userinfo)
            userinfo_response = await client.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={
                    "Authorization": f"Bearer {access_token}"
                }
            )
            
            person_id = None
            person_name = None
            if userinfo_response.status_code == 200:
                userinfo = userinfo_response.json()
                person_id = userinfo.get("sub")  # LinkedIn user ID (person URN suffix)
                person_name = userinfo.get("name", "")
                logging.info(f"LinkedIn user info: {person_id}, {person_name}")
            else:
                logging.error(f"LinkedIn userinfo error: {userinfo_response.text}")
                return RedirectResponse(url=f"/wordpress?error=linkedin_userinfo_error")
            
            if not person_id:
                logging.error("LinkedIn: Could not get person ID")
                return RedirectResponse(url=f"/wordpress?error=linkedin_no_person_id")
            
            # Save token to site config (personal profile posting)
            await db.wordpress_configs.update_one(
                {"id": site_id, "user_id": user_id},
                {"$set": {
                    "linkedin_access_token": access_token,
                    "linkedin_person_id": person_id,
                    "linkedin_person_name": person_name,
                    "linkedin_connected": True,
                    "linkedin_connected_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            logging.info(f"LinkedIn connected for site {site_id}, person_id: {person_id}")
            return RedirectResponse(url=f"/wordpress?success=linkedin_connected")
        
    except Exception as e:
        logging.error(f"LinkedIn callback error: {str(e)}")
        return RedirectResponse(url=f"/wordpress?error=linkedin_error")

@api_router.get("/social/status/{site_id}")
async def get_social_status(site_id: str, user: dict = Depends(get_current_user)):
    """Get social media connection status for a site"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0, "facebook_connected": 1, "facebook_connected_at": 1, 
         "linkedin_connected": 1, "linkedin_connected_at": 1, "linkedin_person_name": 1, "site_url": 1}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    
    return {
        "facebook": {
            "connected": site.get("facebook_connected", False),
            "connected_at": site.get("facebook_connected_at"),
            "page_name": get_facebook_page_name(site_url),
            "page_id": get_facebook_page_id(site_url)
        },
        "linkedin": {
            "connected": site.get("linkedin_connected", False),
            "connected_at": site.get("linkedin_connected_at"),
            "person_name": site.get("linkedin_person_name", ""),
            "available": "seamanshelp" in site_url,
            "type": "personal"  # Now using personal profile
        }
    }

@api_router.delete("/social/facebook/disconnect/{site_id}")
async def disconnect_facebook(site_id: str, user: dict = Depends(get_current_user)):
    """Disconnect Facebook from a site"""
    result = await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$unset": {"facebook_page_token": "", "facebook_connected": "", "facebook_connected_at": ""}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return {"message": "Facebook disconnected"}

@api_router.post("/social/facebook/test-post/{site_id}")
async def test_facebook_post(site_id: str, user: dict = Depends(get_current_user)):
    """Test Facebook posting for a site"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/").lower()
    page_id = get_facebook_page_id(site_url)
    fb_token = site.get("facebook_page_token")
    
    logging.info(f"[FB_TEST] Site URL: {site_url}")
    logging.info(f"[FB_TEST] Page ID from mapping: {page_id}")
    logging.info(f"[FB_TEST] Token exists: {fb_token is not None and len(str(fb_token)) > 10}")
    
    if not page_id:
        return {
            "success": False,
            "error": f"Site {site_url} nu este configurat în FACEBOOK_PAGES. Site-uri disponibile: {list(FACEBOOK_PAGES.keys())}"
        }
    
    if not fb_token:
        return {
            "success": False,
            "error": "Nu există token Facebook salvat. Reconectează Facebook."
        }
    
    # Try a test post
    try:
        result = await post_to_facebook_page(
            page_access_token=fb_token,
            page_id=page_id,
            message="🔧 Test de postare automată - va fi șters\n\nAcesta este un test pentru verificarea conexiunii Facebook.",
            link=site.get("site_url", "https://example.com"),
            image_url=None
        )
        
        return {
            "success": result.get("success", False),
            "post_id": result.get("post_id"),
            "error": result.get("error"),
            "page_id": page_id,
            "site_url": site_url
        }
    except Exception as e:
        logging.error(f"[FB_TEST] Exception: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }

@api_router.delete("/social/linkedin/disconnect/{site_id}")
async def disconnect_linkedin(site_id: str, user: dict = Depends(get_current_user)):
    """Disconnect LinkedIn from a site"""
    result = await db.wordpress_configs.update_one(
        {"id": site_id, "user_id": user["id"]},
        {"$unset": {
            "linkedin_access_token": "", 
            "linkedin_person_id": "", 
            "linkedin_person_name": "",
            "linkedin_company_id": "",  # Legacy cleanup
            "linkedin_connected": "", 
            "linkedin_connected_at": ""
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Site not found")
    
    return {"message": "LinkedIn disconnected"}

@api_router.get("/social/posts/{site_id}")
async def get_social_posts(site_id: str, user: dict = Depends(get_current_user)):
    """Get social media posting history for a site"""
    posts = await db.social_posts.find(
        {"site_id": site_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(50).to_list(50)
    
    return posts

# ============ SETTINGS ROUTES ============

@api_router.get("/settings", response_model=SettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "company_name": "My SEO Agency",
            "logo_url": "",
            "primary_color": "#00E676",
            "email_notifications": True
        }
        await db.settings.insert_one(settings)
    return SettingsResponse(**settings)

@api_router.patch("/settings", response_model=SettingsResponse)
async def update_settings(updates: SettingsUpdate, user: dict = Depends(get_current_user)):
    update_data = updates.model_dump(exclude_unset=True)
    if update_data:
        await db.settings.update_one(
            {"user_id": user["id"]},
            {"$set": update_data}
        )
    settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return SettingsResponse(**settings)

# ============ ARTICLE TEMPLATES ============

@api_router.post("/templates", response_model=ArticleTemplateResponse)
async def create_template(template: ArticleTemplateCreate, user: dict = Depends(get_current_user)):
    """Create a new article template"""
    template_id = str(uuid.uuid4())
    template_doc = {
        "id": template_id,
        "name": template.name,
        "description": template.description,
        "default_tone": template.default_tone,
        "default_length": template.default_length,
        "prompt_template": template.prompt_template,
        "keywords_hint": template.keywords_hint or "",
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.article_templates.insert_one(template_doc)
    return ArticleTemplateResponse(**template_doc)

@api_router.get("/templates", response_model=List[ArticleTemplateResponse])
async def get_templates(user: dict = Depends(get_current_user)):
    """Get all article templates for user"""
    templates = await db.article_templates.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Add default templates if user has none
    if not templates:
        default_templates = [
            {
                "id": str(uuid.uuid4()),
                "name": "Ghid Complet",
                "description": "Articol detaliat tip ghid pas cu pas",
                "default_tone": "professional",
                "default_length": "long",
                "prompt_template": "Scrie un ghid complet și detaliat despre {topic}. Include: introducere, pași clari, exemple practice, sfaturi pro, și o concluzie cu call-to-action.",
                "keywords_hint": "ghid, tutorial, cum să, pași",
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Listicle (Top X)",
                "description": "Articol în format listă cu puncte",
                "default_tone": "casual",
                "default_length": "medium",
                "prompt_template": "Scrie un articol în format listă despre {topic}. Include minim 7-10 puncte, fiecare cu titlu și descriere detaliată. Adaugă introducere captivantă și concluzie.",
                "keywords_hint": "top, cele mai bune, listă, recomandări",
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Comparație Produse",
                "description": "Articol comparativ între opțiuni",
                "default_tone": "authoritative",
                "default_length": "long",
                "prompt_template": "Scrie o comparație detaliată despre {topic}. Include: criterii de evaluare, avantaje și dezavantaje pentru fiecare opțiune, tabel comparativ, și recomandare finală.",
                "keywords_hint": "vs, comparație, care e mai bun, diferențe",
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "How-To Rapid",
                "description": "Tutorial scurt și la obiect",
                "default_tone": "friendly",
                "default_length": "short",
                "prompt_template": "Scrie un tutorial scurt și practic despre {topic}. Mergi direct la subiect cu pași simpli și clari. Include sfaturi rapide la final.",
                "keywords_hint": "cum să, rapid, simplu, ușor",
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Recenzie Expert",
                "description": "Review detaliat cu analiză",
                "default_tone": "authoritative",
                "default_length": "medium",
                "prompt_template": "Scrie o recenzie expertă despre {topic}. Include: prezentare generală, caracteristici cheie, pro și contra, pentru cine e potrivit, verdict final cu scor.",
                "keywords_hint": "recenzie, review, părere, experiență",
                "user_id": user["id"],
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        ]
        await db.article_templates.insert_many(default_templates)
        templates = default_templates
    
    return [ArticleTemplateResponse(**t) for t in templates]

@api_router.get("/templates/{template_id}", response_model=ArticleTemplateResponse)
async def get_template(template_id: str, user: dict = Depends(get_current_user)):
    """Get a specific template"""
    template = await db.article_templates.find_one({"id": template_id, "user_id": user["id"]}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return ArticleTemplateResponse(**template)

@api_router.delete("/templates/{template_id}")
async def delete_template(template_id: str, user: dict = Depends(get_current_user)):
    """Delete a template"""
    result = await db.article_templates.delete_one({"id": template_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted"}

@api_router.post("/articles/generate-from-template", response_model=ArticleResponse)
async def generate_article_from_template(
    template_id: str,
    topic: str,
    keywords: List[str],
    niche: str,
    user: dict = Depends(get_current_user)
):
    """Generate article using a template"""
    template = await db.article_templates.find_one({"id": template_id, "user_id": user["id"]}, {"_id": 0})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        api_key, model_provider, model_name = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
        if not api_key:
            raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
        
        # Build prompt from template
        custom_prompt = template["prompt_template"].replace("{topic}", topic)
        
        chat = LlmChat(
            api_key=api_key,
            system_message="""You are an expert SEO content writer. Generate high-quality, SEO-optimized articles in clean HTML format.
            Use proper HTML tags: <h2>, <h3> for headings, <p> for paragraphs, <ul>/<li> for lists, <strong> for emphasis.
            Do NOT use markdown. Output clean HTML only."""
        ).with_model(model_provider, model_name)
        
        length_words = {"short": 500, "medium": 1000, "long": 2000}
        target_words = length_words.get(template["default_length"], 1000)
        
        prompt = f"""{custom_prompt}

Specificații:
- Cuvinte-cheie țintă: {', '.join(keywords)}
- Nișă: {niche}
- Ton: {template['default_tone']}
- Lungime: aproximativ {target_words} cuvinte

IMPORTANT: Scrie în format HTML curat:
- <h2> și <h3> pentru headings
- <p> pentru paragrafe
- <ul> și <li> pentru liste
- <strong> pentru text bold
- NU folosi markdown (fără #, *, **, etc.)

Include:
- Headings <h2> și <h3> relevante
- Cuvintele-cheie integrate natural
- Meta description la final într-un tag <p>

Scrie articolul HTML acum:"""

        user_message = UserMessage(text=prompt)
        content = await chat.send_message(user_message)
        
        word_count = len(content.split())
        seo_score = min(95, 70 + len(keywords) * 5)
        
        # Create title from topic
        title = topic if len(topic) > 10 else f"Ghid Complet: {topic}"
        
        article_id = str(uuid.uuid4())
        article_doc = {
            "id": article_id,
            "title": title,
            "content": content,
            "keywords": keywords,
            "niche": niche,
            "status": "draft",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user["id"],
            "seo_score": seo_score,
            "word_count": word_count,
            "template_id": template_id
        }
        await db.articles.insert_one(article_doc)
        
        return ArticleResponse(**article_doc)
    except Exception as e:
        logging.error(f"Template article generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate article: {str(e)}")

# ============ AUTOMATION SYSTEM ============

# Categories for diverse article topics
NICHE_CATEGORIES = {
    "maritime": ["Cariere Maritime", "Certificări Navale", "Ghiduri Navigație", "Știri Industrie", "Sfaturi Seafareri", "Companii Shipping", "Echipament Naval", "Reglementări IMO", "Viața la Bord", "Portul și Transportul Maritim"],
    "real estate": ["Investiții Imobiliare", "Ghiduri Cumpărători", "Piața Imobiliară", "Sfaturi Vânzare", "Renovări", "Finanțare", "Legislație", "Tendințe"],
    "fitness": ["Antrenamente", "Nutriție", "Suplimente", "Pierdere Greutate", "Muscle Building", "Yoga", "Cardio", "Recuperare"],
    "tech": ["Software", "Hardware", "AI & ML", "Cybersecurity", "Cloud", "Programare", "Gadgets", "Tendințe Tech"],
    "baby": ["Produse Bebeluși", "Sfaturi Părinți", "Îngrijire Copii", "Jucării Educative", "Siguranță Copii", "Nutriție Copii", "Dezvoltare Copii", "Ghiduri Parenting", "Camera Bebelușului", "Sănătatea Copilului"],
    "babies": ["Produse Bebeluși", "Sfaturi Părinți", "Îngrijire Copii", "Jucării Educative", "Siguranță Copii", "Nutriție Copii", "Dezvoltare Copii", "Ghiduri Parenting", "Camera Bebelușului", "Sănătatea Copilului"],
    "parenting": ["Produse Bebeluși", "Sfaturi Părinți", "Îngrijire Copii", "Jucării Educative", "Siguranță Copii", "Nutriție Copii", "Dezvoltare Copii", "Ghiduri Parenting"],
    "fashion": ["Tendințe Modă", "Stil Elegant", "Accesorii Fashion", "Ghiduri Vestimentare", "Outfit-uri Sezoniere", "Moda Casual", "Fashion Vintage", "Îmbrăcăminte de Ocazie", "Stil Personal", "Tendințe Culori"],
    "women": ["Beauty & Îngrijire", "Lifestyle Feminin", "Sănătate Feminină", "Tendințe Modă", "Accesorii", "Cosmetice", "Îngrijire Personală", "Stil de Viață", "Relații", "Carieră pentru Femei"],
    "ladies": ["Beauty & Îngrijire", "Lifestyle Feminin", "Sănătate Feminină", "Tendințe Modă", "Accesorii", "Cosmetice", "Îngrijire Personală", "Stil de Viață", "Relații", "Carieră pentru Femei"],
    "default": ["Ghiduri Complete", "Sfaturi & Trucuri", "Tendințe Industrie", "Studii de Caz", "Best Practices", "FAQ", "Comparații", "Review-uri"]
}

# Normalize niche names to Romanian
NICHE_TRANSLATIONS = {
    "baby products": "produse pentru bebeluși",
    "baby": "bebeluși și copii",
    "babies": "bebeluși și copii",
    "parenting": "parenting și familie",
    "fashion": "modă și stil",
    "women fashion": "modă feminină",
    "ladies fashion": "modă pentru femei",
    "maritime": "industria maritimă",
    "seafarer": "cariere maritime",
    "shipping": "transport maritim",
    "real estate": "imobiliare",
    "fitness": "fitness și sănătate",
    "tech": "tehnologie",
    "health": "sănătate",
    "beauty": "frumusețe și îngrijire",
    # Specific site niches
    "early childhood education": "educație timpurie și dezvoltarea copiilor",
    "child development": "dezvoltarea copiilor",
    "maritime job": "joburi și cariere maritime",
    "crewing": "recrutare echipaje nave",
    "offshore": "industria offshore",
    "lenjerie": "lenjerie și modă feminină",
    "intimate": "lenjerie intimă",
}

def normalize_niche_to_romanian(niche: str) -> str:
    """Convert English niche names to Romanian for content generation"""
    if not niche:
        return "general"
    niche_lower = niche.lower().strip()
    
    # Direct translation
    if niche_lower in NICHE_TRANSLATIONS:
        return NICHE_TRANSLATIONS[niche_lower]
    
    # Check if contains key English terms and translate
    translated_parts = []
    for eng, ro in NICHE_TRANSLATIONS.items():
        if eng in niche_lower:
            translated_parts.append(ro)
    
    if translated_parts:
        # Return unique translations joined
        return ", ".join(list(dict.fromkeys(translated_parts))[:2])
    
    # If niche already contains Romanian characters, return as-is
    romanian_chars = ['ă', 'â', 'î', 'ș', 'ț', 'Ă', 'Â', 'Î', 'Ș', 'Ț']
    if any(char in niche for char in romanian_chars):
        return niche
    
    return niche  # Return original if no translation found

# ============ IMAGE FUNCTIONS (Pexels - Free) ============

async def fetch_images_for_article(keywords: List[str], niche: str, count: int = 6, article_id: str = "", pexels_key: str = None) -> List[dict]:
    """Fetch free professional images from Pexels - LARGE SIZE, UNIQUE per article"""
    import random
    images = []
    used_photo_ids = set()
    
    # Use provided key or fallback to platform key
    api_key = pexels_key or PEXELS_API_KEY
    if not api_key:
        logging.warning("[IMAGES] No Pexels API key available")
        return images
    
    # Normalize niche - extract key words from long descriptions
    niche_lower = niche.lower()
    detected_niche = "default"
    
    # Detect niche from keywords in description
    niche_keywords = {
        "maritime": ["maritime", "seafarer", "seaman", "ship", "sailor", "vessel", "nautical", "stcw", "shipping", "cargo", "jobsonsea", "jobs on sea", "marin", "navigatie"],
        "baby": ["baby", "infant", "child", "toddler", "newborn", "copii", "bebelus", "bestbuybaby", "best buy baby", "bebe"],
        "fashion": ["fashion", "moda", "clothing", "îmbrăcăminte", "style", "haine", "azurelady", "azure", "eleganta", "rochie"],
        "women": ["women", "ladies", "feminin", "damă", "lenjerie", "feminină", "femeie", "doamne", "storeforladies", "store for ladies"],
        "jobs": ["career", "employment", "hiring", "recruit", "angajare", "cariera"],
        "ecommerce": ["shop", "store", "ecommerce", "retail", "product", "magazin"],
        "tech": ["tech", "software", "digital", "programming"],
        "fitness": ["fitness", "gym", "workout", "exercise"],
        "travel": ["travel", "tourism", "vacation"],
        "food": ["food", "cooking", "recipe", "restaurant"],
        "health": ["health", "medical", "wellness"],
        "beauty": ["beauty", "cosmetic", "skincare", "frumusete"],
        "education": ["education", "training", "learning", "school"],
        "finance": ["finance", "banking", "investment"],
        "real-estate": ["real estate", "property", "imobiliare", "apartment"]
    }
    
    for niche_name, keywords_list in niche_keywords.items():
        for kw in keywords_list:
            if kw in niche_lower:
                detected_niche = niche_name
                break
        if detected_niche != "default":
            break
    
    logging.info(f"[IMAGES] Detected niche '{detected_niche}' from '{niche[:50]}...'")
    
    # Map niche to better search terms - more variety
    niche_search_map = {
        "baby": ["happy baby nursery", "newborn infant care", "baby room colorful", "mother baby love", "cute baby portrait", "baby toys playing", "baby products safe", "infant sleeping peaceful"],
        "babies": ["baby infant newborn", "nursery baby cute", "infant care products", "baby sleeping peaceful", "mother holding baby", "baby first steps"],
        "parenting": ["family baby mother", "parent child bonding", "family happy home", "mother father baby", "family outdoor fun", "parents playing children"],
        "maritime": ["cargo ship ocean view", "sailor working deck professional", "navigation equipment modern", "container vessel sea", "maritime officer uniform", "ship engine room", "seafarer life ocean", "port harbor ships", "captain helm steering", "cruise ship deck"],
        "seamans": ["cargo ship ocean view", "sailor working deck", "navigation equipment bridge", "maritime career professional", "ship captain helm", "seafarer life ocean", "merchant navy", "vessel bridge equipment"],
        "shipping": ["cargo ship ocean", "container port crane", "logistics warehouse", "freight transport international", "shipping industry global", "maritime logistics port"],
        "ladies": ["elegant woman fashion portrait", "female lifestyle beauty", "women accessories luxury", "feminine cosmetics beauty", "woman shopping boutique", "stylish woman dress", "fashion model elegant", "beautiful woman portrait"],
        "fashion": ["elegant woman dress runway", "stylish clothing outfit", "fashion model professional", "trendy shoes handbag", "woman elegant style", "feminine fashion portrait", "designer clothes luxury", "boutique fashion store"],
        "women": ["elegant woman fashion portrait", "female lifestyle beauty", "women accessories luxury", "feminine cosmetics beauty", "woman shopping boutique", "stylish woman dress", "beautiful woman portrait", "woman elegant dress"],
        "ecommerce": ["online shopping cart", "product photography studio", "retail store display", "customer shopping experience", "delivery package box"],
        "real estate": ["house property home", "modern apartment interior", "luxury villa garden", "real estate agent", "home office workspace"],
        "fitness": ["gym workout exercise", "fitness training healthy", "yoga meditation wellness", "running outdoor sport", "healthy nutrition food"],
        "tech": ["technology computer", "programming developer", "digital innovation", "tech startup office", "software coding screen"],
        "jobs": ["professional office work", "career success interview", "business meeting team", "workplace productivity", "job recruitment hiring"],
        "default": ["professional business modern", "modern lifestyle quality", "quality product photography"]
    }
    
    # Get multiple search term options for variety
    niche_terms = niche_search_map.get(detected_niche, niche_search_map.get("default", [detected_niche]))
    if isinstance(niche_terms, str):
        niche_terms = [niche_terms]
    
    # Get previously used photo IDs for this site to avoid repetition
    global_used_ids = set()
    try:
        # Fetch recently used image IDs from the database (last 30 days)
        recent_articles = await db.articles.find(
            {"created_at": {"$gte": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()}},
            {"images": 1, "_id": 0}
        ).to_list(100)
        
        for article in recent_articles:
            for img in article.get("images", []):
                if img.get("photo_id"):
                    global_used_ids.add(img["photo_id"])
        
        logging.info(f"[IMAGES] Found {len(global_used_ids)} recently used photos to avoid")
    except Exception as e:
        logging.warning(f"Could not fetch used images: {e}")
    
    # Combine local and global used IDs
    all_used_ids = used_photo_ids.union(global_used_ids)
    
    # Randomize order based on article_id for uniqueness
    random.seed(hash(article_id + str(datetime.now().timestamp())))
    random.shuffle(niche_terms)
    
    # Combine niche terms with keywords for diverse searches
    search_terms = niche_terms[:2] + [kw for kw in keywords[:3] if kw]
    random.shuffle(search_terms)
    
    # Random page offset to get different images each time (1-10 for more variety)
    page_offset = random.randint(1, 10)
    
    async with httpx.AsyncClient() as client:
        for term in search_terms:
            if len(images) >= count:
                break
            try:
                # Clean search term
                clean_term = term.replace("-", " ").strip()
                logging.info(f"Pexels searching: {clean_term} (page {page_offset})")
                
                response = await client.get(
                    "https://api.pexels.com/v1/search",
                    headers={"Authorization": api_key},
                    params={
                        "query": clean_term, 
                        "per_page": 30,  # Get more results for variety
                        "page": page_offset,  # Random page for unique images
                        "orientation": "landscape",
                        "size": "large"  # Request large size
                    },
                    timeout=15
                )
                if response.status_code == 200:
                    data = response.json()
                    photos = data.get("photos", [])
                    random.shuffle(photos)  # Shuffle for variety
                    logging.info(f"Pexels found {data.get('total_results', 0)} results for '{clean_term}'")
                    
                    for photo in photos:
                        photo_id = photo.get("id")
                        # Skip if already used this photo (locally or globally)
                        if photo_id in all_used_ids:
                            continue
                        all_used_ids.add(photo_id)
                        used_photo_ids.add(photo_id)
                        
                        if len(images) < count:
                            images.append({
                                "url": photo["src"]["large2x"],  # 1880px - LARGEST
                                "url_large": photo["src"]["large"],  # 1200px
                                "url_medium": photo["src"]["medium"],  # 800px
                                "thumb": photo["src"]["small"],
                                "alt": photo.get("alt") or term.title(),
                                "photographer": photo.get("photographer", "Pexels"),
                                "source": "Pexels",
                                "photo_id": photo_id
                            })
                else:
                    logging.warning(f"Pexels API returned {response.status_code} for '{clean_term}'")
            except Exception as e:
                logging.warning(f"Pexels API error for '{term}': {str(e)}")
    
    logging.info(f"Fetched {len(images)} images from Pexels")
    return images

async def upload_image_url_to_wp(config: dict, image_url: str, filename: str) -> tuple:
    """Download image from URL and upload to WordPress"""
    import requests
    import base64 as b64
    import unicodedata
    
    # Sanitize filename - remove Romanian special characters
    def sanitize_filename(name):
        # Replace Romanian characters
        replacements = {
            'ă': 'a', 'â': 'a', 'î': 'i', 'ș': 's', 'ț': 't',
            'Ă': 'A', 'Â': 'A', 'Î': 'I', 'Ș': 'S', 'Ț': 'T'
        }
        for ro, en in replacements.items():
            name = name.replace(ro, en)
        # Remove any other non-ASCII characters
        name = unicodedata.normalize('NFKD', name).encode('ASCII', 'ignore').decode('ASCII')
        # Replace spaces and special chars with dash
        name = re.sub(r'[^a-zA-Z0-9-]', '-', name)
        name = re.sub(r'-+', '-', name)  # Multiple dashes to single
        return name.strip('-')[:50]
    
    clean_filename = sanitize_filename(filename)
    
    try:
        # Download image
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url, timeout=30)
            if img_response.status_code != 200:
                logging.error(f"Failed to download image: {img_response.status_code}")
                return None, None
            image_data = img_response.content
        
        # Upload to WordPress
        credentials = f"{config['username']}:{config['app_password']}"
        token = b64.b64encode(credentials.encode()).decode()
        
        response = requests.post(
            f"{config['site_url']}/wp-json/wp/v2/media",
            headers={
                "Authorization": f"Basic {token}",
                "Content-Disposition": f'attachment; filename="{clean_filename}.jpg"',
                "Content-Type": "image/jpeg"
            },
            data=image_data,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            media_data = response.json()
            logging.info(f"Image uploaded successfully: {clean_filename}")
            return media_data.get("id"), media_data.get("source_url")
        else:
            logging.error(f"WordPress upload failed: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        logging.error(f"WordPress image upload error: {str(e)}")
    
    return None, None

def insert_images_into_content(content: str, images: List[dict], uploaded_urls: List[str]) -> str:
    """Insert uploaded image URLs into article content - improved to always insert images"""
    if not images or not uploaded_urls:
        logging.warning("[IMAGES] No images or URLs to insert")
        return content
    
    logging.info(f"[IMAGES] Attempting to insert {len(uploaded_urls)} images into content")
    
    # Find all h2 tags to insert images after sections
    h2_pattern = r'(<h2[^>]*>.*?</h2>)'
    h2_matches = list(re.finditer(h2_pattern, content, re.IGNORECASE | re.DOTALL))
    
    # Also find h3 tags as backup
    h3_pattern = r'(<h3[^>]*>.*?</h3>)'
    h3_matches = list(re.finditer(h3_pattern, content, re.IGNORECASE | re.DOTALL))
    
    # Find paragraph tags for fallback insertion
    p_pattern = r'(</p>)'
    p_matches = list(re.finditer(p_pattern, content, re.IGNORECASE))
    
    insert_positions = []
    
    # Try h2 first
    if len(h2_matches) >= 2:
        for i, match in enumerate(h2_matches[1:], 1):
            next_p = content.find('</p>', match.end())
            if next_p != -1 and i <= len(uploaded_urls):
                insert_positions.append((next_p + 4, i - 1))
    # Try h3 if not enough h2
    elif len(h3_matches) >= 2:
        for i, match in enumerate(h3_matches[1:], 1):
            next_p = content.find('</p>', match.end())
            if next_p != -1 and i <= len(uploaded_urls):
                insert_positions.append((next_p + 4, i - 1))
    # Fallback: insert after every 3rd paragraph
    elif len(p_matches) >= 4:
        for i, match in enumerate(p_matches):
            if (i + 1) % 3 == 0 and (i // 3) < len(uploaded_urls):
                insert_positions.append((match.end(), i // 3))
    
    if not insert_positions:
        logging.warning("[IMAGES] No suitable positions found for image insertion")
        # Last resort: insert at the middle of content
        if uploaded_urls:
            middle_pos = len(content) // 2
            # Find nearest </p> tag
            nearest_p = content.find('</p>', middle_pos)
            if nearest_p != -1:
                insert_positions.append((nearest_p + 4, 0))
    
    logging.info(f"[IMAGES] Found {len(insert_positions)} positions for image insertion")
    
    # Insert images from end to start to preserve positions
    for pos, img_idx in reversed(insert_positions):
        if img_idx < len(uploaded_urls) and img_idx < len(images):
            img_url = uploaded_urls[img_idx]
            img = images[img_idx]
            img_html = f'''
<figure style="margin: 30px 0; text-align: center;">
  <img src="{img_url}" alt="{img['alt']}" style="max-width: 100%; width: 100%; height: auto; border-radius: 8px;" loading="lazy">
  <figcaption style="font-size: 12px; color: #666; margin-top: 8px;">Foto: {img['photographer']} / {img['source']}</figcaption>
</figure>
'''
            content = content[:pos] + img_html + content[pos:]
            logging.info(f"[IMAGES] Inserted image {img_idx + 1} at position {pos}")
    
    return content

# ============ WORDPRESS CATEGORY FUNCTIONS ============

async def get_or_create_wp_categories(config: dict, categories: List[str]) -> dict:
    """Get or create WordPress categories and return mapping"""
    import requests
    import base64
    
    credentials = f"{config['username']}:{config['app_password']}"
    token = base64.b64encode(credentials.encode()).decode()
    headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
    
    category_map = {}
    
    try:
        # Get existing categories
        response = requests.get(
            f"{config['site_url']}/wp-json/wp/v2/categories",
            headers=headers,
            params={"per_page": 100},
            timeout=15
        )
        
        if response.status_code == 200:
            existing = {cat["name"].lower(): cat["id"] for cat in response.json()}
            
            for cat_name in categories:
                cat_lower = cat_name.lower()
                if cat_lower in existing:
                    category_map[cat_name] = existing[cat_lower]
                else:
                    # Create new category
                    create_resp = requests.post(
                        f"{config['site_url']}/wp-json/wp/v2/categories",
                        headers=headers,
                        json={"name": cat_name},
                        timeout=15
                    )
                    if create_resp.status_code in [200, 201]:
                        category_map[cat_name] = create_resp.json()["id"]
    except Exception as e:
        logging.error(f"WordPress categories error: {str(e)}")
    
    return category_map

async def upload_featured_image_to_wp(config: dict, image_url: str, title: str) -> Optional[int]:
    """Download image and upload to WordPress as featured image"""
    import requests
    import base64
    
    try:
        # Download image
        async with httpx.AsyncClient() as client:
            img_response = await client.get(image_url, timeout=30)
            if img_response.status_code != 200:
                return None
            image_data = img_response.content
        
        # Upload to WordPress
        credentials = f"{config['username']}:{config['app_password']}"
        token = base64.b64encode(credentials.encode()).decode()
        
        filename = f"{title[:30].replace(' ', '-').lower()}-featured.jpg"
        
        response = requests.post(
            f"{config['site_url']}/wp-json/wp/v2/media",
            headers={
                "Authorization": f"Basic {token}",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "image/jpeg"
            },
            data=image_data,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            return response.json().get("id")
    except Exception as e:
        logging.error(f"Failed to upload featured image: {str(e)}")
    
    return None

async def generate_keywords_for_topic(api_key: str, niche: str, category: str) -> tuple:
    """Generate keywords and article title for a specific niche and category"""
    chat = LlmChat(
        api_key=api_key,
        session_id=f"keywords-auto-{uuid.uuid4()}",
        system_message="Ești un expert SEO. Generezi titluri și keywords în limba ROMÂNĂ. NU folosești NICIODATĂ placeholder-uri precum [Nume], [Platformă], [Anul], etc."
    ).with_model("gemini", "gemini-2.0-flash")
    
    current_year = datetime.now().year
    
    prompt = f"""Generează un titlu de articol SEO și 5 keywords pentru:
Nișă: {niche}
Categorie: {category}
Anul curent: {current_year}

REGULI IMPORTANTE:
1. Titlul trebuie să fie COMPLET și CONCRET - fără placeholder-uri precum [Nume], [Platformă], [Oraș], [Anul] etc.
2. Folosește nume reale, exemple concrete, sau formulări generale care nu necesită completare
3. Dacă ai nevoie de un an, folosește {current_year}
4. Titlul trebuie să fie gata de publicare, fără modificări ulterioare

Returnează EXACT în acest format JSON:
{{"title": "Titlul complet și concret aici", "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]}}

Titlul trebuie să fie captivant, specific și optimizat SEO.
Keywords trebuie să fie relevante pentru titlu și nișă.
Scrie în ROMÂNĂ.
Doar JSON, fără alte explicații:"""

    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    try:
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        data = json.loads(clean_response)
        title = data.get("title", f"Ghid {category} - {niche}")
        
        # Extra safety: remove any remaining placeholders
        placeholder_pattern = r'\[.*?\]'
        if re.search(placeholder_pattern, title):
            title = re.sub(placeholder_pattern, '', title).strip()
            title = re.sub(r'\s+', ' ', title)  # Clean multiple spaces
        
        return title, data.get("keywords", [niche, category])
    except:
        return f"Ghid Complet: {category} în {niche}", [niche, category, "ghid", "sfaturi", str(current_year)]


async def generate_keywords_for_topic_from_keywords(api_key: str, niche: str, category: str, site_keywords: List[str]) -> tuple:
    """Generate article title based on site's auto-generated keywords for diversity"""
    chat = LlmChat(
        api_key=api_key,
        session_id=f"keywords-from-site-{uuid.uuid4()}",
        system_message="Ești un expert SEO. Generezi titluri captivante bazate pe cuvinte cheie specifice. Scrii în limba ROMÂNĂ."
    ).with_model("gemini", "gemini-2.0-flash")
    
    current_year = datetime.now().year
    keywords_str = ", ".join(site_keywords)
    
    prompt = f"""Generează un titlu de articol SEO CAPTIVANT bazat pe aceste cuvinte cheie:

CUVINTE CHEIE DE FOLOSIT: {keywords_str}
NIȘĂ: {niche}
CATEGORIE: {category}
AN CURENT: {current_year}

REGULI:
1. Titlul TREBUIE să includă cel puțin unul din cuvintele cheie date
2. Titlul trebuie să fie COMPLET - fără placeholder-uri [Nume], [An], etc.
3. Titlul trebuie să fie specific și captivant pentru cititori
4. Scrie în limba ROMÂNĂ
5. Titlul trebuie să fie diferit de articolele generice despre nișă

Exemple de titluri bune (NU le copia, doar inspiră-te):
- "Cum să Obții Certificarea STCW în România: Ghid Pas cu Pas 2026"
- "Top 10 Produse pentru Camera Bebelușului care Merită Investiția"
- "Tendințe Modă Primăvară 2026: Ce Piese Nu Trebuie să Lipsească"

Returnează EXACT în format JSON:
{{"title": "Titlul tău aici", "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]}}

Doar JSON:"""

    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    try:
        clean_response = response.strip()
        if clean_response.startswith("```"):
            clean_response = clean_response.split("```")[1]
            if clean_response.startswith("json"):
                clean_response = clean_response[4:]
        data = json.loads(clean_response)
        title = data.get("title", f"Ghid: {site_keywords[0]} - {category}")
        
        # Safety: remove placeholders
        placeholder_pattern = r'\[.*?\]'
        if re.search(placeholder_pattern, title):
            title = re.sub(placeholder_pattern, '', title).strip()
            title = re.sub(r'\s+', ' ', title)
        
        # Merge returned keywords with site keywords
        returned_keywords = data.get("keywords", [])
        final_keywords = list(set(site_keywords + returned_keywords))[:8]
        
        logging.info(f"[AUTOMATION] Generated title from site keywords: {title}")
        return title, final_keywords
    except Exception as e:
        logging.warning(f"[AUTOMATION] Failed to generate from keywords: {e}")
        return f"Ghid Complet: {site_keywords[0]} în {niche}", site_keywords + [niche, category]


async def auto_publish_to_wordpress(article_id: str, site_id: str, user_id: str):
    """Internal function to auto-publish article to WordPress"""
    import requests
    import base64
    
    try:
        # Get site config
        config = await db.wordpress_configs.find_one({"id": site_id, "user_id": user_id}, {"_id": 0})
        if not config:
            logging.error(f"WordPress config not found for site {site_id}")
            return {"success": False, "error": "Site not found"}
        
        # Get article
        article = await db.articles.find_one({"id": article_id, "user_id": user_id}, {"_id": 0})
        if not article:
            logging.error(f"Article not found: {article_id}")
            return {"success": False, "error": "Article not found"}
        
        credentials = f"{config['username']}:{config['app_password']}"
        token = base64.b64encode(credentials.encode()).decode()
        headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}
        
        # Get niche and categories
        niche = config.get("niche", article.get("niche", "general")).lower()
        categories = NICHE_CATEGORIES.get(niche, NICHE_CATEGORIES["default"])
        category_map = await get_or_create_wp_categories(config, categories)
        
        site_article_count = await db.articles.count_documents({"site_id": site_id, "status": "published"})
        selected_category = categories[site_article_count % len(categories)]
        category_id = category_map.get(selected_category)
        
        # Try to fetch and upload images, but don't fail if images fail
        featured_image_id = None
        content_with_images = article["content"]
        
        # IMPORTANT: Clean content again to ensure no markdown and correct year
        content_with_images = clean_html_content(content_with_images)
        
        try:
            keywords = article.get("keywords", [])
            images = await fetch_images_for_article(keywords, niche, count=6, article_id=article_id)
            
            content_image_urls = []
            
            if images:
                # Try to upload featured image
                try:
                    featured_id, featured_url = await upload_image_url_to_wp(
                        config, images[0]["url"], f"{article['title'][:30].replace(' ', '-')}-featured"
                    )
                    featured_image_id = featured_id
                except Exception as img_err:
                    logging.warning(f"Failed to upload featured image: {img_err}")
                
                # Try to upload content images
                for i, img in enumerate(images[1:4], 1):  # Max 3 content images
                    try:
                        img_id, img_url = await upload_image_url_to_wp(
                            config, img.get("url_medium", img["url"]), f"{article['title'][:20].replace(' ', '-')}-img-{i}"
                        )
                        if img_url:
                            content_image_urls.append(img_url)
                    except Exception as img_err:
                        logging.warning(f"Failed to upload content image {i}: {img_err}")
                
                if content_image_urls:
                    content_with_images = insert_images_into_content(article["content"], images[1:], content_image_urls)
        except Exception as img_error:
            logging.warning(f"Image processing failed, publishing without images: {img_error}")
        
        # Prepare post data
        post_data = {
            "title": article["title"],
            "content": content_with_images,
            "status": "publish"
        }
        
        if category_id:
            post_data["categories"] = [category_id]
        if featured_image_id:
            post_data["featured_media"] = featured_image_id
        
        # Publish to WordPress
        response = requests.post(
            f"{config['site_url']}/wp-json/wp/v2/posts",
            headers=headers,
            json=post_data,
            timeout=60
        )
        
        if response.status_code in [200, 201]:
            wp_data = response.json()
            post_url = wp_data.get("link", "")
            logging.info(f"Successfully published article to WordPress: {post_url}")
            
            # AUTO-INDEX the new article
            try:
                from services.indexing import auto_index_new_article
                site_url = config.get("site_url", "")
                if post_url and site_url:
                    indexing_result = await auto_index_new_article(
                        article_url=post_url,
                        site_url=site_url,
                        wp_config=config
                    )
                    logging.info(f"[INDEXING] Auto-indexed article: {indexing_result.get('total_success', 0)} services successful")
            except Exception as idx_err:
                logging.warning(f"[INDEXING] Auto-indexing failed (article still published): {idx_err}")
            
            # AUTO-POST to Social Media (Facebook/LinkedIn)
            try:
                # Update article with wordpress_url for social posting
                await db.articles.update_one(
                    {"id": article_id},
                    {"$set": {"wordpress_url": post_url}}
                )
                article["wordpress_url"] = post_url
                
                social_result = await auto_post_article_to_social(db, article, config, user_id)
                fb_success = social_result.get("facebook", {}).get("success", False) if social_result.get("facebook") else False
                li_success = social_result.get("linkedin", {}).get("success", False) if social_result.get("linkedin") else False
                logging.info(f"[SOCIAL] Auto-posted to social media - Facebook: {fb_success}, LinkedIn: {li_success}")
            except Exception as social_err:
                logging.warning(f"[SOCIAL] Auto-posting to social media failed: {social_err}")
            
            return {
                "success": True,
                "post_id": wp_data.get("id"),
                "post_url": post_url
            }
        else:
            logging.error(f"WordPress API error: {response.status_code} - {response.text}")
            return {"success": False, "error": response.text}
            
    except Exception as e:
        logging.error(f"Auto-publish error: {str(e)}")
        return {"success": False, "error": str(e)}

async def generate_automated_article(site: dict, user_id: str, send_email: bool = True):
    """Generate an article automatically for a site
    
    Args:
        site: WordPress site configuration
        user_id: User ID
        send_email: Whether to send email notification (default True, set False to avoid duplicates)
    """
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        logging.error(f"[AUTOMATION] No LLM API key for automation - site: {site.get('site_name', 'Unknown')}")
        return None
    
    niche = site.get("niche", "general").lower()
    niche_romanian = normalize_niche_to_romanian(niche)
    site_id = site.get("id")
    site_name = site.get("site_name", site.get("site_url", "Site"))
    notification_email = site.get("notification_email", "")
    site_url = site.get("site_url", "").lower()
    
    # ALL articles in Romanian - focusing on Romania market
    article_language = "ro"
    lang_name = "ROMÂNĂ"
    lang_instructions = "Scrie DOAR în limba ROMÂNĂ"
    continue_text = "Continuă articolul. Adaugă încă 4-5 secțiuni noi cu <h2>."
    
    logging.info(f"[AUTOMATION] Starting article generation for site: {site_name} (ID: {site_id}) - Language: {article_language}, Niche: {niche_romanian}")
    
    # ===== ALTERNARE TIPURI ARTICOLE PE ZILE =====
    # Luni=0, Marți=1, Miercuri=2, Joi=3, Vineri=4, Sâmbătă=5, Duminică=6
    day_of_week = datetime.now(ROMANIA_TZ).weekday()
    
    ARTICLE_TYPES_BY_DAY = {
        0: {"type": "review", "prefix": "Review:", "instruction": "Scrie un REVIEW detaliat despre un produs sau serviciu din nișă. Include pro/contra, rating, comparații."},
        1: {"type": "ghid", "prefix": "Ghid Complet:", "instruction": "Scrie un GHID COMPLET pas cu pas. Include instrucțiuni detaliate, sfaturi practice, exemple."},
        2: {"type": "top", "prefix": "Top", "instruction": "Scrie un articol de tip TOP/LISTE (ex: Top 10, Cele mai bune). Include descrieri pentru fiecare element."},
        3: {"type": "comparatie", "prefix": "Comparație:", "instruction": "Scrie o COMPARAȚIE detaliată între 2-3 produse/opțiuni. Include tabele, pro/contra pentru fiecare."},
        4: {"type": "sfaturi", "prefix": "Sfaturi:", "instruction": "Scrie un articol cu SFATURI și TRUCURI practice. Include exemple concrete și soluții."},
        5: {"type": "noutati", "prefix": "Noutăți:", "instruction": "Scrie despre NOUTĂȚI și TENDINȚE actuale în nișă. Menționează anul curent."},
        6: {"type": "general", "prefix": "", "instruction": "Scrie un articol informativ complet despre subiect."}
    }
    
    article_type_config = ARTICLE_TYPES_BY_DAY.get(day_of_week, ARTICLE_TYPES_BY_DAY[6])
    article_type = article_type_config["type"]
    article_prefix = article_type_config["prefix"]
    article_instruction = article_type_config["instruction"]
    
    logging.info(f"[AUTOMATION] Day {day_of_week} - Article type: {article_type} (prefix: '{article_prefix}')")
    
    # Get categories for this niche
    categories = NICHE_CATEGORIES.get(niche, NICHE_CATEGORIES["default"])
    
    # Select category based on recently used topics for better diversity
    # Get last 10 articles to avoid repeating recent topics
    recent_articles = await db.articles.find(
        {"site_id": site_id},
        {"_id": 0, "category": 1, "title": 1, "keywords": 1, "created_at": 1}
    ).sort("created_at", -1).limit(30).to_list(30)
    
    recent_categories = [art.get("category", "") for art in recent_articles]
    
    # ===== COOLDOWN 30 ZILE - Evită repetarea subiectelor =====
    from datetime import timedelta
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get titles and keywords from last 30 days
    recent_titles = []
    recent_keywords_used = []
    for art in recent_articles:
        created = art.get("created_at", "")
        if isinstance(created, str):
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if created_dt > thirty_days_ago:
                    recent_titles.append(art.get("title", "").lower())
                    recent_keywords_used.extend(art.get("keywords", []))
            except:
                pass
    
    # Keywords used too recently (cooldown)
    keyword_cooldown = list(set(recent_keywords_used))
    logging.info(f"[AUTOMATION] Cooldown: {len(keyword_cooldown)} keywords used in last 30 days")
    
    # Find categories not used recently
    import random
    available_categories = [cat for cat in categories if cat not in recent_categories[:3]]
    if not available_categories:
        available_categories = categories
    
    # Random selection for more diversity
    category = random.choice(available_categories)
    logging.info(f"[AUTOMATION] Selected category '{category}' (avoided recent: {recent_categories[:3]})")
    
    # Try to get topic ideas from previous business analyses
    topic_from_analysis = None
    try:
        # Get the most recent analysis for this site URL
        site_domain = site_url.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
        recent_analysis = await db.business_analyses.find_one(
            {"user_id": user_id, "url": {"$regex": site_domain, "$options": "i"}},
            {"_id": 0, "analysis": 1, "recommendations": 1}
        )
        
        if recent_analysis:
            # Extract topic suggestions from analysis
            analysis_text = recent_analysis.get("analysis", "")
            
            # Use AI to extract article ideas from analysis
            extract_chat = LlmChat(
                api_key=api_key,
                session_id=f"extract-ideas-{uuid.uuid4()}",
                system_message="Ești un expert SEO. Extragi idei de articole din analize."
            ).with_model("gemini", "gemini-2.0-flash")
            
            extract_prompt = f"""Din următoarea analiză SEO, extrage O SINGURĂ idee concretă pentru un articol nou.
Analiza: {analysis_text[:2000]}

Returnează DOAR un JSON cu formatul:
{{"topic": "Titlul/tema articolului sugerată", "keywords": ["keyword1", "keyword2", "keyword3"]}}

Doar JSON, fără explicații:"""
            
            extract_msg = UserMessage(text=extract_prompt)
            extract_response = await extract_chat.send_message(extract_msg)
            
            try:
                clean_resp = extract_response.strip()
                if clean_resp.startswith("```"):
                    clean_resp = clean_resp.split("```")[1]
                    if clean_resp.startswith("json"):
                        clean_resp = clean_resp[4:]
                idea_data = json.loads(clean_resp)
                if idea_data.get("topic"):
                    topic_from_analysis = idea_data
                    logging.info(f"[AUTOMATION] Using topic from analysis: {topic_from_analysis['topic']}")
            except:
                pass
    except Exception as e:
        logging.warning(f"[AUTOMATION] Could not extract ideas from analysis: {e}")
    
    # Get site's saved keywords to incorporate in article
    site_keywords = site.get("auto_keywords", [])
    if site_keywords:
        logging.info(f"[AUTOMATION] Using {len(site_keywords)} saved keywords for site")
    
    # ===== GOOGLE TRENDS INTEGRATION =====
    trending_keywords = []
    trending_topic_ideas = []
    try:
        logging.info(f"[AUTOMATION] Fetching Google Trends for niche: {niche_romanian}")
        trends_data = get_trending_topics_for_niche(niche_romanian)
        
        if trends_data:
            trending_keywords = trends_data.get("related_queries", [])[:10]
            trending_topic_ideas = trends_data.get("topic_ideas", [])[:10]
            
            if trending_keywords:
                logging.info(f"[AUTOMATION] Found {len(trending_keywords)} trending keywords: {trending_keywords[:5]}")
            if trending_topic_ideas:
                logging.info(f"[AUTOMATION] Found {len(trending_topic_ideas)} topic ideas from trends")
    except Exception as trends_err:
        logging.warning(f"[AUTOMATION] Google Trends error (continuing without): {trends_err}")
    
    # ===== GSC OPPORTUNITIES - queries cu poziție 5-20, CTR < 3% =====
    gsc_opportunities = []
    try:
        gsc_opportunities = await get_gsc_opportunities_for_scoring(user_id, site_url)
        if gsc_opportunities:
            logging.info(f"[AUTOMATION] Found {len(gsc_opportunities)} GSC opportunities for scoring")
    except Exception as gsc_err:
        logging.warning(f"[AUTOMATION] GSC opportunities error (continuing without): {gsc_err}")
    
    # ===== TOPICS LOG - 90 day semantic cooldown =====
    topics_in_long_cooldown = []
    try:
        topics_in_long_cooldown = await get_topics_in_cooldown(site_id, days=90)
        logging.info(f"[AUTOMATION] {len(topics_in_long_cooldown)} topics in 90-day cooldown")
    except Exception as topics_err:
        logging.warning(f"[AUTOMATION] Topics log error: {topics_err}")
    
    # ===== SISTEM SCORING SUBIECTE =====
    # Scorează și filtrează topicurile bazat pe:
    # 1. Trending score (din Google Trends) - 40 pts
    # 2. GSC Opportunity (poziție 5-20, CTR < 3%) - 15 pts
    # 3. Product available in catalog - 20 pts (handled separately)
    # 4. Cooldown 30 zile - penalizare -30 pts
    # 5. Semantic similarity 90 zile - penalizare -20 pts
    
    def score_topic(topic, trending_list, cooldown_list, recent_titles_list, gsc_opps, long_cooldown):
        """Score a topic idea (higher = better) - based on strategy document"""
        score = 50  # Base score
        topic_lower = topic.lower()
        
        # +40 if in trending (normalized from trends volume)
        if any(topic_lower in t.lower() or t.lower() in topic_lower for t in trending_list):
            score += 40
        
        # +15 if matches GSC opportunity (position 5-20, low CTR)
        if any(topic_lower in opp or opp in topic_lower for opp in gsc_opps):
            score += 15
            logging.debug(f"[SCORING] Topic '{topic}' matches GSC opportunity +15")
        
        # -30 if similar to recent title (30-day cooldown)
        for recent_title in recent_titles_list:
            if topic_lower in recent_title or recent_title in topic_lower:
                score -= 30
                break
        
        # -20 if semantically similar to 90-day topics
        topic_words = set(topic_lower.split())
        for old_topic in long_cooldown:
            old_words = set(old_topic.split())
            if len(topic_words & old_words) >= 2:  # 2+ common words = similar
                score -= 20
                break
        
        # -10 per keyword used recently
        for word in topic_words:
            if len(word) > 4 and word in [k.lower() for k in cooldown_list]:
                score -= 10
        
        return max(0, score)
    
    logging.info(f"[AUTOMATION] Site {site_name}: Generating article in category '{category}' (niche: {niche_romanian})")
    
    # Generate keywords and title - use site keywords to influence topic selection
    if topic_from_analysis:
        title = topic_from_analysis["topic"]
        keywords = topic_from_analysis.get("keywords", [niche_romanian, category])
    elif trending_topic_ideas and len(trending_topic_ideas) > 0:
        # Score trending topics and pick the best one
        scored_topics = [(t, score_topic(t, trending_keywords, keyword_cooldown, recent_titles, gsc_opportunities, topics_in_long_cooldown)) 
                         for t in trending_topic_ideas[:10]]
        scored_topics.sort(key=lambda x: x[1], reverse=True)
        
        # Pick from top 3 scored topics
        best_topics = [t[0] for t in scored_topics[:3] if t[1] > 20]
        if best_topics:
            selected_trend = random.choice(best_topics)
        else:
            selected_trend = random.choice(trending_topic_ideas[:5])
        
        logging.info(f"[AUTOMATION] Using scored trending topic: {selected_trend} (scores: {scored_topics[:3]})")
        
        # Combine trending topic with niche keywords
        combined_keywords = trending_keywords[:5] if trending_keywords else []
        title, keywords = await generate_keywords_for_topic_from_keywords(
            api_key, niche_romanian, category, [selected_trend] + combined_keywords[:3]
        )
    elif site_keywords and len(site_keywords) >= 3:
        # Filter out keywords in cooldown
        available_site_keywords = [k for k in site_keywords if k.lower() not in [c.lower() for c in keyword_cooldown]]
        if len(available_site_keywords) < 3:
            available_site_keywords = site_keywords  # Fallback if too few
        
        # Pick 2-3 random keywords from available
        selected_keywords = random.sample(available_site_keywords, min(3, len(available_site_keywords)))
        logging.info(f"[AUTOMATION] Using site keywords (after cooldown filter): {selected_keywords}")
        
        # Generate title based on selected keywords
        title, keywords = await generate_keywords_for_topic_from_keywords(
            api_key, niche_romanian, category, selected_keywords
        )
    else:
        title, keywords = await generate_keywords_for_topic(api_key, niche_romanian, category)
    
    # Merge with trending keywords for better SEO
    if trending_keywords:
        keywords = list(set(keywords + trending_keywords[:5]))
        logging.info(f"[AUTOMATION] Added trending keywords to article")
    
    # Merge with site's saved keywords (add 3-5 from saved keywords for SEO)
    if site_keywords:
        import random
        extra_keywords = random.sample(site_keywords, min(5, len(site_keywords)))
        keywords = list(set(keywords + extra_keywords))
        logging.info(f"[AUTOMATION] Final keywords: {keywords}")
    
    # Generate article content
    target_words = 1000  # Medium length
    # CRITICAL: Force current year - NEVER use 2024 or 2025
    current_year = 2026
    
    # Build keywords string for prompt
    all_keywords_str = ', '.join(keywords)
    site_keywords_str = ', '.join(site_keywords[:10]) if site_keywords else ''
    trending_keywords_str = ', '.join(trending_keywords[:8]) if trending_keywords else ''
    
    # ===== WOOCOMMERCE INTEGRATION FOR E-COMMERCE SITES =====
    products_for_article = []
    products_section = ""
    
    # Check if site has WooCommerce credentials
    wc_consumer_key = site.get("wc_consumer_key")
    wc_consumer_secret = site.get("wc_consumer_secret")
    
    if wc_consumer_key and wc_consumer_secret:
        logging.info(f"[AUTOMATION] Site {site_name}: Fetching WooCommerce products for article...")
        try:
            wc = get_woocommerce_service(site_url, wc_consumer_key, wc_consumer_secret)
            if wc:
                # Get 10 products related to the category/niche
                products_for_article = wc.get_products(per_page=10)
                
                if products_for_article:
                    logging.info(f"[AUTOMATION] Site {site_name}: Found {len(products_for_article)} products to include in article")
                    
                    # Build products section for the prompt
                    products_list = []
                    for p in products_for_article[:8]:  # Max 8 products
                        price_info = f"{p['price']} RON"
                        if p.get('on_sale') and p.get('regular_price'):
                            price_info = f"REDUCERE: {p['sale_price']} RON (era {p['regular_price']} RON)"
                        products_list.append(f"- {p['name']}: {price_info} - URL: {p['url']}")
                    
                    products_section = f"""

PRODUSE DIN MAGAZIN (include linkuri către acestea NATURAL în articol):
{chr(10).join(products_list)}

INSTRUCȚIUNI IMPORTANTE PENTRU LINK-URI PRODUSE:
1. Integrează NATURAL 3-5 linkuri către produse în text
2. Folosește formatul: <a href="URL_PRODUS" target="_blank">nume produs</a>
3. NU lista produsele într-un bloc separat - integrează-le în context
4. Menționează prețurile când e relevant
5. Dacă produsul e la reducere, menționează acest lucru
"""
        except Exception as wc_err:
            logging.warning(f"[AUTOMATION] Site {site_name}: WooCommerce error: {wc_err}")
    
    # Get site tone for article generation
    site_tone = site.get("tone", "")
    tone_instruction = f"\nTON: {site_tone}" if site_tone else "\nTON: profesional, informativ, prietenos"
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"auto-article-{uuid.uuid4()}",
        system_message=f"""Ești un expert SEO content writer care scrie articole de înaltă calitate.
        Scrii articole LUNGI și DETALIATE de minimum {target_words} cuvinte.
        
        FOARTE IMPORTANT: Anul curent este {current_year}. 
        INTERZIS să menționezi anii 2020, 2021, 2022, 2023, 2024 sau 2025.
        Folosește DOAR anul {current_year} sau expresii precum "în prezent", "actualmente", "în acest an".
        
        LIMBA: ROMÂNĂ
        {tone_instruction}
        
        CUVINTE CHEIE PENTRU SEO (include natural în text): {site_keywords_str}"""
    ).with_model("gemini", "gemini-2.0-flash")
    
    # Prepare title with prefix if needed
    final_title = f"{article_prefix} {title}" if article_prefix else title
    
    prompt = f"""Scrie un articol SEO LUNG și DETALIAT în limba ROMÂNĂ.

TIP ARTICOL: {article_type.upper()}
{article_instruction}

TITLU: {final_title}
CUVINTE-CHEIE PRINCIPALE: {all_keywords_str}
CUVINTE-CHEIE SEO PENTRU SITE: {site_keywords_str}
CUVINTE-CHEIE TRENDING (include pentru relevanță actuală): {trending_keywords_str}
NIȘĂ: {niche}
CATEGORIE: {category}
LUNGIME MINIMĂ: {target_words} cuvinte
{products_section}
!!! ATENȚIE - ANUL CURENT ESTE {current_year} !!!
NU menționa NICIODATĂ anii 2020, 2021, 2022, 2023, 2024 sau 2025.
Dacă menționezi un an, folosește DOAR {current_year}.

INSTRUCȚIUNI STRICTE:
1. Scrie DOAR în limba ROMÂNĂ
2. Folosește DOAR tag-uri HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
3. Include NATURAL cuvintele cheie în text pentru SEO
4. Include și cuvintele cheie trending pentru relevanță actuală
5. NU folosi markdown (fără #, ##, **, *, -)
6. NU include DOCTYPE, html, head, body, meta, style
7. Scrie paragrafe LUNGI și DETALIATE
8. Include cel puțin 8 secțiuni cu <h2>
9. Dacă ai primit produse, include 3-5 linkuri către ele NATURAL în text
10. Respectă TIPUL DE ARTICOL cerut ({article_type})

Scrie articolul COMPLET acum:"""

    user_message = UserMessage(text=prompt)
    content = await chat.send_message(user_message)
    
    # Clean HTML and convert any markdown
    content = clean_html_content(content)
    
    word_count = len(re.findall(r'\b\w+\b', content))
    
    # If too short, request continuation (always in Romanian)
    if word_count < target_words * 0.8:
        continuation_prompt = f"""Continuă articolul. Adaugă încă 4-5 secțiuni noi cu <h2>.
Folosește DOAR tag-uri HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>
NU folosi markdown.
Scrie în ROMÂNĂ. Fii DETALIAT.
Anul curent este {current_year}.

Continuă:"""
        user_message2 = UserMessage(text=continuation_prompt)
        continuation = await chat.send_message(user_message2)
        continuation = clean_html_content(continuation)
        content = content + "\n\n" + continuation
        word_count = len(re.findall(r'\b\w+\b', content))
    
    # ===== VERIFICĂRI QA AUTOMATE =====
    qa_results = {
        "word_count": word_count,
        "min_words_ok": word_count >= 800,
        "has_h2_tags": content.count("<h2>") >= 3,
        "has_paragraphs": content.count("<p>") >= 5,
        "keyword_density": 0,
        "product_links_count": 0,
        "qa_passed": False
    }
    
    # Check keyword density (target: 1-3%)
    content_lower = content.lower()
    main_keyword = keywords[0].lower() if keywords else ""
    if main_keyword and word_count > 0:
        keyword_occurrences = content_lower.count(main_keyword)
        qa_results["keyword_density"] = round((keyword_occurrences / word_count) * 100, 2)
    
    # Check product links
    qa_results["product_links_count"] = content.count('target="_blank"')
    
    # Determine if QA passed
    qa_results["qa_passed"] = (
        qa_results["min_words_ok"] and 
        qa_results["has_h2_tags"] and 
        qa_results["has_paragraphs"]
    )
    
    # Calculate improved SEO score based on QA
    seo_score = 50  # Base
    if qa_results["min_words_ok"]:
        seo_score += 15
    if qa_results["has_h2_tags"]:
        seo_score += 10
    if qa_results["has_paragraphs"]:
        seo_score += 5
    if 0.5 <= qa_results["keyword_density"] <= 3:
        seo_score += 10
    if qa_results["product_links_count"] >= 2:
        seo_score += 5
    if len(keywords) >= 5:
        seo_score += 5
    
    seo_score = min(95, seo_score)
    
    logging.info(f"[AUTOMATION] Site {site_name}: QA Results - words:{word_count}, h2:{content.count('<h2>')}, density:{qa_results['keyword_density']}%, links:{qa_results['product_links_count']}, PASSED:{qa_results['qa_passed']}")
    logging.info(f"[AUTOMATION] Site {site_name}: Article generated - '{title}' ({word_count} words, SEO:{seo_score})")
    
    # Save article
    article_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    article_doc = {
        "id": article_id,
        "title": final_title,
        "content": content,
        "keywords": keywords,
        "niche": niche,
        "category": category,
        "status": "draft",
        "created_at": now_iso,
        "user_id": user_id,
        "seo_score": seo_score,
        "word_count": word_count,
        "site_id": site_id,
        "auto_generated": True,
        "article_type": article_type,
        "has_product_links": len(products_for_article) > 0,
        "products_count": len(products_for_article),
        "has_trending_keywords": len(trending_keywords) > 0,
        "trending_keywords_used": trending_keywords[:5] if trending_keywords else [],
        "qa_results": qa_results
    }
    await db.articles.insert_one(article_doc)
    
    # LOG TOPIC pentru cooldown tracking (90 zile semantic similarity)
    try:
        await log_topic_used(site_id, title, seo_score)
    except Exception as log_err:
        logging.warning(f"[AUTOMATION] Failed to log topic: {log_err}")
    
    # AUTO-PUBLISH to WordPress
    publish_success = False
    wp_url = ""
    try:
        logging.info(f"[AUTOMATION] Site {site_name}: Publishing article to WordPress...")
        wp_result = await auto_publish_to_wordpress(article_id, site_id, user_id)
        if wp_result and wp_result.get("success"):
            publish_success = True
            wp_url = wp_result.get("post_url", "")
            published_at = datetime.now(timezone.utc).isoformat()
            article_doc["status"] = "published"
            article_doc["wp_post_url"] = wp_url
            article_doc["wp_post_id"] = wp_result.get("post_id")
            article_doc["published_at"] = published_at
            await db.articles.update_one(
                {"id": article_id},
                {"$set": {
                    "status": "published",
                    "wp_post_url": wp_url,
                    "wp_post_id": wp_result.get("post_id"),
                    "published_at": published_at
                }}
            )
            logging.info(f"[AUTOMATION] Site {site_name}: SUCCESS - Published to {wp_url}")
        else:
            error_msg = wp_result.get("error", "Unknown error") if wp_result else "No response"
            logging.error(f"[AUTOMATION] Site {site_name}: FAILED to publish - {error_msg}")
    except Exception as e:
        logging.error(f"[AUTOMATION] Site {site_name}: EXCEPTION during publish - {str(e)}")
    
    # Send email notification - ONLY if send_email is True to avoid duplicates
    if send_email and notification_email and RESEND_API_KEY:
        try:
            status_text = f"Publicat pe WordPress" if publish_success else "Salvat ca Draft"
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #00E676;">🤖 Articol Generat Automat</h2>
                <p>Un nou articol a fost generat pentru <strong>{site_name}</strong>:</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0;">{title}</h3>
                    <p style="margin: 5px 0;"><strong>Categorie:</strong> {category}</p>
                    <p style="margin: 5px 0;"><strong>Cuvinte:</strong> {word_count}</p>
                    <p style="margin: 5px 0;"><strong>Keywords:</strong> {', '.join(keywords)}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> {status_text}</p>
                    {f'<p style="margin: 5px 0;"><a href="{wp_url}" style="color: #00E676;">Vizualizează articolul →</a></p>' if wp_url else ''}
                </div>
                <p>Accesează aplicația pentru a gestiona articolele.</p>
                <p style="color: #888; font-size: 12px; margin-top: 30px;">
                    Generat automat de SEO Automation Platform
                </p>
            </div>
            """
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": notification_email,
                "subject": f"🤖 Articol nou: {title[:50]}",
                "html": email_html
            })
            logging.info(f"[AUTOMATION] Site {site_name}: Email notification sent to {notification_email}")
        except Exception as e:
            logging.error(f"[AUTOMATION] Site {site_name}: Failed to send email - {str(e)}")
    
    logging.info(f"[AUTOMATION] Site {site_name}: Completed - Article '{title}' (published: {publish_success})")
    return article_doc

async def run_daily_automation():
    """Run daily article generation for all users with automation enabled"""
    logging.info("Running daily automation...")
    
    # Get all automation configs that are enabled
    configs = await db.automation_configs.find({"enabled": True}, {"_id": 0}).to_list(1000)
    
    for config in configs:
        user_id = config.get("user_id")
        next_site_index = config.get("next_site_index", 0)
        
        # Get user's sites
        sites = await db.wordpress_configs.find({"user_id": user_id}, {"_id": 0}).to_list(100)
        
        if not sites:
            continue
        
        # Select site based on rotation
        site = sites[next_site_index % len(sites)]
        site_name = site.get("site_name", site.get("site_url", "Unknown"))
        
        # Generate article with RETRY and EXPONENTIAL BACKOFF
        max_retries = 3
        retry_count = 0
        success = False
        last_error = ""
        
        while retry_count < max_retries and not success:
            try:
                if retry_count > 0:
                    # Exponential backoff: 10s, 30s, 90s
                    wait_time = 10 * (3 ** retry_count)
                    logging.info(f"[AUTOMATION] Retry {retry_count}/{max_retries} for {site_name}, waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                
                await generate_automated_article(site, user_id)
                success = True
                logging.info(f"[AUTOMATION] Successfully generated article for {site_name}")
                
            except Exception as e:
                retry_count += 1
                last_error = str(e)
                logging.error(f"[AUTOMATION] Attempt {retry_count}/{max_retries} failed for {site_name}: {last_error}")
        
        # If all retries failed, send alert
        if not success:
            logging.error(f"[AUTOMATION] COMPLETE FAILURE for {site_name} after {max_retries} retries")
            await send_job_failure_alert(
                job_name="Daily Article Generation",
                error_message=last_error,
                site_name=site_name
            )
        
        # Update next site index for rotation
        await db.automation_configs.update_one(
            {"user_id": user_id},
            {"$set": {
                "next_site_index": (next_site_index + 1) % len(sites),
                "last_generation": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    logging.info("Daily automation completed")

@api_router.get("/automation/config")
async def get_automation_config(user: dict = Depends(get_current_user)):
    """Get user's automation configuration"""
    config = await db.automation_configs.find_one({"user_id": user["id"]}, {"_id": 0})
    if not config:
        # Create default config
        config = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "enabled": False,
            "generation_hour": 8,
            "article_length": "medium",
            "categories": [],
            "last_generation": None,
            "next_site_index": 0
        }
        await db.automation_configs.insert_one(config)
        # Remove _id added by MongoDB
        config.pop("_id", None)
    return config

@api_router.post("/automation/config")
async def update_automation_config(config: AutomationConfig, user: dict = Depends(get_current_user)):
    """Update user's automation configuration"""
    existing = await db.automation_configs.find_one({"user_id": user["id"]})
    
    if existing:
        await db.automation_configs.update_one(
            {"user_id": user["id"]},
            {"$set": {
                "enabled": config.enabled,
                "generation_hour": config.generation_hour,
                "article_length": config.article_length,
                "categories": config.categories
            }}
        )
    else:
        config_doc = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "enabled": config.enabled,
            "generation_hour": config.generation_hour,
            "article_length": config.article_length,
            "categories": config.categories,
            "last_generation": None,
            "next_site_index": 0
        }
        await db.automation_configs.insert_one(config_doc)
    
    # Update scheduler if needed
    global scheduler
    if config.enabled:
        # Remove existing job if any
        try:
            scheduler.remove_job(f"daily_automation_{user['id']}")
        except:
            pass
        
        # Add new job with Romania timezone
        scheduler.add_job(
            run_daily_automation,
            CronTrigger(hour=config.generation_hour, minute=0, timezone=ROMANIA_TZ),
            id=f"daily_automation_{user['id']}",
            replace_existing=True
        )
        logging.info(f"Scheduled automation for user {user['id']} at {config.generation_hour}:00 Romania time")
    else:
        # Remove job if disabled
        try:
            scheduler.remove_job(f"daily_automation_{user['id']}")
        except:
            pass
    
    return {"message": "Automation config updated", "enabled": config.enabled}

@api_router.post("/automation/generate-now")
async def generate_article_now(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Manually trigger article generation for testing"""
    if site_id:
        site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]}, {"_id": 0})
    else:
        site = await db.wordpress_configs.find_one({"user_id": user["id"]}, {"_id": 0})
    
    if not site:
        raise HTTPException(status_code=404, detail="No WordPress site found")
    
    article = await generate_automated_article(site, user["id"])
    
    if article:
        return {"message": "Article generated successfully", "article_id": article["id"], "title": article["title"]}
    else:
        raise HTTPException(status_code=500, detail="Failed to generate article")

@api_router.get("/automation/history")
async def get_automation_history(user: dict = Depends(get_current_user)):
    """Get history of auto-generated articles"""
    articles = await db.articles.find(
        {"user_id": user["id"], "auto_generated": True},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return articles

@api_router.get("/automation/publication-log")
async def get_publication_log(user: dict = Depends(get_current_user)):
    """Get detailed log of all published articles with date, time and site info"""
    # Get all articles that were published (both auto and manual)
    articles = await db.articles.find(
        {"user_id": user["id"], "status": "published"},
        {"_id": 0, "id": 1, "title": 1, "site_id": 1, "status": 1, "created_at": 1, 
         "published_at": 1, "wp_post_url": 1, "word_count": 1, "auto_generated": 1,
         "niche": 1, "category": 1}
    ).sort("published_at", -1).to_list(200)
    
    # Get all sites for enrichment
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]}, 
        {"_id": 0, "id": 1, "site_name": 1, "site_url": 1, "niche": 1}
    ).to_list(100)
    site_map = {s["id"]: s for s in sites}
    
    # Enrich articles with site info
    enriched = []
    for article in articles:
        site_id = article.get("site_id")
        site_info = site_map.get(site_id, {})
        enriched.append({
            "id": article.get("id"),
            "title": article.get("title"),
            "site_id": site_id,
            "site_name": site_info.get("site_name") or site_info.get("site_url", "Necunoscut"),
            "site_url": site_info.get("site_url", ""),
            "status": article.get("status"),
            "created_at": article.get("created_at"),
            "published_at": article.get("published_at") or article.get("created_at"),
            "wp_post_url": article.get("wp_post_url", ""),
            "word_count": article.get("word_count", 0),
            "auto_generated": article.get("auto_generated", False),
            "niche": article.get("niche") or site_info.get("niche", "General"),
            "category": article.get("category", "")
        })
    
    return enriched

@api_router.get("/automation/monitor")
async def get_automation_monitor(user: dict = Depends(get_current_user)):
    """Get real-time monitoring data for automation jobs - last 7 days history per site"""
    
    # Get all user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]}, 
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate date 7 days ago
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    now_romania = datetime.now(ROMANIA_TZ)
    
    monitor_data = []
    
    for site in sites:
        site_id = site.get("id")
        site_name = site.get("site_name") or site.get("site_url", "Unknown")
        
        # Get automation settings
        settings = await db.site_automation_settings.find_one(
            {"site_id": site_id, "user_id": user["id"]},
            {"_id": 0}
        )
        
        # Get articles generated in last 7 days for this site
        recent_articles = await db.articles.find(
            {
                "user_id": user["id"],
                "site_id": site_id,
                "auto_generated": True,
                "created_at": {"$gte": seven_days_ago.isoformat()}
            },
            {"_id": 0, "id": 1, "title": 1, "status": 1, "created_at": 1, "published_at": 1, "wp_post_url": 1, "word_count": 1}
        ).sort("created_at", -1).to_list(50)
        
        # Build daily history for last 7 days
        daily_history = []
        for i in range(7):
            day = datetime.now(timezone.utc) - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_label = day.strftime("%a %d/%m")
            
            # Find articles for this day
            day_articles = [
                a for a in recent_articles 
                if a.get("created_at", "").startswith(day_str)
            ]
            
            daily_history.append({
                "date": day_str,
                "label": day_label,
                "count": len(day_articles),
                "published": len([a for a in day_articles if a.get("status") == "published"]),
                "failed": len([a for a in day_articles if a.get("status") == "draft" and not a.get("wp_post_url")]),
                "articles": day_articles[:3]  # Max 3 articles per day for display
            })
        
        # Calculate next scheduled time
        next_scheduled = None
        if settings and settings.get("mode") == "automatic" and settings.get("enabled") and not settings.get("paused"):
            hour = settings.get("generation_hour", 9)
            next_run = now_romania.replace(hour=hour, minute=0, second=0, microsecond=0)
            if next_run <= now_romania:
                next_run += timedelta(days=1)
            
            # Adjust for frequency
            freq = settings.get("frequency", "daily")
            freq_days = {"daily": 1, "every_2_days": 2, "every_3_days": 3, "weekly": 7}
            interval = freq_days.get(freq, 1)
            
            last_gen = settings.get("last_generation")
            if last_gen and interval > 1:
                try:
                    last_gen_date = datetime.fromisoformat(last_gen.replace("Z", "+00:00"))
                    days_since = (datetime.now(timezone.utc) - last_gen_date).days
                    days_until_next = max(0, interval - days_since)
                    next_run = now_romania.replace(hour=hour, minute=0, second=0, microsecond=0) + timedelta(days=days_until_next)
                except:
                    pass
            
            next_scheduled = next_run.isoformat()
        
        # Determine status
        status = "inactive"
        if settings:
            if settings.get("mode") == "automatic" and settings.get("enabled"):
                if settings.get("paused"):
                    status = "paused"
                else:
                    # Check if last generation was successful
                    last_gen = settings.get("last_generation")
                    if last_gen:
                        last_article = recent_articles[0] if recent_articles else None
                        if last_article and last_article.get("status") == "published":
                            status = "healthy"
                        elif last_article and last_article.get("status") == "draft":
                            status = "warning"  # Generated but not published
                        else:
                            status = "healthy"  # No recent articles but automation is on
                    else:
                        status = "pending"  # Never generated
            else:
                status = "manual"
        
        # Count stats
        total_7days = len(recent_articles)
        published_7days = len([a for a in recent_articles if a.get("status") == "published"])
        success_rate = round((published_7days / total_7days * 100) if total_7days > 0 else 0, 1)
        
        monitor_data.append({
            "site_id": site_id,
            "site_name": site_name,
            "site_url": site.get("site_url", ""),
            "niche": site.get("niche", "General"),
            "status": status,
            "automation": {
                "mode": settings.get("mode", "manual") if settings else "manual",
                "enabled": settings.get("enabled", False) if settings else False,
                "paused": settings.get("paused", False) if settings else False,
                "frequency": settings.get("frequency", "daily") if settings else "daily",
                "generation_hour": settings.get("generation_hour", 9) if settings else 9,
                "last_generation": settings.get("last_generation") if settings else None,
                "next_scheduled": next_scheduled,
                "articles_generated": settings.get("articles_generated", 0) if settings else 0
            },
            "stats_7days": {
                "total": total_7days,
                "published": published_7days,
                "success_rate": success_rate
            },
            "daily_history": list(reversed(daily_history)),  # Oldest first
            "recent_articles": recent_articles[:5]
        })
    
    # Sort by status priority: warning > healthy > pending > paused > manual > inactive
    status_priority = {"warning": 0, "healthy": 1, "pending": 2, "paused": 3, "manual": 4, "inactive": 5}
    monitor_data.sort(key=lambda x: status_priority.get(x["status"], 99))
    
    return {
        "current_time": now_romania.isoformat(),
        "timezone": "Europe/Bucharest",
        "sites": monitor_data,
        "summary": {
            "total_sites": len(monitor_data),
            "active_sites": len([s for s in monitor_data if s["status"] in ["healthy", "warning", "pending"]]),
            "paused_sites": len([s for s in monitor_data if s["status"] == "paused"]),
            "total_articles_7days": sum(s["stats_7days"]["total"] for s in monitor_data),
            "total_published_7days": sum(s["stats_7days"]["published"] for s in monitor_data)
        }
    }

# ============================================
# SEO ANALYSIS ENDPOINTS
# ============================================

@api_router.post("/seo/technical-audit")
async def run_technical_audit(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Run technical SEO audit on a URL"""
    from services.seo_analysis import perform_technical_audit
    
    url = request.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL este obligatoriu")
    
    # Run the audit
    result = await perform_technical_audit(url)
    
    # Save to database
    audit_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "url": url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.seo_audits.insert_one(audit_doc)
    del audit_doc["_id"]
    
    return audit_doc

@api_router.get("/seo/audits")
async def get_seo_audits(
    site_id: str = None,
    user: dict = Depends(get_current_user)
):
    """Get SEO audits for the user, optionally filtered by site"""
    query = {"user_id": user["id"]}
    
    if site_id:
        # Get site URL to filter audits
        site = await db.wordpress_configs.find_one(
            {"id": site_id, "user_id": user["id"]},
            {"_id": 0, "site_url": 1}
        )
        if site and site.get("site_url"):
            # Match audits for this site URL (with or without https/www)
            site_domain = site["site_url"].replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            query["url"] = {"$regex": site_domain, "$options": "i"}
    
    audits = await db.seo_audits.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return audits

@api_router.delete("/seo/audit/{audit_id}")
async def delete_seo_audit(audit_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific SEO audit"""
    result = await db.seo_audits.delete_one({"id": audit_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {"message": "Audit deleted"}

@api_router.delete("/seo/audits/all")
async def delete_all_seo_audits(user: dict = Depends(get_current_user)):
    """Delete all SEO audits for the user"""
    result = await db.seo_audits.delete_many({"user_id": user["id"]})
    return {"message": f"Deleted {result.deleted_count} audits"}

@api_router.post("/seo/business-analysis")
async def run_business_analysis(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Run AI-powered business analysis and generate SEO strategy"""
    from services.seo_analysis import generate_business_analysis
    
    url = request.get("url")
    niche = request.get("niche", "general")
    
    if not url:
        raise HTTPException(status_code=400, detail="URL este obligatoriu")
    
    api_key, _, _ = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
    if not api_key:
        raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
    
    # Generate analysis
    result = await generate_business_analysis(url, niche, api_key)
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Eroare la analiză"))
    
    # Save to database
    analysis_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.business_analyses.insert_one(analysis_doc)
    del analysis_doc["_id"]
    
    return analysis_doc

@api_router.get("/seo/business-analyses")
async def get_business_analyses(
    site_id: str = None,
    user: dict = Depends(get_current_user)
):
    """Get business analyses for the user, optionally filtered by site"""
    query = {"user_id": user["id"]}
    
    if site_id:
        # Get site URL to filter analyses
        site = await db.wordpress_configs.find_one(
            {"id": site_id, "user_id": user["id"]},
            {"_id": 0, "site_url": 1}
        )
        if site and site.get("site_url"):
            # Match analyses for this site URL
            site_domain = site["site_url"].replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
            query["url"] = {"$regex": site_domain, "$options": "i"}
    
    analyses = await db.business_analyses.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return analyses

@api_router.delete("/seo/analysis/{analysis_id}")
async def delete_business_analysis(analysis_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific business analysis"""
    result = await db.business_analyses.delete_one({"id": analysis_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"message": "Analysis deleted"}

@api_router.delete("/seo/analyses/all")
async def delete_all_business_analyses(user: dict = Depends(get_current_user)):
    """Delete all business analyses for the user"""
    result = await db.business_analyses.delete_many({"user_id": user["id"]})
    return {"message": f"Deleted {result.deleted_count} analyses"}

@api_router.post("/seo/auto-fix")
async def run_auto_fix(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Automatically fix SEO issues that can be corrected"""
    from services.seo_analysis import auto_fix_seo_issues
    
    site_id = request.get("site_id")
    url = request.get("url")
    
    if not site_id and not url:
        raise HTTPException(status_code=400, detail="Site ID sau URL este obligatoriu")
    
    api_key, _, _ = await get_user_llm_key(user["id"], user.get("role") == "admin", user.get("email", ""))
    if not api_key:
        raise HTTPException(status_code=500, detail="Nu ai configurat o cheie API. Mergi la Chei API.")
    
    # Get WordPress credentials
    if site_id:
        site = await db.wordpress_configs.find_one(
            {"id": site_id, "user_id": user["id"]},
            {"_id": 0}
        )
        if not site:
            raise HTTPException(status_code=404, detail="Site-ul nu a fost găsit")
        
        wp_site_url = site.get("site_url", "")
        wp_username = site.get("username", "")
        wp_password = site.get("app_password", "")
        url = url or wp_site_url
    else:
        # Try to find site by URL
        site = await db.wordpress_configs.find_one(
            {"user_id": user["id"], "site_url": {"$regex": url.replace("https://", "").replace("http://", "").split("/")[0]}},
            {"_id": 0}
        )
        if site:
            wp_site_url = site.get("site_url", "")
            wp_username = site.get("username", "")
            wp_password = site.get("app_password", "")
        else:
            # No WordPress credentials - can only generate suggestions
            wp_site_url = ""
            wp_username = ""
            wp_password = ""
    
    # Run auto-fix
    result = await auto_fix_seo_issues(
        site_url=url,
        wp_site_url=wp_site_url,
        wp_username=wp_username,
        wp_password=wp_password,
        api_key=api_key
    )
    
    # Save result to database
    fix_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "site_id": site_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.seo_fixes.insert_one(fix_doc)
    del fix_doc["_id"]
    
    return fix_doc

@api_router.get("/seo/fixes")
async def get_seo_fixes(user: dict = Depends(get_current_user)):
    """Get all SEO fix history for the user"""
    fixes = await db.seo_fixes.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return fixes

# ============================================
# INDEXING ENDPOINTS
# ============================================

@api_router.post("/indexing/submit-url")
async def submit_url_for_indexing(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Manually submit a URL for indexing"""
    from services.indexing import auto_index_new_article
    
    url = request.get("url")
    site_id = request.get("site_id")
    
    if not url:
        raise HTTPException(status_code=400, detail="URL este obligatoriu")
    
    # Get site config if site_id provided
    wp_config = None
    site_url = url.split("/")[0] + "//" + url.split("/")[2]  # Extract base URL
    
    if site_id:
        site = await db.wordpress_configs.find_one(
            {"id": site_id, "user_id": user["id"]},
            {"_id": 0}
        )
        if site:
            wp_config = site
            site_url = site.get("site_url", site_url)
    
    # Submit for indexing
    result = await auto_index_new_article(
        article_url=url,
        site_url=site_url,
        wp_config=wp_config
    )
    
    # Save to database
    index_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "site_id": site_id,
        "url": url,
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.indexing_requests.insert_one(index_doc)
    del index_doc["_id"]
    
    return index_doc

@api_router.post("/indexing/bulk-submit")
async def bulk_submit_for_indexing(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Submit multiple URLs or all articles from a site for indexing"""
    from services.indexing import bulk_index_site
    
    site_id = request.get("site_id")
    
    if not site_id:
        raise HTTPException(status_code=400, detail="Site ID este obligatoriu")
    
    # Get site
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site-ul nu a fost găsit")
    
    # Get all published articles for this site
    articles = await db.articles.find(
        {"site_id": site_id, "user_id": user["id"], "status": "published", "wp_post_url": {"$exists": True}},
        {"_id": 0, "wp_post_url": 1}
    ).to_list(100)
    
    article_urls = [a["wp_post_url"] for a in articles if a.get("wp_post_url")]
    
    if not article_urls:
        raise HTTPException(status_code=400, detail="Nu există articole publicate pentru acest site")
    
    # Submit for bulk indexing
    result = await bulk_index_site(site.get("site_url", ""), article_urls)
    
    # Save to database
    index_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "site_id": site_id,
        "type": "bulk",
        "urls_submitted": len(article_urls),
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.indexing_requests.insert_one(index_doc)
    del index_doc["_id"]
    
    return index_doc

@api_router.get("/indexing/history")
async def get_indexing_history(
    site_id: str = None,
    user: dict = Depends(get_current_user)
):
    """Get indexing request history"""
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    
    history = await db.indexing_requests.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    
    return history

@api_router.get("/indexing/status/{site_id}")
async def get_indexing_status(
    site_id: str,
    user: dict = Depends(get_current_user)
):
    """Get indexing status for a site"""
    # Get site
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site-ul nu a fost găsit")
    
    # Count published articles
    total_articles = await db.articles.count_documents({
        "site_id": site_id, 
        "user_id": user["id"], 
        "status": "published"
    })
    
    # Get recent indexing requests
    recent_requests = await db.indexing_requests.find(
        {"site_id": site_id, "user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(10)
    
    # Calculate stats
    total_indexed = sum(r.get("total_success", 0) for r in recent_requests)
    last_indexed = recent_requests[0]["created_at"] if recent_requests else None
    
    return {
        "site_id": site_id,
        "site_name": site.get("site_name", site.get("site_url")),
        "total_articles": total_articles,
        "indexing_requests": len(recent_requests),
        "last_indexed": last_indexed,
        "recent_requests": recent_requests[:5]
    }

@api_router.delete("/indexing/history/{history_id}")
async def delete_indexing_history(history_id: str, user: dict = Depends(get_current_user)):
    """Delete a specific indexing history entry"""
    result = await db.indexing_requests.delete_one({"id": history_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {"message": "History entry deleted"}

@api_router.delete("/indexing/history/all")
async def delete_all_indexing_history(user: dict = Depends(get_current_user)):
    """Delete all indexing history for the user"""
    result = await db.indexing_requests.delete_many({"user_id": user["id"]})
    return {"message": f"Deleted {result.deleted_count} entries"}

@api_router.post("/indexing/full-audit")
async def run_full_indexing_audit(
    request: dict,
    user: dict = Depends(get_current_user)
):
    """Run a complete site indexing audit"""
    from services.indexing import full_site_indexing_audit
    
    site_id = request.get("site_id")
    
    if not site_id:
        raise HTTPException(status_code=400, detail="Site ID este obligatoriu")
    
    # Get site
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site-ul nu a fost găsit")
    
    # Get Google credentials if available
    gsc_creds = await db.gsc_credentials.find_one(
        {"user_id": user["id"]},
        {"_id": 0}
    )
    
    # Run full audit
    result = await full_site_indexing_audit(
        site_url=site.get("site_url"),
        wp_config=site,
        google_credentials=gsc_creds
    )
    
    # Save to database
    audit_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "site_id": site_id,
        "type": "full_audit",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result
    }
    await db.indexing_audits.insert_one(audit_doc)
    del audit_doc["_id"]
    
    return audit_doc

@api_router.get("/indexing/audits")
async def get_indexing_audits(
    site_id: str = None,
    user: dict = Depends(get_current_user)
):
    """Get indexing audit history"""
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    
    audits = await db.indexing_audits.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    return audits

@api_router.get("/automation/stats-per-site")
async def get_automation_stats_per_site(user: dict = Depends(get_current_user)):
    """Get monthly article generation statistics per site"""
    from datetime import datetime, timedelta
    
    # Get all user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]}, 
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate date 30 days ago
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    stats = []
    for site in sites:
        site_id = site.get("id")
        
        # Count articles generated in last 30 days for this site
        monthly_count = await db.articles.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "auto_generated": True,
            "created_at": {"$gte": thirty_days_ago.isoformat()}
        })
        
        # Count total articles for this site
        total_count = await db.articles.count_documents({
            "user_id": user["id"],
            "site_id": site_id,
            "auto_generated": True
        })
        
        # Get automation settings for this site
        settings = await db.site_automation_settings.find_one(
            {"site_id": site_id, "user_id": user["id"]},
            {"_id": 0}
        )
        
        # Calculate expected monthly articles based on frequency
        expected_monthly = 0
        if settings and settings.get("mode") == "automatic" and settings.get("enabled") and not settings.get("paused"):
            freq = settings.get("frequency", "daily")
            freq_days = {"daily": 1, "every_2_days": 2, "every_3_days": 3, "weekly": 7}
            interval = freq_days.get(freq, 1)
            expected_monthly = 30 // interval
        
        stats.append({
            "site_id": site_id,
            "site_name": site.get("site_name") or site.get("site_url", "Unknown"),
            "site_url": site.get("site_url"),
            "niche": site.get("niche", "General"),
            "monthly_articles": monthly_count,
            "total_articles": total_count,
            "expected_monthly": expected_monthly,
            "is_active": settings.get("mode") == "automatic" and settings.get("enabled", False) if settings else False,
            "is_paused": settings.get("paused", False) if settings else False
        })
    
    # Sort by monthly articles descending
    stats.sort(key=lambda x: x["monthly_articles"], reverse=True)
    
    return {
        "stats": stats,
        "total_monthly": sum(s["monthly_articles"] for s in stats),
        "total_all_time": sum(s["total_articles"] for s in stats)
    }

# ============ SITE-SPECIFIC AUTOMATION SETTINGS ============

@api_router.get("/automation/sites")
async def get_all_site_automation_settings(user: dict = Depends(get_current_user)):
    """Get automation settings for all user's sites - with caching"""
    user_id = user["id"]
    cache_key = f"automation_sites_{user_id}"
    
    # Check cache
    if cache_key in api_cache:
        cached_data, cached_time = api_cache[cache_key]
        if (datetime.now(timezone.utc) - cached_time).seconds < API_CACHE_TTL:
            return cached_data
    
    sites = await db.wordpress_configs.find({"user_id": user_id}, {"_id": 0, "app_password": 0}).to_list(100)
    
    result = []
    for site in sites:
        settings = await db.site_automation_settings.find_one(
            {"site_id": site["id"], "user_id": user_id}, 
            {"_id": 0}
        )
        if not settings:
            # Create default settings
            settings = {
                "id": str(uuid.uuid4()),
                "site_id": site["id"],
                "user_id": user["id"],
                "mode": "manual",
                "enabled": False,
                "paused": False,
                "generation_hour": 9,
                "frequency": "daily",
                "article_length": "medium",
                "publish_mode": "publish",
                "email_notification": True,
                "include_product_links": False,
                "product_links_source": "",
                "max_product_links": 3,
                "last_generation": None,
                "next_generation": None,
                "articles_generated": 0
            }
            await db.site_automation_settings.insert_one(settings)
            # Remove _id added by MongoDB
            settings.pop("_id", None)
        
        result.append({
            "site": site,
            "automation": settings
        })
    
    # Cache the result
    api_cache[cache_key] = (result, datetime.now(timezone.utc))
    
    return result

@api_router.get("/automation/diagnostic")
async def automation_diagnostic(user: dict = Depends(get_current_user)):
    """Diagnostic endpoint to check why automation didn't run for sites"""
    user_id = user["id"]
    
    # Get all sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "site_name": 1, "site_url": 1, "niche": 1, "app_password": 1}
    ).to_list(100)
    
    diagnostic = []
    for site in sites:
        site_id = site.get("id")
        site_name = site.get("site_name") or site.get("site_url", "Unknown")
        
        # Get automation settings
        settings = await db.site_automation_settings.find_one(
            {"site_id": site_id, "user_id": user_id},
            {"_id": 0}
        )
        
        # Get today's articles
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        articles_today = await db.articles.count_documents({
            "site_id": site_id,
            "user_id": user_id,
            "created_at": {"$gte": today_start.isoformat()}
        })
        
        # Check issues
        issues = []
        if not settings:
            issues.append("Nu are setări de automatizare salvate")
        elif not settings.get("automation_enabled"):
            issues.append("Automatizarea nu e activată")
        
        if not site.get("app_password"):
            issues.append("Lipsește Application Password pentru WordPress")
        
        if not site.get("niche"):
            issues.append("Nișa nu e setată")
        
        diagnostic.append({
            "site_name": site_name,
            "site_id": site_id,
            "automation_enabled": settings.get("automation_enabled", False) if settings else False,
            "publish_hour": settings.get("publish_hour", "N/A") if settings else "N/A",
            "articles_generated_today": articles_today,
            "has_app_password": bool(site.get("app_password")),
            "has_niche": bool(site.get("niche")),
            "issues": issues,
            "status": "OK" if not issues and settings and settings.get("automation_enabled") else "PROBLEMĂ"
        })
    
    return {"sites": diagnostic, "server_time": datetime.now(timezone.utc).isoformat()}

@api_router.get("/automation/site/{site_id}")
async def get_site_automation_settings(site_id: str, user: dict = Depends(get_current_user)):
    """Get automation settings for a specific site"""
    """Get automation settings for a specific site"""
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]}, 
        {"_id": 0, "app_password": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    settings = await db.site_automation_settings.find_one(
        {"site_id": site_id, "user_id": user["id"]}, 
        {"_id": 0}
    )
    if not settings:
        settings = {
            "id": str(uuid.uuid4()),
            "site_id": site_id,
            "user_id": user["id"],
            "mode": "manual",
            "enabled": False,
            "paused": False,
            "generation_hour": 9,
            "frequency": "daily",
            "article_length": "medium",
            "publish_mode": "draft",
            "email_notification": True,
            "include_product_links": False,
            "product_links_source": "",
            "max_product_links": 3,
            "last_generation": None,
            "next_generation": None,
            "articles_generated": 0
        }
        await db.site_automation_settings.insert_one(settings)
        # Remove _id added by MongoDB
        settings.pop("_id", None)
    
    return {"site": site, "automation": settings}

@api_router.post("/automation/site/{site_id}")
async def update_site_automation_settings(
    site_id: str, 
    settings: SiteAutomationSettings, 
    user: dict = Depends(get_current_user)
):
    """Update automation settings for a specific site"""
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user["id"]})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Calculate next generation time based on frequency
    next_gen = None
    if settings.mode == "automatic" and settings.enabled:
        now = datetime.now(timezone.utc)
        next_gen_date = now.replace(hour=settings.generation_hour, minute=0, second=0, microsecond=0)
        if next_gen_date <= now:
            next_gen_date += timedelta(days=1)
        
        freq_days = {"daily": 1, "every_2_days": 2, "every_3_days": 3, "weekly": 7}
        # No adjustment needed for the first scheduled time
        next_gen = next_gen_date.isoformat()
    
    existing = await db.site_automation_settings.find_one({"site_id": site_id, "user_id": user["id"]})
    
    update_data = {
        "mode": settings.mode,
        "enabled": settings.enabled,
        "paused": settings.paused,
        "generation_hour": settings.generation_hour,
        "frequency": settings.frequency,
        "article_length": settings.article_length,
        "publish_mode": settings.publish_mode,
        "email_notification": settings.email_notification,
        "include_product_links": settings.include_product_links,
        "product_links_source": settings.product_links_source,
        "max_product_links": settings.max_product_links,
        "next_generation": next_gen
    }
    
    if existing:
        await db.site_automation_settings.update_one(
            {"site_id": site_id, "user_id": user["id"]},
            {"$set": update_data}
        )
    else:
        new_settings = {
            "id": str(uuid.uuid4()),
            "site_id": site_id,
            "user_id": user["id"],
            "last_generation": None,
            "articles_generated": 0,
            **update_data
        }
        await db.site_automation_settings.insert_one(new_settings)
    
    # Update scheduler for this site
    job_id = f"site_automation_{site_id}"
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    
    if settings.mode == "automatic" and settings.enabled:
        freq_days = {"daily": 1, "every_2_days": 2, "every_3_days": 3, "weekly": 7}
        days_interval = freq_days.get(settings.frequency, 1)
        
        # Schedule job with Romania timezone
        scheduler.add_job(
            run_site_automation,
            CronTrigger(hour=settings.generation_hour, minute=0, timezone=ROMANIA_TZ),
            id=job_id,
            args=[site_id, user["id"]],
            replace_existing=True
        )
        logging.info(f"Scheduled automation for site {site_id} at {settings.generation_hour}:00 Romania time")
    
    return {"message": "Site automation settings updated", "next_generation": next_gen}

async def run_site_automation(site_id: str, user_id: str):
    """Run automation for a specific site - triggered by scheduler at the configured hour"""
    now_romania = datetime.now(ROMANIA_TZ)
    logging.info(f"[SCHEDULER] Starting automation for site {site_id} at {now_romania.strftime('%Y-%m-%d %H:%M:%S')} (Romania time)")
    
    settings = await db.site_automation_settings.find_one(
        {"site_id": site_id, "user_id": user_id},
        {"_id": 0}
    )
    
    if not settings or not settings.get("enabled") or settings.get("mode") != "automatic":
        logging.info(f"[SCHEDULER] Automation disabled for site {site_id} - skipping")
        return
    
    # Check if paused
    if settings.get("paused"):
        logging.info(f"[SCHEDULER] Automation paused for site {site_id} - skipping")
        return
    
    # Check frequency - only skip if we've generated recently based on frequency
    last_gen = settings.get("last_generation")
    if last_gen:
        try:
            last_gen_date = datetime.fromisoformat(last_gen.replace("Z", "+00:00"))
            freq_days = {"daily": 1, "every_2_days": 2, "every_3_days": 3, "weekly": 7}
            days_required = freq_days.get(settings.get("frequency", "daily"), 1)
            
            # Calculate hours since last generation
            hours_since_last = (datetime.now(timezone.utc) - last_gen_date).total_seconds() / 3600
            min_hours_required = (days_required - 1) * 24 + 20  # Allow 4 hour buffer for same day
            
            if hours_since_last < min_hours_required:
                logging.info(f"[SCHEDULER] Site {site_id}: Skipping - only {hours_since_last:.1f} hours since last generation (requires ~{min_hours_required} hours for {settings.get('frequency')} frequency)")
                return
        except Exception as e:
            logging.warning(f"[SCHEDULER] Site {site_id}: Error parsing last_generation date: {e} - will proceed with generation")
    
    site = await db.wordpress_configs.find_one({"id": site_id, "user_id": user_id}, {"_id": 0})
    if not site:
        logging.error(f"[SCHEDULER] Site {site_id} not found in database")
        return
    
    site_name = site.get("site_name", site.get("site_url", "Unknown"))
    configured_hour = settings.get("generation_hour", 9)
    logging.info(f"[SCHEDULER] Site {site_name}: Running scheduled automation (configured for {configured_hour}:00, current time: {now_romania.strftime('%H:%M')})")
    
    # Generate article with settings - send_email handled inside function
    article = await generate_automated_article_with_settings(site, user_id, settings)
    
    if article:
        # Update statistics
        now_iso = datetime.now(timezone.utc).isoformat()
        await db.site_automation_settings.update_one(
            {"site_id": site_id, "user_id": user_id},
            {"$set": {
                "last_generation": now_iso,
                "articles_generated": settings.get("articles_generated", 0) + 1
            }}
        )
        logging.info(f"[SCHEDULER] Site {site_name}: SUCCESS - Generated article '{article['title']}' at {now_romania.strftime('%H:%M')}")
        
        # NOTE: Email notification is now handled INSIDE generate_automated_article_with_settings
        # to avoid duplicate emails. The function checks settings.email_notification internally.
    else:
        logging.error(f"[SCHEDULER] Site {site_name}: FAILED to generate article")

async def generate_automated_article_with_settings(site: dict, user_id: str, settings: dict):
    """Generate an article with site-specific settings including product links
    
    Email notification is sent from THIS function if settings.email_notification is True.
    This is the ONLY place emails are sent to avoid duplicates.
    """
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        logging.error(f"[AUTOMATION] No LLM API key - cannot generate article")
        return None
    
    niche = site.get("niche", "general").lower()
    niche_romanian = normalize_niche_to_romanian(niche)
    site_id = site.get("id")
    site_name = site.get("site_name", site.get("site_url", "Site"))
    site_url = site.get("site_url", "").lower()
    notification_email = site.get("notification_email", "")
    
    # ALL articles in Romanian - focusing on Romania market
    article_language = "ro"
    
    logging.info(f"[AUTOMATION] Site {site_name}: Starting article generation - Language: {article_language}, Niche: {niche_romanian}")
    
    # Get categories for this niche
    categories = NICHE_CATEGORIES.get(niche, NICHE_CATEGORIES["default"])
    
    # Select category based on recently used topics for better diversity
    import random
    recent_arts = await db.articles.find(
        {"site_id": site_id},
        {"_id": 0, "category": 1}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    recent_cats = [art.get("category", "") for art in recent_arts]
    avail_cats = [cat for cat in categories if cat not in recent_cats[:3]]
    if not avail_cats:
        avail_cats = categories
    category = random.choice(avail_cats)
    
    logging.info(f"[AUTOMATION] Site {site_name}: Generating in category '{category}'")
    
    # Get site's saved keywords for diversity
    site_keywords = site.get("auto_keywords", [])
    
    # Generate keywords and title - USE SITE KEYWORDS for diverse topics
    if site_keywords and len(site_keywords) >= 3:
        import random
        selected_keywords = random.sample(site_keywords, min(3, len(site_keywords)))
        logging.info(f"[AUTOMATION] Using site keywords for topic: {selected_keywords}")
        title, keywords = await generate_keywords_for_topic_from_keywords(
            api_key, niche_romanian, category, selected_keywords
        )
    else:
        title, keywords = await generate_keywords_for_topic(api_key, niche_romanian, category)
    
    # Merge with more site keywords
    if site_keywords:
        extra_kw = random.sample(site_keywords, min(5, len(site_keywords)))
        keywords = list(set(keywords + extra_kw))
    
    # Article length
    length_words = {"short": 500, "medium": 1000, "long": 2000}
    target_words = length_words.get(settings.get("article_length", "medium"), 1000)
    
    # Product links section - always in Romanian
    product_links_instruction = ""
    if settings.get("include_product_links") and site_url:
        product_source = settings.get("product_links_source", "")
        max_links = settings.get("max_product_links", 3)
        
        product_links_instruction = f"""
IMPORTANT - LINKURI PRODUSE:
- Include {max_links} linkuri către produse relevante din site-ul {site_url}
- Folosește linkuri în format: <a href="{site_url}/produs/NUME-PRODUS">Nume Produs</a>
- Plasează linkurile natural în text, în secțiuni relevante
- Produsele trebuie să fie relevante pentru subiectul articolului
{f'- Focus pe produse legate de: {product_source}' if product_source else ''}
"""
    
    # CRITICAL: Force current year - NEVER use 2024 or 2025
    current_year = 2026
    
    # All articles in Romanian
    chat = LlmChat(
        api_key=api_key,
        session_id=f"auto-article-{uuid.uuid4()}",
        system_message=f"""Ești un expert în scriere de conținut SEO. Scrii NUMAI în limba ROMÂNĂ.
        Folosești DOAR tag-uri HTML pentru conținut: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
        NU folosești: <!DOCTYPE>, <html>, <head>, <body>, <meta>, <title>, <style>
        NU folosești markdown (fără #, ##, **, *, -, etc.)
        Scrii articole LUNGI și DETALIATE de minimum {target_words} cuvinte.
        
        FOARTE IMPORTANT: Anul curent este {current_year}. 
        INTERZIS să menționezi anii 2020, 2021, 2022, 2023, 2024 sau 2025.
        Folosește DOAR anul {current_year} sau expresii precum "în prezent", "actualmente", "în acest an"."""
    ).with_model("gemini", "gemini-2.0-flash")
    
    prompt = f"""Scrie un articol SEO LUNG și DETALIAT în limba ROMÂNĂ.

TITLU: {title}
CUVINTE-CHEIE: {', '.join(keywords)}
NIȘĂ: {niche}
CATEGORIE: {category}
LUNGIME MINIMĂ: {target_words} cuvinte

!!! ATENȚIE - ANUL CURENT ESTE {current_year} !!!
NU menționa NICIODATĂ anii 2020, 2021, 2022, 2023, 2024 sau 2025.
Dacă menționezi un an, folosește DOAR {current_year}.

{product_links_instruction}

INSTRUCȚIUNI STRICTE:
1. Scrie DOAR în limba ROMÂNĂ
2. Folosește DOAR tag-uri HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
3. NU folosi markdown (fără #, ##, **, *, -)
4. NU include DOCTYPE, html, head, body, meta, style
5. Scrie paragrafe LUNGI și DETALIATE
6. Include cel puțin 6 secțiuni cu <h2>

Scrie articolul COMPLET acum:"""

    user_message = UserMessage(text=prompt)
    content = await chat.send_message(user_message)
    
    # Clean HTML and convert any markdown
    content = clean_html_content(content)
    
    word_count = len(re.findall(r'\b\w+\b', content))
    
    # If too short, request continuation (always in Romanian)
    if word_count < target_words * 0.8:
        continuation_prompt = f"""Continuă articolul. Adaugă încă 4-5 secțiuni noi cu <h2>.
Folosește DOAR tag-uri HTML: <h2>, <h3>, <p>, <ul>, <li>, <strong>, <a>
NU folosi markdown.
Scrie în ROMÂNĂ. Fii DETALIAT.
Anul curent este {current_year}.
{product_links_instruction}

Continuă:"""
        user_message2 = UserMessage(text=continuation_prompt)
        continuation = await chat.send_message(user_message2)
        continuation = clean_html_content(continuation)
        content = content + "\n\n" + continuation
        word_count = len(re.findall(r'\b\w+\b', content))
    
    seo_score = min(95, 70 + len(keywords) * 5)
    
    logging.info(f"[AUTOMATION] Site {site_name}: Article generated - '{title}' ({word_count} words)")
    
    # Save article
    article_id = str(uuid.uuid4())
    now_iso = datetime.now(timezone.utc).isoformat()
    article_doc = {
        "id": article_id,
        "title": title,
        "content": content,
        "keywords": keywords,
        "niche": niche,
        "category": category,
        "status": "draft",
        "created_at": now_iso,
        "user_id": user_id,
        "seo_score": seo_score,
        "word_count": word_count,
        "site_id": site_id,
        "auto_generated": True,
        "has_product_links": settings.get("include_product_links", False)
    }
    await db.articles.insert_one(article_doc)
    
    # AUTO-PUBLISH to WordPress if publish_mode is "publish"
    publish_success = False
    wp_url = ""
    if settings.get("publish_mode", "publish") == "publish":
        try:
            logging.info(f"[AUTOMATION] Site {site_name}: Publishing article to WordPress...")
            wp_result = await auto_publish_to_wordpress(article_id, site_id, user_id)
            if wp_result and wp_result.get("success"):
                publish_success = True
                wp_url = wp_result.get("post_url", "")
                published_at = datetime.now(timezone.utc).isoformat()
                article_doc["status"] = "published"
                article_doc["wp_post_url"] = wp_url
                article_doc["wp_post_id"] = wp_result.get("post_id")
                article_doc["published_at"] = published_at
                await db.articles.update_one(
                    {"id": article_id},
                    {"$set": {
                        "status": "published",
                        "wp_post_url": wp_url,
                        "wp_post_id": wp_result.get("post_id"),
                        "published_at": published_at
                    }}
                )
                logging.info(f"[AUTOMATION] Site {site_name}: SUCCESS - Published to {wp_url}")
            else:
                error_msg = wp_result.get("error", "Unknown error") if wp_result else "No response"
                logging.error(f"[AUTOMATION] Site {site_name}: FAILED to publish - {error_msg}")
        except Exception as e:
            logging.error(f"[AUTOMATION] Site {site_name}: EXCEPTION during publish - {str(e)}")
    else:
        logging.info(f"[AUTOMATION] Site {site_name}: Saved as draft (publish_mode: draft)")
    
    # Send email notification - ONLY if email_notification setting is enabled
    should_send_email = settings.get("email_notification", True)
    if should_send_email and notification_email and RESEND_API_KEY:
        try:
            status_text = "Publicat pe WordPress" if publish_success else "Salvat ca Draft"
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #00E676;">🤖 Articol Generat Automat</h2>
                <p>Un nou articol a fost generat pentru <strong>{site_name}</strong>:</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0;">{title}</h3>
                    <p style="margin: 5px 0;"><strong>Categorie:</strong> {category}</p>
                    <p style="margin: 5px 0;"><strong>Cuvinte:</strong> {word_count}</p>
                    <p style="margin: 5px 0;"><strong>Keywords:</strong> {', '.join(keywords)}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> {status_text}</p>
                    <p style="margin: 5px 0;"><strong>Linkuri produse:</strong> {'Da' if settings.get('include_product_links') else 'Nu'}</p>
                    {f'<p style="margin: 10px 0 0 0;"><a href="{wp_url}" style="color: #00E676; font-weight: bold;">Vizualizează articolul →</a></p>' if wp_url else ''}
                </div>
                <p>Accesează aplicația pentru a gestiona articolele.</p>
                <p style="color: #888; font-size: 12px; margin-top: 30px;">
                    Generat automat de SEO Automation Platform
                </p>
            </div>
            """
            resend.Emails.send({
                "from": SENDER_EMAIL,
                "to": notification_email,
                "subject": f"🤖 Articol nou: {title[:50]}",
                "html": email_html
            })
            logging.info(f"[AUTOMATION] Site {site_name}: Email notification sent to {notification_email}")
        except Exception as e:
            logging.error(f"[AUTOMATION] Site {site_name}: Failed to send email - {str(e)}")
    
    logging.info(f"[AUTOMATION] Site {site_name}: Completed - Article '{title}' (published: {publish_success})")
    return article_doc

# ============ DASHBOARD STATS ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    
    articles_count = await db.articles.count_documents(query)
    published_query = {**query, "status": "published"}
    published_count = await db.articles.count_documents(published_query)
    keywords_count = await db.keywords.count_documents(query)
    calendar_count = await db.calendar.count_documents(query)
    backlink_requests = await db.backlink_requests.count_documents({"user_id": user["id"]})
    
    return {
        "total_articles": articles_count,
        "published_articles": published_count,
        "draft_articles": articles_count - published_count,
        "total_keywords": keywords_count,
        "scheduled_posts": calendar_count,
        "backlink_requests": backlink_requests,
        "monthly_quota": 30,
        "used_quota": min(articles_count, 30)
    }

@api_router.get("/dashboard/all")
async def get_dashboard_all(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Combined endpoint for all dashboard data - reduces API calls from 5 to 1"""
    user_id = user["id"]
    
    # Check cache first
    cache_key = f"dashboard_all_{user_id}_{site_id or 'all'}"
    cached = api_cache.get(cache_key)
    if cached:
        cached_data, cached_time = cached
        if (datetime.now(timezone.utc) - cached_time).total_seconds() < 30:  # 30 second cache
            return cached_data
    
    query = {"user_id": user_id}
    if site_id:
        query["site_id"] = site_id
    
    # Run all queries in parallel using asyncio.gather
    articles_count_task = db.articles.count_documents(query)
    published_count_task = db.articles.count_documents({**query, "status": "published"})
    keywords_count_task = db.keywords.count_documents(query)
    calendar_count_task = db.calendar.count_documents(query)
    backlink_requests_task = db.backlink_requests.count_documents({"user_id": user_id})
    sites_task = db.wordpress_configs.find({"user_id": user_id}, {"_id": 0, "app_password": 0}).to_list(100)
    automation_task = db.site_automation_settings.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Parallel execution
    (articles_count, published_count, keywords_count, calendar_count, 
     backlink_requests, sites, automation_settings) = await asyncio.gather(
        articles_count_task, published_count_task, keywords_count_task, calendar_count_task,
        backlink_requests_task, sites_task, automation_task
    )
    
    # Build automation data
    automation_map = {a["site_id"]: a for a in automation_settings}
    automation_sites = []
    for site in sites:
        automation_sites.append({
            "site": site,
            "automation": automation_map.get(site["id"], {"enabled": False, "mode": "manual"})
        })
    
    # Get recent history (last 30 articles)
    history = await db.articles.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "title": 1, "site_id": 1, "created_at": 1, "status": 1}
    ).sort("created_at", -1).limit(30).to_list(30)
    
    # Calculate weekly articles
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_articles = sum(1 for h in history if h.get("created_at") and 
                         datetime.fromisoformat(h["created_at"].replace('Z', '+00:00')) > one_week_ago)
    
    # Stats per site
    site_stats = []
    for site in sites:
        site_articles = await db.articles.count_documents({"user_id": user_id, "site_id": site["id"]})
        site_published = await db.articles.count_documents({"user_id": user_id, "site_id": site["id"], "status": "published"})
        site_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name", site.get("site_url", "")),
            "total": site_articles,
            "published": site_published
        })
    
    result = {
        "stats": {
            "total_articles": articles_count,
            "published_articles": published_count,
            "draft_articles": articles_count - published_count,
            "total_keywords": keywords_count,
            "scheduled_posts": calendar_count,
            "backlink_requests": backlink_requests,
            "monthly_quota": 30,
            "used_quota": min(articles_count, 30)
        },
        "automation": {
            "sites": automation_sites,
            "totalSites": len(sites),
            "weeklyArticles": weekly_articles,
            "totalAutoArticles": len(history)
        },
        "site_stats": {
            "stats": site_stats,
            "total_monthly": weekly_articles * 4,
            "total_all_time": articles_count
        },
        "history": history[:10]  # Last 10 for quick display
    }
    
    # Cache the result
    api_cache[cache_key] = (result, datetime.now(timezone.utc))
    
    return result

# Include routers
app.include_router(api_router)

# Include SaaS router
app.include_router(saas_router)

# Include Admin router
app.include_router(admin_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*", "http://localhost:3000", "http://localhost:8001"],
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ STRIPE WEBHOOK ============
from fastapi import Request

@app.post("/api/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    from emergentintegrations.payments.stripe.checkout import StripeCheckout
    
    stripe_api_key = os.environ.get("STRIPE_API_KEY")
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe not configured")
    
    stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
    
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature", "")
        
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        logging.info(f"[STRIPE WEBHOOK] Event: {webhook_response.event_type}, Session: {webhook_response.session_id}")
        
        # Update transaction and subscription based on event
        if webhook_response.payment_status == "paid":
            transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
            if transaction and transaction.get("status") != "paid":
                # Update transaction
                await db.payment_transactions.update_one(
                    {"session_id": webhook_response.session_id},
                    {"$set": {
                        "status": "paid",
                        "payment_status": "paid",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                # Upgrade subscription
                user_id = transaction.get("user_id") or webhook_response.metadata.get("user_id")
                plan = transaction.get("plan") or webhook_response.metadata.get("plan", "starter")
                
                if user_id:
                    subscription_service = SubscriptionService(db)
                    await subscription_service.upgrade_subscription(
                        user_id=user_id,
                        plan=plan,
                        stripe_customer_id=webhook_response.metadata.get("customer_id"),
                        stripe_subscription_id=webhook_response.session_id
                    )
                    logging.info(f"[STRIPE WEBHOOK] Upgraded user {user_id} to {plan}")
        
        return {"status": "success"}
    except Exception as e:
        logging.error(f"[STRIPE WEBHOOK] Error: {e}")
        return {"status": "error", "message": str(e)}

@app.on_event("startup")
async def startup_event():
    """Start the scheduler on app startup"""
    global scheduler
    
    # CREATE MONGODB INDEXES for better performance
    logging.info("[STARTUP] Creating MongoDB indexes for performance...")
    try:
        await db.articles.create_index([("user_id", 1), ("site_id", 1), ("status", 1)])
        await db.articles.create_index([("user_id", 1), ("published_at", -1)])
        await db.wordpress_configs.create_index([("user_id", 1)])
        await db.keywords.create_index([("user_id", 1), ("site_id", 1)])
        await db.niche_backlinks.create_index([("user_id", 1), ("site_id", 1)])
        await db.backlink_outreach.create_index([("user_id", 1), ("site_id", 1), ("status", 1)])
        await db.site_automation_settings.create_index([("user_id", 1), ("site_id", 1)])
        # Topics log index for cooldown tracking
        await db.topics_log.create_index([("site_id", 1), ("used_at", -1)])
        logging.info("[STARTUP] MongoDB indexes created successfully")
    except Exception as e:
        logging.error(f"[STARTUP] Error creating indexes: {e}")
    
    # AUTO-MIGRATE NICHES TO ROMANIAN for all sites
    logging.info("[STARTUP] Auto-migrating site niches to Romanian...")
    try:
        sites = await db.wordpress_configs.find({}, {"_id": 0, "id": 1, "site_url": 1, "niche": 1, "wc_consumer_key": 1}).to_list(1000)
        for site in sites:
            site_url = site.get("site_url", "").lower()
            site_id = site.get("id")
            current_niche = site.get("niche", "")
            
            # Find matching Romanian niche
            new_niche = None
            wc_creds = None
            for domain_key, romanian_niche in SITE_NICHES_ROMANIAN.items():
                if domain_key in site_url:
                    new_niche = romanian_niche
                    # Also check for WooCommerce credentials
                    if domain_key in WOOCOMMERCE_CREDENTIALS:
                        wc_creds = WOOCOMMERCE_CREDENTIALS[domain_key]
                    break
            
            update_fields = {}
            
            if new_niche and new_niche != current_niche:
                update_fields["niche"] = new_niche
                logging.info(f"[STARTUP] Migrated niche for {site_url}: {current_niche} -> {new_niche}")
            
            # Auto-add WooCommerce credentials if not already set
            if wc_creds and not site.get("wc_consumer_key"):
                update_fields["wc_consumer_key"] = wc_creds["consumer_key"]
                update_fields["wc_consumer_secret"] = wc_creds["consumer_secret"]
                logging.info(f"[STARTUP] Added WooCommerce credentials for {site_url}")
            
            if update_fields:
                await db.wordpress_configs.update_one(
                    {"id": site_id},
                    {"$set": update_fields}
                )
    except Exception as e:
        logging.error(f"[STARTUP] Error migrating niches/WooCommerce: {e}")
    
    # Load all enabled automation configs and schedule them (legacy)
    configs = await db.automation_configs.find({"enabled": True}, {"_id": 0}).to_list(1000)
    
    for config in configs:
        user_id = config.get("user_id")
        hour = config.get("generation_hour", 8)
        
        scheduler.add_job(
            run_daily_automation,
            CronTrigger(hour=hour, minute=0, timezone=ROMANIA_TZ),
            id=f"daily_automation_{user_id}",
            replace_existing=True
        )
        logging.info(f"Loaded automation for user {user_id} at {hour}:00 Romania time")
    
    # Load site-specific automation settings
    site_settings = await db.site_automation_settings.find(
        {"enabled": True, "mode": "automatic"}, 
        {"_id": 0}
    ).to_list(1000)
    
    for settings in site_settings:
        site_id = settings.get("site_id")
        user_id = settings.get("user_id")
        hour = settings.get("generation_hour", 9)
        
        scheduler.add_job(
            run_site_automation,
            CronTrigger(hour=hour, minute=0, timezone=ROMANIA_TZ),
            id=f"site_automation_{site_id}",
            args=[site_id, user_id],
            replace_existing=True
        )
        logging.info(f"Loaded site automation for site {site_id} at {hour}:00 Romania time")
    
    scheduler.start()
    logging.info("Scheduler started with Romania timezone (Europe/Bucharest)")
    
    # ===== RECOVER MISSED JOBS =====
    # Check if any automation jobs were missed today and run them
    asyncio.create_task(recover_missed_automation_jobs())
    
    # Schedule DAILY backlink opportunity search at 6:00 AM
    scheduler.add_job(
        search_new_backlink_opportunities,
        CronTrigger(hour=6, minute=0, timezone=ROMANIA_TZ),
        id="daily_backlink_search",
        replace_existing=True
    )
    logging.info("Scheduled daily backlink search at 6:00 AM")
    
    # Schedule DAILY backlink outreach at 12:30 (after articles are published)
    scheduler.add_job(
        run_daily_backlink_outreach,
        CronTrigger(hour=12, minute=30, timezone=ROMANIA_TZ),
        id="daily_backlink_outreach",
        replace_existing=True
    )
    logging.info("Scheduled daily backlink outreach at 12:30 PM")
    
    # Schedule daily keyword generation (every day at 5:00 AM)
    scheduler.add_job(
        auto_generate_keywords_for_all_sites,
        CronTrigger(hour=5, minute=0, timezone=ROMANIA_TZ),
        id="daily_keyword_generation",
        replace_existing=True
    )
    logging.info("Scheduled daily keyword generation at 5:00 AM")
    
    # Schedule monthly SEO report (1st of each month at 9:00)
    scheduler.add_job(
        send_monthly_seo_reports,
        CronTrigger(day=1, hour=9, minute=0, timezone=ROMANIA_TZ),
        id="monthly_seo_report",
        replace_existing=True
    )
    logging.info("Scheduled monthly SEO reports")
    
    # Schedule weekly SEO report (every Monday at 9:00)
    scheduler.add_job(
        send_weekly_seo_reports,
        CronTrigger(day_of_week='mon', hour=9, minute=0, timezone=ROMANIA_TZ),
        id="weekly_seo_report",
        replace_existing=True
    )
    logging.info("Scheduled weekly SEO reports")
    
    # Schedule trial expiration reminders (daily at 10 AM)
    scheduler.add_job(
        check_trial_expirations,
        CronTrigger(hour=10, minute=0, timezone=ROMANIA_TZ),
        id="trial_expiration_check",
        replace_existing=True
    )
    logging.info("Scheduled trial expiration reminders")
    
    # Schedule monthly usage reset (1st of each month at 00:05 AM)
    scheduler.add_job(
        reset_monthly_usage,
        CronTrigger(day=1, hour=0, minute=5, timezone=ROMANIA_TZ),
        id="monthly_usage_reset",
        replace_existing=True
    )
    logging.info("Scheduled monthly usage reset")

async def reset_monthly_usage():
    """Reset monthly article usage for all subscriptions on 1st of month"""
    logging.info("[USAGE] Resetting monthly article usage for all users...")
    
    result = await db.subscriptions.update_many(
        {},
        {"$set": {"articles_used_this_month": 0}}
    )
    
    logging.info(f"[USAGE] Reset {result.modified_count} subscriptions")

async def check_trial_expirations():
    """Check for expiring trials and send reminders"""
    from saas.email_service import email_service
    from datetime import timedelta
    
    logging.info("[TRIAL] Checking for expiring trials...")
    
    now = datetime.now(timezone.utc)
    
    # Find trials expiring in 2 days
    two_days_later = now + timedelta(days=2)
    one_day_later = now + timedelta(days=1)
    
    # Get trials that expire in ~2 days (reminder)
    expiring_trials = await db.subscriptions.find({
        "status": "trialing",
        "trial_ends_at": {
            "$gte": one_day_later.isoformat(),
            "$lte": two_days_later.isoformat()
        }
    }, {"_id": 0}).to_list(1000)
    
    for sub in expiring_trials:
        user = await db.users.find_one({"id": sub["user_id"]}, {"_id": 0})
        if user:
            # Calculate days left
            trial_end = datetime.fromisoformat(sub["trial_ends_at"].replace("Z", "+00:00"))
            days_left = max(1, (trial_end - now).days)
            
            # Get usage stats
            articles_used = sub.get("articles_used_this_month", 0)
            sites_count = await db.wordpress_configs.count_documents({"user_id": sub["user_id"]})
            
            await email_service.send_trial_reminder(
                user["email"],
                user.get("name", "User"),
                days_left,
                articles_used,
                sites_count
            )
            logging.info(f"[TRIAL] Sent reminder to {user['email']} ({days_left} days left)")
    
    # Find and expire old trials
    expired_trials = await db.subscriptions.find({
        "status": "trialing",
        "trial_ends_at": {"$lt": now.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    for sub in expired_trials:
        await db.subscriptions.update_one(
            {"user_id": sub["user_id"]},
            {"$set": {"status": "expired", "updated_at": now.isoformat()}}
        )
        
        user = await db.users.find_one({"id": sub["user_id"]}, {"_id": 0})
        if user:
            await email_service.send_trial_expired(user["email"], user.get("name", "User"))
            logging.info(f"[TRIAL] Trial expired for {user['email']}")
    
    logging.info(f"[TRIAL] Processed {len(expiring_trials)} reminders, {len(expired_trials)} expirations")

async def send_weekly_seo_reports():
    """Send weekly SEO performance reports to all users"""
    logging.info("Sending weekly SEO reports...")
    
    if not RESEND_API_KEY:
        logging.error("No Resend API key for weekly reports")
        return
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    
    for user in users:
        user_id = user["id"]
        user_email = user.get("email")
        user_name = user.get("name", "User")
        
        if not user_email:
            continue
        
        try:
            # Get user's sites
            sites = await db.wordpress_configs.find(
                {"user_id": user_id},
                {"_id": 0, "app_password": 0}
            ).to_list(100)
            
            # Calculate stats for last 7 days
            seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
            
            # Get all articles from last 7 days
            recent_articles = await db.articles.find({
                "user_id": user_id,
                "created_at": {"$gte": seven_days_ago.isoformat()}
            }, {"_id": 0}).to_list(1000)
            
            # Count by article type
            article_types_count = {}
            for art in recent_articles:
                art_type = art.get("article_type", "general")
                article_types_count[art_type] = article_types_count.get(art_type, 0) + 1
            
            # Count with product links
            with_products = sum(1 for a in recent_articles if a.get("has_product_links"))
            
            # Count with trending keywords
            with_trending = sum(1 for a in recent_articles if a.get("has_trending_keywords"))
            
            # Published count
            published = sum(1 for a in recent_articles if a.get("status") == "published")
            
            # Average SEO score
            seo_scores = [a.get("seo_score", 0) for a in recent_articles if a.get("seo_score")]
            avg_seo_score = round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0
            
            # Build article types table
            types_html = ""
            type_names = {
                "review": "Review-uri",
                "ghid": "Ghiduri",
                "top": "Top/Liste",
                "comparatie": "Comparații",
                "sfaturi": "Sfaturi",
                "noutati": "Noutăți",
                "general": "Generale"
            }
            for art_type, count in article_types_count.items():
                types_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{type_names.get(art_type, art_type)}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{count}</td>
                </tr>
                """
            
            # Build sites stats
            sites_html = ""
            for site in sites:
                site_articles = [a for a in recent_articles if a.get("site_id") == site["id"]]
                site_published = sum(1 for a in site_articles if a.get("status") == "published")
                sites_html += f"""
                <tr>
                    <td style="padding: 8px; border-bottom: 1px solid #eee;">{site.get('site_name', site.get('site_url'))}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{len(site_articles)}</td>
                    <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">{site_published}</td>
                </tr>
                """
            
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #00E676; margin-bottom: 5px;">📊 Raport SEO Săptămânal</h1>
                <p style="color: #666; margin-top: 0;">Săptămâna {(datetime.now() - timedelta(days=7)).strftime('%d.%m')} - {datetime.now().strftime('%d.%m.%Y')}</p>
                
                <div style="background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); border-radius: 10px; padding: 20px; margin: 20px 0; color: white;">
                    <h2 style="margin-top: 0; color: #00E676;">Rezumat</h2>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;">
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #00E676;">{len(recent_articles)}</div>
                            <div style="font-size: 12px; color: #aaa;">Articole Generate</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #4CAF50;">{published}</div>
                            <div style="font-size: 12px; color: #aaa;">Publicate</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #FF9800;">{with_products}</div>
                            <div style="font-size: 12px; color: #aaa;">Cu Linkuri Produse</div>
                        </div>
                        <div style="background: rgba(255,255,255,0.1); padding: 15px; border-radius: 8px; text-align: center;">
                            <div style="font-size: 24px; font-weight: bold; color: #2196F3;">{avg_seo_score}</div>
                            <div style="font-size: 12px; color: #aaa;">Scor SEO Mediu</div>
                        </div>
                    </div>
                </div>
                
                <h3 style="color: #333; border-bottom: 2px solid #00E676; padding-bottom: 10px;">Tipuri de Articole</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Tip</th>
                        <th style="padding: 10px; text-align: center;">Număr</th>
                    </tr>
                    {types_html}
                </table>
                
                <h3 style="color: #333; border-bottom: 2px solid #00E676; padding-bottom: 10px;">Statistici per Site</h3>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                    <tr style="background: #f5f5f5;">
                        <th style="padding: 10px; text-align: left;">Site</th>
                        <th style="padding: 10px; text-align: center;">Generate</th>
                        <th style="padding: 10px; text-align: center;">Publicate</th>
                    </tr>
                    {sites_html}
                </table>
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <strong>💡 Sfat SEO:</strong> Articolele cu keywords trending ({with_trending} săptămâna aceasta) 
                    au șanse mai mari să atragă trafic organic în primele zile de la publicare.
                </div>
                
                <p style="color: #666; font-size: 12px; margin-top: 30px; text-align: center;">
                    Generat automat de SEO Automation Hub<br>
                    <a href="https://app.seamanshelp.com" style="color: #00E676;">Accesează Dashboard</a>
                </p>
            </div>
            """
            
            # Send email
            resend.api_key = RESEND_API_KEY
            await asyncio.to_thread(
                resend.Emails.send,
                {
                    "from": "SEO Automation <noreply@seamanshelp.com>",
                    "to": [user_email],
                    "subject": f"📊 Raport SEO Săptămânal - {len(recent_articles)} articole generate",
                    "html": email_html
                }
            )
            logging.info(f"Weekly report sent to {user_email}")
            
        except Exception as e:
            logging.error(f"Error sending weekly report to {user_email}: {e}")

async def recover_missed_automation_jobs():
    """
    Check for missed automation jobs today and run them.
    This runs at startup to catch any jobs that were missed due to server restart.
    """
    await asyncio.sleep(10)  # Wait for server to fully start
    
    logging.info("[RECOVERY] Checking for missed automation jobs today...")
    
    try:
        # Get current time in Romania
        romania_now = datetime.now(ROMANIA_TZ)
        today_start = romania_now.replace(hour=0, minute=0, second=0, microsecond=0)
        current_hour = romania_now.hour
        
        logging.info(f"[RECOVERY] Current time in Romania: {romania_now.strftime('%Y-%m-%d %H:%M')} (hour: {current_hour})")
        
        # Get all automation settings - must match scheduler query exactly
        all_settings = await db.site_automation_settings.find(
            {"enabled": True, "mode": "automatic"}  # Must be automatic mode AND enabled
        ).to_list(100)
        
        logging.info(f"[RECOVERY] Found {len(all_settings)} sites with automation enabled")
        
        for settings in all_settings:
            site_id = settings.get("site_id")
            user_id = settings.get("user_id")
            scheduled_hour = settings.get("generation_hour", 9)  # Use generation_hour, not publish_hour
            
            logging.info(f"[RECOVERY] Checking site {site_id}: scheduled_hour={scheduled_hour}, current_hour={current_hour}")
            
            # Skip if scheduled hour hasn't passed yet today
            if scheduled_hour >= current_hour:
                continue
            
            # Get site info
            site = await db.wordpress_configs.find_one(
                {"id": site_id},
                {"_id": 0, "site_name": 1, "site_url": 1}
            )
            site_name = site.get("site_name") or site.get("site_url", "Unknown") if site else "Unknown"
            
            # Check if article was already generated today for this site
            today_utc_start = today_start.astimezone(timezone.utc)
            
            existing_article = await db.articles.find_one({
                "site_id": site_id,
                "user_id": user_id,
                "auto_generated": True,
                "created_at": {"$gte": today_utc_start.isoformat()}
            })
            
            if existing_article:
                logging.info(f"[RECOVERY] Site {site_name}: Already has article today ('{existing_article.get('title', 'N/A')[:50]}' created at {existing_article.get('created_at')}), skipping")
                continue
            
            # Also check without auto_generated flag (in case it wasn't set)
            any_article_today = await db.articles.find_one({
                "site_id": site_id,
                "user_id": user_id,
                "created_at": {"$gte": today_utc_start.isoformat()}
            })
            
            if any_article_today:
                logging.info(f"[RECOVERY] Site {site_name}: Has non-auto article today, skipping")
                continue
            
            # This job was missed! Run it now
            logging.info(f"[RECOVERY] Site {site_name}: Missed job at {scheduled_hour}:00, running now...")
            
            try:
                await run_site_automation(site_id, user_id)
                logging.info(f"[RECOVERY] Site {site_name}: Successfully recovered missed job!")
            except Exception as job_err:
                logging.error(f"[RECOVERY] Site {site_name}: Error recovering job: {job_err}")
        
        logging.info("[RECOVERY] Finished checking for missed jobs")
        
    except Exception as e:
        logging.error(f"[RECOVERY] Error in recovery process: {e}")

async def search_new_backlink_opportunities():
    """Daily search for new free backlink opportunities + auto-generate outreach emails"""
    logging.info("[BACKLINKS] Running daily backlink opportunity search...")
    
    # Get all users with WordPress sites
    users = await db.users.find({}, {"_id": 0, "id": 1, "name": 1, "email": 1}).to_list(1000)
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        logging.error("[BACKLINKS] No LLM API key for backlink search")
        return
    
    for user in users:
        user_id = user["id"]
        user_name = user.get("name", "SEO Team")
        user_email = user.get("email", "")
        
        # Hardcoded outreach settings for Dan Potrocea
        if user_email == "danpo0446@gmail.com":
            outreach_position = "Administrator"
            outreach_phone = "0721578660"
            outreach_email = user_email
        else:
            # Get user's outreach settings from DB
            user_settings = await db.settings.find_one({"user_id": user_id}, {"_id": 0})
            outreach_position = user_settings.get("outreach_position", "Administrator") if user_settings else "Administrator"
            outreach_phone = user_settings.get("outreach_phone", "") if user_settings else ""
            outreach_email = user_settings.get("outreach_email", user_email) if user_settings else user_email
        
        # Get user's sites and their niches
        sites = await db.wordpress_configs.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "niche": 1, "site_url": 1, "site_name": 1}
        ).to_list(100)
        
        # Process each site individually (not just unique niches)
        for site_info in sites:
            niche = site_info.get("niche")
            if not niche:
                continue
                
            site_id = site_info.get("id")
            
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                
                # Get existing backlinks to avoid duplicates (per site)
                existing = await db.niche_backlinks.find(
                    {"niche": niche, "user_id": user_id},
                    {"_id": 0, "domain": 1}
                ).to_list(500)
                existing_domains = [b["domain"] for b in existing]
                
                response = await chat(
                    api_key=llm_api_key,
                    messages=[Message(role="user", content=f"""
                        Find 10 NEW free backlink opportunities for the niche: {niche}
                        
                        Focus on:
                        - Free guest posting sites
                        - Blog comment opportunities (dofollow)
                        - Free directories
                        - Resource pages accepting submissions
                        - Forums with signature links
                        
                        EXCLUDE these domains (already in database):
                        {', '.join(existing_domains[:50])}
                        
                        Return as JSON array with objects containing:
                        - domain: website domain
                        - type: Guest Post, Blog Comment, Directory, Resource Page, Forum
                        - da: estimated domain authority (20-90)
                        - pa: estimated page authority (20-90)
                        - price: 0 (only free)
                        - contact_info: email or contact form URL if known
                        - category: specific category within the niche
                        
                        Return ONLY the JSON array, no other text.
                    """)],
                    model="gpt-4o",
                    session_id=f"backlink-search-{uuid.uuid4()}"
                )
                
                # Parse response
                clean_response = response.strip()
                if clean_response.startswith("```"):
                    clean_response = clean_response.split("```")[1]
                    if clean_response.startswith("json"):
                        clean_response = clean_response[4:]
                
                new_backlinks = json.loads(clean_response)
                
                # Get user's best published article for this site
                best_article = await db.articles.find_one(
                    {"user_id": user_id, "site_id": site_id, "status": "published"},
                    {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "keywords": 1}
                )
                
                if not best_article:
                    # Get any published article
                    best_article = await db.articles.find_one(
                        {"user_id": user_id, "status": "published"},
                        {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1, "keywords": 1}
                    )
                
                # Save new backlinks and generate outreach emails
                saved_count = 0
                outreach_count = 0
                for bl in new_backlinks:
                    if bl.get("domain") and bl["domain"] not in existing_domains:
                        backlink_id = str(uuid.uuid4())
                        backlink_doc = {
                            "id": backlink_id,
                            "user_id": user_id,
                            "niche": niche,
                            "domain": bl.get("domain", ""),
                            "type": bl.get("type", "Directory"),
                            "da": bl.get("da", 30),
                            "pa": bl.get("pa", 30),
                            "price": 0,
                            "contact_info": bl.get("contact_info", ""),
                            "category": bl.get("category", niche),
                            "auto_discovered": True,
                            "discovered_at": datetime.now(timezone.utc).isoformat()
                        }
                        await db.niche_backlinks.insert_one(backlink_doc)
                        saved_count += 1
                        existing_domains.append(bl["domain"])
                        
                        # Auto-generate outreach email if we have contact info and an article
                        contact_info = bl.get("contact_info", "")
                        if contact_info and best_article and "@" in contact_info:
                            try:
                                # Detect target site language based on domain
                                target_domain = bl.get('domain', '').lower()
                                if target_domain.endswith('.ro'):
                                    target_language = "ROMÂNĂ"
                                    lang_note = ""
                                else:
                                    target_language = "ENGLEZĂ (English)"
                                    lang_note = "IMPORTANT: Articolul este în ROMÂNĂ, dar email-ul trebuie să fie în ENGLEZĂ deoarece site-ul țintă este internațional. Menționează că articolul este valoros pentru audiența vorbitoare de română."
                                
                                # Generate outreach email
                                email_response = await chat(
                                    api_key=llm_api_key,
                                    messages=[Message(role="user", content=f"""
                                        Generează un email profesional de outreach pentru a cere un backlink.
                                        
                                        REGULI CRITICE DE LIMBĂ:
                                        - Site-ul ȚINTĂ ({bl.get('domain')}) este: {target_language}
                                        - Articolul MEU este scris în: ROMÂNĂ
                                        - Email-ul TREBUIE scris în: {target_language}
                                        {lang_note}
                                        
                                        INFORMAȚII EXPEDITOR (folosește EXACT acestea, FĂRĂ placeholder-uri):
                                        - Nume complet: {user_name}
                                        - Poziție: {outreach_position}
                                        - Telefon: {outreach_phone}
                                        - Email: {outreach_email}
                                        - Website: {site_info.get('site_url', '')}
                                        - Nume site: {site_info.get('site_name', '')}
                                        
                                        Site-ul țintă: {bl.get('domain')}
                                        Tip website țintă: {bl.get('type', 'General')}
                                        
                                        Articol de promovat (în ROMÂNĂ):
                                        - Titlu: {best_article.get('title', '')}
                                        - URL: {best_article.get('wordpress_url', site_info.get('site_url', ''))}
                                        
                                        INSTRUCȚIUNI:
                                        1. Scrie ÎNTREGUL email în {target_language}
                                        2. Include un rezumat SCURT (2-3 propoziții) al articolului TRADUS în limba email-ului
                                        3. Subiectul email-ului trebuie să fie în aceeași limbă cu corpul email-ului
                                        4. NU folosi placeholder-uri precum [Nume], [Poziție], etc.
                                        5. Folosește DOAR informațiile reale de la expeditor
                                        6. Include linkul articolului natural în text
                                        7. Termină cu semnătura profesională folosind datele de contact reale
                                        
                                        Format JSON: {{"subject": "...", "body": "...", "detected_language": "..."}}
                                    """)],
                                    model="gpt-4o",
                                    session_id=f"outreach-auto-{uuid.uuid4()}"
                                )
                                
                                # Parse email
                                clean_email = email_response.strip()
                                if clean_email.startswith("```"):
                                    clean_email = clean_email.split("```")[1]
                                    if clean_email.startswith("json"):
                                        clean_email = clean_email[4:]
                                
                                email_data = json.loads(clean_email)
                                
                                # Save outreach draft (pending approval)
                                outreach_doc = {
                                    "id": str(uuid.uuid4()),
                                    "user_id": user_id,
                                    "backlink_id": backlink_id,
                                    "backlink_domain": bl.get("domain", ""),
                                    "site_id": site_id,
                                    "article_id": best_article.get("id"),
                                    "article_title": best_article.get("title", ""),
                                    "article_url": best_article.get("wordpress_url", ""),
                                    "contact_email": contact_info,
                                    "email_subject": email_data.get("subject", ""),
                                    "email_body": email_data.get("body", ""),
                                    "status": "pending_approval",  # Needs user approval
                                    "auto_generated": True,
                                    "created_at": datetime.now(timezone.utc).isoformat()
                                }
                                await db.backlink_outreach.insert_one(outreach_doc)
                                outreach_count += 1
                                
                            except Exception as email_err:
                                logging.error(f"[BACKLINKS] Error generating outreach email: {email_err}")
                
                logging.info(f"[BACKLINKS] Found {saved_count} new opportunities for {niche}, generated {outreach_count} outreach emails")
                
            except Exception as e:
                logging.error(f"[BACKLINKS] Error searching backlinks for {niche}: {e}")
    
    logging.info("[BACKLINKS] Daily backlink search completed")


async def run_daily_backlink_outreach():
    """Daily automation at 12:30: Send outreach emails to FREE opportunities (max 15/day/site)"""
    logging.info("[BACKLINK OUTREACH] Starting daily backlink outreach at 12:30 Romania time...")
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        logging.error("[BACKLINK OUTREACH] No LLM API key")
        return
    
    if not RESEND_API_KEY:
        logging.warning("[BACKLINK OUTREACH] No Resend API key - emails will be saved as drafts")
    
    # Get all users with WordPress sites
    users = await db.users.find({}, {"_id": 0, "id": 1, "email": 1, "name": 1}).to_list(1000)
    
    for user in users:
        user_id = user["id"]
        user_email = user.get("email", "")
        user_name = user.get("name", "SEO Team")
        
        # Get user's sites
        sites = await db.wordpress_configs.find(
            {"user_id": user_id},
            {"_id": 0, "id": 1, "site_url": 1, "site_name": 1, "niche": 1}
        ).to_list(100)
        
        for site in sites:
            site_id = site.get("id")
            site_name = site.get("site_name") or site.get("site_url", "Unknown")
            niche = site.get("niche")
            
            if not niche:
                logging.warning(f"[BACKLINK OUTREACH] Site {site_name} has no niche, skipping")
                continue
            
            logging.info(f"[BACKLINK OUTREACH] Processing site: {site_name} ({niche})")
            
            try:
                # Check how many emails sent today for this site
                today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                emails_sent_today = await db.backlink_outreach.count_documents({
                    "user_id": user_id,
                    "site_id": site_id,
                    "status": "sent",
                    "sent_at": {"$gte": today_start.isoformat()}
                })
                
                remaining_emails = 15 - emails_sent_today
                if remaining_emails <= 0:
                    logging.info(f"[BACKLINK OUTREACH] Site {site_name}: Already sent 15 emails today, skipping")
                    continue
                
                # Get FREE opportunities that haven't been contacted yet
                contacted_domains = await db.backlink_outreach.distinct(
                    "backlink_domain",
                    {"user_id": user_id, "site_id": site_id}
                )
                
                free_opportunities = await db.niche_backlinks.find({
                    "niche": niche,
                    "user_id": user_id,
                    "$or": [
                        {"is_free": True},
                        {"price": 0},
                        {"price": "Free"},
                        {"price": {"$regex": "free", "$options": "i"}}
                    ],
                    "domain": {"$nin": contacted_domains}
                }, {"_id": 0}).to_list(remaining_emails)
                
                if not free_opportunities:
                    logging.info(f"[BACKLINK OUTREACH] Site {site_name}: No new free opportunities to contact")
                    continue
                
                # Get different articles for variety
                articles = await db.articles.find(
                    {"user_id": user_id, "site_id": site_id, "status": "published"},
                    {"_id": 0, "id": 1, "title": 1, "wordpress_url": 1}
                ).sort("created_at", -1).to_list(20)
                
                if not articles:
                    logging.warning(f"[BACKLINK OUTREACH] Site {site_name}: No published articles for outreach")
                    continue
                
                emails_sent = 0
                for i, opportunity in enumerate(free_opportunities):
                    if emails_sent >= remaining_emails:
                        break
                    
                    # Use different articles (rotate through them)
                    article = articles[i % len(articles)]
                    article_url = article.get("wordpress_url") or f"{site.get('site_url', '')}"
                    
                    contact_email = opportunity.get("contact_info", "")
                    if not contact_email or "@" not in contact_email:
                        continue
                    
                    try:
                        # Generate personalized outreach email
                        email_response = await chat(
                            api_key=llm_api_key,
                            messages=[Message(role="user", content=f"""
                                Write a professional, personalized outreach email for a backlink request.
                                
                                My site: {site_name}
                                My article: "{article.get('title')}"
                                Article URL: {article_url}
                                Target site: {opportunity.get('domain')}
                                Opportunity type: {opportunity.get('type')}
                                
                                Make the email:
                                - Short and professional (max 150 words)
                                - Personalized to the target site
                                - Explain why a link would benefit their readers
                                - Include a clear call to action
                                
                                Return ONLY the email body, no subject line.
                            """)],
                            model="gpt-4o",
                            session_id=f"outreach-{uuid.uuid4()}"
                        )
                        
                        email_body = email_response
                        subject = f"Collaboration opportunity - {article.get('title', 'Guest Post')[:50]}"
                        
                        # Save outreach record
                        outreach_doc = {
                            "id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "site_id": site_id,
                            "backlink_domain": opportunity.get("domain"),
                            "contact_email": contact_email,
                            "article_id": article.get("id"),
                            "article_title": article.get("title"),
                            "article_url": article_url,
                            "email_subject": subject,
                            "email_body": email_body,
                            "status": "sent" if RESEND_API_KEY else "draft",
                            "sent_at": datetime.now(timezone.utc).isoformat() if RESEND_API_KEY else None,
                            "created_at": datetime.now(timezone.utc).isoformat()
                        }
                        
                        # Send the email if Resend is configured
                        if RESEND_API_KEY:
                            resend.Emails.send({
                                "from": f"{site_name} <{SENDER_EMAIL}>",
                                "to": [contact_email],
                                "subject": subject,
                                "html": f"""
                                    <div style="font-family: Arial, sans-serif; max-width: 600px;">
                                        {email_body.replace(chr(10), '<br>')}
                                        <br><br>
                                        <p style="color: #666; font-size: 12px;">
                                            Sent from {site_name}
                                        </p>
                                    </div>
                                """
                            })
                        
                        await db.backlink_outreach.insert_one(outreach_doc)
                        emails_sent += 1
                        logging.info(f"[BACKLINK OUTREACH] Site {site_name}: {'Sent' if RESEND_API_KEY else 'Saved'} email to {opportunity.get('domain')}")
                        
                        # Small delay between emails
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logging.error(f"[BACKLINK OUTREACH] Site {site_name}: Failed email to {opportunity.get('domain')} - {e}")
                
                logging.info(f"[BACKLINK OUTREACH] Site {site_name}: Processed {emails_sent} outreach emails")
                
            except Exception as e:
                logging.error(f"[BACKLINK OUTREACH] Site {site_name}: Error in outreach - {e}")
    
    logging.info("[BACKLINK OUTREACH] Daily backlink outreach completed")


async def send_monthly_seo_reports():
    """Send monthly SEO performance reports to all users"""
    logging.info("Sending monthly SEO reports...")
    
    if not RESEND_API_KEY:
        logging.error("No Resend API key for monthly reports")
        return
    
    users = await db.users.find({}, {"_id": 0}).to_list(1000)
    
    for user in users:
        user_id = user["id"]
        user_email = user.get("email")
        user_name = user.get("name", "User")
        
        if not user_email:
            continue
        
        try:
            # Get user's sites
            sites = await db.wordpress_configs.find(
                {"user_id": user_id},
                {"_id": 0, "app_password": 0}
            ).to_list(100)
            
            # Calculate stats for last 30 days
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            
            # Articles generated
            articles_count = await db.articles.count_documents({
                "user_id": user_id,
                "created_at": {"$gte": thirty_days_ago.isoformat()}
            })
            
            # Auto-generated articles
            auto_articles = await db.articles.count_documents({
                "user_id": user_id,
                "auto_generated": True,
                "created_at": {"$gte": thirty_days_ago.isoformat()}
            })
            
            # Published articles
            published = await db.articles.count_documents({
                "user_id": user_id,
                "status": "published",
                "created_at": {"$gte": thirty_days_ago.isoformat()}
            })
            
            # Outreach stats
            outreach_sent = await db.backlink_outreach.count_documents({
                "user_id": user_id,
                "status": "sent"
            })
            
            outreach_responded = await db.backlink_outreach.count_documents({
                "user_id": user_id,
                "status": "responded"
            })
            
            # Build report email
            sites_html = ""
            for site in sites:
                site_articles = await db.articles.count_documents({
                    "user_id": user_id,
                    "site_id": site["id"],
                    "created_at": {"$gte": thirty_days_ago.isoformat()}
                })
                sites_html += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #eee;">{site.get('site_name', site.get('site_url'))}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #eee; text-align: center;">{site_articles}</td>
                </tr>
                """
            
            email_html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #00E676; margin-bottom: 5px;">📊 Raport SEO Lunar</h1>
                <p style="color: #888; margin-top: 0;">Perioada: Ultima lună</p>
                
                <div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); padding: 20px; border-radius: 12px; margin: 20px 0;">
                    <h2 style="color: #fff; margin-top: 0;">Salut, {user_name}! 👋</h2>
                    <p style="color: #ccc;">Iată cum a performat strategia ta SEO luna aceasta:</p>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 20px 0;">
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 32px; font-weight: bold; color: #00E676; margin: 0;">{articles_count}</p>
                        <p style="color: #666; margin: 5px 0 0 0;">Articole Generate</p>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 32px; font-weight: bold; color: #2196F3; margin: 0;">{auto_articles}</p>
                        <p style="color: #666; margin: 5px 0 0 0;">Articole Automate</p>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 32px; font-weight: bold; color: #9C27B0; margin: 0;">{published}</p>
                        <p style="color: #666; margin: 5px 0 0 0;">Publicate pe WordPress</p>
                    </div>
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center;">
                        <p style="font-size: 32px; font-weight: bold; color: #FF9800; margin: 0;">{outreach_sent}</p>
                        <p style="color: #666; margin: 5px 0 0 0;">Outreach Trimise</p>
                    </div>
                </div>
                
                {f'''
                <h3 style="color: #333; margin-top: 30px;">📈 Performanță per Site</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="background: #f8f9fa;">
                            <th style="padding: 10px; text-align: left;">Site</th>
                            <th style="padding: 10px; text-align: center;">Articole</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sites_html}
                    </tbody>
                </table>
                ''' if sites else ''}
                
                <div style="background: #e8f5e9; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h4 style="color: #2e7d32; margin: 0 0 10px 0;">💡 Recomandări pentru luna viitoare:</h4>
                    <ul style="color: #333; margin: 0; padding-left: 20px;">
                        <li>Continuă să publici constant pentru a construi autoritate</li>
                        <li>Răspunde la outreach-urile care au primit răspuns</li>
                        <li>Verifică Google Search Console pentru cuvinte cheie noi</li>
                    </ul>
                </div>
                
                <p style="color: #888; font-size: 12px; margin-top: 30px; text-align: center;">
                    Generat automat de SEO Automation Platform
                </p>
            </div>
            """
            
            resend.Emails.send({
                "from": f"SEO Automation <{SENDER_EMAIL}>",
                "to": [user_email],
                "subject": f"📊 Raport SEO Lunar - {articles_count} articole generate",
                "html": email_html
            })
            
            logging.info(f"Sent monthly report to {user_email}")
            
        except Exception as e:
            logging.error(f"Error sending report to {user.get('email')}: {e}")
    
    logging.info("Monthly SEO reports completed")

async def auto_generate_keywords_for_all_sites():
    """Daily automatic keyword generation for all sites - in Romanian, with sync to main keywords"""
    logging.info("[KEYWORDS] Starting daily keyword generation for all sites...")
    
    llm_api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not llm_api_key:
        logging.error("[KEYWORDS] No LLM API key for keyword generation")
        return
    
    # Get all sites with niches
    sites = await db.wordpress_configs.find(
        {"niche": {"$exists": True, "$ne": ""}},
        {"_id": 0, "id": 1, "niche": 1, "site_name": 1, "site_url": 1, "user_id": 1, "auto_keywords": 1}
    ).to_list(1000)
    
    total_synced = 0
    
    for site in sites:
        try:
            niche = site.get("niche", "")
            user_id = site.get("user_id")
            site_id = site.get("id")
            
            if not niche or not user_id:
                continue
            
            existing_keywords = site.get("auto_keywords", [])
            
            # Generate new keywords in Romanian
            response = await chat(
                api_key=llm_api_key,
                messages=[Message(role="user", content=f"""
                    Generează 15 cuvinte cheie SEO relevante pentru nișa: {niche}
                    
                    Cerințe:
                    - Cuvinte cheie în limba ROMÂNĂ
                    - Mix de short-tail și long-tail keywords
                    - Relevante pentru piața din România
                    - Focus pe intenția de căutare a utilizatorilor români
                    - Include variații și sinonime
                    
                    Cuvinte cheie existente (evită duplicatele): {', '.join(existing_keywords[:20])}
                    
                    Returnează DOAR un array JSON cu cuvintele cheie, fără alt text.
                    Exemplu: ["cuvânt cheie 1", "cuvânt cheie 2"]
                """)],
                model="gpt-4o",
                session_id=f"keywords-auto-{uuid.uuid4()}"
            )
            
            # Parse response
            clean_response = response.strip()
            if clean_response.startswith("```"):
                clean_response = clean_response.split("```")[1]
                if clean_response.startswith("json"):
                    clean_response = clean_response[4:]
            
            new_keywords = json.loads(clean_response)
            
            # Merge with existing, remove duplicates
            all_keywords = list(set(existing_keywords + new_keywords))
            
            # Update site config
            await db.wordpress_configs.update_one(
                {"id": site_id},
                {"$set": {
                    "auto_keywords": all_keywords,
                    "keywords_updated_at": datetime.now(timezone.utc).isoformat()
                }}
            )
            
            # Sync new keywords to main keywords collection
            synced_count = 0
            for kw in new_keywords:
                # Check if keyword already exists for this site
                existing = await db.keywords.find_one({
                    "keyword": kw,
                    "user_id": user_id,
                    "site_id": site_id
                })
                
                if not existing:
                    keyword_doc = {
                        "id": str(uuid.uuid4()),
                        "keyword": kw,
                        "volume": 1000,  # Default estimated volume
                        "difficulty": 50,  # Default difficulty
                        "cpc": 1.0,  # Default CPC
                        "trend": "stable",
                        "user_id": user_id,
                        "niche": niche,
                        "site_id": site_id,
                        "source": "daily_auto",  # Mark as daily auto-generated
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    await db.keywords.insert_one(keyword_doc)
                    synced_count += 1
            
            total_synced += synced_count
            logging.info(f"[KEYWORDS] Generated {len(new_keywords)} new keywords for {site.get('site_name', site_id)}, synced {synced_count} to main collection")
            
        except Exception as e:
            logging.error(f"[KEYWORDS] Error generating keywords for site {site.get('id')}: {e}")
    
    logging.info(f"[KEYWORDS] Daily keyword generation completed. Total synced to main collection: {total_synced}")

@app.on_event("shutdown")
async def shutdown_db_client():
    scheduler.shutdown()
    client.close()
