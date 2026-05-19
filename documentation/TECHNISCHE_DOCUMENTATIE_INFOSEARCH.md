# IT@AP

# Artificiële Intelligentie Project

# Technische documentatie

## InfoSearch — AI-gedreven vacaturezoektocht en bedrijfsprospectie

**Developers:** Nathan ter Hark & Sam Van Ginderen  
**Academiejaar:** 2025-2026, 2de semester  
**Documentdatum:** 16 mei 2026

---

# Inhoudstafel

1. Versiebeheer  
2. Termen en Afkortingen  
3. Samenvatting van de opdracht  
4. Data en Dataset Analyse  
   4.1 Databronnen  
   4.2 Datastructuur  
   4.3 Preprocessing  
   4.4 Data Governance  
5. AI/ML Model Selectie en Architectuur  
   5.1 Model Selectie  
   5.2 Prompt Engineering  
   5.3 Trainingsproces en Hyperparameters  
6. Model Evaluatie en Tests  
7. Deployment en Integratie  
8. Monitoring en Onderhoud  
9. Risicoanalyse en Mitigatie  
10. Operationele Kosten  
11. Ethiek en Bias Analyse  
12. Technisch design  
13. Externe systeeminterfaces  
14. Security en autorisatierollen  
15. Documentatie  
16. Bronvermelding

---

# Versiebeheer

| Nr. | Datum | Verspreiding | Status | Wijziging |
|---|---|---|---|---|
| 0.01 | 2026-05-11 | Projectteam InfoSearch | Eerste draft | Technische documentatie opgesteld op basis van de bestaande Word-template en de huidige projectcode. |
| 1.00 | 2026-05-16 | Projectteam InfoSearch / lector | Finale versie | Finale versie na controle en aanvulling van namen, screenshots en de presentatie. |

# Termen en Afkortingen

| Term | Omschrijving |
|---|---|
| AI | Artificiële intelligentie; in dit project gebruikt voor bedrijfsverrijking en prospectranking. |
| API | Application Programming Interface; interface waarmee frontend, backend, VDAB en AI-service communiceren. |
| CORS | Cross-Origin Resource Sharing; browsermechanisme dat bepaalt welke frontend-origins API-calls mogen doen. |
| CRUD | Create, Read, Update, Delete; basisoperaties op data. |
| Docker Compose | Tool om meerdere containers samen op te starten, zoals MySQL, backend, AI API en Caddy. |
| FastAPI | Python webframework gebruikt voor de backend en AI-service. |
| Frontend | React/Vite webapplicatie waarmee gebruikers zoeken, resultaten bekijken en resultaten opslaan. |
| GDPR | General Data Protection Regulation; Europese privacywetgeving. |
| Groq | Externe LLM-provider gebruikt voor prospectranking via `llama-3.3-70b-versatile`. |
| LLM | Large Language Model; taalmodel dat tekst begrijpt en genereert. |
| MySQL | Relationele database waarin gebruikers, vacatures, bedrijven, zoekopdrachten en resultaten worden opgeslagen. |
| Ollama | Lokale runtime om taalmodellen zoals Qwen te draaien. |
| Qwen | Lokaal LLM-model gebruikt voor extractie en verrijking van bedrijfsprofielen. |
| VDAB | Vlaamse Dienst voor Arbeidsbemiddeling en Beroepsopleiding; databron voor vacatures. |
| Vite | Buildtool en development server voor de React frontend. |

# Samenvatting van de opdracht

InfoSearch is een monorepo voor vacaturezoektocht en AI-gedreven bedrijfsprospectie. De applicatie laat gebruikers vacatures zoeken, bedrijfsprospecten vinden op basis van een product- of dienstomschrijving, zoekopdrachten opslaan en resultaten later opnieuw raadplegen. Het project bestaat uit drie hoofdonderdelen: een React/Vite frontend, een FastAPI backend met MySQL-database en een afzonderlijke AI-service voor enrichment en prospectranking.

De AI-component ondersteunt de commerciële prospectieflow. Bedrijfs- en vacaturedata worden opgehaald uit de backend, verrijkt met gestructureerde bedrijfsinformatie en daarna gebruikt om bedrijven te rangschikken volgens hun match met een opgegeven product of dienst. De applicatie combineert deterministische filtering in de backend met LLM-gebaseerde scoring en motivatie.

# Data en Dataset Analyse

