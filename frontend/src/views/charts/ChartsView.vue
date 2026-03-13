<template>
  <div class="charts-view">
    <PageContainer
      :title="{ icon: 'lucide:chart-column-big', text: '统计分析' }"
      subtitle="通过数据洞察学习模式，掌握成长轨迹"
      max-width="full"
    >
      <div class="charts-layout">
        <aside class="charts-sidebar">
          <div class="filter-list">
            <button
              v-for="tab in tabItems"
              :key="tab.value"
              type="button"
              class="filter-item"
              :class="{ active: charts.activeTab === tab.value }"
              @click="charts.setActiveTab(tab.value)"
            >
              <span class="filter-item__icon">
                <Icon :icon="tab.icon" />
              </span>
              <span class="filter-item__body">
                <strong>{{ tab.label }}</strong>
                <small>{{ tab.brief }}</small>
              </span>
            </button>
          </div>
        </aside>
        <div class="charts-main">
          <div class="charts-main-surface">
            <section class="charts-panel-head">
              <div class="charts-panel-head__copy">
                <span class="panel-kicker">{{ activeTabMeta.panelKicker }}</span>
                <h2>{{ activeTabMeta.panelTitle }}</h2>
                <p>{{ activeTabMeta.panelDescription }}</p>
              </div>
              <div class="charts-panel-head__tags">
                <button
                  v-if="charts.activeTab === 'categories' && isDrilldown"
                  type="button"
                  class="panel-tag panel-tag--button"
                  aria-label="返回上一级分类"
                  @click="handleBackClick"
                >
                  <Icon icon="lucide:arrow-left" />
                  <span>返回上一级</span>
                </button>
                <span class="panel-tag">{{ activeStageName }}</span>
                <span class="panel-tag">{{ analysisWindowLabel }}</span>
                <span
                  v-if="['categories', 'cattrend'].includes(charts.activeTab)"
                  class="panel-tag accent"
                >
                  {{ metricMode === "duration" ? "时长口径" : "效率口径" }}
                </span>
                <span
                  v-if="charts.activeTab === 'categories' && isDrilldown"
                  class="panel-tag accent"
                >
                  {{ currentCategoryName }}
                </span>
              </div>
            </section>

            <div
              v-if="['categories', 'cattrend'].includes(charts.activeTab)"
              class="toolbar-container"
            >
              <div class="toolbar-left">
                <div class="segmented metric-switch">
                  <button
                    :class="['seg-btn', metricMode === 'duration' && 'active']"
                    @click="onMetricModeChange('duration')"
                  >
                    时长
                  </button>
                  <button
                    :class="['seg-btn', metricMode === 'efficiency' && 'active']"
                    @click="onMetricModeChange('efficiency')"
                  >
                    效率
                  </button>
                </div>
              </div>
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
                    v-model="stageSelected"
                    class="stage-select minimal-select"
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
                    :disabled="charts.loading"
                    @clear="onFilterCleared"
                  />
                  <el-date-picker
                    v-else-if="rangeMode === 'weekly'"
                    v-model="datePoint"
                    type="date"
                    value-format="YYYY-MM-DD"
                    placeholder="选择一周中的任意一天"
                    :first-day-of-week="1"
                    clearable
                    :disabled="charts.loading"
                    @clear="onFilterCleared"
                  />
                  <el-date-picker
                    v-else-if="rangeMode === 'monthly'"
                    v-model="datePoint"
                    type="month"
                    value-format="YYYY-MM"
                    placeholder="选择月份"
                    clearable
                    :disabled="charts.loading"
                    @clear="onFilterCleared"
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
                    :disabled="charts.loading"
                    @clear="onFilterCleared"
                  />
                </div>
              </div>
            </div>
            <div class="tab-panels">
              <div v-show="charts.activeTab === 'overview'" class="panel">
                <div v-loading="charts.trendsLoading" class="kpi-grid">
                  <KpiCard label="今天时长" color="amber">
                    <template #icon>
                      <span class="emoji-icon" aria-hidden="true">⏳</span>
                    </template>
                    <template #value>
                      <div class="split-kpi">
                        <div class="split-col today">
                          <div class="split-title today-title">今天</div>
                          <div class="split-value large">
                            {{ todayHoursOnly }}
                          </div>
                          <div class="split-meta">
                            <span class="meta-text">{{
                              todayHoursRankText
                            }}</span>
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
                            <span class="meta-text">{{
                              yesterdayHoursRankText
                            }}</span>
                            <span class="pill accent">{{
                              yesterdayExceedText
                            }}</span>
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
                          <div class="split-value large">
                            {{ todayEfficiencyOnly }}
                          </div>
                          <div class="split-meta">
                            <span class="meta-text">{{
                              todayEfficiencyRankText
                            }}</span>
                            <span class="pill muted">{{
                              todayEfficiencyExceedText
                            }}</span>
                          </div>
                        </div>
                        <div class="divider"></div>
                        <div class="split-col yesterday">
                          <div class="split-title">昨日</div>
                          <div class="split-value medium">
                            {{ yesterdayEfficiencyOnly }}
                            <span class="trend">{{
                              yesterdayEfficiencyTrend
                            }}</span>
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
                        <div class="vol-grid">
                          <div class="vol-cell">
                            <span class="vol-label">Avg</span>
                            <span class="vol-value">{{
                              stabilityAverageText
                            }}</span>
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
                  v-loading="charts.topSummaryLoading"
                  class="kpi-grid top-summary-grid"
                >
                  <KpiCard label="时长 TOP3（近30天）" color="indigo">
                    <template #value>
                      <div
                        class="rank-stack"
                        :class="{ 'rank-stack--loading': showTopSummaryDurationPlaceholder }"
                      >
                        <div
                          v-for="card in topSubCards"
                          :key="card.key"
                          class="rank-stack__item"
                        >
                          <div class="rank-stack__name">{{ card.name }}</div>
                          <div class="rank-stack__value">{{ card.percentText }}</div>
                          <div class="rank-bar">
                            <span
                              :style="{
                                width: card.barWidth,
                                opacity: card.opacity,
                              }"
                            />
                          </div>
                        </div>
                      </div>
                    </template>
                  </KpiCard>
                  <KpiCard label="效率 TOP3（近30天）" color="green">
                    <template #value>
                      <div
                        class="rank-stack"
                        :class="{ 'rank-stack--loading': showTopSummaryEfficiencyPlaceholder }"
                      >
                        <div
                          v-for="card in topSubEfficiencyCards"
                          :key="card.key"
                          class="rank-stack__item"
                        >
                          <div class="rank-stack__name">{{ card.name }}</div>
                          <div class="rank-stack__value">{{ card.valueText }}</div>
                          <div class="rank-bar">
                            <span
                              :style="{
                                width: card.barWidth,
                                opacity: card.opacity,
                              }"
                            />
                          </div>
                        </div>
                      </div>
                    </template>
                  </KpiCard>
                </div>
                <div
                  v-if="!charts.trendsLoading && !charts.hasTrendsData"
                  class="alert-box"
                >
                  <div
                    v-if="charts.trendsError"
                    class="alert alert-info"
                  >
                    趋势图表加载失败：{{ charts.trendsError }}
                  </div>
                  <div
                    v-else-if="rawChartData?.setup_needed"
                    class="alert alert-info"
                  >
                    尚未创建阶段或学习记录，暂时无法生成总体概览。请先添加学习日志。
                  </div>
                  <div v-else class="alert alert-info">
                    暂无学习数据，无法生成总体概览。
                  </div>
                </div>
              </div>
              <div v-show="charts.activeTab === 'trends'" class="panel">
                <div
                  v-if="!charts.trendsLoading && !charts.hasTrendsData"
                  class="alert-box"
                >
                  <div
                    v-if="charts.trendsError"
                    class="alert alert-info"
                  >
                    趋势图表加载失败：{{ charts.trendsError }}
                  </div>
                  <div
                    v-else-if="rawChartData?.setup_needed"
                    class="alert alert-info"
                  >
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
                  :forecast-status="charts.forecastStatus"
                  :forecast-retraining="charts.forecastRetraining"
                  :stage-annotations="charts.stageAnnotations"
                  :has-data="charts.hasTrendsData"
                  :loading="charts.trendsLoading"
                  :initial-view="charts.viewType"
                  @view-change="charts.setViewType"
                  @retrain-forecast="charts.retrainForecasts"
                />
              </div>
            <div
              v-show="charts.activeTab === 'categories'"
              class="panel categories-panel"
            >
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
                :metric-mode="metricMode"
                @slice-click="onCategorySlice"
                @back="handleCategoryBack"
              />
            </div>
            <div v-if="charts.activeTab === 'cattrend'" class="panel">
              <CategoryTrend />
            </div>
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
const hasChartsInitialized = ref(false);
const skipNextActivationRefresh = ref(true);

