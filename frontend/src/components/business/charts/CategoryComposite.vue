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

      <div :class="['right-panel', view === 'drilldown' ? 'has-drilldown' : '']">
        <div v-if="view === 'drilldown'" class="panel-header">
          <el-button class="panel-back" type="primary" text :icon="ArrowLeft" @click="goBack">
            {{ TEXT.back }}
          </el-button>
          <span class="panel-title">{{ drilldownPanelTitle }}</span>
        </div>
        <div class="panel-chart">
          <BarChart :data="barData" :title="barTitle" :colors="chartColors" />
        </div>
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
        d="M12 22C6.477 22 2 17.523 2 12S6.477 2 12 2s10 4.477 10 10-4.477 10-10 10Zm0-2a8 8 0 1 0 0-16 8 8 0 0 0 0 16Zm-.75-11.5h1.5V11h-1.5V8.5Zm0 3h1.5V16h-1.5v-4.5Z"
      />
    </svg>
    <p class="empty-text">{{ TEXT.empty }}</p>
  </div>
</template>

<script setup>
import { ref, computed, watch } from "vue";
import { ArrowLeft } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import DoughnutChart from "./components/DoughnutChart.vue";
import BarChart from "./components/BarChart.vue";
import { buildColors, calculateTotalHours } from "@/utils/charts";

const props = defineProps({
  main: { type: Object, default: () => ({}) },
  drilldown: { type: Object, default: () => ({}) },
});

const emit = defineEmits(["sliceClick", "back"]);

const view = ref("main");
const currentCategory = ref("");

const TEXT = {
  mainTitle: "\u5b66\u4e60\u65f6\u957f\u5360\u6bd4",
  drillTitleSuffix: "\u7684\u5b50\u5206\u7c7b\u5360\u6bd4",
  barMainTitle: "\u5168\u90e8\u5206\u7c7b",
  barDrillSuffix: "\u7684\u5b50\u5206\u7c7b",
  panelSuffix: "\u7684\u5b50\u5206\u7c7b\u65f6\u957f",
  back: "\u8fd4\u56de\u4e0a\u7ea7",
  empty: "\u5f53\u524d\u7b5b\u9009\u8303\u56f4\u6682\u65e0\u5206\u7c7b\u7edf\u8ba1\u6570\u636e",
  noChild: "\u8be5\u5206\u7c7b\u6682\u65e0\u5b50\u5206\u7c7b",
};

const hasData = computed(() => {
  if (view.value === "main") {
    return Boolean(props.main?.labels?.length);
  }
  const target = props.drilldown[currentCategory.value];
  return Boolean(target?.labels?.length);
});

const currentData = computed(() => {
  if (view.value === "main") {
    return props.main || {};
  }
  return props.drilldown[currentCategory.value] || {};
});

const totalHours = computed(() => calculateTotalHours(currentData.value));

const currentTitle = computed(() => {
  if (view.value === "main") {
    return TEXT.mainTitle;
  }
  return `${currentCategory.value} \u00b7 ${TEXT.drillTitleSuffix}`;
});

const barTitle = computed(() => {
  if (view.value === "main") {
    return TEXT.barMainTitle;
  }
  return `${currentCategory.value} \u00b7 ${TEXT.barDrillSuffix}`;
});

const drilldownPanelTitle = computed(() =>
  `${currentCategory.value} \u00b7 ${TEXT.panelSuffix}`
);

const chartColors = computed(() => {
  const length = currentData.value?.labels?.length || 0;
  return buildColors(Math.max(length, 6));
});

const doughnutData = computed(() => currentData.value);
const barData = computed(() => currentData.value);

function handleSliceClick(label) {
  if (view.value !== "main") return;
  const target = props.drilldown[label];
  if (!target || !target.labels?.length) {
    ElMessage.info(TEXT.noChild);
    return;
  }
  currentCategory.value = label;
  view.value = "drilldown";
  emit("sliceClick", label);
}

function goBack() {
  view.value = "main";
  currentCategory.value = "";
  emit("back");
}

defineExpose({ goBack });

watch(
  () => [props.drilldown, currentCategory.value],
  () => {
    if (
      view.value === "drilldown" &&
      !props.drilldown[currentCategory.value]?.labels?.length
    ) {
      view.value = "main";
      currentCategory.value = "";
      emit("back");
    }
  },
  { deep: true }
);
</script>

<style scoped>
.category-wrapper {
  width: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.main-grid {
  display: grid;
  grid-template-columns: minmax(320px, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: stretch;
}

.right-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-panel.has-drilldown {
  padding-top: 40px;
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 6px 12px;
  border-radius: 12px;
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid rgba(99, 102, 241, 0.25);
  backdrop-filter: blur(6px);
}

.panel-header :deep(.panel-back) {
  padding: 2px 6px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}

.panel-header :deep(.panel-back .el-icon) {
  font-size: 14px;
}

.panel-header :deep(.panel-back.el-button--text) {
  color: #4f46e5;
  font-weight: 600;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #4338ca;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.panel-chart {
  flex: 1;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  background: #ffffff;
  border-radius: 16px;
  border: 1px dashed rgba(99, 102, 241, 0.3);
  margin: 1rem 0;
}

.empty-icon {
  width: 56px;
  height: 56px;
  color: #94a3b8;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 15px;
  color: #64748b;
  margin: 0;
  max-width: 420px;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .main-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .main-grid {
    gap: 12px;
  }

  .right-panel {
    padding-top: 44px;
  }

  .panel-header {
    position: static;
    display: flex;
    margin-bottom: 8px;
  }
}
</style>

