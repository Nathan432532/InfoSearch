import asyncio
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers.auth import router as auth_router
from app.routers.vdab import router as vdab_router


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ALLOWED_ORIGINS", "")
    origins = [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]
    if origins:
        return origins
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


app = FastAPI()

origins = _parse_cors_origins()
print(f"DEBUG: Allowed origins are: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vdab_router)


AUTO_SYNC_ON_STARTUP = os.getenv("AUTO_SYNC_ON_STARTUP", "false").strip().lower() in {"1", "true", "yes", "on"}
AUTO_SYNC_ENABLED = os.getenv("AUTO_SYNC_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
AUTO_SYNC_TIME = os.getenv("AUTO_SYNC_TIME", "02:30")
AUTO_SYNC_TZ = os.getenv("AUTO_SYNC_TZ", "Europe/Brussels")
AUTO_SYNC_AMOUNT = int(os.getenv("AUTO_SYNC_AMOUNT", "100"))
_auto_sync_task: asyncio.Task | None = None


def _next_sync_delay_seconds() -> float:
    tz = ZoneInfo(AUTO_SYNC_TZ)
    now = datetime.now(tz)
    hour_str, minute_str = AUTO_SYNC_TIME.split(":", 1)
    target = now.replace(hour=int(hour_str), minute=int(minute_str), second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return max((target - now).total_seconds(), 1.0)


async def _run_full_sync(reason: str) -> None:
    from app.routers.vdab import full_sync

    print(f"[{reason}] Running VDAB full sync ...")
    try:
        result = full_sync(aantal=AUTO_SYNC_AMOUNT)
        print(f"[{reason}] Full sync done: {result}")
    except Exception as e:
        print(f"[{reason}] Full sync failed: {e}")


async def _startup_sync() -> None:
    """Background task: import vacancies from VDAB, then trigger AI enrichment."""
    await asyncio.sleep(5)
    await _run_full_sync("startup")


async def _nightly_sync_loop() -> None:
    while True:
        delay = _next_sync_delay_seconds()
        next_run = datetime.now(ZoneInfo(AUTO_SYNC_TZ)) + timedelta(seconds=delay)
        print(f"[scheduler] Next VDAB sync at {next_run.isoformat()} ({AUTO_SYNC_TZ})")
        await asyncio.sleep(delay)
        await _run_full_sync("scheduler")


@app.on_event("startup")
async def on_startup() -> None:
    global _auto_sync_task

    if AUTO_SYNC_ON_STARTUP:
        asyncio.create_task(_startup_sync())

    if AUTO_SYNC_ENABLED and _auto_sync_task is None:
        _auto_sync_task = asyncio.create_task(_nightly_sync_loop())


@app.on_event("shutdown")
async def on_shutdown() -> None:
    global _auto_sync_task

    if _auto_sync_task is not None:
        _auto_sync_task.cancel()
        try:
            await _auto_sync_task
        except asyncio.CancelledError:
            pass
        _auto_sync_task = None
