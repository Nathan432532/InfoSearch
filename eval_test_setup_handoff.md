# Eval/Test Setup Handoff

Date: 2026-05-20

## Context

Groq hit its on-demand token/rate limits during prospect-ranking eval/testing, so further live testing should wait until quota resets or billing/tier changes.

The main issue seen in Docker logs was not that the ranking model was bad, but that the request payload became too large after increasing the LLM candidate limit.

Observed Groq errors:

- `openai/gpt-oss-120b`
  - TPM limit: 8,000
  - requested: ~12,700–12,900 tokens
  - error: `413 Request too large`

- `llama-3.3-70b-versatile`
  - TPM limit: 12,000
  - requested: ~13,600–13,700 tokens
  - errors: `413 Request too large` and `429 Too Many Requests`
  - daily quota also got close to/exceeded: 100,000 TPD

## What caused the collapse

From `changes.md`, the intended improved flow was:

1. Fetch a broad backend pool, default `PROSPECT_CANDIDATE_FETCH_LIMIT=200`.
2. Deterministically score all fetched companies.
3. Send only the best compact company profiles to the LLM.
4. Return/fill a top 10.

The earlier working setup effectively sent around **30 compact profiles** to the AI.

The problematic change was:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=120
```

That made the prompt too large for Groq's on-demand TPM limits.

## Current code changes made during this handoff

Files touched:

- `AI_project_ai/engine.py`
- `frontend_project/AI_project_frontend/src/pages/ResultPages/ResultPageCompany/CompanyResultPage.tsx`

### `engine.py`

Current experimental setup:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=50
PROSPECT_LLM_BATCH_SIZE=10
PROSPECT_MAX_OUTPUT_TOKENS=900
PROSPECT_LLM_PROMPT_CHAR_LIMIT=24000
```

Behavior:

- Deterministically pre-ranks all fetched companies.
- Keeps top 50 compact candidates.
- Sends candidates to Groq in batches of 10.
- Merges batch winners into a final top 10.
- Avoids retrying fallback models when Groq returns size/rate-limit errors (`413`, `429`, `rate_limit_exceeded`, TPM/TPD errors).
- Falls back to deterministic ranking if Groq cannot return usable batch results.
- Normalizes output so both `techstack` and `tech_stack` are present.
- Also normalizes `machinepark`/`machine_park` where available.

### Frontend tech stack fix

`CompanyResultPage.tsx` now accepts these aliases from API responses:

- tech stack: `techstack`, `tech_stack`, `technologies`
- machine park: `machinepark`, `machine_park`
- business trigger: `businessTrigger`, `business_trigger`

This should fix cases where tech stack exists in backend/AI output but does not show in the frontend because of field-name mismatch.

## Recommendation

Do **not** assume the 50-batched setup is better yet. It should be evaluated.

Recommended comparison:

### Config A — safer production baseline

Use one AI call over 30 compact profiles:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=30
# no batching, or set code/config so batch size >= 30 if batching remains enabled
PROSPECT_LLM_BATCH_SIZE=30
PROSPECT_MAX_OUTPUT_TOKENS=900
```

Pros:

- Closest to the previously successful eval behavior.
- One model call sees all candidates together.
- Lower quota usage.
- Simpler final ranking.

Cons:

- Lower recall than 50 if relevant companies are ranked positions 31–50 deterministically.

### Config B — experimental higher recall

Use 50 candidates in batches of 10:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=50
PROSPECT_LLM_BATCH_SIZE=10
PROSPECT_MAX_OUTPUT_TOKENS=900
```

Pros:

- Better chance relevant companies outside top 30 are seen by the LLM.
- Each request should stay under Groq token limits.

Cons:

- Up to 5 Groq calls per search/eval case.
- Higher quota usage.
- The model does not compare all 50 companies in one shared context.
- Final merge relies more on deterministic score calibration.

## What to test later

After Groq quota resets, run evals for both configs and compare:

- `nDCG@10`
- `recall@10`
- `precision@5`
- `returned_count`
- `score_spread@k`
- `unique_scores@k`
- `flat_score_warning`
- Groq 413/429 errors in logs
- total calls/quota usage

Eval command used previously:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

If running locally against the local backend/API, update `EVAL_API_URL` accordingly.

## What logs should show

For 50-batched mode, expected AI-service logs:

```text
[Groq] Prospect ranking payload: batch=1, candidates=10, chars=..., max_tokens=900
[Groq] Prospect ranking payload: batch=2, candidates=10, chars=..., max_tokens=900
...
```

For 30-single/batch-size-30 mode, expected logs should show either one batch/call with around 30 candidates, or one single ranking payload depending on code/config.

## Verification already performed

These passed after the current changes:

```powershell
python -m py_compile engine.py api.py
npm run build
```

`npm run build` completed successfully, with only a normal Vite chunk-size warning.

## Suggested next step with assistant

When quota resets, ask:

> Run the eval comparison from `eval_test_setup_handoff.md` and tell me whether 30-single or 50-batched performs better.

Then compare metrics and decide which config should be production default.
