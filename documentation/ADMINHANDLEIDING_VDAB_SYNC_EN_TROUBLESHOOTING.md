# Adminhandleiding voor VDAB-sync en troubleshooting

## InfoSearch — beheer, synchronisatie en foutopsporing

**Project:** InfoSearch  
**Doelgroep:** beheerders, ontwikkelaars en testers met adminrechten  
**Laatst bijgewerkt:** 18 mei 2026

---

## 1. Doel van deze handleiding

Deze handleiding beschrijft hoe een beheerder de VDAB-sync gebruikt, controleert en troubleshoot. De VDAB-sync haalt vacatures op uit de VDAB Open Services API, normaliseert de data, bewaart vacatures en bedrijven in MySQL en triggert optioneel AI-verrijking.

---

## 2. Overzicht van de VDAB-datastroom

```text
VDAB API
  |
  | OAuth client credentials + API key
  v
Backend service: app/services/vdab_service.py
  |
  | ruwe vacaturelijst + detailrequests
  v
Cleaning: app/services/json_cleaner.py
  |
  | genormaliseerde vacature + bedrijf
  v
MySQL
  ├─ tblVacatures
  └─ tblBedrijven
  |
  | optioneel
  v
AI-service /enrich-new
  |
  v
tblBedrijven met AI-verrijkingsvelden
```

Belangrijke backendroutes:

| Route | Methode | Doel |
|---|---|---|
| `/health` | GET | basishealthcheck |
| `/vacancies` | GET | vacatures ophalen uit database |
| `/vacancies/{id}` | GET | één vacature ophalen |
| `/vacancies/update?aantal=500` | POST | VDAB-vacatures ophalen en upserten |
| `/sync?aantal=500` | POST | volledige sync: VDAB-import + optionele AI-verrijking |
| `/companies/unenriched?limit=200` | GET | bedrijven zonder AI-verrijking ophalen |
| `/companies/upsert-profile` | POST | AI-verrijking terugschrijven |
| `/companies/prospect` | POST | bedrijfsprospectie uitvoeren |

---

## 3. Adminfunctionaliteit in de frontend

Op de homepagina ziet een admin een extra knop:

```text
VDAB handmatig verversen
```

Deze knop roept aan:

```http
POST /sync?aantal=100
```

De UI toont daarna een melding zoals:

```text
VDAB sync klaar. X vacatures verwerkt, Y opgehaald.
```

Let op: de frontend verbergt de knop voor niet-admins. Voor productie moet de backend zelf ook afdwingen dat alleen admins `/sync` of vergelijkbare beheerendpoints kunnen uitvoeren.

---

## 4. Automatische VDAB-sync

De backend bevat een scheduler in `app/main.py`.

Belangrijke environment variables:

| Variabele | Standaard | Betekenis |
|---|---:|---|
| `AUTO_SYNC_ON_STARTUP` | `false` | sync kort na startup uitvoeren |
| `AUTO_SYNC_ENABLED` | `true` | geplande dagelijkse sync inschakelen |
| `AUTO_SYNC_TIME` | `02:30` | lokaal tijdstip voor de sync |
| `AUTO_SYNC_TZ` | `Europe/Brussels` | tijdzone voor de scheduler |
| `AUTO_SYNC_AMOUNT` | `500` | aantal vacatures per sync |

Voorbeeld:

```env
AUTO_SYNC_ON_STARTUP=false
AUTO_SYNC_ENABLED=true
AUTO_SYNC_TIME=02:30
AUTO_SYNC_TZ=Europe/Brussels
AUTO_SYNC_AMOUNT=500
```

De scheduler logt wanneer de volgende sync gepland staat:

```text
[scheduler] Next VDAB sync at ... Europe/Brussels
```

---

## 5. Handmatige sync uitvoeren

### 5.1 Via frontend

1. Log in als admin.
2. Ga naar `/home`.
3. Klik op **VDAB handmatig verversen**.
4. Wacht op de statusmelding.

### 5.2 Via FastAPI docs

Open:

```text
http://localhost:8000/docs
```

Gebruik:

```http
POST /sync?aantal=100
```

### 5.3 Via terminal

Lokaal:

```bash
curl -X POST "http://localhost:8000/sync?aantal=100"
```

Op de VPS achter Caddy:

```bash
curl -X POST "https://infosearch.duckdns.org/sync?aantal=100"
```

Gebruik in productie bij voorkeur een beveiligde adminroute of interne call, niet een publiek onbeveiligd endpoint.

---

## 6. Wat doet `/sync` precies?

De route `/sync` voert twee stappen uit:

1. `update_vacancies(aantal)`
   - haalt vacaturelijsten op bij VDAB;
   - vraagt per vacature detaildata op;
   - normaliseert data;
   - dedupliceert/koppelt bedrijven;
   - upsert vacatures in `tblVacatures`;
   - upsert bedrijven in `tblBedrijven`.

