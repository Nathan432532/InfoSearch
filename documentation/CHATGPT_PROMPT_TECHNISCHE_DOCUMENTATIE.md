# ChatGPT prompt — Technische documentatie maken volgens Word-template

Kopieer onderstaande prompt naar ChatGPT. Voeg daarna de inhoud van de projectbestanden toe of upload de map/documenten als ChatGPT dat ondersteunt.

---

## Prompt

Je bent een technische documentatie-assistent. Ik moet een technische documentatie maken voor een AI-project. Je mag NIET freestyle schrijven. Je moet de structuur van het Word-document **“Technische documentatie_AI (2).docx”** stap voor stap volgen.

Maak de documentatie in het Nederlands en gebruik exact deze volgorde:

1. Titelpagina
2. Inhoudstafel
3. Versiebeheer
4. Termen en Afkortingen
5. Samenvatting van de opdracht
6. Data en Dataset Analyse
   - Databronnen
   - Datastructuur
   - Preprocessing
   - Data Governance
7. AI/ML Model Selectie en Architectuur
   - Model Selectie
   - Prompt Engineering voor LLM-projecten
   - Trainingsproces en Hyperparameters
8. Model Evaluatie en Tests
9. Deployment en Integratie
10. Monitoring en Onderhoud
11. Risicoanalyse en Mitigatie
12. Operationele Kosten
13. Ethiek en Bias Analyse
14. Technisch design
15. Externe systeeminterfaces
16. Security en autorisatierollen
17. Documentatie
18. Bronvermelding

Belangrijke regels:

- Gebruik de Word-template als blueprint.
- Verwijder alle placeholdertekst uit de template.
- Voeg geen nieuwe hoofdsecties toe buiten de template.
- Als informatie ontbreekt, schrijf duidelijk: **[in te vullen]**.
- Gebruik tabellen waar de template tabellen verwacht, zoals bij versiebeheer, termen, risicoanalyse en operationele kosten.
- Baseer de inhoud op de echte projectbestanden, niet op verzonnen aannames.
- Schrijf professioneel maar begrijpelijk Nederlands.
- Vermeld technische details concreet: gebruikte frameworks, API’s, database, AI-modellen, deployment, security, evaluatiemetrics en risico’s.
- Gebruik geen marketingtaal.

Projectcontext:

Het project heet **InfoSearch**. Het is een monorepo voor vacaturezoektocht en AI-gedreven bedrijfsprospectie.

De repo bestaat uit:

- `backend_project/` — FastAPI backend + MySQL + migraties
- `frontend_project/AI_project_frontend/` — React/Vite frontend
- `AI_project_ai/` — AI-service voor enrichment en prospectgeneratie

Belangrijke technologieën:

- Frontend: React 19, TypeScript, Vite, React Router, TanStack Query, Axios, GSAP, MSAL
- Backend: FastAPI, MySQL, Docker Compose
- AI-service: Python, FastAPI, Ollama, Qwen, optioneel Groq
- Deployment: Docker Compose, Caddy reverse proxy, MySQL volume

Belangrijke functionaliteiten:

- Login/auth flow
- Protected frontend routes
- Vacatures zoeken via query en filters
- Bedrijven prospecteren op basis van product/dienstomschrijving
- AI-verrijking van bedrijfsprofielen
- Prospectranking met motivatie en score
- Opgeslagen zoekopdrachten en resultaten
- Admin-trigger voor handmatige VDAB-sync
- Automatische geplande VDAB-sync

Belangrijke backend endpoints:

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`
- `GET /health`
- `GET /vacancies`
- `POST /search`
- `POST /companies/search`
- `POST /companies/prospect`
- `GET /companies/unenriched`
- `POST /companies/upsert-profile`
- `POST /sync`
- `POST /searches/save`
- `POST /searches/save-item`
- `GET /searches/saved`

Belangrijke AI-service endpoints:

- `POST /sync-and-enrich`
- `POST /generate-prospect`
- `POST /run-benchmark`
- `POST /enrich-new`

AI-details:

- Qwen via Ollama wordt gebruikt voor bedrijfsverrijking.
- Het gebruikte lokale model is `qwen2.5:0.5b`.
- De enrichment-output moet strikt JSON zijn met velden zoals naam, sector, tech_stack, machine_park, contactgegevens, business_trigger, keywords en locatie.
- Groq `llama-3.3-70b-versatile` wordt gebruikt voor prospectranking.
- Ranking gebruikt temperature 0 en geeft maximaal 10 resultaten terug.
- Het model moet evidence-based scoren en locatie mag niet als enige matchreden tellen.

Evaluatiegegevens:

De laatste evaluatie had 15 cases en deze samenvattende metrics:

- nDCG@5: 0.5704
- nDCG@10: 0.6270
- Precision@3: 0.2667
- Precision@5: 0.2133
- Recall@5: 0.3678
- Recall@10: 0.4233
- MRR@10: 0.5111
- Pairwise order accuracy: 0.9790
- Gemiddeld aantal resultaten: 9.4
- Labeled coverage@10: 0.6667

Databasecontext:

Belangrijke tabellen:

- `tblUsers`
- `tblLocalUsers`
- `tblLocalSessions`
- `tblSources`
- `tblBedrijven`
- `tblVacatures`
- `tblSearchSessions`
- `tblSearchResults`
- `tblFeedback`
- `tblEmbeddings`
- `tblModelRuns`

AI-verrijking op bedrijven gebruikt onder andere:

- `sector`
- `ai_beschrijving`
- `tech_stack_json`
- `machine_park_json`
- `business_trigger`
- `keywords_json`
- `ai_enriched_at`

Securitycontext:

- Lokale login met username/password
- Sessiecookies via `infosearch_session`
- Cookie is `HttpOnly`
- `Secure`, `SameSite` en sessieduur zijn configureerbaar via environment variables
- Rollen: `user` en `admin`
- User ziet eigen opgeslagen zoekopdrachten
- Admin kan extra beheeracties uitvoeren zoals VDAB-sync
- Wachtwoorden worden momenteel met SHA-256 gehasht; vermeld dat Argon2/bcrypt/PBKDF2 aanbevolen is voor productie

Deploymentcontext:

Docker Compose services:

- `mysql`
- `backend`
- `ollama-test`
- `ai-api-test`
- `ollama-init`
- `migrator`
- `caddy`

Caddy reverse proxyt `infosearch.duckdns.org` naar `backend:8000`.

Output gevraagd:

Maak een volledige technische documentatie in Markdown, klaar om later naar Word te kopiëren. Houd de secties exact in dezelfde volgorde als hierboven. Gebruik tabellen waar nuttig. Schrijf geen uitleg over wat je gaat doen; geef direct het document.

---

## Extra instructie als ChatGPT bestanden kan lezen

Als ik projectbestanden upload, controleer dan eerst deze bestanden en gebruik ze als primaire bron:

- `README.md`
- `docker-compose.yaml`
- `Caddyfile`
- `PROJECT_CHANGES_2026-05-08.md`
- `backend_project/backend/app/main.py`
- `backend_project/backend/app/routers/auth.py`
- `backend_project/backend/app/routers/vdab.py`
- `backend_project/backend/app/services/vdab_service.py`
- `backend_project/backend/db/migrations/*.sql`
- `AI_project_ai/api.py`
- `AI_project_ai/engine.py`
- `AI_project_ai/evals/eval_ranking.py`
- `AI_project_ai/evals/results/latest_report.json`
- `frontend_project/AI_project_frontend/package.json`

Gebruik geen informatie die niet in deze bestanden staat, tenzij je die duidelijk markeert als **[aanname]** of **[in te vullen]**.
