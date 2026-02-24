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
    <div v-else v-loading="loading" class="trend-chart-card__panel">
      <header class="trend-chart-card__header">
        <div class="trend-chart-card__titles">
          <h3>学习趋势</h3>
        </div>
        <div class="trend-chart-card__switch">
          <button
            :class="['seg-btn', currentView === 'weekly' && 'active']"
            @click="switchView('weekly')"
          >
            <span class="emoji-icon" aria-hidden="true">📅</span>
            <span>周视图</span>
          </button>
          <button
            :class="['seg-btn', currentView === 'daily' && 'active']"
            @click="switchView('daily')"
          >
            <span class="emoji-icon" aria-hidden="true">📆</span>
            <span>日视图</span>
          </button>
        </div>
      </header>
      <v-chart
        class="trend-chart-card__visual"
        :option="chartOption"
        autoresize
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { use, graphic } from "echarts/core";
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
  initialView: { type: String, default: "weekly" },
});

const emit = defineEmits(["view-change"]);

const currentView = ref(props.initialView === "daily" ? "daily" : "weekly");
const themeVersion = ref(0);
let themeObserver = null;

const readThemeVar = (name, fallback) => {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
};

const themeTokens = computed(() => {
  themeVersion.value;
  return {
    textBase: readThemeVar("--color-text-base", "#1c1c1e"),
    textSecondary: readThemeVar("--color-text-secondary", "#8e8e93"),
    textHeading: readThemeVar("--color-text-heading", "#1c1c1e"),
    card: readThemeVar("--surface-card", "#ffffff"),
    subtle: readThemeVar("--surface-subtle", "#f2f2f7"),
    border: readThemeVar("--color-border-card", "#e5e5ea"),
    primary: readThemeVar("--color-primary", "#5856D6"),
    primaryDark: readThemeVar("--color-primary-dark", "#AF52DE"),
    warning: readThemeVar("--color-warning", "#FF9500"),
    warningSoft: "rgba(255, 149, 0, 0.18)",
    primarySoft: readThemeVar("--color-primary-light", "rgba(88, 86, 214, 0.2)"),
    inverse: readThemeVar("--color-text-inverse", "#ffffff"),
  };
});

watch(
  () => props.initialView,
  (newView) => {
    if (!newView || newView === currentView.value) return;
    currentView.value = newView === "daily" ? "daily" : "weekly";
  },
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
  currentView.value === "weekly" ? "周视图" : "日视图",
);

const switchView = (view) => {
  const normalized = view === "daily" ? "daily" : "weekly";
  if (normalized === currentView.value) return;
  currentView.value = normalized;
  emit("view-change", normalized);
};

const durationSeriesLabel = computed(() =>
  currentView.value === "weekly" ? "平均学习时长" : "学习时长",
);

const viewSource = computed(() => {
  const isWeekly = currentView.value === "weekly";
  const duration = isWeekly
    ? props.weeklyDurationData
    : props.dailyDurationData;
  const efficiency = isWeekly
    ? props.weeklyEfficiencyData
    : props.dailyEfficiencyData;

  const labels = Array.isArray(duration?.labels) ? duration.labels : [];
  const durationActual = sanitizeSeries(duration?.actuals, { allowZero: true });
  const efficiencyActual = sanitizeSeries(efficiency?.actuals, {
    allowZero: true,
  });

  return {
    labels,
    durationActual,
    efficiencyActual,
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
        labelSet.has(item.end_week_label),
    )
    .map((item) => [
      {
        name: item.name,
        xAxis: item.start_week_label,
        itemStyle: { opacity: 0.04 }, // Even more subtle
        label: {
          color: themeTokens.value.primary,
          fontWeight: 600,
          fontSize: 12,
        },
      },
      { xAxis: item.end_week_label },
    ]);
});

const showStageHelper = computed(
  () => currentView.value === "weekly" && stageMarkArea.value.length > 0,
);

