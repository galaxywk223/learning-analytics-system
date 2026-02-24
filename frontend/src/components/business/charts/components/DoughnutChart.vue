<template>
  <div class="doughnut-card">
    <header class="doughnut-card__header">
      <div class="doughnut-card__title">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path
            d="M11.5 2.00488C6.255 2.00488 2 6.25988 2 11.5049C2 16.7499 6.255 21.0049 11.5 21.0049C16.745 21.0049 21 16.7499 21 11.5049H11.5V2.00488ZM22.5 10.0049C22.5 5.03488 18.47 1.00488 13.5 1.00488C12.973 1.00488 12.454 1.04888 11.948 1.13488C11.488 1.21288 11.2 1.66588 11.338 2.11188L13.772 10.0179C13.872 10.3369 14.16 10.5549 14.495 10.5549H22.001C22.276 10.5549 22.5 10.3319 22.5 10.0549V10.0049Z"
          />
        </svg>
        <div>
          <h5>{{ title }}</h5>
          <p>{{ uiText.subtitle }}</p>
        </div>
      </div>
    </header>
    <v-chart
      ref="chartRef"
      class="doughnut-card__chart"
      :option="option"
      :update-options="chartUpdateOptions"
      autoresize
      @click="handleSliceClick"
    />
    <div v-if="computedTotal > 0" class="doughnut-card__center">
      <span class="center-label">{{ uiText.totalLabel }}</span>
      <span class="center-value">{{ computedTotal.toFixed(1) }}</span>
      <span class="center-unit">{{ uiText.hoursSuffix }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from "vue";
import { use } from "echarts/core";
import { PieChart } from "echarts/charts";
import { TooltipComponent, LegendComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent]);

const props = defineProps({
  data: {
    type: Object,
    required: true,
  },
  title: {
    type: String,
    default: "\u5b66\u4e60\u65f6\u957f\u5360\u6bd4",
  },
  totalHours: {
    type: Number,
    default: 0,
  },
  colors: {
    type: Array,
    default: () => [
      "#6366f1",
      "#f97316",
      "#0ea5e9",
      "#22c55e",
      "#facc15",
      "#ef4444",
      "#8b5cf6",
    ],
  },
  metricMode: {
    type: String,
    default: "duration", // 'duration' | 'efficiency'
  },
});

const emit = defineEmits(["slice-click"]);

const chartRef = ref();
const themeVersion = ref(0);
let themeObserver = null;

const EMPTY_SLICE_NAME = "\u6682\u65e0\u6570\u636e";
const LEGEND_LIMIT = 10;
const chartUpdateOptions = { replaceMerge: ["series", "legend"] };

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
    textBase: readThemeVar("--color-text-base", "#1f2937"),
    textSecondary: readThemeVar("--color-text-secondary", "#6b7280"),
    textMuted: readThemeVar("--color-text-muted", "#9ca3af"),
    textHeading: readThemeVar("--color-text-heading", "#0f172a"),
    card: readThemeVar("--surface-card", "#ffffff"),
    border: readThemeVar("--color-border-card", "#e2e8f0"),
    inverse: readThemeVar("--color-text-inverse", "#ffffff"),
    primary: readThemeVar("--color-primary", "#6366f1"),
    primaryLight: readThemeVar("--color-primary-light", "#dee4ff"),
  };
});

const uiText = computed(() => ({
  subtitle: props.metricMode === "efficiency" ? "分类效率占比" : "分类时长占比",
  totalLabel: props.metricMode === "efficiency" ? "效率总量" : "累计",
  hoursSuffix: props.metricMode === "efficiency" ? "" : "小时",
  pieName: props.metricMode === "efficiency" ? "学习效率" : "学习分类",
  tooltipUnit: props.metricMode === "efficiency" ? "效率" : "小时",
}));
const baseSlices = computed(() => {
  const labels = Array.isArray(props.data?.labels) ? props.data.labels : [];
  const values = Array.isArray(props.data?.data) ? props.data.data : [];
  return labels.map((label, index) => ({
    name: label,
    value: Number(values[index] ?? 0),
  }));
});

const seriesData = computed(() => {
  const cleaned = baseSlices.value.filter((item) => item.value > 0);
  return cleaned.length ? cleaned : [{ name: EMPTY_SLICE_NAME, value: 1 }];
});

const legendLabels = computed(() => {
  const sorted = [...seriesData.value]
    .filter((item) => item.value > 0 && item.name !== EMPTY_SLICE_NAME)
    .sort((a, b) => b.value - a.value);
  return sorted.slice(0, LEGEND_LIMIT).map((item) => item.name);
});

const computedTotal = computed(() => {
  if (props.totalHours && props.totalHours > 0) {
    return Number(props.totalHours);
  }
  return baseSlices.value.reduce((sum, item) => sum + item.value, 0);
});

