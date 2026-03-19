#!/bin/bash

# ===========================================
# SEO Automation App - Update Script
# ===========================================
# Rulează această comandă pe VPS pentru actualizare:
# cd /root/seo-app && ./update.sh
# Pentru rebuild complet: ./update.sh --force
# ===========================================

set -e

# Culori pentru output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   SEO Automation App - Update Script       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Directorul aplicației
APP_DIR="/root/seo-app"

# Verifică dacă directorul există
if [ ! -d "$APP_DIR" ]; then
    echo -e "${RED}❌ Eroare: Directorul $APP_DIR nu există!${NC}"
    echo "Asigură-te că aplicația este instalată corect."
    exit 1
fi

cd "$APP_DIR"

# Verifică flagul --force
FORCE_BUILD=""
if [ "$1" == "--force" ]; then
    FORCE_BUILD="--no-cache"
    echo -e "${YELLOW}⚠️  Rebuild complet activat (--no-cache)${NC}"
    echo ""
fi

# Pasul 1: Descarcă modificările
echo -e "${YELLOW}📥 Pasul 1/5: Descarcă ultimele modificări...${NC}"
git fetch origin main
git checkout -f origin/main -- backend/ frontend/ docker-compose.yml requirements.txt package.json 2>/dev/null || true

# Pasul 2: Configurează URL-ul backend
echo -e "${YELLOW}🔧 Pasul 2/5: Configurare REACT_APP_BACKEND_URL...${NC}"

# Detectează URL-ul curent din docker-compose.yml
CURRENT_URL=$(grep -o 'REACT_APP_BACKEND_URL=[^[:space:]]*' docker-compose.yml 2>/dev/null | head -1 | cut -d'=' -f2)

# Dacă nu există sau e URL de preview/localhost, cere unul nou
if [ -z "$CURRENT_URL" ] || [[ "$CURRENT_URL" == *"localhost"* ]] || [[ "$CURRENT_URL" == *"preview.emergentagent"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  URL backend invalid sau lipsă!${NC}"
    echo -e "Introdu URL-ul tău (ex: ${GREEN}https://seo.domeniultau.com${NC}):"
    read -r USER_URL
    
    if [ -n "$USER_URL" ]; then
        CURRENT_URL="$USER_URL"
    else
        echo -e "${RED}❌ Nu ai introdus un URL valid. Ieșire.${NC}"
        exit 1
    fi
fi

# Actualizează docker-compose.yml cu URL-ul corect
# Acest sed înlocuiește orice valoare REACT_APP_BACKEND_URL existentă
sed -i "s|REACT_APP_BACKEND_URL=.*|REACT_APP_BACKEND_URL=${CURRENT_URL}|g" docker-compose.yml

echo -e "   URL setat: ${GREEN}${CURRENT_URL}${NC}"

# Pasul 3: Oprește containerele
echo -e "${YELLOW}🛑 Pasul 3/5: Oprește containerele vechi...${NC}"
docker-compose down 2>/dev/null || docker compose down 2>/dev/null || true

# Pasul 4: Curăță cache (dacă --force)
if [ -n "$FORCE_BUILD" ]; then
    echo -e "${YELLOW}🧹 Pasul 4/5: Curățare cache Docker...${NC}"
    docker system prune -af --volumes 2>/dev/null || true
else
    echo -e "${GREEN}✓ Pasul 4/5: Skip curățare cache (folosește --force pentru rebuild complet)${NC}"
fi

# Pasul 5: Pornește containerele
echo -e "${YELLOW}🚀 Pasul 5/5: Pornește containerele noi...${NC}"
docker-compose up -d --build $FORCE_BUILD 2>/dev/null || docker compose up -d --build $FORCE_BUILD

# Așteaptă pornirea
echo ""
echo -e "${YELLOW}⏳ Se așteaptă pornirea serviciilor...${NC}"
sleep 15

# Verifică starea
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅ Actualizare completă cu succes!       ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""

# Afișează starea containerelor
echo -e "${YELLOW}📦 Stare containere:${NC}"
docker-compose ps 2>/dev/null || docker compose ps 2>/dev/null || true

echo ""
echo -e "🌐 Aplicația: ${GREEN}${CURRENT_URL}${NC}"
echo ""
echo -e "${YELLOW}📋 Comenzi utile:${NC}"
echo "   Logs backend:  docker-compose logs -f backend"
echo "   Logs frontend: docker-compose logs -f frontend"
echo "   Restart:       docker-compose restart"
echo "   Stop:          docker-compose down"
echo ""
