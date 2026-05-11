# Infosearch - Presentatie Structuur & Roadmap

**Strategische Context voor deze presentatie:**
Omwille van het onverwacht wegvallen van een teamlid (van 3 naar 2 personen), hebben we de scope van het project moeten aanpassen (Scope Management & Prioritisatie). De focus lag hierdoor 100% op het afwerken van het meest complexe deel: de AI-prospectie flow. Bepaalde functionele en technische eisen (zoals het lokaal draaien van de LLM en de vacature zoek-flow) zijn uitgesteld. Dit document beschrijft hoe we dit verdedigen in de presentatie met een sterke focus op "Future Work".

---

## Slide 1: Titel & Introductie
* **Titel:** Infosearch: AI-gedreven Prospectie
* **Inhoud:**
  * Namen van de 2 groepsleden.
  * Doel: Een tool om efficiënt prospectie te doen door bedrijfsdata en vacatures slim te matchen met commerciële vragen.

## Slide 2: Het Probleem & Onze Scope (Zeer belangrijk!)
* **Titel:** Het Probleem & Onze Scope
* **Inhoud:**
  * Kort het volledige initiële doel: Zowel vacatures zoeken als AI-prospectie doen.
  * **Belangrijke vermelding:** Omwille van het onverwacht wegvallen van een teamlid (van 3 naar 2), hebben we de scope moeten *prioriteren*.
  * Onze focus lag daarom volledig op het afwerken van het meest uitdagende/complexe deel: **De AI-prospectie flow**.

## Slide 3: De Oplossing (Demo)
* **Titel:** Wat werkt er wél: De Prospectie Flow
* **Inhoud:**
  * Korte (live of video) demo van de prospectie-flow.
  * Toon de UI, hoe je zoekt naar prospects op basis van een product/dienst.
  * Toon werkende filters (bv. sector, regio) en hoe frontend met backend praat.

## Slide 4: Architectuur (As-Is)
* **Titel:** Huidige Architectuur & Tech Stack
* **Inhoud:**
  * React/Vite (Frontend) + FastAPI (Backend) + FastAPI/Python AI service.
  * Visueel overzicht of opsomming.
  * Vermelding van Docker Compose om alles samen te draaien.

## Slide 5: AI Evaluatie (Pijnpunten & Realiteit)
* **Titel:** AI Matching: Verwachtingen vs. Realiteit
* **Inhoud:**
  * Hoe het model nu matcht.
  * Onze bevindingen: Het model kiest vaak maar een paar "obvious" winnaars en heeft moeite met nuance.
  * Conclusie: Input-data (skills, tech-stack, grootte) moet hard gestructureerd worden voordat het naar een AI gaat voor een eerlijke match.

---

## 🚀 De Roadmap / Future Work (Het verdedigen van de hiaten)

*Tip voor de presentatie: Wacht niet op de vragen van de jury. Vertel zélf direct waarom jullie een API hebben gebruikt en hoe jullie dit in de toekomst zouden oplossen. Dit toont maturiteit.*

## Slide 6: Roadmap Deel 1 - LLM API vs. Lokaal Draaien
* **Titel:** Future Work: Transitie naar Lokale AI
* **Inhoud:**
  * **De Huidige Situatie:** We gebruiken nu een LLM via een API (zoals Groq/OpenAI) in plaats van lokaal. De reden is *time-to-market* wegens het wegvallen van een teamlid. De API was sneller op te zetten om de applicatie-logica te valideren.
  * **De Toekomstige Oplossing:** 
    * Volledige migratie naar een lokale **Ollama** container binnen onze backend stack.
    * Open-source modellen (Llama-3, Mistral) lokaal hosten.
    * Dit lost de originele requirements op inzake datasecurity (geen data naar de cloud) en geen API-kosten.

## Slide 7: Roadmap Deel 2 - Vacature Functionaliteit
* **Titel:** Future Work: Uitbreiding naar de Vacature Flow
* **Inhoud:**
  * **De Huidige Situatie:** De functionaliteit "vacatures zoeken" is tijdelijk gepauzeerd in onze scope.
  * **De Toekomstige Oplossing (Architecturaal):**
    * Backend: Dedicated FastAPI routes `/search/job` opzetten voor filtering op locatie, sector en beroep via SQL queries.
    * Frontend: Een herbruikbare React search-pagina bouwen die dezelfde layout componenten gebruikt als de prospectie-pagina, maar aangesloten op de job-API.

## Slide 8: Roadmap Deel 3 - Data Pipeline & Test-Driven AI
* **Titel:** Future Work: Betere Data & Evaluatie
* **Inhoud:**
  * **Datastructuur:** Ruwe vacatureteksten structureren (verplichte velden afdwingen zoals bedrijfsgrootte en tech stack) vóór het matchen.
  * **Geautomatiseerde Evaluatie:** Een 'Golden Dataset' bouwen (bv. 50 handmatig gelabelde perfecte matches) om de accuraatheid van toekomstige lokale LLM's geautomatiseerd te testen in een CI/CD flow.

## Slide 9: Conclusie & Q&A
* **Titel:** Conclusie & Vragen
* **Inhoud:**
  * Korte samenvatting: We hebben sterke keuzes moeten maken, maar hierdoor wel een robuuste architectuur gebouwd voor prospectie. We hebben in kaart hoe de rest gebouwd en gemigreerd moet worden.
  * Q&A.
