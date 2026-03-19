"""
WooCommerce Integration Service
Fetches products from WooCommerce stores for SEO article generation
"""

import logging
from woocommerce import API
from typing import List, Dict, Optional
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

# Cache for products (expires after 1 hour)
_products_cache = {}
_cache_expiry = {}
CACHE_TTL = 3600  # 1 hour

class WooCommerceService:
    def __init__(self, site_url: str, consumer_key: str, consumer_secret: str):
        """Initialize WooCommerce API connection"""
        # Ensure URL has https and no trailing slash
        clean_url = site_url.rstrip('/')
        if not clean_url.startswith('http'):
            clean_url = f"https://{clean_url}"
        
        self.site_url = clean_url
        self.wcapi = API(
            url=clean_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            version="wc/v3",
            timeout=30
        )
    
    def get_products(self, per_page: int = 50, category: str = None, in_stock: bool = True) -> List[Dict]:
        """
        Fetch products from WooCommerce store
        
        Args:
            per_page: Number of products to fetch (max 100)
            category: Filter by category slug
            in_stock: Only return products in stock
        
        Returns:
            List of product dictionaries
        """
        cache_key = f"{self.site_url}_{per_page}_{category}_{in_stock}"
        
        # Check cache
        if cache_key in _products_cache:
            if datetime.now() < _cache_expiry.get(cache_key, datetime.min):
                logging.info(f"[WOOCOMMERCE] Returning cached products for {self.site_url}")
                return _products_cache[cache_key]
        
        try:
            params = {
                "per_page": min(per_page, 100),
                "status": "publish",
                "orderby": "popularity",
                "order": "desc"
            }
            
            if in_stock:
                params["stock_status"] = "instock"
            
            if category:
                params["category"] = category
            
            response = self.wcapi.get("products", params=params)
            
            if response.status_code == 200:
                products = response.json()
                
                # Process and simplify product data
                simplified = []
                for p in products:
                    simplified.append({
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "slug": p.get("slug"),
                        "url": p.get("permalink"),
                        "price": p.get("price"),
                        "regular_price": p.get("regular_price"),
                        "sale_price": p.get("sale_price"),
                        "on_sale": p.get("on_sale", False),
                        "description": p.get("short_description", "")[:200],
                        "categories": [c.get("name") for c in p.get("categories", [])],
                        "image": p.get("images", [{}])[0].get("src") if p.get("images") else None,
                        "stock_status": p.get("stock_status"),
                        "average_rating": p.get("average_rating"),
                        "rating_count": p.get("rating_count", 0)
                    })
                
                # Cache the results
                _products_cache[cache_key] = simplified
                _cache_expiry[cache_key] = datetime.now() + timedelta(seconds=CACHE_TTL)
                
                logging.info(f"[WOOCOMMERCE] Fetched {len(simplified)} products from {self.site_url}")
                return simplified
            else:
                logging.error(f"[WOOCOMMERCE] Error fetching products: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logging.error(f"[WOOCOMMERCE] Exception fetching products from {self.site_url}: {e}")
            return []
    
    def get_categories(self) -> List[Dict]:
        """Fetch product categories"""
        try:
            response = self.wcapi.get("products/categories", params={"per_page": 100})
            
            if response.status_code == 200:
                categories = response.json()
                return [{"id": c["id"], "name": c["name"], "slug": c["slug"], "count": c["count"]} 
                        for c in categories if c.get("count", 0) > 0]
            return []
        except Exception as e:
            logging.error(f"[WOOCOMMERCE] Error fetching categories: {e}")
            return []
    
    def get_featured_products(self, limit: int = 10) -> List[Dict]:
        """Get featured/popular products for article linking"""
        try:
            response = self.wcapi.get("products", params={
                "per_page": limit,
                "featured": True,
                "status": "publish",
                "stock_status": "instock"
            })
            
            if response.status_code == 200:
                products = response.json()
                return [{
                    "name": p.get("name"),
                    "url": p.get("permalink"),
                    "price": p.get("price"),
                    "on_sale": p.get("on_sale", False)
                } for p in products]
            return []
        except Exception as e:
            logging.error(f"[WOOCOMMERCE] Error fetching featured products: {e}")
            return []
    
    def get_sale_products(self, limit: int = 10) -> List[Dict]:
        """Get products currently on sale"""
        try:
            response = self.wcapi.get("products", params={
                "per_page": limit,
                "on_sale": True,
                "status": "publish",
                "stock_status": "instock"
            })
            
            if response.status_code == 200:
                products = response.json()
                return [{
                    "name": p.get("name"),
                    "url": p.get("permalink"),
                    "price": p.get("price"),
                    "regular_price": p.get("regular_price"),
                    "sale_price": p.get("sale_price")
                } for p in products]
            return []
        except Exception as e:
            logging.error(f"[WOOCOMMERCE] Error fetching sale products: {e}")
            return []


def get_woocommerce_service(site_url: str, consumer_key: str, consumer_secret: str) -> Optional[WooCommerceService]:
    """Factory function to create WooCommerce service"""
    if not all([site_url, consumer_key, consumer_secret]):
        return None
    return WooCommerceService(site_url, consumer_key, consumer_secret)


async def get_products_for_article(db, site_id: str, user_id: str, limit: int = 10) -> List[Dict]:
    """
    Get products from WooCommerce for a specific site
    Used in article generation to include product links
    """
    # Get site config with WooCommerce credentials
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user_id},
        {"_id": 0, "site_url": 1, "wc_consumer_key": 1, "wc_consumer_secret": 1}
    )
    
    if not site:
        return []
    
    consumer_key = site.get("wc_consumer_key")
    consumer_secret = site.get("wc_consumer_secret")
    
    if not consumer_key or not consumer_secret:
        logging.info(f"[WOOCOMMERCE] No WooCommerce credentials for site {site_id}")
        return []
    
    wc = get_woocommerce_service(site.get("site_url"), consumer_key, consumer_secret)
    if not wc:
        return []
    
    # Run sync function in executor to not block async
    loop = asyncio.get_event_loop()
    products = await loop.run_in_executor(None, lambda: wc.get_products(per_page=limit))
    
    return products
