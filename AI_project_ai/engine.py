from groq import Groq
from validator import valideer_llm_output
import json
import httpx
import re
import os

GROQ_API_KEY = os.getenv("GROQ_API_KEY") or ""
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY") or ""
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai/v1/chat/completions").rstrip("/")
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:8999").rstrip("/")
PROSPECT_RANKING_PROVIDER = os.getenv("PROSPECT_RANKING_PROVIDER", "groq").strip().lower()
PROSPECT_RANKING_MODEL = os.getenv("PROSPECT_RANKING_MODEL", "openai/gpt-oss-120b")
PROSPECT_RANKING_FALLBACK_MODELS = [
    name.strip()
    for name in os.getenv("PROSPECT_RANKING_FALLBACK_MODELS", "llama-3.3-70b-versatile").split(",")
    if name.strip()
]
model = PROSPECT_RANKING_MODEL  # Backwards-compatible alias for older code/imports.
# Deterministically pre-rank all fetched companies, then send a wider compact
# candidate set to the LLM in small batches. This keeps recall higher than 30
# while avoiding the oversized single 120-profile Groq request.
PROSPECT_LLM_CANDIDATE_LIMIT = int(os.getenv("PROSPECT_LLM_CANDIDATE_LIMIT", "50"))
PROSPECT_LLM_BATCH_SIZE = int(os.getenv("PROSPECT_LLM_BATCH_SIZE", "10"))
PROSPECT_MAX_OUTPUT_TOKENS = int(os.getenv("PROSPECT_MAX_OUTPUT_TOKENS", "900"))
PROSPECT_LLM_PROMPT_CHAR_LIMIT = int(os.getenv("PROSPECT_LLM_PROMPT_CHAR_LIMIT", "24000"))

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
            "contactgegevens": (b.get("contactgegevens") or "")[:220],
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


def _score_dimension_average(dimensions: dict) -> float | None:
    if not isinstance(dimensions, dict) or not dimensions:
        return None
    keys = ["technical_fit", "industry_fit", "business_need", "evidence_strength", "data_confidence"]
    values: list[float] = []
    for key in keys:
        try:
            values.append(float(dimensions[key]))
        except (KeyError, TypeError, ValueError):
            continue
    if not values:
        return None
    return sum(values) / len(values)


def _recalibrated_score(raw_score: float, item: dict, deterministic_score: float, original_rank: int) -> float:
    """Turn coarse LLM scores into a granular 0-10 ranking score.

    Groq/Llama sometimes returns flat scores like 1.0 for every candidate. This function
    makes the final score depend mostly on evidence, dimensions and deterministic fit,
    with only a small stable rank tie-breaker.
    """
    dimensions = item.get("score_dimensions") or {}
    dimension_avg = _score_dimension_average(dimensions)
    evidence_count = len(_as_clean_list(item.get("evidence"), 5))
    evidence_bonus = min(0.5, evidence_count * 0.1)

    parts: list[tuple[float, float]] = []
    if deterministic_score > 0:
        parts.append((0.65, deterministic_score))
    if dimension_avg is not None:
        parts.append((0.25, dimension_avg))

    # Raw LLM score is useful when it is calibrated, but it should not dominate flat 1/2 scores.
    raw_weight = 0.10 if deterministic_score > 0 or dimension_avg is not None else 1.0
    parts.append((raw_weight, raw_score))

    total_weight = sum(weight for weight, _ in parts) or 1.0
    score = sum(weight * value for weight, value in parts) / total_weight
    score += evidence_bonus

    # Stable tiny tie-breaker: keeps equal evidence scores deterministic without overpowering relevance.
    score += max(0.0, 0.2 - (original_rank * 0.01))
    return round(max(0.0, min(10.0, score)), 2)


def _spread_tied_scores(rows: list[dict]) -> None:
    """Ensure exactly equal final scores become rare while preserving sorted order."""
    seen: dict[float, int] = {}
    for row in rows:
        score = round(float(row.get("score") or 0), 2)
        count = seen.get(score, 0)
        if count:
            score = max(0.0, round(score - (count * 0.03), 2))
            row["score"] = score
        seen[round(float(row.get("score") or 0), 2)] = count + 1


