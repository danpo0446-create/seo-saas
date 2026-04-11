"""Routes package - Modular route handlers for SEO Automation Platform"""
from .auth import router as auth_router, get_current_user, security
from .pagespeed import router as pagespeed_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router
from .notifications import router as notifications_router
from .trends import router as trends_router
from .templates import router as templates_router
from .articles import router as articles_router
from .keywords import router as keywords_router
from .calendar import router as calendar_router
from .reports import router as reports_router

__all__ = [
    'auth_router', 'get_current_user', 'security',
    'pagespeed_router', 'dashboard_router', 'settings_router',
    'notifications_router', 'trends_router', 'templates_router',
    'articles_router', 'keywords_router', 'calendar_router', 'reports_router'
]
