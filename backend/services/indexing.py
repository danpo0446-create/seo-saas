"""
SEO Indexing Services - Automatic Google/Bing Indexing
"""
import httpx
import asyncio
import logging
import hashlib
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

# IndexNow API endpoints
INDEXNOW_ENDPOINTS = [
    "https://api.indexnow.org/indexnow",
    "https://www.bing.com/indexnow",
    "https://yandex.com/indexnow"
]

# Ping services for search engines
PING_SERVICES = [
    "https://www.google.com/ping?sitemap=",
    "https://www.bing.com/ping?sitemap=",
]

async def ping_search_engines(sitemap_url: str) -> Dict[str, Any]:
    """Ping Google and Bing with sitemap URL"""
    results = {"success": [], "failed": []}
    
    async with httpx.AsyncClient(timeout=30) as client:
        for ping_url in PING_SERVICES:
            try:
                full_url = ping_url + sitemap_url
                response = await client.get(full_url)
                if response.status_code == 200:
                    results["success"].append(ping_url.split("//")[1].split("/")[0])
                    logging.info(f"[INDEXING] Ping success: {ping_url.split('//')[1].split('/')[0]}")
                else:
                    results["failed"].append({"service": ping_url, "status": response.status_code})
            except Exception as e:
                results["failed"].append({"service": ping_url, "error": str(e)})
                logging.error(f"[INDEXING] Ping failed: {e}")
    
    return results

