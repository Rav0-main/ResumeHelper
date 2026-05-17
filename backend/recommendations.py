from typing import Any, Literal
from dataclasses import dataclass

import services.vacancies as vacancies
import services.llm as llm

Method = Literal["mock"] | Literal["AI"]
DataSource = Literal["mock"] | Literal["trudvsem.ru"]

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
        "impact": `llm.SkillRecommendationImpact`
    }
    """

    new_resume: str

    search_query: str
    """
    Запрос для поиска вакансий.
    """

async def get_recommendation_of(
    *,
    role: str,
    years_experience: int,
    skills: list[str],
    resume: str
) -> Recommendation:
    
    works = await vacancies.fetch(
        search_query=role, experience=years_experience
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

    works.sort(
        reverse=True, key=lambda v: max(v.salary_min, v.salary_max)
    )

    skill_recommendations, new_resume = llm.get_recommendations_by(
        resume=resume, skills=skills, vacancies=[
            v.snippet["requirement"] + "\n" + v.snippet["duty"] for v in works[:min(12, works_number_with_salary // 4)]
        ]
    )

    recommendation = Recommendation(
        salary_range_rub_gross_monthly={
            "low": min_salary, "median": median_salary, "high": max_salary
        },
        method="AI",
        data_source=vacancies.DOMAIN_SOURCE,
        data_source_note="Создано нейросетью, используйте с осторожностью.",
        vacancies_used=len(works),
        vacancies_with_salary=works_number_with_salary,
        recommendations=[
            s.__dict__ for s in skill_recommendations
        ],
        new_resume=new_resume,
        search_query=vacancies.VACANCIES_API_URL,
    )

    return recommendation