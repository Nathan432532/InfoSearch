# Privacy- en dataverwerkingsnota

## InfoSearch — vacaturezoektocht en bedrijfsprospectie

**Project:** InfoSearch  
**Doelgroep:** projectteam, beheerders, gebruikers en beoordelaars  
**Laatst bijgewerkt:** 18 mei 2026

---

## 1. Doel van deze nota

Deze nota beschrijft welke gegevens InfoSearch verwerkt, waarom die gegevens verwerkt worden, waar ze opgeslagen worden en welke privacy- en beveiligingsmaatregelen relevant zijn.

InfoSearch is een applicatie voor vacaturezoektocht en AI-gedreven bedrijfsprospectie. De applicatie combineert vacaturedata, bedrijfsinformatie, gebruikersaccounts, zoekopdrachten en AI-output.

> Deze nota is bedoeld als projectdocumentatie. Voor een echte productieomgeving moet dit juridisch nagekeken worden volgens GDPR/AVG en de contractvoorwaarden van gebruikte databronnen en AI-providers.

---

## 2. Korte beschrijving van de verwerking

InfoSearch verwerkt data in twee hoofdflows:

1. **Vacaturezoektocht**
   - De gebruiker zoekt vacatures via een vrije zoekquery en filters.
   - De backend zoekt in lokaal opgeslagen VDAB-vacaturedata.
   - Resultaten kunnen opgeslagen worden.

2. **Bedrijfsprospectie**
   - De gebruiker beschrijft een product, dienst of commerciële vraag.
   - De backend zoekt bedrijven die mogelijk relevant zijn.
   - De AI-service of deterministische ranking beoordeelt welke bedrijven het beste passen.
   - Resultaten kunnen opgeslagen en geëxporteerd worden.

---

## 3. Verwerkte gegevenscategorieën

### 3.1 Gebruikersgegevens

De applicatie bevat lokale gebruikers en sessies.

Mogelijke gegevens:

| Gegeven | Voorbeeld | Doel |
|---|---|---|
| Gebruikers-ID | intern nummer | koppeling met zoekopdrachten en sessies |
| Gebruikersnaam | lokale loginnaam | aanmelden |
| Wachtwoordhash | hashwaarde | authenticatie |
| Displaynaam | naam in UI | persoonlijke begroeting |
| E-mailadres | lokaal/demo of echt adres | gebruikersidentificatie |
| Rol | `user` of `admin` | autorisatie |
| Sessietoken | random token in cookie | ingelogde sessie beheren |
| Vervaltijd sessie | datum/tijd | sessiebeveiliging |

De sessiecookie heet in de code:

```text
infosearch_session
```

### 3.2 Zoekopdrachten en filters

Wanneer gebruikers zoekopdrachten opslaan, worden onder andere verwerkt:

| Gegeven | Doel |
|---|---|
| Querytekst | zoekopdracht opnieuw kunnen tonen |
| Filters | resultaten reproduceerbaar maken |
| Zoektype | onderscheid tussen vacature- en bedrijfszoektocht |
| Titel | herkenbare opgeslagen zoekopdracht |
| Datum/tijd | sorteren en historiek tonen |
| Gekoppelde gebruiker | alleen eigen zoekopdrachten tonen |

Gebruikers moeten vermijden om gevoelige persoonsgegevens in vrije zoekvelden te plaatsen.

### 3.3 Vacaturegegevens

De primaire externe databron is de VDAB Open Services API. De backend haalt vacatures op en bewaart genormaliseerde gegevens in MySQL.

Mogelijke vacaturegegevens:

- interne VDAB-referentie;
- VDAB-referentie;
- status;
- publicatiedatum;
- functietitel;
- beroep/jobdomein;
- ervaring;
- vacatureomschrijving;
- vrije vereisten;
- contracttype en regime;
- locatiegegevens;
- sollicitatiegegevens indien aanwezig;
- ruwe JSON van de bron.

Sollicitatiegegevens kunnen persoonsgegevens bevatten, bijvoorbeeld een contactmailbox, telefoonnummer of naam wanneer de bron die meelevert.

### 3.4 Bedrijfsgegevens

Bedrijfsgegevens worden opgeslagen in `tblBedrijven` en kunnen afkomstig zijn uit VDAB-vacatures of latere verrijking.

Mogelijke bedrijfsgegevens:

