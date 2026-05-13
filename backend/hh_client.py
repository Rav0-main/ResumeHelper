from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from backend.config import settings
from backend.mock_vacancies import mock_items

logger = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    ua = settings.hh_user_agent
    return {
        "User-Agent": ua,
        "HH-User-Agent": ua,
        "Accept": "application/json",
    }


def _hh_error_note(status: int, body: str) -> str:
    try:
        data = json.loads(body)
        errs = data.get("errors") or []
        if errs:
            parts: list[str] = []
            for e in errs[:4]:
                if not isinstance(e, dict):
                    continue
                t = str(e.get("type", "")).strip()
                v = e.get("value")
                if v is not None and str(v).strip():
                    parts.append(f"{t} ({v})" if t else str(v))
                elif t:
                    parts.append(t)
            if parts:
                return f"hh.ru HTTP {status}: " + "; ".join(parts)
        desc = (data.get("description") or "").strip()
        if desc:
            return f"hh.ru HTTP {status}: {desc}"
    except Exception:
        pass
    return f"hh.ru HTTP {status}."


def _vacancy_param_variants(
    *,
    text: str,
    area: str | None,
    experience: str | None,
    per_page: int,
    page: int,
) -> list[dict[str, str | int]]:
    """От более строгого к более мягкому (пустая выдача / гео)."""
    per = min(per_page, 100)
    pg = max(0, int(page))

    def base(*, currency: bool, exp: str | None) -> dict[str, str | int]:
        p: dict[str, str | int] = {
            "text": text,
            "per_page": per,
            "page": pg,
            "only_with_salary": "true",
        }
        if currency:
            p["currency"] = "RUR"
        if area:
            p["area"] = area
        if exp:
            p["experience"] = exp
        return p

    variants: list[dict[str, str | int]] = [
        base(currency=True, exp=experience),
        base(currency=True, exp=None),
        base(currency=False, exp=None),
    ]
    # уникальные по содержимому (если experience изначально None)
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
    """
    (items, source, mock_reason)
    source: 'hh' | 'mock'
    mock_reason: кратко, почему не данные hh (для UI), если source == 'mock'.
    """
    url = f"{settings.hh_base_url.rstrip('/')}/vacancies"
    variants = _vacancy_param_variants(
        text=text, area=area, experience=experience, per_page=per_page, page=page
    )
    last_note: str | None = None

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            for params in variants:
                r = await client.get(url, params=params, headers=_headers())
                if r.status_code != 200:
                    last_note = _hh_error_note(r.status_code, r.text)
                    logger.warning("hh.ru %s params=%s", last_note, params)
                    break

                data = r.json()
                items = data.get("items") or []
                if items:
                    return items, "hh", None

            if last_note is None:
                last_note = (
                    "По запросу на hh.ru не найдено вакансий с указанной зарплатой "
                    "(попробуйте другую роль, регион «Россия» или ослабьте формулировку)."
                )
    except httpx.RequestError as e:
        last_note = f"Сеть: {e}"
        logger.warning("hh.ru request failed: %s", e)
    except Exception as e:
        last_note = f"Ошибка запроса: {e}"
        logger.warning("hh.ru request failed: %s", e)

    if settings.use_mock_on_hh_failure:
        return mock_items(text), "mock", last_note or "hh.ru недоступен."
    raise RuntimeError(last_note or "hh.ru недоступен.")


async def fetch_areas_flat() -> list[dict[str, str]]:
    """Top-level regions for UI (id, name)."""
    url = f"{settings.hh_base_url.rstrip('/')}/areas"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, headers=_headers())
            r.raise_for_status()
            tree = r.json()
            out: list[dict[str, str]] = []
            for node in tree:
                out.append({"id": str(node["id"]), "name": node["name"]})
            return sorted(out, key=lambda x: x["name"])
    except Exception as e:
        logger.warning("areas fetch failed: %s", e)
        return [
            {"id": "1", "name": "Москва"},
            {"id": "2", "name": "Санкт-Петербург"},
            {"id": "113", "name": "Россия"},
            {"id": "3", "name": "Екатеринбург"},
            {"id": "88", "name": "Казань"},
            {"id": "4", "name": "Новосибирск"},
        ]
