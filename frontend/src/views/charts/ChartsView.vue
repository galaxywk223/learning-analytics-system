<template>
  <div class="charts-view">
    <div class="page-header">
      <div class="header-content">
        <h1>📊 统计分析</h1>
        <p class="lead">通过数据洞察学习模式，掌握成长轨迹</p>
      </div>
    </div>

    <div class="toolbar-container">
      <div class="toolbar-left">
        <!-- Tabs 按钮组 -->
        <div class="btn-group tab-switch">
          <button
            :class="['btn', charts.activeTab === 'trends' && 'active']"
            @click="charts.setActiveTab('trends')"
          >
            📈 趋势分析
          </button>
          <button
            :class="['btn', charts.activeTab === 'categories' && 'active']"
            @click="charts.setActiveTab('categories')"
          >
            🎯 分类占比
          </button>
          <button
            :class="['btn', charts.activeTab === 'cattrend' && 'active']"
            @click="charts.setActiveTab('cattrend')"
          >
            📉 分类趋势
          </button>
        </div>
        <!-- 周/日视图切换，仅在趋势分析 tab 显示 -->
        <div class="btn-group view-switch" v-if="charts.activeTab === 'trends'">
          <button
            :class="['btn', charts.viewType === 'weekly' && 'active']"
            @click="charts.setViewType('weekly')"
          >
            📅 周视图
          </button>
          <button
            :class="['btn', charts.viewType === 'daily' && 'active']"
            @click="charts.setViewType('daily')"
          >
            📆 日视图
          </button>
        </div>
      </div>
      <div
        class="category-filters"
        v-if="['categories', 'cattrend'].includes(charts.activeTab)"
      >
        <div class="btn-group filter-switch">
          <button
            v-for="mode in categoryModes"
            :key="mode.value"
            :class="['btn', rangeMode === mode.value && 'active']"
            @click="onRangeModeChange(mode.value)"
          >
            {{ mode.label }}
          </button>
        </div>
        <div class="filter-inputs">
          <select
            v-if="rangeMode === 'stage'"
            class="stage-select"
            v-model="stageSelected"
            @change="onStageChange"
          >
            <option value="all">全部历史</option>
            <option v-for="s in charts.stages" :key="s.id" :value="s.id">
              {{ s.name }}
            </option>
          </select>
          <el-date-picker
            v-else-if="rangeMode === 'daily'"
            v-model="datePoint"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择日期"
            clearable
            @clear="onFilterCleared"
            :disabled="charts.loading"
          />
          <el-date-picker
            v-else-if="rangeMode === 'weekly'"
            v-model="datePoint"
            type="date"
            value-format="YYYY-MM-DD"
            placeholder="选择一周中的任意一天"
            :first-day-of-week="1"
            clearable
            @clear="onFilterCleared"
            :disabled="charts.loading"
          />
          <el-date-picker
            v-else-if="rangeMode === 'monthly'"
            v-model="datePoint"
            type="month"
            value-format="YYYY-MM"
            placeholder="选择月份"
            clearable
            @clear="onFilterCleared"
            :disabled="charts.loading"
          />
          <el-date-picker
            v-else-if="rangeMode === 'custom'"
            v-model="customRange"
            type="daterange"
            value-format="YYYY-MM-DD"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            unlink-panels
            clearable
            @clear="onFilterCleared"
            :disabled="charts.loading"
          />
        </div>
      </div>
    </div>
    <div class="tab-panels">
      <div v-show="charts.activeTab === 'trends'" class="panel">
        <!-- KPI 仅在趋势分析面板内部显示，符合旧项目布局 -->
        <div class="kpi-grid" v-loading="charts.loading">
          <KpiCard
            label="平均每日时长"
            :value="charts.kpis.avg_daily_formatted || '--'"
            color="primary"
          >
            <template #icon>⏱️</template>
          </KpiCard>
          <KpiCard
            label="效率之星"
            :value="charts.kpis.efficiency_star || '--'"
            color="amber"
          >
            <template #icon>⭐</template>
          </KpiCard>
          <KpiCard
            label="本周趋势 (vs 上周)"
            :value="charts.kpis.weekly_trend || '--'"
            color="green"
          >
            <template #icon>📊</template>
          </KpiCard>
        </div>
        <!-- 无数据/初始化提示 -->
        <div v-if="!charts.loading && !charts.hasTrendsData" class="alert-box">
          <div v-if="rawChartData?.setup_needed" class="alert alert-info">
            尚未创建阶段或学习记录，暂时无法生成趋势图表。请先添加学习日志。
          </div>
          <div v-else class="alert alert-info">
            暂无学习数据，无法生成趋势图表。
          </div>
        </div>
        <TrendsChart
          :weekly-duration-data="charts.trends.weekly_duration_data"
          :weekly-efficiency-data="charts.trends.weekly_efficiency_data"
          :daily-duration-data="charts.trends.daily_duration_data"
          :daily-efficiency-data="charts.trends.daily_efficiency_data"
          :stage-annotations="charts.stageAnnotations"
          :has-data="charts.hasTrendsData"
          :loading="charts.loading"
          :initial-view="charts.viewType"
        />
      </div>
      <div v-show="charts.activeTab === 'categories'" class="panel">
        <div
          v-if="!charts.loading && !charts.hasCategoryData"
          class="category-empty-alert alert alert-info text-center"
        >
          当前筛选范围内没有找到任何带分类的学习记录。
        </div>
        <div
          class="category-header"
          :class="{ 'is-inactive': !isDrilldown }"
        >
          <el-button
            class="category-back"
            size="small"
            type="primary"
            plain
            :icon="ArrowLeft"
            :disabled="!isDrilldown"
            @click="handleBackClick"
          >
            返回分类
          </el-button>
          <span class="path" v-if="isDrilldown">
            <span class="path-label">当前层级：</span>
            <span class="breadcrumbs">
              <span class="crumb">{{ currentCategoryName }}</span>
            </span>
          </span>
          <span class="path placeholder" v-else>
            点击图表中的分类可查看子分类占比
          </span>
        </div>
        <CategoryComposite
          ref="categoryCompositeRef"
          :main="charts.categoryData.main"
          :drilldown="charts.categoryData.drilldown"
          :loading="charts.loading"
          :show-panel-header="false"
          @sliceClick="onCategorySlice"
          @back="handleCategoryBack"
        />
      </div>
      <div v-if="charts.activeTab === 'cattrend'" class="panel">
        <CategoryTrend />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, computed, watch } from "vue";
