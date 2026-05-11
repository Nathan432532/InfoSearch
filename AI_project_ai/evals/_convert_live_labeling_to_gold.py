from pathlib import Path
import json
from typing import Any

ROOT = Path(__file__).resolve().parent
STARTER = ROOT / "prospect_ranking_live_labeling_starter.jsonl"
COMPACT_LABELS = ROOT / "prospect_ranking_live_labels.json"
GOLD = ROOT / "prospect_ranking_live_gold.jsonl"

PRODUCT_BY_CASE_ID = {
    "live_001": "Predictive maintenance software for Siemens S7-1500 production lines with automatic fault alerts via Profinet.",
    "live_002": "Machine vision quality inspection system for automated packaging lines.",
    "live_003": "Condition monitoring platform for autonomous agricultural robots and battery-management systems.",
    "live_004": "SCADA modernization toolkit for Schneider Electric based food production sites.",
    "live_005": "Recruitment CRM for industrial service engineers with field-operations workflow automation.",
    "live_006": "Energy monitoring platform for high-power drive systems in heavy manufacturing.",
    "live_007": "Industrial cybersecurity audit service for PLC, SCADA, and OT networks.",
    "live_008": "Warehouse robotics software for autonomous guided vehicles and fleet orchestration.",
    "live_009": "Preventive maintenance SaaS for food and beverage production equipment.",
    "live_010": "AI lead scoring for B2B technical recruitment and industrial staffing.",
    "live_011": "Retrofit package for legacy Siemens and Schneider PLC environments.",
    "live_012": "Remote diagnostics platform for field service teams maintaining industrial machines.",
    "live_013": "Computer vision defect detection for metal forming and CNC production lines.",
    "live_014": "Battery analytics software for electric vehicle component manufacturing plants.",
    "live_015": "Sales CRM for industrial automation integrators with quote and follow-up workflows.",
}


def _read_cases(path: Path) -> list[dict[str, Any]]:
    """Read either JSON array or JSONL cases."""
    text = path.read_text(encoding="utf-8-sig").strip()
    if not text:
        raise ValueError(f"{path} is empty")

    if text.startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON array of cases")
        return data

    cases = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            cases.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on {path.name}:{line_no}") from exc
    return cases


def _starter_case_index() -> dict[str, dict[str, Any]]:
    if not STARTER.exists():
        return {}
    return {case.get("case_id"): case for case in _read_cases(STARTER) if case.get("case_id")}


def convert_case(data: dict[str, Any], starter_index: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    # Supports two input shapes:
    # 1. live starter: { candidate_businesses: [{bedrijf_id, label, reason, ...}] }
    # 2. compact labels: { labels: [{bedrijf_id, label, reason, ...}] }
    starter_index = starter_index or {}
    source_items = data.get("labels") or data.get("candidate_businesses") or []
    starter_case = starter_index.get(data.get("case_id"), {})
    starter_candidates = {
        int(item["bedrijf_id"]): item
        for item in starter_case.get("candidate_businesses", [])
        if item.get("bedrijf_id") is not None
    }

    labels = []
    for item in source_items:
        label = item.get("label")
        if label is None or label == "":
            continue
        bedrijf_id = int(item["bedrijf_id"])
        starter_item = starter_candidates.get(bedrijf_id, {})
        labels.append({
            "bedrijf_id": bedrijf_id,
            "bedrijfsnaam": item.get("bedrijfsnaam") or starter_item.get("bedrijfsnaam"),
            "kbo_nummer": item.get("kbo_nummer") or starter_item.get("kbo_nummer"),
            "label": int(label),
            "reason": str(item.get("reason", "")),
        })

    if not labels:
        raise ValueError(
            f"Case {data.get('case_id')} has no labels. Fill {COMPACT_LABELS.name} or {STARTER.name} before converting."
        )

    return {
        "case_id": data["case_id"],
        "product": data.get("product") or starter_case.get("product") or PRODUCT_BY_CASE_ID.get(data["case_id"], ""),
        "top_k": int(data.get("top_k", starter_case.get("top_k", 10))),
        "notes": data.get("notes") or starter_case.get("notes", "Live compact labels converted to gold."),
        "labels": labels,
    }


def main() -> None:
    input_path = COMPACT_LABELS if COMPACT_LABELS.exists() else STARTER
    starter_index = _starter_case_index()
    converted = [convert_case(case, starter_index) for case in _read_cases(input_path)]
    empty_products = [case["case_id"] for case in converted if not case.get("product")]
    if empty_products:
        raise ValueError(f"Converted cases missing product text: {empty_products}")

    with GOLD.open("w", encoding="utf-8") as fh:
        for case in converted:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Read labels from {input_path}")
    print(f"Converted {len(converted)} labeled live cases to {GOLD}")


if __name__ == "__main__":
    main()
