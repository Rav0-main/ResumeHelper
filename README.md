# Рыночная стоимость резюме

Сервис для хакатона: по введённому профилю (роль, опыт, навыки, регион) подбираются **похожие вакансии с [hh.ru](https://api.hh.ru)**, считается **вилка зарплаты** (нижняя / медиана / верхняя) и выдаются **рекомендации**, как усилить профиль. При недоступности API можно работать на **демо-наборе** вакансий.

---

## Возможности

| | |
| :--- | :--- |
| **Оценка** | Перцентили по зарплатам из выборки вакансий в **RUR gross / месяц** |
| **Рекомендации** | Навыки из вакансий с более высокой медианой, которых нет в вашем списке |
| **Пересчёт** | Обновили навыки или описание — снова «Оценить» / «Пересчитать» |
| **ML (опционально)** | Скрипт обучения `RandomForest` + TF‑IDF по текстам вакансий → файл `backend/models/salary_model.joblib` и лёгкий blend с вилкой по вакансиям |

---

## Стек

- **Backend:** Python 3.11+, FastAPI, httpx, numpy, scikit-learn  
- **Frontend:** React 18, TypeScript, Vite 6  
- **Данные:** публичный API hh.ru (`/vacancies`, `/areas`)

---

## Быстрый старт

### 1. Зависимости

```bash
pip install -r requirements.txt
npm install --prefix frontend
```

Или из корня: `npm run install:frontend` (только фронт).

### 2. Переменные окружения

```bash
cp .env.example .env
```

В PowerShell: `Copy-Item .env.example .env`

Отредактируйте **`.env`**: для реальных запросов к hh.ru обязательно укажите **`HH_USER_AGENT`** в формате, который требует API, например:

`MyTeam-ResumeApp/1.0 (your.email@domain.com)`

### 3. Запуск

**Вариант A — один процесс (бэкенд + фронт):**

```bash
python scripts/dev.py
```

**Вариант B — только API или только UI:**

```bash
python scripts/dev.py --backend-only
python scripts/dev.py --frontend-only
```

**Вариант C — через npm** (подберётся `python3` / `python` / на Windows `py -3`):

```bash
npm run dev
npm run dev:backend
npm run dev:frontend
```

Полезные флаги:

| Команда | Назначение |
| :--- | :--- |
| `python scripts/dev.py --port 8787` | Порт API (если `8000` занят или WinError 10013) |
| `python scripts/dev.py --install` | Перед фронтом выполнить `npm install` в `frontend/` |
| `python scripts/dev.py --frontend-only --install` | То же, только фронт |

После старта:

- **UI:** [http://127.0.0.1:5173](http://127.0.0.1:5173) или [http://localhost:5173](http://localhost:5173) (как в выводе Vite)  
- **API:** [http://127.0.0.1:8000](http://127.0.0.1:8000) (или ваш `BACKEND_PORT`)  
- **Swagger:** `http://127.0.0.1:8000/docs`

---

## Переменные `.env`

| Переменная | Описание |
| :--- | :--- |
| `HH_USER_AGENT` | Строка для заголовков `User-Agent` и `HH-User-Agent` при запросах к hh.ru |
| `USE_MOCK_ON_HH_FAILURE` | `true` — при ошибке API подставляются демо-вакансии; `false` — ошибка пробрасывается клиенту |
| `BACKEND_PORT` | Порт uvicorn (по умолчанию `8000`; Vite читает это значение из корня репозитория для прокси `/api`) |

---

## HTTP API (кратко)

| Метод | Путь | Описание |
| :--- | :--- | :--- |
| `GET` | `/` | Сводка сервиса и ссылки |
| `GET` | `/health` | Проверка живости |
| `GET` | `/api/areas` | Список регионов (id для формы) |
| `POST` | `/api/assess` | Тело JSON: `role`, `years_experience`, `skills[]`, `area` (id hh.ru) |

Пример тела для `/api/assess`:

```json
{
  "role": "Python backend разработчик",
  "years_experience": 4,
  "skills": ["Python", "FastAPI", "PostgreSQL"],
  "area": "1"
}
```

В ответе при демо-режиме может быть поле **`data_source_note`** — краткая причина, почему не использованы живые данные hh.ru.

---

## Обучение ML-модели (опционально)

Из корня репозитория (нужен доступ к API hh или сработает fallback на демо):

```bash
python scripts/train_model.py --text "Python разработчик" --area 1 --pages 3
```

Модель сохраняется в `backend/models/salary_model.joblib`. Если файл есть, оценка может слегка **смешиваться** с перцентилями по вакансиям.

---

## Структура репозитория

```
t-bank/
├── backend/           # FastAPI, клиент hh.ru, оценка, моки
│   └── models/        # salary_model.joblib (после train_model)
├── frontend/          # React + Vite
├── scripts/
│   ├── dev.py         # Кроссплатформенный dev (бэкенд / фронт / оба)
│   ├── call-dev.mjs   # Обёртка для npm run dev
│   └── train_model.py # Обучение модели по вакансиям
├── requirements.txt
├── package.json
├── .env.example
└── README.md
```

---

## Частые проблемы

1. **`bad_user_agent` / 403 от hh.ru** — задайте корректный **`HH_USER_AGENT`** с реальным контактом в скобках (см. [документацию hh](https://github.com/hhru/api)).  
2. **WinError 10013 на порту 8000** — задайте **`BACKEND_PORT`** (например `8787`) или флаг `--port`.  
3. **`vite` is not recognized** — выполните `npm install` в каталоге **`frontend/`** или `python scripts/dev.py --frontend-only --install`.  
4. **`ERR_CONNECTION_REFUSED` на 5173** — убедитесь, что Vite запущен; в конфиге включён `host: true` для совместимости `localhost` и `127.0.0.1`.  
5. **Демо вместо hh** — проверьте сеть, VPN, регион; при `USE_MOCK_ON_HH_FAILURE=false` в ответе API увидите сырую ошибку.

---

## Лицензия

Проект создан в учебных / хакатонных целях. Использование данных и API — в соответствии с [правилами hh.ru](https://dev.hh.ru/).
