<template>
  <div class="bar-card">
    <header class="bar-card__header">
      <div class="bar-card__title">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M3 13h5v8H3v-8Zm6-6h5v14h-5V7Zm6 4h6v10h-6V11Z" />
        </svg>
        <h5>{{ title }}</h5>
      </div>
      <span class="bar-card__badge">{{ badgeText }}</span>
    </header>
    <div class="bar-card__chart-wrapper">
      <v-chart
        class="bar-card__chart"
        :option="option"
        :update-options="chartUpdateOptions"
        autoresize
        :style="chartStyle"
      />
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { use } from "echarts/core";
import { BarChart as EBarChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";

use([CanvasRenderer, EBarChart, GridComponent, TooltipComponent]);

const props = defineProps({
  data: { type: Object, required: true },
  title: { type: String, default: "High Frequency Categories" },
  colors: { type: Array, default: () => [] },
});

const chartUpdateOptions = { replaceMerge: ["series", "yAxis"] };

const normalized = computed(() => {
  const labels = Array.isArray(props.data?.labels) ? props.data.labels : [];
  const values = Array.isArray(props.data?.data) ? props.data.data : [];

  return labels.map((label, idx) => {
    const hasLabel = typeof label === "string" && label.trim().length > 0;
    const name = hasLabel ? label.trim() : `Unnamed Category ${idx + 1}`;
    const rawValue = values[idx];
    const numeric = Number(rawValue ?? 0);
    return { name, value: Number.isFinite(numeric) ? numeric : 0 };
  });
});

const sortedData = computed(() => {
  const items = [...normalized.value];
  return items.sort((a, b) => {
    if (b.value === a.value) {
      return a.name.localeCompare(b.name);
    }
    return b.value - a.value;
  });
});

const displayCount = computed(() => sortedData.value.length);

const badgeText = computed(() => `Total ${displayCount.value} items`);

const chartHeight = computed(() => {
  const rows = Math.max(1, displayCount.value);
  return Math.max(340, rows * 42 + 140);
});

const chartStyle = computed(() => ({
  height: `${chartHeight.value}px`,
  minHeight: "320px",
}));

const barColors = computed(() => {
  if (props.colors?.length) {
    return props.colors.slice(0, displayCount.value);
  }
  return [
    "#6366f1",
    "#22d3ee",
    "#f97316",
    "#0ea5e9",
    "#facc15",
    "#10b981",
    "#f472b6",
    "#fb7185",
    "#14b8a6",
    "#8b5cf6",
  ];
});

const categoryNames = computed(() => sortedData.value.map((item) => item.name));

const longestLabelLength = computed(() =>
  categoryNames.value.reduce((max, name) => Math.max(max, name ? name.length : 0), 0)
);

const axisLabelWidth = computed(() => {
  const charWidth = 6.25;
  const estimated = longestLabelLength.value * charWidth;
  return Math.min(110, Math.max(68, Math.round(estimated)));
});

const gridLeft = computed(() => axisLabelWidth.value + 22);

const seriesData = computed(() =>
  sortedData.value.map((item, idx) => ({
    value: Number.parseFloat(Number(item.value ?? 0).toFixed(2)),
    itemStyle: { color: barColors.value[idx % barColors.value.length] },
  }))
);

const option = computed(() => {
  const categories = categoryNames.value;

  return {
    color: barColors.value,
    grid: {
      left: gridLeft.value,
      right: 48,
      top: 24,
      bottom: 24,
      containLabel: true,
    },
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params) => {
        const item = Array.isArray(params) ? params[0] : params;
        if (!item) return "";
        const value = Number(item.value ?? 0);
        return `${item.name}<br/>${value.toFixed(1)} 小时`;
      },
    },
    xAxis: {
      type: "value",
      splitLine: { show: false },
      axisLabel: { color: "#475569" },
    },
    yAxis: {
      type: "category",
      inverse: true,
      data: categories,
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: "#334155",
        fontSize: 12,
        interval: 0,
        margin: 12,
        align: "right",
        width: axisLabelWidth.value,
        overflow: "break",
        lineHeight: 16,
      },
    },
    series: [
      {
        type: "bar",
        barWidth: 18,
        barCategoryGap: "26%",
        itemStyle: { borderRadius: [0, 12, 12, 0] },
        emphasis: {
          itemStyle: {
            opacity: 0.85,
          },
        },
        data: seriesData.value,
        label: {
          show: true,
          position: "right",
          formatter: ({ value }) => `${Number(value ?? 0).toFixed(1)}h`,
          color: "#1f2937",
          fontSize: 12,
        },
      },
    ],
  };
});
</script>

<style scoped>
.bar-card {
  background: #ffffff;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 235, 0.35);
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 280px;
}

.bar-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-card__title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1f1d47;

  svg {
    width: 20px;
    height: 20px;
    color: #6366f1;
  }

  h5 {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
  }
}

.bar-card__badge {
  font-size: 12px;
  color: #4f46e5;
  background: rgba(99, 102, 241, 0.12);
  border-radius: 999px;
  padding: 4px 12px;
  font-weight: 600;
}

.bar-card__chart-wrapper {
  flex: 1;
  max-height: 420px;
  overflow-y: auto;
  margin-right: -6px;
  padding-right: 6px;
}

.bar-card__chart-wrapper::-webkit-scrollbar {
  width: 6px;
}

.bar-card__chart-wrapper::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 999px;
}

.bar-card__chart {
  width: 100%;
}
</style>
