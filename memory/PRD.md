# SEO Automation SaaS - Product Requirements Document

## Original Problem Statement
Implementare aplicație SaaS pe branch separat conform specificațiilor pentru SEO Automation.
- **Domeniu**: app.clienti.ro (production: saas.seamanshelp.com)
- **Planuri**: Starter €19, Pro €49, Agency €99, Enterprise €199
- **Trial**: 7 zile gratuit
- **BYOAK**: Clienții își pun propriile API keys

## Architecture

### Backend (FastAPI)
```
/app/backend/
├── server.py              # Main FastAPI app with all routes
├── saas/
│   ├── plans.py           # Plan definitions and limits
│   ├── models.py          # Pydantic models for SaaS
│   ├── routes.py          # SaaS API routes (subscriptions, checkout, BYOAK)
│   ├── admin_routes.py    # Admin API routes (users, stats, actions, password reset)
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
│   ├── BillingPage.jsx    # Billing, BYOAK & Security at /app/billing
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

### Date: 2026-04-03 (Latest)

#### Notification Center ✅
- **NEW** Componentă `NotificationCenter.jsx` - dropdown cu notificări în header
- **NEW** Endpoint-uri: GET/PUT/DELETE `/api/notifications/*`
- **NEW** Notificări automate pentru: succes generare articol, erori scheduler, job-uri recuperate
- **NEW** Tipuri de notificări: success (verde), error (roșu), warning (galben), info (albastru), scheduler (violet)
- **NEW** Badge cu număr notificări necitite în header
- **NEW** Funcționalități: mark as read, mark all as read, delete, clear all
- Collection MongoDB: `notifications`

#### Facebook Page Selection UI ✅
- **NEW** Dropdown selector în modal-ul social pentru alegerea paginii Facebook
- **NEW** State-uri pentru `selectedFacebookPage` și `savingFacebookPage` în WordPressPage.jsx
- **NEW** Funcția `selectFacebookPage()` care salvează pagina selectată via API
- UI: Apare automat când `pages_pending=true` și `available_pages` conține pagini
- După selectare, badge-ul "Conectat" apare cu butoanele "Test Post" și "Deconectează"

#### Scheduler Improvements ✅
- **FIX** Adăugat `misfire_grace_time=7200` (2 ore) pentru a prinde job-uri ratate
- **FIX** Adăugat `coalesce=True` pentru a rula o singură dată dacă multiple execuții au fost ratate
- **FIX** Adăugat `max_instances=1` pentru a preveni execuții paralele
- **NEW** Job de recovery zilnic la 10:30 AM care verifică job-urile ratate
- **NEW** Logare detaliată pentru diagnosticare scheduler

#### Social BYOAK Architecture ✅
- Facebook App ID/Secret stocat în `user_api_keys` collection
- LinkedIn Client ID/Secret stocat în `user_api_keys` collection
- OAuth flow folosește cheile utilizatorului pentru autentificare
- Pages disponibile salvate în DB pentru selecție ulterioară

### Date: 2026-04-02

#### Backlink Automation Module ✅
- **NEW** `BacklinkAutomationPage.jsx` - Pagină monitorizare automatizare backlinks
- **NEW** `GET /api/backlinks/automation-status` - Status automatizare per site
- **NEW** `run_daily_backlink_outreach()` - Automatizare zilnică la 12:30 România
- **NEW** Scheduler CronTrigger pentru outreach la 12:30
- Features: Max 15 emailuri/zi/site, oportunități FREE only, emailuri personalizate AI
- Route: `/app/backlinks/automation`
- Link în sidebar după "Backlinks"

### Date: 2026-03-29

#### Password Management ✅
- User password change: `/api/auth/change-password` - users can change their own password
- Admin reset user password: `/api/admin/users/{user_id}/reset-password` - admin can reset any user's password
- UI: Security tab in BillingPage (`/app/billing` -> tab "Securitate")
- UI: Reset password dialog in AdminDashboard (`/app/admin` -> Users tab -> Key icon)
- Validation: minimum 6 characters, current password verification
- **Email notifications**: 
  - User receives confirmation when changing own password
  - User receives email with temp password when admin resets it

### Date: 2026-03-20

#### Admin Dashboard & Footer Pages ✅
- Admin Dashboard at `/app/admin` with:
  - Statistics: Total Users, Active Subscriptions, Total Articles, Sites Connected
  - Financial: Monthly Revenue, Trial Users, Active Today
  - Plan Breakdown distribution
  - User list with search, pagination
  - Actions: Edit subscription (plan/status), Toggle admin role, Delete user, Reset password
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

### Auth Endpoints
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user
- `POST /api/auth/forgot-password` - Request password reset
- `PUT /api/auth/change-password` - Change user password (requires auth)

### Admin Endpoints (require admin role)
- `GET /api/admin/stats` - Platform statistics
- `GET /api/admin/users` - List all users with subscription info
- `GET /api/admin/users/{user_id}` - User details
- `PATCH /api/admin/users/{user_id}/role` - Change user role
- `PATCH /api/admin/users/{user_id}/subscription` - Edit subscription
- `DELETE /api/admin/users/{user_id}` - Delete user and data
- `POST /api/admin/users/{user_id}/reset-password` - Admin reset user password
- `PUT /api/admin/change-password` - Admin change own password
- `GET /api/admin/content` - Get editable page content
- `PUT /api/admin/content/{page_id}` - Update page content
- `GET /api/admin/platform-settings` - Get platform API keys status
- `PUT /api/admin/platform-settings` - Update platform API keys

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

### Notification Endpoints
- `GET /api/notifications` - Get all notifications with unread count
- `PUT /api/notifications/{id}/read` - Mark notification as read
- `PUT /api/notifications/read-all` - Mark all as read
- `DELETE /api/notifications/{id}` - Delete single notification
- `DELETE /api/notifications/clear-all` - Clear all notifications

### Social Media Endpoints
- `GET /api/social/status/{site_id}` - Get Facebook/LinkedIn connection status + available_pages
- `GET /api/social/facebook/auth-url/{site_id}` - Get Facebook OAuth URL
- `GET /api/social/facebook/pages/{site_id}` - Get available Facebook pages
- `POST /api/social/facebook/select-page/{site_id}?page_id={id}` - Select Facebook page
- `DELETE /api/social/facebook/disconnect/{site_id}` - Disconnect Facebook
- `POST /api/social/facebook/test-post/{site_id}` - Test Facebook posting
- `GET /api/social/linkedin/auth-url/{site_id}` - Get LinkedIn OAuth URL
- `DELETE /api/social/linkedin/disconnect/{site_id}` - Disconnect LinkedIn
- `POST /api/social/linkedin/test-post/{site_id}` - Test LinkedIn posting

## Prioritized Backlog

### P0 (Critical) - DONE ✅
- ✅ Admin Dashboard implementation
- ✅ Footer pages (Contact, Terms, Privacy)
- ✅ Admin user management
- ✅ User password change functionality
- ✅ Admin password reset for users
- ✅ Facebook Page Selection UI
- ✅ Scheduler reliability improvements (misfire_grace_time, daily recovery)

### P1 (High) - Pending
- [ ] Verificare email sending reliability (Resend/SendGrid) via BYOAK
- [ ] Configure production Stripe keys on VPS
- [ ] Configure RESEND_API_KEY on VPS for email notifications
- [ ] Update contact info in Contact page from admin

### P2 (Medium)
- [ ] Referral program
- [ ] Team members for Agency/Enterprise plans

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
- Email: test091853@example.com
- Password: test123
- Role: user

## Deployment Notes

### Production (VPS - saas.seamanshelp.com)
- The `emergentintegrations` library is mocked on VPS
- Frontend changes require: `npm run build` then restart nginx
- Backend changes require: `sudo systemctl restart seo-saas`
- SSL configured with Certbot

### Environment Variables Needed for Production
```
STRIPE_API_KEY=sk_live_... (production key)
RESEND_API_KEY=re_... (production key)
```

### Deploy Commands for VPS
```bash
cd /var/www/seo-saas
git pull origin main
cd frontend && npm run build
sudo systemctl restart seo-saas
```