## Databronnen

De primaire databron is de VDAB Open Services API. De backend haalt vacatures op via de VDAB-vacature-endpoints met OAuth client credentials en een API-key. Per vacature worden onder andere referentie, status, publicatiedatum, functietitel, beroepsinformatie, omschrijving, vereisten, contractgegevens, locatie, leverancier/bedrijf en sollicitatiegegevens verwerkt.

Naast VDAB voorziet het databaseschema ook plaats voor aanvullende bronnen zoals KBO, CRM en ResumeReader. In de huidige code worden deze als broncodes en tabellen voorzien, maar de actieve datastroom draait hoofdzakelijk rond VDAB-data, lokale gebruikersdata, opgeslagen zoekopdrachten en AI-verrijking.

De AI-service gebruikt twee soorten input:

- vacature- en bedrijfsgegevens uit de backend;
- een product- of dienstomschrijving die de gebruiker ingeeft in de prospectieflow.

## Datastructuur

De backend gebruikt MySQL als relationele database. Belangrijke tabellen zijn:

| Tabel | Doel |
|---|---|
| `tblUsers` | Applicatiegebruikers met rol `user` of `admin`. |
| `tblLocalUsers` | Lokale loginaccounts met gebruikersnaam en password hash. |
| `tblLocalSessions` | Sessietokens voor ingelogde gebruikers. |
| `tblSources` | Bronregistratie zoals VDAB, KBO, CRM en ResumeReader. |
| `tblBedrijven` | Canonieke bedrijven met KBO-nummer, naam, locatie, contactdata en AI-verrijkingsvelden. |
| `tblVacatures` | VDAB-vacatures met titel, beroep, omschrijving, vereisten, contractdata, locatie en bedrijfskoppeling. |
| `tblSearchSessions` | Opgeslagen zoekopdrachten per gebruiker. |
| `tblSearchResults` | Opgeslagen vacature- of bedrijfsresultaten inclusief rank, score en JSON-uitleg. |
| `tblFeedback` | Voorziene tabel voor feedback op resultaten. |
| `tblEmbeddings` | Voorziene tabel voor vectorrepresentaties. |
| `tblModelRuns` | Voorziene audit-tabel voor modelruns en metrics. |

De AI-verrijking op bedrijven wordt opgeslagen in extra kolommen op `tblBedrijven`, waaronder `sector`, `ai_beschrijving`, `tech_stack_json`, `machine_park_json`, `business_trigger`, `keywords_json` en `ai_enriched_at`.

## Preprocessing

De preprocessing gebeurt in meerdere stappen:

1. VDAB-response wordt opgehaald via de backendservice.
2. Ruwe vacaturedata wordt opgeschoond met `clean_vacature`.
3. Bedrijfsgegevens worden genormaliseerd en gededupliceerd op basis van onder andere naam, e-mail, telefoon, domein, adres en KBO-/BTW-nummer.
4. Vacatures worden gekoppeld aan bedrijven.
5. Voor AI-matching worden bedrijfsprofielen compact gemaakt in een vast schema met sector, locatie, vacaturetitels, beroepen, tech stack, machinepark, keywords, business triggers, evidence snippets en data completeness.
6. Productomschrijvingen worden deterministisch omgezet naar een productprofiel met doelindustrieën, technologieën, pijnpunten, ideale klant-signalen en bad-fit-signalen.

Voor filters gebruikt de backend normalisatie, tokenisatie en synoniemenlijsten. Voorbeelden zijn synoniemen rond `plc`, `scada`, `robotica`, `maintenance`, `voeding`, `logistiek` en locatie-aliases zoals Brussel/Brussels/Bruxelles.

## Data Governance

Data wordt opgeslagen in MySQL-volumes via Docker. De database bevat gebruikers, sessies, vacatures, bedrijven, opgeslagen zoekopdrachten en AI-resultaten. Toegang tot opgeslagen zoekopdrachten vereist een geldige sessiecookie. Gebruikers zien hun eigen opgeslagen zoekopdrachten; adminfunctionaliteit is voorzien via rolcontrole.

Datakwaliteit wordt bewaakt via:

- deduplicatie van bedrijven;
- validatie van verplichte velden bij opslaan;
- scoregrenzen voor opgeslagen bedrijfsresultaten;
- uitsluiten van lage kwaliteit resultaten onder score 4;
- JSON-validatie van LLM-output;
- retrylogica bij VDAB rate limits;
- fallbackgedrag wanneer VDAB tijdelijk niet beschikbaar is.

