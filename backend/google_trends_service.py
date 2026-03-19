"""
Google Trends Integration Service
Fetches trending topics and related queries for SEO content generation
"""

import logging
from pytrends.request import TrendReq
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import time
import random

# Cache for trends (expires after 6 hours)
_trends_cache = {}
_cache_expiry = {}
CACHE_TTL = 21600  # 6 hours

# Niche-specific seed keywords for Romania
NICHE_SEED_KEYWORDS = {
    "bebeluși": ["bebeluș", "copii", "părinți", "produse bebeluși", "îngrijire bebeluși", "jucării copii", "hăinuțe bebeluși"],
    "modă feminină": ["rochii", "modă femei", "haine femei", "ținute elegante", "fashion", "stiluri vestimentare"],
    "lenjerie": ["lenjerie intimă", "lenjerie femei", "chiloți", "sutien", "pijamale femei"],
    "maritim": ["joburi maritime", "carieră maritimă", "navigație", "marinar", "ofițer naval", "croazieră"],
    "general": ["tendințe 2026", "sfaturi", "ghid complet", "top produse"]
}

class GoogleTrendsService:
    def __init__(self, geo: str = "RO", language: str = "ro"):
        """Initialize Google Trends for Romania"""
        self.geo = geo
        self.hl = language
        self.pytrends = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize PyTrends connection with retries"""
        try:
            self.pytrends = TrendReq(hl=self.hl, tz=120, timeout=(10, 25))
            logging.info("[TRENDS] Google Trends connection initialized")
        except Exception as e:
            logging.error(f"[TRENDS] Failed to initialize: {e}")
            self.pytrends = None
    
    def get_trending_searches(self) -> List[str]:
        """Get today's trending searches in Romania"""
        cache_key = f"trending_{self.geo}"
        
        # Check cache
        if cache_key in _trends_cache:
            if datetime.now() < _cache_expiry.get(cache_key, datetime.min):
                logging.info("[TRENDS] Returning cached trending searches")
                return _trends_cache[cache_key]
        
        if not self.pytrends:
            self._init_connection()
            if not self.pytrends:
                return []
        
        try:
            trending = self.pytrends.trending_searches(pn='romania')
            if trending is not None and not trending.empty:
                results = trending[0].tolist()[:20]
                
                # Cache results
                _trends_cache[cache_key] = results
                _cache_expiry[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL)
                
                logging.info(f"[TRENDS] Found {len(results)} trending searches")
                return results
            return []
        except Exception as e:
            logging.error(f"[TRENDS] Error fetching trending searches: {e}")
            return []
    
    def get_related_queries(self, keyword: str) -> Dict[str, List[str]]:
        """Get related queries for a keyword"""
        cache_key = f"related_{keyword}_{self.geo}"
        
        # Check cache
        if cache_key in _trends_cache:
            if datetime.now() < _cache_expiry.get(cache_key, datetime.min):
                return _trends_cache[cache_key]
        
        if not self.pytrends:
            self._init_connection()
            if not self.pytrends:
                return {"top": [], "rising": []}
        
        try:
            self.pytrends.build_payload([keyword], geo=self.geo, timeframe='today 3-m')
            time.sleep(random.uniform(1, 2))  # Rate limiting
            
            related = self.pytrends.related_queries()
            
            result = {"top": [], "rising": []}
            
            if keyword in related:
                if related[keyword]['top'] is not None:
                    result["top"] = related[keyword]['top']['query'].tolist()[:10]
                if related[keyword]['rising'] is not None:
                    result["rising"] = related[keyword]['rising']['query'].tolist()[:10]
            
            # Cache results
            _trends_cache[cache_key] = result
            _cache_expiry[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL)
            
            logging.info(f"[TRENDS] Related queries for '{keyword}': {len(result['top'])} top, {len(result['rising'])} rising")
            return result
            
        except Exception as e:
            logging.error(f"[TRENDS] Error fetching related queries for '{keyword}': {e}")
            return {"top": [], "rising": []}
    
    def get_interest_over_time(self, keywords: List[str], timeframe: str = 'today 3-m') -> Dict[str, int]:
        """Get interest score for keywords (for scoring/ranking)"""
        if not self.pytrends or not keywords:
            return {}
        
        try:
            # Limit to 5 keywords per request (Google Trends limit)
            keywords = keywords[:5]
            self.pytrends.build_payload(keywords, geo=self.geo, timeframe=timeframe)
            time.sleep(random.uniform(1, 2))  # Rate limiting
            
            interest = self.pytrends.interest_over_time()
            
            if interest is not None and not interest.empty:
                # Get average interest for each keyword
                scores = {}
                for kw in keywords:
                    if kw in interest.columns:
                        scores[kw] = int(interest[kw].mean())
                return scores
            return {}
            
        except Exception as e:
            logging.error(f"[TRENDS] Error fetching interest over time: {e}")
            return {}
    
    def get_suggestions(self, keyword: str) -> List[str]:
        """Get keyword suggestions from Google Trends"""
        if not self.pytrends:
            self._init_connection()
            if not self.pytrends:
                return []
        
        try:
            suggestions = self.pytrends.suggestions(keyword)
            if suggestions:
                return [s['title'] for s in suggestions[:10]]
            return []
        except Exception as e:
            logging.error(f"[TRENDS] Error fetching suggestions for '{keyword}': {e}")
            return []


