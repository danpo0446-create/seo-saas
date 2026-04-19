#!/usr/bin/env python3
"""Script to fix SEO scores for existing articles"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

async def update_seo_scores():
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.seo_saas
    
    # Find ALL articles and recalculate SEO score
    articles = await db.articles.find({}).to_list(1000)
    print(f"Found {len(articles)} total articles")
    
    updated = 0
    for article in articles:
        keywords = article.get("keywords", [])
        word_count = article.get("word_count", 0)
        
        # Calculate SEO score
        seo_score = 50  # Base
        if word_count >= 1000:
            seo_score += 15
        elif word_count >= 500:
            seo_score += 10
        if len(keywords) >= 5:
            seo_score += 10
        elif len(keywords) >= 3:
            seo_score += 5
        if article.get("status") == "published":
            seo_score += 10
        
        seo_score = min(95, seo_score)
        
        # Update article
        result = await db.articles.update_one(
            {"id": article["id"]},
            {"$set": {"seo_score": seo_score}}
        )
        if result.modified_count > 0:
            updated += 1
            print(f"Updated: {article.get('title', 'Unknown')[:50]} -> SEO: {seo_score}")
    
    print(f"\nDone! Updated {updated} articles.")

if __name__ == "__main__":
    asyncio.run(update_seo_scores())
