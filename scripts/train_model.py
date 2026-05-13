"""
Fetch vacancies from hh.ru (or use mocks) and train a RandomForest on vacancy text -> salary.

Run from repo root:
  python scripts/train_model.py

Requires network access to api.hh.ru or falls back to embedded mocks.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_extraction.text import TfidfVectorizer

from backend.hh_client import fetch_vacancies


def _mid(v: dict) -> float | None:
    s = v.get("salary")
    if not s:
        return None
    if (s.get("currency") or "").upper() not in ("RUR", "RUB"):
        return None
    f, t = s.get("from"), s.get("to")
    if f is None and t is None:
        return None
    if f is not None and t is not None:
        return (float(f) + float(t)) / 2.0
    return float(f if f is not None else t)


def _text(v: dict) -> str:
    parts = [str(v.get("name") or "")]
    for x in v.get("key_skills") or []:
        if isinstance(x, dict) and x.get("name"):
            parts.append(str(x["name"]))
    sn = v.get("snippet") or {}
    if isinstance(sn, dict):
        for k in ("requirement", "responsibility"):
            if sn.get(k):
                parts.append(str(sn[k])[:400])
    return " ".join(parts)[:4000]


async def collect(text: str, area: str | None, pages: int) -> list[dict]:
    all_items: list[dict] = []
    for page in range(pages):
        items, _, _ = await fetch_vacancies(
            text=text,
            area=area,
            experience=None,
            per_page=100,
            page=page,
        )
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
    return all_items


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="Python разработчик", help="Search query for hh.ru")
    ap.add_argument("--area", default="1", help="Area id (1=Moscow)")
    ap.add_argument("--pages", type=int, default=3, help="Pages to fetch (100 per page)")
    args = ap.parse_args()

    items = asyncio.run(collect(args.text, args.area, args.pages))
    texts: list[str] = []
    ys: list[float] = []
    for v in items:
        m = _mid(v)
        if m is None:
            continue
        texts.append(_text(v))
        ys.append(m)
    if len(texts) < 5:
        print("Not enough labelled vacancies; extend --text/--pages or check API access.")
        print(f"usable={len(texts)} total_items={len(items)}")
        return

    min_df = 1 if len(texts) < 30 else 2
    vectorizer = TfidfVectorizer(max_features=120, ngram_range=(1, 2), min_df=min_df, max_df=0.95)
    X = vectorizer.fit_transform(texts)
    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, ys)

    out_dir = ROOT / "backend" / "models"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "salary_model.joblib"
    joblib.dump({"model": model, "vectorizer": vectorizer}, path)
    print(f"Saved {path} (samples={len(texts)})")


if __name__ == "__main__":
    main()
