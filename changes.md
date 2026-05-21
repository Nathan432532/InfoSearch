# InfoSearch Combined Changes

This file consolidates the project change notes that were previously split across:

- `documentation/PROJECT_CHANGES_2026-05-08.md`
- `changes.md`

Package/vendor changelogs under `node_modules` are intentionally excluded.

---

# Earlier project/application changes

# InfoSearch Project Changes and Model Evaluation Notes

Date: 2026-05-08

This document records the latest project changes, the relevant recent commits, and notes for the model evaluation work.

---

## Documentation practice for future sessions

For this InfoSearch project, future requested changes should also be documented across sessions. When work continues in a later session, add a short entry to the project documentation describing:

- what the user asked to change
- which files or components were changed
- why the change was needed
- how the change was verified
- any remaining caveats or follow-up work

This keeps the project history understandable even when work happens over multiple assistant sessions.

---

## Current uncommitted changes

The latest working-tree changes affect 5 files:

- `frontend_project/AI_project_frontend/src/pages/SavedResultsPage/SavedResultsPage.tsx`
- `frontend_project/AI_project_frontend/src/pages/SearchPages/SearchPageCompany/SearchPageCompany.tsx`
- `frontend_project/AI_project_frontend/src/pages/ResultPages/ResultPageCompany/CompanyResultPage.tsx`
- `frontend_project/AI_project_frontend/src/pages/ResultPages/ResultPageJob/ResultPageJob.tsx`
- `backend_project/backend/app/routers/vdab.py`

### 1. Saved page GSAP warning fix

**Problem:**  
Opening the saved results page could show this console warning:

```text
GSAP target not found
```

**Cause:**  
The saved page always called `gsap.fromTo(...)` after loading, even when the saved item list was empty. GSAP received an empty target list.

**Change:**  
Added a guard before running the animation:

- collect `.savedItem` elements first
- if the list is empty, return early
- only call GSAP when there are actual items to animate

**File changed:**

- `SavedResultsPage.tsx`

---

### 2. Company filters are now passed through correctly

**Problem:**  
The filters added when describing a product were not fully used when viewing company results.

**Cause:**  
The `bedrijfsgrootte` filter existed in the company search form, but it was not added to the result URL and therefore was not sent to the backend result request.

**Changes:**

- `bedrijfsgrootte` is now added to the company result URL.
- `CompanyResultPage.tsx` now reads `bedrijfsgrootte` from the URL.
- The company result request now sends these filters to the backend:
  - `locatie`
  - `sector`
  - `bedrijfsgrootte`
  - `regio`
- Saved company searches now also include `bedrijfsgrootte` in their saved filter metadata.

**Files changed:**

- `SearchPageCompany.tsx`
- `CompanyResultPage.tsx`

---

### 3. Backend company prospect filters are now applied before ranking

**Problem:**  
The backend company prospect endpoint could return results that ignored active filters, especially when the AI wrapper path was used.

**Cause:**  
The AI wrapper currently fetches its own broad candidate list and does not accept the frontend filters. This meant filtered searches could still show unfiltered AI-generated results.

**Changes:**

- Backend now extracts and applies:
  - `locatie`
  - `sector`
  - `bedrijfsgrootte`
  - `regio`
- If filters are active, the backend uses the filtered deterministic ranking path instead of the AI wrapper path.
- This prevents unfiltered AI output from overriding filtered backend candidates.
- If no filters are active and the AI service is configured, the existing AI path can still be used.

**Important caveat:**  
The database does not currently contain real employee-count data, so `bedrijfsgrootte` is temporarily approximated using the number of linked vacancies:

- `klein`: fewer than 5 linked vacancies
- `middel`: 5 to 20 linked vacancies
- `groot`: more than 20 linked vacancies

This should eventually be replaced with real company-size data from KBO, CRM, enrichment data, or another source.

**File changed:**

- `backend_project/backend/app/routers/vdab.py`

---

### 4. Job sector filter is now used

**Problem:**  
The job search page passed a sector filter in the URL, but the job result request did not send it to the backend, and the backend vacancy search did not apply it.

**Changes:**

- `ResultPageJob.tsx` now includes `sector` in the filters sent to `/search`.
- The backend vacancy search now applies the sector filter against the `beroep` column using `LIKE`.
- Saved job searches now include the sector filter metadata.

**Files changed:**

- `ResultPageJob.tsx`
- `backend_project/backend/app/routers/vdab.py`

---

## Verification performed

### Frontend build

Command:

```bash
npm run build
```

Result:

- Passed successfully.
- Vite reported only the existing large-chunk warning.

### Backend syntax check

Command:

```bash
python -m py_compile backend/app/routers/vdab.py
```

Result:

- Passed successfully.

### Frontend lint

Command:

```bash
npm run lint
```

Result:

- Still fails, but because of pre-existing lint issues unrelated to the new changes:
  - `src/components/Header/Header.tsx`
    - `react-hooks/set-state-in-effect`
  - `src/context/AuthContext.tsx`
    - `react-refresh/only-export-components`
  - `src/pages/ResultPages/ResultPageJob/ResultPageJob.tsx`
    - unused eslint-disable warning

---

## Recent commit history reviewed

Recent commits on `main`:

```text
c3e0326 updated readme + basic evaluation_model
9544d1c More functional data for model
954e609 eval
1659ebb Frontend session token fix
92d94f2 Configuraton hetzner/vercel api connectivity
c30fd21 Merge branch 'main' of github.com:Nathan432532/AI_project
89ed207 working model on hetzner, couple bugs
078a80a Added readme
4fde54a first hetzer shit
c114a15 Added cron data sync
2b48b57 Added authenticaiton and rolgebaseerde toegang
90c24b4 Feat: Added authentication/rolgebaseerd
a3d21db Feat: saved searches added
a341023 Fixed frontend/handmatige pull
99f7149 saved results fix - frontend upgrade - qwen pull added
a8f9cde second hash error backend - fix
23812c9 backend path error - fix
1d92949 frontend enhancement - login page
c946a26 model change - prospecting error fix
97f7bff first integrated app
```

Most relevant recent commits:

### `c3e0326` — updated readme + basic evaluation_model

Changed:

- `README.md`
- `backend_project/backend/app/routers/vdab.py`
- `AI_project_ai/evals/results/latest_report.json`

Summary:

- Added or updated README documentation.
- Added basic evaluation-model reporting.
- Updated backend prospecting/search logic.

### `9544d1c` — More functional data for model

Changed:

- `AI_project_ai/api.py`
- `AI_project_ai/engine.py`
- `AI_project_ai/evals/results/latest_report.json`
- `backend_project/backend/app/routers/vdab.py`

Summary:

- Improved the data being sent into the model/evaluation flow.
- Adjusted AI API/backend integration.
- Updated evaluation report output.

### `954e609` — eval

Changed:

- `AI_project_ai/engine.py`
- `AI_project_ai/evals/LABELING_GUIDE.md`
- `AI_project_ai/evals/_build_labeling_starter.py`
- `AI_project_ai/evals/_convert_labeling_to_gold.py`
- `AI_project_ai/evals/eval_ranking.py`
- `AI_project_ai/evals/prospect_ranking_gold.jsonl`
- `AI_project_ai/evals/prospect_ranking_labeling_starter.jsonl`
- `AI_project_ai/evals/results/latest_report.json`

Summary:

- Added the evaluation framework for prospect-ranking quality.
- Added starter/gold labeling data.
- Added ranking evaluation script and latest report output.

---

## Model evaluation notes

The model evaluation showed that the model was still quite simple. It could use generalization, but it was not yet well-suited for strict one-to-one matching between a product description and every possible company.

In the first evaluation, the model tended to choose a small number of obvious top picks, usually around 3 to 5 businesses, and gave little useful differentiation for the rest of the candidate companies. This made the ranking less useful when the goal was to evaluate all companies consistently, not just identify a few standout matches.

