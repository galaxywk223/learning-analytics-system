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
          <KpiCard label="今天时长" color="amber">
            <template #icon>🚀</template>
            <template #value>
              <div class="today-kpi-layout">
                <div class="today-kpi-main">
                  <div class="kpi-value-main">{{ todayHoursWithRank }}</div>
                  <div class="kpi-value-sub">{{ todayExceedText }}</div>
                </div>
                <div class="today-kpi-yesterday">
                  <div class="kpi-value-main">
                    {{ yesterdayHoursWithRank }}
                  </div>
                  <div class="kpi-value-sub">
                    {{ yesterdayExceedText }}
                  </div>
                </div>
              </div>
            </template>
          </KpiCard>
          <KpiCard label="今天效率" color="green">
            <template #icon>⚡</template>
            <template #value>
              <div class="today-kpi-layout">
                <div class="today-kpi-main">
                  <div class="kpi-value-main">
                    {{ todayEfficiencyWithRank }}
                  </div>
                  <div class="kpi-value-sub">
                    {{ todayEfficiencyExceedText }}
                  </div>
                </div>
                <div class="today-kpi-yesterday">
                  <div class="kpi-value-main">
                    {{ yesterdayEfficiencyWithRank }}
                  </div>
                  <div class="kpi-value-sub">
                    {{ yesterdayEfficiencyExceedText }}
                  </div>
                </div>
              </div>
            </template>
          </KpiCard>
          <KpiCard label="近30天波动" color="purple">
            <template #icon>🛡️</template>
            <template #value>
              <div class="kpi-value-main">{{ stabilityTitle }}</div>
              <div class="kpi-value-sub">{{ stabilityDetail }}</div>
            </template>
          </KpiCard>
        </div>
        <div
          class="kpi-grid top-sub-grid"
          v-if="topSubCards.length"
          v-loading="charts.loading"
        >
          <KpiCard
            v-for="card in topSubCards"
            :key="card.key"
            :label="card.label"
            color="indigo"
            dense
          >
            <template #icon>🏷️</template>
            <template #value>
              <div class="kpi-value-main">{{ card.name }}</div>
              <div class="kpi-value-sub">{{ card.percent }}</div>
            </template>
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

const topSubCards = computed(() => {
  const items = charts.kpiTopSubs30d || [];
  const normalized = [...items];
  while (normalized.length < 3) {
    normalized.push({ label: "--", parent: "", percent: 0, hours: 0 });
  }
  return normalized.slice(0, 3).map((item, idx) => {
    const hasParent = !!item.parent;
    const name = item.label === "--"
      ? "暂无数据"
      : hasParent
        ? `${item.parent}：${item.label}`
        : item.label;
    return {
      key: `${item.parent || "legacy"}-${item.label}-${idx}`,
      label: `TOP${idx + 1}（近30天）`,
      name,
      percent: item.label === "--" ? "--" : `${item.percent}%`,
    };
  });
});

// 今日超过历史百分比（全历史）
const todayPercentileValue = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "--";
  const today = dayjs().format("YYYY-MM-DD");
  const idx = labels.indexOf(today);
  if (idx < 0) return "--";
  const todayVal = Number(data[idx] || 0);
  const n = data.length;
  if (!n) return "--";
  const less = data.filter((v) => Number(v || 0) < todayVal).length;
  const pct = Math.round((less * 100) / n);
  return `打败 ${pct}%`;
});

const todayHoursText = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "今日 0h";
  const today = dayjs().format("YYYY-MM-DD");
  const idx = labels.indexOf(today);
  const hours = idx >= 0 ? Number(data[idx] || 0) : 0;
  return `${hours.toFixed(1)}h`;
});

const yesterdayHoursText = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "昨日 0.0h";
  const yesterday = dayjs().subtract(1, "day").format("YYYY-MM-DD");
  const idx = labels.indexOf(yesterday);
  const hours = idx >= 0 ? Number(data[idx] || 0) : 0;
  return `昨日 ${hours.toFixed(1)}h`;
});

const todayHoursWithRank = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return `${todayHoursText.value}`;
  const today = dayjs().format("YYYY-MM-DD");
  const idx = labels.indexOf(today);
  const hoursStr = todayHoursText.value;
  if (idx < 0) return hoursStr;
  const todayVal = Number(data[idx] || 0);
  const sorted = [...data].sort((a, b) => b - a);
  const total = sorted.length;
  let rank = sorted.findIndex((v) => v === todayVal);
  rank = rank >= 0 ? rank + 1 : total; // 1-based
  return `${hoursStr}（${rank}/${total}）`;
});

const yesterdayHoursWithRank = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "昨日 0.0h";
  const yesterday = dayjs().subtract(1, "day").format("YYYY-MM-DD");
  const idx = labels.indexOf(yesterday);
  const hours = idx >= 0 ? Number(data[idx] || 0) : 0;
  const hoursStr = `${hours.toFixed(1)}h`;
  if (idx < 0) return `昨日 ${hoursStr}`;
  const sorted = [...data].sort((a, b) => b - a);
  const total = sorted.length;
  if (!total) return `昨日 ${hoursStr}`;
  let rank = sorted.findIndex((v) => v === hours);
  rank = rank >= 0 ? rank + 1 : total;
  return `昨日 ${hoursStr}（${rank}/${total}）`;
});

