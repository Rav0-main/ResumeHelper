import os
import re
import requests
from dataclasses import dataclass
from typing import Literal
from dotenv import load_dotenv


load_dotenv()

FOLDER_ID = os.getenv("FOLDER_ID")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("YANDEX_MODEL", "yandexgpt")
TEMPERATURE = float(os.getenv("YANDEX_TEMPERATURE", "0.3"))
MAX_TOKENS = int(os.getenv("YANDEX_MAX_TOKENS", "2000"))

if not FOLDER_ID or not API_KEY:
    raise ValueError("Не заданы FOLDER_ID или API_KEY в .env файле")


def run_model(messages: list[dict]) -> str:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }

    yandex_messages = []
    for msg in messages:
        yandex_messages.append({
            "role": msg["role"],
            "text": msg["content"]
        })

    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{MODEL_NAME}",
        "completionOptions": {
            "stream": False,
            "temperature": TEMPERATURE,
            "maxTokens": MAX_TOKENS
        },
        "messages": yandex_messages
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result["result"]["alternatives"][0]["message"]["text"]


SkillRecommendationImpact = Literal["low"] | Literal["medium"] | Literal["high"] | Literal[""]


@dataclass(frozen=True)
class SkillRecommendation:
    title: str
    detail: str
    impact: SkillRecommendationImpact


def get_official_profession_of(profession: str) -> str:
    system_prompt = """
    Ты — строгий классификатор профессий. Твоя единственная задача: преобразовать бытовое, жаргонное или неполное название профессии в официальное наименование согласно ОКПДТР или ЕКС.

    Правила:
    1. На выходе — ТОЛЬКО официальное название профессии в именительном падеже.
    2. Запрещены: кавычки, пояснения, варианты, пометки, точка в конце.
    3. Если бытовое название соответствует нескольким должностям — выбери одну, самую распространённую.
    4. Если точного аналога нет — верни исходное название без изменений.
    5. Не добавляй лишних слов.

    Примеры:
    айтишник → Специалист по информационным технологиям
    кадровик → Специалист по кадрам
    уборщица → Уборщик служебных помещений
    продавец в магазине одежды → Продавец непродовольственных товаров
    повар в детском саду → Повар
    архитектор баз данных → Архитектор баз данных
    джава-программист → Программист
    сисадмин → Системный администратор
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": profession}
    ]
    try:
        return run_model(messages)
    except Exception:
        return profession


def get_recommendations_by(*,
                           resume: str,
                           skills: list[str],
                           vacancies: list[str]
                           ) -> tuple[list[SkillRecommendation], str]:
    vacancy_params = "\n".join(f"вакансия {i}: {line}" for i, line in enumerate(vacancies, start=1))

    system_prompt = """
    Ты — эксперт по анализу рынка труда и подбору вакансий.

    Твоя задача: проанализировать разрыв между текущими навыками пользователя и требованиями из предложенных вакансий. Верни одним выводом список из 3–7 наиболее ценных недостающих навыков, а также итоговое резюме с добавленными навыками.

    ПРАВИЛА:
    1. Отбирай навыки ТОЛЬКО из требований или желательных навыков указанных вакансий.
    2. Новый навык НЕ должен присутствовать в поле «Мои навыки».
    3. Если новых навыков больше 7 — выбери 7 самых ценных (частота, обязательность, влияние на зарплату).
    4. Если новых навыков меньше 3 — выведи все, какие есть. Если новых нет вообще — выбери от 3 до 7 самых частотных навыков из вакансий (даже если они уже есть у пользователя), но для каждого укажи impact: low и в detail объясни, что навык уже освоен, но важен для рынка.
    5. Оцени impact:
       - high: обязательный минимум в 2+ вакансиях или ключевой для всех трёх.
       - medium: желательный в 2+ или обязательный в одной.
       - low: упоминается только в одной как желательный, либо навык уже есть у пользователя.
    6. В detail укажи конкретную причину (частоту, обязательность, связь с зарплатой) со ссылкой на «в анализируемых вакансиях» или «на trudvsem.ru».

    ФОРМАТ ВЫВОДА (строго, без лишнего текста, без markdown, кроме переносов строк):
    Для каждого навыка блок:
    title: <Добавьте|Освойте|Популярен такой навык, как> <Название>
    detail: <одно предложение>
    impact: high|medium|low

    Затем пустая строка и строка:
    Исправленное резюме: <исходное резюме, но в конец списка навыков добавлены новые через запятую>

    ПРИМЕР (для трёх навыков):
    title: Освойте навык: Docker
    detail: Указан как обязательное требование во всех трёх вакансиях и влияет на зарплату на trudvsem.ru.
    impact: high

    title: Добавьте навык: SQL
    detail: Встречается как желательный плюс в двух из трёх вакансий.
    impact: medium

    title: Популярен такой навык, как Redis
    detail: Упоминается только в одной вакансии как опциональный бонус.
    impact: low

    Исправленное резюме: Я Python-разработчик, мои навыки: FastAPI, Docker, SQL, Redis

    ВАЖНО: не выводи ничего, кроме указанного формата. Количество навыков — всегда от 3 до 7.
    """

    user_message = f"""
    Резюме: {resume}
    Мои навыки: {", ".join(skills)}
    Вакансии:
    {vacancy_params}
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    try:
        text = run_model(messages)
    except Exception as e:
        print(f"Ошибка при вызове модели: {e}")
        return [], resume

    skills_pattern = r"title:\s*(.+?)\s*\n\s*detail:\s*(.+?)\s*\n\s*impact:\s*(high|medium|low)"
    skill_matches = re.findall(skills_pattern, text, re.IGNORECASE | re.DOTALL)

    new_resume_pattern = r"Исправленное резюме:\s*(.*?)(?:\n\s*(?:title|$)|$)"
    new_resume_match = re.search(new_resume_pattern, text, re.DOTALL)

    recommendations = [
        SkillRecommendation(title.strip(), detail.strip(), impact)
        for title, detail, impact in skill_matches
    ]

    new_resume = new_resume_match.group(1).strip() if new_resume_match else resume

    return recommendations, new_resume
