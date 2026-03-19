# SEO Automation Platform

## Rulare Locală (Simplu)

### Ce ai nevoie:
1. **Docker Desktop** - descarcă de la https://www.docker.com/products/docker-desktop/

### Pași:

1. **Descarcă proiectul** din GitHub (buton verde "Code" → "Download ZIP")

2. **Extrage ZIP-ul** într-un folder

3. **Pornește Docker Desktop** și așteaptă să pornească complet

4. **Windows**: Dublu-click pe `START.bat`  
   **Mac**: Deschide Terminal în folder și rulează `./start.sh`

5. **Editează fișierul `.env`** și adaugă cheia EMERGENT_LLM_KEY  
   (o găsești în Emergent → Profile → Universal Key)

6. **Deschide în browser**: http://localhost:3000

### Oprire aplicație:
- **Windows**: Dublu-click pe `STOP.bat`
- **Mac**: Rulează `./stop.sh`

---

## Funcționalități

- ✅ Generare articole SEO cu AI (GPT-5.2)
- ✅ Cercetare cuvinte-cheie
- ✅ Calendar editorial 90 zile
- ✅ Manager backlinks (300+ site-uri)
- ✅ Publicare automată WordPress
- ✅ Tracking Google Search Console
- ✅ 5 template-uri de articole
- ✅ Notificări email
- ✅ 100% White-label

---

## Configurare opțională

Editează fișierul `.env` pentru:

```
EMERGENT_LLM_KEY=sk-emergent-xxxx     # OBLIGATORIU
RESEND_API_KEY=re_xxxx                 # Pentru email-uri
```
