<template>
  <div class="trends-wrapper">
    <div v-if="!hasData && !loading" class="alert alert-info no-data">
      暂无学习数据，无法生成趋势图。
    </div>
    <div v-else class="charts-grid" :class="{ loading: loading }">
      <div class="single-chart">
        <h5 class="chart-title">学习时长分析</h5>
        <canvas ref="durationCanvas"></canvas>
      </div>
      <div class="single-chart">
        <h5 class="chart-title">学习效率分析</h5>
        <canvas ref="efficiencyCanvas"></canvas>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from "vue";
import { Chart } from "chart.js/auto";

const props = defineProps({
  weeklyDurationData: { type: Object, required: true },
  weeklyEfficiencyData: { type: Object, required: true },
  dailyDurationData: { type: Object, required: true },
  dailyEfficiencyData: { type: Object, required: true },
  stageAnnotations: { type: Array, default: () => [] },
  hasData: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  initialView: { type: String, default: "weekly" }, // 'weekly' | 'daily'
});

const durationCanvas = ref(null);
const efficiencyCanvas = ref(null);
let durationChart = null;
let efficiencyChart = null;
const currentView = ref(props.initialView);

// 自定义阶段注释插件 (仅在周视图显示)
const stageAnnotationsPlugin = {
  id: "stageAnnotations",
  afterDraw(chart) {
    if (currentView.value !== "weekly") return;
    const annotations = props.stageAnnotations || [];
    if (!annotations.length) return;
    const {
      ctx,
      chartArea: { bottom, left, right },
      scales: { x },
    } = chart;
    ctx.save();
    ctx.font = 'bold 12px "Inter", sans-serif';
    ctx.textAlign = "center";
    ctx.fillStyle = "#4B5563";
    ctx.strokeStyle = "#9CA3AF";
    ctx.lineWidth = 1;
    annotations.forEach((anno) => {
      const startIndex = chart.data.labels.indexOf(anno.start_week_label);
      const endIndex = chart.data.labels.indexOf(anno.end_week_label);
      if (startIndex === -1 || endIndex === -1) return;
      const startPixel = x.getPixelForValue(startIndex);
      const endPixel = x.getPixelForValue(endIndex);
      const middlePixel = startPixel + (endPixel - startPixel) / 2;
      if (middlePixel < left || middlePixel > right) return;
      ctx.beginPath();
      ctx.moveTo(startPixel, bottom + 15);
      ctx.lineTo(endPixel, bottom + 15);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(middlePixel, bottom + 15);
      ctx.lineTo(middlePixel, bottom + 20);
      ctx.stroke();
      ctx.fillText(anno.name, middlePixel, bottom + 35);
    });
    ctx.restore();
  },
};

function createBaseOptions(yTitle) {
  return {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index", intersect: false },
    layout: { padding: { bottom: 40 } },
    plugins: {
      legend: {
        position: "top",
        labels: { usePointStyle: true, boxWidth: 8, padding: 20 },
      },
      tooltip: {
        backgroundColor: "#1f2937",
        titleFont: { size: 14 },
        bodyFont: { size: 12 },
        padding: 10,
        cornerRadius: 6,
        boxPadding: 3,
      },
    },
    scales: {
      x: { grid: { display: false }, ticks: { display: false } },
      y: {
        title: { display: true, text: yTitle },
        grace: "5%",
        beginAtZero: true,
      },
    },
  };
}

function buildDatasets(durationData, efficiencyData) {
  return {
    duration: [
      {
        type: "bar",
        label: "实际时长",
        data: durationData.actuals,
        backgroundColor: "rgba(96, 165, 250, 0.5)",
        order: 2,
      },
      {
        type: "line",
        label: "趋势",
        data: durationData.trends,
        borderColor: "#2563EB",
        tension: 0.4,
        fill: false,
        pointRadius: 0,
        borderWidth: 2.5,
        order: 1,
      },
    ],
    efficiency: [
      {
        type: "bar",
        label: "实际效率",
        data: efficiencyData.actuals,
        backgroundColor: "rgba(248, 113, 113, 0.5)",
        order: 2,
      },
      {
        type: "line",
        label: "趋势",
        data: efficiencyData.trends,
        borderColor: "#991B1B",
        tension: 0.4,
        fill: false,
        pointRadius: 0,
        borderWidth: 2.5,
        order: 1,
        spanGaps: true,
      },
    ],
  };
}

function renderCharts() {
  if (!durationCanvas.value || !efficiencyCanvas.value) return;
  const durationCtx = durationCanvas.value.getContext("2d");
  const efficiencyCtx = efficiencyCanvas.value.getContext("2d");
  const viewPrefix = currentView.value;
  const durationData =
    viewPrefix === "weekly"
      ? props.weeklyDurationData
      : props.dailyDurationData;
  const efficiencyData =
    viewPrefix === "weekly"
      ? props.weeklyEfficiencyData
      : props.dailyEfficiencyData;
  const datasets = buildDatasets(durationData, efficiencyData);

  // 销毁旧实例
  if (durationChart) durationChart.destroy();
  if (efficiencyChart) efficiencyChart.destroy();

  durationChart = new Chart(durationCtx, {
    type: "bar",
    data: { labels: durationData.labels, datasets: datasets.duration },
    options: createBaseOptions("学习时长 (小时)"),
    plugins: [stageAnnotationsPlugin],
  });
  efficiencyChart = new Chart(efficiencyCtx, {
    type: "bar",
    data: { labels: efficiencyData.labels, datasets: datasets.efficiency },
    options: createBaseOptions("学习效率"),
    plugins: [stageAnnotationsPlugin],
  });
}

function switchView(view) {
  if (currentView.value === view) return;
  currentView.value = view;
  renderCharts();
}

// 监听父组件传入的视图类型变化
watch(
  () => props.initialView,
  (newView) => {
    if (newView && currentView.value !== newView) {
      switchView(newView);
    }
  }
);

watch(
  () => [
    props.weeklyDurationData,
    props.weeklyEfficiencyData,
    props.dailyDurationData,
    props.dailyEfficiencyData,
    props.stageAnnotations,
    props.hasData,
  ],
  () => {
    if (props.hasData) {
      renderCharts();
    }
  }
);

onMounted(() => {
  if (props.hasData) renderCharts();
});

onBeforeUnmount(() => {
  if (durationChart) durationChart.destroy();
  if (efficiencyChart) efficiencyChart.destroy();
});
</script>

<style scoped lang="scss">
@import "@/styles/components/trends-chart";
</style>
