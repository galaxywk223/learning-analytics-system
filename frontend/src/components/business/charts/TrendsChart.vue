<template>
  <div class="trend-chart-card">
    <div v-if="!hasData && !loading" class="trend-chart-card__empty">
      <svg
        class="trend-chart-card__empty-icon"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          d="M12 2C17.5228 2 22 6.47715 22 12C22 13.7005 21.578 15.3098 20.8281 16.7241L21.8701 20.1029C22.0415 20.6692 21.6692 21.2585 21.1029 21.4299C20.8579 21.5034 20.5943 21.4713 20.3736 21.3408L17.2759 19.5149C15.8627 20.3517 14.2207 20.8 12.5 20.8C6.97715 20.8 2.5 16.3228 2.5 10.8C2.5 5.27715 6.97715 0.8 12.5 0.8V2ZM12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20C13.6666 20 15.2268 19.5368 16.541 18.7201L17.0833 18.3863L19.1681 19.6304L18.6137 17.541C19.4353 16.2269 19.9 14.6691 19.9 13C19.9 8.58172 16.3183 5 11.9 5L12 4ZM11.25 7.75H12.75V13.5H11.25V7.75ZM11.25 15.25H12.75V17.5H11.25V15.25Z"
        />
      </svg>
      <p class="trend-chart-card__empty-text">
        暂无可视化数据，记录新的学习时长后即可查看趋势。
      </p>
    </div>
    <div v-else class="trend-chart-card__panel" v-loading="loading">
      <header class="trend-chart-card__header">
        <div class="trend-chart-card__titles">
          <span class="trend-chart-card__badge">{{ viewBadge }}</span>
          <h3>学习趋势洞察</h3>
          <p>结合学习时长与效率的双轴分析，快速洞悉进步轨迹</p>
        </div>
      </header>
      <v-chart class="trend-chart-card__visual" :option="chartOption" autoresize />
      <footer v-if="showStageHelper" class="trend-chart-card__footer">
        <span class="trend-chart-card__footer-dot" />
        <span>阶段划分已在图中浅色标注，悬停即可查看阶段名称</span>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { use } from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkAreaComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkAreaComponent,
]);

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

const currentView = ref(props.initialView === "daily" ? "daily" : "weekly");

watch(
  () => props.initialView,
  (newView) => {
    if (!newView || newView === currentView.value) return;
    currentView.value = newView === "daily" ? "daily" : "weekly";
  }
);

const sanitizeSeries = (values, { allowZero = true } = {}) => {
  if (!Array.isArray(values)) return [];
  return values.map((val) => {
    if (val === null || val === undefined || Number.isNaN(Number(val))) {
      return allowZero ? 0 : null;
    }
    const num = Number(val);
    if (!Number.isFinite(num)) {
      return allowZero ? 0 : null;
    }
    return Number(num.toFixed(2));
  });
};

const viewBadge = computed(() =>
  currentView.value === "weekly" ? "周视图" : "日视图"
);

const durationSeriesLabel = computed(() =>
  currentView.value === "weekly" ? "平均学习时长" : "学习时长"
);

const viewSource = computed(() => {
  const isWeekly = currentView.value === "weekly";
  const duration = isWeekly ? props.weeklyDurationData : props.dailyDurationData;
  const efficiency = isWeekly
    ? props.weeklyEfficiencyData
    : props.dailyEfficiencyData;

  const labels = Array.isArray(duration?.labels) ? duration.labels : [];
  const durationActual = sanitizeSeries(duration?.actuals, { allowZero: true });
  const durationTrend = sanitizeSeries(duration?.trends, { allowZero: false });
  const efficiencyActual = sanitizeSeries(efficiency?.actuals, {
    allowZero: true,
  });
  const efficiencyTrend = sanitizeSeries(efficiency?.trends, {
    allowZero: false,
  });

  return {
    labels,
    durationActual,
    durationTrend,
    efficiencyActual,
    efficiencyTrend,
  };
});

const stageMarkArea = computed(() => {
  if (currentView.value !== "weekly") return [];
  const labels = viewSource.value.labels;
  if (!labels.length) return [];

  const labelSet = new Set(labels);
  return (props.stageAnnotations || [])
    .filter(
      (item) =>
        item &&
        labelSet.has(item.start_week_label) &&
        labelSet.has(item.end_week_label)
    )
    .map((item) => [
      {
        name: item.name,
        xAxis: item.start_week_label,
        itemStyle: { opacity: 0.08 },
        label: { color: "#312e81", fontWeight: 600 },
      },
      { xAxis: item.end_week_label },
    ]);
});

