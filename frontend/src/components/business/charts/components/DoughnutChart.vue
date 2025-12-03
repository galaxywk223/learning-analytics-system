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
import { computed, ref } from "vue";
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
});

const emit = defineEmits(["slice-click"]);

const chartRef = ref();

const EMPTY_SLICE_NAME = "\u6682\u65e0\u6570\u636e";
const LEGEND_LIMIT = 10;
const chartUpdateOptions = { replaceMerge: ["series", "legend"] };
const uiText = {
  subtitle: "\u5206\u7c7b\u65f6\u957f\u5360\u6bd4",
  totalLabel: "\u7d2f\u8ba1",
  hoursSuffix: "\u5c0f\u65f6",
  pieName: "\u5b66\u4e60\u5206\u7c7b",
};
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
      backgroundColor: "rgba(30, 27, 75, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#f8fafc" },
      formatter: ({ name, value, percent }) => {
        const numeric = Number(value ?? 0).toFixed(2);
        const percentText = Number(percent ?? 0).toFixed(1);
        return `${name}<br/>${numeric} ${uiText.hoursSuffix} (${percentText}%)`;
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
        color: "#6b7280",
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
                      text: uiText.totalLabel,
                      fill: "#9ca3af",
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
                      fill: "#0f172a",
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
                      text: uiText.hoursSuffix,
                      fill: "#9ca3af",
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
        name: uiText.pieName,
        type: "pie",
        radius: ["68%", "86%"],
        center: ["50%", "48%"],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: "#fff",
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
</script>

<style scoped lang="scss">
.doughnut-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 24px;
  border: none;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
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
      color: #5856D6; /* Indigo */
      padding: 6px;
      border-radius: 10px;
      background: rgba(88, 86, 214, 0.1);
    }

    h5 {
      margin: 0;
      font-size: 17px;
      font-weight: 700;
      color: #1c1c1e;
      letter-spacing: -0.5px;
    }

    p {
      margin: 2px 0 0;
      font-size: 13px;
      color: #8e8e93;
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
      color: #8e8e93;
      font-size: 13px;
      font-weight: 600;
    }

    .center-value {
      color: #1c1c1e;
      font-size: 28px;
      font-weight: 800;
      line-height: 1.2;
      letter-spacing: -0.5px;
    }

    .center-unit {
      color: #8e8e93;
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
```
