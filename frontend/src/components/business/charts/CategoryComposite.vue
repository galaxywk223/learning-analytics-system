<template>
  <div class="category-wrapper" v-if="hasData">
    <div class="main-grid">
      <DoughnutChart
        :data="doughnutData"
        :title="currentTitle"
        :total-hours="totalHours"
        :colors="chartColors"
        @slice-click="handleSliceClick"
      />

      <div class="right-panel">
        <BarChart
          :data="barData"
          :title="barTitle"
          :top-n="TOP_N"
          :colors="chartColors"
        />

        <DataTable
          :data="tableData"
          :total-hours="totalHours"
          :drilldown-data="drilldown"
          :show-navigation="view === 'drilldown'"
          :is-main-view="view === 'main'"
          @drill-down="handleDrillDown"
          @back="goBack"
        />
      </div>
    </div>
  </div>
  <div v-else class="empty-state">
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      class="empty-icon"
    >
      <path
        d="M12 22C6.47715 22 2 17.5228 2 12C2 6.47715 6.47715 2 12 2C17.5228 2 22 6.47715 22 12C22 17.5228 17.5228 22 12 22ZM12 20C16.4183 20 20 16.4183 20 12C20 7.58172 16.4183 4 12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20ZM11 7H13V9H11V7ZM11 11H13V17H11V11Z"
      />
    </svg>
    <p class="empty-text">当前筛选范围内没有找到任何带分类的学习记录</p>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from "vue";
import DoughnutChart from "./components/DoughnutChart.vue";
import BarChart from "./components/BarChart.vue";
import DataTable from "./components/DataTable.vue";
import {
  buildColors,
  transformDataForChart,
  calculateTotalHours,
  formatTableData,
} from "@/utils/charts";

const props = defineProps({
  main: { type: Object, default: () => ({}) },
  drilldown: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["sliceClick"]);

// 响应式数据
const view = ref("main");
const currentCategory = ref("");
const TOP_N = 10;

// 计算属性
const hasData = computed(() => {
  if (view.value === "main") {
    return props.main && props.main.labels && props.main.labels.length > 0;
  } else {
    const dl = props.drilldown[currentCategory.value];
    return dl && dl.labels && dl.labels.length > 0;
  }
});

const currentData = computed(() => {
  if (view.value === "main") {
    return props.main;
  } else {
    return props.drilldown[currentCategory.value] || {};
  }
});

const totalHours = computed(() => calculateTotalHours(currentData.value));

const currentTitle = computed(() => {
  if (view.value === "main") {
    return "分类时长占比";
  } else {
    return `${currentCategory.value} - 子分类占比`;
  }
});

const barTitle = computed(() => {
  if (view.value === "main") {
    return "分类时长排行";
  } else {
    return `${currentCategory.value} - 子分类排行`;
  }
});

const chartColors = computed(() => {
  const dataLength = currentData.value?.labels?.length || 0;
  return buildColors(dataLength);
});

const doughnutData = computed(() => currentData.value);

const barData = computed(() => transformDataForChart(currentData.value, TOP_N));

const tableData = computed(() => formatTableData(currentData.value));

// 事件处理
function handleSliceClick(label) {
  if (view.value === "main" && props.drilldown[label]?.labels?.length > 0) {
    handleDrillDown(label);
  }
}

function handleDrillDown(category) {
  currentCategory.value = category;
  view.value = "drilldown";
  emit("sliceClick", category);
}

function goBack() {
  view.value = "main";
  currentCategory.value = "";
}

// 监听器
watch(
  () => props.main,
  () => {
    if (
      view.value === "drilldown" &&
      !props.drilldown[currentCategory.value]?.labels?.length
    ) {
      goBack();
    }
  },
  { deep: true }
);
</script>

<style scoped>
.category-wrapper {
  width: 100%;
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.main-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  align-items: stretch;
  height: 100%;
  max-height: calc(100vh - 280px);
}

.right-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  min-height: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  background: #ffffff;
  border-radius: 12px;
  border: 1px dashed #d1c4e9;
  margin: 1rem 0;
}

.empty-icon {
  width: 56px;
  height: 56px;
  color: #9ca3af;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 15px;
  color: #6b7280;
  margin: 0;
  max-width: 400px;
  line-height: 1.5;
}

@media (max-width: 1200px) {
  .main-grid {
    grid-template-columns: 1fr;
    gap: 1.5rem;
  }
}

@media (max-width: 768px) {
  .category-wrapper {
    padding: 0;
  }

  .main-grid {
    gap: 1rem;
  }

  .right-panel {
    gap: 1rem;
  }

  .empty-state {
    padding: 40px 20px;
  }

  .empty-icon {
    width: 48px;
    height: 48px;
  }

  .empty-text {
    font-size: 14px;
  }
}
</style>
