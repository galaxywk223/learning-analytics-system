<template>
  <div class="user-category-chart">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { computed } from "vue";
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

const option = computed(() => {
  const source = (props.data || []).map((item) => {
    const hours = Number(item?.hours ?? item?.value ?? 0);
    return {
      name: item?.name ?? "未分类",
      value: Math.max(Math.round(hours * 100) / 100, 0),
    };
  });

  const totalHours = source.reduce((sum, item) => sum + item.value, 0);

  return {
    color: ["#6366f1", "#f97316", "#10b981", "#14b8a6", "#facc15", "#ef4444", "#8b5cf6"],
    tooltip: {
      trigger: "item",
      formatter: ({ name, value, percent }) =>
        `${name}<br/>${value.toFixed(2)} 小时 (${percent}%)`,
    },
    legend: {
      orient: "vertical",
      right: 0,
      top: "middle",
      icon: "circle",
    },
    series: [
      {
        name: "学习分类",
        type: "pie",
        radius: ["45%", "70%"],
        center: ["40%", "50%"],
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
          borderColor: "#fff",
          borderWidth: 1,
        },
      },
    ],
    graphic:
      totalHours > 0
        ? [
            {
              type: "text",
              left: "40%",
              top: "42%",
              style: {
                text: totalHours.toFixed(1),
                textAlign: "center",
                fill: "#111827",
                fontSize: 22,
                fontWeight: 600,
              },
            },
            {
              type: "text",
              left: "40%",
              top: "58%",
              style: {
                text: "总时长 (小时)",
                textAlign: "center",
                fill: "#6b7280",
                fontSize: 12,
              },
            },
          ]
        : [],
  };
});
</script>

<style scoped>
.user-category-chart {
  width: 100%;
  min-height: 260px;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 240px;
}
</style>