import dayjs from "dayjs";
import { ArrowLeft } from "@element-plus/icons-vue";
import { useChartsStore } from "@/stores/modules/charts";
import { useStageStore } from "@/stores/modules/stage";
import TrendsChart from "@/components/business/charts/TrendsChart.vue";
import CategoryComposite from "@/components/business/charts/CategoryComposite.vue";
import CategoryTrend from "@/components/business/charts/CategoryTrend.vue";
import KpiCard from "@/components/business/charts/KpiCard.vue";

const charts = useChartsStore();
const stageStore = useStageStore();
const stageSelected = ref<string | number>("all");
const categoryModes = [
  { value: "all", label: "全部历史" },
  { value: "stage", label: "按阶段" },
  { value: "weekly", label: "按周" },
  { value: "daily", label: "按日" },
  { value: "monthly", label: "按月" },
  { value: "custom", label: "自定义" },
] as const;

type CategoryRangeMode = (typeof categoryModes)[number]["value"];

const rangeMode = computed<CategoryRangeMode>({
  get: () => charts.categoryRangeMode as CategoryRangeMode,
  set: (value) => charts.setCategoryRangeMode(value),
});

const rawChartData = computed<Record<string, any>>(
  () => charts.rawChartData as Record<string, any>
);

const datePoint = computed({
  get: () => charts.categoryDatePoint,
  set: (value) => charts.setCategoryDatePoint(value),
});

const customRange = computed({
  get: () => charts.categoryCustomRange,
  set: (value) => charts.setCategoryCustomRange(value),
});

const isDrilldown = computed(() => charts.currentCategoryView === "drilldown");

const compositeDrilldown = ref(false);

