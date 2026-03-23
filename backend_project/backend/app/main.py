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