The issue was not only the model itself. The input data also needed to change. The model needs richer and more structured company data to reason about matches properly. For example, useful input should include:

- company description
- sector
- location
- vacancy titles
- vacancy summaries
- required skills or technologies
- business triggers
- machine park or technical stack where available
- keywords extracted from vacancy/company data

Because of this, the prompt was changed to push the model toward broader, more consistent ranking behavior. Instead of only selecting a few obvious winners, the prompt should encourage the model to compare all candidate companies against the product description and explain the match quality more evenly.

Main evaluation conclusion:

> The model can identify broad relevance, but the current setup is not strong enough for reliable one-to-one matching. Better input data, stronger candidate features, and a more explicit ranking prompt are needed before the results can be trusted as a precise matching system.

Recommended next improvements:

1. Improve input data quality before sending candidates to the model.
2. Keep candidate payloads structured and comparable.
3. Add explicit ranking criteria to the prompt.
4. Penalize companies with too little evidence instead of guessing.
5. Evaluate more than only the top few matches.
6. Track whether each company has enough data for a fair match decision.
7. Replace the temporary company-size heuristic with real employee/company-size data.

---

## Recommended input data fixes for better model matching

The most important improvement is to make the input data more structured and comparable before it reaches the model. The model should not receive a loose mix of company text, vacancy text, and inferred enrichment without clear labels. It needs consistent evidence for every candidate.

### 1. Use the same structured candidate format for every company

Every company should be converted into the same schema before matching. Example:

```json
{
  "company_name": "...",
  "sector": "...",
  "location": "...",
  "description": "...",
  "vacancy_titles": [],
  "vacancy_summaries": [],
  "required_skills": [],
  "technologies": [],
  "machines_or_tools": [],
  "business_triggers": [],
  "keywords": [],
  "evidence_quality": "high | medium | low"
}
```

This makes the candidates easier to compare. Without a consistent format, the model may over-score companies that simply have more text, not necessarily better fit.

### 2. Add evidence snippets, not only extracted labels

If a company has tags like `PLC`, `SCADA`, or `robotics`, the model should also receive short proof snippets from the source data.

Example:

```json
{
  "technologies": ["PLC", "SCADA"],
  "evidence": [
    "Vacature vraagt ervaring met PLC-sturingen",
    "Omschrijving vermeldt automatisatie van productielijnen"
  ]
}
```

This helps the model explain why a company is a match instead of guessing from isolated keywords.

### 3. Separate real source data from AI-inferred data

The input should show where each field came from:

```json
{
  "source": {
    "sector": "vdab",
    "technologies": "ai_extracted",
    "business_triggers": "ai_inferred"
  }
}
```

This prevents inferred enrichment from being treated as equally reliable as real VDAB/company data.

### 4. Add missing-data and data-completeness fields

If a company has too little information, the model should know that explicitly.

Example:

```json
{
  "data_completeness": {
    "has_description": false,
    "has_vacancies": true,
    "has_technologies": false,
    "has_contact_data": true
  }
}
```

The prompt can then tell the model to lower confidence when evidence is missing instead of filling in the gaps.

### 5. Normalize skills and technology names

The same technology can appear in many forms:

- `PLC`
- `PLC programming`
- `Siemens PLC`
- `S7`
- `S7-1500`

These should be normalized into canonical tags before matching:

```json
{
  "technologies": ["PLC", "Siemens S7", "SCADA"]
}
```

This will make matching more reliable and reduce duplicate or missed signals.

### 6. Structure the product description too

The product input should also be transformed before matching. Instead of only sending a raw product description, extract a product profile first:

```json
{
  "product_summary": "...",
  "target_industries": [],
  "required_technologies": [],
  "pain_points_solved": [],
  "ideal_customer_signals": [],
  "bad_fit_signals": []
}
```

Then the model can compare structured product requirements against structured company evidence.

### 7. Add real company-size and maturity data

Useful prospecting fields include:

- employee count
- number of open vacancies
- company age
- growth signals
- hiring intensity
- number of locations
- recent job posting frequency

This would improve the `bedrijfsgrootte` filter. The current vacancy-count approximation is only a temporary workaround.

### 8. Deduplicate and summarize vacancy data per company

If one company has many similar vacancies, the model should not receive all raw vacancies separately. Instead, group them into a company-level summary.

Example:

```json
{
  "vacancy_summary": "Company is hiring multiple automation engineers for PLC, maintenance, and production-line projects.",
  "top_roles": ["Automation Engineer", "Maintenance Engineer"],
  "repeated_skills": ["PLC", "SCADA", "preventive maintenance"]
}
```

This prevents companies with many repeated vacancies from dominating simply because they have more text.

### 9. Score separate match dimensions

Instead of asking the model for only one final score, ask for multiple dimensions:

```json
{
  "technical_fit": 8,
  "industry_fit": 7,
  "location_fit": 6,
  "business_need": 8,
  "data_confidence": 5,
  "final_score": 7
}
```

This makes the reasoning easier to evaluate and helps detect weak matches with low evidence.

### 10. Build a small gold dataset for evaluation

Create a manually labeled set of product/company pairs:

```json
{
  "product_id": "automation_software",
  "company_id": 123,
  "expected_match": "strong | medium | weak | no_match",
  "reason": "Uses PLC/SCADA and hires automation engineers"
}
```

A first useful target would be 30 to 50 labeled pairs. The evaluation should check whether strong matches are ranked above weak or no-match companies, not just whether the model finds a few good top picks.

### Strongest recommendation

Structure both sides before matching:

1. Convert the product description into a structured product profile.
2. Convert every company into a structured company profile.
3. Match the product profile against each company profile using clear scoring dimensions.
4. Penalize low-confidence or low-evidence candidates.

This will likely improve matching quality more than only switching to a larger model.

---

## 2026-05-08 follow-up: scheduled pull, deduplication, and product-first relevance

Requested change:

- Keep the existing cron setup and scheduled data-pull workflow unchanged.
- Improve the current pull behavior so the scheduled run collects more data, deduplicates businesses, and avoids saving product-irrelevant/location-only matches.

Implemented changes:

### Scheduled pull maximization

- Kept the existing scheduler structure in `backend/app/main.py`.
- Increased the default scheduled pull amount from `100` to `500` using `AUTO_SYNC_AMOUNT`.
- Added the sync settings to `backend/.env.example`:
  - `AUTO_SYNC_ENABLED=true`
  - `AUTO_SYNC_TIME=02:30`
  - `AUTO_SYNC_TZ=Europe/Brussels`
  - `AUTO_SYNC_AMOUNT=500`
- The existing VDAB service already paginates in pages of up to 50 results, so the larger amount lets the existing scheduled run continue pagination instead of stopping after the first small batch.

### Business deduplication

Added normalization and deduplication helpers for businesses in `backend/app/routers/vdab.py`.

Deduplication now uses normalized versions of:

- business name
- website/domain
- phone number
- email address
- address
- VAT/KBO/company number when available

Normalization includes:

- lowercase names
- accent stripping
- punctuation removal
- extra-space cleanup
- ignoring common company suffixes such as `bv`, `bvba`, `nv`, `gmbh`, `ltd`, `srl`
- phone digit normalization
- domain normalization by removing protocol, `www`, paths, and trailing slashes

When an existing business is found during the VDAB pull:

- no second `tblBedrijven` row is created
- useful missing fields are merged into the existing row
- the pull report counts it as merged/skipped instead of newly saved

Saved result deduplication was also improved:

- company saved results below `4/10` are rejected instead of saved
- duplicate saved businesses for the same user are merged instead of inserted again
- merged saved results keep the most complete payload and source list where available

### Product-first relevance scoring

Fixed the issue where location-only matches could appear as partial matches.