const tabItems = [
  {
    value: "overview",
    label: "总体概览",
    brief: "先看今天表现和近30天关键指标",
    icon: "lucide:layout-dashboard",
    kicker: "Overview Snapshot",
    title: "把今天、昨天和近30天的核心状态先看明白",
    description: "适合快速扫一眼当前节奏、波动水平，以及最近最占时间和最高效率的方向。",
    panelKicker: "总体概览",
    panelTitle: "关键指标与近期表现",
    panelDescription: "把原先趋势分析顶部的信息单独收拢成一个概览面板，先看结论，再决定往下钻。",
  },
  {
    value: "trends",
    label: "趋势分析",
    brief: "专注看时长和效率的连续走势",
    icon: "lucide:chart-no-axes-combined",
    kicker: "Trend Focus",
    title: "把学习节奏和效率变化放到同一张图里看",
    description: "适合观察阶段切换、临近考试和休息周期对学习投入的影响。",
    panelKicker: "趋势分析",
    panelTitle: "时长与效率的双轴变化",
    panelDescription: "现在这里只保留趋势图本身，用周视图和日视图切换整体走势，阅读会更轻一些。",
  },
  {
    value: "categories",
    label: "分类占比",
    brief: "看时间分布集中在哪些方向",
    icon: "lucide:pie-chart",
    kicker: "Category Mix",
    title: "快速看清时间被哪些分类真正占据",
    description: "适合判断投入是否过于集中，或者某个重点方向是否已经形成稳定占比。",
    panelKicker: "分类结构",
    panelTitle: "按分类拆开你的学习投入",
    panelDescription: "支持下钻到子分类，观察不同主题在当前筛选范围内的真实分布。",
  },
  {
    value: "cattrend",
    label: "分类趋势",
    brief: "看单一分类在不同时间点的强弱",
    icon: "lucide:route",
    kicker: "Category Trend",
    title: "把某一类学习内容单独拉出来看变化",
    description: "适合追踪刷题、课程、复盘等单个方向是否持续推进，是否出现断档。",
    panelKicker: "分类趋势",
    panelTitle: "跟踪单个分类的连续变化",
    panelDescription: "切换不同分类和子分类，查看它们在一段时间内的投入与效率表现。",
  },
] as const;

