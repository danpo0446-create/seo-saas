# SEO Automation SaaS - Product Requirements Document

## Original Problem Statement
Implementare aplicație SaaS pe branch separat conform specificațiilor pentru SEO Automation.
- **Domeniu**: app.clienti.ro (production: saas.seamanshelp.com)
- **Planuri**: Starter €19, Pro €49, Agency €99, Enterprise €199
- **Trial**: 7 zile gratuit
- **BYOAK**: Clienții își pun propriile API keys

## Latest Updates (26 Martie 2026)

### ✅ AI Functionality Fix Completed
- **Problem**: AI functions (Keyword Research, Article Generation) were broken due to missing `session_id` parameter in `LlmChat` calls
- **Solution**: 
  1. Added `session_id=str(uuid.uuid4())` to all 14 `LlmChat` instances in `/app/backend/server.py`
  2. Implemented BYOAK (Bring Your Own API Key) priority system:
     - First checks user's own API keys (openai_key, gemini_key)
     - Falls back to platform's `EMERGENT_LLM_KEY` if user has no keys
  3. Created helper functions: `get_llm_api_key()` and `create_llm_chat()`

### Testing Status
- ✅ Keyword Research: Working (tested with curl)
- ✅ Article Generation: Working (tested with curl - generated 2218 word article)
- ✅ BYOAK logic: Working (logs show fallback to platform key when user has no keys)

## Architecture

### Backend (FastAPI)
```
/app/backend/
├── server.py              # Main FastAPI app with all routes
├── saas/
│   ├── plans.py           # Plan definitions and limits
│   ├── models.py          # Pydantic models for SaaS
│   ├── routes.py          # SaaS API routes (subscriptions, checkout, BYOAK)
│   ├── admin_routes.py    # Admin API routes (users, stats, actions)
│   ├── subscription_service.py  # Business logic for subscriptions
│   ├── email_service.py   # Email notifications (Resend)
│   └── invoice_service.py # PDF invoice generation
└── .env                   # Environment variables
```

### Frontend (React)
```
/app/frontend/src/
├── pages/
│   ├── LandingPage.jsx    # Public landing page at /
│   ├── PricingPage.jsx    # Pricing comparison at /pricing
│   ├── BillingPage.jsx    # Billing & BYOAK at /app/billing
│   ├── AdminDashboard.jsx # Admin panel at /app/admin
│   ├── ContactPage.jsx    # Contact page at /contact
│   ├── TermsPage.jsx      # Terms at /terms
│   ├── PrivacyPage.jsx    # Privacy policy at /privacy
│   └── ... (existing pages)
├── App.js                 # Routes configuration
└── components/
    └── DashboardLayout.jsx # Sidebar with Admin link for admins
```

### Database (MongoDB)
Collections:
- `users` - User accounts (with `role` field: "user" or "admin")
- `subscriptions` - Subscription status, plan, limits, usage
- `user_api_keys` - Encrypted BYOAK keys
- `payment_transactions` - Stripe payment records
- `invoices` - Generated invoices
- `page_content` - Editable footer page content (for admin)

## What's Been Implemented

### Date: 2026-03-20 (Latest)

#### Admin Dashboard & Footer Pages ✅
- Admin Dashboard at `/app/admin` with:
  - Statistics: Total Users, Active Subscriptions, Total Articles, Sites Connected
  - Financial: Monthly Revenue, Trial Users, Active Today
  - Plan Breakdown distribution
  - User list with search, pagination
  - Actions: Edit subscription (plan/status), Toggle admin role, Delete user
- Admin link in sidebar (red color, only visible to admin users)
- Footer pages: `/contact`, `/terms`, `/privacy`
- Footer links on Landing Page and Pricing Page
- Admin email: seamanshelp2021@gmail.com

### Previous Implementation (2026-03-19)

#### SaaS Core
- ✅ Subscription plans model with limits
- ✅ Trial subscription creation on user registration
- ✅ Usage tracking (articles, sites)
- ✅ Limit enforcement middleware
- ✅ BYOAK encrypted key storage

