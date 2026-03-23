# LLM voor prospectie en bedrijf profielen opstellen

## installatie

Zorg dat je alles in requirements.txt hebt geïnstalleerd.
Voer __ollama pull qwen2.5:7b__ uit.

## hoe opstarten

engine.py, database.py en api.py werken allemaal samen.
database.py wordt enkel gebruikt om data lokaal op te slaan moest het nodig zijn.
Om de FastAPI app te starten voer je __uvicorn api:app --reload__ uit in je terminal>
Deze app vereist een werkende front- en backend.
Onderaan vind je een voorbeeld van een gebruiksklare node.js app die volledig werkt met deze app.
Ook een voorbeeld van een simpel python script om de routes van de api.py aan te spreken.

## wat doet de app

api.py bevat 2 aanroepbare post routes.
__post("/sync-and-enrich")__ zal eerst de vacatures ophalen van de backend server en van de vacatures zal de llm qwen2.5:7b bedrijfsprofielen opstellen. Deze bedrijfsprofielen worden terug naar de backend server gestuurd.
__post("/generate-prospect")__ zal die bedrijfsprofielen ophalen van de backend server en zal de 3 beste prospecten opstellen met een motivatie en een score. Deze prospecten worden momenteel terug naar de backend server gestuurd wegens testen maar dit moet uiteindelijk naar de frontend gestuurd worden.
Je kan ook nog gebruiken maken van de CLI om de LLM te gebruiken, die zal in dit geval gebruik maken van de lokaal opgeslagen data.
Om vacatures op te halen en bedrijfsprofielen op te stellen doe je __python api.py test_file__.
Om prospecten te genereren doe je __python api.py genereer__.

## voorbeeld node.js

