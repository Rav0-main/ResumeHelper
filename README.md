# 💼 ResumeHelper — Оцени свою рыночную стоимость за 5 минут

> **Хакатон Т-Банка**
> *Сервис, который по резюме предсказывает вилку дохода и даёт персональные рекомендации для роста.*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.0-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini_2.5_Flash-4285F4?logo=google&logoColor=white)](https://aistudio.google.com/apikey?hl=ru&_gl=1*1jdxyoq*_ga*MTY2NjUyNzAxMC4xNzc5MDE3OTUy*_ga_P1DBVKWT6V*czE3NzkwNDEzODIkbzMkZzEkdDE3NzkwNDE0MTUkajI3JGwwJGgxOTk2MjY1MTY5)
[![Frontend](https://img.shields.io/badge/HTML5/CSS3/JS-57A1F2?logo=html5)](/frontend/)
[![nginx](https://img.shields.io/badge/nginx-1.26.2-009639?logo=nginx&logoColor=white&labelColor=1a5b2a)](https://nginx.org)

---

## 🔍 Проблема

Многие соискатели **не знают реальной рыночной стоимости** своих навыков:

- Занижают зарплату → теряют деньги  
- Завышают ожидания → получают отказы  
- Резюме составлено плохо: мало конкретики, не хватает ключевых навыков, опыт описан невнятно  

**Результат** – потерянные возможности и несправедливая зарплата.

---

## 💡 Решение

**ResumeHelper** – это AI‑сервис, который:

1. Анализирует твоё резюме (роль, опыт, навыки, резюме).  
2. Находит **похожие вакансии** в датасете российского рынка.  
3. Предсказывает **вилку дохода** (от – до руб.)  
4. Даёт **конкретные рекомендации**, что добавить или изменить.  
5. Позволяет **пересчитать** результат после правок – вилка растёт!

> 🎯 **Цель** – помочь соискателю быстро понять свою ценность и научить улучшать резюме для роста дохода.

## 🛠️ Технологический стек

| Компонент          | Технологии                            |
|:--------------------:|:---------------------------------------:|
| **Backend**        | Python 3.12, FastAPI, httpx, Pydantic, OpenAI|
| **AI**       | Gemini API   |
| **Данные**         | API Работа России                     |
| **Frontend**       | HTML5, CSS, Vanilla JS                |
| **Инфраструктура** | Uvicorn, CORS middleware, env‑конфиги, nginx |

---

## 📁 Структура проекта

```
ResumeHelper/
├── backend/
│   ├── services/
│   │   ├── vacancies.py        # обратывает вакансии с trudvsem.ru
│   │   └── llm.py              # выполняет анализ резюме и даёт рекомендации
│   ├── recommendations.py      # основной контроллер для рекомендаций
│   ├── main.py                 # обработка запросов
│   └── requirements.txt        # python зависимости
├── frontend/
│   ├── css/style.css
│   ├── js/app.js
│   └── index.html
├── .env.example
├── .gitignore
├── nginx.conf.example
├── LICENSE
└── README.md
```

---

## API-endpoints

- `GET /api/v1/hello_girl` — проверка "живности" сервера.
**Ответ**:
```json
{
  "title": "Hi. My name is Poli...",
  "detail": "OK"
}
```

- `POST /api/v1/recommendations` — получение рекомендации на основе данных.
**Запрос**:
```json
{
  "role": String,
  "years_experience": Integer,
  "skills": String,
  "resume": String
}
```

**Ответ**:
- **HTTP 200**
```json
{
  "salary_range_rub_gross_monthly": {
    "low": Integer,
    "median": Integer,
    "high": Integer
  },

  "method": String,
  
  "data_source": String,
  "data_source_note": String,
  
  "vacancies_used": Integer,
  "vacancies_with_salary": Integer,
  
  "recommendations": [
    {
      "title": String,
      "detail": String,
      "impact": String
    }
  ]
}
```

- **Иначе**

`Стандартные коды ошибок HTTP.`

---

## 🚀 Как запустить?

### 1. Клонирование репозитория

```bash
git clone https://github.com/Rav0-main/ResumeHelper.git
cd ResumeHelper
```

### 2. Настройка окружения

#### .env

Создайте файл `.env` в корне проекта по примеру из [.env.example](/.env.example).
Для `Gemini`: 
```bash
API_KEY="ВАШ_API_КЛЮЧ"
AI_API_URL="https://generativelanguage.googleapis.com/v1beta/openai/"
```

#### API-ключ Gemini

`API-ключ` можно получить с официального сайта Google или [отсюда](#https://aistudio.google.com/apikey?hl=ru&_gl=1*1c3h835*_ga*MTY2NjUyNzAxMC4xNzc5MDE3OTUy*_ga_P1DBVKWT6V*czE3NzkwNDEzODIkbzMkZzEkdDE3NzkwNDE0MTUkajI3JGwwJGgxOTk2MjY1MTY5).

### 3. Установка зависимостей backend'a

```bash
python -m venv venv

source venv/bin/activate   # Linux/Mac
# или .\venv\Scripts\activate  (Windows)

pip install -r requirements.txt
```

### 4. Запуск application-сервера

```bash
cd backend
python main.py
```

### 5. Запуск web-сервера

Настройте конфигурацию `nginx.conf` по примеру из [nginx.conf.example](/nginx.conf.example).
Требуется просто поменять директорию фронтенда (19 строка), т.е. `/.../fronted/`.

---

## 🎮 Как использовать (скриншоты)

1. **Форма резюме** – заполните поля (роль, опыт, навыки, регион).
2. **Результат** – вилка дохода и список советов
3. **Улучшайте** – добавьте один недостающий навык, нажмите «Пересчитать».

---

## 🧪 Генерация рекомендаций через OpenAI
 
Промпт формируется из текущего резюме + списка недостающих навыков, найденных в похожих вакансиях.

**Преимущества подхода:**  
- Естественный язык без шаблонов.
- Адаптация под конкретную роль.
- Возможность объяснить **почему** добавление навыка повлияет на зарплату.

---

## 🔮 Перспективы развития

- Автоматическое улучшение резюме (генерация готового текста) 
- Дашборд сравнения с рынком по городам и грейдам
- Интеграция с hh.ru – загрузка резюме по ссылке 
- Мобильное приложение (React Native)

---

## 👥 Команда

> *Сборная УгаБуга*
> Участники хакатона Т-Банка

---

## 📄 Лицензия

MIT – свободно используйте, дорабатывайте, вдохновляйтесь.

---