// 今日超过历史百分比（友好文案）
const todayExceedText = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "超过 0%";
  const today = dayjs().format("YYYY-MM-DD");
  const idx = labels.indexOf(today);
  if (idx < 0) return "超过 0%";
  const todayVal = Number(data[idx] || 0);
  const n = data.length;
  if (!n) return "超过 0%";
  const less = data.filter((v) => Number(v || 0) < todayVal).length;
  const pct = Math.round((less * 100) / n);
  return `超过 ${pct}%`;
});

const yesterdayExceedText = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "超过 0%";
  const yesterday = dayjs().subtract(1, "day").format("YYYY-MM-DD");
  const idx = labels.indexOf(yesterday);
  if (idx < 0) return "超过 0%";
  const yesterdayVal = Number(data[idx] || 0);
  const n = data.length;
  if (!n) return "超过 0%";
  const less = data.filter((v) => Number(v || 0) < yesterdayVal).length;
  const pct = Math.round((less * 100) / n);
  return `超过 ${pct}%`;
});

const todayRankLabel = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const data: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !data.length) return "无记录";
  const today = dayjs().format("YYYY-MM-DD");
  const idx = labels.indexOf(today);
  if (idx < 0) return "无记录";
  const todayVal = Number(data[idx] || 0);
  const sorted = [...data].sort((a, b) => b - a);
  const rank = sorted.findIndex((v) => v === todayVal);
  return rank >= 0 ? `历史第 ${rank + 1}` : "无记录";
});

// ----- 效率 KPI（今日/昨日，与首卡格式一致） -----
const dailyEfficiencyLabels = computed(
  () => (charts.trends.daily_efficiency_data?.labels as string[]) || []
);
const dailyEfficiencyValues = computed(
  () => (charts.trends.daily_efficiency_data?.actuals as number[]) || []
);

function buildEfficiencyStat(targetDate: string) {
  const labels = dailyEfficiencyLabels.value;
  const data = dailyEfficiencyValues.value.map((v) => Number(v || 0));
  const total = data.length;
  const idx = labels.indexOf(targetDate);
  if (total === 0 || idx < 0) {
    return {
      valueWithRank: "0.00（--/--）",
      exceedText: "超过 0%",
    };
  }
  const val = Number(data[idx] || 0);
  const sorted = [...data].sort((a, b) => b - a);
  const rank = sorted.findIndex((v) => v === val);
  const rankStr = rank >= 0 ? `${rank + 1}/${sorted.length}` : `--/${sorted.length}`;
  const valueWithRank = `${val.toFixed(2)}（${rankStr}）`;
  const less = data.filter((v) => v < val).length;
  const exceed = total ? Math.round((less * 100) / total) : 0;
  const exceedText = `超过 ${exceed}%`;
  return { valueWithRank, exceedText };
}

const todayEfficiencyStat = computed(() =>
  buildEfficiencyStat(dayjs().format("YYYY-MM-DD"))
);
const yesterdayEfficiencyStat = computed(() =>
  buildEfficiencyStat(dayjs().subtract(1, "day").format("YYYY-MM-DD"))
);

const todayEfficiencyWithRank = computed(
  () => todayEfficiencyStat.value.valueWithRank
);
const yesterdayEfficiencyWithRank = computed(
  () => yesterdayEfficiencyStat.value.valueWithRank
);
const todayEfficiencyExceedText = computed(
  () => todayEfficiencyStat.value.exceedText
);
const yesterdayEfficiencyExceedText = computed(
  () => yesterdayEfficiencyStat.value.exceedText
);

// 稳定性档位（近30天）
const stabilityGradeValue = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const values: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !values.length) return "--";
  const today = dayjs();
  const start = today.subtract(29, "day");
  const seq: number[] = [];
  for (let i = 0; i < 30; i++) {
    const d = start.add(i, "day").format("YYYY-MM-DD");
    const idx = labels.indexOf(d);
    seq.push(idx >= 0 ? Number(values[idx] || 0) : 0);
  }
  const mean = seq.reduce((a, b) => a + b, 0) / seq.length;
  if (mean <= 0) return "--";
  const variance = seq.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / seq.length;
  const std = Math.sqrt(variance);
  const cv = std / mean;
  if (cv <= 0.35) return "高";
  if (cv <= 0.65) return "中";
  return "低";
});

const stabilityTitle = computed(() => {
  const grade = stabilityGradeValue.value;
  if (grade === "高") return "很稳定";
  if (grade === "中") return "较稳定";
  if (grade === "低") return "波动较大";
  return "--";
});

const stabilityScore = computed(() => {
  // 依据 CV -> 分数（0-100），低 CV 得高分
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const values: number[] = (daily?.actuals as number[]) || [];
  if (!labels.length || !values.length) return 0;
  const today = dayjs();
  const start = today.subtract(29, "day");
  const seq: number[] = [];
  for (let i = 0; i < 30; i++) {
    const d = start.add(i, "day").format("YYYY-MM-DD");
    const idx = labels.indexOf(d);
    seq.push(idx >= 0 ? Number(values[idx] || 0) : 0);
  }
  const mean = seq.reduce((a, b) => a + b, 0) / seq.length;
  if (mean <= 0) return 0;
  const variance = seq.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / seq.length;
  const std = Math.sqrt(variance);
  const cv = std / mean;
  const score = Math.round(Math.max(0, Math.min(1, 1 - Math.min(cv, 1))) * 100);
  return score;
});

const stabilityDetail = computed(() => {
  const grade = stabilityGradeValue.value;
  const score = stabilityScore.value;
  if (grade === "高") return `日时长波动很小（${score}/100）`;
  if (grade === "中") return `日时长波动中等（${score}/100）`;
  if (grade === "低") return `日时长波动较大（${score}/100）`;
  return "近30天暂无数据";
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
