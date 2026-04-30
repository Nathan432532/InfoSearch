import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

ROOT = Path(__file__).resolve().parent
DEFAULT_GOLD_PATH = ROOT / "prospect_ranking_gold.jsonl"
DEFAULT_RESULTS_DIR = ROOT / "results"
DEFAULT_API_URL = os.getenv("EVAL_API_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
SEARCH_ENDPOINT = "/companies/prospect"


@dataclass
class Label:
    bedrijf_id: int
    label: int
    reason: str = ""


@dataclass
class EvalCase:
    case_id: str
    product: str
    top_k: int
    notes: str
    labels: list[Label]


def load_cases(path: Path) -> list[EvalCase]:
    cases: list[EvalCase] = []
    with path.open("r", encoding="utf-8") as fh:
        for line_no, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            data = json.loads(line)
            labels = [
                Label(
                    bedrijf_id=int(item["bedrijf_id"]),
                    label=int(item["label"]),
                    reason=str(item.get("reason", "")),
                )
                for item in data.get("labels", [])
            ]
            if not labels:
                raise ValueError(f"Case on line {line_no} has no labels")
            cases.append(
                EvalCase(
                    case_id=str(data["case_id"]),
                    product=str(data["product"]),
                    top_k=int(data.get("top_k", 10)),
                    notes=str(data.get("notes", "")),
                    labels=labels,
                )
            )
    if not cases:
        raise ValueError(f"No eval cases found in {path}")
    return cases


def _normalize_prediction(item: dict[str, Any], fallback_rank: int) -> dict[str, Any]:
    raw_id = item.get("bedrijf_id", item.get("id"))
    if raw_id is None:
        raise ValueError(f"Prediction missing bedrijf_id/id: {item}")

    try:
        bedrijf_id = int(raw_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid bedrijf_id/id in prediction: {item}") from exc

    raw_score = item.get("score", 0)
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        score = 0.0

    return {
        "bedrijf_id": bedrijf_id,
        "bedrijfsnaam": str(item.get("bedrijfsnaam", item.get("naam", f"bedrijf_{bedrijf_id}"))),
        "score": score,
        "rank": fallback_rank,
        "raw": item,
    }


async def fetch_predictions(api_url: str, product: str, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    payload: dict[str, Any] = {"query": product}
    if filters:
        payload["filters"] = filters

    timeout = httpx.Timeout(180.0, connect=30.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        response = await client.post(f"{api_url.rstrip('/')}{SEARCH_ENDPOINT}", json=payload)
        response.raise_for_status()
        data = response.json()

    raw_results = data.get("results", [])
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(raw_results, start=1):
        normalized.append(_normalize_prediction(item, idx))
    return normalized


def dcg(relevances: list[int]) -> float:
    total = 0.0
    for idx, rel in enumerate(relevances, start=1):
        total += (2**rel - 1) / math.log2(idx + 1)
    return total


def ndcg_at_k(predicted_ids: list[int], gold_map: dict[int, int], k: int) -> float:
    actual = [gold_map.get(bedrijf_id, 0) for bedrijf_id in predicted_ids[:k]]
    ideal = sorted(gold_map.values(), reverse=True)[:k]
    ideal_dcg = dcg(ideal)
    if ideal_dcg == 0:
        return 0.0
    return dcg(actual) / ideal_dcg


def precision_at_k(predicted_ids: list[int], gold_map: dict[int, int], k: int, min_relevance: int = 2) -> float:
    if k <= 0:
        return 0.0
    top = predicted_ids[:k]
    hits = sum(1 for bedrijf_id in top if gold_map.get(bedrijf_id, 0) >= min_relevance)
    return hits / k


def calibration_summary(predictions: list[dict[str, Any]], gold_map: dict[int, int]) -> dict[str, Any]:
    buckets: dict[int, list[float]] = defaultdict(list)
    for item in predictions:
        label = gold_map.get(item["bedrijf_id"])
        if label is None:
            continue
        buckets[label].append(float(item["score"]))

    result: dict[str, Any] = {}
    for label in sorted(buckets):
        scores = buckets[label]
        result[str(label)] = {
            "count": len(scores),
            "avg_model_score": round(sum(scores) / len(scores), 4),
            "min_model_score": round(min(scores), 4),
            "max_model_score": round(max(scores), 4),
        }
    return result


def evaluate_case(case: EvalCase, predictions: list[dict[str, Any]]) -> dict[str, Any]:
    gold_map = {label.bedrijf_id: label.label for label in case.labels}
    predicted_ids = [item["bedrijf_id"] for item in predictions]
    gold_ids = set(gold_map)

    top_k = case.top_k
    labeled_predictions = []
    for item in predictions[:top_k]:
        labeled_predictions.append(
            {
                "bedrijf_id": item["bedrijf_id"],
                "bedrijfsnaam": item["bedrijfsnaam"],
                "score": item["score"],
                "gold_label": gold_map.get(item["bedrijf_id"], 0),
            }
        )

    missed_relevant = [
        {
            "bedrijf_id": label.bedrijf_id,
            "gold_label": label.label,
            "reason": label.reason,
        }
        for label in sorted(case.labels, key=lambda x: (-x.label, x.bedrijf_id))
        if label.label >= 2 and label.bedrijf_id not in predicted_ids[:top_k]
    ]

    unlabeled_top_predictions = [
        item for item in labeled_predictions if item["bedrijf_id"] not in gold_ids
    ]

    return {
        "case_id": case.case_id,
        "product": case.product,
        "top_k": top_k,
        "notes": case.notes,
        "metrics": {
            "ndcg@5": round(ndcg_at_k(predicted_ids, gold_map, 5), 4),
            "ndcg@10": round(ndcg_at_k(predicted_ids, gold_map, 10), 4),
            "precision@3": round(precision_at_k(predicted_ids, gold_map, 3), 4),
            "precision@5": round(precision_at_k(predicted_ids, gold_map, 5), 4),
        },
        "top_predictions": labeled_predictions,
        "missed_relevant": missed_relevant,
        "unlabeled_top_predictions": unlabeled_top_predictions,
        "calibration": calibration_summary(predictions, gold_map),
    }


def aggregate_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        return {"cases": 0, "metrics": {}}

    metric_names = list(case_results[0]["metrics"].keys())
    averaged = {}
    for name in metric_names:
        values = [float(case["metrics"][name]) for case in case_results]
        averaged[name] = round(sum(values) / len(values), 4)

    return {
        "cases": len(case_results),
        "metrics": averaged,
    }


def write_report(results_dir: Path, report: dict[str, Any]) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "latest_report.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


async def main() -> None:
    gold_path = Path(os.getenv("EVAL_GOLD_PATH", DEFAULT_GOLD_PATH))
    results_dir = Path(os.getenv("EVAL_RESULTS_DIR", DEFAULT_RESULTS_DIR))
    api_url = os.getenv("EVAL_API_URL", DEFAULT_API_URL)

    cases = load_cases(gold_path)
    case_results = []

    for case in cases:
        predictions = await fetch_predictions(api_url, case.product)
        case_results.append(evaluate_case(case, predictions))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "api_url": api_url.rstrip("/"),
        "endpoint": SEARCH_ENDPOINT,
        "gold_path": str(gold_path),
        "summary": aggregate_results(case_results),
        "cases": case_results,
    }

    out_path = write_report(results_dir, report)
    print(f"Wrote ranking eval report to {out_path}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
