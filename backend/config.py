"""
Configuration and shared utilities for the SEO Automation Platform
"""
import os
from datetime import datetime, timezone
import pytz

# Database
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'seo_automation')

# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# API Keys
RESEND_API_KEY = os.environ.get('RESEND_API_KEY')
PEXELS_API_KEY = os.environ.get('PEXELS_API_KEY')
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Email
SENDER_EMAIL = "SEO Platform <noreply@seamanshelp.com>"

# Timezone
ROMANIA_TZ = pytz.timezone('Europe/Bucharest')

# OAuth - Google
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI')

# OAuth - Facebook (set in .env)
FACEBOOK_APP_ID = os.environ.get('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.environ.get('FACEBOOK_APP_SECRET', '')

# OAuth - LinkedIn (set in .env)
LINKEDIN_CLIENT_ID = os.environ.get('LINKEDIN_CLIENT_ID', '')
LINKEDIN_CLIENT_SECRET = os.environ.get('LINKEDIN_CLIENT_SECRET', '')

# App URL for OAuth callbacks (auto-detect from FRONTEND_URL or use default)
APP_URL = os.environ.get('APP_URL') or os.environ.get('FRONTEND_URL', 'https://app.seamanshelp.com')

# Niche categories for article generation
NICHE_CATEGORIES = {
    "maritime": ["Shipping News", "Seafarer Life", "Maritime Regulations", "Ship Technology", 
                 "Port Operations", "Maritime Safety", "Crew Management", "Maritime Training",
                 "Vessel Maintenance", "Maritime Careers"],
    "baby": ["Baby Care", "Newborn Essentials", "Toddler Development", "Baby Health",
             "Nursery Ideas", "Baby Products", "Parenting Tips", "Baby Sleep",
             "Baby Nutrition", "Baby Safety"],
    "jobs": ["Job Search Tips", "Career Development", "Resume Writing", "Interview Tips",
             "Workplace Skills", "Remote Work", "Job Market Trends", "Professional Growth",
             "Industry Careers", "Salary Negotiation"],
    "fashion": ["Fashion Trends", "Style Tips", "Wardrobe Essentials", "Seasonal Fashion",
                "Fashion Accessories", "Sustainable Fashion", "Fashion History", "Designer Spotlight",
                "Street Style", "Fashion Events"],
    "ecommerce": ["Online Shopping", "E-commerce Trends", "Product Reviews", "Shopping Guides",
                  "Deals and Discounts", "Customer Experience", "E-commerce Tips", "Online Marketplaces",
                  "Product Comparisons", "Shopping Safety"],
    "default": ["Industry News", "Expert Tips", "How-To Guides", "Product Reviews",
                "Trends and Insights", "Best Practices", "Case Studies", "Resources",
                "FAQs", "Updates"]
}

def get_current_year() -> int:
    """Get current year - always use this instead of hardcoding"""
    return datetime.now().year

def get_now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)

def get_now_romania() -> datetime:
    """Get current Romania datetime"""
    return datetime.now(ROMANIA_TZ)