```javascript
const express = require('express');
const app = express();
const PORT = 8999;

// Zorgt dat we JSON data kunnen lezen in POST requests
app.use(express.json());

const cors = require('cors');
app.use(cors()); // Laat alles toe, net als in je FastAPI

// Een simpele database in het geheugen (tot je de server stopt)
let vacatures = [
    {
        "bedrijf": "AGRO-BOTICS NV",
        "sector": "Landbouwmechanisatie & Robotica",
        "locatie": {
            "adres": "Kouterstraat 15",
            "postcode": "8500",
            "stad": "Kortrijk",
            "provincie": "West-Vlaanderen",
            "industriezone": "Kortrijk-Noord"
        },
        "contact_info": {
            "naam": "Dirk Vanhecke",
            "functie": "Technisch Directeur",
            "email": "d.vanhecke@agrobotics.be",
            "telefoon": "+32 56 12 34 56",
            "linkedin_company": "linkedin.com/company/agrobotics-nv"
        },
        "vacature_details": {
            "titel": "Field Service Engineer - Autonome Maaiers",
            "referentie": "VDAB-2024-9988",
            "urgentie": "Hoog (meerdere openstaande posities)"
        },
        "machine_park": [
            "Autonome GPS-gestuurde voertuigen",
            "Hydraulische systemen",
            "Batterij-management units"
        ],
        "tech_stack": [
            "CODESYS",
            "CAN-bus",
            "Linux-based controllers",
            "Python (scripting)"
        ],
        "business_trigger": "Lancering van een nieuwe generatie zelfrijdende oogstmachines en internationale expansie naar de Franse markt.",
        "keywords": ["service engineer", "robotica", "CAN-bus", "buitendienst", "elektrotechniek"]
    },
    {
        "bedrijf": "BREW-TECH AUTOMATION",
        "sector": "Voedingsmiddelenindustrie (Brouwerijen)",
        "locatie": {
            "adres": "Brouwerijstraat 1",
            "postcode": "3080",
            "stad": "Tervuren",
            "provincie": "Vlaams-Brabant",
            "industriezone": "Park-Midden"
        },
        "contact_info": {
            "naam": "Sarah Janssens",
            "functie": "Maintenance Manager",
            "email": "maintenance@brewtech.com",
            "telefoon": "+32 2 444 55 66",
            "website": "www.brewtech-automation.com"
        },
        "vacature_details": {
            "titel": "Automatisatie Technieker (Shift)",
            "referentie": "VDAB-2024-3322",
            "urgentie": "Gemiddeld"
        },
        "machine_park": [
            "Afvullijnen",
            "Pasteuriseer-installaties",
            "Palletiser-robots"
        ],
        "tech_stack": [
            "Schneider Electric (EcoStruxure)",
            "Wonderware InTouch (SCADA)",
            "Modbus TCP"
        ],
        "business_trigger": "Modernisering van de bestaande PLC-sturingen van S5 naar de nieuwste standaarden en uitbreiding van de productiecapaciteit met 20%.",
        "keywords": ["onderhoud", "storingen", "Schneider", "voeding", "HMI"]
    },
    {
        "bedrijf": "METAL-FORMING BELGIUM",
        "sector": "Zware Metaalindustrie",
        "locatie": {
            "adres": "Staalweg 88",
            "postcode": "3600",
            "stad": "Genk",
            "provincie": "Limburg",
            "industriezone": "Genk-Zuid"
        },
        "contact_info": {
            "naam": "Luc Mertens",
            "functie": "Plant Manager",
            "email": "l.mertens@metalforming.be",
            "telefoon": "+32 89 77 88 99",
            "algemeen_nummer": "+32 89 70 00 00"
        },
        "vacature_details": {
            "titel": "PLC & Drive Specialist",
            "referentie": "VDAB-2024-4455",
            "urgentie": "Kritiek"
        },
        "machine_park": [
            "Walsinstallaties",
            "CNC-bewerkingscentra (Groot formaat)",
            "Frequentieregelaars (High power)"
        ],
        "tech_stack": [
            "Siemens S7-1500",
            "Sinamics Drives",
            "Profinet",
            "Safety PLC"
        ],
        "business_trigger": "Aanleg van een compleet nieuwe productielijn voor chassis-onderdelen van elektrische voertuigen.",
        "keywords": ["PLC", "drives", "Siemens", "industriële elektriciteit", "storingstechnieker"]
    }
];

let prospecten = [{
    "id": 1,
    "bedrijfsnaam": "NV INDUSTRI-BUILD BELGIUM",
    "beschrijving": "Een bedrijf dat actief is in het gebied van prefab betonoplossingen, met een specifieke focus op PLC-gestuurde machines.",
    "waarom": "De technologische stack en machineparkering van NV INDUSTRI-BUILD BELGIUM zijn sterk gericht op industriële automatisering, wat een goede match is voor de technologie die nodig is in een mail cleaner. Hoewel het bedrijf niet direct met e-mailfilteringe ervaring bekend is, kan de technische expertise worden omgezet.",
    "score": 7,
    "contactgegevens": "N/A",
    "techstack": ["Siemens S7"],
    "locatie": "België"
}]

let bedrijfsprofielen = []

app.use((req, res, next) => {
    console.log(`Binnenkomend verzoek: ${req.method} ${req.url}`);
    next();
});

// --- GET Functies ---

// Haal alle items op
app.get('/api/vacatures', (req, res) => {
    console.log("GET verzoek ontvangen voor vacatures ophalen");
    res.json(vacatures);
});

// Haal één specifiek item op via ID
app.get('/api/items/:postcode', (req, res) => {
    const vacature = vacatures.find(i => i.postcode === parseInt(req.params.postcode));
    if (!vacature) return res.status(404).send('Dat item bestaat helemaal niet, suffie!');
    res.json(vacature);
});

app.get('/api/bedrijven/volledig', (req, res) => {
    console.log("GET verzoek ontvangen voor bedrijven");
    res.json(bedrijfsprofielen);
});

// --- POST Functies ---

// Voeg een nieuw item toe
app.post('/api/prospect/upsert', (req, res) => {
    console.log("--- Nieuwe Prospect POST ---");
    const data = req.body;
    
    if (!data || (Array.isArray(data) && data.length === 0)) {
        console.log("FOUT: Lege body ontvangen");
        return res.status(400).send('Lege data ontvangen');
    }

    const itemsToProcess = Array.isArray(data) ? data : [data];
    const addedItems = [];

    itemsToProcess.forEach((item, index) => {
        // Log elk item dat we proberen te verwerken
        console.log(`Verwerken item ${index + 1}:`, item.bedrijfsnaam);

        if (!item.bedrijfsnaam) {
            console.log(`FOUT: Item op index ${index} mist 'bedrijfsnaam'`);
            return; // skip dit item
        }

        const newItem = {
            id: prospecten.length + 1,
            bedrijfsnaam: item.bedrijfsnaam,
            beschrijving: item.beschrijving || "Geen beschrijving",
            waarom: item.waarom || "Geen motivatie",
            score: item.score || 0,
            contactgegevens: item.contactgegevens || "N/A",
            techstack: item.techstack || [],
            locatie: item.locatie || "Onbekend",
            sector: item.sector || "Onbekend"
        };

        prospecten.push(newItem);
        addedItems.push(newItem);
    });

    if (addedItems.length === 0) {
        console.log("FOUT: Geen enkel item was valide");
        return res.status(400).send('Geen valide items gevonden in de lijst');
    }

    console.log(`Succes! ${addedItems.length} items toegevoegd.`);
    res.status(201).json(addedItems);
});

app.post('/api/bedrijf/upsert', (req, res) => {
    if (!req.body.naam) {
        return res.status(400).send('Je moet wel een naam opgeven hoor!');
    }
    console.log("bedrijf", req.body.naam)
    const newItem = {
    "naam": req.body.naam,
    "sector": req.body.sector,
    "tech_stack": req.body.tech_stack,
    "machine_park": req.body.machine_park,
    "contactgegevens": req.body.contactgegevens,
    "business_trigger": req.body.business_trigger,
    "keywords": req.body.keywords,
    "locatie": req.body.locatie
    };

    bedrijfsprofielen.push(newItem);
    console.log("Nieuw bedrijfsprofiel toegevoegd:", newItem);
    res.status(201).json(newItem);

    });


// Start de server
app.listen(PORT, () => {
    console.log(`De server draait op http://localhost:${PORT}... Tevreden?`);
});
```

## voorbeeld python script

```python
import httpx
import json
import asyncio

