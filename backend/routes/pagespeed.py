"""PageSpeed Insights Routes"""
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime, timezone, timedelta
import asyncio
import uuid
import os
import logging

from database import get_database
from routes.auth import get_current_user

router = APIRouter(prefix="/pagespeed", tags=["PageSpeed"])

PAGESPEED_API_KEY = os.environ.get('PAGESPEED_API_KEY', '')


@router.get("/analyze/{site_id}")
async def analyze_pagespeed(site_id: str, user: dict = Depends(get_current_user)):
    """Analyze site with Google PageSpeed Insights API"""
    import json as json_module
    
    db = get_database()
    
    # Get site
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").rstrip("/")
    if not site_url:
        raise HTTPException(status_code=400, detail="Site URL not configured")
    
    if not PAGESPEED_API_KEY:
        raise HTTPException(status_code=400, detail="PageSpeed API key not configured")
    
    results = {"mobile": None, "desktop": None}
    
    for strategy in ["mobile", "desktop"]:
        try:
            # Use curl with -4 flag to force IPv4
            api_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={site_url}&strategy={strategy}&key={PAGESPEED_API_KEY}&category=performance&category=seo&category=accessibility&category=best-practices"
            
            logging.info(f"[PAGESPEED] Running curl for {strategy}...")
            
            # Use asyncio subprocess
            process = await asyncio.create_subprocess_exec(
                "curl", "-4", "-s", "-m", "90", api_url,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=95)
            
            if process.returncode != 0:
                logging.error(f"[PAGESPEED] curl failed: {stderr.decode()}")
                continue
            
            response_text = stdout.decode()
            logging.info(f"[PAGESPEED] Got response for {strategy}, length: {len(response_text)}")
            
            data = json_module.loads(response_text)
            
            # Check for errors
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                logging.error(f"[PAGESPEED] API error for {strategy}: {error_msg}")
                if data["error"].get("code") == 403:
                    raise HTTPException(status_code=403, detail=f"PageSpeed API: {error_msg[:100]}")
                continue
            
            logging.info(f"[PAGESPEED] Raw API response keys: {list(data.keys())}")
            
            lighthouse = data.get("lighthouseResult", {})
            categories = lighthouse.get("categories", {})
            audits = lighthouse.get("audits", {})
            
            logging.info(f"[PAGESPEED] Categories found: {list(categories.keys())}")
            
            # Extract scores (multiply by 100)
            scores = {
                "performance": int((categories.get("performance", {}).get("score") or 0) * 100),
                "seo": int((categories.get("seo", {}).get("score") or 0) * 100),
                "accessibility": int((categories.get("accessibility", {}).get("score") or 0) * 100),
                "best_practices": int((categories.get("best-practices", {}).get("score") or 0) * 100)
            }
            
            logging.info(f"[PAGESPEED] Extracted scores for {strategy}: {scores}")
            
            # Extract recommendations
            recommendations = []
            auto_fixable_ids = {
                "render-blocking-resources": {"fix_type": "minify", "plugin": "Autoptimize"},
                "uses-optimized-images": {"fix_type": "images", "plugin": "ShortPixel"},
                "offscreen-images": {"fix_type": "lazyload", "plugin": "Lazy Load by WP Rocket"},
                "uses-long-cache-ttl": {"fix_type": "cache", "plugin": "LiteSpeed Cache"},
                "efficient-animated-content": {"fix_type": "images", "plugin": "ShortPixel"},
                "uses-responsive-images": {"fix_type": "images", "plugin": "ShortPixel"},
                "unminified-css": {"fix_type": "minify", "plugin": "Autoptimize"},
                "unminified-javascript": {"fix_type": "minify", "plugin": "Autoptimize"},
                "unused-css-rules": {"fix_type": "minify", "plugin": "Autoptimize"},
                "unused-javascript": {"fix_type": "minify", "plugin": "Autoptimize"},
            }
            
            for audit_id, audit in audits.items():
                if audit.get("score") is not None and audit.get("score") < 1:
                    fix_info = auto_fixable_ids.get(audit_id, {})
                    recommendations.append({
                        "id": audit_id,
                        "title": audit.get("title", ""),
                        "description": audit.get("description", ""),
                        "score": int((audit.get("score") or 0) * 100),
                        "savings_ms": audit.get("numericValue", 0),
                        "display_value": audit.get("displayValue", ""),
                        "auto_fixable": audit_id in auto_fixable_ids,
                        "fix_type": fix_info.get("fix_type"),
                        "plugin": fix_info.get("plugin")
                    })
            
            # Sort by impact (lower score = higher priority)
            recommendations.sort(key=lambda x: (x["score"], -x.get("savings_ms", 0)))
            
            results[strategy] = {
                "scores": scores,
                "recommendations": recommendations[:20]  # Top 20 recommendations
            }
            
        except asyncio.TimeoutError:
            logging.error(f"PageSpeed API timeout for {strategy}")
            continue
        except HTTPException:
            raise
        except Exception as e:
            logging.error(f"PageSpeed API error ({strategy}): {str(e)}")
            continue
    
    if not results["mobile"] and not results["desktop"]:
        raise HTTPException(status_code=500, detail="Failed to analyze site with PageSpeed API")
    
    # Save to history
    history_doc = {
        "id": str(uuid.uuid4()),
        "site_id": site_id,
        "user_id": user["id"],
        "site_url": site_url,
        "mobile": results["mobile"],
        "desktop": results["desktop"],
        "analyzed_at": datetime.now(timezone.utc).isoformat()
    }
    await db.pagespeed_history.insert_one(history_doc)
    
    return {
        "site_id": site_id,
        "site_url": site_url,
        "mobile": results["mobile"],
        "desktop": results["desktop"],
        "analyzed_at": history_doc["analyzed_at"]
    }