Bewaartermijnen zijn niet expliciet geconfigureerd in de huidige code. Sessies hebben wel een configureerbare maximumleeftijd via `SESSION_MAX_AGE`, standaard 604800 seconden of 7 dagen. Voor productie moet een expliciet retentiebeleid worden toegevoegd voor vacatures, zoekopdrachten, logs en AI-output.

# AI/ML Model Selectie en Architectuur

## Model Selectie

Het project gebruikt twee AI-routes:

1. **Qwen via Ollama** voor bedrijfsverrijking.  
   De AI-service gebruikt `qwen2.5:0.5b` om uit vacaturetekst gestructureerde bedrijfsinformatie te extraheren. De output moet strikt JSON zijn met velden zoals naam, sector, tech stack, machinepark, contactgegevens, business trigger, keywords en locatie.

2. **Groq `llama-3.3-70b-versatile`** voor prospectranking.  
   Dit model wordt gebruikt om product-market fit te beoordelen tussen een productprofiel en bedrijfsprofielen. Het model geeft per resultaat een score, motivatie, evidence en score-dimensies terug.

De keuze voor Qwen via Ollama is logisch voor lokale, containeriseerbare enrichment zonder dat elke extractie afhankelijk is van een externe API. De keuze voor Groq is logisch voor de rankingstap, omdat die complexere tekstuele afwegingen moet maken en een groter model nuttig is voor evidence-based redeneren.

Alternatieven zijn:

| Alternatief | Voordeel | Nadeel |
|---|---|---|
| Alleen deterministische ranking | Snel, goedkoop, uitlegbaar | Minder flexibel bij semantische matching. |
| Alleen lokaal Qwen-model | Minder afhankelijk van externe provider | Klein model geeft zwakkere rankingkwaliteit. |
| Groter lokaal model | Meer controle en privacy | Vereist meer geheugen/CPU/GPU. |
| Embeddings/SBERT | Geschikt voor semantische retrieval | Vereist extra vectorpipeline en evaluatie. |

De output is gedeeltelijk interpreteerbaar doordat het rankingmodel verplicht wordt om score-dimensies en evidence-snippets terug te geven. Daardoor kan een gebruiker zien waarom een bedrijf als match wordt getoond.

## Prompt Engineering voor LLM-projecten

De enrichmentprompt instrueert het model om als entity resolution agent te werken en uitsluitend geldige JSON terug te geven. De prompt bevat een vast outputschema en verbiedt extra tekst of Markdown. De LLM-output wordt nadien gevalideerd met `valideer_llm_output`.

De prospectrankingprompt is evidence-first ontworpen. Belangrijke promptregels zijn:

- vergelijk productprofiel en bedrijfsprofielen expliciet;
- geef hoge scores alleen bij concrete overlap in evidence, technologieën, rollen, vacaturetitels of business triggers;
- locatie mag nooit op zichzelf productrelevantie creëren;
- penaliseer lage evidence quality en ontbrekende data;
- laat no-match bedrijven weg;
- geef aparte score-dimensies voor technical fit, industry fit, business need, evidence strength en data confidence;
- antwoord uitsluitend in geldige JSON.

Geteste edge cases zijn onder andere:

- bedrijven met weinig data;
- bedrijven die enkel op locatie matchen;
- dubbele bedrijven;
- lage scores;
- filtercombinaties zoals sector, regio, locatie en bedrijfsgrootte;
- gevallen waarin de AI-service of externe API niet beschikbaar is.

## Trainingsproces en Hyperparameters

Er is geen klassiek trainingsproces met eigen modeltraining. Het project gebruikt bestaande LLM's en stuurt gedrag via prompt engineering, preprocessing en evaluatie. De belangrijkste hyperparameters/configuraties zijn:

