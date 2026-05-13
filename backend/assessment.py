from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from backend.hh_client import fetch_vacancies

EXPERIENCE_MAP = [
    (0, "noExperience"),
    (1, "between1And3"),
    (3, "between3And6"),
    (6, "moreThan6"),
]


def years_to_experience_id(years: float) -> str:
    y = max(0.0, float(years))
    chosen = EXPERIENCE_MAP[0][1]
    for threshold, eid in EXPERIENCE_MAP:
        if y >= threshold:
            chosen = eid
    return chosen


def _vacancy_monthly_rub_gross(v: dict[str, Any]) -> float | None:
    s = v.get("salary")
    if not s:
        return None
    cur = (s.get("currency") or "").upper()
    if cur not in ("RUR", "RUB"):
        return None
    f, t = s.get("from"), s.get("to")
    if f is None and t is None:
        return None
    if f is not None and t is not None:
        return (float(f) + float(t)) / 2.0
    return float(f if f is not None else t)


def _norm_skill(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip()).casefold()


def _skills_from_vacancy(v: dict[str, Any]) -> list[str]:
    ks = v.get("key_skills") or []
    names: list[str] = []
    for x in ks:
        if isinstance(x, dict) and x.get("name"):
            names.append(str(x["name"]).strip())
    return names


def _build_search_text(role: str, skills: list[str]) -> str:
    parts = [role.strip()] + [s.strip() for s in skills if s.strip()]
    return " ".join(parts)[:200]


def _percentiles(values: list[float]) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    arr = np.array(sorted(values), dtype=float)
    def pct(p: float) -> float:
        if len(arr) == 1:
            return float(arr[0])
        k = (len(arr) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(arr[int(k)])
        return float(arr[f] * (c - k) + arr[c] * (k - f))
    return pct(0.25), pct(0.5), pct(0.75)


def _model_path() -> Path:
    return Path(__file__).resolve().parent / "models" / "salary_model.joblib"


def _predict_with_model(
    role: str,
    years_experience: float,
    skills: list[str],
    area: str | None,
) -> tuple[float, float, float] | None:
    path = _model_path()
    if not path.exists():
        return None
    try:
        bundle = joblib.load(path)
        model = bundle["model"]
        vectorizer = bundle["vectorizer"]
        skill_part = " ".join(s.strip() for s in skills if s.strip())
        area_part = f" регион {area}" if area else ""
        text = f"{role.strip()} {skill_part} опыт {years_experience:g} лет{area_part}"
        X = vectorizer.transform([text])
        pred = float(model.predict(X)[0])
        spread = max(pred * 0.12, 15000.0)
        return pred - spread, pred, pred + spread
    except Exception:
        return None


async def assess_profile(
    *,
    role: str,
    years_experience: float,
    skills: list[str],
    area: str | None,
    per_page: int,
) -> dict[str, Any]:
    text = _build_search_text(role, skills)
    exp_id = years_to_experience_id(years_experience)
    items, source, mock_reason = await fetch_vacancies(
        text=text,
        area=area,
        experience=exp_id,
        per_page=per_page,
    )

    salaries: list[float] = []
    skill_rows: list[tuple[float, list[str]]] = []
    for v in items:
        mid = _vacancy_monthly_rub_gross(v)
        sk = _skills_from_vacancy(v)
        if mid is not None:
            salaries.append(mid)
            skill_rows.append((mid, sk))

    model_range = _predict_with_model(role, years_experience, skills, area)

    if salaries:
        p25, p50, p75 = _percentiles(salaries)
        low, med, high = round(p25, -2), round(p50, -2), round(p75, -2)
        method = "vacancies_percentiles"
    elif model_range:
        low, med, high = (round(x, -2) for x in model_range)
        method = "ml_model_only"
    else:
        low = med = high = 0.0
        method = "insufficient_data"

    if model_range and salaries and method == "vacancies_percentiles":
        m_low, m_med, m_high = model_range
        blend = 0.35
        low = round(blend * m_low + (1 - blend) * low, -2)
        med = round(blend * m_med + (1 - blend) * med, -2)
        high = round(blend * m_high + (1 - blend) * high, -2)
        method = "vacancies_plus_ml_blend"

    user_set = {_norm_skill(s) for s in skills if s.strip()}
    recommendations = _recommendations_from_vacancies(skill_rows, user_set, role)

    out: dict[str, Any] = {
        "salary_range_rub_gross_monthly": {"low": int(low), "median": int(med), "high": int(high)},
        "method": method,
        "data_source": source,
        "vacancies_used": len(items),
        "vacancies_with_salary": len(salaries),
        "recommendations": recommendations,
        "search_query": text,
    }
    if mock_reason:
        out["data_source_note"] = mock_reason
    return out


def _recommendations_from_vacancies(
    skill_rows: list[tuple[float, list[str]]],
    user_skills_norm: set[str],
    role: str,
    top_n: int = 8,
) -> list[dict[str, Any]]:
    if not skill_rows:
        return [
            {
                "title": "Добавьте больше навыков",
                "detail": "Укажите стек и инструменты из вакансий вашей специализации.",
                "impact": "medium",
            }
        ]
    salaries_only = [s for s, _ in skill_rows]
    cut = float(np.median(salaries_only)) if salaries_only else 0.0
    high_skills: list[str] = []
    low_skills: list[str] = []
    for sal, sks in skill_rows:
        bucket = high_skills if sal >= cut else low_skills
        bucket.extend(sks)

    hi = Counter(high_skills)
    lo = Counter(low_skills)
    scored: list[tuple[float, str]] = []
    for name, c_hi in hi.items():
        if not name.strip():
            continue
        n = _norm_skill(name)
        if n in user_skills_norm:
            continue
        c_lo = lo.get(name, 0) + 1
        score = c_hi / c_lo
        scored.append((score, name))
    scored.sort(reverse=True, key=lambda x: x[0])
    picks = [name for _, name in scored[:top_n]]

    recs: list[dict[str, Any]] = []
    for name in picks:
        recs.append(
            {
                "title": f"Добавьте навык: {name}",
                "detail": "Чаще встречается в более высокооплачиваемых похожих вакансиях на hh.ru.",
                "impact": "high" if scored and name == picks[0] else "medium",
                "skill": name,
            }
        )

    vague = len(role.strip()) < 8
    if vague:
        recs.insert(
            0,
            {
                "title": "Конкретизируйте должность",
                "detail": "Вместо «разработчик» укажите «Python backend middle» — так выбор вакансий будет точнее.",
                "impact": "high",
            },
        )

    if len(user_skills_norm) < 3:
        recs.append(
            {
                "title": "Расширьте блок навыков",
                "detail": "Добавьте 5–10 ключевых технологий из типичных требований (языки, фреймворки, БД, DevOps).",
                "impact": "medium",
            }
        )

    return recs[:top_n + 2]
