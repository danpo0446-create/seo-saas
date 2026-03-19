"""
Authentication Routes
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timezone
import bcrypt
import jwt
import uuid
import os

from models import UserCreate, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])
security = HTTPBearer()

SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

def get_db():
    """Get database instance - will be set by main server"""
    from server import db
    return db

def create_token(user_id: str) -> str:
    """Create JWT token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc).timestamp() + 86400 * 7  # 7 days
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from token"""
    db = get_db()
    payload = verify_token(credentials.credentials)
    user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    db = get_db()
    
    # Check if user exists
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = bcrypt.hashpw(user_data.password.encode(), bcrypt.gensalt())
    
    # Create user
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password": hashed_password.decode(),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    # Create token
    token = create_token(user_id)
    
    return {
        "token": token,
        "user": UserResponse(
            id=user_id,
            email=user_data.email,
            name=user_data.name,
            created_at=user_doc["created_at"]
        )
    }

@router.post("/login")
async def login(user_data: UserLogin):
    """Login user"""
    db = get_db()
    
    # Find user
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not bcrypt.checkpw(user_data.password.encode(), user["password"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create token
    token = create_token(user["id"])
    
    return {
        "token": token,
        "user": UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"]
        )
    }

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(**user)
