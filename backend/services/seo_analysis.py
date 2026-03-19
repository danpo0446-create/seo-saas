"""
SEO Analysis Services - Business Analysis AI & Technical SEO Audit
"""
import httpx
import re
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup
import logging

async def fetch_page(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Fetch a webpage and return content with metadata"""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, verify=False) as client:
            response = await client.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            return {
                "success": True,
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers),
                "url": str(response.url),
                "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else 0
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "status_code": 0
        }

def analyze_meta_tags(soup: BeautifulSoup) -> Dict[str, Any]:
    """Analyze meta tags on a page"""
    results = {
        "title": None,
        "title_length": 0,
        "description": None,
        "description_length": 0,
        "keywords": None,
        "og_tags": {},
        "twitter_tags": {},
        "canonical": None,
        "robots": None,
        "issues": []
    }
    
    # Title
    title_tag = soup.find('title')
    if title_tag:
        results["title"] = title_tag.get_text().strip()
        results["title_length"] = len(results["title"])
        if results["title_length"] < 30:
            results["issues"].append("Titlul este prea scurt (< 30 caractere)")
        elif results["title_length"] > 60:
            results["issues"].append("Titlul este prea lung (> 60 caractere)")
    else:
        results["issues"].append("Lipsește tag-ul <title>")
    
    # Meta description
    desc_tag = soup.find('meta', attrs={'name': 'description'})
    if desc_tag and desc_tag.get('content'):
        results["description"] = desc_tag['content']
        results["description_length"] = len(results["description"])
        if results["description_length"] < 120:
            results["issues"].append("Meta description prea scurtă (< 120 caractere)")
        elif results["description_length"] > 160:
            results["issues"].append("Meta description prea lungă (> 160 caractere)")
    else:
        results["issues"].append("Lipsește meta description")
    
    # Keywords
    keywords_tag = soup.find('meta', attrs={'name': 'keywords'})
    if keywords_tag and keywords_tag.get('content'):
        results["keywords"] = keywords_tag['content']
    
    # Canonical
    canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
    if canonical_tag:
        results["canonical"] = canonical_tag.get('href')
    else:
        results["issues"].append("Lipsește tag-ul canonical")
    
    # Robots
    robots_tag = soup.find('meta', attrs={'name': 'robots'})
    if robots_tag:
        results["robots"] = robots_tag.get('content')
    
    # Open Graph tags
    for og_tag in soup.find_all('meta', attrs={'property': re.compile(r'^og:')}):
        prop = og_tag.get('property', '').replace('og:', '')
        results["og_tags"][prop] = og_tag.get('content', '')
    
    if not results["og_tags"]:
        results["issues"].append("Lipsesc tag-urile Open Graph (importante pentru social media)")
    
    # Twitter tags
    for tw_tag in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
        name = tw_tag.get('name', '').replace('twitter:', '')
        results["twitter_tags"][name] = tw_tag.get('content', '')
    
    return results

def analyze_headings(soup: BeautifulSoup) -> Dict[str, Any]:
    """Analyze heading structure"""
    results = {
        "h1_count": 0,
        "h1_texts": [],
        "h2_count": 0,
        "h2_texts": [],
        "h3_count": 0,
        "heading_structure": [],
        "issues": []
    }
    
    for i in range(1, 7):
        headings = soup.find_all(f'h{i}')
        if i == 1:
            results["h1_count"] = len(headings)
            results["h1_texts"] = [h.get_text().strip()[:100] for h in headings]
        elif i == 2:
            results["h2_count"] = len(headings)
            results["h2_texts"] = [h.get_text().strip()[:100] for h in headings[:10]]
        elif i == 3:
            results["h3_count"] = len(headings)
        
        for h in headings:
            results["heading_structure"].append({
                "level": i,
                "text": h.get_text().strip()[:50]
            })
    
    if results["h1_count"] == 0:
        results["issues"].append("Lipsește tag-ul H1 - critic pentru SEO")
    elif results["h1_count"] > 1:
        results["issues"].append(f"Prea multe tag-uri H1 ({results['h1_count']}). Ar trebui să fie doar unul.")
    
    if results["h2_count"] == 0:
        results["issues"].append("Lipsesc tag-urile H2 - structură slabă")
    
    return results

def analyze_images(soup: BeautifulSoup) -> Dict[str, Any]:
    """Analyze images for SEO"""
    results = {
        "total_images": 0,
        "images_without_alt": 0,
        "images_with_empty_alt": 0,
        "images_list": [],
        "issues": []
    }
    
    images = soup.find_all('img')
    results["total_images"] = len(images)
    
    for img in images[:20]:  # Analyze first 20 images
        src = img.get('src', '')
        alt = img.get('alt')
        
        img_info = {"src": src[:100], "alt": alt}
        results["images_list"].append(img_info)
        
        if alt is None:
            results["images_without_alt"] += 1
        elif alt.strip() == "":
            results["images_with_empty_alt"] += 1
    
    if results["images_without_alt"] > 0:
        results["issues"].append(f"{results['images_without_alt']} imagini fără atribut alt")
    
    if results["images_with_empty_alt"] > 0:
        results["issues"].append(f"{results['images_with_empty_alt']} imagini cu alt gol")
    
    return results

def analyze_links(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """Analyze links on the page"""
    from urllib.parse import urljoin, urlparse
    
    results = {
        "total_links": 0,
        "internal_links": 0,
        "external_links": 0,
        "nofollow_links": 0,
        "broken_anchors": 0,
        "issues": []
    }
    
    base_domain = urlparse(base_url).netloc
    links = soup.find_all('a', href=True)
    results["total_links"] = len(links)
    
    for link in links:
        href = link.get('href', '')
        rel = link.get('rel', [])
        
        if href.startswith('#') or href.startswith('javascript:'):
            continue
        
        full_url = urljoin(base_url, href)
        link_domain = urlparse(full_url).netloc
        
        if link_domain == base_domain:
            results["internal_links"] += 1
        else:
            results["external_links"] += 1
        
        if 'nofollow' in rel:
            results["nofollow_links"] += 1
        
        # Check for empty anchor text
        if not link.get_text().strip():
            results["broken_anchors"] += 1
    
    if results["broken_anchors"] > 0:
        results["issues"].append(f"{results['broken_anchors']} link-uri fără text anchor")
    
    return results

def analyze_content(soup: BeautifulSoup) -> Dict[str, Any]:
    """Analyze page content"""
    results = {
        "word_count": 0,
        "paragraph_count": 0,
        "avg_paragraph_length": 0,
        "issues": []
    }
    
    # Remove script and style elements
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    
    text = soup.get_text()
    words = re.findall(r'\b\w+\b', text)
    results["word_count"] = len(words)
    
    paragraphs = soup.find_all('p')
    results["paragraph_count"] = len(paragraphs)
    
    if results["paragraph_count"] > 0:
        total_p_words = sum(len(re.findall(r'\b\w+\b', p.get_text())) for p in paragraphs)
        results["avg_paragraph_length"] = round(total_p_words / results["paragraph_count"], 1)
    
    if results["word_count"] < 300:
        results["issues"].append(f"Conținut insuficient ({results['word_count']} cuvinte). Minim recomandat: 300")
    
    return results

def analyze_technical(page_data: Dict, soup: BeautifulSoup) -> Dict[str, Any]:
    """Analyze technical SEO aspects"""
    results = {
        "response_time": page_data.get("response_time", 0),
        "status_code": page_data.get("status_code", 0),
        "https": page_data.get("url", "").startswith("https"),
        "has_viewport": False,
        "has_charset": False,
        "has_lang": False,
        "has_favicon": False,
        "issues": []
    }
    
    # Check viewport
    viewport = soup.find('meta', attrs={'name': 'viewport'})
    results["has_viewport"] = viewport is not None
    if not results["has_viewport"]:
        results["issues"].append("Lipsește meta viewport - probleme pe mobile")
    
    # Check charset
    charset = soup.find('meta', attrs={'charset': True}) or soup.find('meta', attrs={'http-equiv': 'Content-Type'})
    results["has_charset"] = charset is not None
    
    # Check lang attribute
    html_tag = soup.find('html')
    results["has_lang"] = html_tag and html_tag.get('lang')
    if not results["has_lang"]:
        results["issues"].append("Lipsește atributul lang pe tag-ul <html>")
    
    # Check favicon
    favicon = soup.find('link', attrs={'rel': re.compile(r'icon', re.I)})
    results["has_favicon"] = favicon is not None
    if not results["has_favicon"]:
        results["issues"].append("Lipsește favicon")
    
    # Check HTTPS
    if not results["https"]:
        results["issues"].append("Site-ul nu folosește HTTPS - critic pentru SEO și securitate")
    
    # Check response time
    if results["response_time"] > 3:
        results["issues"].append(f"Timp de răspuns lent ({results['response_time']:.2f}s). Target: < 2s")
    
    return results

async def perform_technical_audit(url: str) -> Dict[str, Any]:
    """Perform a complete technical SEO audit"""
    logging.info(f"Starting technical SEO audit for {url}")
    
    # Ensure URL has protocol
    if not url.startswith('http'):
        url = 'https://' + url
    
    # Fetch the page
    page_data = await fetch_page(url)
    
    if not page_data["success"]:
        return {
            "success": False,
            "error": page_data.get("error", "Nu s-a putut accesa site-ul"),
            "url": url
        }
    
    soup = BeautifulSoup(page_data["content"], 'html.parser')
    
    # Run all analyses
    meta_analysis = analyze_meta_tags(soup)
    heading_analysis = analyze_headings(soup)
    image_analysis = analyze_images(soup)
    link_analysis = analyze_links(soup, url)
    content_analysis = analyze_content(soup)
    technical_analysis = analyze_technical(page_data, soup)
    
    # Collect all issues
    all_issues = []
    for analysis in [meta_analysis, heading_analysis, image_analysis, link_analysis, content_analysis, technical_analysis]:
        all_issues.extend(analysis.get("issues", []))
    
    # Calculate score
    max_score = 100
    deduction_per_issue = 5
    score = max(0, max_score - (len(all_issues) * deduction_per_issue))
    
    # Determine grade
    if score >= 90:
        grade = "A"
        grade_color = "green"
    elif score >= 70:
        grade = "B"
        grade_color = "yellow"
    elif score >= 50:
        grade = "C"
        grade_color = "orange"
    else:
        grade = "D"
        grade_color = "red"
    
    return {
        "success": True,
        "url": url,
        "analyzed_at": datetime.utcnow().isoformat(),
        "score": score,
        "grade": grade,
        "grade_color": grade_color,
        "total_issues": len(all_issues),
        "issues": all_issues,
        "meta": meta_analysis,
        "headings": heading_analysis,
        "images": image_analysis,
        "links": link_analysis,
        "content": content_analysis,
        "technical": technical_analysis
    }

async def generate_business_analysis(site_url: str, site_niche: str, api_key: str) -> Dict[str, Any]:
    """Generate AI-powered business analysis and SEO strategy"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    logging.info(f"Starting business analysis for {site_url}")
    
    # First, perform technical audit to get site data
    audit = await perform_technical_audit(site_url)
    
    if not audit["success"]:
        return {
            "success": False,
            "error": audit.get("error", "Nu s-a putut analiza site-ul")
        }
    
    # Prepare context for AI
    site_context = f"""
Site URL: {site_url}
Nișă: {site_niche}
Scor SEO Tehnic: {audit['score']}/100 (Nota: {audit['grade']})
Probleme Tehnice: {len(audit['issues'])}
Titlu: {audit['meta'].get('title', 'N/A')}
Descriere: {audit['meta'].get('description', 'N/A')[:200] if audit['meta'].get('description') else 'N/A'}
Cuvinte pe pagină: {audit['content'].get('word_count', 0)}
H1: {', '.join(audit['headings'].get('h1_texts', [])[:2])}
H2: {', '.join(audit['headings'].get('h2_texts', [])[:5])}
Link-uri interne: {audit['links'].get('internal_links', 0)}
Link-uri externe: {audit['links'].get('external_links', 0)}
Imagini fără ALT: {audit['images'].get('images_without_alt', 0)}
Probleme identificate: {', '.join(audit['issues'][:10])}
"""
    
    # Generate analysis with AI
    chat = LlmChat(
        api_key=api_key,
        session_id=f"business-analysis-{datetime.utcnow().timestamp()}",
        system_message="""Ești un expert SEO senior cu experiență în strategii de marketing digital.
Analizezi site-uri web și oferi recomandări concrete, acționabile pentru îmbunătățirea vizibilității în motoarele de căutare.
Răspunde DOAR în limba ROMÂNĂ.
Structurează răspunsul în secțiuni clare cu emoji-uri pentru vizibilitate.
Fii specific și oferă exemple concrete."""
    ).with_model("gemini", "gemini-2.0-flash")
    
    prompt = f"""Analizează acest site și generează o strategie SEO completă:

{site_context}

Generează un raport detaliat cu următoarele secțiuni:

1. 📊 SUMAR EXECUTIV (2-3 propoziții despre starea actuală a site-ului)

2. 🎯 TOP 5 KEYWORDS RECOMANDATE
   - Pentru fiecare keyword: volumul estimat de căutări, dificultate, prioritate
   - Explică de ce sunt relevante pentru nișa {site_niche}

3. 📈 OPORTUNITĂȚI DE CONȚINUT
   - 5 idei de articole cu titluri complete
   - Gap-uri de conținut identificate
   - Tipuri de conținut recomandate (ghiduri, liste, how-to, etc.)

4. 🔧 ACȚIUNI PRIORITARE
   - Top 10 acțiuni în ordinea priorității
   - Pentru fiecare: impact estimat (mare/mediu/mic) și efort necesar

5. 📱 RECOMANDĂRI TEHNICE
   - Probleme tehnice de rezolvat urgent
   - Optimizări pentru mobile și viteză

6. 🔗 STRATEGIE DE BACKLINKS
   - Tipuri de backlinks recomandate
   - 3-5 surse potențiale de backlinks pentru această nișă

7. 📅 PLAN DE ACȚIUNE 30 ZILE
   - Săptămâna 1: Ce trebuie făcut
   - Săptămâna 2: Ce trebuie făcut
   - Săptămâna 3: Ce trebuie făcut
   - Săptămâna 4: Ce trebuie făcut

8. 💡 PREDICȚII
   - Trafic estimat după implementare (3 luni, 6 luni)
   - KPIs de urmărit

Fii CONCRET și ACȚIONABIL. Oferă exemple specifice, nu sfaturi generice."""

    try:
        analysis_text = await chat.send_message(UserMessage(text=prompt))
        
        return {
            "success": True,
            "url": site_url,
            "niche": site_niche,
            "analyzed_at": datetime.utcnow().isoformat(),
            "technical_score": audit["score"],
            "technical_grade": audit["grade"],
            "technical_issues": audit["issues"][:10],
            "analysis": analysis_text,
            "meta_title": audit["meta"].get("title"),
            "meta_description": audit["meta"].get("description"),
            "word_count": audit["content"].get("word_count", 0)
        }
    except Exception as e:
        logging.error(f"Error generating business analysis: {e}")
        return {
            "success": False,
            "error": str(e)
        }



async def auto_fix_seo_issues(
    site_url: str, 
    wp_site_url: str,
    wp_username: str, 
    wp_password: str,
    api_key: str,
    issues_to_fix: List[str] = None
) -> Dict[str, Any]:
    """
    Automatically fix SEO issues that can be corrected via WordPress API
    
    Fixable issues:
    - Missing/bad meta description -> Generate with AI
    - Missing alt tags on images -> Generate with AI
    - Missing Open Graph tags -> Add defaults
    - Title optimization -> Suggest better title
    """
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import base64
    
    logging.info(f"[AUTO-FIX] Starting auto-fix for {site_url}")
    
    fixes_applied = []
    fixes_failed = []
    suggestions = []
    
    # First, run a fresh audit to get current issues
    audit = await perform_technical_audit(site_url)
    
    if not audit.get("success"):
        return {
            "success": False,
            "error": "Nu s-a putut analiza site-ul",
            "fixes_applied": [],
            "fixes_failed": []
        }
    
    # WordPress API base
    wp_api_base = wp_site_url.rstrip('/') + '/wp-json/wp/v2'
    auth_string = base64.b64encode(f"{wp_username}:{wp_password}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_string}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=30, verify=False) as client:
        
        # 1. Fix Missing Meta Description
        if not audit["meta"].get("description") or audit["meta"].get("description_length", 0) < 50:
            logging.info("[AUTO-FIX] Attempting to fix missing/short meta description")
            try:
                # Generate meta description with AI
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"autofix-meta-{datetime.utcnow().timestamp()}",
                    system_message="Ești expert SEO. Generezi meta descrieri optimizate, între 120-155 caractere. Răspunde DOAR cu meta descrierea, fără explicații."
                ).with_model("gemini", "gemini-2.0-flash")
                
                title = audit["meta"].get("title", site_url)
                h1_texts = audit["headings"].get("h1_texts", [])
                h1 = h1_texts[0] if h1_texts else title
                
                prompt = f"""Generează o meta descriere SEO optimizată pentru această pagină:
Titlu: {title}
H1: {h1}
URL: {site_url}

Cerințe:
- Între 120-155 caractere
- Include cuvinte cheie relevante
- Call-to-action subtil
- În limba română dacă site-ul e în română

Răspunde DOAR cu meta descrierea:"""
                
                new_description = await chat.send_message(UserMessage(text=prompt))
                new_description = new_description.strip().strip('"').strip("'")
                
                if 100 < len(new_description) < 170:
                    # Try to update via Yoast SEO API or store for manual update
                    suggestions.append({
                        "type": "meta_description",
                        "current": audit["meta"].get("description", "Lipsește"),
                        "suggested": new_description,
                        "action": "Adaugă în Yoast SEO sau în <head> al temei"
                    })
                    fixes_applied.append(f"Meta description generată: {new_description[:50]}...")
                    logging.info(f"[AUTO-FIX] Generated meta description: {new_description[:50]}...")
            except Exception as e:
                fixes_failed.append(f"Meta description: {str(e)}")
                logging.error(f"[AUTO-FIX] Failed to fix meta description: {e}")
        
        # 2. Fix Images Without Alt Tags
        if audit["images"].get("images_without_alt", 0) > 0:
            logging.info("[AUTO-FIX] Attempting to fix images without alt tags")
            try:
                # Get images from WordPress
                media_response = await client.get(
                    f"{wp_api_base}/media?per_page=50",
                    headers=headers
                )
                
                if media_response.status_code == 200:
                    media_items = media_response.json()
                    fixed_count = 0
                    
                    for media in media_items:
                        alt_text = media.get("alt_text", "")
                        if not alt_text or len(alt_text) < 3:
                            # Generate alt text with AI
                            media_title = media.get("title", {}).get("rendered", "")
                            media_url = media.get("source_url", "")
                            filename = media_url.split("/")[-1] if media_url else ""
                            
                            chat = LlmChat(
                                api_key=api_key,
                                session_id=f"autofix-alt-{media.get('id')}",
                                system_message="Generezi texte alt pentru imagini, scurte și descriptive (max 125 caractere). Răspunde DOAR cu textul alt."
                            ).with_model("gemini", "gemini-2.0-flash")
                            
                            prompt = f"""Generează un text alt SEO pentru această imagine:
Titlu: {media_title}
Nume fișier: {filename}

Cerințe:
- Max 125 caractere
- Descriptiv și relevant
- Include cuvinte cheie dacă e posibil

Răspunde DOAR cu textul alt:"""
                            
                            new_alt = await chat.send_message(UserMessage(text=prompt))
                            new_alt = new_alt.strip().strip('"').strip("'")[:125]
                            
                            # Update media item
                            update_response = await client.post(
                                f"{wp_api_base}/media/{media['id']}",
                                headers=headers,
                                json={"alt_text": new_alt}
                            )
                            
                            if update_response.status_code == 200:
                                fixed_count += 1
                                logging.info(f"[AUTO-FIX] Fixed alt for media {media['id']}: {new_alt[:30]}...")
                            
                            if fixed_count >= 10:  # Limit to 10 images per run
                                break
                    
                    if fixed_count > 0:
                        fixes_applied.append(f"Alt tags adăugate pentru {fixed_count} imagini")
                else:
                    fixes_failed.append(f"Nu s-a putut accesa media library: {media_response.status_code}")
            except Exception as e:
                fixes_failed.append(f"Alt tags: {str(e)}")
                logging.error(f"[AUTO-FIX] Failed to fix alt tags: {e}")
        
        # 3. Generate Open Graph Suggestions
        if not audit["meta"].get("og_tags"):
            logging.info("[AUTO-FIX] Generating Open Graph tag suggestions")
            try:
                title = audit["meta"].get("title", site_url)
                description = audit["meta"].get("description", "")
                
                og_suggestions = {
                    "og:title": title,
                    "og:description": description[:200] if description else f"Vizitează {site_url}",
                    "og:type": "website",
                    "og:url": site_url,
                    "og:locale": "ro_RO"
                }
                
                suggestions.append({
                    "type": "open_graph",
                    "current": "Lipsesc",
                    "suggested": og_suggestions,
                    "action": "Adaugă în Yoast SEO sau în <head> al temei"
                })
                fixes_applied.append("Open Graph tags generate")
            except Exception as e:
                fixes_failed.append(f"Open Graph: {str(e)}")
        
        # 4. Title Optimization Suggestion
        title_length = audit["meta"].get("title_length", 0)
        if title_length < 30 or title_length > 60:
            logging.info("[AUTO-FIX] Generating title optimization suggestion")
            try:
                chat = LlmChat(
                    api_key=api_key,
                    session_id=f"autofix-title-{datetime.utcnow().timestamp()}",
                    system_message="Ești expert SEO. Optimizezi titluri pentru motoare de căutare. Răspunde DOAR cu titlul optimizat."
                ).with_model("gemini", "gemini-2.0-flash")
                
                current_title = audit["meta"].get("title", "")
                h1_texts = audit["headings"].get("h1_texts", [])
                
                prompt = f"""Optimizează acest titlu pentru SEO:
Titlu actual: {current_title}
Lungime actuală: {title_length} caractere
H1 pagină: {h1_texts[0] if h1_texts else 'N/A'}

Cerințe:
- Între 50-60 caractere
- Include cuvinte cheie principale
- Atractiv pentru utilizatori

Răspunde DOAR cu titlul optimizat:"""
                
                optimized_title = await chat.send_message(UserMessage(text=prompt))
                optimized_title = optimized_title.strip().strip('"').strip("'")
                
                if 40 <= len(optimized_title) <= 65:
                    suggestions.append({
                        "type": "title",
                        "current": current_title,
                        "suggested": optimized_title,
                        "action": "Actualizează în WordPress sau Yoast SEO"
                    })
                    fixes_applied.append(f"Titlu optimizat sugerat: {optimized_title[:40]}...")
            except Exception as e:
                fixes_failed.append(f"Title optimization: {str(e)}")
    
    # Calculate improvement
    original_score = audit.get("score", 0)
    potential_improvement = len(fixes_applied) * 5  # ~5 points per fix
    estimated_new_score = min(100, original_score + potential_improvement)
    
    return {
        "success": True,
        "url": site_url,
        "original_score": original_score,
        "original_grade": audit.get("grade", "?"),
        "estimated_new_score": estimated_new_score,
        "fixes_applied": fixes_applied,
        "fixes_failed": fixes_failed,
        "suggestions": suggestions,
        "total_issues_found": audit.get("total_issues", 0),
        "issues_addressed": len(fixes_applied) + len(suggestions),
        "timestamp": datetime.utcnow().isoformat()
    }