const chartOption = computed(() => {
  const { labels, durationActual, efficiencyActual } = viewSource.value;
  const windowSize = currentView.value === "weekly" ? 26 : 90;
  const enableZoom = labels.length > windowSize;
  const startIndex = Math.max(0, labels.length - windowSize);
  const zoomStartValue = labels[startIndex];
  const zoomEndValue = labels[labels.length - 1];

  const token = themeTokens.value;

  // Apple-style Colors
  const colors = {
    duration: {
      line: token.primary,
      areaStart: token.primarySoft,
      areaEnd: "rgba(88, 86, 214, 0.02)",
    },
    efficiency: {
      line: token.warning,
      areaStart: token.warningSoft,
      areaEnd: "rgba(255, 149, 0, 0.02)",
    },
  };

  return {
    color: [colors.duration.line, colors.efficiency.line],
    tooltip: {
      trigger: "axis",
      backgroundColor: token.card,
      borderColor: token.border,
      borderWidth: 1,
      padding: [12, 16],
      textStyle: {
        color: token.textBase,
        fontSize: 13,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      },
      extraCssText:
        "box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-radius: 12px;",
    },
    legend: {
      top: 12,
      icon: "circle",
      itemGap: 24,
      textStyle: {
        color: token.textSecondary,
        fontSize: 13,
      },
      data: [durationSeriesLabel.value, "学习效率"],
    },
    grid: {
      left: 20,
      right: 20,
      top: 80,
      bottom: enableZoom ? 60 : 20,
      containLabel: true,
      borderColor: token.border,
    },
    dataZoom: enableZoom
      ? [
          {
            type: "inside",
            startValue: zoomStartValue,
            endValue: zoomEndValue,
          },
          {
            type: "slider",
            startValue: zoomStartValue,
            endValue: zoomEndValue,
            bottom: 16,
            height: 4, // Thinner slider
            borderRadius: 2,
            brushSelect: false,
            handleSize: 16,
            handleStyle: {
              color: token.card,
              borderColor: token.border,
              shadowBlur: 2,
              shadowColor: "rgba(0,0,0,0.1)",
            },
            fillerColor: token.primarySoft,
            borderColor: "transparent",
            backgroundColor: token.subtle,
            showDataShadow: false,
            showDetail: false,
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: labels,
      axisLabel: {
        color: token.textSecondary,
        fontSize: 12,
        margin: 12,
        formatter: (value) => value.slice(5),
      },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: "value",
        name: "学习时长 (小时)",
        min: 0,
        nameTextStyle: { color: token.textSecondary, padding: [0, 0, 0, 20] },
        axisLabel: { color: token.textSecondary, fontSize: 12 },
        splitLine: {
          lineStyle: { type: "dashed", color: token.border },
        },
      },
      {
        type: "value",
        name: "效率指数",
        min: 0,
        nameTextStyle: { color: token.textSecondary, padding: [0, 20, 0, 0] },
        axisLabel: { color: token.textSecondary, fontSize: 12 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: durationSeriesLabel.value,
        type: "line",
        smooth: 0.4,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 8,
        data: durationActual,
        itemStyle: {
          color: colors.duration.line,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 3,
          shadowColor: "rgba(88, 86, 214, 0.3)",
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors.duration.areaStart },
            { offset: 1, color: colors.duration.areaEnd },
          ]),
        },
        markArea: stageMarkArea.value.length
          ? { silent: true, data: stageMarkArea.value }
          : undefined,
      },
      {
        name: "学习效率",
        type: "line",
        smooth: 0.4,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 8,
        yAxisIndex: 1,
        data: efficiencyActual,
        itemStyle: {
          color: colors.efficiency.line,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 3,
          color: colors.efficiency.line,
          shadowColor: "rgba(255, 149, 0, 0.3)",
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors.efficiency.areaStart },
            { offset: 1, color: colors.efficiency.areaEnd },
          ]),
        },
      },
    ],
  };
});

onMounted(() => {
  if (typeof window === "undefined" || !window.MutationObserver) return;
  themeObserver = new MutationObserver(() => {
    themeVersion.value += 1;
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme", "class", "style"],
  });
});

onUnmounted(() => {
  if (themeObserver) {
    themeObserver.disconnect();
    themeObserver = null;
  }
});
</script>

<style scoped lang="scss">
@import "@/styles/components/trends-chart";
</style>
