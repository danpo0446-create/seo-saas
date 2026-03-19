"""
Subscription Plans Configuration for SEO Automation SaaS
"""
from typing import Dict, Any

# Annual discount percentage
ANNUAL_DISCOUNT = 20  # 20% discount for annual billing

# Plan definitions
PLANS: Dict[str, Dict[str, Any]] = {
    "free": {
        "id": "free",
        "name": "Free Trial",
        "price_eur": 0,
        "price_annual_eur": 0,
        "sites_limit": 1,
        "articles_limit": 5,
        "features": [
            "1 site WordPress",
            "5 articole/lună",
            "Generare AI de bază",
            "Dashboard simplu"
        ],
        "stripe_price_id": None,
        "stripe_price_id_annual": None
    },
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_eur": 19,
        "price_annual_eur": 182,  # 19 * 12 * 0.8 = 182.4 rounded
        "sites_limit": 1,
        "articles_limit": 15,
        "features": [
            "1 site WordPress",
            "15 articole/lună",
            "Generare AI articole",
            "Keyword research",
            "Calendar editorial",
            "Publicare automată"
        ],
        "stripe_price_id": "price_starter_monthly",
        "stripe_price_id_annual": "price_starter_annual"
    },
    "pro": {
        "id": "pro",
        "name": "Pro",
        "price_eur": 49,
        "price_annual_eur": 470,  # 49 * 12 * 0.8 = 470.4 rounded
        "sites_limit": 5,
        "articles_limit": 50,
        "features": [
            "5 site-uri WordPress",
            "50 articole/lună",
            "Toate funcțiile Starter",
            "Google Search Console",
            "Backlinks Manager",
            "Rapoarte avansate",
            "Email notificări"
        ],
        "stripe_price_id": "price_pro_monthly",
        "stripe_price_id_annual": "price_pro_annual"
    },
    "agency": {
        "id": "agency",
        "name": "Agency",
        "price_eur": 99,
        "price_annual_eur": 950,  # 99 * 12 * 0.8 = 950.4 rounded
        "sites_limit": 20,
        "articles_limit": 200,
        "features": [
            "20 site-uri WordPress",
            "200 articole/lună",
            "Toate funcțiile Pro",
            "WooCommerce integrare",
            "Social Media posting",
            "Audit SEO tehnic",
            "Business Analysis AI",
            "Suport prioritar"
        ],
        "stripe_price_id": "price_agency_monthly",
        "stripe_price_id_annual": "price_agency_annual"
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise",
        "price_eur": 199,
        "price_annual_eur": 1910,  # 199 * 12 * 0.8 = 1910.4 rounded
        "sites_limit": -1,  # Unlimited
        "articles_limit": -1,  # Unlimited
        "features": [
            "Site-uri nelimitate",
            "Articole nelimitate",
            "Toate funcțiile Agency",
            "API access",
            "White-label complet",
            "Suport dedicat 24/7",
            "Training personalizat"
        ],
        "stripe_price_id": "price_enterprise_monthly",
        "stripe_price_id_annual": "price_enterprise_annual"
    }
}

# Trial configuration
TRIAL_CONFIG = {
    "duration_days": 7,
    "plan_features": "pro",  # Trial users get Pro features
    "sites_limit": 5,
    "articles_limit": 10,
    "reminder_day": 5  # Send reminder on day 5
}

def get_plan(plan_id: str) -> Dict[str, Any]:
    """Get plan configuration by ID"""
    return PLANS.get(plan_id, PLANS["free"])

def get_all_plans() -> Dict[str, Dict[str, Any]]:
    """Get all plans"""
    return PLANS

def is_feature_allowed(plan_id: str, feature: str) -> bool:
    """Check if a feature is allowed for a plan"""
    plan = get_plan(plan_id)
    # Enterprise has all features
    if plan_id == "enterprise":
        return True
    # Check feature hierarchy
    feature_requirements = {
        "gsc": ["pro", "agency", "enterprise"],
        "backlinks": ["pro", "agency", "enterprise"],
        "woocommerce": ["agency", "enterprise"],
        "social_media": ["agency", "enterprise"],
        "technical_audit": ["agency", "enterprise"],
        "business_analysis": ["agency", "enterprise"],
        "api_access": ["enterprise"],
        "white_label": ["enterprise"]
    }
    allowed_plans = feature_requirements.get(feature, list(PLANS.keys()))
    return plan_id in allowed_plans
