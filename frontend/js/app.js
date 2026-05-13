const BACKEND_URL = 'http://127.0.0.1:8000';

const resumeForm = document.getElementById('resumeForm');
const submitBtn = document.getElementById('submitBtn');
const btnText = document.getElementById('btnText');
const spinner = document.getElementById('spinner');

const resultBox = document.getElementById('resultBox');
const positionTitle = document.getElementById('positionTitle');
const salaryRange = document.getElementById('salaryRange');
const recList = document.getElementById('recList');
const recalcBtn = document.getElementById('recalcBtn');

resumeForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const payload = {
        fullName: document.getElementById('fullName').value,
        targetJob: document.getElementById('targetJob').value,
        experienceYears: parseFloat(document.getElementById('experienceYears').value),
        skillsText: document.getElementById('skillsText').value,
        experienceText: document.getElementById('experienceText').value
    };

    submitBtn.disabled = true;
    btnText.style.display = 'none';
    spinner.style.display = 'block';

    try {
        const response = await fetch(`${BACKEND_URL}/api/analyze`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Ошибка сервера при анализе');
        }

        const data = await response.json();

        positionTitle.innerText = `Определенная позиция: ${data.position}`;
        salaryRange.innerText = `${data.salary_min.toLocaleString('ru-RU')} — ${data.salary_max.toLocaleString('ru-RU')} ₽`;

        recList.innerHTML = '';
        data.recommendations.forEach(rec => {
            const li = document.createElement('li');
            li.innerText = rec;
            recList.appendChild(li);
        });

        resumeForm.style.display = 'none';
        resultBox.style.display = 'block';

    } catch (error) {
        alert(`Произошла ошибка: ${error.message}\nУбедитесь, что сервер main.py запущен локально.`);
    } finally {
        submitBtn.disabled = false;
        btnText.style.display = 'inline';
        spinner.style.display = 'none';
    }
});

recalcBtn.addEventListener('click', () => {
    resultBox.style.display = 'none';
    resumeForm.style.display = 'block';
});