async def submit_to_indexnow(url: str, site_url: str, api_key: str = None) -> Dict[str, Any]:
    """
    Submit URL to IndexNow for instant indexing on Bing, Yandex, etc.
    
    IndexNow is a protocol that allows websites to notify search engines
    about URL changes instantly.
    """
    # Generate a key if not provided (should be stored and reused)
    if not api_key:
        api_key = hashlib.md5(site_url.encode()).hexdigest()[:32]
    
    host = site_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    payload = {
        "host": host,
        "key": api_key,
        "urlList": [url]
    }
    
    results = {"success": [], "failed": []}
    
    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 202]:
                    engine = endpoint.split("//")[1].split("/")[0].replace("api.", "").replace("www.", "")
                    results["success"].append(engine)
                    logging.info(f"[INDEXING] IndexNow success: {engine} for {url}")
                else:
                    results["failed"].append({
                        "endpoint": endpoint, 
                        "status": response.status_code,
                        "response": response.text[:200]
                    })
            except Exception as e:
                results["failed"].append({"endpoint": endpoint, "error": str(e)})
                logging.warning(f"[INDEXING] IndexNow failed for {endpoint}: {e}")
    
    return {
        "url": url,
        "api_key": api_key,
        "results": results,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

async def request_google_indexing(url: str, credentials: dict) -> Dict[str, Any]:
    """
    Request Google to index a URL using the Indexing API.
    
    Requires Google Search Console API credentials.
    Note: This API is primarily for job postings and livestream content,
    but can help with general indexing requests.
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        if not credentials or not credentials.get("token"):
            return {
                "success": False,
                "error": "Google credentials not configured",
                "url": url
            }
        
        creds = Credentials(
            token=credentials.get("token"),
            refresh_token=credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials.get("client_id"),
            client_secret=credentials.get("client_secret")
        )
        
        # Build the indexing service
        service = build('indexing', 'v3', credentials=creds)
        
        # Request indexing
        body = {
            "url": url,
            "type": "URL_UPDATED"
        }
        
        response = service.urlNotifications().publish(body=body).execute()
        
        logging.info(f"[INDEXING] Google Indexing API success for {url}")
        
        return {
            "success": True,
            "url": url,
            "response": response,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logging.error(f"[INDEXING] Google Indexing API failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "url": url
        }

async def generate_sitemap_xml(site_url: str, articles: List[dict]) -> str:
    """Generate XML sitemap for a list of articles"""
    
    sitemap_header = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
'''
    
    sitemap_footer = '</urlset>'
    
    urls = []
    
    # Add homepage
    urls.append(f'''  <url>
    <loc>{site_url}</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>''')
    
    # Add articles
    for article in articles:
        article_url = article.get("wp_post_url", "")
        if not article_url:
            continue
            
        lastmod = article.get("published_at", article.get("created_at", ""))
        if lastmod:
            lastmod = lastmod.split("T")[0]  # Just date part
        
        url_entry = f'''  <url>
    <loc>{article_url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.8</priority>
  </url>'''
        urls.append(url_entry)
    
    return sitemap_header + "\n".join(urls) + "\n" + sitemap_footer

async def submit_sitemap_to_wordpress(wp_config: dict, sitemap_content: str) -> Dict[str, Any]:
    """Upload sitemap to WordPress and ping search engines"""
    import base64
    
    site_url = wp_config.get("site_url", "").rstrip("/")
    
    # Note: Most WordPress sites with Yoast SEO or similar plugins 
    # auto-generate sitemaps. This function pings the existing sitemap.
    
    sitemap_url = f"{site_url}/sitemap.xml"
    
    # Try common sitemap URLs
    sitemap_urls_to_try = [
        f"{site_url}/sitemap.xml",
        f"{site_url}/sitemap_index.xml",
        f"{site_url}/wp-sitemap.xml",
        f"{site_url}/post-sitemap.xml"
    ]
    
    # Find working sitemap
    working_sitemap = None
    async with httpx.AsyncClient(timeout=15, verify=False) as client:
        for url in sitemap_urls_to_try:
            try:
                response = await client.head(url)
                if response.status_code == 200:
                    working_sitemap = url
                    logging.info(f"[INDEXING] Found sitemap at {url}")
                    break
            except:
                continue
    
    if working_sitemap:
        # Ping search engines with the sitemap
        ping_results = await ping_search_engines(working_sitemap)
        return {
            "success": True,
            "sitemap_url": working_sitemap,
            "ping_results": ping_results
        }
    else:
        return {
            "success": False,
            "error": "No sitemap found on WordPress site",
            "tried_urls": sitemap_urls_to_try
        }

async def auto_index_new_article(
    article_url: str, 
    site_url: str, 
    wp_config: dict = None,
    google_credentials: dict = None
) -> Dict[str, Any]:
    """
    Automatically submit new article for indexing across all services.
    Called after an article is published.
    """
    logging.info(f"[INDEXING] Starting auto-indexing for {article_url}")
    
    results = {
        "url": article_url,
        "site": site_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    # 1. Submit to IndexNow (Bing, Yandex, etc.)
    try:
        indexnow_result = await submit_to_indexnow(article_url, site_url)
        results["services"]["indexnow"] = indexnow_result
    except Exception as e:
        results["services"]["indexnow"] = {"success": False, "error": str(e)}
    
    # 2. Ping search engines with sitemap
    if wp_config:
        try:
            sitemap_result = await submit_sitemap_to_wordpress(wp_config, "")
            results["services"]["sitemap_ping"] = sitemap_result
        except Exception as e:
            results["services"]["sitemap_ping"] = {"success": False, "error": str(e)}
    
    # 3. Google Indexing API (if credentials available)
    if google_credentials and google_credentials.get("token"):
        try:
            google_result = await request_google_indexing(article_url, google_credentials)
            results["services"]["google_indexing_api"] = google_result
        except Exception as e:
            results["services"]["google_indexing_api"] = {"success": False, "error": str(e)}
    
    # Calculate overall success
    successful_services = []
    for service, result in results["services"].items():
        if isinstance(result, dict):
            if result.get("success") or (result.get("results", {}).get("success")):
                successful_services.append(service)
    
    results["successful_services"] = successful_services
    results["total_success"] = len(successful_services)
    
    logging.info(f"[INDEXING] Completed auto-indexing for {article_url}: {len(successful_services)} services successful")
    
    return results

async def bulk_index_site(site_url: str, article_urls: List[str]) -> Dict[str, Any]:
    """Submit multiple URLs for indexing at once"""
    
    results = {
        "site": site_url,
        "total_urls": len(article_urls),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "indexnow": None,
        "sitemap_ping": None
    }
    
    # Generate API key for IndexNow
    api_key = hashlib.md5(site_url.encode()).hexdigest()[:32]
    host = site_url.replace("https://", "").replace("http://", "").split("/")[0]
    
    # Submit all URLs to IndexNow at once
    payload = {
        "host": host,
        "key": api_key,
        "urlList": article_urls[:100]  # Max 100 URLs per request
    }
    
    indexnow_results = {"success": [], "failed": []}
    
    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        for endpoint in INDEXNOW_ENDPOINTS:
            try:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code in [200, 202]:
                    engine = endpoint.split("//")[1].split("/")[0].replace("api.", "").replace("www.", "")
                    indexnow_results["success"].append(engine)
                    logging.info(f"[INDEXING] Bulk IndexNow success: {engine} for {len(article_urls)} URLs")
            except Exception as e:
                indexnow_results["failed"].append({"endpoint": endpoint, "error": str(e)})
    
    results["indexnow"] = indexnow_results
    
    # Also ping sitemap
    sitemap_url = f"{site_url}/sitemap.xml"
    results["sitemap_ping"] = await ping_search_engines(sitemap_url)
    
    return results



async def check_robots_txt(site_url: str) -> Dict[str, Any]:
    """Check and analyze robots.txt file"""
    robots_url = site_url.rstrip("/") + "/robots.txt"
    
    result = {
        "url": robots_url,
        "exists": False,
        "content": None,
        "issues": [],
        "recommendations": []
    }
    
    try:
        async with httpx.AsyncClient(timeout=15, verify=False) as client:
            response = await client.get(robots_url)
            
            if response.status_code == 200:
                result["exists"] = True
                result["content"] = response.text[:2000]  # Limit content size
                
                content_lower = response.text.lower()
                
                # Check for common issues
                if "disallow: /" in content_lower and "disallow: / " not in content_lower:
                    # Check if it's blocking everything
                    lines = content_lower.split("\n")
                    for line in lines:
                        if line.strip() == "disallow: /":
                            result["issues"].append("CRITIC: Site-ul blochează toți roboții cu 'Disallow: /'")
                            break
                
                if "sitemap:" not in content_lower:
                    result["issues"].append("Lipsește referința către sitemap în robots.txt")
                    result["recommendations"].append("Adaugă: Sitemap: " + site_url.rstrip("/") + "/sitemap.xml")
                
                if "user-agent: *" not in content_lower:
                    result["recommendations"].append("Adaugă reguli pentru 'User-agent: *'")
                
                # Check for Googlebot specific rules
                if "googlebot" in content_lower:
                    if "disallow" in content_lower.split("googlebot")[1].split("user-agent")[0]:
                        result["issues"].append("Există restricții specifice pentru Googlebot")
            else:
                result["issues"].append(f"robots.txt nu există (status: {response.status_code})")
                result["recommendations"].append("Creează un fișier robots.txt pentru a controla indexarea")
                
    except Exception as e:
        result["issues"].append(f"Eroare la verificare: {str(e)}")
    
    return result

async def discover_site_pages(site_url: str, max_pages: int = 100) -> Dict[str, Any]:
    """Discover all pages on a site by crawling sitemap and common pages"""
    from bs4 import BeautifulSoup
    import xml.etree.ElementTree as ET
    
    site_url = site_url.rstrip("/")
    discovered_pages = set()
    discovered_pages.add(site_url + "/")
    
    result = {
        "site_url": site_url,
        "pages_found": 0,
        "pages": [],
        "sitemaps_found": [],
        "method": []
    }
    
    async with httpx.AsyncClient(timeout=30, verify=False, follow_redirects=True) as client:
        # 1. Try to find sitemap from robots.txt
        try:
            robots_response = await client.get(site_url + "/robots.txt")
            if robots_response.status_code == 200:
                for line in robots_response.text.split("\n"):
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        result["sitemaps_found"].append(sitemap_url)
        except:
            pass
        
        # 2. Try common sitemap URLs
        common_sitemaps = [
            "/sitemap.xml",
            "/sitemap_index.xml",
            "/wp-sitemap.xml",
            "/sitemap/sitemap-index.xml",
            "/post-sitemap.xml",
            "/page-sitemap.xml"
        ]
        
        for sitemap_path in common_sitemaps:
            sitemap_url = site_url + sitemap_path
            if sitemap_url not in result["sitemaps_found"]:
                try:
                    response = await client.get(sitemap_url)
                    if response.status_code == 200 and "<?xml" in response.text[:100]:
                        result["sitemaps_found"].append(sitemap_url)
                except:
                    pass
        
        # 3. Parse sitemaps to extract URLs
        for sitemap_url in result["sitemaps_found"][:5]:  # Limit to 5 sitemaps
            try:
                response = await client.get(sitemap_url)
                if response.status_code == 200:
                    # Check if it's a sitemap index
                    if "<sitemapindex" in response.text:
                        # Parse sitemap index
                        root = ET.fromstring(response.text)
                        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                        for sitemap in root.findall('.//sm:sitemap/sm:loc', ns):
                            if sitemap.text and sitemap.text not in result["sitemaps_found"]:
                                result["sitemaps_found"].append(sitemap.text)
                    else:
                        # Parse regular sitemap
                        root = ET.fromstring(response.text)
                        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
                        for url_elem in root.findall('.//sm:url/sm:loc', ns):
                            if url_elem.text:
                                discovered_pages.add(url_elem.text)
                                if len(discovered_pages) >= max_pages:
                                    break
                        result["method"].append("sitemap")
            except Exception as e:
                logging.warning(f"[INDEXING] Error parsing sitemap {sitemap_url}: {e}")
        
        # 4. If no pages found from sitemap, crawl homepage
        if len(discovered_pages) <= 1:
            try:
                response = await client.get(site_url)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('/'):
                            full_url = site_url + href
                        elif href.startswith(site_url):
                            full_url = href
                        else:
                            continue
                        
                        # Clean URL
                        full_url = full_url.split('#')[0].split('?')[0].rstrip('/')
                        if full_url and full_url.startswith(site_url):
                            discovered_pages.add(full_url)
                            if len(discovered_pages) >= max_pages:
                                break
                    result["method"].append("crawl")
            except Exception as e:
                logging.warning(f"[INDEXING] Error crawling homepage: {e}")
    
    result["pages"] = list(discovered_pages)[:max_pages]
    result["pages_found"] = len(result["pages"])
    
    return result

async def check_google_indexing_status(site_url: str, credentials: dict) -> Dict[str, Any]:
    """Check indexing status via Google Search Console API"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        if not credentials or not credentials.get("token"):
            return {
                "success": False,
                "error": "Google Search Console nu este conectat",
                "recommendation": "Conectează Google Search Console din Setări pentru a vedea statusul indexării"
            }
        
        creds = Credentials(
            token=credentials.get("token"),
            refresh_token=credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials.get("client_id"),
            client_secret=credentials.get("client_secret")
        )
        
        # Build the Search Console service
        service = build('searchconsole', 'v1', credentials=creds)
        
        # Normalize site URL for GSC (they use specific formats)
        site_url_normalized = site_url.rstrip("/") + "/"
        
        # Try to get site info
        try:
            sites = service.sites().list().execute()
            site_list = sites.get('siteEntry', [])
            
            # Find matching site
            matched_site = None
            for site in site_list:
                if site_url.replace("https://", "").replace("http://", "").rstrip("/") in site.get('siteUrl', ''):
                    matched_site = site
                    break
            
            if not matched_site:
                return {
                    "success": False,
                    "error": "Site-ul nu este verificat în Google Search Console",
                    "available_sites": [s.get('siteUrl') for s in site_list],
                    "recommendation": "Adaugă și verifică site-ul în Google Search Console"
                }
            
            # Get indexing stats using Search Analytics
            # Query for the last 28 days
            from datetime import datetime, timedelta
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=28)).strftime('%Y-%m-%d')
            
            analytics = service.searchanalytics().query(
                siteUrl=matched_site.get('siteUrl'),
                body={
                    'startDate': start_date,
                    'endDate': end_date,
                    'dimensions': ['page'],
                    'rowLimit': 100
                }
            ).execute()
            
            indexed_pages = len(analytics.get('rows', []))
            total_clicks = sum(row.get('clicks', 0) for row in analytics.get('rows', []))
            total_impressions = sum(row.get('impressions', 0) for row in analytics.get('rows', []))
            
            return {
                "success": True,
                "site_url": matched_site.get('siteUrl'),
                "permission_level": matched_site.get('permissionLevel'),
                "indexed_pages_visible": indexed_pages,
                "total_clicks_28d": total_clicks,
                "total_impressions_28d": total_impressions,
                "period": f"{start_date} - {end_date}"
            }
            
        except Exception as api_error:
            return {
                "success": False,
                "error": f"Eroare API: {str(api_error)}",
                "recommendation": "Verifică permisiunile Google Search Console"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

async def submit_sitemap_to_gsc(sitemap_url: str, site_url: str, credentials: dict) -> Dict[str, Any]:
    """Submit sitemap to Google Search Console"""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        if not credentials or not credentials.get("token"):
            return {
                "success": False,
                "error": "Google Search Console nu este conectat"
            }
        
        creds = Credentials(
            token=credentials.get("token"),
            refresh_token=credentials.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=credentials.get("client_id"),
            client_secret=credentials.get("client_secret")
        )
        
        service = build('searchconsole', 'v1', credentials=creds)
        
        # Normalize site URL
        site_url_normalized = site_url.rstrip("/") + "/"
        
        # Submit sitemap
        service.sitemaps().submit(
            siteUrl=site_url_normalized,
            feedpath=sitemap_url
        ).execute()
        
        logging.info(f"[INDEXING] Submitted sitemap {sitemap_url} to GSC")
        
        return {
            "success": True,
            "sitemap_url": sitemap_url,
            "site_url": site_url_normalized,
            "message": "Sitemap trimis cu succes la Google Search Console"
        }
        
    except Exception as e:
        logging.error(f"[INDEXING] Failed to submit sitemap to GSC: {e}")
        return {
            "success": False,
            "error": str(e)
        }

async def full_site_indexing_audit(
    site_url: str,
    wp_config: dict = None,
    google_credentials: dict = None
) -> Dict[str, Any]:
    """
    Perform a complete site indexing audit and optimization.
    
    This includes:
    1. Check robots.txt
    2. Discover all site pages
    3. Check sitemap status
    4. Submit sitemap to search engines
    5. Check Google indexing status
    6. Submit all pages to IndexNow
    """
    logging.info(f"[INDEXING] Starting full site indexing audit for {site_url}")
    
    result = {
        "site_url": site_url,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "robots_txt": None,
        "pages_discovered": None,
        "sitemap_status": None,
        "google_status": None,
        "indexnow_submission": None,
        "ping_results": None,
        "overall_score": 0,
        "issues": [],
        "recommendations": []
    }
    
    # 1. Check robots.txt
    try:
        result["robots_txt"] = await check_robots_txt(site_url)
        if result["robots_txt"]["exists"]:
            result["overall_score"] += 20
        else:
            result["issues"].append("robots.txt nu există")
            result["recommendations"].append("Creează robots.txt pentru a controla indexarea")
        result["issues"].extend(result["robots_txt"].get("issues", []))
        result["recommendations"].extend(result["robots_txt"].get("recommendations", []))
    except Exception as e:
        result["robots_txt"] = {"error": str(e)}
    
    # 2. Discover site pages
    try:
        result["pages_discovered"] = await discover_site_pages(site_url, max_pages=200)
        if result["pages_discovered"]["pages_found"] > 0:
            result["overall_score"] += 20
            if result["pages_discovered"]["sitemaps_found"]:
                result["overall_score"] += 10
            else:
                result["issues"].append("Nu s-a găsit niciun sitemap")
                result["recommendations"].append("Creează un sitemap.xml pentru site")
    except Exception as e:
        result["pages_discovered"] = {"error": str(e)}
    
    # 3. Check sitemap and ping search engines
    if result["pages_discovered"] and result["pages_discovered"].get("sitemaps_found"):
        main_sitemap = result["pages_discovered"]["sitemaps_found"][0]
        try:
            result["ping_results"] = await ping_search_engines(main_sitemap)
            if result["ping_results"]["success"]:
                result["overall_score"] += 15
        except Exception as e:
            result["ping_results"] = {"error": str(e)}
        
        # Submit to GSC if credentials available
        if google_credentials and google_credentials.get("token"):
            try:
                result["sitemap_status"] = await submit_sitemap_to_gsc(
                    main_sitemap, site_url, google_credentials
                )
                if result["sitemap_status"].get("success"):
                    result["overall_score"] += 15
            except Exception as e:
                result["sitemap_status"] = {"error": str(e)}
    
    # 4. Check Google indexing status
    if google_credentials and google_credentials.get("token"):
        try:
            result["google_status"] = await check_google_indexing_status(site_url, google_credentials)
            if result["google_status"].get("success"):
                result["overall_score"] += 10
        except Exception as e:
            result["google_status"] = {"error": str(e)}
    else:
        result["recommendations"].append("Conectează Google Search Console pentru a vedea statusul indexării")
    
    # 5. Submit all discovered pages to IndexNow
    if result["pages_discovered"] and result["pages_discovered"].get("pages"):
        pages_to_submit = result["pages_discovered"]["pages"][:100]  # Max 100
        try:
            result["indexnow_submission"] = await bulk_index_site(site_url, pages_to_submit)
            if result["indexnow_submission"].get("indexnow", {}).get("success"):
                result["overall_score"] += 10
        except Exception as e:
            result["indexnow_submission"] = {"error": str(e)}
    
    # Calculate final score (max 100)
    result["overall_score"] = min(100, result["overall_score"])
    
    # Add grade
    if result["overall_score"] >= 80:
        result["grade"] = "A"
    elif result["overall_score"] >= 60:
        result["grade"] = "B"
    elif result["overall_score"] >= 40:
        result["grade"] = "C"
    else:
        result["grade"] = "D"
    
    logging.info(f"[INDEXING] Completed full site audit for {site_url}: Score {result['overall_score']}/100")
    
    return result
