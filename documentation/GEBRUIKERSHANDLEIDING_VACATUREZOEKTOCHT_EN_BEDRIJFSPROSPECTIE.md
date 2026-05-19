# Gebruikershandleiding voor vacaturezoektocht en bedrijfsprospectie

## InfoSearch — werken met de applicatie

**Project:** InfoSearch  
**Doelgroep:** eindgebruikers, demo-gebruikers en testers  
**Laatst bijgewerkt:** 18 mei 2026

---

## 1. Wat is InfoSearch?

InfoSearch is een webapplicatie voor twee zoekflows:

1. **Vacatures zoeken** — zoeken in vacaturedata op basis van een vrije query en filters.
2. **Bedrijven prospecteren** — bedrijven vinden die commercieel interessant kunnen zijn voor een product of dienst.

De applicatie gebruikt VDAB-vacaturedata als bron. Voor bedrijfsprospectie worden bedrijven en vacature-informatie gecombineerd met AI of met een deterministische fallbackranking wanneer de AI-service niet beschikbaar is.

---

## 2. Aanmelden

1. Open de applicatie in de browser.
2. Je komt op de loginpagina:

```text
/login
```

3. Vul je gebruikersnaam en wachtwoord in.
4. Klik op aanmelden.

Na succesvolle login ga je naar de homepagina:

```text
/home
```

Alle hoofdschermen behalve `/login` vereisen een actieve sessie.

---

## 3. Homepagina

Op de homepagina ziet de gebruiker:

- een persoonlijke begroeting;
- knoppen voor de twee hoofdflows;
- recente opgeslagen zoekopdrachten;
- voor admins: een knop om VDAB-data handmatig te verversen.

Belangrijkste acties:

| Actie | Knop |
|---|---|
| Vacatures zoeken | **Vacatures zoeken** |
| Bedrijven prospecteren | **Bedrijven prospecteren** |
| Opgeslagen items bekijken | **Alles bekijken** of navigatie naar `/saved` |
| VDAB handmatig syncen | Alleen zichtbaar voor admingebruikers |

---

## 4. Vacaturezoektocht

### 4.1 Nieuwe vacaturezoektocht starten

Ga via de homepagina naar:

```text
/search/job
```

Of klik op **Vacatures zoeken**.

### 4.2 Query invullen

Vul in het veld **Query** een zoekterm of profielomschrijving in.

Voorbeelden:

- `software developer python`
- `technisch tekenaar Antwerpen`
- `PLC engineer Siemens`
- `administratief medewerker deeltijds`

De query is verplicht. Zonder query wordt de zoekopdracht niet gestart.

### 4.3 Bestanden uploaden

De UI bevat een uploadzone voor PDF/DOCX-bestanden. De huidige zoekflow stuurt de belangrijkste zoekinformatie via query en filters naar de backend. Uploadfunctionaliteit is visueel voorzien, maar moet per deployment gecontroleerd worden op volledige backendverwerking.

Ondersteunde formaten in de UI:

- PDF;
- DOCX.

### 4.4 Filters gebruiken

Klik op de filterknop om extra filters te tonen.

Beschikbare vacaturefilters:

| Filter | Betekenis | Voorbeeld |
|---|---|---|
| Locatie | gemeente/regio waar de vacature zich bevindt | `Gent`, `Brussel`, `Antwerpen` |
| Contracttype | type contract of regime | `voltijds`, `deeltijds`, `freelance`, `interim` |
| Sector | sector of domein | `IT`, `Zorg`, `Industrie` |
| Ervaringsniveau | gewenst ervaringsniveau | `junior`, `medior`, `senior` |

### 4.5 Resultaten bekijken

Na het starten van de zoekopdracht ga je naar:

```text
/results/job
```

De frontend roept de backend aan via:

```http
POST /search
```

De resultaten tonen per vacature onder andere:

- vacaturetitel;
- bedrijfsnaam;
- locatie;
- beroep/sector;
- omschrijving;
- vereisten of motivatie;
- contactgegevens indien beschikbaar;
- VDAB/interne referentie indien beschikbaar.

### 4.6 Vacatureresultaten opslaan

Op de resultatenpagina kan je:

- de volledige zoekopdracht opslaan;
- resultaten exporteren naar Excel;
- een nieuwe zoekopdracht starten.

Opgeslagen zoekopdrachten verschijnen later in `/saved`.

---

## 5. Bedrijfsprospectie

### 5.1 Nieuwe prospectie starten

Ga via de homepagina naar:

```text
/search/company
```

Of klik op **Bedrijven prospecteren**.

### 5.2 Product- of dienstomschrijving invullen

Bij bedrijfsprospectie beschrijf je wat je verkoopt of aanbiedt. De applicatie zoekt bedrijven waarvoor dit relevant kan zijn.

Goede voorbeelden:

- `Predictive maintenance software voor Siemens S7-1500 installaties`
- `Cybersecurity awareness training voor middelgrote IT-bedrijven`
- `Automatisatie-oplossingen voor voedingsproductie en verpakkingslijnen`
- `Cloudmigratie voor KMO's met verouderde Windows Server infrastructuur`

Tips voor betere resultaten:

- wees concreet over technologieën;
- vermeld doelindustrieën;
- vermeld het probleem dat je oplost;
- gebruik termen die ook in vacatureteksten kunnen voorkomen;
- vermijd te korte queries zoals alleen `software` of `AI`.

### 5.3 Filters gebruiken

Klik op de filterknop om extra filters te tonen.

Beschikbare bedrijfsfilters:

| Filter | Betekenis | Voorbeeld |
|---|---|---|
| Locatie | gemeente of locatiebeperking | `Gent`, `Kortrijk`, `Brussel` |
| Sector | sector of technische context | `industrie`, `IT`, `voeding` |
| Bedrijfsgrootte | ruwe grootte-indicatie | `klein`, `middel`, `groot` |
| Regio | brede geografische regio | `Vlaanderen`, `Wallonië`, `Brussel` |

Let op: bedrijfsgrootte is in de huidige code een proxy op basis van het aantal gekoppelde vacatures. Er is nog geen echte personeelsdata uit CRM/KBO beschikbaar.

### 5.4 Resultaten bekijken

Na het starten van de zoekopdracht ga je naar:

```text
/results/company
```

De frontend roept de backend aan via:

```http
POST /companies/prospect
```

De resultaten tonen per bedrijf onder andere:

- bedrijfsnaam;
- sector;
- locatie;
- beschrijving;
- motivatie waarom het bedrijf past;
- score;
- contactgegevens indien beschikbaar;
- tech stack;
- machinepark;
- business trigger.

Als de AI-service actief is en er geen actieve filters zijn, kan de backend AI-ranking gebruiken. Als filters actief zijn of AI niet bereikbaar is, gebruikt de backend een deterministische ranking/fallback om te vermijden dat ongefilterde AI-resultaten getoond worden.

### 5.5 Scores interpreteren

De score is bedoeld als indicatie van commerciële relevantie.

| Score | Interpretatie |
|---:|---|
| 8-10 | sterke match met duidelijke evidence |
| 5-7 | mogelijke of goede match, verder na te kijken |
| 4 | zwakke maar nog bruikbare match |
| lager dan 4 | wordt normaal weggefilterd |

Gebruik de motivatie en evidence altijd samen met de score. Een hoge score zonder duidelijke inhoudelijke reden moet kritisch bekeken worden.

---

## 6. Opgeslagen zoekopdrachten en resultaten

Ga naar:

```text
/saved
```

Op deze pagina kan je wisselen tussen:

- **Hele zoekopdrachten**;
- **Individuele resultaten**.

Je kan zoeken op:

- titel;
- query;
- datum;
- bedrijfsnaam of vacaturetitel.

Je kan sorteren op:

- nieuwste eerst;
- oudste eerst;
- alfabetisch.

### 6.1 Opgeslagen zoekopdracht opnieuw openen

Klik op een opgeslagen zoekopdracht om de resultaten opnieuw te bekijken. De frontend opent dan de juiste resultatenpagina met de opgeslagen data.

### 6.2 Opgeslagen items verwijderen

Bij opgeslagen zoekopdrachten en individuele resultaten kan je items verwijderen. De applicatie vraagt eerst bevestiging.

Verwijderen is definitief voor de actieve database.

---

## 7. Exporteren naar Excel

Op resultatenpagina's kan je resultaten exporteren. De frontend gebruikt hiervoor de ingebouwde exportfunctionaliteit en maakt een `.xlsx`-bestand.

Typische exports:

- `vacature-resultaten.xlsx`;
- `bedrijf-resultaten.xlsx`.

Gebruik export voor verdere analyse, rapportering of demo's.

---

## 8. Goede zoekstrategieën

### Voor vacatures

Gebruik combinaties van:

- functietitel;
- technologie;
- locatie;
- contracttype;
- ervaringsniveau.

Voorbeeld:

```text
PLC technieker Siemens onderhoud Antwerpen
```

### Voor bedrijven

Beschrijf je aanbod alsof je uitlegt waarom een bedrijf het nodig heeft.

Minder goed:

```text
AI software
```

Beter:

```text
AI-software voor automatische kwaliteitscontrole in productiebedrijven met cameravisie en PLC-integratie
```

---

## 9. Beperkingen en aandachtspunten

- De datakwaliteit hangt af van VDAB-vacatureteksten.
- Sommige bedrijven hebben weinig of onvolledige informatie.
- AI-output moet kritisch gelezen worden.
- Bedrijfsgrootte is voorlopig een schatting op basis van vacatureactiviteit.
- Filters beperken de dataset, maar kunnen ook relevante bedrijven uitsluiten.
- Contactgegevens zijn alleen beschikbaar als ze in de brondata aanwezig zijn.
- Opgeslagen zoekopdrachten zijn gekoppeld aan de ingelogde gebruiker.

---

## 10. Foutmeldingen voor gebruikers

| Melding | Mogelijke oorzaak | Actie |
|---|---|---|
| “Voer een zoekopdracht in” | queryveld is leeg | vul een query in |
| “Geen vacatures gevonden” | geen match in database | probeer bredere zoekterm of minder filters |
| “Geen bedrijven gevonden” | geen match na filters/ranking | probeer andere query of verwijder filters |
| “Controleer of de backend draait” | backend niet bereikbaar | meld aan beheerder |
| Login mislukt | foutieve login of sessieprobleem | controleer gegevens of meld aan beheerder |
| Opslaan mislukt | sessie verlopen of databaseprobleem | opnieuw inloggen of beheerder contacteren |

---

## 11. Privacy voor gebruikers

Gebruik geen gevoelige persoonsgegevens in vrije zoekvelden tenzij dat noodzakelijk en toegestaan is. Zoekopdrachten en opgeslagen resultaten worden in de database bewaard en zijn gekoppeld aan de ingelogde gebruiker.

Voor meer details: zie `PRIVACY_EN_DATAVERWERKINGSNOTA.md`.