def _is_size_or_rate_limit_error(error: Exception) -> bool:
    """Providers report oversized requests/rate limits with 413/429-style errors.

    Retrying the same oversized prompt against fallback models only burns quota, so
    these errors should short-circuit into deterministic fallback instead.
    """
    text = str(error).lower()
    return any(
        marker in text
        for marker in [
            "request too large",
            "tokens per minute",
            "tokens per day",
            "rate_limit_exceeded",
            "error code: 413",
            "error code: 429",
            "status_code: 429",
            "http 429",
            "rate limit",
        ]
    )


def _deterministic_report_from_candidates(candidates: list[dict], fill_to: int = 10) -> list[dict]:
    """Return a usable top-N when the LLM is unavailable or quota-limited."""
    rows = []
    for candidate in sorted(
        candidates,
        key=lambda row: float(row.get("deterministic_score") or 0),
        reverse=True,
    )[:fill_to]:
        det_score = float(candidate.get("deterministic_score") or 0)
        rows.append({
            "id": candidate.get("id"),
            "bedrijf_id": candidate.get("id"),
            "bedrijfsnaam": candidate.get("company_name", ""),
            "beschrijving": candidate.get("description", ""),
            "waarom": "Deterministische ranking gebruikt omdat de LLM-call niet binnen de Groq-limieten paste: "
                      + "; ".join(candidate.get("deterministic_reasons", [])[:3]),
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
            "score": round(det_score + min(0.4, len(candidate.get("evidence_snippets", [])) * 0.05), 2),
            "contactgegevens": candidate.get("contactgegevens", ""),
            "techstack": candidate.get("required_skills_or_technologies", []),
            "locatie": candidate.get("location", ""),
            "sector": candidate.get("sector", ""),
            "llm_fallback_reason": "groq_size_or_rate_limit",
        })
    _spread_tied_scores(rows)
    rows.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    return rows


def _normalize_ranked_results(result, deterministic_by_id: dict[str, dict] | None = None, fill_to: int = 10):
    """Normalize LLM output and keep ranking deterministic and schema-compatible."""
    if not isinstance(result, list):
        return result
    normalized = []
    seen_ids: set[str] = set()
    for original_rank, item in enumerate(result, start=1):
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
            item.setdefault("deterministic_score", deterministic_score)
            item.setdefault("deterministic_reasons", deterministic_meta.get("deterministic_reasons", []))
        item["id"] = raw_id
        item["bedrijf_id"] = raw_id
        item.setdefault("score_dimensions", dimensions)
        item.setdefault("data_confidence", dimensions.get("data_confidence") if isinstance(dimensions, dict) else None)
        item.setdefault("evidence", item.get("evidence_snippets", deterministic_meta.get("evidence_snippets", [])))
        techstack = _as_clean_list(
            item.get("techstack") or item.get("tech_stack") or item.get("technologies")
            or deterministic_meta.get("required_skills_or_technologies"),
            8,
        )
        item["techstack"] = techstack
        item["tech_stack"] = techstack
        machinepark = _as_clean_list(item.get("machinepark") or item.get("machine_park") or deterministic_meta.get("machines_or_tools"), 8)
        if machinepark:
            item["machinepark"] = machinepark
            item["machine_park"] = machinepark
        if not item.get("sector"):
            item["sector"] = deterministic_meta.get("sector", "")
        if not item.get("locatie"):
            item["locatie"] = deterministic_meta.get("location", "")
        if not item.get("contactgegevens"):
            item["contactgegevens"] = deterministic_meta.get("contactgegevens", "")
        item["score"] = _recalibrated_score(score, item, deterministic_score, original_rank)
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
                "score": round(det_score + min(0.4, len(candidate.get("evidence_snippets", [])) * 0.05), 2),
                "contactgegevens": "",
                "techstack": candidate.get("required_skills_or_technologies", []),
                "locatie": candidate.get("location", ""),
                "sector": candidate.get("sector", ""),
            })
            seen_ids.add(raw_id)
            if len(normalized) >= fill_to:
                break

    normalized.sort(key=lambda row: float(row.get("score") or 0), reverse=True)
    _spread_tied_scores(normalized)
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

