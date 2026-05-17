import httpx
import json
import logging
from typing import Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

VACANCIES_API_URL = "http://opendata.trudvsem.ru/api/v1"
DOMAIN_SOURCE = "trudvsem.ru"


class VacancyParseException(Exception):
    ...


@dataclass(frozen=True)
class Vacancy:
    id: str
    name: str
    """
    Наименование вакансии.
    """

    salary_min: int
    """
    Если salary_min == 0 => salary_min == NULL
    """
    
    salary_max: int
    """
    Если salary_max == 0 => salary_max == NULL
    """


    snippet: dict[str, str]
    """
    Краткое описание вакансии: \n
    {
        "requirement": `str`,
        "duty": `str`
    }
    """

    skills: list[str]
    """
    Навыки для вакансии.
    """

    experience: int


def _get_headers() -> dict[str, str]:
    return {
        "User-Agent": "ResumeHelper/1.0",
        "Accept": "application/json",
    }


def _write_error_note(
    status: int,
    body: str
) -> str:
    
    try:
        data = json.loads(body)
        meta = data.get("meta") or {}
        err = meta.get("error")
        if err:
            return f"trudvsem.ru HTTP {status}: {err}"
        
    except Exception:
        ...

    return f"trudvsem.ru HTTP {status}."


def _format_vacancy(
    v: dict[str, Any]
) -> Vacancy:
    return Vacancy(
        id=str(v.get("id", "")),
        name=v.get("job-name", "Вакансия"),
        salary_min=int(v.get("salary_min", 0)),
        salary_max=int(v.get("salary_max", 0)),
        snippet={
            "requirement": v.get("requirement", {}).get("education", ""),
            "duty": v.get("duty", "")
        },
        skills=v.get("skills", []),
        experience=int(v["requirement"].get("experience", 0))
    )


def _get_params_to_api(*,
    search_query: str,
    offset: int,
    limit: int = 100,
    need_salary: bool = True
) -> dict[str, str | int]:
    request: dict[str, str | int] = {
            "text": search_query,
            "offset": offset,
            "limit": limit,
        }

    request["salary"] = int(need_salary)

    return request


async def _parse_vacancies_page(*,
    client: httpx.AsyncClient,
    url: str,
    params: dict[str, str | int],
    experience: int
):
    items = []
    response = await client.get(
        url, params=params, headers=_get_headers()
    )
    
    if response.status_code != 200:
        _write_error_note(response.status_code, response.text)
        raise VacancyParseException(f"HTTP error code: {response.status_code}")

    data = response.json()
    results = data.get("results") or {}
    vacancies_raw = results.get("vacancies") or []

    raw_items = [v.get("vacancy", {}) for v in vacancies_raw if v.get("vacancy")]
    for raw_item in raw_items:
        vacancy = _format_vacancy(raw_item)
        if vacancy.experience is None or \
            (vacancy.experience is not None and experience >= vacancy.experience):
            items.append(vacancy)

    return items

async def fetch(*,
    search_query: str,
    experience: int,
    max_viewed_vacancies: int = 500
) -> list[Vacancy]:
    
    url = f"{VACANCIES_API_URL.rstrip('/')}/vacancies"

    last_note: str | None = None

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            items = []
            offset: int = -100
            limit: int = 100
            while offset < max_viewed_vacancies:
                offset += limit
                params = _get_params_to_api(
                    search_query=search_query, offset=offset, limit=limit, need_salary=True
                )
                try:
                    items.extend(await _parse_vacancies_page(
                        client=client, url=url, params=params, experience=experience
                    ))

                except VacancyParseException:
                    break

            if items:
                return items
            
            offset: int = -100
            while offset < max_viewed_vacancies:
                offset += limit
                params = _get_params_to_api(
                    search_query=search_query, offset=offset, limit=limit, need_salary=False
                )
                try:
                    items.extend(await _parse_vacancies_page(
                        client=client, url=url, params=params, experience=experience
                    ))

                except VacancyParseException:
                    break

    except httpx.RequestError as e:
        last_note = f"Сеть: {e}"
        logger.warning("Запрос к trudvsem.ru не удался: %s", e)
    
    except Exception as e:
        last_note = f"Ошибка запроса: {e}"
        logger.warning("Запрос к trudvsem.ru не удался: %s", e)

    raise RuntimeError(last_note or "trudvsem.ru недоступен.")