The product/service query is now treated as the primary matching factor. Location filters only constrain the candidate set and do not create relevance by themselves.

For example, if a user searches for a specific product/service with an Antwerpen filter, a business should not be treated as relevant just because it is located in Antwerpen. The company still needs evidence that it is connected to the requested product, service, supplier category, or closely related equipment/industry.

If a candidate only matches the location but has no concrete product/service evidence, its score is capped as low-quality and it is not returned/saved as a useful prospect.

### Query expansion and synonyms

Added generic product synonym expansion for matching terms around broad categories already used by the system, such as:

- automation and robotics
- PLC/SCADA/industrial control
- food/packaging/horeca equipment
- maintenance and field service
- recruitment/staffing signals

This lets the search try relevant variants before giving up, without hardcoding one specific example product into the system.

### End-of-run reporting

The VDAB pull now returns a `run_report` containing:

- number of new businesses saved
- number of duplicates merged or skipped
- number of low-quality results rejected
- best search terms / pull source note
- whether pagination maximization was used

The prospect endpoint also returns a `run_report` containing:

- number of businesses returned
- number of low-quality candidates rejected
- best product terms used
- whether query expansion was used
- whether location was used only as a constraint

Verification:

- `python -m py_compile backend/app/routers/vdab.py backend/app/main.py backend/app/services/vdab_service.py` passed.
- `npm run build` in the frontend passed, with only the existing large bundle-size warning.

Caveats:

- Real source URL history for `tblBedrijven` is still limited by the current schema. Saved result payloads can merge source lists, and business rows merge available website/contact fields, but a dedicated business-source history table would be cleaner later.
- The scheduler time itself was not changed.
- The VDAB source is still the main data source; this does not add a new external source crawler.

---

## Suggested commit message for the current uncommitted work

```text
Improve scheduled pull deduplication and product-first relevance
```

Possible longer description:

```text
- Increase default scheduled VDAB pull amount while keeping existing scheduler flow
- Deduplicate businesses using normalized name, contact, domain, address, and KBO/VAT signals
- Merge useful fields into existing business/saved-result records instead of duplicating
- Reject low-score location-only saved company results
- Add product-first scoring and generic query expansion
- Add run reports for pull/prospect result quality and query expansion
- Document the workflow and remaining caveats
```
---

## 2026-05-11 follow-up: structured model inputs and richer ranking eval

Requested change:

- Improve the prospect-matching model/evaluation after reviewing the project changes notes.

Implemented changes:

### Structured AI candidate payloads

Updated `AI_project_ai/engine.py` so company candidates are no longer sent to the LLM as a loose/flat mix of fields. Each company is now compacted into a consistent evidence-first schema containing:

- company name, sector, location, description
- vacancy titles, roles, vacancy summaries
- required skills/technologies
- machines/tools
- business triggers and keywords
- short evidence snippets
- data completeness flags
- evidence quality (`high`, `medium`, `low`)
- source reliability hints for sector, vacancies, enrichment, and triggers

This should make company-to-company comparison fairer and reduce over-scoring companies that merely have more text.

### Structured product profile before matching

Added a deterministic product-profile extraction step before the LLM prompt. The product profile now separates:

- product summary
- target industries
- required technologies
- pain points solved
- ideal customer signals
- bad-fit signals

The LLM prompt now compares this product profile against structured company profiles instead of comparing raw product text against raw company text.

### Evidence-based scoring prompt

Reworked the prospect-generation prompt to require separate scoring dimensions:

- `technical_fit`
- `industry_fit`
- `business_need`
- `evidence_strength`
- `data_confidence`

The final score must now be consistent with those dimensions, and low evidence/data confidence should pull the score down. The output also includes explicit evidence snippets, making later debugging and evaluation easier.

### Output normalization

Added post-processing for LLM results to:

- deduplicate company IDs
- normalize `id`/`bedrijf_id`
- clamp scores to `0-10`
- sort results deterministically by score
- keep the existing API-compatible fields while adding richer evaluation fields

### Richer evaluation metrics

Updated `AI_project_ai/evals/eval_ranking.py` with additional metrics beyond nDCG and precision:

- `recall@5`
- `recall@10`
- `mrr@10`
- `pairwise_order_accuracy`
- `returned_count`
- `labeled_coverage@10`

This makes the eval better at showing whether the model finds all relevant companies, ranks the first relevant result early, preserves ordering among labeled candidates, and returns too many/too few results.

Verification:

- `python -m py_compile AI_project_ai\engine.py AI_project_ai\api.py AI_project_ai\evals\eval_ranking.py` passed.
- A small local `evaluate_case(...)` smoke test passed and produced the new metric fields.

Caveats / follow-up:

- The live eval report was not regenerated yet because that requires the backend/API endpoint to be running with current data.
- The gold dataset is still small and synthetic/starter-oriented; model quality will improve more once real labeled product/company pairs are added.
---

## 2026-05-11 status note: is the model/prompt better?

Short answer: yes, the model/prompt setup is better structurally, but the live ranking quality still needs to be proven by rerunning the eval against the active backend data.

Why it is better now:

- The LLM receives a consistent company schema instead of a loose mix of fields.
- Each company now includes evidence snippets, data-completeness flags, evidence quality, and source-reliability hints.
- The product is converted into a structured product profile before matching.
- The prompt now forces separate scoring dimensions for technical fit, industry fit, business need, evidence strength, and data confidence.
- The model is explicitly told to penalize weak/missing evidence instead of guessing.
- LLM output is normalized, deduplicated, score-clamped, and sorted before use.
- The eval now tracks recall, MRR, pairwise ordering, returned count, and labeled coverage, not only precision/nDCG.

Important caveat:

- This improves the matching design and should reduce bad high scores from vague/generic evidence, but it is not yet a measured quality improvement until `AI_project_ai/evals/eval_ranking.py` is rerun against the current API/backend and the new `latest_report.json` is reviewed.

Recommended next verification:

```bash
cd AI_project_ai
python evals/eval_ranking.py
```

Then compare the new `evals/results/latest_report.json` against the previous report, especially:

- `ndcg@5` / `ndcg@10`
- `precision@3` / `precision@5`
- `recall@5` / `recall@10`
- `mrr@10`
- `pairwise_order_accuracy`
- number of missed relevant companies
- number of unlabeled top predictions
---

## 2026-05-11 clarification: where prospect matches come from

Question answered:

- Does a prospect request call the VDAB API live, or does the AI get matches from the database?

Current behavior:

- A normal prospect request does **not** call the external VDAB API live.
- `/companies/prospect` loads companies and linked vacancies from the local database using `_fetch_all_companies_with_vacatures()`.
- That local data comes from `tblBedrijven` joined with `tblVacatures`.
- The backend first computes deterministic/product-first prospect rankings from the database candidates.
- If `AI_SERVICE_URL` is configured and no filters are active, the backend may call the AI wrapper at `/generate-prospect`.
- The AI wrapper also fetches candidates from the backend `/companies/search`, which itself queries the local database; it does not call VDAB directly for live matches.

Where VDAB is called:

- VDAB is called during import/sync/pull flows, where vacancies are fetched, cleaned, deduplicated, and saved into `tblVacatures` / `tblBedrijven`.
- Matching requests then use that stored database snapshot.

Important caveat:

- If the local database is stale, prospect matching is also stale until the VDAB sync/pull flow runs again.
---

## 2026-05-11 filter assessment

Question answered:

- Are the current company prospect filters working correctly?

Assessment:

- The filters are not trash; the main company prospect filter path is wired correctly now.
- `SearchPageCompany.tsx` puts `locatie`, `sector`, `bedrijfsgrootte`, and `regio` into the result URL.
- `CompanyResultPage.tsx` reads those URL params and sends them in `body.filters` to `/companies/prospect`.
- `/companies/prospect` applies filters before ranking companies.
- When filters are active, the backend skips the AI wrapper because the wrapper still fetches its own broad candidates and does not accept filters. This prevents unfiltered AI results from leaking into filtered searches.