def _llm_candidate_view(candidate: dict) -> dict:
    """Trim candidate fields sent to the ranking LLM; keep only ranking evidence."""
    return {
        "id": candidate.get("id"),
        "company_name": candidate.get("company_name", ""),
        "sector": candidate.get("sector", ""),
        "location": candidate.get("location", ""),
        "description": (candidate.get("description") or "")[:180],
        "vacancy_titles": _as_clean_list(candidate.get("vacancy_titles"), 3),
        "roles": _as_clean_list(candidate.get("roles"), 3),
        "technologies": _as_clean_list(candidate.get("required_skills_or_technologies"), 5),
        "machines_or_tools": _as_clean_list(candidate.get("machines_or_tools"), 4),
        "business_triggers": _as_clean_list(candidate.get("business_triggers"), 1),
        "keywords": _as_clean_list(candidate.get("keywords"), 5),
        "evidence_snippets": _as_clean_list(candidate.get("evidence_snippets"), 4),
        "evidence_quality": candidate.get("evidence_quality"),
        "deterministic_score": candidate.get("deterministic_score", 0),
        "deterministic_reasons": _as_clean_list(candidate.get("deterministic_reasons"), 3),
    }


def _build_prospect_prompt(product_profile: dict, candidates: list[dict]) -> str:
    """Build a compact prompt. Instructions are intentionally short to save tokens."""
    llm_candidates = [_llm_candidate_view(candidate) for candidate in candidates]
    return f"""
JE BENT EEN KRITISCHE B2B MATCHING ENGINE.
Rank de bedrijven op product-market fit voor het PRODUCTPROFIEL.
Gebruik alleen concrete evidence uit het bedrijfsprofiel; gok ontbrekende capabilities niet bij.
Locatie mag nooit productrelevantie creëren. Penaliseer lage evidence_quality.
Geef maximaal 10 bedrijven terug, gesorteerd op matchkwaliteit. Gebruik decimale scores 0-10.

SCORES:
9-10 directe expliciete technologie/sector-overlap; 7-8 duidelijke fit; 5-6 beperkte concrete fit; 3-4 zwak/indirect; 0-2 niet teruggeven.
Geef score_dimensions voor technical_fit, industry_fit, business_need, evidence_strength, data_confidence.
Gebruik deterministic_score alleen als extra signaal/tiebreaker, niet blind.

PRODUCTPROFIEL:{json.dumps(product_profile, ensure_ascii=False, separators=(',', ':'))}
BEDRIJFSPROFIELEN:{json.dumps(llm_candidates, ensure_ascii=False, separators=(',', ':'))}

ANTWOORD UITSLUITEND GELDIGE JSON: een lijst van maximaal 10 objecten met deze velden:
id, bedrijf_id, bedrijfsnaam, beschrijving, waarom, evidence, score_dimensions,
deterministic_score, deterministic_reasons, score, contactgegevens, techstack, locatie, sector.
Geen markdown, geen tekst buiten JSON. Professioneel Nederlands.
""".strip()


async def _call_groq_prospect_llm(prompt: str, model_name: str) -> str:
    if client is None:
        raise RuntimeError("GROQ_API_KEY ontbreekt; kan Groq ranking model niet aanroepen")
    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name,
        temperature=0,
        max_tokens=PROSPECT_MAX_OUTPUT_TOKENS,
    )
    return chat_completion.choices[0].message.content or ""


async def _call_mistral_prospect_llm(prompt: str, model_name: str) -> str:
    if not MISTRAL_API_KEY:
        raise RuntimeError("MISTRAL_API_KEY ontbreekt; kan Mistral ranking model niet aanroepen")

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": PROSPECT_MAX_OUTPUT_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    timeout = httpx.Timeout(120.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout) as http_client:
        response = await http_client.post(MISTRAL_API_URL, headers=headers, json=payload)
    if response.status_code >= 400:
        raise RuntimeError(f"Mistral HTTP {response.status_code}: {response.text[:500]}")
    data = response.json()
    return (((data.get("choices") or [{}])[0].get("message") or {}).get("content") or "")


