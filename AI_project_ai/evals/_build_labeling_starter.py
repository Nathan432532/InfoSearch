from pathlib import Path
import ast
import json
import re

ROOT = Path(r"C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project")
AI_README = ROOT / "AI_project_ai" / "README.md"
ENGINE = ROOT / "AI_project_ai" / "engine.py"
OUT_JSONL = ROOT / "AI_project_ai" / "evals" / "prospect_ranking_labeling_starter.jsonl"
OUT_MD = ROOT / "AI_project_ai" / "evals" / "LABELING_GUIDE.md"


def extract_sample_companies() -> list[dict]:
    text = AI_README.read_text(encoding="utf-8", errors="ignore")
    marker = "let vacatures = ["
    start = text.find(marker)
    if start == -1:
        return []
    start = text.find("[", start)
    end = text.find("let prospecten =", start)
    if end == -1:
        return []
    raw = text[start:end].strip()
    raw = raw.rstrip().rstrip(';')
    raw = re.sub(r"//.*", "", raw)
    raw = raw.replace("true", "True").replace("false", "False").replace("null", "None")
    data = ast.literal_eval(raw)
    companies = []
    for idx, item in enumerate(data, start=1):
        companies.append(
            {
                "bedrijf_id": idx,
                "bedrijfsnaam": item.get("bedrijf"),
                "sector": item.get("sector"),
                "locatie": ", ".join(
                    p for p in [
                        item.get("locatie", {}).get("stad"),
                        item.get("locatie", {}).get("provincie"),
                    ] if p
                ),
                "business_trigger": item.get("business_trigger"),
                "tech_signals": item.get("tech_stack", []),
                "vacature_titel": item.get("vacature_details", {}).get("titel"),
                "keywords": item.get("keywords", []),
            }
        )
    return companies


def extract_product_prompts() -> list[str]:
    text = ENGINE.read_text(encoding="utf-8", errors="ignore")
    prompts = []
    for match in re.findall(r'product\"\s*:\s*\"([^\"]+)\"', text):
        prompts.append(match.strip())
    for match in re.findall(r'PRODUCT:\s*(.+)', text):
        cleaned = match.strip().strip('"')
        if cleaned and "{" not in cleaned:
            prompts.append(cleaned)
    prompts.extend([
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
    ])
    deduped = []
    seen = set()
    for p in prompts:
        p = p.strip()
        if not p or p in seen:
            continue
        seen.add(p)
        deduped.append(p)
    return deduped[:15]


def build_cases(companies: list[dict], products: list[str]) -> list[dict]:
    cases = []
    for idx, product in enumerate(products, start=1):
        cases.append(
            {
                "case_id": f"starter_{idx:03d}",
                "product": product,
                "top_k": 10,
                "notes": "Real starter set built from repo sample company data. Fill in labels manually: 3=strong fit, 2=plausible, 1=weak, 0=no fit.",
                "candidate_businesses": [
                    {
                        "bedrijf_id": c["bedrijf_id"],
                        "bedrijfsnaam": c["bedrijfsnaam"],
                        "sector": c["sector"],
                        "locatie": c["locatie"],
                        "vacature_titel": c["vacature_titel"],
                        "business_trigger": c["business_trigger"],
                        "tech_signals": c["tech_signals"],
                        "keywords": c["keywords"],
                        "label": None,
                        "reason": ""
                    }
                    for c in companies
                ],
            }
        )
    return cases


def write_outputs(cases: list[dict]) -> None:
    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with OUT_JSONL.open("w", encoding="utf-8") as fh:
        for case in cases:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")

    guide = """# Labeling guide

Use `prospect_ranking_labeling_starter.jsonl` as the manual review set.

For each `candidate_businesses` item, fill:
- `label`: 3, 2, 1, or 0
- `reason`: short justification

Rubric:
- 3 = strong fit
- 2 = plausible fit
- 1 = weak fit
- 0 = no fit

Rule: judge only from evidence in the product description and business fields.
Do not infer hidden capabilities.

Suggested workflow:
- start with 5 easy cases
- then label the remaining 10 templates
- keep your reasons short and concrete
- prefer harsh negatives over generous guessing
"""
    OUT_MD.write_text(guide, encoding="utf-8")


def main() -> None:
    companies = extract_sample_companies()
    products = extract_product_prompts()
    cases = build_cases(companies, products)
    write_outputs(cases)
    print(f"Wrote {len(cases)} labeling cases to {OUT_JSONL}")


if __name__ == "__main__":
    main()
