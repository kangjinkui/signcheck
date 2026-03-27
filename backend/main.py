from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.judge import router as judge_router
from api.chat import router as chat_router
from api.admin import router as admin_router
from db import engine
from db.schema_compat import ensure_schema_compatibility


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await ensure_schema_compatibility(engine)
    except Exception:
        logger.exception("Database schema compatibility check failed during startup")
        raise
    yield

app = FastAPI(
    title="광고판정 (AdJudge) API",
    description="강남구 옥외광고 인허가 자문 시스템",
    version="1.0.0",
    lifespan=lifespan,
)

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(judge_router)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"service": "광고판정 API", "version": "1.0.0"}
