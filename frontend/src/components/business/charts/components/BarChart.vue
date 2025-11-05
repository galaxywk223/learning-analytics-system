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

// 当标签长度变化或布局变化时，需要同时更新 grid 和 yAxis
const chartUpdateOptions = { replaceMerge: ["series", "yAxis", "grid"] };

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

// 将标签按字符数截断，超出 4 个字符用 ...
const truncateLabel = (text, limit = 4) => {
  if (!text) return "";
  let out = "";
  let count = 0;
  for (const ch of String(text)) {
    if (count >= limit) break;
    out += ch;
    count += 1;
  }
  // 使用 code point 计算长度，避免多字节被截断
  const len = Array.from(String(text)).length;
  return len > limit ? `${out}...` : out;
};

const truncatedAxisLabels = computed(() =>
  categoryNames.value.map((n) => truncateLabel(n))
);

// 估算标签文字宽度（px），用于计算 grid.left
const estimateTextWidth = (text, fontSize = 12) => {
  if (!text) return 0;
  let units = 0;
  for (const ch of String(text)) {
    const code = ch.codePointAt(0) || 0;
    // 粗略估算：ASCII 0.6 单位，CJK/其他 1.0 单位
    units += code <= 0x7f ? 0.6 : 1.0;
  }
  return Math.ceil(units * fontSize);
};

const maxLabelWidth = computed(() => {
  // 网格左边距基于截断后的标签宽度，避免长名称把柱子挤到右侧
  const names = truncatedAxisLabels.value;
  if (!names.length) return 0;
  const size = 12; // 与 axisLabel.fontSize 保持一致
  return Math.max(...names.map((n) => estimateTextWidth(n, size)));
});

// grid.left 为标签预留空间：基本间距 8px + 估算宽度，限制最大 160px
const gridLeft = computed(() => {
  const base = 8;
  const cap = 160;
  return Math.min(Math.max(base, maxLabelWidth.value + base), cap);
});

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
      // 为左侧分类名称预留空间，避免与柱子重叠且不被裁切
      left: gridLeft.value,
      right: 40,
      top: 24,
      bottom: 24,
      containLabel: false,
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
      // 使用原始名称作为数据，工具提示仍可显示完整名称
      data: categories,
      axisTick: { show: false },
      axisLine: { show: false },
      // 左侧显示分类名称，放在网格之外，避免与柱子重叠
      axisLabel: {
        show: true,
        inside: false,
        color: "#1f2937",
        fontSize: 12,
        // 在左轴上将文字右对齐，这样文本位于轴线左侧
        align: "right",
        margin: 4,
        formatter: (val) => truncateLabel(val, 4),
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
