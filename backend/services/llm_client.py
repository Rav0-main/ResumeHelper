import asyncio
from transformers import pipeline
from backend.schemas.resume import ResumeInput


class LocalMLService:
    def __init__(self):
        print("🤖 Загрузка бесплатной локальной ИИ-модели классификации...")
        # Используем легковесную модель для анализа текста, которая быстро работает на CPU
        self.classifier = pipeline(
            "zero-shot-classification",
            model="Babelscape/wikineural-multilingual-ner"
        )

        # Экспертная матрица рынка труда для распределения по секторам экономики
        self.market_sectors = {
            "Разработка ПО и IT": {"base_salary": 120000,
                                   "skills": ["python", "git", "sql", "api", "docker", "linux", "js", "ci/cd"]},
            "Маркетинг, Маркетплейсы и Дизайн": {"base_salary": 85000,
                                                 "skills": ["figma", "seo", "smm", "ads", "analytics", "copywriting"]},
            "Управление проектами и Аналитика": {"base_salary": 140000,
                                                 "skills": ["scrum", "agile", "jira", "sql", "tableau", "excel",
                                                            "python"]},
            "Финансы, Юриспруденция и Бухгалтерия": {"base_salary": 75000,
                                                     "skills": ["1с", "excel", "аудит", "налоги", "p&l", "договоры"]}
        }

    async def analyze_resume(self, data: ResumeInput) -> dict:
        # Переносим вычисления модели в пул потоков, чтобы FastAPI работал асинхронно и не блокировался
        loop = asyncio.get_event_loop()
        labels = list(self.market_sectors.keys())

        def run_inference():
            return self.classifier(data.targetJob, candidate_labels=labels)

        res = await loop.run_in_executor(None, run_inference)

        # Определяем сектор с наивысшим совпадением
        matched_cluster = res['labels'][0]
        cluster_info = self.market_sectors[matched_cluster]

        # Проверяем совпадение навыков кандидата с требованиями рынка
        user_skills_lower = data.skillsText.lower()
        matched_skills = [s for s in cluster_info["skills"] if s in user_skills_lower]
        missing_skills = [s for s in cluster_info["skills"] if s not in user_skills_lower]

        # Алгоритм расчета финансовой вилки на основе опыта и навыков
        experience_factor = 1.0 + min(1.5, data.experienceYears * 0.18)
        skills_factor = 0.75 + (0.25 * (len(matched_skills) / max(1, len(cluster_info["skills"]))))

        calculated_base = cluster_info["base_salary"] * experience_factor * skills_factor
        salary_min = int(calculated_base * 0.85)
        salary_max = int(calculated_base * 1.25)

        # Формирование персональных рекомендаций
        recommendations = [
            f"Локальный ИИ отнес вашу профессию к сектору: '{matched_cluster}'."
        ]

        if missing_skills:
            recommendations.append(
                f"Для увеличения дохода рекомендуем освоить и указать в резюме ключевые навыки: {', '.join(missing_skills[:3]).upper()}."
            )
        else:
            recommendations.append("У вас указан отличный технологический базис для выбранного направления.")

        if len(data.experienceText.split()) < 15:
            recommendations.append(
                "Описание проектов выглядит коротким. Распишите достижения по методологии STAR (Ситуация, Задача, Действие, Результат).")

        if data.experienceYears == 0:
            recommendations.append(
                "При отсутствии коммерческого стажа делайте упор на учебную практику, дипломные проекты и хакатоны.")

        return {
            "position": f"{data.targetJob} ({matched_cluster})",
            "salary_min": max(35000, salary_min),
            "salary_max": max(50000, salary_max),
            "recommendations": recommendations
        }


llm_service = LocalMLService()
