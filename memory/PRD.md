# SEO Automation Platform - PRD

## CHANGELOG (Martie 2026)

- **19 Mar 2026**: Fix GSC Data + Pregătire SaaS
  
  ### FIX GSC DATE CORECTE ✅
  - Schimbat prioritate URL-uri: https:// fără www > https:// cu www > sc-domain:
  - Adăugat delay 3 zile pentru GSC (datele reale au delay)
  - Sincronizare GSC site cu WordPress site selectat
  - Logging detaliat pentru debug
  - Eliminat zile cu 0 la finalul graficului
  
  ### PREGĂTIRE SAAS ✅
  - Creat specificații complete în `/app/memory/SAAS_SPECS.md`
  - Plan: aplicație separată pe branch `saas`
  - Domeniu: app.clienti.ro
  - Planuri: Starter €19, Pro €49, Agency €99, Enterprise €199
  - Trial 7 zile, BYOAK (Bring Your Own API Keys)

- **18 Mar 2026 (PM - Late)**: Implementare Completă Strategie E-Commerce ✅
  
  ### FUNCȚIONALITĂȚI NOI IMPLEMENTATE (conform strategie_postare_automata.docx):
  
  #### 1. GSC OPPORTUNITIES SCORING (+15 pts) ✅
  - Nou endpoint `/api/search-console/opportunities` 
  - Identifică queries cu poziție 5-20 și CTR < 3%
  - Adaugă +15 puncte în scoring pentru topicuri ce match-uiesc oportunități GSC
  - Funcție helper `get_gsc_opportunities_for_scoring()`
  
  #### 2. TOPICS LOG - 90 ZILE SEMANTIC COOLDOWN ✅
  - Colecție nouă `topics_log` în MongoDB cu index
  - Funcții: `log_topic_used()`, `get_topics_in_cooldown()`, `is_topic_similar()`
  - Penalizare -20 pts pentru topicuri semantic similare în ultimele 90 zile
  - Toate articolele generate sunt logate automat
  
  #### 3. RETRY CU EXPONENTIAL BACKOFF ✅
  - 3 încercări cu backoff: 10s, 30s, 90s
  - Logging detaliat pentru fiecare retry
  - Alertă email la eșec complet
  
  #### 4. JOB FAILURE ALERTS ✅
  - Funcție `send_job_failure_alert()` trimite email la eșec
  - Include: job name, site name, error message, timestamp
  - Notifică toți utilizatorii admin
  
  #### 5. TONE PER SITE ✅
  - Nou câmp `tone` în configurația WordPress
  - Editabil din UI (WordPressPage.jsx)
  - Inclus în prompt-ul de generare articole
  - Ex: "cald, empatic, de încredere pentru mame"
  
  #### 6. SCORING ALGORITHM ÎMBUNĂTĂȚIT ✅
  - +40 pts pentru trending keywords (increased from 20)
  - +15 pts pentru GSC opportunities match (NOU)
  - -30 pts pentru cooldown 30 zile
  - -20 pts pentru similaritate semantică 90 zile (NOU)
  - -10 pts per keyword folosit recent
  
  - Fișiere modificate:
    - `backend/server.py`: GSC opportunities, topics_log, retry logic, job alerts, tone
    - `frontend/src/pages/WordPressPage.jsx`: câmp tone în editare

