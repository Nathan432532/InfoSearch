import sys
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import engine
import database
import json
import os

# Gebruik de servicenaam van Docker, of val terug op localhost voor lokale tests
BACKEND_URL = os.getenv("BACKEND_URL", "http://host.docker.internal:8999")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
# Cruciaal voor de Ollama library:
os.environ["OLLAMA_HOST"] = os.getenv("OLLAMA_HOST", "localhost:11434")


app = FastAPI(title="AI Enrichment Wrapper")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. De Automatische Verwerker
@app.post("/sync-and-enrich")
async def sync_and_enrich(background_tasks: BackgroundTasks):
    """Haalt rauwe data, verwerkt deze via AI en pusht terug naar SQL."""
    vacatures = await engine.haal_vacatures()
    print("vacatures ophalen...")
    
    if not vacatures:
        return {"status": "geen nieuwe vacatures gevonden"}

    for v in vacatures:
        # We doen dit in de achtergrond zodat de API snel reageert
        profiel = await engine.extraheer_en_verrijk(f"{v}")
        print("Qwen aanroepen om bedrijfsproefiel op te stellen...")
        await engine.push_profiel_naar_backend(profiel)
        print("bedrijfsprofiel aan het sturen...")
    
    return {"status": "processing", "count": len(vacatures)}

# 2. De Prospectie Engine
@app.post("/generate-prospect")
async def generate_prospect(product: str):
    # Haal bedrijven + vacatures op bij de backend — stuur product als query mee
    import httpx
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        # Haal eerst gefilterde resultaten op basis van product
        res = await client.post(
            f"{engine.BACKEND_URL}/companies/search",
            json={"query": product},
        )
        data = res.json()
        raw_bedrijven = data.get("results", [])

        # Als de gefilterde set te klein is, vul aan met alle bedrijven
        if len(raw_bedrijven) < 10:
            res_all = await client.post(
                f"{engine.BACKEND_URL}/companies/search",
                json={"query": ""},
            )
            all_data = res_all.json()
            all_bedrijven = all_data.get("results", [])
            seen_ids = {b.get("id") for b in raw_bedrijven}
            for b in all_bedrijven:
                if b.get("id") not in seen_ids:
                    raw_bedrijven.append(b)
                if len(raw_bedrijven) >= 50:
                    break

        print(f"bedrijven opgehaald van backend: {len(raw_bedrijven)} stuks")

    # Slim data down for Groq token limits — only essential fields
    bedrijven = []
    for b in raw_bedrijven:
        vacatures = b.get("vacatures", [])
        titels = [v.get("titel", "") for v in vacatures][:5]
        beroepen = list({v.get("beroep", "") for v in vacatures if v.get("beroep")})
        bedrijven.append({
            "id": b.get("id"),
            "naam": b.get("bedrijfsnaam", ""),
            "locatie": b.get("locatie", ""),
            "contactgegevens": b.get("contactgegevens", ""),
            "sector": beroepen[0] if beroepen else "Onbekend",
            "vacature_titels": titels,
            "beroepen": beroepen,
        })

    rapport = await engine.genereer_prospectie_rapport(product, bedrijven)
    print("rapport gegenereerd")

    return {"status": "success", "rapport": rapport}

@app.post("/run-benchmark")
async def run_benchmark_endpoint(iterations: int = 20):
    """Triggert de benchmark voor de geladen vacatures."""
    import validator # Zorg dat je validator.py in dezelfde map staat
    
    vacatures = await engine.haal_vacatures() # Haalt de 5 'killers' op uit server.js
    if not vacatures:
        return {"error": "Geen vacatures gevonden om te testen"}
        
    results = []
    for v in vacatures:
        # We testen hier specifiek de extractie-stap
        res = await validator.run_benchmark(
            engine.extraheer_en_verrijk, 
            json.dumps(v), 
            iterations=iterations
        )
        results.append({"vacature_id": v.get("id"), "stats": res})
        
    return {"status": "benchmark voltooid", "results": results}


# 4. Incrementele bedrijfsenrichment (startup + weekly cron)
@app.post("/enrich-new")
async def enrich_new_companies():
    """Fetch unenriched companies from the backend, run Qwen extraction,
    and push structured profiles back.  Processes only companies whose
    ai_enriched_at IS NULL so it's safe to call repeatedly."""
    import httpx

    timeout = httpx.Timeout(120.0, connect=60.0)

    # Step 1 – get unenriched companies from backend
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.get(f"{BACKEND_URL}/companies/unenriched?limit=200")
        if res.status_code != 200:
            return {"status": "error", "detail": f"Backend returned {res.status_code}"}
        data = res.json()
        companies = data.get("companies", [])

    if not companies:
        return {"status": "ok", "enriched": 0, "message": "Geen unenriched bedrijven"}

    enriched = 0
    failed = 0

    for company in companies:
        bedrijf_id = company.get("bedrijf_id")
        vacature_tekst = company.get("vacature_tekst", "")

        if not vacature_tekst:
            continue

        # Step 2 – run Qwen extraction on the vacancy text
        try:
            profiel = await engine.extraheer_en_verrijk(vacature_tekst)
        except Exception as e:
            print(f"[enrich] Qwen extraction failed for bedrijf {bedrijf_id}: {e}")
            failed += 1
            continue

        if not profiel:
            print(f"[enrich] No valid profile for bedrijf {bedrijf_id}, skipping")
            failed += 1
            continue

        # Step 3 – push enriched profile back to backend
        payload = {
            "bedrijf_id": bedrijf_id,
            "sector": profiel.get("sector"),
            "ai_beschrijving": profiel.get("business_trigger"),
            "tech_stack": profiel.get("tech_stack", []),
            "machine_park": profiel.get("machine_park", []),
            "business_trigger": profiel.get("business_trigger"),
            "keywords": profiel.get("keywords", []),
            "locatie": profiel.get("locatie"),
            "contactgegevens": profiel.get("contactgegevens"),
        }

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                push_res = await client.post(
                    f"{BACKEND_URL}/companies/upsert-profile",
                    json=payload,
                )
                if push_res.status_code == 200:
                    enriched += 1
                    print(f"[enrich] ✓ bedrijf {bedrijf_id} enriched")
                else:
                    print(f"[enrich] ✗ bedrijf {bedrijf_id}: {push_res.text}")
                    failed += 1
        except Exception as e:
            print(f"[enrich] Push failed for bedrijf {bedrijf_id}: {e}")
            failed += 1

    return {
        "status": "ok",
        "enriched": enriched,
        "failed": failed,
        "total": len(companies),
    }

# --- CLI COMMANDO'S ---
if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "test_file":
            try:
                with open("vacature.json", "r") as f:
                    data = json.load(f)
                    res = engine.extraheer_en_verrijk(data)
                    database.save_lokale_backup(res)
                    print("\n[CLI] Bestand succesvol verwerkt!")
            except FileNotFoundError:
                print("[FOUT] vacature.json niet gevonden.")
        elif cmd == "genereer":
            prod = input("Wat heb je gemaakt? ")
            db = database.lees_lokale_backups()
            print(engine.genereer_prospectie_rapport(prod, db))
    else:
        print("Start API met: uvicorn api:app --reload")