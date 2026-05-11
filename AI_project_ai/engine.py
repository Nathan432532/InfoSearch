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


def _as_clean_list(value, limit: int | None = None) -> list[str]:
    """Normalize loose API fields into short comparable string lists."""
    if value is None:
        items: list[str] = []
    elif isinstance(value, list):
        items = value
    else:
        items = [value]

    cleaned: list[str] = []
    seen: set[str] = set()
    for item in items:
        if isinstance(item, dict):
            item = item.get("titel") or item.get("beroep") or item.get("omschrijving") or json.dumps(item, ensure_ascii=False)
        text = str(item).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text[:220])
        if limit and len(cleaned) >= limit:
            break
    return cleaned


def _extract_evidence_snippets(company: dict, limit: int = 6) -> list[str]:
    """Keep short proof snippets so the model can cite evidence instead of guessing."""
    snippets: list[str] = []
    fields = [
        company.get("sector"),
        company.get("business_trigger"),
        company.get("ai_beschrijving"),
        *_as_clean_list(company.get("vacature_titels") or company.get("vacatures"), 4),
        *_as_clean_list(company.get("vacature_samenvattingen"), 3),
        *_as_clean_list(company.get("tech_stack") or company.get("techstack"), 6),
        *_as_clean_list(company.get("machine_park") or company.get("machinepark"), 6),
        *_as_clean_list(company.get("keywords"), 8),
    ]
    seen: set[str] = set()
    for value in fields:
        text = str(value or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        snippets.append(text[:180])
        if len(snippets) >= limit:
            break
    return snippets


def _data_completeness(company: dict) -> dict[str, bool]:
    return {
        "has_sector": bool(company.get("sector")),
        "has_location": bool(company.get("locatie")),
        "has_description": bool(company.get("ai_beschrijving") or company.get("business_trigger")),
        "has_vacancies": bool(company.get("vacature_titels") or company.get("vacatures")),
        "has_technologies": bool(company.get("tech_stack") or company.get("techstack")),
        "has_keywords": bool(company.get("keywords")),
    }


def _evidence_quality(completeness: dict[str, bool]) -> str:
    score = sum(1 for value in completeness.values() if value)
    if score >= 5:
        return "high"
    if score >= 3:
        return "medium"
    return "low"


def _extract_product_profile(product: str) -> dict:
    """Cheap deterministic product profile; keeps matching criteria explicit before the LLM call."""
    text = (product or "").lower()
    signals = {
        "target_industries": [],
        "required_technologies": [],
        "pain_points_solved": [],
        "ideal_customer_signals": [],
        "bad_fit_signals": [],
    }
    technology_terms = [
        "siemens", "s7-1500", "profinet", "scada", "schneider", "ecostruxure", "plc",
        "sinamics", "robot", "robotics", "agv", "machine vision", "computer vision", "cnc",
        "battery", "bms", "field service", "predictive maintenance", "preventive maintenance",
        "crm", "cybersecurity", "ot", "warehouse", "packaging",
    ]
    industry_terms = [
        "food", "beverage", "brouwerij", "agricultural", "landbouw", "metal", "heavy manufacturing",
        "ev", "electric vehicle", "industrial automation", "recruitment", "staffing", "warehouse",
    ]
    pain_terms = [
        "fault", "alerts", "quality inspection", "defect", "monitoring", "modernization", "retrofit",
        "diagnostics", "lead scoring", "quote", "follow-up", "audit", "workflow",
    ]
    for term in technology_terms:
        if term in text:
            signals["required_technologies"].append(term)
    for term in industry_terms:
        if term in text:
            signals["target_industries"].append(term)
    for term in pain_terms:
        if term in text:
            signals["pain_points_solved"].append(term)
    if signals["required_technologies"]:
        signals["ideal_customer_signals"].append("mentions or hires for matching technologies")
    if signals["target_industries"]:
        signals["ideal_customer_signals"].append("operates in the requested target industry")
    signals["bad_fit_signals"].extend([
        "only matches the location, not the product/service",
        "generic industrial wording without concrete technical evidence",
        "missing source evidence for the claimed capability",
    ])
    return {"product_summary": product, **signals}


def _compact_bedrijven_data(bedrijven_data):
    """Convert every company into the same compact evidence-first schema for fair ranking."""
    compacte_bedrijven = []

    for b in bedrijven_data[:30]:
        vacature_titels = _as_clean_list(b.get("vacature_titels") or b.get("vacatures"), 5)
        beroepen = _as_clean_list(b.get("beroepen"), 5)
        tech_stack = _as_clean_list(b.get("tech_stack") or b.get("techstack"), 8)
        machine_park = _as_clean_list(b.get("machine_park") or b.get("machinepark"), 8)
        keywords = _as_clean_list(b.get("keywords"), 10)
        vacature_samenvattingen = _as_clean_list(b.get("vacature_samenvattingen"), 4)
        completeness = _data_completeness({**b, "vacature_titels": vacature_titels, "tech_stack": tech_stack, "keywords": keywords})

        compacte_bedrijven.append({
            "id": b.get("id"),
            "company_name": b.get("naam") or b.get("bedrijfsnaam") or "",
            "sector": b.get("sector") or "Onbekend",
            "location": b.get("locatie") or "",
            "description": (b.get("ai_beschrijving") or "")[:320],
            "vacancy_titles": vacature_titels,
            "roles": beroepen,
            "vacancy_summaries": vacature_samenvattingen,
            "required_skills_or_technologies": tech_stack,
            "machines_or_tools": machine_park,
            "business_triggers": _as_clean_list(b.get("business_trigger"), 2),
            "keywords": keywords,
            "evidence_snippets": _extract_evidence_snippets({**b, "vacature_titels": vacature_titels}, 6),
            "data_completeness": completeness,
            "evidence_quality": _evidence_quality(completeness),
            "source_reliability": {
                "sector": "backend/vdab_or_enrichment" if b.get("sector") else "missing",
                "technologies": "backend/enrichment" if tech_stack else "missing",
                "business_triggers": "backend/enrichment" if b.get("business_trigger") else "missing",
                "vacancies": "backend/vdab" if vacature_titels else "missing",
            },
        })

    return compacte_bedrijven


def _normalize_ranked_results(result):
    """Normalize LLM output and keep ranking deterministic and schema-compatible."""
    if not isinstance(result, list):
        return result
    normalized = []
    seen_ids: set[str] = set()
    for item in result:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id") or item.get("bedrijf_id")
        if raw_id is None or str(raw_id) in seen_ids:
            continue
        seen_ids.add(str(raw_id))
        dimensions = item.get("score_dimensions") or {}
        try:
            score = float(item.get("score", item.get("final_score", 0)))
        except (TypeError, ValueError):
            score = 0.0
        score = max(0, min(10, score))
        item["id"] = raw_id
        item["bedrijf_id"] = raw_id
        item["score"] = score
        item.setdefault("score_dimensions", dimensions)
        item.setdefault("data_confidence", dimensions.get("data_confidence") if isinstance(dimensions, dict) else None)
        item.setdefault("evidence", item.get("evidence_snippets", []))
        normalized.append(item)
    normalized.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return normalized[:10]


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
    """Genereer ranked company matches via Groq with structured evidence and score dimensions."""
    product_profile = _extract_product_profile(product)
    bedrijven_data = _compact_bedrijven_data(bedrijven_data)

    prompt = f"""
            JE BENT EEN KRITISCHE B2B MATCHING ENGINE.
            Beoordeel PRODUCT-MARKET FIT tussen een gestructureerd PRODUCTPROFIEL en een lijst gestructureerde BEDRIJFSPROFIELEN.

            BELANGRIJKSTE DOEL:
            Rank ALLEEN bedrijven waarvoor er concrete bron-evidence in het bedrijfsprofiel staat.
            Een bedrijf met meer tekst mag niet automatisch hoger scoren; bewijs moet relevant zijn voor het product.

            BESLISREGELS:
            1. Vergelijk het productprofiel expliciet met elk bedrijfsprofiel op technische fit, sectorfit, business need en datakwaliteit.
            2. Hoge scores vereisen concrete overlap in evidence_snippets, required_skills_or_technologies, machines_or_tools, roles, vacancy_titles of business_triggers.
            3. Locatie mag nooit productrelevantie creeren. Locatie is hoogstens een extra contextfactor.
            4. Penaliseer lage evidence_quality en ontbrekende data_completeness. Gok ontbrekende capabilities niet bij.
            5. Als product specifieke termen noemt (bv. Siemens S7-1500, Profinet, SCADA, machine vision, field service), moeten die of directe synoniemen in de bedrijfsdata terugkomen voor een sterke match.
            6. Algemene woorden zoals "industrie", "onderhoud", "productie" of "techniek" zijn op zichzelf onvoldoende.
            7. Laat no-match bedrijven weg. Een lege lijst is toegestaan.
            8. Geen dubbele bedrijven. Gebruik uitsluitend verstrekte data.

            SCORE-RUBRIEK VOOR final score:
            - 9-10: directe, sterke, expliciete product/technologie/sector-overlap + goede evidence quality
            - 7-8: duidelijke fit met meerdere concrete signalen, maar niet perfect
            - 5-6: plausibele beperkte fit met minstens een concreet signaal
            - 3-4: zwakke/indirecte fit of lage dataconfidence
            - 0-2: geen zinvolle fit -> niet teruggeven

            SCORE-DIMENSIES:
            Geef aparte scores van 0-10 voor:
            - technical_fit: technologie, machines, rollen, vaardigheden
            - industry_fit: sector/use-case/context
            - business_need: trigger, vacaturedruk, pijnpunt of operationele behoefte
            - evidence_strength: hoe concreet en controleerbaar de snippets zijn
            - data_confidence: volledigheid/betrouwbaarheid van het bedrijfsprofiel
            De eindscore moet consistent zijn met deze dimensies en lager zijn bij lage evidence_strength of data_confidence.

            PRODUCTPROFIEL: {json.dumps(product_profile, ensure_ascii=False, separators=(',', ':'))}
            BEDRIJFSPROFIELEN: {json.dumps(bedrijven_data, ensure_ascii=False, separators=(',', ':'))}

            ANTWOORD UITSLUITEND IN GELDIGE JSON, ALS EEN LIJST VAN MAXIMAAL 10 OBJECTEN:
            [
                {{
                    "id": number,
                    "bedrijf_id": number,
                    "bedrijfsnaam": string,
                    "beschrijving": string,
                    "waarom": string,
                    "evidence": string[],
                    "score_dimensions": {{
                        "technical_fit": number,
                        "industry_fit": number,
                        "business_need": number,
                        "evidence_strength": number,
                        "data_confidence": number
                    }},
                    "score": number,
                    "contactgegevens": string,
                    "techstack": string[],
                    "locatie": string,
                    "sector": string
                }}
            ]

            EXTRA REGELS:
            - Sorteer aflopend op echte matchkwaliteit.
            - `waarom` moet kort, concreet en evidence-based zijn.
            - `evidence` bevat alleen korte snippets uit het bedrijfsprofiel.
            - `techstack` bevat alleen technologieen die in het bedrijfsprofiel staan.
            - Geen tekst voor of na de JSON. Geen Markdown code blocks.
            - Professioneel Nederlands.
            """
    
    try:
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0,
            max_tokens=2600,
        )
        content = chat_completion.choices[0].message.content or ""
    except Exception as e:
        print(f"[Groq] LLM call mislukt: {e}")
        return {"error": str(e), "raw": ""}

    try:
        match = re.search(r"(\[.*\]|\{.*\})", content, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            return _normalize_ranked_results(parsed)
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