2. AI-verrijking, alleen als `AI_SERVICE_URL` gezet is:
   - roept `POST {AI_SERVICE_URL}/enrich-new` aan;
   - AI-service haalt bedrijven zonder `ai_enriched_at` op;
   - AI-service extraheert sector/tech stack/machinepark/business trigger/keywords;
   - AI-service schrijft resultaat terug via `/companies/upsert-profile`.

Voorbeeldrespons:

```json
{
  "import": {
    "fetched": 100,
    "upserted": 95,
    "new_businesses_saved": 20,
    "duplicates_merged_or_skipped": 5
  },
  "enrichment": {
    "status": "ok",
    "enriched": 18,
    "failed": 2,
    "total": 20
  }
}
```

De exacte velden kunnen verschillen per codeversie.

---

## 7. VDAB-configuratie

De backend gebruikt `app/services/vdab_service.py`.

Vereiste variabelen:

```env
VDAB_CLIENT_ID=<client-id>
VDAB_CLIENT_SECRET=<client-secret>
VDAB_API_KEY=<api-key>
VDAB_HOST=op-derden.vdab.be
VDAB_ALLOW_FALLBACK=true
```

Betekenis:

| Variabele | Doel |
|---|---|
| `VDAB_CLIENT_ID` | OAuth client credentials flow |
| `VDAB_CLIENT_SECRET` | OAuth secret |
| `VDAB_API_KEY` | header `X-IBM-Client-Id` |
| `VDAB_HOST` | VDAB-host voor tokenendpoint |
| `VDAB_ALLOW_FALLBACK` | fallbackvacature gebruiken bij rate limit of testproblemen |

Voor productie is aanbevolen:

```env
VDAB_ALLOW_FALLBACK=false
```

Zo vermijd je dat fallback/testdata in productie verschijnt.

---

## 8. Logs bekijken

### 8.1 Backendproject lokaal

