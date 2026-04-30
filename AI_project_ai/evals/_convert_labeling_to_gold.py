from pathlib import Path
import json

ROOT = Path(r"C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project")
STARTER = ROOT / "AI_project_ai" / "evals" / "prospect_ranking_labeling_starter.jsonl"
GOLD = ROOT / "AI_project_ai" / "evals" / "prospect_ranking_gold.jsonl"


def convert_case(data: dict) -> dict:
    labels = []
    for item in data.get("candidate_businesses", []):
        label = item.get("label")
        if label is None or label == "":
            continue
        labels.append(
            {
                "bedrijf_id": int(item["bedrijf_id"]),
                "label": int(label),
                "reason": str(item.get("reason", "")),
            }
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
        for line in fh:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            converted.append(convert_case(data))

    with GOLD.open("w", encoding="utf-8") as fh:
        for case in converted:
            fh.write(json.dumps(case, ensure_ascii=False) + "\n")

    print(f"Converted {len(converted)} cases to {GOLD}")


if __name__ == "__main__":
    main()