const option = computed(() => {
  const palette = props.colors.length
    ? props.colors
    : [
        "#6366f1",
        "#f97316",
        "#0ea5e9",
        "#22c55e",
        "#facc15",
        "#ef4444",
        "#8b5cf6",
      ];

  return {
    color: palette,
    animation: false,
    tooltip: {
      trigger: "item",
      backgroundColor: themeTokens.value.card,
      borderColor: themeTokens.value.border,
      borderWidth: 1,
      textStyle: { color: themeTokens.value.textBase },
      formatter: ({ name, value, percent }) => {
        const numeric = Number(value ?? 0).toFixed(2);
        const percentText = Number(percent ?? 0).toFixed(1);
        const unit = uiText.value.tooltipUnit;
        const suffix = unit ? ` ${unit}` : "";
        return `${name}<br/>${numeric}${suffix} (${percentText}%)`;
      },
    },
    legend: {
      type: "scroll",
      orient: "horizontal",
      bottom: 0,
      left: "center",
      data: legendLabels.value,
      icon: "circle",
      itemWidth: 8,
      itemHeight: 8,
      itemGap: 14,
      textStyle: {
        color: themeTokens.value.textSecondary,
        fontSize: 12,
      },
    },
    graphic:
      computedTotal.value > 0
        ? {
            elements: [
              {
                type: "group",
                left: "center",
                top: "42%",
                children: [
                  {
                    type: "text",
                    style: {
                      text: uiText.value.totalLabel,
                      fill: themeTokens.value.textMuted,
                      fontSize: 13,
                      fontWeight: 600,
                      textAlign: "center",
                    },
                    left: "center",
                  },
                  {
                    type: "text",
                    top: 22,
                    style: {
                      text: `${computedTotal.value.toFixed(1)}`,
                      fill: themeTokens.value.textHeading,
                      fontSize: 26,
                      fontWeight: 800,
                      textAlign: "center",
                    },
                    left: "center",
                  },
                  {
                    type: "text",
                    top: 48,
                    style: {
                      text: uiText.value.hoursSuffix,
                      fill: themeTokens.value.textMuted,
                      fontSize: 12,
                      fontWeight: 600,
                      textAlign: "center",
                    },
                    left: "center",
                  },
                ],
              },
            ],
          }
        : undefined,
    series: [
      {
        name: uiText.value.pieName,
        type: "pie",
        radius: ["68%", "86%"],
        center: ["50%", "48%"],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: themeTokens.value.card,
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        labelLine: {
          show: false,
        },
        data: seriesData.value,
      },
    ],
  };
});

function handleSliceClick(params) {
  if (!params?.data?.name) return;
  emit("slice-click", params.data.name);
}

function highlightSlice(label) {
  const chart = chartRef.value;
  const series = seriesData.value;
  if (!chart || !series?.length) return;
  chart.dispatchAction({ type: "downplay", seriesIndex: 0 });
  const idx = series.findIndex((item) => item.name === label);
  if (idx >= 0) {
    chart.dispatchAction({ type: "highlight", seriesIndex: 0, dataIndex: idx });
  }
}

function clearHighlight() {
  const chart = chartRef.value;
  if (!chart) return;
  chart.dispatchAction({ type: "downplay", seriesIndex: 0 });
}

defineExpose({ highlightSlice, clearHighlight });

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
.doughnut-card {
  background: var(--surface-card);
  border-radius: 24px;
  padding: 24px;
  border: 1px solid var(--color-border-card);
  box-shadow: var(--box-shadow-card);
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--box-shadow-hover);
  }

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
    position: relative;
    z-index: 1;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 12px;

    svg {
      width: 32px;
      height: 32px;
      color: var(--color-primary);
      padding: 6px;
      border-radius: 10px;
      background: var(--color-primary-light);
    }

    h5 {
      margin: 0;
      font-size: 17px;
      font-weight: 700;
      color: var(--color-text-heading);
      letter-spacing: -0.5px;
    }

    p {
      margin: 2px 0 0;
      font-size: 13px;
      color: var(--color-text-secondary);
    }
  }

  &__chart {
    width: 100%;
    height: 340px;
    position: relative;
    z-index: 1;

    @media (max-width: 768px) {
      height: 300px;
    }
  }

  &__center {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    pointer-events: none;
    text-align: center;
    gap: 2px;
    z-index: 2;

    .center-label {
      color: var(--color-text-secondary);
      font-size: 13px;
      font-weight: 600;
    }

    .center-value {
      color: var(--color-text-heading);
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
      letter-spacing: -0.5px;
    }

    .center-unit {
      color: var(--color-text-secondary);
      font-size: 12px;
      font-weight: 600;
    }
  }
}

@media (max-width: 768px) {
  .doughnut-card {
    padding: 20px;
  }
}
</style>
