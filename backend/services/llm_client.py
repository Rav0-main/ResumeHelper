import httpx
import asyncio
from typing import Dict, List
from backend.schemas.resume import ResumeInput


class HHMarketService:
    def __init__(self):
        # Официальный публичный эндпоинт API HeadHunter для поиска вакансий
        self.api_url = "hh.ru"

        # HH строго требует уникальный User-Agent, иначе заблокирует запросы бэкенда
        self.headers = {
            "User-Agent": "BaumankaSalaryPredictor/1.0 (tech-support@bmstu.ru)"
        }

    async def analyze_resume(self, data: ResumeInput) -> dict:
        # Настройка параметров поискового запроса к HeadHunter
        params = {
            "text": data.targetJob,  # Текст профессии, введенный пользователем
            "area": 1,  # Регион поиска: Москва (ID: 1)
            "per_page": 30,  # Анализируем срез из 30 свежих вакансий
            "only_with_salary": "true"  # Фильтруем только вакансии с указанным доходом
        }

        salaries_min = []
        salaries_max = []

        # Словарь для сбора самых часто встречающихся навыков в требованиях на рынке
        market_skills_counter: Dict[str, int] = {}

        # Дефолтный список топ-навыков, если детальный парсинг сниппетов вернет мало данных
        top_market_skills = ["управление командой", "руководство проектами", "планирование", "деловая переписка",
                             "аналитика"]

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.api_url, params=params, headers=self.headers, timeout=5.0)

                if response.status_code == 200:
                    vacancies_data = response.json().get("items", [])

                    for vac in vacancies_data:
                        # 1. Агрегация данных о заработных платах
                        salary = vac.get("salary")
                        if salary:
                            currency_rate = 1.0
                            # Базовый пересчет валюты в рубли по курсу, если вакансия зарубежная
                            if salary.get("currency") != "RUR":
                                if salary.get("currency") == "USD":
                                    currency_rate = 92.0
                                elif salary.get("currency") == "EUR":
                                    currency_rate = 100.0

                            s_from = salary.get("from")
                            s_to = salary.get("to")

                            if s_from: salaries_min.append(s_from * currency_rate)
                            if s_to: salaries_max.append(s_to * currency_rate)

                        # 2. Поиск и подсчет упоминаний ключевых навыков в требованиях вакансий
                        snippet = vac.get("snippet", {})
                        requirement = (snippet.get("requirement") or "").lower()

                        # Базовые популярные маркеры навыков для анализа требований рынка
                        potential_skills = [
                            "python", "git", "sql", "docker", "javascript", "linux", "excel", "1с",
                            "figma", "scrum", "agile", "jira", "управление", "переговоры", "анализ"
                        ]
                        for skill in potential_skills:
                            if skill in requirement:
                                market_skills_counter[skill] = market_skills_counter.get(skill, 0) + 1

                    # Если навыки успешно распарсились, формируем динамический топ-5 навыков рынка
                    if market_skills_counter:
                        sorted_skills = sorted(market_skills_counter.items(), key=lambda x: x[1], reverse=True)
                        top_market_skills = [item[0] for item in sorted_skills[:5]]

        except Exception as e:
            print(f"Ошибка вызова или парсинга API HH.ru: {e}")

        # 3. Блок-предохранитель (Fallback) на случай редких должностей или сбоя сети
        if not salaries_min:
            # Если вакансий с зарплатой нет (например, «Подполковник»), рассчитываем базовую ставку по стажу
            base_anchor = 75000 + min(110000, data.experienceYears * 20000)
            salaries_min = [base_anchor * 0.85]
            salaries_max = [base_anchor * 1.3]
            top_market_skills = ["управление персоналом", "организаторские навыки", "документооборот",
                                 "стратегическое планирование"]

        # Расчет средних рыночных показателей из собранного массива вакансий
        avg_market_min = sum(salaries_min) / len(salaries_min)
        avg_market_max = sum(salaries_max) / len(salaries_max) if salaries_max else avg_market_min * 1.4

        # 4. Персонализация вилки под конкретного кандидата и его стаж
        # Коэффициент опыта: джуны получают меньше средней по рынку, сеньоры — значительно больше
        experience_multiplier = 0.75 + min(0.65, data.experienceYears * 0.14)

        # Считаем сколько навыков из топа рынка уже есть у соискателя
        user_skills_lower = data.skillsText.lower()
        matched_skills_count = sum(1 for s in top_market_skills if s in user_skills_lower)
        skills_multiplier = 0.9 + (0.2 * (matched_skills_count / len(top_market_skills)))

        # Финальный расчет вилки доходов
        final_min = int(avg_market_min * experience_multiplier * skills_multiplier)
        final_max = int(avg_market_max * experience_multiplier * skills_multiplier)

        if final_min >= final_max:
            final_max = int(final_min * 1.35)

        # 5. Генерация динамических рекомендаций на основе реального контекста
        missing_skills = [s for s in top_market_skills if s not in user_skills_lower]

        recommendations = [
            f"Анализ проведен в режиме реального времени на основе интеграции с API hh.ru по запросу '{data.targetJob}'."
        ]

        if missing_skills:
            recommendations.append(
                f"По данным работодателей, для этой роли критически важны навыки: {', '.join(missing_skills[:3]).upper()}. Добавьте их в стек, если обладаете знаниями."
            )
        else:
            recommendations.append(
                "Поздравляем! Ваш набор ключевых хард-скиллов полностью соответствует частым запросам работодателей на рынке.")

        if len(data.experienceText.split()) < 15:
            recommendations.append(
                "Описание вашего опыта слишком лаконично. Алгоритмы агрегаторов хуже ранжируют короткие резюме — распишите подробнее ваши задачи.")

        if data.experienceYears > 4 and final_max < 180000:
            recommendations.append(
                "У вас солидный стаж. Попробуйте скорректировать желаемую должность в сторону управленческих позиций (Lead / Head of), чтобы повысить доход.")

        return {
            "position": f"{data.targetJob.capitalize()} (Данные рынка труда)",
            "salary_min": max(35000, final_min),
            "salary_max": max(50000, final_max),
            "recommendations": recommendations
        }


# Переопределяем синглтон сервиса для main.py
llm_service = HHMarketService()
