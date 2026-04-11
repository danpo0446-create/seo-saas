"""Reports Routes"""
from fastapi import APIRouter, Depends
from datetime import datetime, timezone, timedelta

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/weekly")
async def get_weekly_report(user: dict = Depends(get_current_user)):
    """Get weekly performance report"""
    db = get_database()
    user_id = user["id"]
    
    # Get user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate stats for last 7 days
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    
    # Get all articles from last 7 days
    recent_articles = await db.articles.find({
        "user_id": user_id,
        "created_at": {"$gte": seven_days_ago.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    # Count by article type
    article_types_count = {}
    for art in recent_articles:
        art_type = art.get("article_type", "general")
        article_types_count[art_type] = article_types_count.get(art_type, 0) + 1
    
    # Count with product links
    with_products = sum(1 for a in recent_articles if a.get("has_product_links"))
    
    # Count with trending keywords
    with_trending = sum(1 for a in recent_articles if a.get("has_trending_keywords"))
    
    # Published count
    published = sum(1 for a in recent_articles if a.get("status") == "published")
    
    # Draft count
    drafts = sum(1 for a in recent_articles if a.get("status") == "draft")
    
    # Average SEO score
    seo_scores = [a.get("seo_score", 0) for a in recent_articles if a.get("seo_score")]
    avg_seo_score = round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0
    
    # Average word count
    word_counts = [a.get("word_count", 0) for a in recent_articles if a.get("word_count")]
    avg_word_count = round(sum(word_counts) / len(word_counts)) if word_counts else 0
    
    # Stats per site
    sites_stats = []
    for site in sites:
        site_articles = [a for a in recent_articles if a.get("site_id") == site["id"]]
        site_published = sum(1 for a in site_articles if a.get("status") == "published")
        site_drafts = sum(1 for a in site_articles if a.get("status") == "draft")
        sites_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name") or site.get("site_url"),
            "articles_generated": len(site_articles),
            "articles_published": site_published,
            "articles_draft": site_drafts
        })
    
    # Daily breakdown
    daily_stats = {}
    for art in recent_articles:
        created = art.get("created_at", "")[:10]  # Get date part
        if created not in daily_stats:
            daily_stats[created] = {"generated": 0, "published": 0}
        daily_stats[created]["generated"] += 1
        if art.get("status") == "published":
            daily_stats[created]["published"] += 1
    
    return {
        "period": {
            "start": seven_days_ago.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "days": 7
        },
        "summary": {
            "total_articles": len(recent_articles),
            "published": published,
            "drafts": drafts,
            "with_product_links": with_products,
            "with_trending_keywords": with_trending,
            "avg_seo_score": avg_seo_score,
            "avg_word_count": avg_word_count
        },
        "article_types": article_types_count,
        "sites_stats": sites_stats,
        "daily_stats": daily_stats
    }


@router.get("/monthly")
async def get_monthly_report(user: dict = Depends(get_current_user)):
    """Get monthly performance report"""
    db = get_database()
    user_id = user["id"]
    
    # Get user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user_id},
        {"_id": 0, "app_password": 0}
    ).to_list(100)
    
    # Calculate stats for last 30 days
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
    # Get all articles from last 30 days
    recent_articles = await db.articles.find({
        "user_id": user_id,
        "created_at": {"$gte": thirty_days_ago.isoformat()}
    }, {"_id": 0}).to_list(1000)
    
    # Count by article type
    article_types_count = {}
    for art in recent_articles:
        art_type = art.get("article_type", "general")
        article_types_count[art_type] = article_types_count.get(art_type, 0) + 1
    
    # Counts
    with_products = sum(1 for a in recent_articles if a.get("has_product_links"))
    with_trending = sum(1 for a in recent_articles if a.get("has_trending_keywords"))
    published = sum(1 for a in recent_articles if a.get("status") == "published")
    drafts = sum(1 for a in recent_articles if a.get("status") == "draft")
    auto_generated = sum(1 for a in recent_articles if a.get("auto_generated"))
    
    # Averages
    seo_scores = [a.get("seo_score", 0) for a in recent_articles if a.get("seo_score")]
    avg_seo_score = round(sum(seo_scores) / len(seo_scores), 1) if seo_scores else 0
    word_counts = [a.get("word_count", 0) for a in recent_articles if a.get("word_count")]
    avg_word_count = round(sum(word_counts) / len(word_counts)) if word_counts else 0
    
    # Outreach stats
    outreach_sent = await db.backlink_outreach.count_documents({
        "user_id": user_id,
        "status": "sent"
    })
    outreach_pending = await db.backlink_outreach.count_documents({
        "user_id": user_id,
        "status": "pending_approval"
    })
    
    # Stats per site
    sites_stats = []
    for site in sites:
        site_articles = [a for a in recent_articles if a.get("site_id") == site["id"]]
        site_published = sum(1 for a in site_articles if a.get("status") == "published")
        sites_stats.append({
            "site_id": site["id"],
            "site_name": site.get("site_name") or site.get("site_url"),
            "articles_generated": len(site_articles),
            "articles_published": site_published
        })
    
    # Weekly breakdown
    weekly_stats = {}
    for art in recent_articles:
        created = art.get("created_at", "")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                week_num = dt.isocalendar()[1]
                week_key = f"Săpt. {week_num}"
                if week_key not in weekly_stats:
                    weekly_stats[week_key] = {"generated": 0, "published": 0}
                weekly_stats[week_key]["generated"] += 1
                if art.get("status") == "published":
                    weekly_stats[week_key]["published"] += 1
            except:
                pass
    
    return {
        "period": {
            "start": thirty_days_ago.isoformat(),
            "end": datetime.now(timezone.utc).isoformat(),
            "days": 30
        },
        "summary": {
            "total_articles": len(recent_articles),
            "auto_generated": auto_generated,
            "published": published,
            "drafts": drafts,
            "with_product_links": with_products,
            "with_trending_keywords": with_trending,
            "avg_seo_score": avg_seo_score,
            "avg_word_count": avg_word_count
        },
        "outreach": {
            "emails_sent": outreach_sent,
            "pending_approval": outreach_pending
        },
        "article_types": article_types_count,
        "sites_stats": sites_stats,
        "weekly_stats": weekly_stats
    }
