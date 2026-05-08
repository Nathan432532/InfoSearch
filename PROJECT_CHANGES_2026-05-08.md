# InfoSearch Project Changes and Model Evaluation Notes

Date: 2026-05-08

This document records the latest project changes, the relevant recent commits, and notes for the model evaluation work.

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

## Suggested commit message for the current uncommitted work

```text
Fix saved page animation warning and apply search filters to results
```

Possible longer description:

```text
- Guard saved-results GSAP animation when no saved items are rendered
- Pass company bedrijfsgrootte filter through search URL and results request
- Apply company prospect filters before backend ranking
- Avoid unfiltered AI prospect results when filters are active
- Send and apply job sector filter in vacancy search
```
