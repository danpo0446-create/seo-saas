# SEO Automation SaaS - Ghid Deploy VPS

## Cerințe Minime VPS
- Ubuntu 22.04 / Debian 12
- 2GB RAM minim
- 20GB disk
- Acces root/sudo

## Pași Deploy

### 1. Salvează în GitHub
Folosește butonul **"Save to Github"** din interfața Emergent.

### 2. Conectare VPS
```bash
ssh root@IP_VPS
```

### 3. Descarcă și rulează scriptul
```bash
# Descarcă scriptul
curl -O https://raw.githubusercontent.com/danpo0446-create/seo-automation/main/deploy-vps.sh

# SAU creează manual și lipește conținutul
nano deploy-vps.sh

# Fă-l executabil
chmod +x deploy-vps.sh

# IMPORTANT: Editează cheile API în script ÎNAINTE de rulare
nano deploy-vps.sh
# Modifică secțiunea CONFIGURĂRI cu cheile tale

# Rulează
sudo bash deploy-vps.sh
```

### 4. Configurare DNS
În panoul de control DNS (Cloudflare, etc.):
```
Type: A
Name: app
Value: IP_VPS_TAU
TTL: Auto
```

### 5. Configurare Stripe Webhook
1. Mergi la https://dashboard.stripe.com/webhooks
2. Add endpoint: `https://app.clienti.ro/api/webhook/stripe`
3. Select events: `checkout.session.completed`, `payment_intent.succeeded`

## Comenzi Utile

```bash
# Vezi logs backend în timp real
journalctl -u seo-saas -f

# Restart backend
sudo systemctl restart seo-saas

# Restart nginx
sudo systemctl restart nginx

# Status toate serviciile
sudo systemctl status seo-saas mongod nginx

# Editare .env backend
sudo nano /var/www/seo-saas/backend/.env

# Rebuild frontend (după modificări)
cd /var/www/seo-saas/frontend
sudo yarn build
sudo systemctl reload nginx

# Update cod din GitHub
cd /var/www/seo-saas
sudo git pull
sudo systemctl restart seo-saas
cd frontend && sudo yarn build
```

## Troubleshooting

### Backend nu pornește
```bash
# Verifică logs
journalctl -u seo-saas -n 50

# Verifică dacă portul e ocupat
sudo lsof -i :8002

# Test manual
cd /var/www/seo-saas/backend
source venv/bin/activate
python -c "from server import app; print('OK')"
```

### Eroare MongoDB
```bash
sudo systemctl status mongod
sudo systemctl restart mongod
```

### Eroare Nginx
```bash
sudo nginx -t  # Test config
sudo tail -f /var/log/nginx/error.log
```

### SSL nu funcționează
```bash
sudo certbot --nginx -d app.clienti.ro
```

## Chei API Necesare

| Cheie | De unde | Obligatoriu |
|-------|---------|-------------|
| EMERGENT_LLM_KEY | Emergent Platform | ✅ Da |
| STRIPE_API_KEY | dashboard.stripe.com | ✅ Da |
| RESEND_API_KEY | resend.com | ⚠️ Pentru email |
| PEXELS_API_KEY | pexels.com/api | ⚠️ Pentru imagini |

## Structura Fișiere pe VPS

```
/var/www/seo-saas/
├── backend/
│   ├── .env              # Configurări backend
│   ├── server.py         # FastAPI app
│   ├── venv/             # Python virtual environment
│   └── saas/             # Module SaaS
├── frontend/
│   ├── .env              # Configurări frontend
│   ├── build/            # React build (servit de nginx)
│   └── src/              # Cod sursă React
└── deploy-vps.sh         # Script deploy
```

## Backup

```bash
# Backup MongoDB
mongodump --db seo_saas --out /backup/mongo_$(date +%Y%m%d)

# Backup complet aplicație
tar -czvf /backup/seo-saas_$(date +%Y%m%d).tar.gz /var/www/seo-saas
```
