
# ResumeHelper

**ИИ-инструмент для оценки рыночной стоимости резюме и рекомендаций по его улучшению**

> Решение кейса «Заработок» — хакатон Т-Банк × МГТУ им. Н.Э. Баумана 2026

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg)](https://www.python.org)

[![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688.svg)](https://fastapi.tiangolo.com)

---

## О проекте

ResumeHelper — бэкенд-сервис, который по введённым данным резюме (должность, опыт, навыки, регион, текст резюме) формирует **зарплатную вилку** и **персонализированные рекомендации** по улучшению резюме.

Проект использует реальные вакансии с портала trudvsem.ru и LLM (Gemini) для анализа и генерации рекомендаций.

---

## Возможности

- Получение списка популярных регионов РФ
- Приём данных резюме (роль, годы опыта, навыки, регион, текст резюме)
- Поиск релевантных вакансий через API trudvsem.ru
- Нормализация названия профессии в официальное (ОКПДТР / ЕКС) с помощью LLM
- Генерация рекомендаций по улучшению резюме и улучшенной версии резюме
- Возврат структурированной зарплатной вилки (low / median / high)
- CORS-поддержка для фронтенда

---

## Технологический стек

- **Язык**: Python 3.11+
- **Фреймворк**: FastAPI
- **LLM**: OpenAI-совместимый клиент (Gemini через custom base_url)
- **HTTP**: httpx
- **Валидация**: Pydantic v2
- **ASGI-сервер**: Uvicorn
- **Другое**: python-dotenv, scikit-learn, pandas, numpy

---

## 📁 Структура проекта

```bash
ResumeHelper/
├── backend/                          # Backend-часть (FastAPI)
│   ├── main.py                       # FastAPI приложение и эндпоинты
│   ├── recommendations.py            # Основная бизнес-логика
│   ├── placements.py                 # Статические данные регионов
│   ├── services/
│   │   ├── llm.py                    # Сервис работы с LLM (Gemini)
│   │   ├── vacancies.py              # Сервис поиска вакансий
│   │   └── .env.example
│   └── requirements.txt
│
├── frontend/                         # Frontend-часть (Vanilla JS)
│   ├── index.html
│   ├── css/
│   └── js/
│
├── .env.example
├── nginx.conf.example
└── README.md
```

---

## Основные API эндпоинты

- `GET /api/v1/placements` — возвращает список регионов
- `POST /api/v1/recommendations` — основной эндпоинт  
  Тело запроса (`RecommendationRequest`):
  - `role` — должность
  - `years_experience` — опыт в годах
  - `skills` — список навыков
  - `placement` — регион (опционально)
  - `resume` — текст резюме (опционально)

---

## Быстрый запуск

### 1. Клонирование и переход на dev-ветку

```bash
git clone https://github.com/Rav0-main/ResumeHelper.git
cd ResumeHelper
git checkout dev
```

### 2. Backend

```bash
cd backend

# Установка зависимостей
pip install -r requirements.txt

# Настройка API-ключа
cp services/.env.example services/.env
# Отредактируйте services/.env — укажите API_KEY и AI_API_URL
```

```bash
# Запуск
cd backend && python main.py
# или
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер запускается на `http://localhost:8000`

### Frontend

Поднимите статический сервер (рекомендуется Nginx с конфигом `nginx.conf.example`).

---

## Архитектура

- `main.py` — входная точка, FastAPI-приложение, модели запросов, CORS
- `recommendations.py` — оркестратор: собирает вакансии + вызывает LLM
- `services/vacancies.py` — взаимодействие с API trudvsem.ru
- `services/llm.py` — работа с Gemini (нормализация профессии + генерация рекомендаций)
- `placements.py` — статический справочник регионов для скорости

---

## Лицензия

Проект распространяется под лицензией **MIT** (см. файл [LICENSE](LICENSE)).

---

**Сделано на хакатоне Т-Банк × МГТУ им. Баумана 2026**