const showStageHelper = computed(
  () => currentView.value === "weekly" && stageMarkArea.value.length > 0
);

const chartOption = computed(() => {
  const {
    labels,
    durationActual,
    durationTrend,
    efficiencyActual,
    efficiencyTrend,
  } = viewSource.value;

  const hasDurationTrend = durationTrend.some((val) => val !== null);
  const hasEfficiencyTrend = efficiencyTrend.some((val) => val !== null);
  const enableZoom = labels.length > 14;
  const sliderWindow = enableZoom
    ? Math.min(100, Math.round((14 / labels.length) * 100))
    : 100;
  const sliderStart = enableZoom ? Math.max(0, 100 - sliderWindow) : 0;

  const series = [
    {
      name: durationSeriesLabel.value,
      type: "line",
      smooth: true,
      symbol: "circle",
      symbolSize: 6,
      data: durationActual,
      lineStyle: { width: 3, color: "#6366f1" },
      areaStyle: {
        color: "rgba(99, 102, 241, 0.18)",
      },
      emphasis: { focus: "series" },
      markArea: stageMarkArea.value.length
        ? {
            silent: true,
            data: stageMarkArea.value,
          }
        : undefined,
      zlevel: 1,
    },
  ];

  if (hasDurationTrend) {
    series.push({
      name: "时长趋势",
      type: "line",
      smooth: true,
      symbol: "none",
      data: durationTrend,
      lineStyle: {
        color: "#4338ca",
        width: 2,
        type: "dashed",
      },
      tooltip: { valueFormatter: (val) => (val == null ? "--" : `${val} h`) },
      connectNulls: true,
    });
  }

  series.push({
    name: "学习效率",
    type: "line",
    smooth: true,
    symbol: "diamond",
    symbolSize: 6,
    data: efficiencyActual,
    yAxisIndex: 1,
    lineStyle: { width: 3, color: "#f97316" },
    areaStyle: {
      color: "rgba(249, 115, 22, 0.12)",
    },
    emphasis: { focus: "series" },
    zlevel: 1,
  });

  if (hasEfficiencyTrend) {
    series.push({
      name: "效率趋势",
      type: "line",
      smooth: true,
      symbol: "none",
      data: efficiencyTrend,
      yAxisIndex: 1,
      lineStyle: {
        color: "#ea580c",
        width: 2,
        type: "dotted",
      },
      connectNulls: true,
    });
  }

  return {
    color: ["#6366f1", "#4338ca", "#f97316", "#ea580c"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: "rgba(15, 23, 42, 0.9)",
      borderWidth: 0,
      textStyle: { color: "#f8fafc" },
      formatter: (params) => {
        const header = `<strong>${params[0]?.axisValueLabel ?? ""}</strong>`;
        const lines = params
          .map((item) => {
            const value =
              item.value == null || Number.isNaN(item.value)
                ? "--"
                : Number(item.value).toFixed(2);
            const unit = item.seriesName.includes("效率") ? "" : " h";
            return `<span style="display:inline-block;margin-right:8px;border-radius:50%;width:8px;height:8px;background:${item.color}"></span>${item.seriesName}：${value}${unit}`;
          })
          .join("<br/>");
        return `${header}<br/>${lines}`;
      },
    },
    legend: {
      top: 12,
      icon: "circle",
    },
    grid: {
      left: 18,
      right: 24,
      top: 86,
      bottom: enableZoom ? 60 : 32,
      containLabel: true,
    },
    dataZoom: enableZoom
      ? [
          { type: "inside", start: sliderStart, end: 100 },
          {
            type: "slider",
            start: sliderStart,
            end: 100,
            bottom: 16,
            height: 14,
            borderRadius: 8,
            brushSelect: false,
            handleSize: 0,
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: labels,
      axisLabel: {
        color: "#475569",
        formatter: (value) => value.slice(5),
      },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.45)" } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: "value",
        name: "学习时长 (小时)",
        min: 0,
        nameTextStyle: { color: "#475569" },
        axisLabel: { color: "#475569" },
        splitLine: { lineStyle: { type: "dashed", color: "rgba(148, 163, 184, 0.4)" } },
      },
      {
        type: "value",
        name: "效率指数",
        min: 0,
        nameTextStyle: { color: "#475569" },
        axisLabel: { color: "#475569" },
        splitLine: { show: false },
      },
    ],
    series,
  };
});
</script>

<style scoped lang="scss">
@import "@/styles/components/trends-chart";
</style>