| Component | Parameter | Waarde / gedrag |
|---|---|---|
| Qwen enrichment | Model | `qwen2.5:0.5b` |
| Qwen enrichment | Temperature | `0` voor deterministische extractie |
| Qwen enrichment | Retries | standaard 2 retries |
| Groq ranking | Model | `llama-3.3-70b-versatile` |
| Groq ranking | Temperature | `0` voor consistente ranking |
| Groq ranking | Max tokens | `2600` |
| Prospectranking | Max bedrijven naar prompt | maximaal 50 compacte bedrijfsprofielen; de AI-service vult aan tot maximaal 50 kandidaten wanneer de initiële gefilterde set minder dan 10 bedrijven bevat |
| Prospectranking | Max output | 10 bedrijven |
| Backend sync | Aantal vacatures | standaard 500 via `AUTO_SYNC_AMOUNT` |
| Scheduler | Sync tijd | standaard `02:30` Europe/Brussels |

# Model Evaluatie en Tests

De evaluatie gebeurt met een ranking-evaluatiescript in `AI_project_ai/evals/eval_ranking.py`. Dit script leest gelabelde gold data uit JSONL-bestanden, roept de backendendpoint `/companies/prospect` aan en berekent rankingmetrics.

De laatst gevonden evaluatierapportage (`latest_report.json`, gegenereerd op 2026-05-11T14:02:51Z) bevat 15 cases met deze samenvatting:

| Metric | Waarde |
|---|---:|
| nDCG@5 | 0.5704 |
| nDCG@10 | 0.6270 |
| Precision@3 | 0.2667 |
| Precision@5 | 0.2133 |
| Recall@5 | 0.3678 |
| Recall@10 | 0.4233 |
| MRR@10 | 0.5111 |
| Pairwise order accuracy | 0.9790 |
| Gemiddeld aantal resultaten | 9.4 |
| Labeled coverage@10 | 0.6667 |

De evaluatie toont dat de ranking al onderscheid kan maken tussen sommige relevante en minder relevante bedrijven, maar dat precision en recall nog beperkt zijn. Een belangrijk aandachtspunt is dat modelscorekalibratie niet altijd sterk is: in meerdere cases kregen verschillende bedrijven dezelfde score, waardoor de rangorde onvoldoende fijnmazig werd.

Naast modeltests zijn ook technische controles uitgevoerd:

- frontend build met `npm run build`;
- backend syntaxcheck met `python -m py_compile backend/app/routers/vdab.py`;
- frontend lint met `npm run lint`, waarbij nog bestaande lintissues buiten de nieuwe wijzigingen aanwezig zijn.

# Deployment en Integratie

De applicatie is containergericht opgezet. De hoofdstack in `docker-compose.yaml` bevat:

| Service | Doel |
|---|---|
| `mysql` | MySQL 8.0 database met persistent volume. |
| `backend` | FastAPI backend op interne poort 8000. |
| `ollama-test` | Ollama runtime voor lokaal AI-model. |
| `ai-api-test` | AI-service die backend en Ollama/Groq verbindt. |
| `ollama-init` | Init-container die het Qwen-model downloadt. |
| `migrator` | Voert SQL-migraties uit. |
| `caddy` | Reverse proxy naar de backend via `infosearch.duckdns.org`. |

De frontend draait lokaal via Vite of kan apart gebouwd en gehost worden. In de code is API-configuratie voorzien via `VITE_API_URL`; zonder expliciete configuratie gebruikt de frontend localhost of een serverfallback.

Belangrijke integratiepunten:

- frontend → backend via Axios/fetch met `withCredentials` voor sessiecookies;
- backend → VDAB via OAuth/API-key;
- backend → MySQL via `mysql-connector-python`;
- backend → AI-service via `AI_SERVICE_URL`;
- AI-service → backend via `BACKEND_URL`;
- AI-service → Ollama via `OLLAMA_HOST`;
- AI-service → Groq via `GROQ_API_KEY`.

Er is geen volledige CI/CD-pipeline in de repository aanwezig. Wel zijn build-, lint- en migratiescripts aanwezig. Voor productie wordt aanbevolen om een pipeline toe te voegen die minstens frontend build, backend tests, migraties en containerbuilds uitvoert.

# Monitoring en Onderhoud

De backend bevat een automatische VDAB-syncscheduler. Configuratie gebeurt via environment variables:

| Variabele | Doel |
|---|---|
| `AUTO_SYNC_ON_STARTUP` | Bepaalt of sync bij startup draait. |
| `AUTO_SYNC_ENABLED` | Bepaalt of geplande sync actief is. |
| `AUTO_SYNC_TIME` | Tijdstip van geplande sync, standaard `02:30`. |
| `AUTO_SYNC_TZ` | Tijdzone, standaard `Europe/Brussels`. |
| `AUTO_SYNC_AMOUNT` | Aantal vacatures per sync, standaard 500. |

