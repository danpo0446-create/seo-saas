# SEO Automation SaaS - Product Requirements Document

## Original Problem Statement
Implementare aplicație SaaS pe branch separat conform specificațiilor pentru SEO Automation.
- **Domeniu**: app.clienti.ro
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
│   └── subscription_service.py  # Business logic for subscriptions
└── .env                   # Environment variables
```

### Frontend (React)
```
/app/frontend/src/
├── pages/
│   ├── LandingPage.jsx    # Public landing page at /
│   ├── PricingPage.jsx    # Pricing comparison at /pricing
│   ├── BillingPage.jsx    # Billing & BYOAK at /app/billing
│   └── ... (existing pages)
├── App.js                 # Routes configuration
└── components/
    └── DashboardLayout.jsx
```

### Database (MongoDB)
Collections:
- `users` - User accounts
- `subscriptions` - Subscription status, plan, limits, usage
- `user_api_keys` - Encrypted BYOAK keys
- `payment_transactions` - Stripe payment records

## Core Requirements (Static)

### Subscription Plans
| Plan       | Price/mo | Sites | Articles/mo | Features                        |
|------------|----------|-------|-------------|----------------------------------|
| Starter    | €19      | 1     | 15          | Basic features                   |
| Pro        | €49      | 5     | 50          | + GSC, Backlinks, Reports        |
| Agency     | €99      | 20    | 200         | + WooCommerce, Social, Audit     |
| Enterprise | €199     | ∞     | ∞           | Full access, API, White-label    |

### Trial Configuration
- Duration: 7 days
- Features: Pro-level (5 sites, 10 articles)
- Status: `trialing` → `active` (after payment) or `expired`

### BYOAK (Bring Your Own API Keys)
- OpenAI API Key (for GPT article generation)
- Google Gemini API Key (alternative AI)
- Resend API Key (email notifications)
- Pexels API Key (article images)

## What's Been Implemented

### Date: 2026-03-19

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

#### Frontend Pages
- ✅ Landing page with hero, features, pricing preview, testimonials
- ✅ Pricing page with all 4 plans comparison
- ✅ Billing page with subscription status and usage
- ✅ BYOAK tab for API keys configuration

#### API Endpoints
- `GET /api/saas/plans` - Get all plans
- `GET /api/saas/subscription` - Get user subscription
- `GET /api/saas/subscription/usage` - Get usage stats
- `POST /api/saas/checkout` - Create Stripe checkout
- `GET /api/saas/checkout/status/{session_id}` - Check payment
- `GET /api/saas/api-keys` - Get BYOAK status
- `PUT /api/saas/api-keys` - Update BYOAK keys
- `POST /api/webhook/stripe` - Stripe webhook

## Prioritized Backlog

### P0 (Critical)
- [ ] Configure production Stripe keys
- [ ] Setup domain (app.clienti.ro)

### P1 (High)
- [ ] Email notifications on trial expiration
- [ ] Billing portal integration
- [ ] Monthly usage reset scheduler

### P2 (Medium)
- [ ] Annual billing option (20% discount)
- [ ] Invoice PDF generation
- [ ] Usage analytics dashboard
- [ ] Referral program

### P3 (Nice to have)
- [ ] Team members for Agency/Enterprise
- [ ] API rate limiting per plan
- [ ] Custom domain white-label

## Next Tasks
1. Configure production Stripe account
2. Setup email notifications (Resend) for:
   - Welcome email on registration
   - Trial expiration reminder (day 5)
   - Payment confirmation
   - Usage limit warnings
3. Add billing portal for subscription management
4. Deploy to production domain

## User Personas
1. **Blogger** - Uses Starter, 1 site, occasional articles
2. **Freelancer** - Uses Pro, multiple client sites, regular content
3. **Agency** - Uses Agency/Enterprise, high volume, needs automation
