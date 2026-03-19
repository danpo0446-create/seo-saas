"""
Pydantic Models for SaaS functionality
"""
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

# Subscription Models
class SubscriptionCreate(BaseModel):
    plan: str = "free"

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    plan: str
    status: str  # active, trialing, canceled, past_due, expired
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    trial_ends_at: Optional[str] = None
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    sites_limit: int
    articles_limit: int
    articles_used_this_month: int = 0
    sites_used: int = 0
    created_at: str
    updated_at: Optional[str] = None

class SubscriptionUsage(BaseModel):
    plan: str
    plan_name: str
    status: str
    sites_limit: int
    sites_used: int
    articles_limit: int
    articles_used: int
    trial_ends_at: Optional[str] = None
    days_remaining: Optional[int] = None
    can_add_site: bool
    can_generate_article: bool

# BYOAK Models (Bring Your Own API Keys)
class UserApiKeysUpdate(BaseModel):
    openai_key: Optional[str] = None
    gemini_key: Optional[str] = None
    resend_key: Optional[str] = None
    pexels_key: Optional[str] = None

class UserApiKeysResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    has_openai_key: bool = False
    has_gemini_key: bool = False
    has_resend_key: bool = False
    has_pexels_key: bool = False
    updated_at: Optional[str] = None

# Stripe Models
class CreateCheckoutRequest(BaseModel):
    plan: str
    origin_url: str
    billing_period: str = "monthly"  # "monthly" or "annual"

class CheckoutResponse(BaseModel):
    url: str
    session_id: str

class BillingPortalRequest(BaseModel):
    origin_url: str

class BillingPortalResponse(BaseModel):
    url: str

# Invoice Models
class InvoiceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    invoice_number: str
    user_id: str
    plan_name: str
    billing_period: str
    amount: float
    currency: str
    status: str
    created_at: str
    pdf_generated: bool = False

# Payment Transaction Model
class PaymentTransaction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    session_id: str
    plan: str
    amount: float
    currency: str = "eur"
    status: str  # initiated, paid, failed, expired
    payment_status: str
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: Optional[str] = None
