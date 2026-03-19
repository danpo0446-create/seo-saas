#!/bin/bash
#
# SEO Automation SaaS - Script Deploy VPS
# Rulează ca root sau cu sudo
#
# Utilizare: sudo bash deploy-vps.sh
#

set -e  # Oprește la eroare

# ============ CONFIGURĂRI - MODIFICĂ AICI ============
DOMAIN="app.clienti.ro"
APP_DIR="/var/www/seo-saas"
BACKEND_PORT="8002"
MONGO_DB="seo_saas"
GIT_REPO="https://github.com/danpo0446-create/seo-automation.git"

# Chei API - ÎNLOCUIEȘTE CU ALE TALE
JWT_SECRET="schimba-aceasta-cheie-cu-una-secreta-lunga-min-32-caractere"
EMERGENT_LLM_KEY=""           # De la Emergent
RESEND_API_KEY=""             # De la resend.com
PEXELS_API_KEY=""             # De la pexels.com
STRIPE_API_KEY=""             # De la Stripe (sk_live_xxx)
# =====================================================

echo "=========================================="
echo "  SEO Automation SaaS - Deploy Script"
echo "=========================================="
echo ""

# Verifică dacă rulează ca root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Rulează scriptul cu sudo: sudo bash deploy-vps.sh"
    exit 1
fi

# ============ 1. INSTALARE DEPENDENȚE ============
echo "📦 [1/8] Instalare dependențe sistem..."

apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    nodejs \
    npm \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl

# Instalare Yarn
npm install -g yarn

# Instalare MongoDB (dacă nu există)
if ! command -v mongod &> /dev/null; then
    echo "📦 Instalare MongoDB..."
    curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
    echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] http://repo.mongodb.org/apt/debian bookworm/mongodb-org/7.0 main" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list
    apt-get update
    apt-get install -y mongodb-org
    systemctl start mongod
    systemctl enable mongod
fi

echo "✅ Dependențe instalate"

# ============ 2. CLONARE REPO ============
echo ""
echo "📥 [2/8] Clonare repository..."

if [ -d "$APP_DIR" ]; then
    echo "⚠️  Directorul $APP_DIR există. Se face backup și se șterge..."
    mv "$APP_DIR" "${APP_DIR}_backup_$(date +%Y%m%d_%H%M%S)"
fi

git clone "$GIT_REPO" "$APP_DIR"
cd "$APP_DIR"

echo "✅ Repository clonat în $APP_DIR"

# ============ 3. CONFIGURARE BACKEND ============
echo ""
echo "⚙️  [3/8] Configurare Backend..."

cat > "$APP_DIR/backend/.env" << EOF
MONGO_URL=mongodb://localhost:27017
DB_NAME=$MONGO_DB
JWT_SECRET=$JWT_SECRET
EMERGENT_LLM_KEY=$EMERGENT_LLM_KEY
RESEND_API_KEY=$RESEND_API_KEY
PEXELS_API_KEY=$PEXELS_API_KEY
STRIPE_API_KEY=$STRIPE_API_KEY
FRONTEND_URL=https://$DOMAIN
SENDER_EMAIL=noreply@$DOMAIN
EOF

cd "$APP_DIR/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

echo "✅ Backend configurat"

# ============ 4. CONFIGURARE FRONTEND ============
echo ""
echo "⚙️  [4/8] Configurare Frontend..."

cat > "$APP_DIR/frontend/.env" << EOF
REACT_APP_BACKEND_URL=https://$DOMAIN
EOF

cd "$APP_DIR/frontend"
yarn install
yarn build

echo "✅ Frontend configurat și build creat"

# ============ 5. CREARE SERVICIU SYSTEMD ============
echo ""
echo "🔧 [5/8] Creare serviciu systemd..."

cat > /etc/systemd/system/seo-saas.service << EOF
[Unit]
Description=SEO Automation SaaS Backend
After=network.target mongod.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR/backend
Environment="PATH=$APP_DIR/backend/venv/bin"
ExecStart=$APP_DIR/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port $BACKEND_PORT
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Setare permisiuni
chown -R www-data:www-data "$APP_DIR"

systemctl daemon-reload
systemctl enable seo-saas
systemctl start seo-saas

echo "✅ Serviciu systemd creat și pornit"

# ============ 6. CONFIGURARE NGINX ============
echo ""
echo "🌐 [6/8] Configurare Nginx..."

cat > /etc/nginx/sites-available/$DOMAIN << EOF
server {
    listen 80;
    server_name $DOMAIN;

    # Frontend (React build)
    root $APP_DIR/frontend/build;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Frontend routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Static files cache
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Activare site
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/

# Test și reload nginx
nginx -t && systemctl reload nginx

echo "✅ Nginx configurat"

# ============ 7. SSL CU CERTBOT ============
echo ""
echo "🔒 [7/8] Configurare SSL..."

# Verifică dacă domeniul pointează către server
echo "⚠️  Asigură-te că DNS-ul pentru $DOMAIN pointează către acest server!"
echo ""
read -p "Continui cu SSL? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN --redirect
    echo "✅ SSL configurat"
else
    echo "⏭️  SSL sărit. Rulează manual: sudo certbot --nginx -d $DOMAIN"
fi

# ============ 8. VERIFICARE FINALĂ ============
echo ""
echo "🔍 [8/8] Verificare finală..."

# Status servicii
echo ""
echo "Status MongoDB:"
systemctl status mongod --no-pager -l | head -5

echo ""
echo "Status SEO SaaS Backend:"
systemctl status seo-saas --no-pager -l | head -5

echo ""
echo "Status Nginx:"
systemctl status nginx --no-pager -l | head -5

# ============ DONE ============
echo ""
echo "=========================================="
echo "  ✅ DEPLOY COMPLET!"
echo "=========================================="
echo ""
echo "🌐 Aplicația este disponibilă la:"
echo "   https://$DOMAIN"
echo ""
echo "📋 Comenzi utile:"
echo "   - Logs backend:  journalctl -u seo-saas -f"
echo "   - Restart backend: systemctl restart seo-saas"
echo "   - Status:        systemctl status seo-saas"
echo ""
echo "⚠️  NU UITA să configurezi:"
echo "   1. Cheile API în $APP_DIR/backend/.env"
echo "   2. DNS pentru $DOMAIN"
echo "   3. Stripe webhook URL: https://$DOMAIN/api/webhook/stripe"
echo ""
echo "=========================================="