- bedrijfsnaam;
- KBO-nummer indien beschikbaar;
- type bedrijf;
- website;
- algemeen e-mailadres;
- telefoonnummer;
- adres/postcode/gemeente/provincie;
- broncode;
- AI-verrijkingsvelden zoals sector, beschrijving, tech stack, machinepark, business trigger en keywords.

Bedrijfsgegevens zijn meestal ondernemingsdata. Toch kunnen contactgegevens of kleine ondernemingen indirect persoonsgegevens bevatten.

### 3.5 AI-input en AI-output

Voor bedrijfsprospectie en verrijking worden gegevens verwerkt door de AI-service.

Mogelijke AI-input:

- product- of dienstomschrijving van de gebruiker;
- bedrijfsprofielen;
- vacaturetitels;
- vacaturetekstfragmenten;
- sector/locatie/contactgegevens indien beschikbaar;
- tech stack, machinepark en keywords.

Mogelijke AI-output:

- score;
- motivatie waarom een bedrijf past;
- evidence snippets;
- sectorinschatting;
- business trigger;
- verrijkte beschrijving;
- gestructureerde keywords.

De AI-output is probabilistisch en kan fouten bevatten. Resultaten moeten daarom als ondersteunend advies worden gezien, niet als definitieve waarheid.

### 3.6 Logs en technische metadata

De applicatie logt via console/Dockerlogs onder andere:

- opstartinformatie;
- schedulerstatus;
- syncvoortgang;
- foutmeldingen;
- externe API-statussen;
- AI-verrijkingsstatus.

Logs mogen geen secrets of onnodige persoonsgegevens bevatten. In productie is logmasking en centrale logretentie aanbevolen.

---

## 4. Bronnen van gegevens

| Bron | Type data | Gebruik |
|---|---|---|
| VDAB Open Services API | vacatures en bijhorende bedrijfsinformatie | vacaturezoektocht, bedrijfsdataset en prospectie |
| Gebruiker | query's, filters, opgeslagen zoekopdrachten | zoekfunctionaliteit en historiek |
| Backenddatabase | eerder gesynchroniseerde data | snelle lokale zoekacties |
| AI-service / Ollama | AI-verrijking | gestructureerde bedrijfsprofielen |
| Groq, indien geconfigureerd | LLM-ranking | prospectranking op basis van bedrijfsprofielen |

Het databaseschema voorziet ook broncodes voor KBO, CRM en ResumeReader. In de huidige actieve flow ligt de nadruk op VDAB-data, lokale gebruikersdata en AI-output.

---

## 5. Doeleinden van de verwerking

InfoSearch verwerkt gegevens voor deze doeleinden:

1. Gebruikers laten aanmelden en sessies beheren.
2. Vacatures zoeken op basis van query en filters.
3. Bedrijven identificeren op basis van vacaturedata.
4. Bedrijfsprofielen verrijken met gestructureerde informatie.
5. Bedrijven rangschikken op commerciële relevantie voor een product/dienst.
6. Zoekopdrachten en resultaten opslaan voor later gebruik.
7. Resultaten exporteren voor analyse of rapportering.
8. Beheeracties ondersteunen, zoals VDAB-sync en troubleshooting.
9. Technische monitoring en foutopsporing.

---

## 6. Rechtsgrond en projectcontext

Voor een school- of demo-context is de verwerking primair technisch en educatief. Voor productie moet een verwerkingsverantwoordelijke formeel bepalen welke rechtsgrond van toepassing is.

Mogelijke rechtsgronden onder GDPR/AVG kunnen zijn:

- gerechtvaardigd belang voor B2B-prospectie, mits belangenafweging;
- uitvoering van een overeenkomst voor gebruikersaccounts binnen een organisatie;
- toestemming wanneer specifieke persoonsgegevens vrijwillig ingevoerd worden;
- wettelijke of contractuele verplichting indien databronvoorwaarden dat vereisen.

Voor commerciële inzet moet ook rekening gehouden worden met:

- VDAB-gebruiksvoorwaarden;
- ePrivacyregels rond elektronische communicatie;
- rechten van betrokkenen;
- bewaartermijnen;
- afspraken met AI-/cloudproviders.

---

## 7. Opslaglocaties

### 7.1 Database

De MySQL-database bevat onder andere:

