<template>
  <div class="bar-card card-animated">
    <div class="card-header">
      <div class="title-with-icon">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
          class="title-icon"
        >
          <path d="M2 13H8V21H2V13ZM9 3H15V21H9V3ZM16 8H22V21H16V8Z" />
        </svg>
        <h5 class="chart-title">{{ title }}</h5>
      </div>
      <div class="top-badge">TOP {{ topN }}</div>
    </div>
    <canvas ref="canvas" class="bar-canvas"></canvas>
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
    default: "分类时长排行",
  },
  topN: {
    type: Number,
    default: 10,
  },
  colors: {
    type: Array,
    required: true,
  },
});

const canvas = ref(null);
let chart = null;

function renderChart() {
  if (!canvas.value || !props.data?.labels?.length) return;

  if (chart) {
    chart.destroy();
  }

  chart = new Chart(canvas.value, {
    type: "bar",
    data: {
      labels: props.data.labels,
      datasets: [
        {
          data: props.data.data,
          backgroundColor: props.colors,
          borderRadius: 8,
          borderSkipped: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      indexAxis: "y",
      layout: {
        padding: {
          left: 0,
          right: 0,
          top: 0,
          bottom: 0,
        },
      },
      interaction: { intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const label = ctx.label || "";
              const value = ctx.parsed.x || 0;
              return `${label}: ${value.toFixed(1)}h`;
            },
          },
        },
      },
      scales: {
        x: {
          display: false,
          grid: { display: false },
          beginAtZero: true,
        },
        y: {
          grid: { display: false },
          ticks: {
            autoSkip: false,
            maxRotation: 0,
            minRotation: 0,
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
.bar-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 0.75rem;
  border: 1px solid #d1c4e9;
  box-shadow: 0 2px 4px rgba(103, 58, 183, 0.08);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.bar-card:hover {
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

.top-badge {
  background: #f59e0b;
  color: #fff;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.bar-canvas {
  width: 100%;
  flex: 1;
  min-height: 0;
  max-height: 100%;
}

@media (max-width: 768px) {
  .bar-card {
    padding: 1rem;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .top-badge {
    align-self: flex-end;
  }
}
</style>
