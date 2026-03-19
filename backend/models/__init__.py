"""
Pydantic Models for SEO Automation Platform
"""
from pydantic import BaseModel, ConfigDict, EmailStr
from typing import List, Optional

# ============ AUTH MODELS ============

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

# ============ ARTICLE MODELS ============

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

# ============ KEYWORD MODELS ============

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

# ============ CALENDAR MODELS ============

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

# ============ BACKLINK MODELS ============

class BacklinkSite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    domain: str
    da: int
    pa: int
    category: str
    status: str
    price: float

# ============ WORDPRESS MODELS ============

class WordPressConfig(BaseModel):
    site_url: str
    site_name: str = ""
    username: str
    app_password: str
    niche: str = ""
    notification_email: str = ""

class WordPressConfigUpdate(BaseModel):
    site_url: Optional[str] = None
    site_name: Optional[str] = None
    username: Optional[str] = None
    app_password: Optional[str] = None
    niche: Optional[str] = None
    notification_email: Optional[str] = None

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

# ============ AUTOMATION MODELS ============

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

class SiteAutomationSettings(BaseModel):
    site_id: str
    mode: str = "manual"  # "manual" or "automatic"
    enabled: bool = False
    paused: bool = False
    generation_hour: int = 9
    frequency: str = "daily"  # "daily", "every_2_days", "every_3_days", "weekly"
    article_length: str = "medium"  # "short", "medium", "long"
    publish_mode: str = "draft"  # "draft" or "publish"
    email_notification: bool = True
    include_product_links: bool = False
    product_links_source: str = ""
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
    articles_generated: int = 0

# ============ WEB 2.0 MODELS ============

class Web2Site(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    url: str
    category: str
    da: int
    allow_links: bool
    registration_required: bool
    difficulty: str

class Web2Link(BaseModel):
    site_id: str
    target_url: str
    anchor_text: str
    article_title: Optional[str] = None
    notes: Optional[str] = None

class Web2LinkResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    site_id: str
    site_name: str
    target_url: str
    anchor_text: str
    article_title: Optional[str] = None
    notes: Optional[str] = None
    status: str
    created_at: str