const activeTabMeta = computed(
  () => tabItems.find((item) => item.value === charts.activeTab) || tabItems[0],
);

// 指标模式：时长/效率
const metricMode = computed({
  get: () => charts.metricMode,
  set: (value: "duration" | "efficiency") => charts.setMetricMode(value),
});

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
  () => charts.rawChartData as Record<string, any>,
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

const activeStageName = computed(() => {
  if (rangeMode.value === "stage") {
    if (`${stageSelected.value}` === "all") return "全部历史";
    const matchedStage = (charts.stages as any[]).find(
      (item) => `${item.id}` === `${stageSelected.value}`,
    );
    return matchedStage?.name || "当前阶段";
  }
  return stageStore.activeStage?.name || "全部阶段";
});

const analysisFocusLabel = computed(() => {
  if (charts.activeTab === "categories" && isDrilldown.value) {
    return `分类下钻 · ${currentCategoryName.value}`;
  }
  if (charts.activeTab === "cattrend") {
    return "分类连续变化";
  }
  return activeTabMeta.value.label;
});

const analysisWindowLabel = computed(() => {
  if (charts.activeTab === "overview") {
    return "关键指标";
  }

  if (charts.activeTab === "trends") {
    return charts.viewType === "daily" ? "按日走势" : "按周走势";
  }

  if (rangeMode.value === "all") return "全部历史";
  if (rangeMode.value === "stage") return "按阶段";

  if (rangeMode.value === "custom" && customRange.value) {
    return `${customRange.value[0]} 至 ${customRange.value[1]}`;
  }

  if (datePoint.value) {
    return `${datePoint.value}`;
  }

  return "当前筛选范围";
});

