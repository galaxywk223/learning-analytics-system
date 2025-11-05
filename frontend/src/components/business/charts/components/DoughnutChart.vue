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
      <div v-if="computedTotal > 0" class="doughnut-card__summary">
        <span class="label">{{ uiText.totalLabel }}</span>
        <strong>{{ computedTotal.toFixed(1) }}h</strong>
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
      itemWidth: 10,
      itemHeight: 10,
      textStyle: {
        color: "#1f2937",
        fontSize: 12,
      },
    },
    series: [
      {
        name: uiText.pieName,
        type: "pie",
        radius: ["56%", "84%"],
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
</script>

<style scoped lang="scss">
.doughnut-card {
  background: rgba(255, 255, 255, 0.96);
  border-radius: 20px;
  padding: 22px 22px 18px;
  border: 1px solid rgba(148, 163, 235, 0.4);
  box-shadow: 0 18px 48px rgba(99, 102, 241, 0.18);
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  overflow: hidden;

  &::after {
    content: "";
    position: absolute;
    inset: -120px 40% auto -120px;
    height: 280px;
    border-radius: 50%;
    background: radial-gradient(
      circle,
      rgba(129, 140, 248, 0.4) 0%,
      rgba(255, 255, 255, 0) 60%
    );
    filter: blur(90px);
    pointer-events: none;
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
      width: 36px;
      height: 36px;
      color: #6366f1;
      padding: 8px;
      border-radius: 12px;
      background: rgba(99, 102, 241, 0.12);
    }

    h5 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
      color: #1e1b4b;
    }

    p {
      margin: 4px 0 0;
      font-size: 12px;
      color: rgba(79, 70, 229, 0.7);
    }
  }

  &__summary {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    padding: 8px 14px;
    border-radius: 12px;
    background: linear-gradient(
      135deg,
      rgba(99, 102, 241, 0.12),
      rgba(79, 70, 229, 0.12)
    );
    position: relative;
    z-index: 1;

    .label {
      font-size: 11px;
      color: #6b7280;
      text-transform: uppercase;
      letter-spacing: 0.4px;
    }

    strong {
      font-size: 18px;
      color: #312e81;
      font-weight: 700;
    }
  }

  &__chart {
    width: 100%;
    height: 320px;
    position: relative;
    z-index: 1;

    @media (max-width: 768px) {
      height: 300px;
    }
  }
}

@media (max-width: 768px) {
  .doughnut-card {
    padding: 20px 16px;
  }
}
</style>

