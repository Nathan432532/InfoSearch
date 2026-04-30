from groq import Groq
from validator import valideer_llm_output
import json
import httpx
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
client = Groq(api_key=GROQ_API_KEY)
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:8999").rstrip("/")
model = "llama-3.3-70b-versatile"  # Snel, deterministisch, geen agentic overhead

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


def _compact_bedrijven_data(bedrijven_data):
    """Hou de prompt klein genoeg voor Groq TPM limieten."""
    compacte_bedrijven = []

    for b in bedrijven_data[:15]:
        vacature_titels = [str(t).strip() for t in (b.get("vacature_titels") or []) if str(t).strip()][:3]
        beroepen = [str(r).strip() for r in (b.get("beroepen") or []) if str(r).strip()][:3]

        compacte_bedrijven.append({
            "id": b.get("id"),
            "naam": b.get("naam", ""),
            "sector": b.get("sector", "Onbekend"),
            "locatie": b.get("locatie", ""),
            "vacature_titels": vacature_titels,
            "beroepen": beroepen,
        })

    return compacte_bedrijven

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
    """Genereer ranked company matches via Groq."""
    bedrijven_data = _compact_bedrijven_data(bedrijven_data)

    prompt = f"""
            JE BENT EEN KRITISCHE B2B MATCHING ENGINE.
            Jouw taak is om PRODUCT-MARKET FIT te beoordelen tussen één PRODUCT en een BEDRIJFSDATABASE.

            DOEL:
            - Zoek alleen bedrijven waarvoor er expliciete signalen in de dataset staan.
            - Wees streng. Liever te weinig resultaten dan zwakke of verzonnen matches.
            - Gebruik alleen bewijs uit sector, vacaturetitels, beroepen en locatie.

            BESLISREGELS:
            1. Een hoge score vereist concrete technische of operationele overlap.
            2. Algemene woorden zoals "industrie", "onderhoud", "productie" of "techniek" zijn op zichzelf NIET genoeg voor een hoge score.
            3. Als het product specifieke technologie noemt (bv. Siemens S7-1500, Profinet, SCADA, machine vision, field service), dan moeten die signalen duidelijk of redelijk direct terugkomen in de data voor een sterke match.
            4. Als de match speculatief of indirect is, geef een lage score.
            5. Als er geen duidelijke fit is, laat het bedrijf weg.
            6. Geen dubbele bedrijven.
            7. Gebruik uitsluitend de verstrekte database; verzin geen capabilities, installaties, use cases of contactgegevens.

            SCORE-RUBRIEK:
            - 9-10: bijna directe match, sterke expliciete overlap
            - 7-8: duidelijke relevante fit, maar niet perfect
            - 5-6: plausibele maar beperkte fit
            - 3-4: zwakke of indirecte fit
            - 0-2: geen zinvolle fit -> normaal niet teruggeven

            OUTPUTVEREISTEN:
            - Retourneer MAXIMAAL 10 matches.
            - Retourneer ZO WEINIG MATCHES ALS NODIG. Een lege lijst is toegestaan.
            - Sorteer aflopend op echte matchkwaliteit, niet op algemeenheid.
            - `waarom` moet kort en concreet verwijzen naar signalen uit de dataset.
            - `beschrijving` moet feitelijk blijven en niet marketingachtig worden.
            - `techstack` mag alleen elementen bevatten die echt in de dataset zitten.

            PRODUCT: {product}
            DATABASE: {json.dumps(bedrijven_data, ensure_ascii=False, separators=(',', ':'))}

            ANTWOORD UITSLUITEND IN GELDIGE JSON, ALS EEN LIJST VAN OBJECTEN:
            [
                {{
                    "id": number,
                    "bedrijfsnaam": string,
                    "beschrijving": string,
                    "waarom": string,
                    "score": number,
                    "contactgegevens": string,
                    "techstack": string[],
                    "locatie": string,
                    "sector": string
                }}
            ]

            EXTRA REGELS:
            - Geen tekst voor of na de JSON.
            - Geen Markdown code blocks.
            - Professioneel Nederlands.
            - Als bewijs zwak is, geef liever geen resultaat dan een mooie gok.
            """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0,
            max_tokens=2048,
        )
        content = chat_completion.choices[0].message.content or ""
    except Exception as e:
        print(f"[Groq] LLM call mislukt: {e}")
        return {"error": str(e), "raw": ""}

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