const currentCategoryName = computed(() => {
  if (!isDrilldown.value) {
    return "";
  }
  const name = charts.currentCategory;
  if (!name) return "";
  return String(name);
});

const showTopSummaryDurationPlaceholder = computed(
  () => charts.topSummaryLoading && (charts.kpiTopSubs30d || []).length === 0,
);

const showTopSummaryEfficiencyPlaceholder = computed(
  () =>
    charts.topSummaryLoading &&
    (charts.kpiTopSubsEfficiency30d || []).length === 0,
);

const topSubCards = computed(() => {
  if (showTopSummaryDurationPlaceholder.value) {
    return Array.from({ length: 3 }, (_, idx) => ({
      key: `duration-loading-${idx}`,
      label: `时长 TOP${idx + 1}（近30天）`,
      name: "加载中",
      percentText: "请稍候",
      medal: "",
      barWidth: `${72 - idx * 14}%`,
      opacity: 0.45,
    }));
  }
  const items = charts.kpiTopSubs30d || [];
  const normalized = [...items];
  while (normalized.length < 3) {
    normalized.push({ label: "--", parent: "", percent: 0, hours: 0 });
  }
  const medals = ["🥇", "🥈", "🥉"];
  return normalized.slice(0, 3).map((item, idx) => {
    const hasParent = !!item.parent;
    const name =
      item.label === "--"
        ? "暂无数据"
        : hasParent
          ? `${item.parent}：${item.label}`
          : item.label;
    const pctNum = Number(item.percent || 0);
    return {
      key: `duration-${item.parent || "legacy"}-${item.label}-${idx}`,
      label: `时长 TOP${idx + 1}（近30天）`,
      name,
      percentText: item.label === "--" ? "--" : `${pctNum}%`,
      medal: medals[idx] || "🏅",
      barWidth: `${Math.max(10, Math.min(100, pctNum || 0))}%`,
      opacity: idx === 0 ? 1 : idx === 1 ? 0.75 : 0.6,
    };
  });
});

