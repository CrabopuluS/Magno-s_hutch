import { getApiBase, setApiBase } from './utils.js';

const apiInput = document.getElementById('apiBase');
const btnSave = document.getElementById('saveApi');
const btnReload = document.getElementById('reload');
const fromEl = document.getElementById('from');
const toEl = document.getElementById('to');

apiInput.value = getApiBase();

btnSave.addEventListener('click', () => {
  setApiBase(apiInput.value.trim() || 'http://localhost:8000');
  alert('API base saved.');
});

function defaultDates() {
  const today = new Date();
  const start = new Date(today.getTime() - 6*86400000); // last 7 days
  toEl.valueAsDate = today;
  fromEl.valueAsDate = start;
}
defaultDates();

let dailyChart, histChart;

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

function drawDaily(data) {
  const labels = data.map(d => d.date);
  const plays = data.map(d => d.plays_count);
  const avgScore = data.map(d => d.avg_score);
  const avgDur = data.map(d => d.avg_session_sec);
  const users = data.map(d => d.unique_users);

  if (dailyChart) dailyChart.destroy();
  const ctx = document.getElementById('dailyChart').getContext('2d');
  dailyChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        { label: 'Plays', data: plays },
        { label: 'Avg Score', data: avgScore },
        { label: 'Avg Session (sec)', data: avgDur },
        { label: 'Unique Users', data: users },
      ]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

function drawHist(bins) {
  const labels = bins.map(b => `${b.from}–${b.to}`);
  const counts = bins.map(b => b.count);

  if (histChart) histChart.destroy();
  const ctx = document.getElementById('histChart').getContext('2d');
  histChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{ label: 'Sessions by duration (sec)', data: counts }]
    },
    options: { responsive: true, maintainAspectRatio: false }
  });
}

async function reload() {
  const api = getApiBase();
  const from = fromEl.value;
  const to = toEl.value;
  const daily = await fetchJSON(`${api}/metrics/daily?from=${from}&to=${to}`);
  const hist = await fetchJSON(`${api}/metrics/session-hist?bins=10`);
  drawDaily(daily);
  drawHist(hist);
}

btnReload.addEventListener('click', reload);

// initial load
reload();
