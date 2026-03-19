"""
Social Media Auto-Posting Service
Handles automatic posting to Facebook Pages and LinkedIn Company Page
"""

import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# Facebook Page IDs mapping
FACEBOOK_PAGES = {
    "seamanshelp.com": {"page_id": "112431577304128", "name": "Seamen's help"},
    "jobsonsea.com": {"page_id": "112401348165516", "name": "Jobs On Sea"},
    "bestbuybabys.com": {"page_id": "106559875661899", "name": "Best Buy Babys"},
    "azurelady.com": {"page_id": "412510071952130", "name": "Azure Lady"},
    "storeforladies.com": {"page_id": "115952541516299", "name": "Store for Ladies"},
}

async def post_to_facebook_page(
    page_access_token: str,
    page_id: str,
    message: str,
    link: str,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Post to a Facebook Page
    
    Args:
        page_access_token: Page-specific access token
        page_id: Facebook Page ID
        message: Post message/description
        link: URL to share
        image_url: Optional image URL
    
    Returns:
        dict with success status and post_id or error
    """
    try:
        async with httpx.AsyncClient() as client:
            # Post with link
            post_data = {
                "message": message,
                "link": link,
                "access_token": page_access_token
            }
            
            response = await client.post(
                f"https://graph.facebook.com/v19.0/{page_id}/feed",
                data=post_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"[FACEBOOK] Successfully posted to page {page_id}: {result.get('id')}")
                return {
                    "success": True,
                    "post_id": result.get("id"),
                    "platform": "facebook",
                    "page_id": page_id
                }
            else:
                error = response.json()
                logging.error(f"[FACEBOOK] Error posting to page {page_id}: {error}")
                return {
                    "success": False,
                    "error": error.get("error", {}).get("message", "Unknown error"),
                    "platform": "facebook"
                }
                
    except Exception as e:
        logging.error(f"[FACEBOOK] Exception posting to page {page_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": "facebook"
        }


async def post_to_linkedin_personal(
    access_token: str,
    person_id: str,
    title: str,
    description: str,
    link: str,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Post to LinkedIn Personal Profile
    
    Args:
        access_token: LinkedIn OAuth access token
        person_id: LinkedIn Person/Member ID (sub from userinfo)
        title: Post title
        description: Post description
        link: URL to share
        image_url: Optional image URL
    
    Returns:
        dict with success status and post_id or error
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202401"
            }
            
            # Create share on LinkedIn personal profile using Posts API
            post_data = {
                "author": f"urn:li:person:{person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"{title}\n\n{description}"
                        },
                        "shareMediaCategory": "ARTICLE",
                        "media": [
                            {
                                "status": "READY",
                                "originalUrl": link,
                                "title": {
                                    "text": title
                                },
                                "description": {
                                    "text": description[:200] if len(description) > 200 else description
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get("id", "")
                logging.info(f"[LINKEDIN] Successfully posted to personal profile {person_id}: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "platform": "linkedin",
                    "person_id": person_id
                }
            else:
                error_text = response.text
                logging.error(f"[LINKEDIN] Error posting to personal profile {person_id}: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "platform": "linkedin"
                }
                
    except Exception as e:
        logging.error(f"[LINKEDIN] Exception posting to personal profile {person_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": "linkedin"
        }


async def post_to_linkedin_company(
    access_token: str,
    company_id: str,
    title: str,
    description: str,
    link: str,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Post to LinkedIn Company Page (requires w_organization_social scope)
    
    Args:
        access_token: LinkedIn OAuth access token
        company_id: LinkedIn Company/Organization ID
        title: Post title
        description: Post description
        link: URL to share
        image_url: Optional image URL
    
    Returns:
        dict with success status and post_id or error
    """
    try:
        async with httpx.AsyncClient() as client:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            # Create share on LinkedIn
            post_data = {
                "author": f"urn:li:organization:{company_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"{title}\n\n{description}"
                        },
                        "shareMediaCategory": "ARTICLE",
                        "media": [
                            {
                                "status": "READY",
                                "originalUrl": link,
                                "title": {
                                    "text": title
                                },
                                "description": {
                                    "text": description[:200] if len(description) > 200 else description
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = await client.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                post_id = result.get("id", "")
                logging.info(f"[LINKEDIN] Successfully posted to company {company_id}: {post_id}")
                return {
                    "success": True,
                    "post_id": post_id,
                    "platform": "linkedin",
                    "company_id": company_id
                }
            else:
                error_text = response.text
                logging.error(f"[LINKEDIN] Error posting to company {company_id}: {error_text}")
                return {
                    "success": False,
                    "error": error_text,
                    "platform": "linkedin"
                }
                
    except Exception as e:
        logging.error(f"[LINKEDIN] Exception posting to company {company_id}: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "platform": "linkedin"
        }


async def auto_post_article_to_social(
    db,
    article: Dict[str, Any],
    site: Dict[str, Any],
    user_id: str
) -> Dict[str, Any]:
    """
    Automatically post a published article to social media
    
    Args:
        db: Database connection
        article: Article document
        site: WordPress site configuration
        user_id: User ID
    
    Returns:
        dict with results for each platform
    """
    results = {
        "facebook": None,
        "linkedin": None,
        "posted_at": datetime.now(timezone.utc).isoformat()
    }
    
    site_url = site.get("site_url", "").replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    article_url = article.get("wordpress_url") or article.get("url", "")
    title = article.get("title", "Articol nou")
    
    logging.info(f"[SOCIAL] Article URL for posting: {article_url}")
    
    # Create post message
    excerpt = article.get("meta_description") or article.get("excerpt", "")
    if not excerpt and article.get("content"):
        # Extract first 200 chars from content
        import re
        clean_content = re.sub(r'<[^>]+>', '', article.get("content", ""))
        excerpt = clean_content[:200] + "..." if len(clean_content) > 200 else clean_content
    
    # Include link directly in message for better visibility
    message = f"📰 {title}\n\n{excerpt}\n\n👉 Citește articolul complet: {article_url}"
    
    # Get featured image
    image_url = None
    if article.get("images") and len(article["images"]) > 0:
        image_url = article["images"][0].get("url")
        logging.info(f"[SOCIAL] Featured image URL: {image_url}")
    
    # Clean site_url for Facebook lookup - normalize URL
    clean_url = site_url.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/").lower()
    logging.info(f"[SOCIAL] Processing social posting for site: {clean_url}")
    logging.info(f"[SOCIAL] Available Facebook pages: {list(FACEBOOK_PAGES.keys())}")
    
    # Post to Facebook if page is configured - flexible matching
    fb_config = None
    matched_domain = None
    for domain, config in FACEBOOK_PAGES.items():
        if domain.lower() in clean_url or clean_url in domain.lower():
            fb_config = config
            matched_domain = domain
            break
    
    logging.info(f"[SOCIAL] Facebook config for {clean_url}: {fb_config} (matched: {matched_domain})")
    
    if fb_config:
        # Get page access token from site settings
        fb_token = site.get("facebook_page_token")
        
        # If no token for this site, try to find one from another site with the same user
        if not fb_token:
            logging.info(f"[SOCIAL] No FB token for {clean_url}, searching for shared token...")
            try:
                # Find another site with a Facebook token (same user)
                other_site = await db.wordpress_configs.find_one(
                    {"user_id": user_id, "facebook_page_token": {"$exists": True, "$ne": ""}},
                    {"_id": 0, "facebook_page_token": 1, "site_url": 1}
                )
                if other_site and other_site.get("facebook_page_token"):
                    fb_token = other_site["facebook_page_token"]
                    logging.info(f"[SOCIAL] Using Facebook token from {other_site.get('site_url')}")
            except Exception as e:
                logging.warning(f"[SOCIAL] Could not find shared FB token: {e}")
        
        logging.info(f"[SOCIAL] Facebook token exists: {fb_token is not None and len(str(fb_token)) > 10}")
        
        if fb_token:
            logging.info(f"[SOCIAL] Attempting to post to Facebook page {fb_config['page_id']}")
            results["facebook"] = await post_to_facebook_page(
                page_access_token=fb_token,
                page_id=fb_config["page_id"],
                message=message,
                link=article_url,
                image_url=image_url
            )
            logging.info(f"[SOCIAL] Facebook post result: {results['facebook']}")
        else:
            logging.warning(f"[SOCIAL] No Facebook token for site {clean_url}")
            results["facebook"] = {"success": False, "error": "No Facebook token configured - please connect Facebook in WordPress Sites page"}
    else:
        logging.warning(f"[SOCIAL] Site {clean_url} not in FACEBOOK_PAGES dictionary")
    
    # Post to LinkedIn only for seamanshelp (personal profile)
    if "seamanshelp" in clean_url:
        linkedin_token = site.get("linkedin_access_token")
        linkedin_person_id = site.get("linkedin_person_id")
        if linkedin_token and linkedin_person_id:
            results["linkedin"] = await post_to_linkedin_personal(
                access_token=linkedin_token,
                person_id=linkedin_person_id,
                title=title,
                description=excerpt,
                link=article_url,
                image_url=image_url
            )
        else:
            results["linkedin"] = {"success": False, "error": "No LinkedIn token configured"}
    
    # Save posting log
    log_entry = {
        "id": f"social-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "user_id": user_id,
        "site_id": site.get("id"),
        "article_id": article.get("id"),
        "article_title": title,
        "article_url": article_url,
        "results": results,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.social_posts.insert_one(log_entry)
    
    return results


def get_facebook_page_id(site_url: str) -> Optional[str]:
    """Get Facebook Page ID for a site URL"""
    clean_url = site_url.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    page_config = FACEBOOK_PAGES.get(clean_url)
    return page_config["page_id"] if page_config else None


def get_facebook_page_name(site_url: str) -> Optional[str]:
    """Get Facebook Page name for a site URL"""
    clean_url = site_url.replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
    page_config = FACEBOOK_PAGES.get(clean_url)
    return page_config["name"] if page_config else None
