"""Calendar Routes - CRUD operations only (generate-90-days rămâne în server.py pentru LLM)"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
import uuid

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/calendar", tags=["Calendar"])


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


@router.post("", response_model=CalendarResponse)
async def create_calendar_entry(entry: CalendarEntry, user: dict = Depends(get_current_user)):
    """Create a new calendar entry"""
    db = get_database()
    entry_id = str(uuid.uuid4())
    entry_doc = {
        "id": entry_id,
        "title": entry.title,
        "keywords": entry.keywords,
        "scheduled_date": entry.scheduled_date,
        "status": entry.status,
        "article_id": None,
        "user_id": user["id"],
        "site_id": entry.site_id
    }
    await db.calendar.insert_one(entry_doc)
    return CalendarResponse(**entry_doc)


@router.get("", response_model=List[CalendarResponse])
async def get_calendar(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all calendar entries"""
    db = get_database()
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    entries = await db.calendar.find(query, {"_id": 0}).to_list(1000)
    return [CalendarResponse(**e) for e in entries]


@router.patch("/{entry_id}")
async def update_calendar_entry(entry_id: str, entry: CalendarEntry, user: dict = Depends(get_current_user)):
    """Update a calendar entry"""
    db = get_database()
    update_data = entry.model_dump(exclude_unset=True)
    result = await db.calendar.update_one(
        {"id": entry_id, "user_id": user["id"]},
        {"$set": update_data}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry updated"}


@router.delete("/{entry_id}")
async def delete_calendar_entry(entry_id: str, user: dict = Depends(get_current_user)):
    """Delete a calendar entry"""
    db = get_database()
    result = await db.calendar.delete_one({"id": entry_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"message": "Entry deleted"}