| Tabel | Inhoud |
|---|---|
| `tblUsers` | applicatiegebruikers en rollen |
| `tblLocalUsers` | lokale loginaccounts |
| `tblLocalSessions` | sessietokens |
| `tblBedrijven` | bedrijven en AI-verrijkingsvelden |
| `tblVacatures` | VDAB-vacatures |
| `tblSearchSessions` | opgeslagen zoekopdrachten |
| `tblSearchResults` | opgeslagen resultaten |
| `tblFeedback` | voorziene feedbackdata |
| `tblEmbeddings` | voorziene vectorrepresentaties |
| `tblModelRuns` | voorziene modelrun-audit |

In Docker wordt MySQL opgeslagen in een volume, bijvoorbeeld:

```text
mysql_data
```

### 7.2 Browser

De browser bewaart een sessiecookie voor authenticatie. De frontend gebruikt verder runtime state en kan waarden zoals displaynaam tijdelijk in `sessionStorage` bewaren.

### 7.3 Logs

Dockerlogs worden bewaard door de Dockerhost zolang logretentie niet expliciet is ingesteld. In productie moet logrotatie geconfigureerd worden.

### 7.4 Externe AI-provider

Als `GROQ_API_KEY` geconfigureerd is en de AI-route gebruikt wordt, kunnen promptdata en bedrijfsprofielen naar Groq gestuurd worden voor ranking. Controleer hiervoor de providervoorwaarden, verwerkersafspraken en dataretentie-instellingen.

Ollama draait lokaal/containerized en verwerkt data binnen de eigen infrastructuur, zolang het gebruikte model lokaal draait.

---

## 8. Delen met derden

Mogelijke ontvangers of verwerkers:

| Partij | Wanneer | Data |
|---|---|---|
| VDAB | bij sync/API-aanroepen | requestmetadata en API-authenticatie; vacatures worden opgehaald |
| Groq | alleen indien geconfigureerd voor ranking | productomschrijving en compacte bedrijfsprofielen |
| VPS/cloudprovider | bij hosting | database, logs en applicatiedata op serverinfrastructuur |
| Beheerders | bij support/troubleshooting | logs, databasecontroles en accountbeheer |

Stuur geen onnodige persoonsgegevens naar externe AI-providers. Gebruik indien mogelijk lokale AI voor gevoelige data.

---

## 9. Bewaartermijnen

De huidige code bevat geen volledig retentiebeleid voor alle datatypes. Wel hebben sessies een configureerbare vervaltijd:

```env
SESSION_MAX_AGE=604800
```

Dit is standaard 604800 seconden, dus 7 dagen.

Aanbevolen retentiebeleid voor productie:

| Data | Aanbevolen bewaartermijn |
|---|---|
| Sessies | maximaal 7-30 dagen |
| Opgeslagen zoekopdrachten | zolang gebruiker/account actief is of max. 12 maanden |
| Zoekresultaten | gelijk aan zoekopdrachten |
| Vacaturedata | periodiek vernieuwen en oude vacatures verwijderen of archiveren |
| AI-output | zolang nodig voor opgeslagen resultaten, daarna verwijderen |
| Logs | 14-90 dagen, afhankelijk van supportbehoefte |
| Backups | 30-180 dagen, versleuteld |

Maak bewaartermijnen configureerbaar en documenteer wie verantwoordelijk is voor periodieke opschoning.

---

## 10. Rechten van betrokkenen

Als persoonsgegevens verwerkt worden, kunnen betrokkenen rechten hebben zoals:

- recht op inzage;
- recht op correctie;
- recht op verwijdering;
- recht op beperking van verwerking;
- recht op bezwaar;
- recht op dataportabiliteit, waar van toepassing.

Voor productie moet een beheerproces voorzien worden om gebruikersdata, opgeslagen zoekopdrachten en eventueel persoonsgegevens in vacature-/bedrijfsdata terug te vinden en te verwijderen.

---

## 11. Beveiligingsmaatregelen

Huidige en aanbevolen maatregelen:

| Maatregel | Status / aanbeveling |
|---|---|
| Sessiecookies | aanwezig via `infosearch_session` |
| HttpOnly cookies | aanwezig in backendlogin |
| Secure cookies | instelbaar via `SESSION_COOKIE_SECURE`; productie: `true` |
| SameSite cookies | instelbaar via `SESSION_COOKIE_SAMESITE` |
| CORS beperking | configureerbaar via `CORS_ALLOWED_ORIGINS` |
| Rolmodel | `user` en `admin` aanwezig |
| Database niet publiek publiceren | aanbevolen en in rootstack voorzien |
| Secrets in `.env` | aanwezig als werkwijze; niet committen |
| Password hashing | huidige code gebruikt eenvoudige SHA-256; productie: vervangen door Argon2/bcrypt |
| Adminroutes server-side beschermen | aanbevolen uitbreiding |
| HTTPS | via Caddy mogelijk |
| Backups | aanbevolen, versleuteld bewaren |
| Logging | geen secrets loggen; logrotatie instellen |

