from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from backend.assessment import assess_profile
from backend.hh_client import fetch_areas_flat

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Market Value", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AssessRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=200)
    years_experience: float = Field(..., ge=0, le=50)
    skills: Annotated[list[str], Field(default_factory=list, max_length=40)]
    area: str | None = Field(default=None, description="hh.ru area id, e.g. 1 for Moscow")


@app.get("/")
async def root() -> dict[str, Any]:
    return {
        "service": app.title,
        "version": app.version,
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/health",
        "endpoints": {"areas": "GET /api/areas", "assess": "POST /api/assess"},
        "ui": "Запустите фронтенд (Vite) и откройте http://127.0.0.1:5173 или http://localhost:5173 — адрес как в выводе Vite в терминале.",
    }


@app.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/areas")
async def areas() -> dict[str, Any]:
    items = await fetch_areas_flat()
    return {"items": items}


@app.post("/api/assess")
async def assess(body: AssessRequest) -> dict[str, Any]:
    skills = [s for s in body.skills if isinstance(s, str) and s.strip()]
    result = await assess_profile(
        role=body.role,
        years_experience=body.years_experience,
        skills=skills,
        area=body.area,
        per_page=100,
    )
    return result
