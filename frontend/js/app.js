// Currency formatter for Russian Rubles
const rubFormatter = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

// DOM elements
const assessForm = document.getElementById("assessForm");
const roleInput = document.getElementById("roleInput");
const yearsInput = document.getElementById("yearsInput");
const resumeInput = document.getElementById("resumeInput");
const skillsInput = document.getElementById("skillsInput");
const submitBtn = document.getElementById("submitBtn");
const btnText = document.getElementById("btnText");
const spinner = document.getElementById("spinner");
const recalcBtn = document.getElementById("recalcBtn");
const errorMsg = document.getElementById("errorMsg");
const placeholderText = document.getElementById("placeholderText");
const resultContainer = document.getElementById("resultContainer");
const rangeGrid = document.getElementById("rangeGrid");
const metaInfo = document.getElementById("metaInfo");
const metaWarn = document.getElementById("metaWarn");
const queryInfo = document.getElementById("queryInfo");
const recommendationsList = document.getElementById("recommendationsList");

// App state
let isLoading = false;
let currentResult = null;

// API functions
async function fetchPlacements() {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/v1/placements");
    if (!response.ok) throw new Error("placements_failed");
    const data = await response.json();
    return data.items ?? [];
  } catch (e) {
    console.error("Failed to fetch placements:", e);
    return [];
  }
}

async function fetchRecommendationsOf(payload) {
  const response = await fetch("http://127.0.0.1:8000/api/v1/recommendations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "recommendations_failed");
  }

  return response.json();
}

// Parse skills from textarea
function parseSkills(skillsText) {
  return skillsText
    .split(/\n|,|;/)
    .map((s) => s.trim())
    .filter(Boolean);
}

// Display error message
function showError(message) {
  errorMsg.textContent = message;
  errorMsg.style.display = "block";
}

// Hide error message
function hideError() {
  errorMsg.style.display = "none";
}

// Update UI loading state
function setLoading(loading) {
  isLoading = loading;
  submitBtn.disabled = loading;
  recalcBtn.disabled = loading;
  roleInput.disabled = loading;
  yearsInput.disabled = loading;
  skillsInput.disabled = loading;

  if (loading) {
    btnText.style.display = "none";
    spinner.style.display = "inline-block";
  } else {
    btnText.style.display = "inline";
    spinner.style.display = "none";
  }
}

// Display results
function displayResults(result) {
  currentResult = result;
  placeholderText.style.display = "none";
  resultContainer.style.display = "block";
  recalcBtn.style.display = "inline-block";

  // Display salary range
  rangeGrid.innerHTML = `
    <div class="range-pill low">
      <span class="lbl">Нижняя граница</span>
      <span class="val">${rubFormatter.format(result.salary_range_rub_gross_monthly.low)}</span>
    </div>
    <div class="range-pill med">
      <span class="lbl">Медиана</span>
      <span class="val">${rubFormatter.format(result.salary_range_rub_gross_monthly.median)}</span>
    </div>
    <div class="range-pill high">
      <span class="lbl">Верхняя граница</span>
      <span class="val">${rubFormatter.format(result.salary_range_rub_gross_monthly.high)}</span>
    </div>
  `;

  // Display metadata
  const dataSourceLabel = result.data_source;
  metaInfo.innerHTML = `
    Источник данных: <strong>${dataSourceLabel}</strong>
    · Вакансий: ${result.vacancies_used}, с зарплатой: ${result.vacancies_with_salary}
    · Метод: ${result.method}
  `;

  // Display warning if present
  if (result.data_source_note) {
    metaWarn.textContent = result.data_source_note;
    metaWarn.style.display = "block";
  } else {
    metaWarn.style.display = "none";
  }

  // Display search query
  queryInfo.textContent = `Запрос к trudvsem.ru: «${result.search_query}»`;

  // Display recommendations
  recommendationsList.innerHTML = result.recommendations
    .map((rec, i) => {
      const impact = rec.impact || "medium";
      return `
        <li class="rec impact-${impact}">
          <div class="rec-title">${rec.title}</div>
          <div class="rec-detail">${rec.detail}</div>
        </li>
      `;
    })
    .join("");
}

// Clear results
function clearResults() {
  currentResult = null;
  placeholderText.style.display = "block";
  resultContainer.style.display = "none";
  recalcBtn.style.display = "none";
}

// Handle form submission
async function handleSubmit(e) {
  e.preventDefault();
  hideError();
  setLoading(true);

  try {
    const payload = {
      role: roleInput.value,
      years_experience: parseFloat(yearsInput.value),
      skills: parseSkills(skillsInput.value),
      area: null,
      resume: resumeInput.value || null
    };

    const result = await fetchRecommendationsOf(payload);
    displayResults(result);
  } catch (e) {
    const message =
      e instanceof Error ? e.message : "Ошибка запроса";
    showError(message);
    clearResults();
  } finally {
    setLoading(false);
  }
}

// Handle recalculate button
function handleRecalculate() {
  handleSubmit(new Event("submit"));
}

// Initialize
assessForm.addEventListener("submit", handleSubmit);
recalcBtn.addEventListener("click", handleRecalculate);

// Load areas when page loads
document.addEventListener("DOMContentLoaded", () => {
  loadPlacements();
});
