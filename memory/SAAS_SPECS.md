# SEO Automation SaaS - Specificații pentru Sesiune Nouă

## Informații Proiect

**Domeniu SaaS:** app.clienti.ro
**Aplicație existentă:** app.seamanshelp.com (rămâne separată pentru owner)
**VPS:** Hostinger KVM 1 (4GB RAM, 50GB disk) - same server

---

## Arhitectură

### Aplicația Owner (existentă)
- Path: `/root/seo-app`
- Branch: `main`
- DB: `test_database`
- Fără limite, fără Stripe

### Aplicația SaaS (de creat)
- Path: `/root/seo-saas`
- Branch: `saas`
- DB: `seo_saas`
- Cu Stripe, planuri, limite, BYOAK

---

## Funcționalități de Implementat

### 1. Stripe Integration
- Checkout Session pentru subscripții
- Customer Portal pentru management
- Webhook pentru evenimente (payment success, cancel, etc.)
- Test keys disponibile în pod

### 2. Planuri Subscripție

| Plan | ID | Site-uri | Articole/lună | Preț |
|------|-----|----------|---------------|------|
| Starter | starter | 1 | 15 | €19/lună |
| Pro | pro | 5 | 50 | €49/lună |
| Agency | agency | 20 | 200 | €99/lună |
| Enterprise | enterprise | ∞ | ∞ | €199/lună |

### 3. Trial Gratuit
- 7 zile fără card
- Acces la toate funcționalitățile (plan Pro)
- Reminder email la ziua 5
- Blocare după expirare

### 4. BYOAK (Bring Your Own API Keys)
Clienții își pun propriile keys pentru:
- OpenAI / Gemini (generare articole)
- Resend (email-uri)
- Pexels (imagini)

În setări: formular pentru adăugare keys, validare, stocare criptată.

### 5. Limite per Plan
- Număr site-uri WordPress
- Număr articole generate/lună
- Blocare la depășire + upsell

### 6. Landing Page
- Hero section cu beneficii
- Funcționalități cheie
- Pricing table
- Testimoniale (placeholder)
- FAQ
- CTA → Register

### 7. Pagini Noi
- `/` - Landing page
- `/pricing` - Planuri detaliate
- `/register` - Înregistrare cu trial
- `/login` - Autentificare
- `/dashboard` - Aplicația (după login)
- `/settings/billing` - Stripe Customer Portal
- `/settings/api-keys` - BYOAK

---

## Modificări Backend

### Modele noi (MongoDB):
```python
# subscriptions collection
{
    "user_id": "...",
    "stripe_customer_id": "cus_...",
    "stripe_subscription_id": "sub_...",
    "plan": "pro",  # starter/pro/agency/enterprise
    "status": "active",  # active/trialing/canceled/past_due
    "trial_ends_at": "2026-03-26T...",
    "current_period_end": "2026-04-19T...",
    "sites_limit": 5,
    "articles_limit": 50,
    "articles_used_this_month": 12
}

# user_api_keys collection (BYOAK)
{
    "user_id": "...",
    "openai_key": "encrypted_...",
    "gemini_key": "encrypted_...",
    "resend_key": "encrypted_...",
    "pexels_key": "encrypted_..."
}
```

### Middleware limite:
- Verifică plan la fiecare request
- Blochează dacă limita e depășită
- Returnează `402 Payment Required` sau `403 Forbidden`

---

## Modificări Frontend

### Componente noi:
- `LandingPage.jsx`
- `PricingPage.jsx`
- `BillingSettings.jsx`
- `ApiKeysSettings.jsx`
- `TrialBanner.jsx` (afișează zile rămase)
- `UpgradeModal.jsx` (când atinge limita)

### Protecție rute:
- Verifică subscripție activă
- Redirect la pricing dacă trial expirat

---

## Deploy pe VPS

### Structură finală:
```
/root/seo-app/     → app.seamanshelp.com (owner)
/root/seo-saas/    → app.clienti.ro (SaaS)
```

### Nginx config pentru app.clienti.ro:
```nginx
server {
    listen 80;
    server_name app.clienti.ro;
    
    location /api {
        proxy_pass http://localhost:8002;
    }
    
    location / {
        proxy_pass http://localhost:3001;
    }
}
```

### Docker compose (porturi diferite):
- Backend: 8002 (în loc de 8001)
- Frontend: 3001 (în loc de 3000)

---

## Pași Implementare

1. [ ] Creez branch `saas` din `main`
2. [ ] Modific porturi în docker-compose
3. [ ] Adaug Stripe integration (folosind playbook)
4. [ ] Creez modele subscriptions și user_api_keys
5. [ ] Implementez middleware limite
6. [ ] Creez BYOAK în settings
7. [ ] Creez landing page
8. [ ] Creez pricing page
9. [ ] Modific register pentru trial
10. [ ] Adaug billing settings cu Stripe Portal
11. [ ] Testez flow complet
12. [ ] Deploy pe VPS

---

## Notă pentru Agent

- Repository GitHub: același ca aplicația owner
- Branch pentru SaaS: `saas`
- Sincronizare: `git merge main` pentru updates comune
- Stripe test keys: disponibile în environment
- Limba: Română pentru UI

---

## Contact Owner

Pentru întrebări despre:
- Planuri/prețuri: poate modifica ulterior
- Design: preferă stilul actual (dark theme)
- Funcționalități: focus pe simplitate
