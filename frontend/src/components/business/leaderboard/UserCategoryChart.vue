<template>
  <div class="user-category-chart">
    <v-chart class="chart" :option="option" autoresize />
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
    textBase: readThemeVar("--color-text-base", "#1f2937"),
    textSecondary: readThemeVar("--color-text-secondary", "#6b7280"),
    textHeading: readThemeVar("--color-text-heading", "#111827"),
    card: readThemeVar("--surface-card", "#ffffff"),
    border: readThemeVar("--color-border-card", "#e2e8f0"),
  };
});

const option = computed(() => {
  const token = themeTokens.value;
  const source = (props.data || []).map((item) => {
    const hours = Number(item?.hours ?? item?.value ?? 0);
    return {
      name: item?.name ?? "未分类",
      value: Math.max(Math.round(hours * 100) / 100, 0),
    };
  });

  const totalHours = source.reduce((sum, item) => sum + item.value, 0);

  return {
    color: [
      "#6366f1",
      "#f97316",
      "#10b981",
      "#14b8a6",
      "#facc15",
      "#ef4444",
      "#8b5cf6",
    ],
    animation: false,
    tooltip: {
      trigger: "item",
      backgroundColor: token.card,
      borderColor: token.border,
      borderWidth: 1,
      textStyle: { color: token.textBase },
      formatter: ({ name, value, percent }) =>
        `${name}<br/>${value.toFixed(2)} 小时 (${percent}%)`,
    },
    legend: {
      type: "scroll",
      orient: "horizontal",
      bottom: 0,
      left: "center",
      icon: "circle",
      textStyle: {
        color: token.textSecondary,
      },
    },
    series: [
      {
        name: "学习分类",
        type: "pie",
        radius: ["45%", "70%"],
        center: ["50%", "48%"],
        avoidLabelOverlap: true,
        label: {
          formatter: "{b}\n{d}%",
        },
        labelLine: {
          smooth: true,
        },
        data: source.length
          ? source
          : [
              {
                value: 1,
                name: "暂无数据",
              },
            ],
        itemStyle: {
          borderRadius: 8,
          borderColor: token.card,
          borderWidth: 1,
        },
      },
    ],
    graphic:
      totalHours > 0
        ? [
            {
              type: "text",
              left: "50%",
              top: "42%",
              style: {
                text: totalHours.toFixed(1),
                textAlign: "center",
                fill: token.textHeading,
                fontSize: 22,
                fontWeight: 600,
              },
            },
            {
              type: "text",
              left: "50%",
              top: "60%",
              style: {
                text: "总时长 (小时)",
                textAlign: "center",
                fill: token.textSecondary,
                fontSize: 12,
              },
            },
          ]
        : [],
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
.user-category-chart {
  width: 100%;
  min-height: 260px;
  background: var(--surface-card);
  border-radius: 12px;
  padding: 12px;
  box-shadow: var(--box-shadow-card);
  border: 1px solid var(--color-border-card);
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 240px;
}
</style>
