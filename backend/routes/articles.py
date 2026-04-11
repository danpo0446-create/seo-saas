"""Articles Routes - CRUD operations only (generate rămâne în server.py)"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
from typing import Optional, List
import logging

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/articles", tags=["Articles"])


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    status: Optional[str] = None


class ArticleResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    content: str
    keywords: List[str]
    status: str
    site_id: Optional[str] = None
    user_id: str
    word_count: int = 0
    created_at: str
    updated_at: Optional[str] = None
    published_url: Optional[str] = None
    wordpress_post_id: Optional[int] = None


@router.get("", response_model=List[ArticleResponse])
async def get_articles(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get all articles for user"""
    db = get_database()
    query = {"user_id": user["id"]}
    if site_id:
        query["site_id"] = site_id
        logging.info(f"[ARTICLES] Filtering by site_id: {site_id}")
    else:
        logging.info(f"[ARTICLES] No site_id filter, returning all articles")
    articles = await db.articles.find(query, {"_id": 0}).to_list(1000)
    logging.info(f"[ARTICLES] Returning {len(articles)} articles")
    return [ArticleResponse(**a) for a in articles]


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: str, user: dict = Depends(get_current_user)):
    """Get a specific article"""
    db = get_database()
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return ArticleResponse(**article)


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(article_id: str, updates: ArticleUpdate, user: dict = Depends(get_current_user)):
    """Update article title, content, keywords or status"""
    db = get_database()
    article = await db.articles.find_one({"id": article_id, "user_id": user["id"]}, {"_id": 0})
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    update_data = {}
    if updates.title is not None:
        update_data["title"] = updates.title
    if updates.content is not None:
        update_data["content"] = updates.content
        update_data["word_count"] = len(updates.content.split())
    if updates.keywords is not None:
        update_data["keywords"] = updates.keywords
    if updates.status is not None:
        update_data["status"] = updates.status
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.articles.update_one(
            {"id": article_id, "user_id": user["id"]},
            {"$set": update_data}
        )
    
    updated_article = await db.articles.find_one({"id": article_id}, {"_id": 0})
    return ArticleResponse(**updated_article)


@router.patch("/{article_id}/status")
async def update_article_status(article_id: str, status: str, user: dict = Depends(get_current_user)):
    """Update article status only"""
    db = get_database()
    result = await db.articles.update_one(
        {"id": article_id, "user_id": user["id"]},
        {"$set": {"status": status}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Status updated"}


@router.delete("/{article_id}")
async def delete_article(article_id: str, user: dict = Depends(get_current_user)):
    """Delete an article"""
    db = get_database()
    result = await db.articles.delete_one({"id": article_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"message": "Article deleted"}