const topSubEfficiencyCards = computed(() => {
  if (showTopSummaryEfficiencyPlaceholder.value) {
    return Array.from({ length: 3 }, (_, idx) => ({
      key: `efficiency-loading-${idx}`,
      label: `效率 TOP${idx + 1}（近30天）`,
      name: "加载中",
      valueText: "请稍候",
      medal: "",
      barWidth: `${72 - idx * 14}%`,
      opacity: 0.45,
    }));
  }
  const items = charts.kpiTopSubsEfficiency30d || [];
  const normalized = [...items];
  while (normalized.length < 3) {
    normalized.push({ label: "--", parent: "", percent: 0, hours: 0 });
  }
  const medals = ["🥇", "🥈", "🥉"];
  // 找到最大效率值用于归一化进度条
  const maxEfficiency = Math.max(
    ...normalized.map((x) => Number(x.hours || 0)),
    1,
  );
  return normalized.slice(0, 3).map((item, idx) => {
    const hasParent = !!item.parent;
    const name =
      item.label === "--"
        ? "暂无数据"
        : hasParent
          ? `${item.parent}：${item.label}`
          : item.label;
    const efficiencyValue = Number(item.hours || 0);
    const barPercent = (efficiencyValue / maxEfficiency) * 100;
    return {
      key: `efficiency-${item.parent || "legacy"}-${item.label}-${idx}`,
      label: `效率 TOP${idx + 1}（近30天）`,
      name,
      valueText: item.label === "--" ? "--" : efficiencyValue.toFixed(1),
      medal: medals[idx] || "🏅",
      barWidth: `${Math.max(10, Math.min(100, barPercent || 0))}%`,
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
  todayHoursText.value.replace("今日 ", ""),
);
const yesterdayHoursOnly = computed(() =>
  yesterdayHoursText.value.replace("昨日 ", ""),
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
  () => (charts.trends.daily_efficiency_data?.labels as string[]) || [],
);
const dailyEfficiencyValues = computed(
  () => (charts.trends.daily_efficiency_data?.actuals as number[]) || [],
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
  const rankStr =
    rank >= 0 ? `${rank + 1}/${sorted.length}` : `--/${sorted.length}`;
  const valueWithRank = `${val.toFixed(2)}（${rankStr}）`;
  const less = data.filter((v) => v < val).length;
  const exceed = total ? Math.round((less * 100) / total) : 0;
  const exceedText = `超过 ${exceed}%`;
  return { valueWithRank, exceedText };
}

const todayEfficiencyStat = computed(() =>
  buildEfficiencyStat(dayjs().format("YYYY-MM-DD")),
);
const yesterdayEfficiencyStat = computed(() =>
  buildEfficiencyStat(dayjs().subtract(1, "day").format("YYYY-MM-DD")),
);

const todayEfficiencyWithRank = computed(
  () => todayEfficiencyStat.value.valueWithRank,
);
const yesterdayEfficiencyWithRank = computed(
  () => yesterdayEfficiencyStat.value.valueWithRank,
);
const todayEfficiencyExceedText = computed(
  () => todayEfficiencyStat.value.exceedText,
);
const yesterdayEfficiencyExceedText = computed(
  () => yesterdayEfficiencyStat.value.exceedText,
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
    chooseMaxEfficiency: boolean,
  ) => {
    const candidates = series.filter((item) => item.hours === target);
    if (!candidates.length) return null;
    const best = candidates.reduce(
      (acc, cur) => {
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
      },
      null as (typeof series)[number] | null,
    );
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
    Math.max(sorted.length - 3, 0),
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
    const dateText = target.value > 0 && target.date ? target.date : "";
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

function onMetricModeChange(mode: "duration" | "efficiency") {
  if (metricMode.value !== mode) {
    metricMode.value = mode;
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
  },
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
  },
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
  },
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
  },
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
  hasChartsInitialized.value = true;
});

onActivated(async () => {
  if (!hasChartsInitialized.value) {
    return;
  }
  if (skipNextActivationRefresh.value) {
    skipNextActivationRefresh.value = false;
    return;
  }
  await charts.refreshAll();
});
</script>

<style scoped lang="scss">
@import "@/styles/views/charts/charts-view";

.charts-layout {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: stretch;
}

.charts-sidebar {
  position: static;
  margin-left: 0;
  padding: 0;
  width: 100%;
  border: none;
  background: transparent;
  box-shadow: none;

  .filter-list {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
  }

  .filter-item {
    width: auto;
    min-height: 72px;
    padding: 14px 16px;
    border-radius: 18px;
    display: grid;
    grid-template-columns: 40px minmax(0, 1fr);
    align-items: center;
    justify-content: stretch;
    gap: 12px;
    background: color-mix(in srgb, var(--surface-card) 78%, rgba(255, 255, 255, 0.02));
    border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
    text-align: left;
    box-shadow:
      0 12px 28px -24px rgba(15, 23, 42, 0.45),
      inset 0 1px 0 rgba(255, 255, 255, 0.04);

    &:hover {
      transform: translateY(-1px);
      background: color-mix(in srgb, var(--surface-card) 88%, rgba(255, 255, 255, 0.03));
      border-color: color-mix(in srgb, var(--color-primary) 16%, transparent);
    }

    &.active {
      background: linear-gradient(
        135deg,
        color-mix(in srgb, var(--color-primary) 16%, rgba(255, 255, 255, 0.03)) 0%,
        color-mix(in srgb, var(--surface-card) 92%, rgba(255, 255, 255, 0.02)) 100%
      );
      border-color: color-mix(in srgb, var(--color-primary) 22%, transparent);
      color: var(--color-text-heading);
    }
  }
}

.filter-item__icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: color-mix(in srgb, var(--color-primary) 12%, rgba(255, 255, 255, 0.02));
  color: var(--color-primary);

  :deep(svg) {
    width: 20px;
    height: 20px;
  }
}

.filter-item__body {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
  min-width: 0;

  strong {
    color: var(--color-text-heading);
    font-size: 16px;
    font-weight: 700;
  }

  small {
    color: var(--color-text-secondary);
    font-size: 13px;
    line-height: 1.35;
  }
}

.charts-main {
  width: 100%;
}

.charts-main-surface {
  position: relative;
  width: 100%;
  padding: 22px;
  border-radius: 30px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 8%, transparent) 0%, transparent 28%),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--surface-card) 90%, rgba(255, 255, 255, 0.02)) 0%,
      color-mix(in srgb, var(--surface-card-strong) 97%, rgba(15, 23, 42, 0.1)) 100%
    );
  box-shadow:
    0 24px 44px -34px rgba(15, 23, 42, 0.54),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

