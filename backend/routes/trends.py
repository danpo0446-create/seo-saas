"""Google Trends Routes"""
from fastapi import APIRouter, Depends
from typing import List
import logging

from routes.auth import get_current_user
from google_trends_service import (
    GoogleTrendsService, 
    get_trending_topics_for_niche, 
    score_keywords_by_trend
)

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("/trending")
async def get_trending_searches(user: dict = Depends(get_current_user)):
    """Get current trending searches in Romania"""
    try:
        trends = GoogleTrendsService()
        trending = trends.get_trending_searches()
        return {"trending": trending, "count": len(trending)}
    except Exception as e:
        logging.error(f"[TRENDS] Error: {e}")
        return {"trending": [], "count": 0, "error": str(e)}


@router.get("/niche/{niche}")
async def get_trends_for_niche(niche: str, user: dict = Depends(get_current_user)):
    """Get trending topics relevant to a specific niche"""
    try:
        result = get_trending_topics_for_niche(niche)
        return result
    except Exception as e:
        logging.error(f"[TRENDS] Error for niche '{niche}': {e}")
        return {"niche": niche, "error": str(e), "topic_ideas": []}


@router.post("/score-keywords")
async def score_keywords(keywords: List[str], user: dict = Depends(get_current_user)):
    """Score keywords by their trending interest"""
    try:
        if not keywords:
            return {"scored_keywords": []}
        scored = score_keywords_by_trend(keywords[:20])  # Limit to 20
        return {"scored_keywords": scored}
    except Exception as e:
        logging.error(f"[TRENDS] Error scoring keywords: {e}")
        return {"scored_keywords": [], "error": str(e)}


@router.get("/related/{keyword}")
async def get_related_queries(keyword: str, user: dict = Depends(get_current_user)):
    """Get related queries for a keyword"""
    try:
        trends = GoogleTrendsService()
        related = trends.get_related_queries(keyword)
        suggestions = trends.get_suggestions(keyword)
        return {
            "keyword": keyword,
            "top_queries": related.get("top", []),
            "rising_queries": related.get("rising", []),
            "suggestions": suggestions
        }
    except Exception as e:
        logging.error(f"[TRENDS] Error for keyword '{keyword}': {e}")
        return {"keyword": keyword, "error": str(e)}