def get_trending_topics_for_niche(niche: str) -> Dict[str, any]:
    """
    Get trending topics relevant to a niche
    Returns dict with trending keywords and topic suggestions
    """
    trends = GoogleTrendsService()
    
    # Determine seed keywords based on niche
    niche_lower = niche.lower()
    seed_keywords = NICHE_SEED_KEYWORDS.get("general", [])
    
    for niche_key, keywords in NICHE_SEED_KEYWORDS.items():
        if niche_key in niche_lower or niche_lower in niche_key:
            seed_keywords = keywords
            break
    
    # Also check for partial matches
    if "bebel" in niche_lower or "copil" in niche_lower or "părinti" in niche_lower:
        seed_keywords = NICHE_SEED_KEYWORDS["bebeluși"]
    elif "modă" in niche_lower or "rochii" in niche_lower or "feminin" in niche_lower:
        seed_keywords = NICHE_SEED_KEYWORDS["modă feminină"]
    elif "lenjer" in niche_lower or "intim" in niche_lower:
        seed_keywords = NICHE_SEED_KEYWORDS["lenjerie"]
    elif "marit" in niche_lower or "naval" in niche_lower or "navigat" in niche_lower:
        seed_keywords = NICHE_SEED_KEYWORDS["maritim"]
    
    result = {
        "niche": niche,
        "seed_keywords": seed_keywords,
        "trending_general": [],
        "related_queries": [],
        "suggestions": [],
        "topic_ideas": []
    }
    
    try:
        # Get general trending searches in Romania
        result["trending_general"] = trends.get_trending_searches()[:10]
        
        # Get related queries for seed keywords
        all_related = []
        for kw in seed_keywords[:3]:  # Limit to avoid rate limiting
            related = trends.get_related_queries(kw)
            all_related.extend(related.get("top", [])[:5])
            all_related.extend(related.get("rising", [])[:5])
            time.sleep(0.5)  # Rate limiting
        
        result["related_queries"] = list(set(all_related))[:15]
        
        # Get suggestions for main keyword
        if seed_keywords:
            result["suggestions"] = trends.get_suggestions(seed_keywords[0])
        
        # Combine all for topic ideas
        topic_ideas = []
        topic_ideas.extend(result["related_queries"][:5])
        topic_ideas.extend([f"{kw} {datetime.now().year}" for kw in seed_keywords[:3]])
        topic_ideas.extend([f"Ghid {kw}" for kw in seed_keywords[:2]])
        topic_ideas.extend([f"Top {kw}" for kw in seed_keywords[:2]])
        
        result["topic_ideas"] = list(set(topic_ideas))[:15]
        
    except Exception as e:
        logging.error(f"[TRENDS] Error getting trending topics for niche '{niche}': {e}")
    
    return result


def score_keywords_by_trend(keywords: List[str]) -> List[Dict[str, any]]:
    """
    Score keywords by their trending interest
    Returns sorted list with scores
    """
    if not keywords:
        return []
    
    trends = GoogleTrendsService()
    
    # Process in batches of 5 (Google limit)
    all_scores = {}
    for i in range(0, len(keywords), 5):
        batch = keywords[i:i+5]
        scores = trends.get_interest_over_time(batch)
        all_scores.update(scores)
        time.sleep(1)  # Rate limiting between batches
    
    # Create scored list
    scored = []
    for kw in keywords:
        scored.append({
            "keyword": kw,
            "trend_score": all_scores.get(kw, 0),
            "is_trending": all_scores.get(kw, 0) > 50
        })
    
    # Sort by score descending
    scored.sort(key=lambda x: x["trend_score"], reverse=True)
    
    return scored
