from groq import Groq
from validator import valideer_llm_output
import json
import httpx
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
client = Groq(api_key=GROQ_API_KEY)
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:8999")
model = "groq/compound"  # Of "llama3-8b-8192" voor nog meer snelheid

PROFIEL_EXTRACTOR_PROMPT = """
JE BENT EEN ENTITY RESOLUTION AGENT.
Extraheer de bedrijfsidentiteit uit de vacaturetekst. 
Maak de naam uniform (bijv. 'NV Industri-Build' ipv 'Industri Build').
OUTPUT IN STRIKT JSON:
{
  "naam": "Bedrijfsnaam",
  "sector": "Sector",
  "tech_stack": ["Lijst", "van", "technieken"],
  "machine_park": ["Lijst", "van", "machines"],
  "contactgegevens": "Contactgegevens",
  "business_trigger": "Reden",
  "keywords": ["key1", "key2"],
  "locatie": "Locatie"
}
REGELS: Geen tekst om de JSON heen. Geen Markdown.
"""

async def extraheer_en_verrijk(vacature_tekst: str, retries: int = 2, raw_mode: bool = False):
    import ollama
    
    for _ in range(retries + 1):
        response = ollama.chat(
            model="qwen2.5:0.5b",
            messages=[
                {"role": "system", "content": PROFIEL_EXTRACTOR_PROMPT},
                {"role": "user", "content": vacature_tekst}
            ],
            options={"temperature": 0}
        )
        content = response["message"]["content"] or ""

        if raw_mode:
            return content # Stuur de rauwe string terug voor de benchmark
        
        # Gebruik het externe validatie script
        profiel, error = valideer_llm_output(content)
        
        if profiel:
            return profiel
        print(f"Validatie mislukt: {error}. Opnieuw proberen...")
        
    return None # Of een fallback profiel

# ... (Houd je PROFIEL_EXTRACTOR_PROMPT hetzelfde als in) ...

# async def extraheer_en_verrijk(vacature_tekst):
#     """Gebruik Groq voor razendsnelle extractie."""
#     chat_completion = client.chat.completions.create(
#         messages=[
#             {"role": "system", "content": PROFIEL_EXTRACTOR_PROMPT},
#             {"role": "user", "content": vacature_tekst},
#         ],
#         model=model, # Of "llama3-8b-8192" voor nog meer snelheid
#         temperature=0,
#     )
#     content = chat_completion.choices[0].message.content
#     if not content:
#         print("WAARSCHUWING: LLM gaf lege content terug.")
#         return {} # Of hanteer een default profiel
#     clean_json = content.replace("```json", "").replace("```", "").strip()
#     return json.loads(clean_json)

async def genereer_prospectie_rapport(product, bedrijven_data):
    """Genereer de TOP 3 matches via Groq."""
    prompt = f"""
            JE BENT EEN STRATEGISCHE B2B ANALYST. 
            Je doel is om een 'Product-Market Fit' te bepalen tussen een PRODUCT en een BEDRIJFSDATABASE.

            ANALYSE-METHODIEK:
            1. COMMERCIËLE SYNERGIE: Match de groei-triggers van het bedrijf (expansie, nieuw personeel, investeringen) met de waarde die het product levert.
            2. OPERATIONELE RELEVANTIE: Sluit de tech-stack of het machinepark aan op het gebruik van het product?
            3. SEGMENTATIE: Is de sector van het bedrijf een logische afnemer voor dit type product?

            STRIKTE LOGICA:
            - Filter op unieke bedrijfsnamen; elk bedrijf mag slechts één keer in de lijst verschijnen.
            - Gebruik uitsluitend de verstrekte database.
            - Scores moeten de werkelijke match-kwaliteit reflecteren (0-10). Wees meedogenloos objectief.
            - Taal: Zakelijk Nederlands, zonder AI-clichés of herhalingen.

            OUTPUT: Een JSON-lijst van unieke matches.

            PRODUCT: {product}
            DATABASE: {json.dumps(bedrijven_data)}
            GEEF EEN TOP 3

            ANTWOORD UITSLUITEND IN DIT JSON FORMAAT (EEN LIJST VAN OBJECTEN!):
            [
                {{
                    id: number;
                    bedrijfsnaam: string;
                    beschrijving: string;
                    waarom: string;
                    score: number;
                    contactgegevens: string;
                    techstack: string[];
                    locatie: string;
                    sector: string;
                }}
            ]

            STRIKTE REGELS:
            - Geen tekst voor of na de JSON.
            - Geen Markdown code blocks.
            - Antwoord in professioneel Nederlands.
            """
    
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model
    )
    content = chat_completion.choices[0].message.content or ""

    try:
        match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        else:
            raise ValueError("Geen JSON gevonden")
    except Exception as e:
        return {"error": str(e), "raw": content}


async def haal_vacatures():
    """Haalt onverwerkte vacatures uit de backend van de collega."""
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        print(f"DEBUG: AI-API probeert te verbinden met: {BACKEND_URL}")
        res = await client.get(f"{BACKEND_URL}/api/vacatures")
        print("vacatures opgehaald")
        return res.json() if res.status_code == 200 else []


async def push_profiel_naar_backend(profiel_json):
    """Stuurt het schone profiel terug naar de backend voor SQL UPSERT."""
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            print(f"Poging tot POST naar: {BACKEND_URL}/api/bedrijf/upsert")
            res = await client.post(
                f"{BACKEND_URL}/api/bedrijf/upsert", json=profiel_json
            )
            print(f"Server antwoordde met status: {res.status_code}")
        except Exception as e:
            print(f"FOUT TIJDENS PUSH: {e}")  # Hier zie je eindelijk wat er misgaat!


async def push_prospect_naar_frontend(prospect):
    """Stuurt het gegenereerde prospect naar de frontend."""
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            print(f"Poging tot POST naar: {BACKEND_URL}/api/prospect/upsert")
            res = await client.post(f"{BACKEND_URL}/api/prospect/upsert", json=prospect)
            print(f"Server antwoordde met status: {res.status_code}")
        except Exception as e:
            print(f"FOUT TIJDENS PUSH: {e}")  # Hier zie je eindelijk wat er misgaat!