---

## 12. AI-specifieke privacyrisico's

AI-verwerking brengt extra aandachtspunten mee:

1. **Prompt leakage** — data in prompts kan bij externe providers terechtkomen.
2. **Hallucinaties** — AI kan foute sectoren, triggers of motivaties genereren.
3. **Bias** — bedrijven kunnen onterecht hoger/lager gerangschikt worden door onvolledige vacaturedata.
4. **Onvoldoende uitlegbaarheid** — scores moeten altijd samen met evidence/motivatie getoond worden.
5. **Data-minimalisatie** — stuur alleen compacte bedrijfsprofielen naar AI, geen onnodige ruwe persoonsgegevens.

Aanbevolen maatregelen:

- gebruik lokale Ollama-verwerking voor gevoelige data;
- beperk externe AI-input tot noodzakelijke velden;
- toon AI-resultaten als advies, niet als feit;
- log modelruns en evaluatiemetrics;
- voer periodieke kwaliteitscontroles uit met een golden dataset;
- laat gebruikers resultaten kritisch beoordelen.

---

## 13. Data-minimalisatie

Verwerk alleen data die nodig is voor de werking van de applicatie.

Praktische richtlijnen:

- bewaar geen volledige ruwe data als genormaliseerde velden volstaan;
- stuur geen CV's of persoonlijke documenten naar AI zonder noodzaak;
- vermijd persoonsgegevens in vrije queryvelden;
- beperk AI-prompts tot relevante bedrijfs- en vacaturefragmenten;
- verwijder oude zoekopdrachten en logs periodiek;
- anonimiseer of pseudonimiseer data in evaluatiesets.

---

## 14. Incidenten en datalekken

Voor productie moet een incidentproces bestaan:

1. Detecteer incident via logs, monitoring of melding.
2. Beperk toegang of stop de betrokken service.
3. Onderzoek welke data geraakt is.
4. Roteer secrets/API keys indien nodig.
5. Herstel uit backup indien nodig.
6. Documenteer impact en maatregelen.
7. Meld aan bevoegde instanties/betrokkenen indien wettelijk vereist.

Mogelijke incidenten:

- gelekte `.env`-bestanden;
- publiek toegankelijke databasepoort;
- foutieve CORS-instelling;
- onbeveiligde adminendpoint;
- logs met secrets;
- externe AI-provider ontvangt te veel data;
- verlies of corruptie van databasevolume.

---

## 15. Aanbevolen acties vóór productie

- [ ] Verwijder of wijzig demoaccounts.
- [ ] Vervang SHA-256 password hashing door Argon2 of bcrypt.
- [ ] Dwing adminrechten server-side af op `/sync` en beheerendpoints.
- [ ] Zet `SESSION_COOKIE_SECURE=true` bij HTTPS.
- [ ] Beperk `CORS_ALLOWED_ORIGINS` tot echte frontenddomeinen.
- [ ] Zet `VDAB_ALLOW_FALLBACK=false` in productie.
- [ ] Voeg expliciet retentiebeleid toe.
- [ ] Configureer logrotatie en masking.
- [ ] Maak versleutelde backups.
- [ ] Documenteer verwerkers en externe providers.
- [ ] Controleer VDAB-voorwaarden.
- [ ] Voer DPIA/risicoanalyse uit als de scope dat vereist.
- [ ] Voorzie export/verwijdering van gebruikersdata.

---

## 16. Samenvatting

InfoSearch verwerkt vooral vacaturedata, bedrijfsdata, gebruikerssessies, zoekopdrachten en AI-output. Voor een demo- of schoolcontext is de verwerking overzichtelijk, maar voor productie zijn extra maatregelen nodig rond autorisatie, password hashing, retentie, logging, externe AI-verwerking en formele GDPR-documentatie.

De belangrijkste privacyprincipes voor dit project zijn:

- beperk de hoeveelheid persoonsgegevens;
- bescherm sessies en adminacties;
- publiceer geen secrets;
- wees transparant over AI-gebruik;
- bewaar data niet langer dan nodig;
- controleer externe databron- en providervoorwaarden.
