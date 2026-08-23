// Sidebar toggle (mobile)
document.addEventListener('DOMContentLoaded', function () {
  const sidebar = document.querySelector('.sidebar');
  const backdrop = document.querySelector('.sidebar-backdrop');
  const burger = document.querySelector('.hamburger');
  if (burger) {
    burger.addEventListener('click', () => {
      sidebar.classList.toggle('open');
      if (backdrop) backdrop.classList.toggle('show');
    });
  }
  if (backdrop) {
    backdrop.addEventListener('click', () => {
      sidebar.classList.remove('open');
      backdrop.classList.remove('show');
    });
  }

  // Auto-dismiss flash messages
  document.querySelectorAll('[data-autohide]').forEach((el) => {
    setTimeout(() => { el.style.transition = 'opacity .4s'; el.style.opacity = '0';
      setTimeout(() => el.remove(), 400); }, 4000);
  });
});

// Chart palette helper
const DC = {
  colors: {
    primary: getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#2563eb',
    accent: getComputedStyle(document.documentElement).getPropertyValue('--accent').trim() || '#06b6d4',
    palette: ['#2563eb', '#06b6d4', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#f97316'],
  },
};

function readJSON(id) {
  const el = document.getElementById(id);
  if (!el) return null;
  try { return JSON.parse(el.textContent); } catch (e) { return null; }
}

function gradientFill(ctx, color) {
  const g = ctx.createLinearGradient(0, 0, 0, 300);
  g.addColorStop(0, color + '55');
  g.addColorStop(1, color + '05');
  return g;
}

function lineChart(canvasId, dataId, label) {
  const canvas = document.getElementById(canvasId);
  const data = readJSON(dataId);
  if (!canvas || !data) return;
  const ctx = canvas.getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [{
        label: label || '',
        data: data.data,
        borderColor: DC.colors.primary,
        backgroundColor: gradientFill(ctx, DC.colors.primary),
        fill: true, tension: 0.4, borderWidth: 3,
        pointBackgroundColor: DC.colors.primary, pointRadius: 3,
      }],
    },
    options: baseOptions(),
  });
}

function barChart(canvasId, dataId, label) {
  const canvas = document.getElementById(canvasId);
  const data = readJSON(dataId);
  if (!canvas || !data) return;
  new Chart(canvas.getContext('2d'), {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: label || '',
        data: data.data,
        backgroundColor: DC.colors.primary,
        borderRadius: 8, maxBarThickness: 34,
      }],
    },
    options: baseOptions(),
  });
}

function doughnutChart(canvasId, dataId) {
  const canvas = document.getElementById(canvasId);
  const data = readJSON(dataId);
  if (!canvas || !data) return;
  new Chart(canvas.getContext('2d'), {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{ data: data.data, backgroundColor: DC.colors.palette, borderWidth: 0 }],
    },
    options: {
      responsive: true, maintainAspectRatio: false, cutout: '62%',
      plugins: { legend: { position: 'bottom', labels: { usePointStyle: true, padding: 14 } } },
    },
  });
}

function baseOptions() {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
      y: { grid: { color: '#eef2f7' }, ticks: { color: '#94a3b8' }, beginAtZero: true },
    },
  };
}

// Dynamic formset "add row"
function addFormsetRow(prefix) {
  const totalForms = document.querySelector(`#id_${prefix}-TOTAL_FORMS`);
  const container = document.querySelector(`#${prefix}-rows`);
  const template = document.querySelector(`#${prefix}-empty`);
  if (!totalForms || !container || !template) return;
  const index = parseInt(totalForms.value, 10);
  const html = template.innerHTML.replace(/__prefix__/g, index);
  const wrapper = document.createElement('div');
  wrapper.innerHTML = html;
  container.appendChild(wrapper);
  totalForms.value = index + 1;
}