Limitations:

- `bedrijfsgrootte` is still a weak approximation based on number of linked vacancies, not real employee count.
  - `klein`: fewer than 5 linked vacancies
  - `middel`: 5 to 20 linked vacancies
  - `groot`: more than 20 linked vacancies
- `sector` filtering is substring-based against company sector and vacancy titles, so it can miss synonyms or related industries.
- `locatie` is substring-based against the combined location string, so spelling/region variations may miss.
- `regio` only supports the configured broad buckets (`vlaanderen`, `wallonie`, `brussel`).
- Filters are applied in Python after loading database candidates instead of directly in SQL for `/companies/prospect`, which is okay for small/medium datasets but may become inefficient later.

Conclusion:

- Filters are functional and safer than before, especially because filtered requests no longer use the unfiltered AI wrapper path.
- They are still basic/heuristic and should eventually be upgraded with normalized location/sector fields and real employee/company-size data.
---

## 2026-05-11 filter improvement implementation

Requested change:

- Improve the company prospect filters so they are less brittle than direct substring checks.

Files changed:

- `backend_project/backend/app/routers/vdab.py`
- `PROJECT_CHANGES_2026-05-08.md`

Implemented changes:

### Normalized filter matching

Filter matching now normalizes text before comparison:

- lowercase
- accent stripping (`Li?ge` / `Liege`, `industri?le` / `industriele`)
- whitespace cleanup
- hyphen/space variants for terms such as `oost-vlaanderen` / `oost vlaanderen`

### Better location and region aliases

Added aliases for common Belgian location/province variants, including examples such as:

- `brussel`, `brussels`, `bruxelles`
- `antwerpen`, `antwerp`, `anvers`
- `luik`, `liege`, `li?ge`
- province aliases such as `oost-vlaanderen`, `east flanders`, `flandre orientale`

Region filtering now expands broad regions into province/location terms using aliases:

- Vlaanderen / Flanders
- Wallonie / Wallonia
- Brussel / Brussels / Bruxelles

### Better sector aliases

Sector matching now expands common business/industry terms before filtering. Examples:

- automation / automatisatie / PLC / SCADA / robotica
- techniek / onderhoud / maintenance / engineering
- voeding / food / beverage / brouwerij / packaging
- logistiek / warehouse / magazijn / AGV
- metaal / metal / CNC / machining
- zorg / healthcare / medisch
- ICT / IT / software / cloud / cybersecurity

### Wider sector evidence matching

Sector filters are now matched against more than just the company sector and vacancy titles. The backend now checks a combined sector evidence text containing:

- company sector
- AI description
- business trigger
- vacancy titles
- roles/beroepen
- tech stack
- machine park
- keywords
- vacancy summaries

This should reduce false negatives where the sector is not stored cleanly but is visible in vacancy/enrichment data.

### Filter diagnostics in run report

`/companies/prospect` now includes `filters_applied` in `run_report`, with:

- original candidate count
- count after each filter stage
- final filtered count
- expanded filter terms used
- warnings for ignored/unknown company-size filters

This makes it easier to debug whether filters are too strict or too broad.

Still limited:

- `bedrijfsgrootte` still uses linked-vacancy count as a temporary heuristic because real employee-count/company-size data is not available yet.
- Filters are still applied after loading DB candidates into Python, not pushed fully into SQL.
- Alias lists are useful but incomplete; they should grow as real user searches reveal misses.

Verification:

- `python -m py_compile backend_project\backend\app\routers\vdab.py AI_project_ai\engine.py AI_project_ai\api.py AI_project_ai\evals\eval_ranking.py` passed.
---

## 2026-05-11 eval report review

Reviewed file:

- `AI_project_ai/evals/results/latest_report.json`

Report generated against:

- `https://infosearch.duckdns.org`
- endpoint `/companies/prospect`
- generated at `2026-05-11T13:09:14Z`

Observed summary metrics:

- `ndcg@5`: 0.1876
- `ndcg@10`: 0.1876
- `precision@3`: 0.1333
- `precision@5`: 0.08
- `recall@5`: 0.2222
- `recall@10`: 0.2222
- `mrr@10`: 0.3
- average `returned_count`: 2.2667
- `labeled_coverage@10`: 0.2622

Important interpretation:

- These numbers look weak, but the report is likely not a valid quality measurement yet.
- The gold file labels companies by numeric IDs from the old/starter sample data (`bedrijf_id` 1, 2, 3).
- The live Hetzner database uses different real company IDs/names. For example, the report maps `bedrijf_id: 2` to `ArcelorMittal Gent`, while the starter gold labels expected ID 2 to be the sample company `BREW-TECH AUTOMATION`.
- Because of this ID mismatch, many predictions are scored as wrong even when the model may be doing something reasonable for the live database.

Conclusion:

- The current eval report is useful as a smoke test that the endpoint runs and returns structured metrics.
- It is not yet reliable for judging actual model quality on Hetzner.

Recommended next fix:

- Rebuild the gold dataset from the actual Hetzner/live database, or make eval labels use stable company identifiers such as normalized company name/domain instead of environment-specific numeric IDs.
- Until then, avoid using the current metrics as proof that the model got better or worse.
---

## 2026-05-11 live gold/labeling set rebuild

Requested change:

- Rebuild the gold database/set after discovering that the old gold labels used starter/sample company IDs that do not match the live Hetzner database.

Implemented changes:

### Live labeling set builder

Added:

- `AI_project_ai/evals/_build_live_labeling_set.py`

This script fetches the current live companies from:

- `{EVAL_API_URL or BACKEND_URL or https://infosearch.duckdns.org}/companies/search`

It then builds:

- `AI_project_ai/evals/prospect_ranking_live_labeling_starter.jsonl`
- `AI_project_ai/evals/LIVE_LABELING_GUIDE.md`

The generated starter set uses live DB company IDs, names, KBO numbers, locations, contact data, and compact vacancy evidence. It creates 15 product cases with 12 likely candidate companies per case.

### Live labeling converter

Added:

- `AI_project_ai/evals/_convert_live_labeling_to_gold.py`

After labels are manually filled in the live starter file, this script converts it into:

- `AI_project_ai/evals/prospect_ranking_live_gold.jsonl`

The converter refuses to create gold cases with no labels, because unlabeled data should not be treated as gold.

### Eval metadata hardening

Updated:

- `AI_project_ai/evals/eval_ranking.py`

The eval loader now accepts optional `bedrijfsnaam` and `kbo_nummer` fields in labels. Reports now include expected company names for labeled predictions/missed relevant companies and can show `id_name_mismatches` if a numeric ID points to a different company name than expected.

Generated live starter set:

- Fetched 41 live companies from `https://infosearch.duckdns.org`.
- Wrote 15 live labeling cases.
- Each case currently has 12 candidates with `label: null` and empty `reason` fields ready for manual labeling.

Important caveat:

- The real `prospect_ranking_live_gold.jsonl` was not generated yet because the new live starter set needs human labels first. Auto-labeling it would create a weak synthetic benchmark, not a real gold set.

Recommended workflow:

```bash
cd AI_project_ai
python evals/_build_live_labeling_set.py
# manually fill labels/reasons in evals/prospect_ranking_live_labeling_starter.jsonl
python evals/_convert_live_labeling_to_gold.py
EVAL_GOLD_PATH=evals/prospect_ranking_live_gold.jsonl python evals/eval_ranking.py
```

Verification:

- `python AI_project_ai\evals\_build_live_labeling_set.py` succeeded.
- `python -m py_compile AI_project_ai\evals\_build_live_labeling_set.py AI_project_ai\evals\_convert_live_labeling_to_gold.py AI_project_ai\evals\eval_ranking.py` passed.
---

