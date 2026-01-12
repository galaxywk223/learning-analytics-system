<template>
  <div v-if="hasData" class="category-wrapper">
    <div class="main-grid">
      <DoughnutChart
        ref="doughnutRef"
        :data="doughnutData"
        :title="currentTitle"
        :total-hours="totalHours"
        :colors="chartColors"
        :metric-mode="metricMode"
        @slice-click="handleSliceClick"
      />

      <div
        :class="[
          'right-panel',
          view === 'drilldown' ? 'has-drilldown' : '',
          !showPanelHeader ? 'no-header' : '',
        ]"
      >
        <div
          v-if="showPanelHeader && view === 'drilldown'"
          class="panel-header"
        >
          <el-button
            class="panel-back"
            type="primary"
            text
            :icon="ArrowLeft"
            @click="goBack"
          >
            {{ TEXT.back }}
          </el-button>
          <span class="panel-title">{{ drilldownPanelTitle }}</span>
        </div>
        <div class="panel-chart">
          <BarChart
            ref="barRef"
            :data="barData"
            :title="barTitle"
            :colors="chartColors"
            :metric-mode="metricMode"
            @bar-click="handleSliceClick"
            @bar-hover="handleBarHover"
            @bar-leave="handleBarLeave"
          />
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
import { ref, computed, watch, nextTick } from "vue";
import { ArrowLeft } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";
import DoughnutChart from "./components/DoughnutChart.vue";
import BarChart from "./components/BarChart.vue";
import { buildColors, calculateTotalHours } from "@/utils/charts";

const props = defineProps({
  main: { type: Object, default: () => ({}) },
  drilldown: { type: Object, default: () => ({}) },
  showPanelHeader: { type: Boolean, default: true },
  metricMode: { type: String, default: "duration" }, // 'duration' | 'efficiency'
});

const emit = defineEmits(["sliceClick", "back"]);

const view = ref("main");
const currentCategory = ref("");
const barRef = ref(null);
const doughnutRef = ref(null);

const TEXT = computed(() => ({
  mainTitle:
    props.metricMode === "efficiency" ? "学习效率占比" : "学习时长占比",
  drillTitleSuffix:
    props.metricMode === "efficiency" ? "的子分类效率占比" : "的子分类占比",
  barMainTitle:
    props.metricMode === "efficiency" ? "全部分类（效率）" : "全部分类",
  barDrillSuffix:
    props.metricMode === "efficiency" ? "的子分类（效率）" : "的子分类",
  panelSuffix:
    props.metricMode === "efficiency" ? "的子分类效率" : "的子分类时长",
  back: "返回上级",
  empty: "当前筛选范围暂无分类统计数据",
  noChild: "该分类暂无子分类",
}));

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
    return TEXT.value.mainTitle;
  }
  return `${currentCategory.value} · ${TEXT.value.drillTitleSuffix}`;
});

const barTitle = computed(() => {
  if (view.value === "main") {
    return TEXT.value.barMainTitle;
  }
  return `${currentCategory.value} · ${TEXT.value.barDrillSuffix}`;
});

const drilldownPanelTitle = computed(
  () => `${currentCategory.value} · ${TEXT.value.panelSuffix}`,
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
    ElMessage.info(TEXT.value.noChild);
    return;
  }
  currentCategory.value = label;
  view.value = "drilldown";
  emit("sliceClick", label);
  // 进入下钻后，将条形图滚动到顶部
  nextTick(() => {
    barRef.value?.scrollToTop?.();
  });
}

function goBack() {
  view.value = "main";
  currentCategory.value = "";
  emit("back");
  // 返回主视图时重置条形图滚动
  nextTick(() => {
    barRef.value?.scrollToTop?.();
  });
}

defineExpose({ goBack });

function handleBarHover(label) {
  doughnutRef.value?.highlightSlice?.(label);
}

function handleBarLeave() {
  doughnutRef.value?.clearHighlight?.();
}

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
  { deep: true },
);
</script>

<style scoped lang="scss">
.category-wrapper {
  width: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
}

.main-grid {
  display: grid;
  grid-template-columns: 3fr 7fr;
  gap: 24px;
  align-items: stretch;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.right-panel {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.right-panel.has-drilldown {
  padding-top: 48px;
}

.right-panel.no-header {
  padding-top: 0;
}

.panel-header {
  position: absolute;
  top: 0;
  left: 0;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0;
  background: transparent;
  border: none;
  backdrop-filter: none;
}

.panel-header :deep(.panel-back) {
  padding: 8px 12px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 15px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  transition: all 0.2s ease;

  &:hover {
    background: #f2f2f7;
    transform: translateY(-1px);
  }
}

.panel-header :deep(.panel-back .el-icon) {
  font-size: 16px;
}

.panel-header :deep(.panel-back.el-button--text) {
  color: #007aff;
  font-weight: 600;
}

.panel-title {
  font-size: 17px;
  font-weight: 700;
  color: #1c1c1e;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-left: 8px;
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
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  margin: 1rem 0;
  border: none;
}

.empty-icon {
  width: 56px;
  height: 56px;
  color: #d1d1d6;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 15px;
  color: #8e8e93;
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
    gap: 16px;
  }

  .right-panel {
    padding-top: 52px;
  }

  .right-panel.no-header {
    padding-top: 0;
  }

  .panel-header {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    margin-bottom: 0;
  }
}
</style>
