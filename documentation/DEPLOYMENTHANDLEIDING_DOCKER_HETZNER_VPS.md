# Deploymenthandleiding voor Docker / Hetzner / VPS

## InfoSearch — productiegerichte deployment

**Project:** InfoSearch  
**Doelgroep:** beheerders en ontwikkelaars die de applicatie op een VPS willen draaien  
**Laatst bijgewerkt:** 18 mei 2026

---

## 1. Doel van deze handleiding

Deze handleiding beschrijft hoe InfoSearch gedeployed kan worden met Docker Compose op een VPS, bijvoorbeeld een Hetzner Cloud-server. De root van het project bevat hiervoor een productiegerichte `docker-compose.yaml` met:

- MySQL database;
- FastAPI backend;
- AI-service;
- Ollama;
- model-init container;
- migrator;
- Caddy reverse proxy.

De frontend kan lokaal via Vite draaien, apart statisch gehost worden, of later als nginx-container aan de rootstack toegevoegd worden.

---

## 2. Architectuur van de deployment

```text
Gebruiker / browser
        |
        | HTTPS
        v
Caddy reverse proxy
        |
        v
FastAPI backend :8000
        |
        |---------------------> MySQL :3306
        |
        |---------------------> AI-service :8000 intern / :8001 lokaal
                                  |
                                  v
                               Ollama :11434
```

In de rootstack wordt de database niet rechtstreeks publiek gepubliceerd. Caddy publiceert HTTP/HTTPS en proxyt naar de backend.

Belangrijke bestanden:

| Bestand | Doel |
|---|---|
| `docker-compose.yaml` | rootstack voor serverdeployment |
| `Caddyfile` | reverse proxy en TLS |
| `backend_project/backend/.env` | backendconfiguratie |
| `backend_project/.env` | database/migratorconfiguratie |
| `AI_project_ai/.env` | AI-service, Ollama en Groq-configuratie |
| `frontend_project/AI_project_frontend/.env` | optionele frontend API URL |

---

## 3. VPS voorbereiden

### 3.1 Serverkeuze

Voor een minimale VPS-test met MySQL + backend + Caddy is een kleine server voldoende. Voor Ollama/AI is meer geheugen nodig.

Aanbevolen minimum:

| Scenario | CPU/RAM |
|---|---|
| Backend + MySQL + Caddy | 2 vCPU / 2 GB RAM |
| Volledige stack met klein Qwen-model | 2 vCPU / 4 GB RAM |
| Groter lokaal model | 4+ vCPU / 8+ GB RAM of GPU |

De huidige rootstack beperkt MySQL tot ongeveer `512M`, AI API tot `512M` en Ollama tot ongeveer `2G`. Daarom past een klein model zoals `qwen2.5:0.5b` beter op een 4 GB VPS dan een groter model.

### 3.2 Basispackages installeren

Op een Ubuntu/Debian VPS:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git curl ca-certificates ufw
```

Installeer Docker en Docker Compose volgens de officiële Docker-documentatie of via de packagebron van je distributie. Controleer daarna:

```bash
docker --version
docker compose version
```

Zorg dat je gebruiker Docker mag gebruiken of voer composecommando's met `sudo` uit.

---

## 4. Domein en DNS

De huidige `Caddyfile` verwijst naar:

```text
infosearch.duckdns.org
```

Voor deployment moet het domein naar het publieke IPv4-adres van de VPS wijzen.

Stappen:

1. Maak of kies een domein/subdomein.
2. Zet een A-record naar het VPS-IP.
3. Pas `Caddyfile` aan als je een ander domein gebruikt.
4. Open poorten `80` en `443`.

Voorbeeld `Caddyfile`:

```caddy
{
    email jouw-email@example.com
}

infosearch.duckdns.org {
    reverse_proxy backend:8000
}
```

Caddy vraagt automatisch TLS-certificaten aan zodra DNS correct staat en poort 80/443 bereikbaar zijn.

---

## 5. Firewall instellen

Sta alleen noodzakelijke poorten toe:

```bash
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

