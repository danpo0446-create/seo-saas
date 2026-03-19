#!/bin/bash

echo "=========================================="
echo "   SEO Automation - Pornire Aplicatie"
echo "=========================================="
echo ""

# Verifică dacă Docker rulează
if ! docker info > /dev/null 2>&1; then
    echo "[EROARE] Docker nu rulează!"
    echo "Pornește Docker Desktop și încearcă din nou."
    exit 1
fi

# Verifică dacă există .env
if [ ! -f ".env" ]; then
    echo "[!] Fișierul .env nu există."
    echo ""
    echo "Creez fișierul .env din .env.example..."
    cp .env.example .env
    echo ""
    echo "[IMPORTANT] Deschide fișierul .env și adaugă cheia ta EMERGENT_LLM_KEY"
    echo "O găsești în Emergent -> Profile -> Universal Key"
    echo ""
    read -p "Apasă Enter după ce ai editat .env..."
fi

echo ""
echo "Pornesc aplicația... (prima dată durează 5-10 minute)"
echo ""

docker-compose up --build -d

echo ""
echo "=========================================="
echo "   Aplicația pornește!"
echo "=========================================="
echo ""
echo "Așteaptă 1-2 minute, apoi deschide în browser:"
echo ""
echo "   http://localhost:3000"
echo ""
echo "Pentru a opri aplicația, rulează: ./stop.sh"
echo "=========================================="
