"""Routes package - Modular route handlers for SEO Automation Platform"""
from .auth import router as auth_router, get_current_user, security
from .pagespeed import router as pagespeed_router
from .dashboard import router as dashboard_router
from .settings import router as settings_router

# calendar_router și keywords_router nu sunt activate deoarece au dependențe circulare
# cu get_user_llm_key din server.py. Aceste rute rămân în server.py pentru moment.

__all__ = [
    'auth_router', 'get_current_user', 'security',
    'pagespeed_router', 'dashboard_router', 'settings_router'
]
