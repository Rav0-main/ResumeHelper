from typing import Any, Literal
from dataclasses import dataclass

import services.vacancies as vacancies

Method = Literal["mock"] | Literal["AI"]
DataSource = Literal["mock"] | Literal["hh.ru"]
RecommendationImpact = Literal["low"] | Literal["medium"] | Literal["high"]

@dataclass(frozen=True)
class Recommendation:
    salary_range_rub_gross_monthly: dict[str, int]
    """
    Словарь зарплат в рублях в месяц:\n
    {
        "low": `int`,
        "median": `int`,
        "high": `int`
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
        "title": `str`,
        "detail": `str`,
        "impact": `RecommendationImpact`
    }
    """

    search_query: str
    """
    Запрос для поиска вакансий.
    """

async def get_recommendation(
    *,
    role: str,
    years_experience: int,
    skills: list[str],
    placement: str | None,
    count: int,
    resume: str | None
) -> Recommendation:
    works = await vacancies.fetch(
        text=role,
        experience=years_experience,
        per_page=count,
        page=0
    )

    works_number_with_salary = sum(
        1 for v in works if v.salary_min != 0 or v.salary_max != 0
    )
    
    salaries = [v.salary_max for v in works if v.salary_max != 0]
    salaries.extend(v.salary_min for v in works if v.salary_min != 0)
    salaries.sort()
    
    median_salary = salaries[len(salaries) // 2] if salaries else 0
    min_salary = salaries[0] if salaries else 0
    max_salary = salaries[-1] if salaries else 0

    out = Recommendation(
        salary_range_rub_gross_monthly={"low": min_salary, "median": median_salary, "high": max_salary},
        method="mock",
        data_source="mock",
        data_source_note="This is mock data.",
        vacancies_used=len(works),
        vacancies_with_salary=works_number_with_salary,
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
        search_query=vacancies.VACANCIES_API_URL,
    )

    return out