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
DEFAULT_GOLD_PATH = ROOT / "prospect_ranking_live_gold.jsonl"
DEFAULT_RESULTS_DIR = ROOT / "results"
DEFAULT_API_URL = os.getenv("EVAL_API_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"
SEARCH_ENDPOINT = "/companies/prospect"
EVAL_SSL_VERIFY = os.getenv("EVAL_SSL_VERIFY", "true").lower() not in {"0", "false", "no"}


@dataclass
class Label:
    bedrijf_id: int
    label: int
    reason: str = ""
    bedrijfsnaam: str = ""
    kbo_nummer: str = ""


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
                    bedrijfsnaam=str(item.get("bedrijfsnaam") or ""),
                    kbo_nummer=str(item.get("kbo_nummer") or ""),
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
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=EVAL_SSL_VERIFY) as client:
        response = await client.post(f"{api_url.rstrip('/')}{SEARCH_ENDPOINT}", json=payload)
        if response.status_code >= 400:
            preview = response.text[:500].replace("\n", " ")
            raise RuntimeError(
                f"Eval API returned HTTP {response.status_code} for {response.request.url}. "
                f"Response preview: {preview}"
            )
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


def recall_at_k(predicted_ids: list[int], gold_map: dict[int, int], k: int, min_relevance: int = 2) -> float:
    relevant_ids = {bedrijf_id for bedrijf_id, label in gold_map.items() if label >= min_relevance}
    if not relevant_ids:
        return 0.0
    hits = sum(1 for bedrijf_id in predicted_ids[:k] if bedrijf_id in relevant_ids)
    return hits / len(relevant_ids)


def mrr_at_k(predicted_ids: list[int], gold_map: dict[int, int], k: int, min_relevance: int = 2) -> float:
    for rank, bedrijf_id in enumerate(predicted_ids[:k], start=1):
        if gold_map.get(bedrijf_id, 0) >= min_relevance:
            return 1.0 / rank
    return 0.0


def pairwise_order_accuracy(predictions: list[dict[str, Any]], gold_map: dict[int, int]) -> float | None:
    """How often higher-labeled items receive higher/equal model scores among labeled predictions."""
    labeled = [item for item in predictions if item["bedrijf_id"] in gold_map]
    comparisons = 0
    correct = 0
    for i, left in enumerate(labeled):
        for right in labeled[i + 1:]:
            left_label = gold_map[left["bedrijf_id"]]
            right_label = gold_map[right["bedrijf_id"]]
            if left_label == right_label:
                continue
            comparisons += 1
            left_score = float(left.get("score") or 0)
            right_score = float(right.get("score") or 0)
            if (left_label > right_label and left_score >= right_score) or (right_label > left_label and right_score >= left_score):
                correct += 1
    if comparisons == 0:
        return None
    return correct / comparisons


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


def score_diagnostics(predictions: list[dict[str, Any]], k: int = 10) -> dict[str, Any]:
    """Detect flat scoring/ranking collapse, e.g. every result receiving score 1.0."""
    top = predictions[:k]
    if not top:
        return {
            "score_spread@k": 0.0,
            "unique_scores@k": 0,
            "top_score_tie_count@k": 0,
            "flat_score_warning": True,
        }

    scores = [round(float(item.get("score") or 0), 4) for item in top]
    top_score = max(scores)
    unique_scores = set(scores)
    top_ties = sum(1 for score in scores if score == top_score)
    return {
        "score_spread@k": round(max(scores) - min(scores), 4),
        "unique_scores@k": len(unique_scores),
        "top_score_tie_count@k": top_ties,
        "flat_score_warning": len(unique_scores) <= 2 or top_ties >= max(3, len(top) // 2),
    }


def evaluate_case(case: EvalCase, predictions: list[dict[str, Any]]) -> dict[str, Any]:
    gold_map = {label.bedrijf_id: label.label for label in case.labels}
    gold_meta = {label.bedrijf_id: label for label in case.labels}
    predicted_ids = [item["bedrijf_id"] for item in predictions]
    gold_ids = set(gold_map)

    top_k = case.top_k
    labeled_predictions = []
    id_name_mismatches = []
    for item in predictions[:top_k]:
        meta = gold_meta.get(item["bedrijf_id"])
        expected_name = meta.bedrijfsnaam if meta else ""
        if expected_name and expected_name.lower() != item["bedrijfsnaam"].lower():
            id_name_mismatches.append(
                {
                    "bedrijf_id": item["bedrijf_id"],
                    "expected_bedrijfsnaam": expected_name,
                    "predicted_bedrijfsnaam": item["bedrijfsnaam"],
                }
            )
        labeled_predictions.append(
            {
                "bedrijf_id": item["bedrijf_id"],
                "bedrijfsnaam": item["bedrijfsnaam"],
                "expected_bedrijfsnaam": expected_name or None,
                "score": item["score"],
                "gold_label": gold_map.get(item["bedrijf_id"], 0),
            }
        )

    missed_relevant = [
        {
            "bedrijf_id": label.bedrijf_id,
            "bedrijfsnaam": label.bedrijfsnaam or None,
            "kbo_nummer": label.kbo_nummer or None,
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
            "recall@5": round(recall_at_k(predicted_ids, gold_map, 5), 4),
            "recall@10": round(recall_at_k(predicted_ids, gold_map, 10), 4),
            "mrr@10": round(mrr_at_k(predicted_ids, gold_map, 10), 4),
            "pairwise_order_accuracy": (
                None if pairwise_order_accuracy(predictions, gold_map) is None
                else round(pairwise_order_accuracy(predictions, gold_map) or 0.0, 4)
            ),
            "returned_count": len(predictions),
            "labeled_coverage@10": round(
                sum(1 for bedrijf_id in predicted_ids[:10] if bedrijf_id in gold_ids) / max(1, min(10, len(predicted_ids))),
                4,
            ),
            **score_diagnostics(predictions, top_k),
        },
        "top_predictions": labeled_predictions,
        "missed_relevant": missed_relevant,
        "unlabeled_top_predictions": unlabeled_top_predictions,
        "id_name_mismatches": id_name_mismatches,
        "calibration": calibration_summary(predictions, gold_map),
    }


def aggregate_results(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        return {"cases": 0, "metrics": {}}

    metric_names = list(case_results[0]["metrics"].keys())
    averaged = {}
    for name in metric_names:
        values = [case["metrics"].get(name) for case in case_results]
        numeric_values = [float(value) for value in values if isinstance(value, (int, float))]
        averaged[name] = round(sum(numeric_values) / len(numeric_values), 4) if numeric_values else None

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
        try:
            print(f"Evaluating case {case.case_id}...")
            predictions = await fetch_predictions(api_url, case.product)
            case_results.append(evaluate_case(case, predictions))
        except Exception as e:
            print(f"WARNING: Skipping case {case.case_id} due to fetch error: {e}")

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
