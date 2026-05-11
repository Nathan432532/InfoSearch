import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent
OUT_JSONL = ROOT / "prospect_ranking_live_labeling_starter.jsonl"
OUT_MD = ROOT / "LIVE_LABELING_GUIDE.md"
DEFAULT_API_URL = os.getenv("EVAL_API_URL") or os.getenv("BACKEND_URL") or "https://infosearch.duckdns.org"

PRODUCTS = [
    "Predictive maintenance software for Siemens S7-1500 production lines with automatic fault alerts via Profinet.",
    "Machine vision quality inspection system for automated packaging lines.",
    "Condition monitoring platform for autonomous agricultural robots and battery-management systems.",
    "SCADA modernization toolkit for Schneider Electric based food production sites.",
    "Recruitment CRM for industrial service engineers with field-operations workflow automation.",
    "Energy monitoring platform for high-power drive systems in heavy manufacturing.",
    "Industrial cybersecurity audit service for PLC, SCADA, and OT networks.",
    "Warehouse robotics software for autonomous guided vehicles and fleet orchestration.",
    "Preventive maintenance SaaS for food and beverage production equipment.",
    "AI lead scoring for B2B technical recruitment and industrial staffing.",
    "Retrofit package for legacy Siemens and Schneider PLC environments.",
    "Remote diagnostics platform for field service teams maintaining industrial machines.",
    "Computer vision defect detection for metal forming and CNC production lines.",
    "Battery analytics software for electric vehicle component manufacturing plants.",
    "Sales CRM for industrial automation integrators with quote and follow-up workflows.",
]

SYNONYMS = {
    "siemens": ["s7", "s7-1500", "sinamics", "plc"],
    "schneider": ["ecostruxure", "modicon", "plc"],
    "scada": ["hmi", "wonderware", "intouch", "supervisory"],
    "plc": ["s7", "s7-1500", "codesys", "automation", "automatisatie"],
    "maintenance": ["onderhoud", "storing", "storingen", "preventive", "predictive"],
    "vision": ["camera", "inspectie", "inspection", "defect", "computer vision"],
    "packaging": ["verpakking", "afvul", "afvullijn", "food", "voeding"],
    "food": ["voeding", "beverage", "brouwerij", "brewery", "horeca"],
    "robot": ["robotica", "robotics", "autonome", "autonomous", "agv"],
    "robots": ["robotica", "robotics", "autonome", "autonomous", "agv"],
    "warehouse": ["magazijn", "logistiek", "logistics", "intralogistics", "agv"],
    "field": ["buitendienst", "service engineer", "field service"],
    "service": ["buitendienst", "service engineer", "field service"],
    "recruitment": ["staffing", "hiring", "hr", "vacature", "rekrutering"],
    "staffing": ["recruitment", "hiring", "hr", "vacature"],
    "drives": ["drive", "sinamics", "frequentieregelaar", "power"],
    "metal": ["metaal", "cnc", "wals", "staal", "machining"],
    "cnc": ["bewerkingscentra", "machining", "metal", "metaal"],
    "battery": ["batterij", "bms", "ev", "electric vehicle"],
    "cybersecurity": ["security", "ot", "network", "netwerk"],
    "crm": ["sales", "lead", "follow-up", "workflow", "quote"],
}

STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "een", "het", "de", "van", "voor", "met",
    "software", "platform", "system", "service", "services", "toolkit", "package", "automatic", "automated",
}


def normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        value = " ".join(str(x) for x in value)
    text = unicodedata.normalize("NFKD", str(value).lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def tokens(value: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9][a-z0-9\-\+\.]{1,}", normalize(value))
        if token not in STOPWORDS and len(token) > 1
    }


def product_terms(product: str) -> set[str]:
    out = tokens(product)
    for token in list(out):
        for synonym in SYNONYMS.get(token, []):
            out.update(tokens(synonym))
    return out


def company_text(company: dict[str, Any]) -> str:
    vacancies = company.get("vacatures") or []
    vacancy_parts = []
    for vacancy in vacancies:
        if isinstance(vacancy, dict):
            vacancy_parts.extend([
                vacancy.get("titel"),
                vacancy.get("beroep"),
                vacancy.get("omschrijving"),
                vacancy.get("vrije_vereiste"),
                vacancy.get("gemeente"),
            ])
        else:
            vacancy_parts.append(str(vacancy))
    return normalize(" ".join(str(part) for part in [
        company.get("bedrijfsnaam"),
        company.get("sector"),
        company.get("locatie"),
        *vacancy_parts,
    ] if part))


