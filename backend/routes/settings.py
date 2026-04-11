"""Settings Routes"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List
import uuid

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/settings", tags=["Settings"])


class SettingsUpdate(BaseModel):
    company_name: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    email_notifications: Optional[bool] = True
    outreach_position: Optional[str] = None
    outreach_phone: Optional[str] = None
    outreach_email: Optional[str] = None


class SettingsResponse(BaseModel):
    id: str
    company_name: str
    logo_url: str
    primary_color: str
    email_notifications: bool
    user_id: str
    outreach_position: str = ""
    outreach_phone: str = ""
    outreach_email: str = ""

    class Config:
        extra = "ignore"


@router.get("", response_model=SettingsResponse)
async def get_settings(user: dict = Depends(get_current_user)):
    """Get user settings"""
    db = get_database()
    settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
    if not settings:
        settings = {
            "id": str(uuid.uuid4()),
            "user_id": user["id"],
            "company_name": "My SEO Agency",
            "logo_url": "",
            "primary_color": "#00E676",
            "email_notifications": True,
            "outreach_position": "",
            "outreach_phone": "",
            "outreach_email": ""
        }
        await db.settings.insert_one(settings)
    return SettingsResponse(**settings)


@router.patch("", response_model=SettingsResponse)
async def update_settings(updates: SettingsUpdate, user: dict = Depends(get_current_user)):
    """Update user settings"""
    db = get_database()
    update_data = updates.model_dump(exclude_unset=True)
    if update_data:
        await db.settings.update_one(
            {"user_id": user["id"]},
            {"$set": update_data}
        )
    settings = await db.settings.find_one({"user_id": user["id"]}, {"_id": 0})
    return SettingsResponse(**settings)
