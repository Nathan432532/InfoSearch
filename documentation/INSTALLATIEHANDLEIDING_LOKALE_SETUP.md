# Installatiehandleiding voor lokale setup

## InfoSearch — lokale ontwikkelomgeving

**Project:** InfoSearch  
**Doelgroep:** ontwikkelaars, testers en lectoren die het project lokaal willen draaien  
**Laatst bijgewerkt:** 18 mei 2026

---

## 1. Doel van deze handleiding

Deze handleiding beschrijft hoe je InfoSearch lokaal opstart. InfoSearch bestaat uit drie onderdelen:

- `backend_project/` — FastAPI backend, MySQL database en migraties;
- `frontend_project/AI_project_frontend/` — React/Vite frontend;
- `AI_project_ai/` — AI-service voor bedrijfsverrijking en prospectranking.

Voor een minimale lokale test heb je backend + frontend nodig. Voor de volledige prospectieflow met AI-verrijking start je ook de AI-service en Ollama.

---

## 2. Vereisten

Installeer vooraf:

| Tool | Aanbevolen versie | Gebruik |
|---|---:|---|
| Git | recent | repository beheren |
| Docker Desktop | recent | MySQL, backend en optioneel AI-containers |
| Node.js | 20+ | frontend developmentserver |
| npm | meegeleverd met Node | frontend dependencies |
| Python | 3.12+ voor backend, 3.11+ voor AI-service | lokale FastAPI-runs zonder Docker |
| Ollama | recent | lokale LLM-runtime voor enrichment |

Controleer de installaties:

```powershell
git --version
docker --version
docker compose version
node --version
npm --version
python --version
```

---

## 3. Repository openen

Open een terminal in de root van het project:

```powershell
cd C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project
```

De root bevat normaal onder andere:

```text
AI_project/
├─ README.md
├─ docker-compose.yaml
├─ Caddyfile
├─ backend_project/
├─ frontend_project/
├─ AI_project_ai/
├─ documentation/
└─ presentatie/
```

---

## 4. Environment files configureren

De repository gebruikt meerdere `.env`-bestanden. Commit nooit echte secrets of API keys.

### 4.1 Backend database/VDAB-configuratie

Maak of controleer:

```text
backend_project/.env
backend_project/backend/.env
```

Gebruik de voorbeelden als basis:

```powershell
Copy-Item backend_project\.env.example backend_project\.env
Copy-Item backend_project\backend\.env.example backend_project\backend\.env
```

Belangrijke variabelen:

| Variabele | Doel |
|---|---|
| `MYSQL_ROOT_PASSWORD` | rootwachtwoord voor MySQL-container |
| `MYSQL_DATABASE` | standaard `InfoSearch` |
| `MYSQL_USER` / `MYSQL_PASSWORD` | applicatiegebruiker voor backend |
| `MYSQL_HOST` | in Docker meestal `mysql` |
| `MYSQL_PORT` | in Docker meestal `3306`; vanaf host vaak `3307` |
| `VDAB_CLIENT_ID` | VDAB OAuth client id |
| `VDAB_CLIENT_SECRET` | VDAB OAuth secret |
| `VDAB_API_KEY` | VDAB API key / client id header |
| `VDAB_HOST` | standaard `op-derden.vdab.be` |
| `VDAB_ALLOW_FALLBACK` | bij `true` kan de backend fallbackdata gebruiken bij VDAB-problemen |
| `CORS_ALLOWED_ORIGINS` | toegestane frontend-URL's, bv. `http://localhost:5173` |
| `AI_SERVICE_URL` | optioneel, bv. `http://host.docker.internal:8001` of intern `http://ai-api-test:8000` |
| `SESSION_COOKIE_SECURE` | lokaal meestal `false` |
| `SESSION_COOKIE_SAMESITE` | lokaal meestal `lax` |
| `AUTO_SYNC_ENABLED` | automatische nachtelijke VDAB-sync aan/uit |
| `AUTO_SYNC_TIME` | standaard `02:30` |
| `AUTO_SYNC_TZ` | standaard `Europe/Brussels` |
| `AUTO_SYNC_AMOUNT` | aantal vacatures per automatische sync |

### 4.2 AI-service configuratie

Maak of controleer:

```text
AI_project_ai/.env
```

Minimale variabelen:

```env
BACKEND_URL=http://host.docker.internal:8000
FRONTEND_URL=http://localhost:5173
OLLAMA_HOST=http://ollama-test:11434
GROQ_API_KEY=
```

Gebruik `GROQ_API_KEY` alleen als prospectranking via Groq gebruikt wordt. Zonder Groq kan de backend terugvallen op deterministische ranking wanneer de AI-route niet beschikbaar is.

### 4.3 Frontend configuratie

Optioneel kan je in `frontend_project/AI_project_frontend/.env` zetten:

```env
VITE_API_URL=http://localhost:8000
```

Zonder `VITE_API_URL` gebruikt de frontend deze logica:

- op `localhost` → `http://localhost:8000`;
- buiten localhost → `protocol://hostname:8000`;
- fallback in code → `http://91.99.180.245:8000`.

---

## 5. Backend lokaal starten met Docker Compose

Ga naar het backendproject:

```powershell
cd backend_project
docker compose up --build
```

Dit start normaal:

- `mysql` — MySQL 8 database;
- `backend` — FastAPI op `http://localhost:8000`;
- `migrator` — voert SQL-migraties uit en stopt daarna.

Controleer:

```powershell
curl http://localhost:8000/health
```

Open de FastAPI-documentatie:

```text
http://localhost:8000/docs
```

### 5.1 Databasepoort

De database draait in Docker op poort `3306`. Vanaf je host is de poort in de backend-compose meestal gepubliceerd als:

```text
localhost:3307
```

Gebruik dit alleen voor debugging via een databaseclient. De backendcontainer gebruikt intern `mysql:3306`.

---

## 6. Frontend lokaal starten

Open een tweede terminal:

```powershell
cd C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project\frontend_project\AI_project_frontend
npm install
npm run dev
```

De Vite-server toont daarna de lokale URL, meestal:

```text
http://localhost:5173
```

De applicatie start op `/login`. Alle andere routes zijn protected.

Belangrijke routes:

| Route | Doel |
|---|---|
| `/login` | aanmelden |
| `/home` | dashboard |
| `/keuze` | keuze tussen vacaturezoektocht en bedrijfsprospectie |
| `/search/job` | vacaturezoektocht |
| `/search/company` | bedrijfsprospectie |
| `/results/job` | vacatureresultaten |
| `/results/company` | bedrijfsresultaten |
| `/saved` | opgeslagen zoekopdrachten en resultaten |

---

## 7. AI-service lokaal starten

Voor de volledige AI-flow start je ook de AI-service.

### 7.1 Via Docker Compose

Open een derde terminal:

```powershell
cd C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project\AI_project_ai
docker compose up --build
```

Dit start:

- `ollama-test` — Ollama runtime;
- `ollama-init` — downloadt het ingestelde Qwen-model;
- `ai-api-test` — FastAPI AI-wrapper op `http://localhost:8001`.

AI API-documentatie:

```text
http://localhost:8001/docs
```

### 7.2 Model controleren

Als Ollama lokaal draait, kan je modellen controleren met:

```powershell
ollama list
```

Het project gebruikt in de compose-configuratie een Qwen-model zoals `qwen2.5:3b` of in de rootstack `qwen2.5:0.5b`, afhankelijk van de gebruikte compose-file en beschikbare RAM.

---

## 8. Aanbevolen lokale opstartvolgorde

### Minimale app zonder AI-container

1. Backend + MySQL starten:

```powershell
cd backend_project
docker compose up --build
```

2. Frontend starten:

```powershell
cd frontend_project\AI_project_frontend
npm install
npm run dev
```

3. Open:

```text
http://localhost:5173
```

### Volledige app met AI-service

1. Backend + MySQL starten.
2. AI-service + Ollama starten.
3. Frontend starten.
4. Controleer dat `AI_SERVICE_URL` in de backend correct naar de AI-service wijst.

Voor lokale Docker/host-combinaties is dit vaak:

```env
AI_SERVICE_URL=http://host.docker.internal:8001
```

Voor één gezamenlijke Docker Compose-stack kan dit intern zijn:

```env
AI_SERVICE_URL=http://ai-api-test:8000
```

---

## 9. Basisgebruik na installatie

1. Open de frontend.
2. Log in met een lokaal testaccount dat in de database/migraties is voorzien.
3. Ga naar `/home`.
4. Kies:
   - **Vacatures zoeken** voor vacaturezoektocht;
   - **Bedrijven prospecteren** voor AI-gedreven prospectie.
5. Sla zoekopdrachten of individuele resultaten op om ze later via `/saved` te bekijken.

> Let op: wijzig demo- of standaardaccounts voor productie. Documenteer echte wachtwoorden niet in de repository.

---

## 10. Handige healthchecks

| Onderdeel | Check |
|---|---|
| Backend | `http://localhost:8000/health` |
| Backend API docs | `http://localhost:8000/docs` |
| AI API docs | `http://localhost:8001/docs` |
| Frontend | `http://localhost:5173` |
| Docker containers | `docker compose ps` |
| Logs | `docker compose logs -f` |

Voor de backend vanuit `backend_project/`:

```powershell
docker compose ps
docker compose logs -f backend
docker compose logs -f migrator
docker compose logs -f mysql
```

Voor de rootstack vanuit de projectroot:

```powershell
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs -f backend
```

---

## 11. Veelvoorkomende problemen

### Frontend toont “backend draait niet”

Controleer:

```powershell
curl http://localhost:8000/health
```

Als dit faalt:

- draait Docker Desktop?
- staat de backendcontainer aan?
- zijn de `.env`-variabelen correct?
- is poort `8000` vrij?

### Login werkt niet

Controleer:

- zijn de migraties succesvol uitgevoerd?
- bestaat `tblLocalUsers`?
- gebruikt de frontend dezelfde backend-URL?
- zijn cookies toegestaan in de browser?
- lokaal: `SESSION_COOKIE_SECURE=false`;
- CORS bevat `http://localhost:5173`.

### VDAB-sync faalt

Controleer:

- `VDAB_CLIENT_ID`;
- `VDAB_CLIENT_SECRET`;
- `VDAB_API_KEY`;
- netwerktoegang naar VDAB;
- backendlogs voor `Token error`, `Vacatures error` of `429`.

### AI-service geeft geen resultaten

Controleer:

- draait `ai-api-test`?
- draait `ollama-test`?
- is het model gedownload?
- klopt `BACKEND_URL` in `AI_project_ai/.env`?
- klopt `AI_SERVICE_URL` in `backend_project/backend/.env`?
- is `GROQ_API_KEY` gezet als Groq-ranking gebruikt wordt?

### Database blijft leeg

Controleer migratorlogs:

```powershell
docker compose logs migrator
```

Daarna kan je handmatig een sync starten via backend docs of via de admin-knop in de frontend.

---

## 12. Stoppen en opschonen

Containers stoppen zonder data te verwijderen:

```powershell
docker compose down
```

Containers stoppen en volumes verwijderen:

```powershell
docker compose down -v
```

Gebruik `-v` alleen als je de lokale database bewust wilt wissen.
