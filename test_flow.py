"""Quick end-to-end flow test for the prospecting pipeline."""
import httpx, json, sys

BACKEND = "http://localhost:8000"
AI_SERVICE = "http://localhost:8001"

def test_backend_search():
    print("=== 1. Backend /companies/search ===")
    r = httpx.post(f"{BACKEND}/companies/search", json={"query": "test"}, timeout=15)
    print(f"  Status: {r.status_code}")
    d = r.json()
    count = len(d.get("results", []))
    print(f"  Companies found: {count}")
    return count > 0

def test_backend_prospect():
    print("\n=== 2. Backend /companies/prospect (small query) ===")
    r = httpx.post(f"{BACKEND}/companies/prospect", json={"query": "server kast"}, timeout=180)
    print(f"  Status: {r.status_code}")
    d = r.json()
    results = d.get("results", [])
    ai = d.get("ai_powered", False)
    print(f"  AI powered: {ai}")
    print(f"  Results: {len(results)}")
    for i, res in enumerate(results[:3]):
        name = res.get("bedrijfsnaam", "?")
        score = res.get("score", "?")
        why = (res.get("waarom") or "")[:80]
        print(f"    {i+1}. {name} — score: {score}/10 — {why}")
    return results

def test_save(results):
    print("\n=== 3. Save prospect list ===")
    payload = {
        "query": "server kast",
        "type": "company",
        "title": "Test: server kast",
        "filters": None,
        "results": results[:3],
    }
    r = httpx.post(f"{BACKEND}/searches/save", json=payload, timeout=15)
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    return r.status_code == 200

def test_saved_list():
    print("\n=== 4. Retrieve saved searches ===")
    r = httpx.get(f"{BACKEND}/searches/saved", timeout=15)
    print(f"  Status: {r.status_code}")
    d = r.json()
    searches = d if isinstance(d, list) else d.get("searches", [])
    print(f"  Saved searches: {len(searches)}")
    for s in searches[:3]:
        print(f"    - [{s.get('id')}] {s.get('title')} ({s.get('result_count', '?')} results)")
    return len(searches) > 0

def test_ai_service():
    print("\n=== 5. AI service health ===")
    try:
        r = httpx.get(f"{AI_SERVICE}/docs", timeout=10)
        print(f"  Status: {r.status_code}")
        return r.status_code == 200
    except Exception as e:
        print(f"  Error: {e}")
        return False

if __name__ == "__main__":
    ok = True
    ok = test_backend_search() and ok
    ok = test_ai_service() and ok
    results = test_backend_prospect()
    if results:
        ok = test_save(results) and ok
        ok = test_saved_list() and ok
    else:
        print("\n  SKIP save test — no prospect results")
        ok = False

    print(f"\n{'='*40}")
    print(f"Overall: {'PASS' if ok else 'SOME FAILURES'}")
