# Labeling guide

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
