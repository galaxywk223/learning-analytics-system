<template>
  <div class="category-wrapper" v-if="hasData">
    <div class="main-grid">
      <div class="doughnut-card">
        <h5 class="chart-title" id="categoryChartTitle">{{ currentTitle }}</h5>
        <div class="doughnut-container">
          <canvas ref="doughnutCanvas"></canvas>
          <div class="center-text" v-if="totalHours">
            {{ totalHours.toFixed(1) }}h<br /><small>总时长</small>
          </div>
        </div>
      </div>
      <div class="bar-card">
        <h5 class="chart-title">{{ barTitle }}</h5>
        <canvas ref="barCanvas" class="bar-canvas"></canvas>
        <hr />
        <div class="table-container" ref="tableContainer"></div>
      </div>
    </div>
    <div class="actions" v-if="view === 'drilldown'">
      <button class="btn btn-sm" @click="backToMain">
        <span>返回上级</span>
      </button>
    </div>
  </div>
  <div v-else class="alert alert-info text-center">
    当前筛选范围内没有找到任何带分类的学习记录。
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from "vue";
import { Chart } from "chart.js/auto";
import ChartDataLabels from "chartjs-plugin-datalabels";

Chart.register(ChartDataLabels);

const props = defineProps({
  main: { type: Object, required: true }, // {labels:[], data:[]}
  drilldown: { type: Object, required: true }, // {category: {labels:[], data:[]}}
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["sliceClick", "back"]);

const doughnutCanvas = ref(null);
const barCanvas = ref(null);
let doughnutChart = null;
let barChart = null;
const view = ref("main");
const currentCategory = ref("");
const totalHours = ref(0);

// 改为计算属性，实时检查是否有数据
const hasData = computed(() => {
  if (view.value === "main") {
    return props.main && props.main.labels && props.main.labels.length > 0;
  } else {
    const dl = props.drilldown[currentCategory.value];
    return dl && dl.labels && dl.labels.length > 0;
  }
});

const currentTitle = ref("分类时长占比");
const barTitle = ref("分类时长排行");
const TOP_N = 10;

function buildColors(count) {
  const palette = [
    "#60A5FA",
    "#F87171",
    "#FBBF24",
    "#4ADE80",
    "#A78BFA",
    "#2DD4BF",
    "#F472B6",
    "#818CF8",
    "#FB923C",
    "#34D399",
  ];
  if (count <= palette.length) return palette.slice(0, count);
  while (palette.length < count) {
    palette.push("#" + Math.random().toString(16).slice(2, 8));
  }
  return palette;
}

function renderCharts() {
  console.log("[CategoryComposite] renderCharts called");
  console.log("[CategoryComposite] doughnutCanvas:", doughnutCanvas.value);
  console.log("[CategoryComposite] barCanvas:", barCanvas.value);
  console.log("[CategoryComposite] props.main:", props.main);
  console.log("[CategoryComposite] props.drilldown:", props.drilldown);

  if (!doughnutCanvas.value || !barCanvas.value) {
    console.log("[CategoryComposite] Canvas not ready, skipping render");
    return;
  }

  // 计算数据源
  let sourceArray = [];
  if (view.value === "main") {
    sourceArray = props.main.labels
      .map((l, i) => ({ label: l, value: props.main.data[i] }))
      .sort((a, b) => b.value - a.value);
    currentTitle.value = "分类时长占比";
    barTitle.value = "分类时长排行";
  } else {
    const dl = props.drilldown[currentCategory.value];
    sourceArray = dl.labels
      .map((l, i) => ({ label: l, value: dl.data[i] }))
      .sort((a, b) => b.value - a.value);
    currentTitle.value = currentCategory.value + " - 标签详情";
    barTitle.value = currentCategory.value + " - 标签排行";
  }

  console.log("[CategoryComposite] sourceArray:", sourceArray);
  totalHours.value = sourceArray.reduce((s, i) => s + i.value, 0);
  console.log("[CategoryComposite] totalHours:", totalHours.value);
  // hasData 现在是计算属性，不需要手动设置
  const colors = buildColors(sourceArray.length);

  // 销毁旧图
  if (doughnutChart) doughnutChart.destroy();
  if (barChart) barChart.destroy();

  doughnutChart = new Chart(doughnutCanvas.value.getContext("2d"), {
    type: "doughnut",
    data: {
      labels: sourceArray.map((d) => d.label),
      datasets: [
        {
          data: sourceArray.map((d) => d.value),
          backgroundColor: colors,
          borderWidth: 2,
          borderColor: "transparent",
        },
      ],
    },
    options: {
      cutout: "70%",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const total = ctx.chart.getDatasetMeta(0).total || 0;
              const pct = total ? ((ctx.parsed / total) * 100).toFixed(1) : 0;
              return `${ctx.label}: ${ctx.parsed.toFixed(1)}小时 (${pct}%)`;
            },
          },
        },
        datalabels: {
          display: true,
          formatter: (value, context) => {
            const ds = context.chart.data.datasets[0];
            const total = ds.data.reduce((t, v) => t + v, 0);
            const pct = total ? (value / total) * 100 : 0;
            return pct > 3
              ? context.chart.data.labels[context.dataIndex]
              : null;
          },
          color: "#000",
          font: { weight: "bold" },
          padding: 4,
        },
      },
    },
  });

  const barData = sourceArray.slice(0, TOP_N);
  barChart = new Chart(barCanvas.value.getContext("2d"), {
    type: "bar",
    data: {
      labels: barData.map((d) => d.label),
      datasets: [
        {
          data: barData.map((d) => d.value),
          backgroundColor: colors.slice(0, barData.length),
          borderWidth: 2,
          borderColor: "transparent",
        },
      ],
    },
    options: {
      indexAxis: "y",
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.parsed.toFixed(1)}小时`,
          },
        },
      },
      scales: {
        x: { display: false, grid: { display: false } },
        y: { grid: { display: false } },
      },
    },
  });

  // 表格渲染
  const tableRoot = tableContainer.value;
  if (tableRoot) {
    let html =
      '<table class="table table-hover"><thead><tr><th>名称</th><th>时长(h)</th><th>占比(%)</th></tr></thead><tbody>';
    sourceArray.forEach((item) => {
      const pct = totalHours.value
        ? ((item.value / totalHours.value) * 100).toFixed(1)
        : "0.0";
      const drillInfo =
        view.value === "main" &&
        props.drilldown[item.label] &&
        props.drilldown[item.label].labels.length > 0
          ? ` data-drill="${item.label}" style="cursor:pointer"`
          : "";
      html += `<tr${drillInfo}><td>${item.label}</td><td>${item.value.toFixed(1)}</td><td>${pct}</td></tr>`;
    });
    html += "</tbody></table>";
    tableRoot.innerHTML = html;
    tableRoot.querySelectorAll("tr[data-drill]").forEach((row) => {
      row.addEventListener("click", () => {
        currentCategory.value = row.getAttribute("data-drill");
        view.value = "drilldown";
        renderCharts();
        emit("sliceClick", currentCategory.value);
      });
    });
  }

  // 绑定 doughnut 点击
  doughnutCanvas.value.onclick = (evt) => {
    const points = doughnutChart.getElementsAtEventForMode(
      evt,
      "nearest",
      { intersect: true },
      true
    );
    if (points.length && view.value === "main") {
      const idx = points[0].index;
      const label = doughnutChart.data.labels[idx];
      if (props.drilldown[label] && props.drilldown[label].labels.length > 0) {
        currentCategory.value = label;
        view.value = "drilldown";
        renderCharts();
        emit("sliceClick", label);
      }
    }
  };
}

function backToMain() {
  view.value = "main";
  currentCategory.value = "";
  renderCharts();
  emit("back");
}

const tableContainer = ref(null);

watch(
  () => [props.main, props.drilldown],
  () => {
    renderCharts();
  },
  { deep: true }
);

onMounted(() => {
  renderCharts();
});
onBeforeUnmount(() => {
  if (doughnutChart) doughnutChart.destroy();
  if (barChart) barChart.destroy();
});
</script>

<style scoped>
.category-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.doughnut-card,
.bar-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
  min-height: 520px;
  position: relative;
}
.chart-title {
  font-size: 14px;
  font-weight: 600;
  margin: 0 0 12px;
}
.doughnut-container {
  position: relative;
  height: 420px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.center-text {
  position: absolute;
  text-align: center;
  font-weight: 600;
  pointer-events: none;
}
.bar-canvas {
  height: 250px;
}
.table-container {
  max-height: 180px;
  overflow-y: auto;
  margin-top: 12px;
}
.actions {
  display: flex;
}
.btn {
  background: #fff;
  border: 1px solid #d1d5db;
  padding: 4px 10px;
  cursor: pointer;
  font-size: 12px;
  border-radius: 6px;
}
.btn:hover {
  background: #f3f4f6;
}
.alert {
  padding: 16px;
  border: 1px solid #dbeafe;
  background: #eff6ff;
  border-radius: 6px;
}
</style>
