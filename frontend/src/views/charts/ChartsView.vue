<template>
  <div class="charts-view">
    <PageContainer
      :title="{ icon: '📊', text: '统计分析' }"
      subtitle="通过数据洞察学习模式，掌握成长轨迹"
    >
      <div class="charts-layout">
        <aside class="charts-sidebar">
          <div class="filter-list">
            <button
              type="button"
              class="filter-item"
              :class="{ active: charts.activeTab === 'trends' }"
              @click="charts.setActiveTab('trends')"
            >
              趋势分析
            </button>
            <button
              type="button"
              class="filter-item"
              :class="{ active: charts.activeTab === 'categories' }"
              @click="charts.setActiveTab('categories')"
            >
              分类占比
            </button>
            <button
              type="button"
              class="filter-item"
              :class="{ active: charts.activeTab === 'cattrend' }"
              @click="charts.setActiveTab('cattrend')"
            >
              分类趋势
            </button>
          </div>
        </aside>
        <div class="charts-main">
          <button
            v-if="charts.activeTab === 'categories' && isDrilldown"
            class="floating-back"
            type="button"
            @click="handleBackClick"
            aria-label="返回上一级分类"
          >
            <Icon icon="lucide:arrow-left" />
          </button>
          <div
            class="toolbar-container"
            v-if="['categories', 'cattrend'].includes(charts.activeTab)"
          >
            <div class="toolbar-left"></div>
            <div class="category-filters">
              <div class="segmented filter-switch">
                <button
                  v-for="mode in categoryModes"
                  :key="mode.value"
                  :class="['seg-btn', rangeMode === mode.value && 'active']"
                  @click="onRangeModeChange(mode.value)"
                >
                  {{ mode.label }}
                </button>
              </div>
              <div class="filter-inputs">
                <select
                  v-if="rangeMode === 'stage'"
                  class="stage-select minimal-select"
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
            <template #icon>
              <span class="emoji-icon" aria-hidden="true">⏳</span>
            </template>
            <template #value>
              <div class="split-kpi">
                <div class="split-col today">
                  <div class="split-title today-title">今天</div>
                  <div class="split-value large">{{ todayHoursOnly }}</div>
                  <div class="split-meta">
                    <span class="meta-text">{{ todayHoursRankText }}</span>
                    <span class="pill muted">{{ todayExceedText }}</span>
                  </div>
                </div>
                <div class="divider"></div>
                <div class="split-col yesterday">
                  <div class="split-title">昨日</div>
                  <div class="split-value medium">
                    {{ yesterdayHoursOnly }}
                    <span class="trend">{{ yesterdayHoursTrend }}</span>
                  </div>
                  <div class="split-meta">
                    <span class="meta-text">{{ yesterdayHoursRankText }}</span>
                    <span class="pill accent">{{ yesterdayExceedText }}</span>
                  </div>
                </div>
              </div>
            </template>
          </KpiCard>
          <KpiCard label="今天效率" color="green">
            <template #icon>
              <span class="emoji-icon" aria-hidden="true">⚡️</span>
            </template>
            <template #value>
              <div class="split-kpi">
                <div class="split-col today">
                  <div class="split-title today-title">今天</div>
                  <div class="split-value large">{{ todayEfficiencyOnly }}</div>
                  <div class="split-meta">
                    <span class="meta-text">{{ todayEfficiencyRankText }}</span>
                    <span class="pill muted">{{ todayEfficiencyExceedText }}</span>
                  </div>
                </div>
                <div class="divider"></div>
                <div class="split-col yesterday">
                  <div class="split-title">昨日</div>
                  <div class="split-value medium">
                    {{ yesterdayEfficiencyOnly }}
                    <span class="trend">{{ yesterdayEfficiencyTrend }}</span>
                  </div>
                  <div class="split-meta">
                    <span class="meta-text">
                      {{ yesterdayEfficiencyRankText }}
                    </span>
                    <span class="pill accent">
                      {{ yesterdayEfficiencyExceedText }}
                    </span>
                  </div>
                </div>
              </div>
            </template>
          </KpiCard>
          <KpiCard label="近30天波动" color="purple">
            <template #icon>
              <span class="emoji-icon" aria-hidden="true">🛡️</span>
            </template>
            <template #value>
              <div class="volatility-card">
                <div class="vol-main">
                  <span class="vol-state">{{ stabilityTitle }}</span>
                  <span class="vol-score">{{ stabilityScore }}</span>
                </div>
                <div class="vol-sub">平均时长：{{ stabilityAverageText }}</div>
                <div class="vol-grid">
                  <div class="vol-cell">
                    <span class="vol-label">Avg</span>
                    <span class="vol-value">{{ stabilityAverageText }}</span>
                  </div>
                  <div class="vol-cell">
                    <span class="vol-label">Max</span>
                    <span class="vol-value">
                      {{ durationExtremeDisplay.max.valueText }}
                    </span>
                  </div>
                  <div class="vol-cell">
                    <span class="vol-label">Min</span>
                    <span class="vol-value">
                      {{ durationExtremeDisplay.min.valueText }}
                    </span>
                  </div>
                </div>
              </div>
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
            <template #icon>
              <span class="emoji-icon" aria-hidden="true">{{ card.medal }}</span>
            </template>
            <template #value>
              <div class="rank-card">
                <div class="rank-title">{{ card.name }}</div>
                <div class="rank-percent">{{ card.percentText }}</div>
                <div class="rank-bar">
                  <span :style="{ width: card.barWidth, opacity: card.opacity }" />
                </div>
              </div>
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
          @view-change="charts.setViewType"
        />
      </div>
      <div v-show="charts.activeTab === 'categories'" class="panel categories-panel">
        <div
          v-if="!charts.loading && !charts.hasCategoryData"
          class="category-empty-alert alert alert-info text-center"
        >
          当前筛选范围内没有找到任何带分类的学习记录。
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
      </div>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, computed, watch } from "vue";