## 2026-05-11 live labels compact format support

Requested clarification:

- The user asked whether they can fill labels in a compact JSON array format like `{ case_id, labels: [...] }` instead of editing the full live candidate starter JSONL file.

Change made:

- Updated `AI_project_ai/evals/_convert_live_labeling_to_gold.py` to support both input formats:
  1. the full starter file `prospect_ranking_live_labeling_starter.jsonl` with `candidate_businesses`
  2. a compact JSON array file `prospect_ranking_live_labels.json` with `labels`

New preferred compact workflow:

```powershell
cd "C:\Users\nterh\OneDrive\Bureaublad\ai_project\AI_project\AI_project_ai"
notepad evals\prospect_ranking_live_labels.json
python evals\_convert_live_labeling_to_gold.py
$env:EVAL_GOLD_PATH="evals\prospect_ranking_live_gold.jsonl"
$env:EVAL_API_URL="https://infosearch.duckdns.org"
python evals\eval_ranking.py
```

The converter now reads `prospect_ranking_live_labels.json` if it exists; otherwise it falls back to `prospect_ranking_live_labeling_starter.jsonl`.

Verification:

- `python -m py_compile AI_project_ai\evals\_convert_live_labeling_to_gold.py` passed.
---

## 2026-05-11 eval speed / AI path clarification

Observed behavior:

- The live eval against `https://infosearch.duckdns.org` completed very quickly.
- A direct check of `/companies/prospect` returned `ai_powered: false`.

Interpretation:

- The eval is currently measuring the backend deterministic prospect-ranking fallback, not the AI wrapper/Groq prompt path.
- This explains why the report can be written in a few seconds for 15 cases.
- If the AI path were active for every case, the eval would normally take noticeably longer because each case would involve an AI service call.

Additional observation:

- The direct response had an empty `run_report`, which suggests the deployed Hetzner backend may not yet include the latest local backend changes that add richer run-report/filter diagnostics.

Fix made locally:

- Updated `AI_project_ai/evals/eval_ranking.py` so optional `bedrijfsnaam` / `kbo_nummer` fields do not appear as the literal string `"None"` in reports when compact labels omit them.

Next checks:

- Confirm the Hetzner backend has the latest commits deployed.
- Confirm `AI_SERVICE_URL` is set in the backend environment.
- Confirm the AI wrapper service is running and reachable from the backend.
- Rerun a single `/companies/prospect` request and check whether `ai_powered` becomes `true`.



---

# Model, ranking, and evaluation changes

# Changes made to model/evaluation

Date: 2026-05-19

## Files changed

- `AI_project_ai/engine.py`
- `AI_project_ai/api.py`
- `AI_project_ai/evals/eval_ranking.py`
- `AI_project_ai/evals/results/latest_report.json` (regenerated by live eval runs)

## `AI_project_ai/engine.py`

### Added deterministic pre-ranking

Added an evidence-based deterministic scorer before the LLM ranking step.

Purpose:

- prevent relevant companies from being missed before the LLM sees them
- break flat/identical LLM score ties
- improve ranking stability
- reduce false positives from generic/manual-service companies

New helper logic includes:

- `_contains_any(...)`
- `_tokenize_for_matching(...)`
- `_candidate_text(...)`
- `_deterministic_match(...)`

The deterministic score uses:

- direct technology overlap
- sector overlap
- business/pain-point overlap
- Dutch/English synonym groups
- token overlap
- data completeness
- evidence quality
- penalties for weak/manual-service matches

### Added Dutch/English synonym matching

Examples of synonym groups added:

- predictive maintenance / condition monitoring ↔ onderhoud / storing / technieker
- PLC / Siemens / SCADA / Schneider ↔ automatisatie / sturing / elektricien
- machine vision / quality inspection ↔ inspectie / kwaliteit / CNC / controle
- warehouse / AGV / robotics ↔ magazijn / logistiek / heftruck / robot
- recruitment / CRM / workflow ↔ vacature / planning / sales / account
- food / packaging ↔ voeding / productie / verpakking / afvul
- battery / BMS / EV ↔ batterij / elektrisch / automotive

### Changed candidate handling

Before:

- only the first 30 business profiles were compacted/sent onward

After:

- all fetched companies are compacted and deterministically scored first
- then the best evidence-ranked candidates are selected for the LLM

