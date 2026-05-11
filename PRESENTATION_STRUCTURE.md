# Infosearch - Presentatie Structuur & Roadmap

**Strategische Context voor deze presentatie:**
Omwille van het onverwacht wegvallen van een teamlid (van 3 naar 2 personen), hebben we de scope van het project moeten aanpassen (Scope Management & Prioritisatie). De focus lag hierdoor 100% op het afwerken van het meest complexe deel: de AI-prospectie flow. Bepaalde functionele en technische eisen (zoals het lokaal draaien van de LLM en de vacature zoek-flow) zijn uitgesteld. Dit document beschrijft hoe we dit verdedigen in de presentatie.

---

## Slide 1: Titel & Introductie
* **Titel:** Infosearch: AI-gedreven Prospectie
* **Inhoud:**
  * Namen van de 2 groepsleden.
  * Doel: Een tool om efficiënt prospectie te doen door bedrijfsdata en vacatures slim te matchen met commerciële vragen.

## Slide 2: Het Initiële Probleem & Onze Scope
* **Titel:** Doelstelling & Scope Prioritisatie
* **Inhoud:**
  * Kort het volledige initiële doel: Zowel vacatures zoeken als AI-prospectie doen via een lokale LLM.
  * **Scope aanpassing:** Door het onverwacht wegvallen van een teamlid zijn we van 3 naar 2 personen gegaan. Hierdoor hebben we moeten prioriteren.
  * Onze focus lag volledig op het afwerken van het meest uitdagende deel: **De AI-prospectie flow**.

## Slide 3: Status Update - Wat werkt er wel & wat niet?
* **Titel:** Huidige Status van het Project
* **Inhoud:**
  * **Wat werkt er wél (In Scope):**
    * De Frontend interface voor prospectie (React/Vite).
    * De Backend API en database integratie (FastAPI/MySQL).
    * De AI Service en het matching model via een API.
    * Authenticatie en opgeslagen zoekopdrachten.
  * **Wat werkt er niet / is uitgesteld (Out of Scope):**
    * De "Vacatures zoeken" module (niet geïmplementeerd wegens tijdsgebrek).
    * Volledig lokaal draaien van de LLM (momenteel via externe API wegens *time-to-market* restricties).

## Slide 4: Demo van de Oplossing
* **Titel:** Demo: De Prospectie Flow in actie
* **Inhoud:**
  * Korte (live of video) demo van de prospectie-flow.
  * Toon de UI, hoe je zoekt naar prospects op basis van een product/dienst.
  * Toon de werkende filters (bv. sector, regio) en hoe frontend met backend praat.

## Slide 5: Architectuur & Data
* **Titel:** Architectuur & Onderliggende Data
* **Inhoud:**
  * **Architectuur:** React (Frontend) + FastAPI (Backend) + FastAPI/Python AI service, georkestreerd via Docker Compose.
  * **Welke Data gebruiken we?** 
    * We baseren ons op VDAB data (vacatures) om inzichten te krijgen over bedrijven.
    * *Kanttekening:* Omdat we geen toegang hebben tot volledige CRM data (zoals echte bedrijfsgrootte), gebruiken we het *aantal openstaande vacatures* tijdelijk als proxy om bedrijfsgrootte te bepalen.

## Slide 6: Uitdagingen (Organisatorisch & Technisch)
* **Titel:** Uitdagingen tijdens het project
* **Inhoud:**
  * **Organisatorische Uitdagingen:** 
    * De transitie van een 3-koppig naar een 2-koppig team halverwege het project vroeg om snelle keuzes in architectuur en een strikte scope afbakening.
  * **Data & Technische Uitdagingen:** 
    * **Data Kwaliteit:** Werken met ongestructureerde VDAB tekstdata maakt het moeilijk voor de AI om consistente keuzes te maken. 
    * **Filter logica:** Het was complex om filters (zoals regio, sector) die door de gebruiker in de Frontend worden gekozen, correct door de Backend naar de AI-wrapper te sturen.

## Slide 7: AI Evaluatie (Pijnpunten & Realiteit)
* **Titel:** AI Matching: Verwachtingen vs. Realiteit
* **Inhoud:**
  * Hoe het model nu matcht.
  * Onze bevindingen: Het model kiest vaak maar een paar "obvious" winnaars en heeft moeite met nuance als het ruwe tekst krijgt.
  * Conclusie: Input-data (skills, tech-stack, grootte) moet hard gestructureerd worden vóórdat het naar een AI gaat.

---

## 🚀 De Roadmap / Future Work (Het verdedigen van de hiaten)

## Slide 8: Roadmap Deel 1 - LLM API vs. Lokaal Draaien
* **Titel:** Future Work: Transitie naar Lokale AI
* **Inhoud:**
  * **De Toekomstige Oplossing:** 
    * Volledige migratie naar een lokale **Ollama** container binnen onze backend stack om de afhankelijkheid van externe API's op te vangen.
    * Open-source modellen (zoals Llama-3, Mistral) lokaal hosten om te voldoen aan de originele datasecurity eisen.

## Slide 9: Roadmap Deel 2 - Vacature Flow & Data Evaluatie
* **Titel:** Future Work: Uitbreiding & Test-Driven AI
* **Inhoud:**
  * **Vacature Flow Implementeren:** FastAPI routes uitbreiden (`/search/job`) en de herbruikbare React componenten koppelen aan de job-API.
  * **Data Evaluatie verbeteren:** Een 'Golden Dataset' bouwen (bv. 50 handmatig gelabelde perfecte matches) om de accuraatheid van toekomstige lokale LLM's geautomatiseerd te testen.

## Slide 10: Conclusie & Q&A
* **Titel:** Conclusie & Vragen
* **Inhoud:**
  * Korte samenvatting: Ondanks de organisatorische uitdagingen hebben we een robuuste architectuur gebouwd voor prospectie. We hebben in kaart hoe de rest gebouwd en gemigreerd moet worden.
  * Q&A.
