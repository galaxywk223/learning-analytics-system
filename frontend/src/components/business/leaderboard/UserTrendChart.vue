<template>
  <div class="user-trend-chart">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { use } from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
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
]);

const props = defineProps({
  data: {
    type: Array,
    default: () => [],
  },
});

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
    primary: readThemeVar("--color-primary", "#2563eb"),
    warning: readThemeVar("--color-warning", "#f97316"),
    textBase: readThemeVar("--color-text-base", "#1f2937"),
    textSecondary: readThemeVar("--color-text-secondary", "#6b7280"),
    card: readThemeVar("--surface-card", "#ffffff"),
    subtle: readThemeVar("--surface-subtle", "#f1f5f9"),
    border: readThemeVar("--color-border-card", "#e2e8f0"),
  };
});

const option = computed(() => {
  const token = themeTokens.value;
  const source = props.data || [];
  const categories = source.map((item) => item.date);
  const durationSeries = source.map((item) => {
    const minutes = Number(item?.duration_minutes ?? 0);
    return Math.round((minutes / 60) * 100) / 100;
  });
  const efficiencySeries = source.map((item) => {
    const efficiency = Number(item?.average_efficiency ?? 0);
    return Math.round(efficiency * 100) / 100;
  });
  const hasData = categories.length > 0;

  return {
    color: [token.primary, token.warning],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
      backgroundColor: token.card,
      borderColor: token.border,
      borderWidth: 1,
      textStyle: {
        color: token.textBase,
      },
    },
    legend: {
      top: 0,
      icon: "circle",
      textStyle: {
        color: token.textSecondary,
      },
    },
    grid: {
      left: 16,
      right: 16,
      bottom: hasData ? 48 : 24,
      top: 48,
    },
    dataZoom: hasData
      ? [
          { type: "inside", start: 0, end: 100 },
          {
            type: "slider",
            start: 0,
            end: 100,
            height: 16,
            bottom: 12,
            brushSelect: false,
            backgroundColor: token.subtle,
            fillerColor: token.primary,
            borderColor: "transparent",
            handleStyle: {
              color: token.card,
              borderColor: token.border,
            },
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: categories,
      axisLabel: {
        formatter: (value) => value.slice(5),
        color: token.textSecondary,
      },
      axisLine: { lineStyle: { color: token.border } },
    },
    yAxis: [
      {
        type: "value",
        name: "学习时长 (小时)",
        min: 0,
        nameTextStyle: { color: token.textSecondary },
        axisLabel: { formatter: (val) => `${val}`, color: token.textSecondary },
        splitLine: { lineStyle: { type: "dashed", color: token.border } },
      },
      {
        type: "value",
        name: "效率指数",
        min: 0,
        nameTextStyle: { color: token.textSecondary },
        axisLabel: { formatter: (val) => `${val}`, color: token.textSecondary },
        splitLine: { lineStyle: { type: "dashed", color: token.border } },
      },
    ],
    series: [
      {
        name: "学习时长",
        type: "line",
        smooth: true,
        areaStyle: { opacity: 0.15 },
        symbol: "circle",
        symbolSize: 6,
        data: durationSeries,
      },
      {
        name: "效率指数",
        type: "line",
        yAxisIndex: 1,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        data: efficiencySeries,
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

<style scoped>
.user-trend-chart {
  width: 100%;
  min-height: 280px;
  background: var(--surface-card);
  border-radius: 12px;
  padding: 12px;
  box-shadow: var(--box-shadow-card);
  border: 1px solid var(--color-border-card);
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 260px;
}
</style>
