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
    # Haal bedrijven + vacatures op bij de backend
    import httpx
    timeout = httpx.Timeout(120.0, connect=60.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        res = await client.post(
            f"{engine.BACKEND_URL}/companies/search",
            json={"query": ""},
        )
        print("bedrijven opgehaald van backend")
        data = res.json()
        raw_bedrijven = data.get("results", [])

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