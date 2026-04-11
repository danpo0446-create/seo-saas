"""Routes package - Modular route handlers for SEO Automation Platform"""
from .auth import router as auth_router, get_current_user, security
from .pagespeed import router as pagespeed_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router
from .notifications import router as notifications_router
from .trends import router as trends_router
from .templates import router as templates_router

__all__ = [
    'auth_router', 'get_current_user', 'security',
    'pagespeed_router', 'dashboard_router', 'settings_router',
    'notifications_router', 'trends_router', 'templates_router'
]
