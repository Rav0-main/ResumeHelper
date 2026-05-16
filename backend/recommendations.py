from typing import Any, Literal
from dataclasses import dataclass

Method = Literal["mock"] | Literal["AI"]
DataSource = Literal["mock"] | Literal["hh.ru"]
RecommendationImpact = Literal["low"] | Literal["medium"] | Literal["high"]

@dataclass(frozen=True)
class Recommendation:
    salary_range_rub_gross_monthly: dict[str, int]
    """
    Словарь зарплат в рублях в месяц:\n
    {
        "low": int,
        "median": int,
        "high": int
    }
    """

    method: Method
    """
    Метод, с помощью которого были получены рекомендации.
    """

    data_source: DataSource
    """
    Источник данных для получения рекомендаций.
    """

    data_source_note: str | None
    """
    Meta для data_source.
    """

    vacancies_used: int
    """
    Количество использованных вакансий.
    """

    vacancies_with_salary: int
    """
    Количество вакансий, которые содержали информацию о зарплате.
    """

    recommendations: list[dict[str, Any]]
    """
    Словарь рекомендаций для улучшения резюме:\n
    {
        "title": str,
        "detail": str,
        "impact": RecommendationImpact
    }
    """

    search_query: str
    """
    Запрос для поиска вакансий.
    """

async def get_recommendation(
    *,
    role: str,
    years_experience: float,
    skills: list[str],
    area: str | None,
    per_page: int,
) -> Recommendation:
    out = Recommendation(
        salary_range_rub_gross_monthly={"low": 100_000, "median": 200_000, "high": 300_000},
        method="mock",
        data_source="mock",
        data_source_note="This is mock data.",
        vacancies_used=105,
        vacancies_with_salary=70,
        recommendations=[
            {
                "title": "Добавьте навык: Python",
                "detail": "Чаще встречается в более высокооплачиваемых похожих вакансиях на hh.ru.",
                "impact": "high",
                "skill": "Python",
            },
            {
                "title": "Добавьте навык: FastAPI",
                "detail": "Чаще встречается в более высокооплачиваемых похожих вакансиях на hh.ru.",
                "impact": "medium",
                "skill": "FastAPI",
            }
        ],
        search_query="hh.ru/api/v1/moneys",
    )

    return out