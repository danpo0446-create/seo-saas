@echo off
echo ==========================================
echo    SEO Automation - Pornire Aplicatie
echo ==========================================
echo.

REM Verifică dacă Docker rulează
docker info >nul 2>&1
if errorlevel 1 (
    echo [EROARE] Docker Desktop nu ruleaza!
    echo Porneste Docker Desktop si incearca din nou.
    pause
    exit /b 1
)

REM Verifică dacă există .env
if not exist ".env" (
    echo [!] Fisierul .env nu exista.
    echo.
    echo Creez fisierul .env din .env.example...
    copy .env.example .env
    echo.
    echo [IMPORTANT] Deschide fisierul .env si adauga cheia ta EMERGENT_LLM_KEY
    echo O gasesti in Emergent -^> Profile -^> Universal Key
    echo.
    notepad .env
    pause
)

echo.
echo Pornesc aplicatia... (prima data dureaza 5-10 minute)
echo.

docker-compose up --build -d

echo.
echo ==========================================
echo    Aplicatia porneste!
echo ==========================================
echo.
echo Asteapta 1-2 minute, apoi deschide in browser:
echo.
echo    http://localhost:3000
echo.
echo Pentru a opri aplicatia, ruleaza: STOP.bat
echo ==========================================
pause
