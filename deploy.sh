#!/bin/bash
# ===========================================
# Script de Deploy pentru SEO Automation SaaS
# Folosire: ./deploy.sh
# ===========================================

set -e  # Exit on error

echo "🚀 Începe procesul de deploy..."

# Directorul aplicației
APP_DIR="/var/www/seo-saas"

# Verifică dacă directorul există
if [ ! -d "$APP_DIR" ]; then
    echo "❌ Eroare: Directorul $APP_DIR nu există!"
    exit 1
fi

cd "$APP_DIR"

echo ""
echo "📥 1. Descarcă ultimele modificări din Git..."
git checkout -- .
git pull origin main

echo ""
echo "📦 2. Instalează dependențele backend (dacă s-au schimbat)..."
cd backend
pip install -r requirements.txt --quiet 2>/dev/null || true
cd ..

echo ""
echo "🔨 3. Construiește frontend-ul..."
cd frontend
npm install --silent 2>/dev/null || true
npm run build

echo ""
echo "🔄 4. Repornește serviciile..."
cd "$APP_DIR"
sudo systemctl restart seo-saas

echo ""
echo "✅ Deploy finalizat cu succes!"
echo ""
echo "🔍 Pentru a verifica statusul: sudo systemctl status seo-saas"
echo "📋 Pentru a vedea log-urile: sudo journalctl -u seo-saas -f"
