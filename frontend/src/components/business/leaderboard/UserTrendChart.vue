<template>
  <div class="user-trend-chart">
    <v-chart class="chart" :option="option" autoresize />
  </div>
</template>

<script setup>
import { computed } from "vue";
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

const option = computed(() => {
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
    color: ["#2563eb", "#f97316"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "cross" },
    },
    legend: {
      top: 0,
      icon: "circle",
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
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: categories,
      axisLabel: {
        formatter: (value) => value.slice(5),
      },
    },
    yAxis: [
      {
        type: "value",
        name: "学习时长 (小时)",
        min: 0,
        axisLabel: { formatter: (val) => `${val}` },
        splitLine: { lineStyle: { type: "dashed" } },
      },
      {
        type: "value",
        name: "效率指数",
        min: 0,
        axisLabel: { formatter: (val) => `${val}` },
        splitLine: { lineStyle: { type: "dashed" } },
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
</script>

<style scoped>
.user-trend-chart {
  width: 100%;
  min-height: 280px;
  background: #fff;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.chart {
  width: 100%;
  height: 100%;
  min-height: 260px;
}
</style>