.charts-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  align-items: flex-start;
  margin-bottom: 18px;
}

.charts-panel-head__copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;

  h2 {
    margin: 0;
    font-size: clamp(1.4rem, 2.2vw, 1.8rem);
    line-height: 1.12;
    letter-spacing: -0.04em;
    color: var(--color-text-heading);
  }

  p {
    margin: 0;
    max-width: 42rem;
    color: var(--color-text-secondary);
    line-height: 1.65;
  }
}

.panel-kicker {
  color: var(--color-primary);
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.charts-panel-head__tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.panel-tag {
  display: inline-flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-card-strong) 88%, rgba(255, 255, 255, 0.02));
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: 600;

  &.accent {
    background: color-mix(in srgb, var(--color-primary) 14%, rgba(255, 255, 255, 0.03));
    color: var(--color-text-heading);
  }
}

.toolbar-container {
  padding: 16px;
  margin-bottom: 18px;
  border-radius: 22px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
  background: color-mix(in srgb, var(--surface-card-strong) 86%, rgba(255, 255, 255, 0.02));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
}

.tab-panels {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel {
  min-height: 0;
}

.kpi-grid {
  gap: 12px;
  margin-bottom: 14px;
}

.top-summary-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 14px;

  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
}

.panel-tag--button {
  gap: 6px;
  cursor: pointer;
  color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 12%, rgba(255, 255, 255, 0.03));
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;

  &:hover {
    transform: translateY(-1px);
    border-color: color-mix(in srgb, var(--color-primary) 24%, var(--stroke-soft));
    background: color-mix(in srgb, var(--color-primary) 18%, rgba(255, 255, 255, 0.04));
  }

  :deep(svg) {
    width: 14px;
    height: 14px;
  }
}

.split-kpi {
  gap: 14px;
}

.volatility-card {
  gap: 12px;
}

.rank-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.rank-stack {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rank-stack--loading {
  .rank-stack__name,
  .rank-stack__value,
  .rank-bar span {
    position: relative;
    overflow: hidden;
  }

  .rank-stack__name,
  .rank-stack__value {
    color: color-mix(in srgb, var(--color-text-secondary) 72%, transparent);
  }

  .rank-stack__name::after,
  .rank-stack__value::after,
  .rank-bar span::after {
    content: "";
    position: absolute;
    inset: 0;
    transform: translateX(-100%);
    background: linear-gradient(
      90deg,
      transparent 0%,
      rgba(255, 255, 255, 0.14) 50%,
      transparent 100%
    );
    animation: rank-loading-sheen 1.4s ease-in-out infinite;
  }
}

.rank-stack__item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-bottom: 14px;
  border-bottom: 1px solid
    color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));

  &:last-child {
    padding-bottom: 0;
    border-bottom: none;
  }
}

.rank-stack__name {
  color: var(--color-text-heading);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
}

.rank-stack__value {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
}

.rank-title {
  color: var(--color-text-heading);
  font-size: 15px;
  font-weight: 700;
  line-height: 1.45;
}

.rank-percent {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: 600;
}

.rank-bar {
  width: 100%;
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--surface-card-strong) 84%, rgba(255, 255, 255, 0.02));
  overflow: hidden;

  span {
    display: block;
    height: 100%;
    border-radius: inherit;
    background: linear-gradient(
      90deg,
      var(--color-primary) 0%,
      color-mix(in srgb, var(--color-primary-dark) 76%, #ffffff) 100%
    );
  }
}

@keyframes rank-loading-sheen {
  to {
    transform: translateX(100%);
  }
}

@media (max-width: 1200px) {
  .charts-sidebar .filter-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .charts-sidebar .filter-list {
    grid-template-columns: 1fr;
  }

  .charts-sidebar .filter-item {
    min-height: 68px;
  }

  .charts-panel-head {
    flex-direction: column;
  }

  .charts-panel-head__tags {
    justify-content: flex-start;
  }

}

@media (max-width: 768px) {
  .charts-main-surface {
    padding: 18px;
    border-radius: 24px;
  }

  .charts-sidebar {
    padding: 14px;
    border-radius: 22px;
  }

  .toolbar-container {
    padding: 14px;
  }
}
</style>