FRONTEND_URL = "http://localhost:8000" # Pas poort aan indien nodig


async def bedrijfsprofiel_maken():
    """Stuurt het schone profiel terug naar de backend voor SQL UPSERT."""
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        await client.post(f"{FRONTEND_URL}/sync-and-enrich")

async def genereer_prospect():
    """Stuurt het product naar de API om een rapport te genereren."""
    timeout = httpx.Timeout(120.0, connect=60.0)
    
    # Dit is het product dat je wilt testen
    params = {"product": "Predictive Maintenance software voor Siemens S7-1500 systemen met automatische foutmeldingen via Profinet."}
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        # We voegen de string toe via de 'params' argument
        response = await client.post(
            f"{FRONTEND_URL}/generate-prospect", 
            params=params
        )
        
        if response.status_code == 200:
            print("Succes! Rapport is gegenereerd.")
            print(response.json())
        else:
            print(f"Foutje bedankt: {response.status_code}")
            print(response.text)

async def main():
    # Eerst de database vullen...
    await bedrijfsprofiel_maken()
    
    # Even een korte pauze om de achtergrondtaken in FastAPI de tijd te geven
    print("Even wachten tot de achtergrondtaken klaar zijn...")
    await asyncio.sleep(5) 
    
    # ...en dan pas matchen!
    await genereer_prospect()

if __name__ == "__main__":
    asyncio.run(main())
```

```yaml
version: '3.8'

services:
  # De AI Engine (Jouw Python code)
  ai-service:
    build: .
    container_name: ai-api
    ports:
      - "8000:8000"
    env_file:
      - .env
    # De variabelen worden nu uit .env gehaald, dus we hoeven ze hier niet te herhalen
    extra_hosts:
      - "host.docker.internal:host-gateway"
    # depends_on: ollama-server is niet meer nodig

# De rest (volumes en ollama-server) mag weg om RAM te besparen
```
