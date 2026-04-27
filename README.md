# AI Project

Monorepo met drie onderdelen:

- `backend_project/` — FastAPI backend + MySQL + migrator
- `frontend_project/AI_project_frontend/` — React/Vite frontend
- `AI_project_ai/` — aparte AI service voor enrichment/prospect generatie

## Vereisten

Installeer lokaal:

- Python 3.12+
- Node.js 20+
- npm
- Docker Desktop
- Ollama (voor de AI service)

## Repository structuur

```text
AI_project/
├─ backend_project/
│  ├─ backend/
│  └─ docker-compose.yml
├─ frontend_project/
│  └─ AI_project_frontend/
└─ AI_project_ai/
```

## 1. Backend starten

De backend draait via Docker samen met MySQL en de migrator.

### Configuratie

Maak deze file aan indien nodig:

- `backend_project/backend/.env`

Je kan starten van:

- `backend_project/backend/.env.example`

### Startcommando

```bash
cd backend_project
docker compose up --build
```

Wat dit opstart:

- FastAPI backend op `http://localhost:8000`
- MySQL op poort `3307`
- migrator die de SQL migrations uitvoert

### Controle

Open daarna:

- API root/docs: `http://localhost:8000/docs`

## 2. Frontend starten

De frontend gebruikt Vite en verwacht standaard de backend op `http://localhost:8000`.

### Installatie

```bash
cd frontend_project/AI_project_frontend
npm install
```

### Startcommando

```bash
npm run dev
```

Frontend draait dan lokaal via Vite. De exacte URL wordt in de terminal getoond, meestal:

- `http://localhost:5173`

### API configuratie

De frontend leest:

- `VITE_API_URL`

Als die niet gezet is, gebruikt de app standaard:

- `http://localhost:8000`

## 3. AI service starten

Deze service verzorgt enrichment en prospect generatie.

### Configuratie

Vul eerst de `.env` in:

- `AI_project_ai/.env`

### Belangrijke environment variabelen

De service gebruikt onder andere:

- `BACKEND_URL`
- `FRONTEND_URL`
- `OLLAMA_HOST`
- `GROQ_API_KEY` indien Groq gebruikt wordt

### Startcommando

```bash
cd AI_project_ai
docker compose up --build
```

Wat dit opstart:

- Ollama container
- model init container
- AI API container op `http://localhost:8001`

## Aanbevolen lokale opstartvolgorde

### Alleen backend + frontend

1. Start backend:
   ```bash
   cd backend_project
   docker compose up --build
   ```
2. Start frontend:
   ```bash
   cd frontend_project/AI_project_frontend
   npm install
   npm run dev
   ```

### Backend + frontend + AI service

1. Start backend via Docker
2. Start frontend via `npm run dev`
3. Vul `AI_project_ai/.env` in
4. Start AI service via Docker:
   ```bash
   cd AI_project_ai
   docker compose up --build
   ```

## Handige startpunten

- Backend docs: `http://localhost:8000/docs`
- Frontend: meestal `http://localhost:5173`
- AI service docs: `http://localhost:8001/docs`

## Bekende aandachtspunten

- De repo bevat meerdere `.env`-bestanden en defaults. Controleer welke effectief gebruikt worden.
- De AI service verwacht een correct ingevulde `AI_project_ai/.env`.
- De AI service draait via Docker op `8001`, de backend op `8000`.
- Voor een propere eerste start moet Docker Desktop actief zijn voordat je `docker compose up` uitvoert.

## Minimale quick start

Als je gewoon de hoofdapp lokaal wil zien werken:

```bash
cd backend_project
docker compose up --build
```

in een tweede terminal:

```bash
cd frontend_project/AI_project_frontend
npm install
npm run dev
```

Ga daarna naar de Vite URL in je terminal.
