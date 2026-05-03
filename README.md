# Infosearch

Infosearch is een monorepo voor vacaturezoektocht en AI-gedreven prospectie.

De repo bestaat uit drie delen:

- `backend_project/` — FastAPI backend + MySQL + migraties
- `frontend_project/AI_project_frontend/` — React/Vite frontend
- `AI_project_ai/` — AI service voor enrichment en prospectgeneratie

## Wat de applicatie doet

Infosearch ondersteunt twee hoofdflows:

1. **Vacatures zoeken**
   - gebruikers zoeken vacatures via query + filters
   - resultaten worden opgehaald via de backend
   - opgeslagen zoekopdrachten zijn opnieuw beschikbaar vanuit de homepagina

2. **Bedrijven prospecteren**
   - gebruikers zoeken bedrijven op basis van een product/dienst of commerciële vraag
   - de AI service verrijkt bedrijfsdata
   - prospects en bedrijfsprofielen worden via de backend verwerkt

De frontend bevat daarnaast:

- login/auth flow
- protected routes
- recente zoekopdrachten
- admin-trigger voor handmatige VDAB sync

## Tech stack

### Frontend
- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Axios
- GSAP
- MSAL (`@azure/msal-browser`, `@azure/msal-react`)

### Backend
- FastAPI
- MySQL
- Docker Compose

### AI service
- Python
- FastAPI
- Ollama
- optioneel Groq
- Docker Compose

## Repository structuur

```text
AI_project/
├─ README.md
├─ backend_project/
│  ├─ backend/
│  └─ docker-compose.yml
├─ frontend_project/
│  └─ AI_project_frontend/
│     ├─ src/
│     └─ package.json
└─ AI_project_ai/
```

## Vereisten

Installeer lokaal:

- Python 3.12+
- Node.js 20+
- npm
- Docker Desktop
- Ollama

## Snel starten

### 1. Backend starten

Maak indien nodig een `.env` op basis van:

- `backend_project/backend/.env.example`

Start daarna de backend stack:

```bash
cd backend_project
docker compose up --build
```

Dit start normaal:

- FastAPI backend op `http://localhost:8000`
- MySQL op poort `3307`
- migrator voor SQL-migraties

Backend docs:

- `http://localhost:8000/docs`

---

### 2. Frontend starten

```bash
cd frontend_project/AI_project_frontend
npm install
npm run dev
```

De frontend draait lokaal via Vite, meestal op:

- `http://localhost:5173`

### Frontend API-configuratie

De frontend gebruikt `VITE_API_URL` als die gezet is.

Zonder expliciete configuratie geldt deze logica:

- op localhost → `http://localhost:8000`
- buiten localhost → `protocol://hostname:8000`
- server fallback in code → `http://91.99.180.245:8000`

---

### 3. AI service starten

Vul eerst de `.env` in:

- `AI_project_ai/.env`

Belangrijke variabelen:

- `BACKEND_URL`
- `FRONTEND_URL`
- `OLLAMA_HOST`
- `GROQ_API_KEY` (indien Groq gebruikt wordt)

Start daarna:

```bash
cd AI_project_ai
docker compose up --build
```

Dit start normaal:

- Ollama
- model init
- AI API op `http://localhost:8001`

AI docs:

- `http://localhost:8001/docs`

## Aanbevolen opstartvolgorde

### Alleen hoofdapp

1. Start backend
2. Start frontend

```bash
cd backend_project
docker compose up --build
```

Tweede terminal:

```bash
cd frontend_project/AI_project_frontend
npm install
npm run dev
```

### Volledige stack

1. Start backend
2. Start frontend
3. Configureer `AI_project_ai/.env`
4. Start AI service

## Frontend routes

Belangrijkste routes in de huidige frontend:

- `/login` — aanmelden
- `/home` — dashboard
- `/keuze` — keuze tussen flows
- `/search/job` — vacaturezoektocht
- `/search/company` — prospectie / bedrijfszoektocht
- `/results/job` — vacatureresultaten
- `/results/company` — bedrijfsresultaten
- `/saved` — opgeslagen zoekopdrachten

Alle routes behalve `/login` zijn protected.

## Belangrijke functionele punten

### Authenticatie

De frontend verwacht een backend-auth flow via:

- `GET /auth/me`
- `POST /auth/login`
- `POST /auth/logout`

De UI gebruikt `withCredentials: true`, dus cookie/session-gedrag aan backendzijde moet correct staan.

### VDAB sync

Admins kunnen vanuit de homepagina een handmatige VDAB sync starten.

De frontend roept daarvoor aan:

- `POST /sync?aantal=100`

### Opgeslagen zoekopdrachten

De homepagina haalt recente zoekopdrachten op via:

- `GET /searches/saved`

### Vacaturezoektocht

De job search ondersteunt:

- vrije query
- bestandupload
- filters zoals locatie, contracttype, sector, ervaringsniveau

### Bedrijfsprospectie

De company search ondersteunt:

- vrije query
- filters zoals locatie, sector, bedrijfsgrootte, regio

## Bekende aandachtspunten

- De repo bevat meerdere `.env`-bestanden. Controleer per onderdeel welke effectief gebruikt worden.
- De AI service is niet standalone nuttig zonder correcte backend-koppeling.
- De frontend bevat een hardcoded API fallback naar `91.99.180.245:8000`; dat is functioneel maar niet ideaal voor productiebeheer.
- Docker Desktop moet actief zijn voor de compose-based onderdelen.
- De subproject README’s zijn niet consistent in detailniveau en stijl.

## Development scripts

### Frontend

```bash
npm run dev
npm run build
npm run lint
npm run preview
```

## Handige URLs

- Backend docs: `http://localhost:8000/docs`
- Frontend: meestal `http://localhost:5173`
- AI docs: `http://localhost:8001/docs`

## Korte quick start

Als je alleen snel lokaal wilt testen:

```bash
cd backend_project
docker compose up --build
```

Tweede terminal:

```bash
cd frontend_project/AI_project_frontend
npm install
npm run dev
```

Open daarna de Vite-URL uit de terminal.