Added configurable limit:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=120
```

Default is now `120` instead of the hardcoded `30`.

### Added score blending

LLM scores are blended with deterministic scores when available.

Purpose:

- avoid many companies receiving identical scores
- improve ordering when the LLM returns flat or poorly calibrated scores

### Added top-10 fallback filling

If the LLM returns too few prospects, the code now fills the ranking with deterministic evidence-ranked fallback candidates.

Purpose:

- avoid returning only 1-3 results
- improve recall@10 and nDCG@10
- make evaluation more meaningful

Fallback candidates include:

- `bedrijf_id`
- `bedrijfsnaam`
- evidence snippets
- deterministic score/reasons
- estimated score dimensions
- short evidence-based `waarom`

### Prompt changes

Updated the ranking prompt so the LLM:

- uses `deterministic_score` as an extra signal
- prefers a full top 10 when enough candidates exist
- gives low scores for weak candidates instead of hiding them too aggressively
- still avoids true no-match companies

## `AI_project_ai/api.py`

### Increased backend candidate fetch pool

Added configurable backend fetch limit:

```env
PROSPECT_CANDIDATE_FETCH_LIMIT=200
```

Default is `200`.

### Changed candidate retrieval behavior

Before:

- the API only fetched extra companies if the initial filtered result had fewer than 10 companies
- fallback stopped around 50 companies

After:

- the API always fetches a broader candidate pool
- it merges the product-search results with a broader empty-query company list
- it deduplicates companies by ID
- it stops at `PROSPECT_CANDIDATE_FETCH_LIMIT`

Reason:

- using only ~30 profiles can hide relevant companies before ranking/evaluation
- this was likely one of the main reasons for low recall/nDCG

## `AI_project_ai/evals/eval_ranking.py`

### Added score diagnostics

Added `score_diagnostics(...)` to detect score/ranking collapse.

New metrics added to each case and the summary:

- `score_spread@k`
- `unique_scores@k`
- `top_score_tie_count@k`
- `flat_score_warning`

Purpose:

- detect when many results receive the same score
- make score calibration problems visible in eval output

### Added SSL verify env flag

Added:

```env
EVAL_SSL_VERIFY=false
```

Purpose:

- allow eval against the deployed backend with a self-signed certificate

### Improved HTTP error reporting

Before:

- eval failed with a generic `httpx.HTTPStatusError`

After:

- eval reports HTTP status, URL, and a short response preview

This made the Fortinet/DNS blocking issue clear during testing.

## Eval runs performed

Eval command used:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

### First successful deployed eval

Summary:

- `nDCG@5`: 0.4249
- `nDCG@10`: 0.4331
- `precision@3`: 0.2444
- `precision@5`: 0.1600
- `recall@5`: 0.2822
- `recall@10`: 0.2989
- `MRR@10`: 0.5333
- `returned_count`: 3.0
- `flat_score_warning`: 1.0

Finding:

- deployed backend returned only about 3 prospects per query
- recall and nDCG were capped by too few returned candidates

### Second deployed eval rerun

Summary:

- `nDCG@5`: 0.4409
- `nDCG@10`: 0.4443
- `precision@3`: 0.2667
- `precision@5`: 0.1733
- `recall@5`: 0.2956
- `recall@10`: 0.2956
- `MRR@10`: 0.5333
- `returned_count`: 3.1333
- `flat_score_warning`: 1.0

Finding:

- slight improvement, but same main issue: too few results returned

### Latest deployed eval after backend candidate behavior appeared improved

Summary:

- `nDCG@5`: 0.5523
- `nDCG@10`: 0.6014
- `precision@3`: 0.2667
- `precision@5`: 0.2133
- `recall@5`: 0.3678
- `recall@10`: 0.4567
- `MRR@10`: 0.5111
- `pairwise_order_accuracy`: 0.9774
- `returned_count`: 8.8
- `flat_score_warning`: 1.0

Improvement compared with previous deployed eval:

- `nDCG@10`: 0.4443 → 0.6014
- `recall@10`: 0.2956 → 0.4567
- `returned_count`: 3.13 → 8.8

Finding:

- sending/evaluating more business profiles is very likely a major improvement
- score calibration/ties still remain a problem because `flat_score_warning` stayed at 1.0

## Verification performed

Syntax checks passed:

```powershell
python -m py_compile api.py engine.py evals\eval_ranking.py
```

Smoke test performed:

- mocked `groq` import
- confirmed deterministic scorer ranks a Siemens/Profinet industrial company above irrelevant manual farm work
- confirmed a relevant company at position 199 is now included after scoring, instead of being sliced out before scoring

## Current recommendation

Deploy the changed backend/AI code, then rerun:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Watch especially:

- `nDCG@10`
- `recall@10`
- `returned_count`
- `flat_score_warning`

The next improvement should focus on score calibration/tie-breaking if `flat_score_warning` remains high.

## 2026-05-19 15:49 ? Deployed eval after backend update

Command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Summary:

- `nDCG@5`: 0.5442
- `nDCG@10`: 0.6082
- `precision@3`: 0.2667
- `precision@5`: 0.2133
- `recall@5`: 0.3678
- `recall@10`: 0.4567
- `MRR@10`: 0.4667
- `pairwise_order_accuracy`: 0.9804
- `returned_count`: 10.0
- `labeled_coverage@10`: 0.6333
- `score_spread@k`: 0.6667
- `unique_scores@k`: 1.3333
- `top_score_tie_count@k`: 7.2
- `flat_score_warning`: 1.0

Finding:

- Backend now returns a full top 10 on average (`returned_count` 10.0), so the candidate-volume issue is fixed.
- `nDCG@10` improved slightly compared with the previous 0.6014 run, now 0.6082.
- `flat_score_warning` is still 1.0 and top-score ties increased, so the next bottleneck is score calibration/tie-breaking rather than candidate count.

## 2026-05-19 15:51 ? Score calibration/tie-breaking fix

Problem:

- Latest deployed eval returned a full top 10, but `flat_score_warning` stayed at 1.0.
- Many cases still had all candidates scored as `1.0`, causing ranking ties even when candidate count was fixed.

Changes in `AI_project_ai/engine.py`:

- Added `_score_dimension_average(...)` to aggregate LLM score dimensions.
- Added `_recalibrated_score(...)` to convert coarse LLM scores into granular 0-10 scores.
- Added `_spread_tied_scores(...)` to avoid exact equal final scores while preserving relevance order.
- Updated `_normalize_ranked_results(...)` so final scores combine:
  - deterministic evidence score
  - LLM score dimensions
  - raw LLM score
  - evidence count bonus
  - a tiny stable rank tie-breaker
- Updated fallback candidate scoring so fallback rows also receive more granular scores.
- Updated the LLM prompt to explicitly request decimal scores and avoid flat 1/2/3 scoring.

Verification:

```powershell
python -m py_compile api.py engine.py evals\eval_ranking.py
```

Smoke test:

- Simulated flat LLM scores of `1.0` for all candidates.
- New normalization produced distinct evidence-based scores:
  - strong Siemens/Profinet industrial match: 9.49
  - maintenance fallback: 4.18
  - weaker MRO/inspection match: 2.97
  - irrelevant manual farm work: 1.56

Expected impact after deploy:

- `flat_score_warning` should drop.
- `unique_scores@k` and `score_spread@k` should increase.
- nDCG may improve because relevant candidates can move above weak candidates instead of being tied.

## 2026-05-19 18:21 ? Deployed eval attempt blocked

Command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Result:

- Eval did not complete.
- Backend request returned HTTP 403 before the API response.
- Response preview showed `Fortinet Secure DNS Service Portal` / `Web Page Blocked`.

Finding:

- This was a network/content-filtering block against the DuckDNS backend, not an eval-code failure.
- No new metrics were generated; `evals/results/latest_report.json` still contains the previous successful report.

## 2026-05-19 18:26 ? Deployed eval after network switch

Command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Summary:

- `nDCG@5`: 0.5446
- `nDCG@10`: 0.5996
- `precision@3`: 0.2444
- `precision@5`: 0.2000
- `recall@5`: 0.3344
- `recall@10`: 0.4233
- `MRR@10`: 0.5111
- `pairwise_order_accuracy`: 0.9774
- `returned_count`: 8.8
- `labeled_coverage@10`: 0.6733
- `score_spread@k`: 0.6667
- `unique_scores@k`: 1.3333
- `top_score_tie_count@k`: 6.0
- `flat_score_warning`: 1.0

Finding:

- Eval completed successfully after switching networks.
- Metrics are close to the earlier 0.6014 nDCG@10 run, but lower than the full-top-10 0.6082 run.
- `returned_count` is back to 8.8 rather than 10.0, suggesting the latest backend currently does not always return a full top 10.
- Score ties remain unresolved on the deployed backend (`flat_score_warning` 1.0), which likely means the local score-calibration changes have not been deployed yet or are not active in the live endpoint.

## 2026-05-19 18:31 ? Deployed eval completed but results collapsed

Command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Summary:

- `nDCG@5`: 0.0419
- `nDCG@10`: 0.0394
- `precision@3`: 0.0222
- `precision@5`: 0.0133
- `recall@5`: 0.0222
- `recall@10`: 0.0222
- `MRR@10`: 0.0667
- `pairwise_order_accuracy`: null
- `returned_count`: 0.1333
- `labeled_coverage@10`: 0.1333
- `flat_score_warning`: 1.0

Finding:

- Eval technically succeeded, but the live endpoint returned almost no results.
- 13 out of 15 cases returned 0 predictions.
- Only `live_013` and `live_015` returned 1 prediction each.
- This is likely a deployed backend/API/runtime issue, not a normal ranking-quality result.
- Recommended next check: inspect deployed backend logs for `/companies/prospect`, especially LLM/API errors, candidate fetch errors, fallback fill behavior, and any exceptions swallowed into empty `results`.

## 2026-05-19 20:28 ? Ranking model upgraded

Changed `AI_project_ai/engine.py` so the prospect-ranking Groq model is configurable instead of hardcoded.

Before:

```python
model = "llama-3.3-70b-versatile"
```

After:

```env
PROSPECT_RANKING_MODEL=openai/gpt-oss-120b
PROSPECT_RANKING_FALLBACK_MODELS=llama-3.3-70b-versatile
```

Code behavior:

- Uses `openai/gpt-oss-120b` as the new default ranking model.
- Falls back to `llama-3.3-70b-versatile` if the primary model fails, is unavailable, or hits a provider/model error.
- Logs which Groq model is used for each prospect-ranking call.
- Keeps `model = PROSPECT_RANKING_MODEL` as a backwards-compatible alias for older imports/code.

Verification:

```powershell
python -m py_compile api.py engine.py evals\eval_ranking.py
```

Expected impact:

- Better reasoning/ranking quality from the stronger default model.
- Safer deployment because the previous model remains available as fallback.
- Eval should be rerun after deployment, preferably with delay/backoff to avoid rate limits.

## 2026-05-19 20:37 ? Post-backend-update eval/model check blocked

Requested check:

- Run deployed eval after backend update.
- Check whether the GPT model (`openai/gpt-oss-120b`) is being used.

Probe command:

```python
POST https://infosearch.duckdns.org/companies/prospect
```

Result:

- Request returned HTTP 403 before reaching the backend API.
- Response was `Fortinet Secure DNS Service Portal` / `Web Page Blocked`.
- Because the request is blocked at the network/content-filter level, the eval was not run.

Model visibility note:

- The public `/companies/prospect` response does not currently guarantee model metadata.
- The code logs the selected model server-side with:
  - `[Groq] Prospect ranking model: openai/gpt-oss-120b`
  - or fallback model if primary fails.
- Definitive confirmation requires backend logs, or exposing a debug/model field in the API response temporarily.

## 2026-05-19 20:42 ? Deployed eval after network switch and GPT model update

Pre-eval probe:

```python
POST https://infosearch.duckdns.org/companies/prospect
```

Probe result for Siemens predictive-maintenance query:

- HTTP 200
- `ai_powered`: false
- `results`: []
- `run_report.input_count`: 41
- `run_report.low_quality_results_rejected`: 41
- No model/Groq metadata exposed in the response.

Eval command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Summary:

- `nDCG@5`: 0.0419
- `nDCG@10`: 0.0394
- `precision@3`: 0.0222
- `precision@5`: 0.0133
- `recall@5`: 0.0222
- `recall@10`: 0.0222
- `MRR@10`: 0.0667
- `pairwise_order_accuracy`: null
- `returned_count`: 0.1333
- `labeled_coverage@10`: 0.1333
- `flat_score_warning`: 1.0

Finding:

- Eval reached the backend and completed, but the live endpoint returned almost no predictions.
- This does not look like a model-quality result; it looks like the deployed endpoint is not using the AI ranking path for most cases, or is rejecting nearly all candidates before AI ranking.
- The response did not expose whether `openai/gpt-oss-120b` was used.
- To confirm GPT model usage, check backend logs for `[Groq] Prospect ranking model: openai/gpt-oss-120b`.
- Also inspect why responses show `ai_powered: false` and `low_quality_results_rejected` equals the full input count for some queries.

## 2026-05-20 14:12 ? Deployed eval rerun

Command:

```powershell
$env:EVAL_API_URL="https://infosearch.duckdns.org"
$env:EVAL_SSL_VERIFY="false"
python evals\eval_ranking.py
```

Summary:

- `nDCG@5`: 0.0419
- `nDCG@10`: 0.0394
- `precision@3`: 0.0222
- `precision@5`: 0.0133
- `recall@5`: 0.0222
- `recall@10`: 0.0222
- `MRR@10`: 0.0667
- `pairwise_order_accuracy`: null
- `returned_count`: 0.1333
- `labeled_coverage@10`: 0.1333
- `score_spread@k`: 0.0
- `unique_scores@k`: 0.1333
- `top_score_tie_count@k`: 0.1333
- `flat_score_warning`: 1.0

Finding:

- Eval completed without network/HTTP failure.
- Results are still collapsed: the deployed endpoint returns almost no predictions.
- This matches the previous failed-quality run and suggests the live backend is still not using the intended AI ranking/fallback path, or is rejecting almost all candidates before ranking.
- Recommended next check: inspect `/companies/prospect` backend logs for `ai_powered: false`, candidate rejection counts, Groq model selection, and any swallowed model/fallback errors.
---

## 2026-05-21 eval handoff follow-up: Docker AI service routing

Requested change:

- Combine the split project change notes and review the eval handoff.
- Help unblock the prospect-ranking eval.

Implemented changes:

- Consolidated the root `changes.md` with `documentation/PROJECT_CHANGES_2026-05-08.md`.
- Excluded vendor/package changelogs under `node_modules`.
- Checked the live `/companies/prospect` endpoint with the first eval-style query.
- Confirmed the live endpoint still returned `ai_powered: false` and no results for that query, so a full eval would still measure the broken fallback path rather than ranking quality.
- Updated `docker-compose.yaml` so Docker services use Compose service names instead of host-only addresses:
  - backend -> AI API: `http://ai-api-test:8000`
  - AI API -> backend: `http://backend:8000`