const currentCategoryName = computed(() => {
  if (!isDrilldown.value) {
    return "";
  }
  const name = charts.currentCategory;
  if (!name) return "";
  return String(name);
});

function onCategorySlice(cat) {
  if (!cat) return;
  compositeDrilldown.value = true;
  charts.drillCategory(cat);
}

function handleCategoryBack() {
  compositeDrilldown.value = false;
  charts.backCategory();
}

const categoryCompositeRef = ref<{ goBack?: () => void } | null>(null);

function handleBackClick() {
  if (!isDrilldown.value) {
    return;
  }
  charts.backCategory();
}

function onRangeModeChange(mode: CategoryRangeMode) {
  if (rangeMode.value !== mode) {
    rangeMode.value = mode;
  }
}

function onStageChange() {
  charts.setStage(stageSelected.value);
}

function onFilterCleared() {
  if (rangeMode.value !== "all") {
    rangeMode.value = "all";
  }
}

watch(
  () => charts.stageId,
  (value) => {
    if (rangeMode.value === "stage") {
      stageSelected.value = value as string | number;
    }
  }
);

watch(
  () => rangeMode.value,
  (mode, previous) => {
    if (previous === mode) return;

    if (previous === "stage" && mode !== "stage") {
      if (stageSelected.value !== "all") {
        stageSelected.value = "all";
      }
      if (charts.stageId !== "all") {
        charts.setStage("all");
      }
    }

    if (mode === "stage") {
      const activeId =
        stageStore.activeStage?.id ??
        (charts.stages.length ? charts.stages[0].id : "all");
      stageSelected.value = activeId as string | number;
      if (charts.stageId !== activeId) {
        charts.setStage(activeId);
      } else {
        charts.fetchCategories();
      }
      return;
    }

    const today = dayjs();

    if (mode === "daily") {
      const date = today.format("YYYY-MM-DD");
      if (datePoint.value !== date) {
        datePoint.value = date;
      } else {
        charts.fetchCategories();
      }
      return;
    }

    if (mode === "weekly") {
      const date = today.format("YYYY-MM-DD");
      if (datePoint.value !== date) {
        datePoint.value = date;
      } else {
        charts.fetchCategories();
      }
      return;
    }

    if (mode === "monthly") {
      const month = today.format("YYYY-MM");
      if (datePoint.value !== month) {
        datePoint.value = month;
      } else {
        charts.fetchCategories();
      }
      return;
    }

    if (mode === "custom") {
      const range: [string, string] = [
        today.startOf("month").format("YYYY-MM-DD"),
        today.format("YYYY-MM-DD"),
      ];
      if (
        !customRange.value ||
        customRange.value[0] !== range[0] ||
        customRange.value[1] !== range[1]
      ) {
        customRange.value = range;
      } else {
        charts.fetchCategories();
      }
      return;
    }

    charts.fetchCategories();
  }
);

watch(
  () => stageStore.activeStage?.id,
  (activeId) => {
    if (!activeId || rangeMode.value !== "stage") return;
    if (stageSelected.value !== activeId) {
      stageSelected.value = activeId;
    }
    if (charts.stageId !== activeId) {
      charts.setStage(activeId);
    }
  }
);

watch(
  () => charts.currentCategoryView,
  (view) => {
    if (view === "drilldown" || !compositeDrilldown.value) return;
    const target = categoryCompositeRef.value;
    if (target && typeof target.goBack === "function") {
      target.goBack();
      compositeDrilldown.value = false;
    }
  }
);

onMounted(async () => {
  await Promise.all([stageStore.ensureStages(), charts.initStages()]);
  if (rangeMode.value === "stage") {
    const activeId =
      stageStore.activeStage?.id ??
      (charts.stages.length ? charts.stages[0].id : "all");
    stageSelected.value = activeId as string | number;
    if (charts.stageId !== activeId) {
      charts.setStage(activeId);
    }
  }
  await charts.refreshAll();
});

onActivated(async () => {
  await charts.refreshAll();
});

</script>

<style scoped lang="scss">
@import "@/styles/views/charts/charts-view";
</style>