def score_candidate(product: str, company: dict[str, Any]) -> float:
    terms = product_terms(product)
    text = company_text(company)
    score = 0.0
    for term in terms:
        if term in text:
            score += 1.0
    # Prefer richer candidates for labeling because they are easier to judge.
    score += min(2.0, len(company.get("vacatures") or []) * 0.2)
    return score


def compact_company(company: dict[str, Any]) -> dict[str, Any]:
    vacancies = company.get("vacatures") or []
    compact_vacancies = []
    for vacancy in vacancies[:4]:
        if not isinstance(vacancy, dict):
            continue
        compact_vacancies.append({
            "titel": vacancy.get("titel"),
            "beroep": vacancy.get("beroep"),
            "gemeente": vacancy.get("gemeente"),
            "omschrijving": (vacancy.get("omschrijving") or "")[:260],
            "vrije_vereiste": (vacancy.get("vrije_vereiste") or "")[:220],
        })
    return {
        "bedrijf_id": company.get("id"),
        "bedrijfsnaam": company.get("bedrijfsnaam"),
        "kbo_nummer": company.get("kbo_nummer"),
        "locatie": company.get("locatie"),
        "contactgegevens": company.get("contactgegevens"),
        "vacatures": compact_vacancies,
        "label": None,
        "reason": "",
    }


def fetch_live_companies(api_url: str) -> list[dict[str, Any]]:
    with httpx.Client(timeout=180.0, follow_redirects=True) as client:
        response = client.post(f"{api_url.rstrip('/')}/companies/search", json={"query": "", "filters": {}})
        response.raise_for_status()
        data = response.json()
    companies = data.get("results", [])
    if not isinstance(companies, list) or not companies:
        raise RuntimeError("No companies returned from /companies/search")
    return companies


def build_cases(companies: list[dict[str, Any]], max_candidates: int) -> list[dict[str, Any]]:
    cases = []
    for idx, product in enumerate(PRODUCTS, start=1):
        ranked = sorted(companies, key=lambda c: (-score_candidate(product, c), normalize(c.get("bedrijfsnaam"))))
        selected = ranked[:max_candidates]
        cases.append({
            "case_id": f"live_{idx:03d}",
            "product": product,
            "top_k": 10,
            "notes": "Live Hetzner labeling set. Fill labels manually: 3=strong, 2=plausible, 1=weak, 0=no fit. Numeric IDs come from the live DB at build time; use name/KBO to sanity-check.",
            "candidate_businesses": [compact_company(company) for company in selected],
        })
    return cases


def write_outputs(cases: list[dict[str, Any]], api_url: str) -> None:
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")

    OUT_MD.write_text(f"""# Live labeling guide

This file was generated from the live backend:

```text
{api_url.rstrip('/')}
```

Label this file:

```text
prospect_ranking_live_labeling_starter.jsonl
```

For each `candidate_businesses` item, fill:

- `label`: 3, 2, 1, or 0
- `reason`: short evidence-based justification

Rubric:

- 3 = strong/direct fit
- 2 = plausible fit
- 1 = weak/indirect fit
- 0 = no fit

Rules:

- Judge only from the product description and candidate company/vacancy fields.
- Do not infer hidden capabilities.
- Use `bedrijfsnaam` and `kbo_nummer` to sanity-check the company; numeric IDs can differ between environments.
- After labeling, run:

```bash
python evals/_convert_live_labeling_to_gold.py
EVAL_GOLD_PATH=evals/prospect_ranking_live_gold.jsonl python evals/eval_ranking.py
```
""", encoding="utf-8")


def main() -> None:
    api_url = DEFAULT_API_URL.rstrip("/")
    max_candidates = int(os.getenv("LIVE_LABEL_CANDIDATES_PER_CASE", "12"))
    companies = fetch_live_companies(api_url)
    cases = build_cases(companies, max_candidates=max_candidates)
    write_outputs(cases, api_url)
    print(f"Fetched {len(companies)} live companies from {api_url}")
    print(f"Wrote {len(cases)} live labeling cases to {OUT_JSONL}")
    print(f"Candidates per case: {max_candidates}")


if __name__ == "__main__":
    main()
