import asyncio
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.vdab import router as vdab_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vdab_router)


AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "false").strip().lower() in {"1", "true", "yes", "on"}


async def _startup_sync() -> None:
    """Background task: import vacancies from VDAB, then trigger AI enrichment."""
    from app.routers.vdab import full_sync

    await asyncio.sleep(5)

    print("[startup] Running VDAB full sync ...")
    try:
        result = full_sync(aantal=100)
        print(f"[startup] Full sync done: {result}")
    except Exception as e:
        print(f"[startup] Full sync failed: {e}")


@app.on_event("startup")
async def on_startup() -> None:
    if AUTO_SYNC_ON_STARTUP:
        asyncio.create_task(_startup_sync())
