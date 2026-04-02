import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.vdab import router as vdab_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://localhost:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vdab_router)


async def _startup_sync() -> None:
    """Background task: import vacancies from VDAB, then trigger AI enrichment."""
    import httpx
    from app.routers.vdab import update_vacancies

    ai_url = os.getenv("AI_SERVICE_URL", "").rstrip("/")

    # Small delay so the server is fully ready before heavy work
    await asyncio.sleep(5)

    # Step 1 — import VDAB vacancies
    print("[startup] Importing vacancies from VDAB …")
    try:
        result = update_vacancies(aantal=100)
        print(f"[startup] Vacancy import done: {result}")
    except Exception as e:
        print(f"[startup] Vacancy import failed: {e}")
        return

    # Step 2 — trigger AI enrichment for new companies
    if not ai_url:
        print("[startup] AI_SERVICE_URL not set, skipping enrichment.")
        return

    # Wait for the AI service (Ollama) to be ready
    for attempt in range(12):
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                probe = await client.get(f"{ai_url}/docs")
                if probe.status_code == 200:
                    break
        except Exception:
            pass
        print(f"[startup] Waiting for AI service … (attempt {attempt + 1})")
        await asyncio.sleep(10)

    print("[startup] Triggering AI enrichment for unenriched companies …")
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            res = await client.post(f"{ai_url}/enrich-new")
            print(f"[startup] Enrichment result: {res.json()}")
    except Exception as e:
        print(f"[startup] Enrichment call failed: {e}")


@app.on_event("startup")
async def on_startup() -> None:
    asyncio.create_task(_startup_sync())