Why this was needed:

- The handoff showed eval collapse was caused by the backend not using the intended AI ranking path or rejecting nearly all candidates.
- The live probe matched that failure mode: `ai_powered: false`, `results: []`, and all candidates counted as low quality.
- Incorrect service routing can make the backend fail to reach the AI API, forcing deterministic fallback and making eval metrics meaningless.

Verification:

- `python -m py_compile AI_project_ai/api.py AI_project_ai/engine.py AI_project_ai/evals/eval_ranking.py backend_project/backend/app/routers/vdab.py` passed.
- `docker compose -f docker-compose.yaml config --quiet` passed.
- Live probe against `https://infosearch.duckdns.org/companies/prospect` still showed the deployed environment needs this fix deployed/restarted before rerunning the full comparison eval.

Next step:

- Deploy/restart with the corrected service routing, then run the handoff eval comparison for 30-single vs 50-batched.
---

## 2026-05-21 eval follow-up: restore enriched model profiles

Problem observed:

- After the backend/AI routing fix, `/companies/prospect` used the AI path again, but the AI logs showed batches receiving only 42 backend candidates and one Groq batch failed JSON parsing.
- The AI wrapper fetched candidates through `/companies/search`, but that endpoint no longer returned the enriched company profile fields that the ranking prompt expects.
- As a result, the model saw thin company profiles made mostly from vacancy snippets instead of enriched `ai_beschrijving`, `tech_stack`, `machine_park`, `business_trigger`, and `keywords` evidence.

Implemented changes:

- Updated `backend_project/backend/app/routers/vdab.py` `/companies/search` to select and return enriched company profile fields:
  - `sector`
  - `ai_beschrijving`
  - `business_trigger`
  - `tech_stack`
  - `machine_park`
  - `keywords`
  - `vacature_samenvattingen`
- Expanded `/companies/search` text matching so product queries can match enriched profile columns, not only vacancy text and company name.
- Updated `AI_project_ai/engine.py` so normalized/fallback ranking results preserve `contactgegevens` from the compact company profile.
- Stopped the in-progress eval run because it was measuring the broken/thin profile input shape.

Verification:

- `python -m py_compile backend_project/backend/app/routers/vdab.py AI_project_ai/api.py AI_project_ai/engine.py AI_project_ai/evals/eval_ranking.py` passed.

Next step:

- Restart/redeploy backend and AI API with this patch, probe `/companies/search` to confirm enriched fields are present, then rerun the ranking eval.
---

## 2026-05-21 eval/manual search follow-up: avoid empty AI result pages

Problem observed:

- Manual product search for `automatische aardappel schiller` returned zero companies even though the AI API generated a report.
- Live probing confirmed `/companies/prospect` returned `ai_powered: true` but `results: []`.
- The backend was applying a hard post-AI cutoff of `score >= 4`, so niche/low-confidence AI-ranked candidates could all be removed before reaching the frontend.

Implemented change:

- Updated `/companies/prospect` so AI results are filtered by `score >= 4` only when that leaves at least one candidate.
- If every AI-ranked result is below 4, the backend now returns the top low-confidence AI candidates instead of an empty list.
- Added `quality_filter_relaxed` to the run report to make this fallback visible.

Verification:

- `python -m py_compile backend_project/backend/app/routers/vdab.py AI_project_ai/engine.py AI_project_ai/api.py` passed.

Deployment note:

- The live backend still needs to be rebuilt/restarted for this patch and the enriched `/companies/search` profile fields to take effect.
---

## 2026-05-21 eval follow-up: Mistral ranking provider support

Requested change:

- Allow the prospect-ranking engine to call Mistral directly instead of only Groq.
- Use `mistral-medium-2508` with the Mistral API key from `.env`.

Implemented changes:

- Updated `AI_project_ai/engine.py` with provider-aware ranking calls:
  - `PROSPECT_RANKING_PROVIDER=mistral` uses the Mistral chat completions endpoint.
  - `PROSPECT_RANKING_PROVIDER=groq` keeps the existing Groq path.