#### Stripe Integration
- ✅ Checkout session creation
- ✅ Payment status verification
- ✅ Webhook handler for payment events
- ✅ Subscription upgrade on successful payment
- ✅ Billing Portal endpoint
- ✅ Annual billing with 20% discount

#### Analytics & Reporting
- ✅ ROI & Estimated Value dashboard
- ✅ Usage analytics
- ✅ PDF invoice generation
- ✅ Invoice download

#### Email Notifications (Resend)
- ✅ Welcome email on registration
- ✅ Trial reminder (2 days before expiration)
- ✅ Trial expired notification
- ✅ Payment success confirmation
- ⚠️ Requires RESEND_API_KEY in production

## API Endpoints

### Admin Endpoints (require admin role)
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/users` - List all users with subscription info
- `GET /api/admin/users/{user_id}` - User details
- `PATCH /api/admin/users/{user_id}/role` - Change user role
- `PATCH /api/admin/users/{user_id}/subscription` - Edit subscription
- `POST /api/admin/users/{user_id}/reset-password` - Reset user password (manual)
- `DELETE /api/admin/users/{user_id}` - Delete user and data
- `GET /api/admin/content` - Get editable page content
- `PUT /api/admin/content/{page_id}` - Update page content
- `GET /api/admin/platform-settings` - Get platform API keys status
- `PUT /api/admin/platform-settings` - Update Stripe/Resend keys
- `PUT /api/admin/change-password` - Change admin password

### SaaS Endpoints
- `GET /api/saas/plans` - Get all plans
- `GET /api/saas/subscription` - Get user subscription
- `GET /api/saas/subscription/usage` - Get usage stats
- `POST /api/saas/checkout` - Create Stripe checkout
- `GET /api/saas/checkout/status/{session_id}` - Check payment
- `GET /api/saas/api-keys` - Get BYOAK status
- `PUT /api/saas/api-keys` - Update BYOAK keys
- `GET /api/saas/invoices` - List invoices
- `GET /api/saas/invoices/{id}/pdf` - Download invoice PDF

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- ✅ Admin Dashboard implementation
- ✅ Footer pages (Contact, Terms, Privacy)
- ✅ Admin user management
- ✅ Buton "Autentificare" funcționează corect → duce la /login
- ✅ Endpoint resetare manuală parolă utilizator (Admin)
- ✅ Script deploy.sh pentru automatizare deployment VPS

### P1 (High) - Pending
- [ ] Configure production Stripe keys on VPS
- [ ] Configure RESEND_API_KEY on VPS for email notifications
- [ ] Update contact info in Contact page from admin

### P2 (Medium)
- [ ] Team members for Agency/Enterprise plans
- [ ] Referral program

### P3 (Nice to have)
- [ ] API rate limiting per plan
- [ ] Custom domain white-label

## Test Credentials

### Admin Account
- Email: seamanshelp2021@gmail.com
- Password: admin123
- Role: admin
- Plan: Enterprise

### Test Account
- Email: test@example.com
- Password: test123
- Role: user

## Deployment Notes

### Production (VPS - saas.seamanshelp.com)
- The `emergentintegrations` library is mocked on VPS
- Frontend changes require: `npm run build` then restart nginx
- Backend changes require: `sudo systemctl restart seo-saas`
- SSL configured with Certbot
- **Script deploy.sh**: `/app/deploy.sh` - automatizează deploy-ul

### Environment Variables Needed for Production
```
STRIPE_API_KEY=sk_live_... (production key)
RESEND_API_KEY=re_... (production key)
```

### Deploy Commands (VPS)
Pentru deploy rapid, folosește scriptul:
```bash
cd /var/www/seo-saas && ./deploy.sh
```

Sau manual:
```bash
cd /var/www/seo-saas && git checkout -- . && git pull origin main && cd frontend && npm run build && sudo systemctl restart seo-saas
```

## Changelog

### 2026-12 (Curent)
- ✅ Fix buton "Autentificare" - ruta corectă /login
- ✅ Endpoint `POST /api/admin/users/{user_id}/reset-password` - resetare manuală parolă
- ✅ Script `deploy.sh` pentru automatizare deployment VPS