@router.get("/history/{site_id}")
async def get_pagespeed_history(site_id: str, days: int = 30, user: dict = Depends(get_current_user)):
    """Get PageSpeed analysis history for a site"""
    db = get_database()
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    
    history = await db.pagespeed_history.find(
        {
            "site_id": site_id,
            "user_id": user["id"],
            "analyzed_at": {"$gte": cutoff.isoformat()}
        },
        {"_id": 0}
    ).sort("analyzed_at", 1).to_list(1000)
    
    return {"history": history, "days": days}


@router.get("/latest/{site_id}")
async def get_latest_pagespeed(site_id: str, user: dict = Depends(get_current_user)):
    """Get latest PageSpeed analysis for a site"""
    db = get_database()
    latest = await db.pagespeed_history.find_one(
        {"site_id": site_id, "user_id": user["id"]},
        {"_id": 0},
        sort=[("analyzed_at", -1)]
    )
    
    if not latest:
        return {"latest": None}
    
    return {"latest": latest}


@router.get("/all-sites")
async def get_all_sites_pagespeed(user: dict = Depends(get_current_user)):
    """Get latest PageSpeed analysis for all user's sites"""
    db = get_database()
    
    # Get all user's sites
    sites = await db.wordpress_configs.find(
        {"user_id": user["id"]},
        {"_id": 0, "id": 1, "site_name": 1, "site_url": 1}
    ).to_list(100)
    
    results = []
    for site in sites:
        latest = await db.pagespeed_history.find_one(
            {"site_id": site["id"], "user_id": user["id"]},
            {"_id": 0},
            sort=[("analyzed_at", -1)]
        )
        results.append({
            "site_id": site["id"],
            "site_name": site.get("site_name") or site.get("site_url", "Unknown"),
            "site_url": site.get("site_url", ""),
            "latest_analysis": latest
        })
    
    return {"sites": results}


@router.post("/optimize/{site_id}")
async def optimize_pagespeed(
    site_id: str, 
    fix_type: str = Query("all", description="cache|images|minify|lazyload|all"),
    user: dict = Depends(get_current_user)
):
    """Install WordPress optimization plugins via REST API"""
    import httpx
    import base64
    
    db = get_database()
    
    # Get site with WordPress credentials
    site = await db.wordpress_configs.find_one(
        {"id": site_id, "user_id": user["id"]},
        {"_id": 0}
    )
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    site_url = site.get("site_url", "").rstrip("/")
    username = site.get("username")
    app_password = site.get("app_password")
    
    if not username or not app_password:
        raise HTTPException(status_code=400, detail="WordPress credentials not configured for this site")
    
    # Define plugins by fix type
    plugins_map = {
        "cache": [{"slug": "litespeed-cache", "name": "LiteSpeed Cache"}],
        "images": [{"slug": "shortpixel-image-optimiser", "name": "ShortPixel Image Optimizer"}],
        "minify": [{"slug": "autoptimize", "name": "Autoptimize"}],
        "lazyload": [{"slug": "rocket-lazy-load", "name": "Lazy Load by WP Rocket"}]
    }
    
    if fix_type == "all":
        plugins_to_install = []
        for plist in plugins_map.values():
            plugins_to_install.extend(plist)
    else:
        plugins_to_install = plugins_map.get(fix_type, [])
    
    if not plugins_to_install:
        raise HTTPException(status_code=400, detail=f"Invalid fix_type: {fix_type}")
    
    # Create auth header
    auth_string = f"{username}:{app_password}"
    auth_bytes = base64.b64encode(auth_string.encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_bytes}",
        "Content-Type": "application/json"
    }
    
    results = []
    async with httpx.AsyncClient(timeout=30.0) as client:
        for plugin in plugins_to_install:
            try:
                # Try to install plugin
                install_url = f"{site_url}/wp-json/wp/v2/plugins"
                response = await client.post(
                    install_url,
                    headers=headers,
                    json={"slug": plugin["slug"], "status": "active"}
                )
                
                if response.status_code in [200, 201]:
                    results.append({"plugin": plugin["name"], "status": "installed", "success": True})
                elif response.status_code == 400 and "already installed" in response.text.lower():
                    # Plugin already exists, try to activate
                    activate_url = f"{site_url}/wp-json/wp/v2/plugins/{plugin['slug']}/{plugin['slug']}"
                    activate_response = await client.put(
                        activate_url,
                        headers=headers,
                        json={"status": "active"}
                    )
                    if activate_response.status_code == 200:
                        results.append({"plugin": plugin["name"], "status": "activated", "success": True})
                    else:
                        results.append({"plugin": plugin["name"], "status": "already_installed", "success": True})
                else:
                    results.append({
                        "plugin": plugin["name"], 
                        "status": "failed", 
                        "success": False,
                        "error": response.text[:200]
                    })
            except Exception as e:
                results.append({
                    "plugin": plugin["name"], 
                    "status": "error", 
                    "success": False,
                    "error": str(e)
                })
    
    successful = sum(1 for r in results if r["success"])
    return {
        "site_id": site_id,
        "fix_type": fix_type,
        "results": results,
        "successful": successful,
        "total": len(results)
    }
