from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
STARTER = ROOT / "prospect_ranking_live_labeling_starter.jsonl"
GOLD = ROOT / "prospect_ranking_live_gold.jsonl"


def convert_case(data: dict) -> dict:
    labels = []
    for item in data.get("candidate_businesses", []):
        label = item.get("label")
        if label is None or label == "":
            continue
        labels.append({
            "bedrijf_id": int(item["bedrijf_id"]),
            "bedrijfsnaam": item.get("bedrijfsnaam"),
            "kbo_nummer": item.get("kbo_nummer"),
            "label": int(label),
            "reason": str(item.get("reason", "")),
        })

    if not labels:
        raise ValueError(
            f"Case {data.get('case_id')} has no labels. Fill labels in {STARTER.name} before converting."
        )

    return {
        "case_id": data["case_id"],
        "product": data["product"],
        "top_k": int(data.get("top_k", 10)),
        "notes": data.get("notes", ""),
        "labels": labels,
    }


def main() -> None:
    converted = []
    with STARTER.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            converted.append(convert_case(json.loads(line)))

    with GOLD.open("w", encoding="utf-8") as fh:
        for case in converted:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Converted {len(converted)} labeled live cases to {GOLD}")


if __name__ == "__main__":
    main()
