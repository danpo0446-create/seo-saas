"""Dashboard Routes"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta
from typing import Optional
import asyncio

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get dashboard statistics"""
    db = get_database()
    user_id = user["id"]
    
    query = {"user_id": user_id}
    if site_id:
        query["site_id"] = site_id
    
    # Run queries in parallel
    articles_count, published_count, keywords_count, calendar_count, backlink_requests = await asyncio.gather(
        db.articles.count_documents(query),
        db.articles.count_documents({**query, "status": "published"}),
        db.keywords.count_documents(query),
        db.calendar.count_documents(query),
        db.backlink_requests.count_documents({"user_id": user_id})
    )
    
    return {
        "total_articles": articles_count,
        "published_articles": published_count,
        "draft_articles": articles_count - published_count,
        "total_keywords": keywords_count,
        "scheduled_posts": calendar_count,
        "backlink_requests": backlink_requests,
        "monthly_quota": 30,
        "used_quota": min(articles_count, 30)
    }


@router.get("/all")
async def get_dashboard_all(site_id: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Combined endpoint for all dashboard data - reduces API calls from 5 to 1"""
    db = get_database()
    user_id = user["id"]
    
    query = {"user_id": user_id}
    if site_id:
        query["site_id"] = site_id
    
    # Run all queries in parallel using asyncio.gather
    articles_count_task = db.articles.count_documents(query)
    published_count_task = db.articles.count_documents({**query, "status": "published"})
    keywords_count_task = db.keywords.count_documents(query)
    calendar_count_task = db.calendar.count_documents(query)
    backlink_requests_task = db.backlink_requests.count_documents({"user_id": user_id})
    sites_task = db.wordpress_configs.find({"user_id": user_id}, {"_id": 0, "app_password": 0}).to_list(100)
    automation_task = db.site_automation_settings.find({"user_id": user_id}, {"_id": 0}).to_list(100)
    
    # Parallel execution
    (articles_count, published_count, keywords_count, calendar_count, 
     backlink_requests, sites, automation_settings) = await asyncio.gather(
        articles_count_task, published_count_task, keywords_count_task, calendar_count_task,
        backlink_requests_task, sites_task, automation_task
    )
    
    # Build automation data
    automation_map = {a["site_id"]: a for a in automation_settings}
    automation_sites = []
    for site in sites:
        automation_sites.append({
            "site": site,
            "automation": automation_map.get(site["id"], {"enabled": False, "mode": "manual"})
        })
    
    # Get recent history (last 30 articles)
    history = await db.articles.find(
        {"user_id": user_id},
        {"_id": 0, "id": 1, "title": 1, "site_id": 1, "created_at": 1, "status": 1}
    ).sort("created_at", -1).limit(30).to_list(30)
    
    # Calculate weekly articles
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_articles = sum(1 for h in history if h.get("created_at") and 
                         datetime.fromisoformat(h["created_at"].replace('Z', '+00:00')) > one_week_ago)
    
    # Stats per site
    site_stats = []
    for site in sites:
        site_articles = await db.articles.count_documents({"user_id": user_id, "site_id": site["id"]})
        site_published = await db.articles.count_documents({"user_id": user_id, "site_id": site["id"], "status": "published"})
        site_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name", site.get("site_url", "")),
            "total": site_articles,
            "published": site_published
        })
    
    return {
        "stats": {
            "total_articles": articles_count,
            "published_articles": published_count,
            "draft_articles": articles_count - published_count,
            "total_keywords": keywords_count,
            "scheduled_posts": calendar_count,
            "backlink_requests": backlink_requests,
            "monthly_quota": 30,
            "used_quota": min(articles_count, 30)
        },
        "automation": {
            "sites": automation_sites,
            "totalSites": len(sites),
            "weeklyArticles": weekly_articles,
            "totalAutoArticles": len(history)
        },
        "site_stats": {
            "stats": site_stats,
            "total_monthly": weekly_articles * 4,
            "total_all_time": articles_count
        },
        "history": history[:10]  # Last 10 for quick display
    }
