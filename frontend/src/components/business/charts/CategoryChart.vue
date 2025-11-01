<template>
  <div class="chart-container">
    <v-chart class="chart" :option="option" autoresize @click="onChartClick" />
  </div>
</template>

<script setup>
import { computed } from "vue";
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
} from "echarts/components";
import VChart from "vue-echarts";

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  ToolboxComponent,
]);

const props = defineProps({
  data: { type: Array, default: () => [] },
  title: { type: String, default: "学习分类占比" },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
  drillable: { type: Boolean, default: true },
});

const emit = defineEmits(["sliceClick"]);

const option = computed(() => ({
  title: { text: props.title, left: "center" },
  tooltip: {
    trigger: "item",
    formatter: (params) => {
      const pct = props.total
        ? ((params.value / props.total) * 100).toFixed(1)
        : "0";
      return `${params.name}<br/>时长: ${params.value} min (${pct}%)`;
    },
  },
  legend: { orient: "vertical", left: "left" },
  series: [
    {
      name: "分类",
      type: "pie",
      radius: ["40%", "70%"],
      avoidLabelOverlap: true,
      data: props.data,
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: "rgba(0,0,0,0.4)",
        },
      },
      label: { formatter: "{b}\n{d}%" },
      cursor: props.drillable ? "pointer" : "default",
    },
  ],
  toolbox: { feature: { saveAsImage: {} } },
  animation: props.loading ? false : true,
}));

function onChartClick(event) {
  if (!props.drillable) return;
  // vue-echarts 将原生事件透传，需通过组件实例获取点击的 series 数据
  // 简化：尝试从 event 中抽取数据 (若后续需精准可使用 v-chart expose 的 chart 实例)
  const payload = event?.data || event; // 兼容不同结构
  if (payload && payload.id) emit("sliceClick", payload);
}
</script>

<style scoped>
.chart-container {
  height: 450px;
  position: relative;
}
.chart {
  height: 100%;
  width: 100%;
}
</style>
