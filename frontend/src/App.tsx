import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

type Area = { id: string; name: string };

type SalaryRange = { low: number; median: number; high: number };

type Recommendation = {
  title: string;
  detail: string;
  impact?: string;
  skill?: string;
};

type AssessResponse = {
  salary_range_rub_gross_monthly: SalaryRange;
  method: string;
  data_source: string;
  data_source_note?: string;
  vacancies_used: number;
  vacancies_with_salary: number;
  recommendations: Recommendation[];
  search_query: string;
};

const rub = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

async function fetchAreas(): Promise<Area[]> {
  const r = await fetch("/api/areas");
  if (!r.ok) throw new Error("areas_failed");
  const j = await r.json();
  return j.items ?? [];
}

async function assess(payload: {
  role: string;
  years_experience: number;
  skills: string[];
  area: string | null;
}): Promise<AssessResponse> {
  const r = await fetch("/api/assess", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!r.ok) {
    const t = await r.text();
    throw new Error(t || "assess_failed");
  }
  return r.json();
}

export default function App() {
  const [role, setRole] = useState("Python backend разработчик");
  const [years, setYears] = useState(4);
  const [skillsText, setSkillsText] = useState(
    ["Python", "Django", "PostgreSQL", "Docker", "REST"].join("\n"),
  );
  const [area, setArea] = useState<string>("1");
  const [areas, setAreas] = useState<Area[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssessResponse | null>(null);

  useEffect(() => {
    fetchAreas()
      .then(setAreas)
      .catch(() =>
        setAreas([
          { id: "1", name: "Москва" },
          { id: "2", name: "Санкт-Петербург" },
          { id: "113", name: "Россия" },
        ]),
      );
  }, []);

  const skills = useMemo(
    () =>
      skillsText
        .split(/\n|,|;/)
        .map((s) => s.trim())
        .filter(Boolean),
    [skillsText],
  );

  const runAssess = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await assess({
        role,
        years_experience: years,
        skills,
        area: area || null,
      });
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка запроса");
    } finally {
      setLoading(false);
    }
  }, [area, role, skills, years]);

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void runAssess();
  };

  return (
    <div className="page">
      <header className="hero">
        <p className="eyebrow">Хакатон · hh.ru + ML</p>
        <h1>Рыночная стоимость резюме</h1>
        <p className="lede">
          Заполните профиль — сервис подберёт похожие вакансии на hh.ru, оценит вилку зарплат и подскажет, что
          добавить, чтобы выглядеть сильнее на рынке.
        </p>
      </header>

      <div className="layout">
        <section className="card form-card">
          <h2>Профиль</h2>
          <form onSubmit={onSubmit} className="form">
            <label className="field">
              <span>Роль / специализация</span>
              <input value={role} onChange={(e) => setRole(e.target.value)} required minLength={2} />
            </label>

            <label className="field">
              <span>Опыт, лет</span>
              <input
                type="number"
                min={0}
                max={50}
                step={0.5}
                value={years}
                onChange={(e) => setYears(Number(e.target.value))}
              />
            </label>

            <label className="field">
              <span>Регион (hh.ru)</span>
              <select value={area} onChange={(e) => setArea(e.target.value)}>
                {areas.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="field">
              <span>Навыки (с новой строки или через запятую)</span>
              <textarea
                rows={6}
                value={skillsText}
                onChange={(e) => setSkillsText(e.target.value)}
                placeholder="Python&#10;FastAPI&#10;PostgreSQL"
              />
            </label>

            <div className="actions">
              <button type="submit" className="btn primary" disabled={loading}>
                {loading ? "Считаем…" : "Оценить"}
              </button>
              {result && (
                <button type="button" className="btn ghost" disabled={loading} onClick={() => void runAssess()}>
                  Пересчитать
                </button>
              )}
            </div>
            {error && <p className="error">{error}</p>}
          </form>
        </section>

        <section className="card results">
          <h2>Результат</h2>
          {!result && (
            <p className="muted">Нажмите «Оценить», чтобы получить вилку и рекомендации на основе вакансий hh.ru.</p>
          )}
          {result && (
            <>
              <div className="range-grid">
                <div className="range-pill low">
                  <span className="lbl">Нижняя граница</span>
                  <span className="val">{rub.format(result.salary_range_rub_gross_monthly.low)}</span>
                </div>
                <div className="range-pill med">
                  <span className="lbl">Медиана</span>
                  <span className="val">{rub.format(result.salary_range_rub_gross_monthly.median)}</span>
                </div>
                <div className="range-pill high">
                  <span className="lbl">Верхняя граница</span>
                  <span className="val">{rub.format(result.salary_range_rub_gross_monthly.high)}</span>
                </div>
              </div>
              <p className="meta">
                Источник данных: <strong>{result.data_source === "hh" ? "hh.ru API" : "демо-набор (API недоступен)"}</strong>
                {" · "}
                Вакансий: {result.vacancies_used}, с зарплатой: {result.vacancies_with_salary}
                {" · "}
                Метод: {result.method}
              </p>
              {result.data_source_note && <p className="meta warn">{result.data_source_note}</p>}
              <p className="meta subtle">Запрос к hh.ru: «{result.search_query}»</p>

              <h3>Рекомендации</h3>
              <ul className="recs">
                {result.recommendations.map((r, i) => (
                  <li key={i} className={`rec impact-${r.impact ?? "medium"}`}>
                    <div className="rec-title">{r.title}</div>
                    <div className="rec-detail">{r.detail}</div>
                  </li>
                ))}
              </ul>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