Monitoring gebeurt momenteel vooral via consolelogs, health endpoints en foutafhandeling. De backend heeft `/health`, de AI-service heeft FastAPI-routes, en Docker healthchecks controleren MySQL. VDAB-aanroepen hebben retrylogica bij rate limits.

Datadrift en modeldrift worden nog niet automatisch gedetecteerd. De bestaande evaluatieset kan wel periodiek opnieuw uitgevoerd worden om rankingkwaliteit te controleren. Aanbevolen uitbreidingen zijn:

- periodiek evaluatierapport opslaan in `tblModelRuns`;
- logging centraliseren;
- alerts bij dalende nDCG/precision/recall;
- monitoring van AI API fouten en Groq rate limits;
- tracking van data completeness per bedrijf;
- detectie van veel lege of dubbele bedrijfsprofielen.

Foutafhandeling bestaat onder andere uit HTTP-statuscodes, try/except-blokken, fallback bij VDAB rate limits en foutmeldingen bij mislukte Groq-calls. Voor productie is gestructureerde logging met correlation IDs aanbevolen.

# Risicoanalyse en Mitigatie

| Risico | Kans | Impact | Mitigatie |
|---|---|---|---|
| Model geeft onjuiste of zwak onderbouwde prospects | Medium | Hoog | Evidence-first prompt, score-dimensies, evaluatieset, lage scores weren, human review. |
| Externe VDAB API niet beschikbaar of rate-limited | Medium | Hoog | Retry met backoff, fallbackdata, geplande sync buiten piekuren. |
| Groq API niet beschikbaar of rate-limited | Medium | Hoog | HTTP 429 doorgeven, deterministic fallbackranking gebruiken, retry/backoff toevoegen. |
| Onvoldoende datakwaliteit bij bedrijven | Hoog | Hoog | Data completeness berekenen, ontbrekende data penalizeren, betere enrichment en KBO/CRM-data toevoegen. |
| Dubbele bedrijven in resultaten | Medium | Medium | Dedupe op KBO, domein, e-mail, telefoon, naam en adres. |
| Sessietoken of cookie verkeerd geconfigureerd | Medium | Hoog | `HttpOnly`, `SameSite`, `Secure` in productie activeren en CORS strict configureren. |
| Hardcoded fallback API URL in frontend | Medium | Medium | Alleen `VITE_API_URL` gebruiken en fallback verwijderen voor productie. |
| Docker/Ollama resourcegebruik te hoog | Medium | Medium | Klein Qwen-model, memory limits en monitoring van containers. |
| GDPR-risico door persoonsgegevens in vacatures/contactdata | Medium | Hoog | Dataminimalisatie, retentiebeleid, toegangscontrole en documentatie van verwerkingsdoeleinden. |

# Operationele Kosten

| Component | Eenheid | Geschatte kost | Opmerkingen |
|---|---|---:|---|
| VPS/cloudhosting | Per maand | €5-€25 | Afhankelijk van gekozen server. Ollama vereist extra geheugen. |
| Domein/DNS | Per maand | €0-€2 | `duckdns.org` kan gratis gebruikt worden. |
| MySQL opslag | Per GB/maand | laag | Bij lokale Docker-host vooral inbegrepen in serverkost. |
| Groq API calls | Per tokens/API-gebruik | afhankelijk van providerplan | Ranking gebruikt `llama-3.3-70b-versatile`; kosten hangen af van volume. |
| Ollama/Qwen | Per maand | €0 licentiekost | Draait lokaal, maar gebruikt CPU/RAM. |
| VDAB API | Per gebruik | niet bepaald in code | Afhankelijk van VDAB-toegang/voorwaarden. |
| Caddy/SSL | Per maand | €0 | Caddy en Let's Encrypt zijn gratis te gebruiken. |

# Ethiek en Bias Analyse

Het project maakt aanbevelingen voor vacatures en bedrijfsprospects. Daardoor kan bias ontstaan wanneer de brondata onvolledig, verouderd of scheef verdeeld is. Bijvoorbeeld: bedrijven met meer vacatures of meer tekst kunnen sneller hoger scoren, ook als ze niet inhoudelijk beter passen. De huidige prompt probeert dit te beperken door concrete evidence te eisen en lage datakwaliteit te penalizeren.

