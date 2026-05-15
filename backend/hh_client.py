from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.config import settings
from backend.mock_vacancies import mock_items

logger = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    return {
        "User-Agent": settings.hh_user_agent,
        "Accept": "application/json",
    }


def _trudvsem_error_note(status: int, body: str) -> str:
    try:
        data = json.loads(body)
        meta = data.get("meta") or {}
        err = meta.get("error")
        if err:
            return f"trudvsem.ru HTTP {status}: {err}"
    except Exception:
        pass
    return f"trudvsem.ru HTTP {status}."


def _normalize_vacancy(v: dict[str, Any]) -> dict[str, Any]:
    """Маппинг полей ответа Трудвсем в структуру HeadHunter."""
    salary_min = v.get("salary_min")
    salary_max = v.get("salary_max")

    salary_dict = None
    if salary_min or salary_max:
        salary_dict = {
            "from": salary_min if salary_min else None,
            "to": salary_max if salary_max else None,
            "currency": "RUR",
            "gross": None
        }

    # Защита от AttributeError: проверяем, что company является словарем
    company_data = v.get("company")
    company_name = company_data.get("name", "Работодатель") if isinstance(company_data, dict) else "Работодатель"

    requirement = v.get("requirement", {}).get("education", "")
    duty = v.get("duty", "")

    key_skills = []
    if v.get("requirement", {}).get("qualifications"):
        key_skills.append({"name": v["requirement"]["qualifications"]})

    return {
        "id": str(v.get("id", "")),
        "name": v.get("vacancy-name", "Вакансия"),
        "salary": salary_dict,
        "employer": {"name": company_name},
        "snippet": {
            "requirement": requirement or None,
            "responsibility": duty or None
        },
        "key_skills": key_skills,
        "alternate_url": v.get("vac_url", ""),
        "experience": {"name": v.get("experience", "Не указан")},
        "area": {"name": v.get("region", {}).get("name", "Россия")}
    }


def _vacancy_param_variants(
        *,
        text: str,
        area: str | None,
        experience: str | None,
        per_page: int,
        page: int,
) -> list[dict[str, str | int]]:
    limit = min(per_page, 100)
    offset = max(0, int(page)) * limit

    exp_val = None
    if experience:
        if "noExperience" in experience:
            exp_val = "от 0"
        elif "between1And3" in experience:
            exp_val = "от 1"
        elif "between3And6" in experience:
            exp_val = "от 3"
        else:
            exp_val = experience

    def base(*, with_salary: bool, use_exp: str | None, use_area: str | None) -> dict[str, str | int]:
        p: dict[str, str | int] = {
            "text": text,
            "offset": offset,
            "limit": limit,
        }
        if with_salary:
            p["salary"] = 1
        if use_area:
            p["region"] = use_area
        if use_exp:
            p["experience"] = use_exp
        return p

    # ИСПРАВЛЕНО: Заменен несуществующий аргумент use_none на use_area
    variants: list[dict[str, str | int]] = [
        base(with_salary=True, use_exp=exp_val, use_area=area),
        base(with_salary=True, use_exp=None, use_area=area),
        base(with_salary=True, use_exp=None, use_area=None),
    ]

    seen: list[str] = []
    out: list[dict[str, str | int]] = []
    for v in variants:
        key = json.dumps(v, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.append(key)
        out.append(v)
    return out


async def fetch_vacancies(
        *,
        text: str,
        area: str | None,
        experience: str | None,
        per_page: int,
        page: int = 0,
) -> tuple[list[dict[str, Any]], str, str | None]:
    base_url = settings.hh_base_url.rstrip("/")
    url = f"{base_url}/vacancies"

    variants = _vacancy_param_variants(
        text=text, area=area, experience=experience, per_page=per_page, page=page
    )
    last_note: str | None = None

    try:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            for params in variants:
                r = await client.get(url, params=params, headers=_headers())
                if r.status_code != 200:
                    last_note = _trudvsem_error_note(r.status_code, r.text)
                    logger.warning("trudvsem.ru %s params=%s", last_note, params)
                    break

                data = r.json()
                results = data.get("results") or {}
                vacancies_raw = results.get("vacancies") or []

                raw_items = [v.get("vacancy", {}) for v in vacancies_raw if v.get("vacancy")]
                if raw_items:
                    items = [_normalize_vacancy(item) for item in raw_items]
                    return items, "hh", None

            if last_note is None:
                last_note = "По запросу на ТрудВсем вакансий с зарплатой не найдено."
    except httpx.RequestError as e:
        last_note = f"Сеть: {e}"
        logger.warning("trudvsem.ru request failed: %s", e)
    except Exception as e:
        last_note = f"Ошибка запроса: {e}"
        logger.warning("trudvsem.ru request failed: %s", e)

    if settings.use_mock_on_hh_failure:
        return mock_items(text), "mock", last_note or "trudvsem.ru недоступен."
    raise RuntimeError(last_note or "trudvsem.ru недоступен.")


async def fetch_areas_flat() -> list[dict[str, str]]:
    """Локальный справочник кодов регионов РФ для обеспечения высокой скорости UI на хакатоне."""
    return [
        {"id": "77", "name": "Москва"},
        {"id": "78", "name": "Санкт-Петербург"},
        {"id": "66", "name": "Свердловская область"},
        {"id": "16", "name": "Республика Татарстан"},
        {"id": "54", "name": "Новосибирская область"},
        {"id": "50", "name": "Московская область"},
        {"id": "74", "name": "Челябинская область"},
        {"id": "52", "name": "Нижегородская область"},
        {"id": "34", "name": "Волгоградская область"},
        {"id": "23", "name": "Краснодарский край"},
    ]
