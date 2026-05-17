import logging
from typing import Annotated, Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from recommendations import get_recommendation_of

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Resume Helper", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RecommendationRequest(BaseModel):
    role: str = Field(..., min_length=2, max_length=200)
    years_experience: int = Field(..., ge=0, le=50)
    skills: Annotated[list[str], Field(default_factory=list, max_length=40)]
    resume: str | None = Field(default=None, description="Resume text")


@app.get("/api/v1/hello_girl")
async def index():
    return {
        "title": "Hi. My name is Poli...",
        "detail": "OK"
    }


@app.post("/api/v1/recommendations")
async def recommendations(
    body: RecommendationRequest
) -> dict[str, Any]:
    
    skills = [s for s in body.skills if isinstance(s, str) and s.strip()]

    result = await get_recommendation_of(
        role=body.role,
        years_experience=body.years_experience,
        skills=skills,
        resume=body.resume if body.resume is not None else ""
    )
    
    return result.__dict__


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
    