- Added Mistral env support:
  - `MISTRAL_API_KEY`
  - `MISTRAL_API_URL` with default `https://api.mistral.ai/v1/chat/completions`
- Preserved the same prompt, batching, JSON parsing, and deterministic fallback logic.
- Updated local `.env` ranking settings to use:
  - `PROSPECT_RANKING_PROVIDER=mistral`
  - `PROSPECT_RANKING_MODEL=mistral-medium-2508`
  - `PROSPECT_LLM_CANDIDATE_LIMIT=30`
  - `PROSPECT_LLM_BATCH_SIZE=5`
  - `PROSPECT_MAX_OUTPUT_TOKENS=700`

Verification:

- `python -m py_compile AI_project_ai/engine.py AI_project_ai/api.py backend_project/backend/app/routers/vdab.py` passed.

Deployment note:

- Rebuild/restart `ai-api-test` after copying these env/code changes to the VM.
- Logs should show `[Mistral] Prospect ranking model: mistral-medium-2508`.
---

## 2026-05-21 Mistral integration fix: ignore Groq model ids

Problem observed:

- The AI API was configured with `PROSPECT_RANKING_PROVIDER=mistral`, but the VM still had Groq model ids in the model/fallback env values.
- Logs showed Mistral receiving invalid models such as `qwen/qwen3-32b`, `llama-3.1-8b-instant`, and `llama-3.3-70b-versatile`.
- Mistral correctly rejected those with HTTP 400 `invalid_model`, causing every batch to fall back deterministically.

Implemented changes:

- Added `MISTRAL_DEFAULT_RANKING_MODEL`, defaulting to `mistral-medium-2508`.
- When `PROSPECT_RANKING_PROVIDER=mistral`, the engine now filters model candidates to Mistral-family model ids only.
- If no compatible Mistral model is configured, the engine logs this and uses `mistral-medium-2508` automatically.
- When `PROSPECT_RANKING_PROVIDER=groq`, Mistral model ids are ignored for Groq calls.

Required VM env:

```env
PROSPECT_RANKING_PROVIDER=mistral
PROSPECT_RANKING_MODEL=mistral-medium-2508
PROSPECT_RANKING_FALLBACK_MODELS=
MISTRAL_DEFAULT_RANKING_MODEL=mistral-medium-2508
```

Verification:

- `python -m py_compile AI_project_ai/engine.py AI_project_ai/api.py` passed.
---

## 2026-05-21 Mistral timeout follow-up

Problem observed:

- After switching to Mistral, backend logs showed `AI service unreachable (timed out), using deterministic fallback...`.
- The AI service was reachable, but Mistral ranking runs multiple sequential batches. The backend's fixed 120-second wait could expire before the AI API finished.
- When that happened, the backend returned deterministic fallback results, which can be empty for niche product queries.

Implemented changes:

- Added `AI_SERVICE_TIMEOUT_SECONDS` to `backend_project/backend/app/routers/vdab.py`, defaulting to `360` seconds.
- The backend `/companies/prospect` call to `/generate-prospect` now uses this configurable timeout instead of hard-coded `120.0`.
- Reduced local low-latency Mistral settings for manual testing:
  - `PROSPECT_LLM_CANDIDATE_LIMIT=15`
  - `PROSPECT_LLM_BATCH_SIZE=5`
  - `PROSPECT_MAX_OUTPUT_TOKENS=600`

Verification:

- `python -m py_compile backend_project/backend/app/routers/vdab.py AI_project_ai/engine.py AI_project_ai/api.py` passed.

Deployment note:

- Rebuild/restart both backend and AI API after applying this change.
- Add `AI_SERVICE_TIMEOUT_SECONDS=360` to the backend env on the VM if you want an explicit value.
---

## 2026-05-21 Mistral latency reduction

Problem observed:

- Mistral ranking could take too long for manual product search because batches were executed sequentially.
- Increasing backend timeout prevented premature fallback, but did not improve user-facing latency.

Implemented changes:

- Added `PROSPECT_LLM_CONCURRENCY` to `AI_project_ai/engine.py`.
- Ranking batches now run concurrently with an asyncio semaphore instead of strictly one after another.
- This keeps concurrency bounded while reducing wait time for interactive searches.
- Updated local fast/manual-search settings:
  - `PROSPECT_LLM_CANDIDATE_LIMIT=10`
  - `PROSPECT_LLM_BATCH_SIZE=5`
  - `PROSPECT_LLM_CONCURRENCY=2`
  - `PROSPECT_MAX_OUTPUT_TOKENS=500`

Recommended usage:

- Manual/product search: 10 candidates, batch size 5, concurrency 2.
- Eval/quality comparison: temporarily raise candidate limit to 30 after confirming latency and provider quota are acceptable.

Verification:

- `python -m py_compile AI_project_ai/engine.py AI_project_ai/api.py backend_project/backend/app/routers/vdab.py` passed.
---

## 2026-05-21 Mistral single-batch ranking config

Requested change:

- Use one Mistral request containing 30 companies instead of multiple smaller batches.

Updated settings:

```env
PROSPECT_LLM_CANDIDATE_LIMIT=30
PROSPECT_LLM_BATCH_SIZE=30
PROSPECT_LLM_CONCURRENCY=1
PROSPECT_MAX_OUTPUT_TOKENS=900
PROSPECT_LLM_PROMPT_CHAR_LIMIT=30000
```

Expected behavior:

- The AI service should log one ranking payload with `candidates=30`.
- This removes multi-batch sequencing overhead, but creates one larger prompt/request.

Verification:

- `python -m py_compile AI_project_ai/engine.py AI_project_ai/api.py backend_project/backend/app/routers/vdab.py` passed.
---

## 2026-05-21 Mistral JSON/fallback explanation fix

Problem observed:

- Result explanations still said `Groq-limieten` while the active provider was Mistral.
- This happened when the ranking engine fell back to deterministic ranking because no parseable LLM result was produced.

Implemented changes:

- Replaced the provider-specific fallback explanation with a generic AI-ranking fallback message.
- Changed fallback reason from `groq_size_or_rate_limit` to `llm_unavailable_or_unparseable`.
- Updated the Mistral request to use JSON mode: `response_format={"type":"json_object"}`.
- Updated the prompt to ask for `{ "results": [...] }` instead of a bare array.
- Made JSON parsing accept both bare lists and common object wrappers such as `results`, `rapport`, `companies`, `prospects`, or `matches`.

Verification:

- `python -m py_compile AI_project_ai/engine.py AI_project_ai/api.py backend_project/backend/app/routers/vdab.py` passed.
---

## 2026-05-21 disable deterministic prospect fallback

Problem observed:

- The frontend still showed deterministic fallback explanations even though the user wanted only real Mistral ranking results.
- The AI service could fail or return unusable output, and the backend would silently fall back to deterministic ranking.

Implemented changes:

- Added `PROSPECT_DISABLE_DETERMINISTIC_FALLBACK=true` in the AI engine path so normalized results no longer append deterministic candidates when Mistral returns fewer than 10 results.
- If the AI engine gets no usable LLM output and fallback is disabled, it returns an error instead of deterministic prospects.
- Added `AI_PROSPECT_DISABLE_DETERMINISTIC_FALLBACK=true` in the backend path by default.
- If `/generate-prospect` fails, times out, or returns unusable output, `/companies/prospect` now returns HTTP 503 instead of fake deterministic matches.

Verification:

- `python -m py_compile backend_project/backend/app/routers/vdab.py AI_project_ai/engine.py AI_project_ai/api.py` passed.

Deployment note:

- Rebuild/restart both `backend` and `ai-api-test`.
- Expected behavior: either real Mistral-ranked results, or an explicit error; no deterministic fallback results.

