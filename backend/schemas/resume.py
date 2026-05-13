from pydantic import BaseModel, Field
from typing import List

class ResumeInput(BaseModel):
    fullName: str = Field(..., example="Иванов Иван")
    targetJob: str = Field(..., example="Python разработчик")
    experienceYears: float = Field(..., example=2.5)
    skillsText: str = Field(..., example="Python, FastAPI, SQL, Docker")
    experienceText: str = Field(..., example="Разрабатывал REST API, оптимизировал запросы в PostgreSQL.")

class AnalysisResponse(BaseModel):
    position: str = Field(..., example="Middle Python Developer")
    salary_min: int = Field(..., example=150000)
    salary_max: int = Field(..., example=220000)
    recommendations: List[str] = Field(..., example=["Добавьте коммерческий опыт с брокерами сообщений."])
