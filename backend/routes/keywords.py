"""Keywords Routes - CRUD operations only (research rămâne în server.py pentru LLM)"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/keywords", tags=["Keywords"])


class KeywordResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    keyword: str
    volume: int = 0
    difficulty: int = 0
    cpc: float = 0.0
    trend: str = "stable"
    site_id: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[str] = None


@router.get("", response_model=List[KeywordResponse])
async def get_keywords(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all keywords for user"""
    db = get_database()
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
    keywords = await db.keywords.find(query, {"_id": 0}).to_list(1000)
    return [KeywordResponse(**k) for k in keywords]


@router.delete("/{keyword_id}")
async def delete_keyword(keyword_id: str, user: dict = Depends(get_current_user)):
    """Delete a keyword"""
    db = get_database()
    result = await db.keywords.delete_one({"id": keyword_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Keyword not found")
    return {"message": "Keyword deleted"}
