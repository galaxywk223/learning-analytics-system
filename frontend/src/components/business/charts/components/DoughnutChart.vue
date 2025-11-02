<template>
  <div class="doughnut-card card-animated">
    <div class="card-header">
      <div class="title-with-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="title-icon"
        >
          <path
            d="M11 2.04932V12.9993L18.3611 16.9993C17.1175 19.4376 14.7452 21.1993 12 21.1993C8.13401 21.1993 5 18.0653 5 14.1993C5 11.4544 6.76165 9.08206 9.2 7.83842L11 2.04932ZM13 2.04932L14.8 7.83842C17.2383 9.08206 19 11.4544 19 14.1993C19 15.3126 18.7187 16.3608 18.2217 17.2832L13 14.3017V2.04932ZM12 0.0493164C5.92487 0.0493164 1 4.97419 1 11.0493C1 17.1245 5.92487 22.0493 12 22.0493C18.0751 22.0493 23 17.1245 23 11.0493H21C21 16.0199 16.9706 20.0493 12 20.0493C7.02944 20.0493 3 16.0199 3 11.0493C3 6.07876 7.02944 2.04932 12 2.04932V0.0493164Z"
          />
        </svg>
        <h5 class="chart-title" id="categoryChartTitle">
          {{ title }}
        </h5>
      </div>
      <div class="total-badge" v-if="totalHours">
        <span class="badge-label">总计</span>
        <span class="badge-value">{{ totalHours.toFixed(1) }}h</span>
      </div>
    </div>
    <div class="doughnut-container">
      <canvas ref="canvas" @click="handleClick"></canvas>
      <div class="center-text" v-if="totalHours">
        <div class="center-value">{{ totalHours.toFixed(1) }}h</div>
        <div class="center-label">总时长</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from "vue";
import Chart from "chart.js/auto";

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  title: {
    type: String,
    default: "分类时长占比",
  },
  totalHours: {
    type: Number,
    default: 0,
  },
  colors: {
    type: Array,
    required: true,
  },
});

const emit = defineEmits(["slice-click"]);

const canvas = ref(null);
let chart = null;

function handleClick(evt) {
  if (!chart) return;

  const points = chart.getElementsAtEventForMode(
    evt,
    "nearest",
    { intersect: true },
    true
  );

  if (points.length) {
    const idx = points[0].index;
    const label = chart.data.labels[idx];
    emit("slice-click", label);
  }
}

function renderChart() {
  if (!canvas.value || !props.data?.labels?.length) return;

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(canvas.value, {
    type: "doughnut",
    data: {
      labels: props.data.labels,
      datasets: [
        {
          data: props.data.data,
          backgroundColor: props.colors,
          borderWidth: 0,
          cutout: "60%",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const label = ctx.label || "";
              const value = ctx.parsed || 0;
              const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
              const percentage = ((value / total) * 100).toFixed(1);
              return `${label}: ${value.toFixed(1)}h (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

onMounted(() => {
  nextTick(() => {
    renderChart();
  });
});

watch(() => props.data, renderChart, { deep: true });
</script>

<style scoped>
.doughnut-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 0.75rem;
  border: 1px solid #d1c4e9;
  box-shadow: 0 2px 4px rgba(103, 58, 183, 0.08);
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
}

.doughnut-card:hover {
  box-shadow: 0 4px 8px rgba(103, 58, 183, 0.12);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}

.title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.title-icon {
  width: 20px;
  height: 20px;
  color: #667eea;
  flex-shrink: 0;
}

.chart-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  color: #1f2937;
}

.total-badge {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  background: #667eea;
  padding: 6px 12px;
  border-radius: 6px;
  flex-shrink: 0;
}

.badge-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.badge-value {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  line-height: 1.2;
}

.doughnut-container {
  position: relative;
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.center-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}

.center-value {
  font-size: 28px;
  font-weight: 800;
  color: #1e293b;
  line-height: 1;
  margin-bottom: 4px;
}

.center-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 600;
  margin: 0;
  text-align: center;
}

@media (max-width: 768px) {
  .doughnut-card {
    padding: 1rem;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .total-badge {
    align-self: flex-end;
  }

  .doughnut-container {
    height: 300px;
    max-height: 300px;
  }

  .center-text .center-value {
    font-size: 28px;
  }

  .center-text .center-label {
    font-size: 12px;
  }
}
</style>