import { Icon } from "@iconify/vue";
import dayjs from "dayjs";
import { ArrowLeft } from "@element-plus/icons-vue";
import { useChartsStore } from "@/stores/modules/charts";
import { useStageStore } from "@/stores/modules/stage";
import TrendsChart from "@/components/business/charts/TrendsChart.vue";
import CategoryComposite from "@/components/business/charts/CategoryComposite.vue";
import CategoryTrend from "@/components/business/charts/CategoryTrend.vue";
import KpiCard from "@/components/business/charts/KpiCard.vue";
import PageContainer from "@/components/layout/PageContainer.vue";

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
  const medals = ["🥇", "🥈", "🥉"];
  return normalized.slice(0, 3).map((item, idx) => {
    const hasParent = !!item.parent;
    const name = item.label === "--"
      ? "暂无数据"
      : hasParent
        ? `${item.parent}：${item.label}`
        : item.label;
    const pctNum = Number(item.percent || 0);
    return {
      key: `${item.parent || "legacy"}-${item.label}-${idx}`,
      label: `TOP${idx + 1}（近30天）`,
      name,
      percentText: item.label === "--" ? "--" : `${pctNum}%`,
      medal: medals[idx] || "🏅",
      barWidth: `${Math.max(10, Math.min(100, pctNum || 0))}%`,
      opacity: idx === 0 ? 1 : idx === 1 ? 0.75 : 0.6,
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

const todayHoursOnly = computed(() =>
  todayHoursText.value.replace("今日 ", "")
);
const yesterdayHoursOnly = computed(() =>
  yesterdayHoursText.value.replace("昨日 ", "")
);
const todayHoursRankText = computed(() => {
  const match = todayHoursWithRank.value.match(/（(.+?)）/);
  return match ? match[1] : todayHoursWithRank.value;
});
const yesterdayHoursRankText = computed(() => {
  const match = yesterdayHoursWithRank.value.match(/（(.+?)）/);
  return match ? match[1] : yesterdayHoursWithRank.value;
});
const yesterdayHoursTrend = computed(() => "↑");

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
const todayEfficiencyOnly = computed(() => {
  const match = todayEfficiencyWithRank.value.match(/^(.+?)（/);
  return match ? match[1] : todayEfficiencyWithRank.value;
});
const yesterdayEfficiencyOnly = computed(() => {
  const match = yesterdayEfficiencyWithRank.value.match(/^(.+?)（/);
  return match ? match[1] : yesterdayEfficiencyWithRank.value;
});
const todayEfficiencyRankText = computed(() => {
  const match = todayEfficiencyWithRank.value.match(/（(.+?)）/);
  return match ? match[1] : todayEfficiencyWithRank.value;
});
const yesterdayEfficiencyRankText = computed(() => {
  const match = yesterdayEfficiencyWithRank.value.match(/（(.+?)）/);
  return match ? match[1] : yesterdayEfficiencyWithRank.value;
});
const yesterdayEfficiencyTrend = computed(() => "↑");

// 近30天时长序列（补齐缺失日期，方便统一计算；包含效率用于极值的日期选择）
const last30DurationSeries = computed(() => {
  const daily = charts.trends.daily_duration_data;
  const labels: string[] = (daily?.labels as string[]) || [];
  const values: number[] = (daily?.actuals as number[]) || [];
  const effLabels: string[] =
    (charts.trends.daily_efficiency_data?.labels as string[]) || [];
  const effValues: number[] =
    (charts.trends.daily_efficiency_data?.actuals as number[]) || [];
  if (!labels.length || !values.length) return [];
  const today = dayjs();
  const start = today.subtract(29, "day");
  const series: {
    date: string;
    hours: number;
    hasRecord: boolean;
    efficiency: number | null;
  }[] = [];
  for (let i = 0; i < 30; i++) {
    const d = start.add(i, "day").format("YYYY-MM-DD");
    const idx = labels.indexOf(d);
    const hasRecord = idx >= 0;
    const val = hasRecord ? Number(values[idx] || 0) : 0;
    const effIdx = effLabels.indexOf(d);
    const eff = effIdx >= 0 ? Number(effValues[effIdx] || 0) : null;
    series.push({ date: d, hours: val, hasRecord, efficiency: eff });
  }
  return series;
});

const averageDuration30d = computed(() => {
  const series = last30DurationSeries.value;
  if (!series.length) {
    return { value: 0, text: "--" };
  }
  const total = series.reduce((acc, item) => acc + item.hours, 0);
  const avg = total / series.length;
  return { value: avg, text: `${avg.toFixed(1)}h` };
});

const durationExtremes30d = computed(() => {
  const series = last30DurationSeries.value;
  if (!series.length) {
    return {
      max: null as null | { value: number; date: string | null },
      min: null as null | { value: number; date: string | null },
    };
  }
  const values = series.map((item) => item.hours);
  const maxValue = Math.max(...values);
  const minValue = Math.min(...values);
  const pickDateByEfficiency = (
    target: number,
    chooseMaxEfficiency: boolean
  ) => {
    const candidates = series.filter((item) => item.hours === target);
    if (!candidates.length) return null;
    const best = candidates.reduce((acc, cur) => {
      if (acc === null) return cur;
      const accEff = acc.efficiency;
      const curEff = cur.efficiency;
      // 缺失效率视为最低优先级
      if (curEff === null && accEff !== null) return acc;
      if (curEff !== null && accEff === null) return cur;
      if (curEff === null && accEff === null) return acc;
      if (chooseMaxEfficiency) {
        return (curEff as number) > (accEff as number) ? cur : acc;
      }
      return (curEff as number) < (accEff as number) ? cur : acc;
    }, null as (typeof series)[number] | null);
    return best ? dayjs(best.date).format("MM-DD") : null;
  };
  return {
    max: { value: maxValue, date: pickDateByEfficiency(maxValue, true) },
    min: { value: minValue, date: pickDateByEfficiency(minValue, false) },
  };
});

// 稳定性档位（近30天）- 使用截尾后的变异系数 + 覆盖率惩罚，更平滑
const stabilityStats = computed(() => {
  const series = last30DurationSeries.value;
  if (!series.length) {
    return { grade: "--", score: 0, descriptor: "近30天暂无数据" };
  }
  const recorded = series.filter((item) => item.hasRecord);
  const values = recorded.map((item) => item.hours);
  if (!values.length) {
    return { grade: "--", score: 0, descriptor: "近30天暂无数据" };
  }
  const sorted = [...values].sort((a, b) => a - b);
  const trimCount = Math.min(
    Math.floor(sorted.length * 0.1),
    Math.max(sorted.length - 3, 0)
  );
  const trimmed =
    trimCount > 0 && sorted.length - trimCount * 2 >= 3
      ? sorted.slice(trimCount, sorted.length - trimCount)
      : sorted;

  const mean = trimmed.reduce((acc, v) => acc + v, 0) / trimmed.length;
  if (mean <= 0) {
    return { grade: "--", score: 0, descriptor: "近30天暂无数据" };
  }

  const variance =
    trimmed.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / trimmed.length;
  const std = Math.sqrt(variance);
  const cv = std / mean;

  // 以 cv=0.8 作为极端波动上界，叠加记录覆盖率惩罚（缺失越多分数越低）
  const normalizedCv = Math.min(cv / 0.8, 1);
  const coveragePenalty = 1 - Math.min(recorded.length / series.length, 1);
  const penalty = normalizedCv * 0.7 + coveragePenalty * 0.3;
  const score = Math.round(Math.max(0, 1 - penalty) * 100);

  const grade =
    score >= 80
      ? "很稳定"
      : score >= 60
        ? "较稳定"
        : score >= 40
          ? "波动中等"
          : "波动较大";

  const descriptor =
    grade === "很稳定"
      ? "日时长波动很小"
      : grade === "较稳定"
        ? "日时长波动较小"
        : grade === "波动中等"
          ? "日时长波动中等"
          : "日时长波动较大";

  return { grade, score, descriptor };
});

const stabilityTitleWithScore = computed(() => {
  const { grade, score } = stabilityStats.value;
  if (grade === "--") return "近30天暂无数据";
  return `${grade}（${score}/100）`;
});

const stabilityTitle = computed(() => stabilityStats.value.grade);
const stabilityScore = computed(() => stabilityStats.value.score);

const stabilityAverageText = computed(() => averageDuration30d.value.text);

const durationExtremeDisplay = computed(() => {
  const { max, min } = durationExtremes30d.value;
  const format = (target: { value: number; date: string | null } | null) => {
    if (!target) {
      return { valueText: "--", dateText: "" };
    }
    const valueText = `${target.value.toFixed(1)}h`;
    const dateText =
      target.value > 0 && target.date ? target.date : "";
    return { valueText, dateText };
  };
  return {
    max: format(max),
    min: format(min),
  };
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