Publiceer MySQL niet naar internet. De rootstack gebruikt MySQL intern via Docker-netwerk.

---

## 6. Project deployen

Clone of kopieer de repository naar de VPS:

```bash
git clone <repository-url> AI_project
cd AI_project
```

Als de repository al op de server staat:

```bash
cd AI_project
git pull
```

Controleer de structuur:

```bash
ls
```

Je verwacht onder andere:

```text
backend_project/
frontend_project/
AI_project_ai/
documentation/
presentatie/
docker-compose.yaml
Caddyfile
```

---

## 7. Productie-environment configureren

### 7.1 Backend databaseconfiguratie

Maak `backend_project/.env` en `backend_project/backend/.env` aan op basis van de voorbeelden.

Belangrijke productie-instellingen:

```env
MYSQL_ROOT_PASSWORD=<sterk-root-wachtwoord>
MYSQL_DATABASE=InfoSearch
MYSQL_USER=<app-user>
MYSQL_PASSWORD=<sterk-app-wachtwoord>
MYSQL_HOST=mysql
MYSQL_PORT=3306
```

In `backend_project/backend/.env`:

```env
VDAB_CLIENT_ID=<vdab-client-id>
VDAB_CLIENT_SECRET=<vdab-client-secret>
VDAB_API_KEY=<vdab-api-key>
VDAB_HOST=op-derden.vdab.be
VDAB_ALLOW_FALLBACK=false

MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_DATABASE=InfoSearch
MYSQL_USER=<app-user>
MYSQL_PASSWORD=<sterk-app-wachtwoord>

CORS_ALLOWED_ORIGINS=https://infosearch.duckdns.org
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=lax
SESSION_MAX_AGE=604800

AI_SERVICE_URL=http://ai-api-test:8000

AUTO_SYNC_ENABLED=true
AUTO_SYNC_TIME=02:30
AUTO_SYNC_TZ=Europe/Brussels
AUTO_SYNC_AMOUNT=500
```

> Voor productie is `VDAB_ALLOW_FALLBACK=false` aanbevolen, zodat testfallbackdata niet ongemerkt in productie terechtkomt.

### 7.2 AI-serviceconfiguratie

In `AI_project_ai/.env`:

```env
BACKEND_URL=http://backend:8000
FRONTEND_URL=https://infosearch.duckdns.org
OLLAMA_HOST=http://ollama-test:11434
GROQ_API_KEY=<optioneel-alleen-indien-groq-gebruikt-wordt>
```

Gebruik geen echte secrets in documentatie, screenshots of commits.

---

## 8. Rootstack starten

Vanuit de projectroot:

```bash
docker compose -f docker-compose.yaml up --build -d
```

Controleer containers:

```bash
docker compose -f docker-compose.yaml ps
```

Bekijk logs:

```bash
docker compose -f docker-compose.yaml logs -f backend
docker compose -f docker-compose.yaml logs -f migrator
docker compose -f docker-compose.yaml logs -f caddy
```

De migrator voert SQL-bestanden uit uit:

```text
backend_project/backend/db/migrations/
```

De rootstack bevat een named volume voor MySQL:

```text
mysql_data
```

Caddy gebruikt:

```text
caddy_data
caddy_config
```

---

## 9. Deployment controleren

### 9.1 Backend

```bash
curl https://infosearch.duckdns.org/health
```

Of lokaal op de server:

```bash
docker compose -f docker-compose.yaml exec backend python -c "import requests; print(requests.get('http://localhost:8000/health').text)"
```

Open eventueel:

```text
https://infosearch.duckdns.org/docs
```

Let op: FastAPI docs publiek openzetten is handig voor demo's, maar minder wenselijk voor productie.

### 9.2 Database

```bash
docker compose -f docker-compose.yaml logs migrator
```

De migrator moet eindigen met een succesvolle melding. Als de migrator faalt, start de backend mogelijk wel, maar ontbreken tabellen.

### 9.3 AI-service

Omdat de AI-service in de rootstack alleen intern/lokaal bereikbaar is, test je vanaf de server:

```bash
curl http://127.0.0.1:8001/docs
```

Of via Docker-netwerk:

