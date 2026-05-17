"use strict";

const rubFormatter = new Intl.NumberFormat("ru-RU", {
  style: "currency",
  currency: "RUB",
  maximumFractionDigits: 0,
});

const recommendationsForm = document.getElementById("assessForm");
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
const newResumeContainer = document.getElementById("newResumeContainer");

//Состояние прилы
let isLoading = false;
let currentResult = null;

async function fetchRecommendationsOf(payload) {
  const response = await fetch("/api/v1/recommendations", {
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

function parseSkills(skillsText) {
  return skillsText
    .split(/\n|,|;/)
    .map((s) => s.trim())
    .filter(Boolean);
}

//Ошибки
function showError(message) {
  errorMsg.textContent = message;
  errorMsg.style.display = "block";
}

function hideError() {
  errorMsg.style.display = "none";
}

//Ожидание (загрузка)
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

function displayResults(result) {
  currentResult = result;
  placeholderText.style.display = "none";
  resultContainer.style.display = "block";
  recalcBtn.style.display = "inline-block";

  //Зарплата
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

  //Metadata
  const dataSourceLabel = result.data_source;
  metaInfo.innerHTML = `
    Источник данных: <strong>${dataSourceLabel}</strong>
    · Вакансий: ${result.vacancies_used}, с зарплатой: ${result.vacancies_with_salary}
    · Метод: ${result.method}
  `;

  //Внимание
  if (result.data_source_note) {
    metaWarn.textContent = result.data_source_note;
    metaWarn.style.display = "block";
  } else {
    metaWarn.style.display = "none";
  }

  //Запрос
  queryInfo.textContent = `Запрос к trudvsem.ru: «${result.search_query}»`;

  //Рекомендации
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

  //Исправленное резюме
  if (result.new_resume) {
    newResumeContainer.textContent = result.new_resume;
    newResumeContainer.style.display = "block";
  } else {
    newResumeContainer.style.display = "none";
  }
}

function clearResults() {
  currentResult = null;
  placeholderText.style.display = "block";
  resultContainer.style.display = "none";
  recalcBtn.style.display = "none";
}

//Загрузка рекомендаций
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
    showError("Произошла ошибка. Попробуйте снова.");
    clearResults();
  } finally {
    setLoading(false);
  }
}

//main
recommendationsForm.addEventListener("submit", handleSubmit);
recalcBtn.addEventListener("click", handleSubmit);