- **18 Mar 2026 (PM)**: Pagina Rapoarte Implementată ✅
  
  ### PAGINĂ NOUĂ: RAPOARTE DE PERFORMANȚĂ ✅
  - Creat `ReportsPage.jsx` - pagină dedicată pentru vizualizarea rapoartelor
  - Tab "Săptămânal" - statistici ultimele 7 zile
  - Tab "Lunar" - statistici ultimele 30 zile
  - Afișează: Total articole, Publicate, Cu produse, Cu trending
  - Metrici de calitate: Scor SEO mediu, Cuvinte medii per articol
  - Tipuri de articole, Statistici per site, Activitate zilnică
  - Adăugat link "Rapoarte" în meniu (cu icon BarChart3)
  
  ### GRAFICE VIZUALE ADĂUGATE ✅
  - **Area Chart** - Activitate Zilnică (articole generate vs publicate pe zi)
  - **Donut Pie Chart** - Distribuție Tipuri Articole cu procentaje
  - **Horizontal Bar Chart** - Performanță per Site (generate vs publicate)
  - **Progress Bars** - Metrici calitate (SEO score, word count)
  - **Mini Stats** - Rată publicare %, Link-uri produse
  - Folosește biblioteca Recharts pentru grafice interactive
  - Culori consistente: verde (#10b981), albastru (#3b82f6)
  - Tooltip-uri personalizate pentru toate graficele
  
  - Fișiere modificate:
    - `frontend/src/pages/ReportsPage.jsx` (NOU)
    - `frontend/src/components/DashboardLayout.jsx` (nav update)
    - `frontend/src/App.js` (route adăugat)

- **18 Mar 2026**: Fix-uri Bug-uri Recurente + Script Update Îmbunătățit
  
  ### 1. FIX: BIFA CALENDAR PENTRU PUBLICĂRI MANUALE ✅
  - Problema: Bifele apăreau doar pentru site-urile cu automatizare activă
  - Soluție: Acum toate articolele publicate (auto sau manual) apar cu bifă verde
  - Modificat logica în `AutomationPage.jsx` - secțiunea de afișare articole publicate
  
  ### 2. FIX: MANAGER BACKLINKS - TOATE SITE-URILE ✅
  - Problema: Email-urile de outreach se generau doar pentru site-uri cu articole publicate
  - Soluție: Nou endpoint `/api/backlinks/search-opportunities-with-emails`
    - Caută backlink-uri pentru TOATE site-urile
    - Generează email-uri de outreach automat
    - Include `site_id` în fiecare backlink pentru tracking
  - Butonul "Caută Oportunități Noi" folosește acum endpoint-ul complet
  
  ### 3. SCRIPT UPDATE.SH ÎMBUNĂTĂȚIT ✅
  - Verificare automată URL backend în docker-compose.yml
  - Detectează și corectează URL-uri localhost/preview
  - Opțiune `--force` pentru rebuild complet cu cache clean
  - Output colorat și pași clari 1-5
  - Validare existență director și docker-compose.yml

- **15 Mar 2026**: FINALIZARE COMPLETĂ - Toate Funcționalitățile Verificate și Funcționale
  
  ### 1. BIFELE PE CALENDAR ✅
  - Funcții noi: `isPublishedOnDate()`, `getArticlesForDate()`, `anyArticlePublishedOnDate()`
  - Conversie timezone UTC → Romania (Europe/Bucharest)
  - Articolele publicate fără programare apar ca card verde "Publicat"
  
  ### 2. NIȘELE ÎN ROMÂNĂ (AUTO-MIGRARE) ✅
  - La startup, nișele sunt actualizate automat în română
  - seamanshelp → "Cariere maritime, navigație și viața la bord"
  - jobsonsea → "Joburi maritime, recrutare echipaje și cariere offshore"
  - bestbuybabys → "Produse și sfaturi pentru bebeluși, copii și părinți"
  - azurelady → "Modă feminină elegantă și stil"
  - storeforladies → "Lenjerie intimă și îmbrăcăminte feminină"
  
  ### 3. KEYWORDS ZILNICE → ARTICOLE ✅
  - 5:00 AM: Generare keywords noi
  - 9:00 AM: Articolele folosesc keywords-urile generate
  - Funcție nouă: `generate_keywords_for_topic_from_keywords()`
  
  ### 4. EMAIL-URI BACKLINKS ✅
  - .ro → Email în ROMÂNĂ
  - Internațional → Email în ENGLEZĂ cu mențiune română
  
  ### 5. FACEBOOK TOATE PAGINILE ✅
  - 5 pagini configurate
  - Token sharing la reconectare
  - Link direct în mesaj: `👉 Citește articolul complet: [URL]`
  
  ### 6. IMAGINI RELEVANTE + ÎN INTERIOR ✅
  - Detectare nișă îmbunătățită
  - Inserare în articol cu fallback h2→h3→p
  
  ### 7. DIVERSIFICARE TEME + ROMÂNĂ ✅
  - Evită ultimele 3 categorii
  - Toate articolele în limba română

- **14 Mar 2026**: Fix-uri Majore pentru Articole, Imagini și Facebook
  - **FIX: LinkedIn Integration** - Schimbat de la Company Page la Personal Profile
    - Folosește `w_member_social` scope (deja autorizat în LinkedIn App)
    - Postează pe profilul personal al utilizatorului
    - Funcția nouă `post_to_linkedin_personal()` în `social_posting.py`
  - **NEW: Social Media Status Badges** pe pagina Site-uri WordPress
    - Badge-uri vizibile direct pe fiecare site card
    - "FB Conectat" (verde) / "FB Neconectat" (gri)
    - "LI Conectat" (albastru) / "LI Neconectat" (gri) - doar pentru seamanshelp
  - **NEW: Automatizare Backlink-uri** - Sistem complet automat
    - **Căutare zilnică la 6:00 AM** pentru oportunități noi gratuite (de la săptămânal)
    - **Generare automată email-uri outreach** pentru fiecare oportunitate nouă
    - **Sistem de aprobare email-uri** - tab nou "De Aprobat" în pagina Backlinks
    - Endpoint-uri noi:
      - `GET /api/backlinks/outreach/pending` - Email-uri în așteptare
      - `POST /api/backlinks/outreach/{id}/approve` - Aprobă și trimite email
      - `POST /api/backlinks/outreach/{id}/reject` - Respinge email
      - `POST /api/backlinks/outreach/approve-all` - Aprobă toate
      - `GET /api/backlinks/outreach/stats` - Statistici outreach
    - Frontend: Tab nou cu listă email-uri, buton "Aprobă & Trimite Toate"
  - **FIX: WordPressConfigResponse** - Adăugat câmpuri `facebook_connected` și `linkedin_connected`

- **04 Mar 2026**: Funcționalitate Indexare Site-Wide Completă
  - **NEW: Tab Audit Site-Wide** (`/indexing`) - Pagină completă cu 2 tab-uri
    - Tab 1: Indexare URL-uri individuale + Bulk indexare articole
    - Tab 2: Audit Complet Site-Wide cu:
      - Verificare robots.txt
      - Descoperire automată pagini din sitemap
      - Ping Google & Bing
      - IndexNow pentru Bing/Yandex (indexare instantă)
      - Verificare status Google Search Console
      - Scor general (A/B/C/D) cu recomandări
      - Istoric audituri
  - **NEW: Script update.sh** - Update VPS cu o singură comandă
  - Backend Endpoints: `/api/indexing/full-audit`, `/api/indexing/audits`, `/api/indexing/status/{site_id}`

- **03 Mar 2026**: Fix-uri Critice Automatizare + Funcționalități Noi
  - **FIX: Markdown → HTML** - Articolele publicate conțin acum HTML corect
  - **FIX: Anul 2024 → 2026** - Conținutul generat folosește anul curent
  - **FIX: Emailuri Duplicate** - Eliminat trimiterea dublă a notificărilor
  - **FIX: Ore de Publicare** - Scheduler respectă ora configurată
  - **FIX: Logging Detaliat** - Prefix `[AUTOMATION]` pentru debug
  - **NEW: Dashboard Monitorizare** (`/monitor`) - Status real-time per site
  - **NEW: Technical SEO Audit** (`/technical-audit`)
    - Scanare automată pentru: meta tags, headings, imagini, links, conținut
    - Scor SEO cu notă (A/B/C/D)
    - Identificare probleme tehnice: HTTPS, mobile, viteză, canonical
    - Istoric audituri
  - **NEW: Business Analysis AI** (`/business-analysis`)
    - Analiză AI completă a site-ului
    - Strategie SEO personalizată cu keywords recomandate
    - Oportunități de conținut și gap-uri identificate
    - Plan de acțiune 30 zile
    - Predicții trafic
  - **REFACTOR: Structură Backend Modulară**
    - `config.py` - Configurări centralizate (API keys, timezone, constante)
    - `models/__init__.py` - Toate modelele Pydantic (User, Article, WordPress, etc.)
    - `routes/auth.py` - Rutele de autentificare (pregătit pentru migrare)
    - `routes/__init__.py` - Export routes
    - `services/seo_analysis.py` - Logica pentru audit și business analysis
    - `server.py` acum importă din module (pregătit pentru separare completă)

## CHANGELOG (Februarie 2026)
- **21 Feb 2026**: Fix-uri critice și funcționalități noi
  - **FIX: Filtrare articole per site** - Web2Page și alte pagini filtrează acum corect articolele după site-ul selectat
  - **FIX: Refresh automat GSC** - Dashboard-ul actualizează automat statisticile GSC la schimbarea site-ului fără refresh manual
  - **FIX: Imagini mari și unice** - Pexels folosește acum `large2x` (1880px) și randomizare pentru imagini unice per articol
  - **FIX: Email notificări** - Corectat EMERGENT_API_KEY în EMERGENT_LLM_KEY pentru funcționarea corectă a LLM-ului
  - **NOU: Jurnal Publicări** - Tabel în secțiunea Automatizare cu data și ora exactă a publicării pentru fiecare articol pe fiecare site
  - **NOU: Endpoint /api/automation/publication-log** - Returnează istoric detaliat cu site_name, published_at, wp_post_url
  - **ÎMBUNĂTĂȚIT: Tabs în AutomationPage** - "Setări & Calendar" și "Jurnal Publicări"

## CHANGELOG (Decembrie 2025)
- **13 Dec 2025**: Sistem Complet Backlinks Automate
  - Căutare săptămânală automată (luni 10:00) pentru oportunități noi gratuite
  - Buton manual "Caută Noi Oportunități" în pagina Backlinks
  - Raport SEO lunar automat (1 a lunii, ora 9:00) pe email
  - Sistem Web 2.0 - generare posturi pentru Medium, Blogger, LinkedIn, Tumblr, Pinterest
  - Pagină nouă `/web2` pentru management Web 2.0
- **13 Dec 2025**: Sistem Backlink Outreach Automat
  - Endpoint-uri noi: `/api/backlinks/outreach/prepare`, `/api/backlinks/outreach/{id}/send`
  - AI găsește articolul relevant pentru fiecare site de backlink
  - Generare automată email personalizat cu AI
  - Opțiune trimitere manuală (preview + editare) sau automată
  - Tracking status: draft → trimis → răspuns primit
  - UI cu tabs (Oportunități / Outreach), statistici, dialog editare
- **13 Dec 2025**: Fix Scheduler Timezone România
  - Scheduler-ul folosește acum `Europe/Bucharest` 
  - Orele de generare sunt interpretate în ora României
- **12 Dec 2025**: Widget statistici articole generate per site pe dashboard
  - Adăugat endpoint `/api/automation/stats-per-site` pentru statistici lunare
  - Widget vizual cu grafic bar chart orizontal pe dashboard
  - Afișare articole generate în ultima lună per site cu status (activ/pauză/inactiv)
  - Indicator procent din ținta lunară
- **12 Dec 2025**: Fix bug calendar automatizare - toate site-urile active se afișează corect în calendar
  - Corectat `getScheduledDates()` pentru a exclude site-urile în pauză
  - Adăugat verificare duplicări pentru site-uri
  - Actualizat legenda și condițiile de afișare calendar

## Original Problem Statement
Aplicație de automatizare SEO care include:
- 30 articole SEO/lună, scrise și publicate automat
- Cercetare cuvinte-cheie + calendar editorial 90 zile
- Backlinks automate (300+ site-uri de calitate incluse)
- Publicare automată pe WordPress
- Tracking Google Search Console
- 100% white-label — fără logo sau mențiune terțe

## Architecture
- **Frontend**: React + TailwindCSS + Shadcn/UI + Recharts
- **Backend**: FastAPI + MongoDB + Motor (async) + APScheduler
- **AI Integration**: emergentintegrations with GPT-4o
- **Email**: Resend API
- **Deployment**: Docker Compose (local) / MongoDB Atlas (cloud)
- **Theme**: Cyber-Swiss Dark (Primary: #00E676, Background: #050505)

## ✅ IMPLEMENTAT COMPLET

### Phase 1 - Core MVP
- [x] JWT Authentication (register/login)
- [x] Article generation with GPT-4o (HTML format)
- [x] Keyword research AI
- [x] Editorial calendar (manual + 90-day AI generation)
- [x] Backlinks database + AI generation per niche
- [x] WordPress multi-site connection & publishing
- [x] White-label settings

### Phase 2 - Google Search Console
- [x] GSC OAuth Integration
- [x] Real-time traffic chart (clicks, impressions)
- [x] Top queries & pages
- [x] Date range filtering (7, 28, 90, 180 days)

### Phase 3 - Email & Templates
- [x] Email notifications (Resend) - on article publish
- [x] 5 article templates (Ghid, Listicle, Comparație, How-To, Recenzie)
- [x] Template-based generation

### Phase 4 - Multi-Site Support
- [x] MongoDB Atlas cloud database
- [x] Multiple WordPress sites per user
- [x] Global site selector in header
- [x] Site context across all pages

### Phase 5 - Daily SEO Articles Automation ✅
- [x] Site-specific automation (manual/automatic mode)
- [x] Frequency: daily, every 2/3 days, weekly
- [x] Generation hour (0-23)
- [x] Article length (short/medium/long)
- [x] Product links integration
- [x] Dashboard widget with stats
- [x] **Browser push notifications**
- [x] **Visual calendar for scheduled generations**
- [x] APScheduler backend with per-site jobs

### Phase 6 - Images & Categories (February 2025) ✅
- [x] **Featured image** - 1200px, uploaded to WordPress
- [x] **Content images** - 4-6 images inserted in article (~800px)
- [x] Images from Pexels (free, matching article theme)
- [x] **WordPress categories** - 6-8 per niche, auto-created
- [x] Auto-assign category on publish
- [x] **GSC caching** - 5 minute cache for faster loading

---

## 📋 CE MAI RĂMÂNE DE FĂCUT

### P0 - Critical (Core Features Missing)
**Nimic** - MVP complet ✅

### P1 - High Priority (Funcționalități Principale)
~~1. **Business Analysis AI** - Analiză site și strategie SEO personalizată~~ ✅ IMPLEMENTAT
~~2. **Technical SEO Audit** - Scanare site pentru probleme tehnice~~ ✅ IMPLEMENTAT

### P1.5 - Refactorizare
~~3. **Început refactorizare `server.py`** - Creat folder `services/`~~ ✅ ÎNCEPUT
4. **Continuare refactorizare** - Separare routes, models (server.py > 4000 linii)

### P2 - Medium Priority (Îmbunătățiri)
4. **AI Image Generation** - Imagini featured pentru fiecare articol (OpenAI DALL-E sau Gemini)
5. **Email Outreach pentru Backlinks** - Generare email-uri personalizate pentru outreach
6. **LLM Visibility Tracking** - Tracking cum apare site-ul în răspunsurile ChatGPT/Perplexity
7. **Monthly SEO Report** - Raport automat lunar pe email

### P3 - Low Priority (Nice to Have)
8. **Shopify Integration** - Publicare articole pe Shopify
9. **Wix Integration** - Publicare articole pe Wix
10. **Webflow Integration** - Publicare articole pe Webflow
11. **Social Media Auto-Post** - Postare automată pe Facebook/LinkedIn
12. **Team Collaboration** - Mai mulți utilizatori pe același cont
13. **API Access** - API pentru integrări externe

---

## Configurare Necesară

### Email (Opțional - pentru notificări)
```env
RESEND_API_KEY=re_xxxx
```

### Google Search Console (Opțional)
```env
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=https://your-domain/api/search-console/callback
```

---

## DB Collections
- `users` - Conturi utilizatori
- `wordpress_configs` - Site-uri WordPress conectate
- `site_automation_settings` - Setări automatizare per site
- `articles` - Articole generate
- `keywords` - Rezultate keyword research
- `calendar` - Calendar editorial
- `niche_backlinks` - Oportunități backlink generate AI

---

## Key Files
- `backend/server.py` - Tot backend-ul (FastAPI + MongoDB + APScheduler)
- `frontend/src/pages/AutomationPage.jsx` - Pagina automatizare cu calendar
- `frontend/src/pages/DashboardPage.jsx` - Dashboard cu widget automatizare
- `frontend/src/components/DashboardLayout.jsx` - Layout + navigație