Belangrijke ethische aandachtspunten:

- VDAB-data kan persoonsgegevens of contactgegevens bevatten;
- AI-output mag geen ongecontroleerde aannames maken over bedrijven;
- locatie mag niet als enige reden gebruikt worden voor relevantie;
- bedrijven met weinig publieke data mogen niet automatisch negatief beoordeeld worden zonder context;
- gebruikers moeten begrijpen dat scores ondersteunend zijn en geen absolute waarheid.

GDPR-compliance vereist dat enkel noodzakelijke gegevens worden verwerkt, dat toegang beperkt blijft tot geautoriseerde gebruikers en dat er een retentiebeleid komt. Sessies en opgeslagen resultaten zijn gekoppeld aan gebruikers. Productiegebruik vereist ook duidelijke privacyinformatie en afspraken rond externe AI-verwerking via Groq.

# Technisch design

InfoSearch bestaat uit drie hoofdcomponenten:

```text
[React/Vite Frontend]
        |
        | HTTPS / JSON / cookies
        v
[FastAPI Backend] ---- SQL ---- [MySQL]
        |
        | REST
        v
[AI Service FastAPI] ---- Ollama ---- [Qwen]
        |
        | Groq API
        v
[llama-3.3-70b-versatile]

[FastAPI Backend] ---- HTTPS/OAuth/API-key ---- [VDAB API]
```

De frontend bevat routes voor login, home, keuze tussen flows, job search, company search, resultaten en opgeslagen resultaten. Protected routes vereisen een ingelogde gebruiker.

De backend verzorgt:

- authenticatie en sessies;
- ophalen en opslaan van VDAB-vacatures;
- bedrijfszoektocht;
- prospectranking;
- opslaan en verwijderen van zoekopdrachten/resultaten;
- databaseconnectie en migraties;
- automatische geplande sync.

De AI-service verzorgt:

- enrichment van nieuwe bedrijven;
- extractie van bedrijfsprofielen uit vacaturetekst;
- voorbereiding van compacte bedrijfsprofielen;
- productprofilering;
- LLM-gebaseerde ranking met JSON-output.

De conceptuele databankstructuur bestaat uit gebruikers, bedrijven, vacatures, zoekopdrachten, resultaten en uitbreidingen voor tags, feedback, embeddings en modelruns. De database is relationeel opgezet met foreign keys tussen gebruikers, zoekopdrachten, resultaten, vacatures en bedrijven.

# Externe systeeminterfaces

| Interface | Richting | Protocol | Doel |
|---|---|---|---|
| Frontend → Backend | Uitgaand vanuit browser | HTTPS/JSON | Zoeken, login, resultaten opslaan/ophalen. |
| Backend → VDAB | Server-side | HTTPS/OAuth/API-key | Vacatures ophalen. |
| Backend → MySQL | Intern | MySQL TCP | Persistente opslag. |
| Backend → AI-service | Intern/HTTP | REST/JSON | Prospectranking en enrichment triggeren. |
| AI-service → Backend | Intern/HTTP | REST/JSON | Bedrijven ophalen en verrijkte profielen terugsturen. |
| AI-service → Ollama | Intern | HTTP via Ollama host | Qwen-model lokaal aanroepen. |
| AI-service → Groq | Extern | HTTPS/API-key | Ranking via groot LLM. |
| Caddy → Backend | Reverse proxy | HTTP/HTTPS | Publieke toegang tot backenddomein. |

DFD-overzicht:

```text
Gebruiker
  |
  v
Frontend -- login/search/save --> Backend
  |                              |
  |                              +--> MySQL
  |                              +--> VDAB API
  |                              +--> AI Service
  |                                      |
  |                                      +--> Ollama/Qwen
  |                                      +--> Groq LLM
  v
Resultaten, scores, motivatie en opgeslagen zoekopdrachten
```

Belangrijke backend endpoints zijn onder andere:

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

Belangrijke AI-service endpoints zijn:

- `POST /sync-and-enrich`
- `POST /generate-prospect`
- `POST /run-benchmark`
- `POST /enrich-new`

# Security en autorisatierollen

Authenticatie gebeurt via lokale gebruikers en sessiecookies. Bij login wordt een sessietoken gegenereerd met `secrets.token_urlsafe(32)` en opgeslagen in `tblLocalSessions`. De cookie heet `infosearch_session` en wordt `HttpOnly` gezet. `Secure`, `SameSite` en sessieduur zijn configureerbaar via environment variables.

