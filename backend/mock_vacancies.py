"""Offline vacancy samples (RUB, gross) when hh.ru API is unavailable."""

from __future__ import annotations

import re

MOCK_BY_KEYWORD: list[tuple[re.Pattern[str], list[dict]]] = [
    (
        re.compile(r"java|jvm|spring|kotlin", re.I),
        [
            {
                "name": "Java backend",
                "salary": {"from": 170000, "to": 260000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "Java"}, {"name": "Spring"}, {"name": "PostgreSQL"}, {"name": "Kafka"}],
            },
            {
                "name": "Senior Java",
                "salary": {"from": 240000, "to": 380000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "Java"}, {"name": "Spring Boot"}, {"name": "Kubernetes"}, {"name": "gRPC"}],
            },
            {
                "name": "Java developer",
                "salary": {"from": 140000, "to": 210000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "Java"}, {"name": "Hibernate"}, {"name": "Maven"}],
            },
        ],
    ),
    (
        re.compile(r"frontend|react|vue|angular|typescript|javascript", re.I),
        [
            {
                "name": "Frontend React",
                "salary": {"from": 150000, "to": 240000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "React"}, {"name": "TypeScript"}, {"name": "Webpack"}, {"name": "CSS"}],
            },
            {
                "name": "Senior Frontend",
                "salary": {"from": 220000, "to": 340000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "React"}, {"name": "Next.js"}, {"name": "GraphQL"}, {"name": "Testing"}],
            },
        ],
    ),
    (
        re.compile(r"1c|1с|бухгалтер|финанс", re.I),
        [
            {
                "name": "Программист 1С",
                "salary": {"from": 120000, "to": 200000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "1С"}, {"name": "БП"}, {"name": "ЗУП"}],
            },
            {
                "name": "1С разработчик middle+",
                "salary": {"from": 160000, "to": 260000, "currency": "RUR", "gross": True},
                "key_skills": [{"name": "1С:Предприятие"}, {"name": "ERP"}, {"name": "SQL"}],
            },
        ],
    ),
]

DEFAULT_MOCK = [
    {
        "name": "Python backend",
        "salary": {"from": 180000, "to": 280000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "Django"}, {"name": "PostgreSQL"}, {"name": "Docker"}],
    },
    {
        "name": "Senior Python",
        "salary": {"from": 250000, "to": 400000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "FastAPI"}, {"name": "Kubernetes"}, {"name": "SQL"}],
    },
    {
        "name": "Middle Python разработчик",
        "salary": {"from": 150000, "to": 220000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "REST API"}, {"name": "Git"}],
    },
    {
        "name": "Python / Data",
        "salary": {"from": 200000, "to": 320000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "pandas"}, {"name": "SQL"}, {"name": "Airflow"}],
    },
    {
        "name": "Backend Python",
        "salary": {"from": 160000, "to": 240000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "Flask"}, {"name": "Redis"}, {"name": "Linux"}],
    },
    {
        "name": "Fullstack Python/React",
        "salary": {"from": 170000, "to": 260000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "React"}, {"name": "TypeScript"}, {"name": "Docker"}],
    },
    {
        "name": "Python developer",
        "salary": {"from": 140000, "to": 200000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "Django"}, {"name": "Celery"}],
    },
    {
        "name": "DevOps + Python",
        "salary": {"from": 220000, "to": 350000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "Kubernetes"}, {"name": "Terraform"}, {"name": "AWS"}],
    },
    {
        "name": "ML Engineer",
        "salary": {"from": 230000, "to": 380000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "Python"}, {"name": "PyTorch"}, {"name": "ML"}, {"name": "SQL"}],
    },
    {
        "name": "Аналитик данных",
        "salary": {"from": 130000, "to": 190000, "currency": "RUR", "gross": True},
        "key_skills": [{"name": "SQL"}, {"name": "Python"}, {"name": "Excel"}, {"name": "BI"}],
    },
]


def mock_items(search_text: str = "") -> list[dict]:
    t = search_text or ""
    for pat, rows in MOCK_BY_KEYWORD:
        if pat.search(t):
            return [{"id": f"mock-{i}", **v} for i, v in enumerate(rows)]
    return [{"id": f"mock-{i}", **v} for i, v in enumerate(DEFAULT_MOCK)]