```bash
docker compose -f docker-compose.yaml exec backend python -c "import httpx; print(httpx.get('http://ai-api-test:8000/docs').status_code)"
```

---

## 10. Frontend deployen

De rootstack bevat momenteel een uitgeschakelde voorbeeldservice voor een nginx-frontend. Er zijn drie praktische opties.

### Optie A — frontend lokaal draaien tijdens demo

Stel lokaal in:

```env
VITE_API_URL=https://infosearch.duckdns.org
```

Start lokaal:

```bash
cd frontend_project/AI_project_frontend
npm install
npm run dev
```

### Optie B — frontend build statisch hosten

Build de frontend:

```bash
cd frontend_project/AI_project_frontend
npm install
npm run build
```

De output staat in:

```text
frontend_project/AI_project_frontend/dist/
```

Deze map kan via nginx, Caddy of een statische host geserveerd worden.

### Optie C — nginx-container activeren

In `docker-compose.yaml` staat een voorbeeld voor een nginx-frontendservice in commentaar. Die kan later geactiveerd worden door:

1. frontend te builden;
2. de service uit commentaar te halen;
3. Caddy eventueel te laten reverse-proxyen naar die frontendservice;
4. backend API onder een apart path of subdomein te plaatsen.

Voor de huidige projectstatus is de backenddeployment via Caddy het meest uitgewerkt.

---

## 11. Updates deployen

Voor code-updates:

```bash
cd AI_project
git pull
docker compose -f docker-compose.yaml up --build -d
```

Controleer daarna:

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs --tail=100 backend
```

Als migraties wijzigen, draait de migrator opnieuw en slaat reeds toegepaste migraties over op basis van checksumregistratie in `schema_migrations`.

---

## 12. Backups

Maak backups van minimaal:

- MySQL-data (`mysql_data` volume);
- `.env`-bestanden, veilig buiten Git;
- eventueel Caddy-data voor certificaten.

Voor een eenvoudige databasebackup:

```bash
docker compose -f docker-compose.yaml exec mysql \
  mysqldump -u root -p InfoSearch > infosearch_backup.sql
```

Bewaar backups versleuteld en niet in de publieke repository.

---

## 13. Monitoring en logs

Nuttige commando's:

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs -f backend
docker compose -f docker-compose.yaml logs -f ai-api-test
docker compose -f docker-compose.yaml logs -f ollama-test
docker compose -f docker-compose.yaml logs -f caddy
docker stats
```

Let specifiek op:

- VDAB `429` rate limits;
- VDAB token/auth-fouten;
- MySQL connectiefouten;
- CORS-fouten;
- AI-service timeouts;
- Groq rate limits of ontbrekende API key;
- geheugenproblemen bij Ollama.

---

## 14. Security-aandachtspunten

Voor een productieomgeving:

- gebruik sterke databasewachtwoorden;
- zet `SESSION_COOKIE_SECURE=true` bij HTTPS;
- beperk `CORS_ALLOWED_ORIGINS` tot echte frontenddomeinen;
- publiceer MySQL niet;
- commit geen `.env`-bestanden;
- verwijder of wijzig standaard demoaccounts;
- overweeg FastAPI docs af te schermen;
- bescherm adminacties zoals `/sync` server-side met rolcontrole;
- draai updates van OS en Docker regelmatig;
- maak periodieke backups.

Belangrijk: in de huidige frontend wordt de handmatige VDAB-sync alleen getoond aan admingebruikers. Controleer voor productie ook server-side autorisatie op adminroutes, zodat een niet-admin de endpoint niet rechtstreeks kan aanroepen.

---

## 15. Rollback

Een eenvoudige rollback bestaat uit:

1. teruggaan naar een vorige Git-commit;
2. containers opnieuw builden/starten;
3. indien nodig databasebackup herstellen.

Voorbeeld:

```bash
git log --oneline
git checkout <vorige-commit>
docker compose -f docker-compose.yaml up --build -d
```

Databasewijzigingen zijn niet automatisch omkeerbaar. Maak daarom altijd een backup vóór risicovolle migraties.
