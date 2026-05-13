import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.schemas.resume import ResumeInput, AnalysisResponse
from backend.services.llm_client import llm_service

app = FastAPI(
    title="Baumanka Local Predictor API",
    version="1.0.0",
    description="MVP сервиса оценки резюме на базе локальной бесплатной ИИ-модели"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/api/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Локальный анализ резюме"
)
async def analyze(payload: ResumeInput):
    try:
        result = await llm_service.analyze_resume(payload)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при обработке локальной нейросетью: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
