from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router

app = FastAPI(
    title="DropFix",
    version="0.1.0",
    description="Sprint 1 scaffolding for a reliable retention-to-revision pipeline.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

@app.get("/health")
def healthcheck():
    return {"status": "ok"}

