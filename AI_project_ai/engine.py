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
PROSPECT_LLM_CANDIDATE_LIMIT = int(os.getenv("PROSPECT_LLM_CANDIDATE_LIMIT", "120"))

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




def _contains_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def _tokenize_for_matching(text: str) -> set[str]:
    """Small language-agnostic tokenizer for fallback overlap scoring."""
    stopwords = {
        "the", "and", "for", "with", "from", "that", "this", "een", "het", "de", "van", "voor", "met",
        "naar", "bij", "aan", "in", "op", "en", "of", "to", "a", "an", "software", "platform", "service",
        "system", "toolkit", "package", "saas",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9+.#/-]{2,}", (text or "").lower())
        if token not in stopwords
    }


def _candidate_text(company: dict) -> str:
    fields = [
        company.get("company_name"),
        company.get("sector"),
        company.get("description"),
        *company.get("vacancy_titles", []),
        *company.get("roles", []),
        *company.get("vacancy_summaries", []),
        *company.get("required_skills_or_technologies", []),
        *company.get("machines_or_tools", []),
        *company.get("business_triggers", []),
        *company.get("keywords", []),
        *company.get("evidence_snippets", []),
    ]
    return " ".join(str(value or "") for value in fields).lower()


def _deterministic_match(company: dict, product_profile: dict) -> dict:
    """Evidence-first lexical scorer used to pre-rank candidates and break LLM score ties."""
    product = str(product_profile.get("product_summary") or "")
    product_text = product.lower()
    company_text = _candidate_text(company)
    score = 0.0
    reasons: list[str] = []

    for term in product_profile.get("required_technologies", []):
        if term and term in company_text:
            score += 2.2
            reasons.append(f"technologie-overlap: {term}")
    for term in product_profile.get("target_industries", []):
        if term and term in company_text:
            score += 1.4
            reasons.append(f"sector-overlap: {term}")
    for term in product_profile.get("pain_points_solved", []):
        if term and term in company_text:
            score += 1.2
            reasons.append(f"pijnpunt-overlap: {term}")

    synonym_groups = [
        (["predictive maintenance", "preventive maintenance", "condition monitoring", "remote diagnostics"], ["onderhoud", "maintenance", "preventief", "curatief", "storing", "diagnose", "technieker", "mecanicien"]),
        (["siemens", "s7", "s7-1500", "profinet", "plc", "scada", "schneider", "retrofit", "modernization"], ["siemens", "s7", "s7-1500", "profinet", "plc", "scada", "schneider", "automatisatie", "sturing", "elektricien"]),
        (["machine vision", "computer vision", "quality inspection", "defect detection"], ["inspectie", "inspection", "kwaliteit", "quality", "defect", "cnc", "laser", "operator", "controle"]),
        (["warehouse", "agv", "autonomous guided", "fleet orchestration", "robotics"], ["magazijn", "warehouse", "logistiek", "logistics", "heftruck", "transport", "robot", "automatisatie"]),
        (["recruitment", "staffing", "crm", "field-operations", "lead scoring"], ["vacature", "aanwerving", "rekrutering", "personeel", "technieker", "service", "planning", "sales", "account"]),
        (["field service", "industrial machines", "service engineers"], ["buitendienst", "field", "service", "installatie", "montage", "technieker", "onderhoud", "machine"]),
        (["food", "beverage", "production equipment", "packaging"], ["voeding", "food", "drank", "beverage", "productie", "verpakking", "packaging", "afvul"]),
        (["metal", "heavy manufacturing", "cnc", "production lines"], ["metaal", "metal", "staal", "steel", "cnc", "productie", "lijn", "wals", "industrieel"]),
        (["battery", "bms", "electric vehicle", "ev"], ["batterij", "battery", "bms", "elektrisch", "ev", "automotive", "voertuig"]),
        (["cybersecurity", "audit", "ot networks"], ["security", "cyber", "netwerk", "network", "ot", "plc", "scada", "audit"]),
    ]
    for product_terms, company_terms in synonym_groups:
        if _contains_any(product_text, product_terms) and _contains_any(company_text, company_terms):
            score += 1.5
            reasons.append("domein-synoniemen matchen")

    overlap = sorted(_tokenize_for_matching(product) & _tokenize_for_matching(company_text))
    if overlap:
        score += min(2.0, len(overlap) * 0.35)
        reasons.append("term-overlap: " + ", ".join(overlap[:5]))

    completeness = company.get("data_completeness") or {}
    completeness_count = sum(1 for value in completeness.values() if value)
    if company.get("evidence_quality") == "high":
        score += 0.8
    elif company.get("evidence_quality") == "medium":
        score += 0.4
    else:
        score -= 0.6
    score += min(0.8, completeness_count * 0.12)

    weak_manual_terms = ["poets", "schoonmaak", "huishoud", "tuin", "aardbei", "horeca", "kelner", "chauffeur"]
    if score < 2.5 and _contains_any(company_text, weak_manual_terms):
        score -= 1.0
        reasons.append("penalty: weinig bewijs en vooral manueel/servicewerk")

    return {
        "deterministic_score": round(max(0.0, min(10.0, score)), 2),
        "deterministic_reasons": reasons[:5],
    }

