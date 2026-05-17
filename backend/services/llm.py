from openai import OpenAI
from dataclasses import dataclass
from typing import Literal
from dotenv import load_dotenv
from pathlib import Path
from os import getenv
import re

SkillRecommendationImpact = Literal["low"] | Literal["medium"] | Literal["high"] | Literal[""]

ENV_FILEPATH = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=ENV_FILEPATH)

CLIENT = OpenAI(
    api_key=getenv("API_KEY"),
    base_url=getenv("AI_API_URL")
)

@dataclass(frozen=True)
class SkillRecommendation:
    title: str
    detail: str
    impact: SkillRecommendationImpact
    

def get_recommendations_by(*,
    resume: str,
    skills: list[str],
    vacancies: list[str]
) -> tuple[list[SkillRecommendation], str]:
    
    vacancy_params: str = "\n".join(
        f"вакансия {i}: {line}" for i, line in enumerate(vacancies, start=1)
    )

    response = CLIENT.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
        {
            "role": "user",
            "content": f"""
    Ты — эксперт по анализу рынка труда и подбору вакансий.
    Твоя задача — проанализировать разрыв между навыками пользователя и требованиями вакансий,
    после чего предложить от 3-ёх до 7-и наиболее ценных недостающих навыков.
    Возможные навыки бери ТОЛЬКО из предложенных вакансий.
    Новые навыки человека не должны совпадать с освоенными.

    Входной формат:
    Резюме: {resume}
    Навыки: {", ".join(skills)}
    {vacancy_params}

    Правила анализа:
    Определи, какие навыки из требований вакансий отсутствуют в поле "мои навыки".
    Выбери от 3-ёх до 7-и, которые принесут наибольшую пользу пользователю.

    Оцени impact по шкале:
    high — навык указан как обязательный минимум в 2+ вакансиях или является ключевым для всех трёх вакансий
    medium — навык указан как желательный/плюс в 2+ вакансиях или обязательный в одной вакансии
    low — навык упоминается только в одной вакансии как желательный, либо встречается редко

    В поле detail укажи конкретную причину выбора именно этого навыка,
    ссылаясь на частоту упоминаний или уровень зарплат (используй формулировки "на trudvsem.ru" как обоснование рыночной ситуации).
    Формат вывода (строго один блок, без пояснений, без лишней markdown-разметки, кроме переносов строк):

    title: Добавьте|Освойте навык <Другое наименование>: <Название>
    detail: <одно предложение на русском, почему важен навык>
    impact: high|medium|low

    Исправленное резюме: <Полное резюме пользователя, в конец списка "мои навыки"
    через запятую добавлен рекомендованный навык. Названия навыков — с заглавной буквы. Не меняй остальную структуру резюме, только дополни навыки>

    Примеры:

    Пример 1 (high):
    title: Освойте навык: Docker
    detail: Указан как обязательное требование во всех трёх вакансиях и влияет на
    уровень зарплаты на trudvsem.ru.
    impact: high
    Исправленное резюме: Я Python-разработчик, мои навыки: FastAPI, Docker

    Пример 2 (medium):
    title: Добавьте навык: SQL
    detail: Встречается как желательный плюс в двух из трёх вакансий.
    impact: medium
    Исправленное резюме: Я Python-разработчик, мои навыки: FastAPI, SQL

    Пример 3 (low):
    title: Популярен такой навык, как Redis
    detail: Упоминается только в одной вакансии как опциональный бонус.
    impact: low
    Исправленное резюме: Я Python-разработчик, мои навыки: FastAPI, Redis

    Важно:
    Не выводи ничего, кроме указанного блока формата.
    Если в вакансиях нет новых навыков (все уже есть у пользователя) —
    выбери самый частотный навык из требований, но поставь impact: low.
    В исправленное резюме добавь его повторно
    (если его не было — добавь, если был — оставь как есть).
    Название навыка пиши с заглавной буквы.

    После запятых в формате ставь пробел.
        """},
    ])

    text = response.choices[0].message.content if response.choices[0].message.content is not None \
        else ""
    skills_pattern = r"title:\s*(.+?)\s*\n\s*detail:\s*(.+?)\s*\n\s*impact:\s*(high|medium|low)"
    skill_matches = re.findall(skills_pattern, text, re.IGNORECASE | re.DOTALL)
    
    new_resume_pattern = r"Исправленное резюме:\s*(.*?)(?:\n\s*(?:title|$)|$)"
    new_resume_match = re.search(new_resume_pattern, text, re.DOTALL)

    return ([
        SkillRecommendation(
            title, detail, impact
        )
        for title, detail, impact in skill_matches
    ], new_resume_match.group(1).strip() if new_resume_match else resume)
