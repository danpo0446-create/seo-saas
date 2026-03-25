"""
Authentication utilities for SaaS application
"""
import os
import jwt
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'seo-automation-secret-key-2024')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Security
security = HTTPBearer()

# Lazy database connection
_client = None
_db = None

def get_db():
    """Get database connection (lazy loading)"""
    global _client, _db
    if _client is None:
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        _client = AsyncIOMotorClient(mongo_url)
        _db = _client[os.environ.get('DB_NAME', 'seo_saas')]
    return _db

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user"""
    try:
        db = get_db()
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
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")