def _compact_bedrijven_data(bedrijven_data, product_profile: dict | None = None):
    """Convert every company into the same compact evidence-first schema for fair ranking."""
    compacte_bedrijven = []

    for b in bedrijven_data:
        vacature_titels = _as_clean_list(b.get("vacature_titels") or b.get("vacatures"), 5)
        beroepen = _as_clean_list(b.get("beroepen"), 5)
        tech_stack = _as_clean_list(b.get("tech_stack") or b.get("techstack"), 8)
        machine_park = _as_clean_list(b.get("machine_park") or b.get("machinepark"), 8)
        keywords = _as_clean_list(b.get("keywords"), 10)
        vacature_samenvattingen = _as_clean_list(b.get("vacature_samenvattingen"), 4)
        completeness = _data_completeness({**b, "vacature_titels": vacature_titels, "tech_stack": tech_stack, "keywords": keywords})

        compact = {
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
        }
        if product_profile:
            compact.update(_deterministic_match(compact, product_profile))
        compacte_bedrijven.append(compact)

    if product_profile:
        compacte_bedrijven.sort(key=lambda row: row.get("deterministic_score", 0), reverse=True)
        # Feed the LLM a broad but evidence-ranked candidate set. The previous 30-profile
        # cap hid relevant companies before ranking/eval; keep this configurable for cost.
        return compacte_bedrijven[:PROSPECT_LLM_CANDIDATE_LIMIT]

    return compacte_bedrijven


def _normalize_ranked_results(result, deterministic_by_id: dict[str, dict] | None = None, fill_to: int = 10):
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
        # If the model returns flat/poorly calibrated scores, blend in deterministic evidence.
        deterministic_meta = (deterministic_by_id or {}).get(str(raw_id), {})
        try:
            deterministic_score = float(item.get("deterministic_score", deterministic_meta.get("deterministic_score", 0)) or 0)
        except (TypeError, ValueError):
            deterministic_score = 0.0
        if deterministic_score > 0:
            score = round((0.65 * score) + (0.35 * deterministic_score), 2)
            item.setdefault("deterministic_score", deterministic_score)
            item.setdefault("deterministic_reasons", deterministic_meta.get("deterministic_reasons", []))
        item["id"] = raw_id
        item["bedrijf_id"] = raw_id
        item["score"] = score
        item.setdefault("score_dimensions", dimensions)
        item.setdefault("data_confidence", dimensions.get("data_confidence") if isinstance(dimensions, dict) else None)
        item.setdefault("evidence", item.get("evidence_snippets", []))
        normalized.append(item)
    # If the LLM is overly strict and returns only a few prospects, fill the ranking
    # with deterministic evidence-ranked candidates. Evals and users both benefit from
    # a complete top-10 with calibrated low/medium scores instead of hidden candidates.
    if deterministic_by_id and len(normalized) < fill_to:
        for raw_id, candidate in sorted(
            deterministic_by_id.items(),
            key=lambda pair: float(pair[1].get("deterministic_score") or 0),
            reverse=True,
        ):
            if raw_id in seen_ids:
                continue
            det_score = float(candidate.get("deterministic_score") or 0)
            normalized.append({
                "id": candidate.get("id"),
                "bedrijf_id": candidate.get("id"),
                "bedrijfsnaam": candidate.get("company_name", ""),
                "beschrijving": candidate.get("description", ""),
                "waarom": "Deterministische fallback op basis van beschikbare evidence: " + "; ".join(candidate.get("deterministic_reasons", [])[:3]),
                "evidence": candidate.get("evidence_snippets", [])[:3],
                "score_dimensions": {
                    "technical_fit": det_score,
                    "industry_fit": det_score,
                    "business_need": min(det_score, 6.0),
                    "evidence_strength": det_score,
                    "data_confidence": 8 if candidate.get("evidence_quality") == "high" else 5 if candidate.get("evidence_quality") == "medium" else 2,
                },
                "deterministic_score": det_score,
                "deterministic_reasons": candidate.get("deterministic_reasons", []),
                "score": round(det_score, 2),
                "contactgegevens": "",
                "techstack": candidate.get("required_skills_or_technologies", []),
                "locatie": candidate.get("location", ""),
                "sector": candidate.get("sector", ""),
            })
            seen_ids.add(raw_id)
            if len(normalized) >= fill_to:
                break

    normalized.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return normalized[:fill_to]


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
    bedrijven_data = _compact_bedrijven_data(bedrijven_data, product_profile)
    deterministic_by_id = {str(b.get("id")): b for b in bedrijven_data if b.get("id") is not None}

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
            7. Geef bij voorkeur een volledige top 10 terug. Als er minder dan 10 sterke matches zijn,
               vul aan met zwakkere kandidaten met lage score en duidelijke onzekerheid.
               Laat alleen bedrijven weg die echt 0 productrelevantie hebben.
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

            LET OP OVER deterministic_score:
            - deterministic_score is een evidence-based pre-ranking van 0-10.
            - Gebruik die score als extra signaal, maar corrigeer hem als jouw inhoudelijke analyse dat vraagt.
            - Bij gelijke LLM-inschatting moet het bedrijf met hogere deterministic_score hoger staan.

            ANTWOORD UITSLUITEND IN GELDIGE JSON, ALS EEN LIJST VAN MAXIMAAL 10 OBJECTEN
            EN MIK OP 10 OBJECTEN ALS ER GENOEG BEDRIJFSPROFIELEN ZIJN:
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
                    "deterministic_score": number,
                    "deterministic_reasons": string[],
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
            return _normalize_ranked_results(parsed, deterministic_by_id, fill_to=10)
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