def _ranking_provider_for_model(model_name: str) -> str:
    if PROSPECT_RANKING_PROVIDER in {"mistral", "groq"}:
        return PROSPECT_RANKING_PROVIDER
    if model_name.lower().startswith("mistral"):
        return "mistral"
    return "groq"


async def _call_prospect_llm(prompt: str, model_candidates: list[str]) -> str | None:
    """Call the configured ranking provider with fallback models."""
    for model_name in model_candidates:
        provider = _ranking_provider_for_model(model_name)
        try:
            print(f"[{provider.title()}] Prospect ranking model: {model_name}")
            if provider == "mistral":
                return await _call_mistral_prospect_llm(prompt, model_name)
            return await _call_groq_prospect_llm(prompt, model_name)
        except Exception as e:
            print(f"[{provider.title()}] LLM call mislukt met model {model_name}: {e}")
            if _is_size_or_rate_limit_error(e):
                print(f"[{provider.title()}] Size/rate limit geraakt; geen fallback retry met dezelfde payload.")
                return None
    return None


def _parse_prospect_json(content: str):
    match = re.search(r"(\[.*\]|\{.*\})", content or "", re.DOTALL)
    if not match:
        raise ValueError("Geen JSON gevonden")
    return json.loads(match.group(0))


async def genereer_prospectie_rapport(product, bedrijven_data):
    """Genereer ranked company matches via the configured LLM provider."""
    product_profile = _extract_product_profile(product)
    bedrijven_data = _compact_bedrijven_data(bedrijven_data, product_profile)
    deterministic_by_id = {str(b.get("id")): b for b in bedrijven_data if b.get("id") is not None}

    if not bedrijven_data:
        return []

    model_candidates = [PROSPECT_RANKING_MODEL, *PROSPECT_RANKING_FALLBACK_MODELS]
    batch_size = max(1, PROSPECT_LLM_BATCH_SIZE)
    llm_rows: list[dict] = []
    seen_ids: set[str] = set()

    # Use compact candidates for recall, but rank them in small batches
    # so each LLM request stays within provider token/rate limits.
    for batch_index, start in enumerate(range(0, len(bedrijven_data), batch_size), start=1):
        prompt_candidates = bedrijven_data[start:start + batch_size]
        prompt = _build_prospect_prompt(product_profile, prompt_candidates)
        while len(prompt) > PROSPECT_LLM_PROMPT_CHAR_LIMIT and len(prompt_candidates) > 3:
            prompt_candidates = prompt_candidates[:-1]
            prompt = _build_prospect_prompt(product_profile, prompt_candidates)

        print(
            f"[{PROSPECT_RANKING_PROVIDER.title()}] Prospect ranking payload: "
            f"batch={batch_index}, candidates={len(prompt_candidates)}, chars={len(prompt)}, "
            f"max_tokens={PROSPECT_MAX_OUTPUT_TOKENS}"
        )

        content = await _call_prospect_llm(prompt, model_candidates)
        if content is None:
            continue

        try:
            parsed = _parse_prospect_json(content)
            batch_meta = {str(b.get("id")): b for b in prompt_candidates if b.get("id") is not None}
            normalized = _normalize_ranked_results(parsed, batch_meta, fill_to=min(10, len(prompt_candidates)))
            if isinstance(normalized, list):
                for row in normalized:
                    raw_id = row.get("id") or row.get("bedrijf_id")
                    if raw_id is None or str(raw_id) in seen_ids:
                        continue
                    seen_ids.add(str(raw_id))
                    llm_rows.append(row)
        except Exception as e:
            print(f"[{PROSPECT_RANKING_PROVIDER.title()}] JSON parsing/normalisatie mislukt voor batch {batch_index}: {e}")

    if llm_rows:
        # Merge all batch winners into one global top-10, then fill any gaps with
        # deterministic candidates from the full top-50 compact set.
        return _normalize_ranked_results(llm_rows, deterministic_by_id, fill_to=10)

    print(f"[{PROSPECT_RANKING_PROVIDER.title()}] Geen bruikbare LLM-batches; gebruik deterministic fallback over alle kandidaten.")
    return _deterministic_report_from_candidates(bedrijven_data, fill_to=10)


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