Wachtwoorden worden momenteel met SHA-256 gehasht. Voor productie is dit onvoldoende sterk; aanbevolen wordt Argon2, bcrypt of PBKDF2 met salt en voldoende work factor.

Rollen:

| Rol | Toegang |
|---|---|
| `user` | Login, zoeken, resultaten bekijken, eigen zoekopdrachten en resultaten opslaan/verwijderen. |
| `admin` | Zelfde als user plus adminfunctionaliteit zoals handmatige VDAB-sync vanuit de frontend. |

Securitymaatregelen in de huidige code:

- sessiecontrole via `get_current_user_from_token`;
- user-based filtering bij opgeslagen zoekopdrachten;
- `HttpOnly` sessiecookie;
- configureerbare CORS origins;
- environment variables voor secrets;
- database foreign keys en constraints;
- validatie via Pydantic modellen;
- scorevalidatie en rejectie van lage kwaliteit saved company results.

Aanbevolen productieverbeteringen:

- `SESSION_COOKIE_SECURE=true` achter HTTPS;
- strengere CORS-configuratie zonder wildcard;
- sterke password hashing;
- secrets nooit committen in `.env`;
- rate limiting op login en AI endpoints;
- auditlogging voor adminacties;
- expliciete GDPR-retentie en dataverwijdering.

# Documentatie

Documentatie is aanwezig in meerdere bestanden:

- root `README.md` beschrijft monorepo, stack, quick start, routes en aandachtspunten;
- `AI_project_ai/README.md` beschrijft AI-service, routes en testvoorbeelden;
- `PROJECT_CHANGES_2026-05-08.md` documenteert recente wijzigingen, model-evaluatienotes en verificatie;
- evaluatiebestanden in `AI_project_ai/evals/` documenteren labeling, gold data en rankingrapportage;
- SQL-migraties documenteren databankstructuur en wijzigingen;
- code bevat docstrings en inline commentaar bij scheduler, enrichment en evaluatie.

Bij oplevering wordt aanbevolen om volgende handleidingen toe te voegen:

1. installatiehandleiding voor lokale setup;
2. deploymenthandleiding voor Docker/Hetzner/VPS;
3. gebruikershandleiding voor vacaturezoektocht en bedrijfsprospectie;
4. adminhandleiding voor VDAB-sync en troubleshooting;
5. privacy- en dataverwerkingsnota.

# Bronvermelding

[1] Projectteam InfoSearch. (2026). *InfoSearch repository README*. Lokaal projectbestand `README.md`.

[2] Projectteam InfoSearch. (2026). *InfoSearch Project Changes and Model Evaluation Notes*. Lokaal projectbestand `PROJECT_CHANGES_2026-05-08.md`.

[3] Projectteam InfoSearch. (2026). *AI enrichment wrapper en prospectranking*. Lokale bronbestanden `AI_project_ai/api.py` en `AI_project_ai/engine.py`.

[4] Projectteam InfoSearch. (2026). *Backend routers, authenticatie en VDAB-integratie*. Lokale bronbestanden `backend_project/backend/app/routers/auth.py`, `backend_project/backend/app/routers/vdab.py` en `backend_project/backend/app/services/vdab_service.py`.

[5] Projectteam InfoSearch. (2026). *Database schema en migraties*. Lokale projectbestanden in `backend_project/backend/db/migrations/`.

[6] Projectteam InfoSearch. (2026). *Ranking evaluation report*. Lokaal projectbestand `AI_project_ai/evals/results/latest_report.json`.

[7] FastAPI. (z.d.). *FastAPI documentation*. Opgehaald van https://fastapi.tiangolo.com/

[8] React. (z.d.). *React documentation*. Opgehaald van https://react.dev/

[9] Vite. (z.d.). *Vite documentation*. Opgehaald van https://vite.dev/

[10] Docker. (z.d.). *Docker Compose documentation*. Opgehaald van https://docs.docker.com/compose/

[11] Ollama. (z.d.). *Ollama documentation*. Opgehaald van https://ollama.com/

[12] Groq. (z.d.). *Groq documentation*. Opgehaald van https://console.groq.com/docs/

[13] VDAB. (z.d.). *VDAB Open Services vacatures*. Gebruikt via de in de code geconfigureerde VDAB API endpoints.