Vanuit `backend_project/`:

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f migrator
docker compose logs -f mysql
```

### 8.2 Rootstack / VPS

Vanuit de projectroot:

```bash
docker compose -f docker-compose.yaml ps
docker compose -f docker-compose.yaml logs -f backend
docker compose -f docker-compose.yaml logs -f ai-api-test
docker compose -f docker-compose.yaml logs -f ollama-test
docker compose -f docker-compose.yaml logs -f caddy
```

### 8.3 Belangrijke logregels

Let op meldingen zoals:

- `Missing VDAB_CLIENT_ID / VDAB_CLIENT_SECRET env vars`;
- `Missing VDAB_API_KEY env var`;
- `Token error 401` of `Token error 403`;
- `Vacatures error ...`;
- `VDAB rate limit (429)`;
- `[vacancies] Processing X/Y ...`;
- `[scheduler] Next VDAB sync at ...`;
- `AI service unreachable`;
- `[enrich] Qwen extraction failed`.

---

## 9. Troubleshooting per probleem

### 9.1 Backend start niet

Controleer:

```bash
docker compose logs backend
```

Mogelijke oorzaken:

- `.env` ontbreekt;
- MySQL is nog niet healthy;
- poort `8000` is bezet;
- Python dependency ontbreekt;
- databasevariabelen kloppen niet.

Acties:

```bash
docker compose ps
docker compose logs mysql
docker compose logs migrator
docker compose up --build
```

### 9.2 Migrator faalt

Controleer:

```bash
docker compose logs migrator
```

Mogelijke oorzaken:

- database credentials mismatch;
- MySQL nog niet klaar;
- SQL-migratie bevat fout;
- oude database heeft afwijkend schema.

De migrator gebruikt een `schema_migrations` tabel om toegepaste migraties bij te houden. Idempotente DDL-fouten zoals bestaande tabellen/kolommen worden deels genegeerd.

### 9.3 VDAB token error

Voorbeeld:

```text
Token error 401: ...
```

Controleer:

- `VDAB_CLIENT_ID`;
- `VDAB_CLIENT_SECRET`;
- juiste omgeving/host;
- toegang bij VDAB;
- geen extra spaties in `.env`.

### 9.4 Missing VDAB_API_KEY

Voorbeeld:

```text
Missing VDAB_API_KEY env var
```

Zet `VDAB_API_KEY` in `backend_project/backend/.env`. De service gebruikt deze waarde voor de header:

```http
X-IBM-Client-Id: <VDAB_API_KEY>
```

### 9.5 Rate limit 429

De code probeert VDAB-aanroepen drie keer met backoff `1`, `2`, `4` seconden.

Bij `VDAB_ALLOW_FALLBACK=true` kan de service fallbackdata gebruiken. Bij productie is dit liever `false`.

Acties:

- verlaag `AUTO_SYNC_AMOUNT`;
- sync minder frequent;
- wacht en probeer later opnieuw;
- controleer VDAB-limieten;
- gebruik logs om te zien of fallback is gebruikt.

### 9.6 Sync duurt lang

Bij `aantal=500` wordt voor elke vacature detaildata opgehaald. Dat kan lang duren.

Acties:

- test eerst met `aantal=10` of `100`;
- monitor logs;
- controleer netwerk/VDAB-responstijd;
- zet AI-verrijking tijdelijk uit door `AI_SERVICE_URL` leeg te laten.

### 9.7 AI-verrijking faalt

Controleer:

```bash
docker compose logs ai-api-test
docker compose logs ollama-test
```

Mogelijke oorzaken:

- `AI_SERVICE_URL` fout in backend;
- `BACKEND_URL` fout in AI-service;
- Ollama draait niet;
- model niet gedownload;
- te weinig RAM;
- Groq API key ontbreekt of rate-limited.

Test AI-service:

```bash
curl http://localhost:8001/docs
```

Test of backend de AI-service intern ziet:

```bash
docker compose -f docker-compose.yaml exec backend python -c "import httpx; print(httpx.get('http://ai-api-test:8000/docs').status_code)"
```

### 9.8 Geen bedrijven bij prospectie

Mogelijke oorzaken:

- database bevat nog geen vacatures/bedrijven;
- VDAB-sync nog niet uitgevoerd;
- filters zijn te streng;
- AI-service geeft lege output;
- lage scores worden weggefilterd.

Acties:

1. Voer `/sync?aantal=100` uit.
2. Controleer `tblBedrijven` en `tblVacatures`.
3. Zoek zonder filters.
4. Gebruik een concretere productomschrijving.

### 9.9 CORS- of cookieproblemen

Symptomen:

- login lukt niet;
- frontend krijgt 401;
- browser blokkeert requests;
- cookies worden niet gezet.

Controleer:

```env
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://jouw-domein.be
SESSION_COOKIE_SECURE=false   # lokaal
SESSION_COOKIE_SECURE=true    # productie met HTTPS
SESSION_COOKIE_SAMESITE=lax
```

De frontend gebruikt `withCredentials`, dus CORS moet credentials toelaten en exact dezelfde origin bevatten.

---

## 10. Databasecontrole

Belangrijke tabellen:

| Tabel | Doel |
|---|---|
| `tblUsers` | gebruikers en rollen |
| `tblLocalUsers` | lokale loginaccounts |
| `tblLocalSessions` | sessietokens |
| `tblBedrijven` | bedrijven uit VDAB/AI |
| `tblVacatures` | vacatures uit VDAB |
| `tblSearchSessions` | opgeslagen zoekopdrachten |
| `tblSearchResults` | opgeslagen resultaten |
| `tblModelRuns` | voorzien voor modelrun-audit |

Voor controle via MySQL CLI:

```bash
docker compose exec mysql mysql -u root -p InfoSearch
```

Voorbeelden:

```sql
SELECT COUNT(*) FROM tblVacatures;
SELECT COUNT(*) FROM tblBedrijven;
SELECT COUNT(*) FROM tblBedrijven WHERE ai_enriched_at IS NOT NULL;
SELECT id, username, is_active FROM tblLocalUsers;
SELECT id, role, email, display_name FROM tblUsers;
```

---

## 11. Beheer van gebruikers en rollen

Rollen staan in `tblUsers.role` met waarden:

- `user`;
- `admin`.

De frontend gebruikt `/auth/me` om te bepalen of iemand admin is. Een admin krijgt extra UI-acties te zien.

Voor productie:

- wijzig of verwijder demoaccounts;
- gebruik sterke wachtwoorden;
- vervang eenvoudige SHA-256 password hashing door een password hashing algoritme zoals Argon2 of bcrypt;
- dwing adminrechten ook server-side af op beheerendpoints.

---

## 12. Checklist voor een gezonde sync

Voor een betrouwbare sync moeten deze punten in orde zijn:

- [ ] backend draait;
- [ ] MySQL is healthy;
- [ ] migraties zijn succesvol uitgevoerd;
- [ ] VDAB credentials zijn ingevuld;
- [ ] `VDAB_API_KEY` is ingevuld;
- [ ] `CORS_ALLOWED_ORIGINS` klopt;
- [ ] admin kan inloggen;
- [ ] `/health` geeft antwoord;
- [ ] `/sync?aantal=10` werkt als korte test;
- [ ] logs bevatten geen token-, database- of AI-errors;
- [ ] `tblVacatures` en `tblBedrijven` worden gevuld;
- [ ] optioneel: AI-verrijking vult `ai_enriched_at`.

---

## 13. Aanbevolen verbeteringen

Voor een productieklare beheeromgeving zijn deze uitbreidingen aanbevolen:

1. Server-side admincheck op `/sync`, `/vacancies/update` en vergelijkbare routes.
2. Rate limiting op beheerendpoints.
3. Structured logging in plaats van alleen consolelogs.
4. Centrale monitoring en alerting.
5. Retentiebeleid voor oude vacatures, logs en zoekresultaten.
6. Auditlog voor adminacties.
7. Robuuste password hashing.
8. CI/CD-pipeline met tests, build en migratiecontrole.
9. Periodieke backup en restoretest.
10. Modelkwaliteit periodiek evalueren met `AI_project_ai/evals/eval_ranking.py`.
