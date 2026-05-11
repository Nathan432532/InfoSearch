# Live labeling guide

This file was generated from the live backend:

```text
https://infosearch.duckdns.org
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
