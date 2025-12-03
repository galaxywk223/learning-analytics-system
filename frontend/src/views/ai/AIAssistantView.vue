<template>
  <div class="ios-view">
    <PageContainer
      :title="{ icon: '🤖', text: '智能规划' }"
      subtitle="按日、周、月或阶段梳理学习数据，生成易读的总结与下一步规划。"
    >
      <div class="ios-content-wrapper">
        <!-- Control Panel -->
        <div class="ios-card control-panel">
          <div class="panel-header">
            <h3 class="panel-title">配置分析范围</h3>
            <div class="current-status">
              <span class="status-badge">{{ scopeLabel }}</span>
              <span class="status-badge secondary" v-if="!isStageScope">{{ currentPeriodLabel }}</span>
              <span class="status-badge secondary" v-else>{{ currentStageLabel }}</span>
            </div>
          </div>
          
          <div class="panel-body">
            <div class="control-group">
              <label class="group-label">时间维度</label>
              <div class="ios-segmented-control">
                <button
                  v-for="item in scopeOptions"
                  :key="item.value"
                  :class="['segment-btn', scopeValue === item.value && 'active']"
                  @click="scopeValue = item.value"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>

            <div class="control-group">
              <label class="group-label">选择范围</label>
              <div class="picker-wrapper">
                <template v-if="!isStageScope">
                  <button class="ios-picker-btn" @click="openDatePicker">
                    <span class="icon">📅</span>
                    <span class="value">{{ dateValue || datePlaceholder }}</span>
                    <el-icon class="arrow"><ArrowRight /></el-icon>
                  </button>
                  <el-date-picker
                    ref="datePicker"
                    v-model="dateValue"
                    :type="datePickerType"
                    value-format="YYYY-MM-DD"
                    :placeholder="datePlaceholder"
                    :clearable="false"
                    class="hidden-date-input"
                  />
                </template>
                <template v-else>
                  <el-select
                    v-model="stageValue"
                    placeholder="请选择阶段"
                    filterable
                    class="ios-select"
                    :teleported="false"
                  >
                    <el-option
                      v-for="stage in stageOptions"
                      :key="stage.value"
                      :label="stage.label"
                      :value="stage.value"
                    />
                  </el-select>
                </template>
              </div>
            </div>

            <div class="action-group">
              <button
                class="ios-btn primary"
                :disabled="analysisLoading || planLoading"
                @click="handleGenerateAnalysis"
              >
                <span class="icon">✨</span> 生成分析
              </button>
              <button
                class="ios-btn primary-alt"
                :disabled="analysisLoading || planLoading"
                @click="handleGeneratePlan"
              >
                <span class="icon">🎯</span> 生成规划
              </button>
              <button class="ios-btn ghost" :disabled="!hasResult" @click="handleClear">
                <span class="icon">🗑️</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Results Grid -->
        <div class="results-grid">
          <!-- Analysis Card -->
          <section class="ios-card result-card" :class="{ 'is-loading': analysisLoading }">
            <div class="card-header">
              <div class="header-left">
                <div class="icon-box analysis-icon">📊</div>
                <div class="header-text">
                  <h3 class="title">分析总结</h3>
                  <span class="subtitle" v-if="analysisMeta.period">{{ analysisMeta.period }}</span>
                </div>
              </div>
              <span class="ios-tag latest">最新</span>
            </div>
            <div class="card-body" v-loading="analysisLoading">
              <div v-if="analysisHtml" class="markdown-content">
                <div class="markdown-body" v-html="analysisHtml"></div>
                <div v-if="analysisMeta.generatedAt" class="timestamp">
                  生成于 {{ formatDateTime(analysisMeta.generatedAt) }}
                </div>
              </div>
              <div v-else class="empty-state">
                <span class="emoji">🤔</span>
                <p>暂无分析数据</p>
              </div>
            </div>
          </section>

          <!-- Plan Card -->
          <section class="ios-card result-card" :class="{ 'is-loading': planLoading }">
            <div class="card-header">
              <div class="header-left">
                <div class="icon-box plan-icon">🧭</div>
                <div class="header-text">
                  <h3 class="title">规划建议</h3>
                  <div class="subtitle-row" v-if="planMeta.period">
                    <span>{{ planMeta.period }}</span>
                    <el-icon v-if="planMeta.nextPeriod"><ArrowRight /></el-icon>
                    <span v-if="planMeta.nextPeriod">{{ planMeta.nextPeriod }}</span>
                  </div>
                </div>
              </div>
              <span class="ios-tag plan">规划</span>
            </div>
            <div class="card-body" v-loading="planLoading">
              <div v-if="planHtml" class="markdown-content plan-content">
                <div class="markdown-body" v-html="planHtml"></div>
                <div v-if="planMeta.generatedAt" class="timestamp">
                  生成于 {{ formatDateTime(planMeta.generatedAt) }}
                </div>
              </div>
              <div v-else class="empty-state">
                <span class="emoji">💭</span>
                <p>暂无规划建议</p>
              </div>
            </div>
          </section>
        </div>

        <!-- History Section -->
        <div class="ios-card history-section" v-loading="historyLoading">
          <div class="section-header">
            <div class="header-title">
              <span class="icon">🕒</span>
              <h3>历史记录</h3>
            </div>
            <div class="header-controls">
              <div class="ios-segmented-control small">
                <button
                  v-for="item in historyTypeOptions"
                  :key="item.value"
                  :class="['segment-btn', historyTypeValue === item.value && 'active']"
                  @click="historyTypeValue = item.value"
                >
                  {{ item.label }}
                </button>
              </div>
              <button class="icon-btn" @click="handleRefreshHistory">
                🔄
              </button>
            </div>
          </div>
          
          <div class="history-list" v-if="historyRows.length">
            <div
              class="history-item"
              v-for="item in historyRows"
              :key="item.id"
              @click="handlePreview(item)"
            >
              <div class="item-icon" :class="item.type">
                {{ item.type === 'plan' ? '🧭' : '📊' }}
              </div>
              <div class="item-content">
                <div class="item-top">
                  <span class="item-title">{{ item.typeLabel }}</span>
                  <span class="item-date">{{ item.createdAt }}</span>
                </div>
                <div class="item-bottom">
                  <span class="item-period">{{ item.period }}</span>
                  <span class="item-scope">{{ item.scopeLabel }}</span>
                </div>
              </div>
              <el-icon class="item-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
          <div v-else class="empty-history">
            <span class="text">暂无历史记录</span>
          </div>
        </div>
      </div>

      <!-- Preview Dialog -->
      <el-dialog
        v-model="previewDialogVisible"
        :title="previewDialog.title"
        width="90%"
        class="ios-dialog"
        destroy-on-close
        align-center
      >
        <div class="dialog-meta">
          <span class="meta-item" v-if="previewDialog.period">
            <el-icon><Calendar /></el-icon> {{ previewDialog.period }}
          </span>
          <span class="meta-item" v-if="previewDialog.generatedAt">
            <el-icon><Clock /></el-icon> {{ previewDialog.generatedAt }}
          </span>
        </div>
        <div
          v-if="previewDialog.html"
          class="markdown-body ios-markdown"
          v-html="previewDialog.html"
        ></div>
        <el-empty v-else description="暂无内容" />
      </el-dialog>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import dayjs from "dayjs";
import { marked } from "marked";
import DOMPurify from "dompurify";
import PageContainer from "@/components/layout/PageContainer.vue";
import { ArrowRight, Calendar, Clock } from "@element-plus/icons-vue";
import {
  useAIAssistantStore,
  type HistoryType,
  type Scope,
} from "@/stores/modules/aiAssistant";
import { useStageStore } from "@/stores/modules/stage";
marked.setOptions({ breaks: true, gfm: true });

interface HistoryRow {
  id: number;
  raw: any;
  type: HistoryType;
  typeLabel: string;
  scope: Scope;
  scopeLabel: string;
  period: string;
  nextPeriod?: string;
  createdAt: string;
}

interface PreviewDialogState {
  title: string;
  html: string;
  generatedAt: string;
  period?: string;
  nextPeriod?: string;
}

const scopeLabelMap: Record<Scope, string> = {
  day: "日度",
  week: "周度",
  month: "月度",
  stage: "阶段",
};

const aiStore = useAIAssistantStore();
const stageStore = useStageStore();

const scopeOptions: Array<{ value: Scope; label: string }> = [
  { value: "day", label: "日度" },
  { value: "week", label: "周度" },
  { value: "month", label: "月度" },
  { value: "stage", label: "阶段" },
];

const historyTypeOptions: Array<{ value: HistoryType; label: string }> = [
  { value: "all", label: "全部" },
  { value: "analysis", label: "分析" },
  { value: "plan", label: "规划" },
];

const analysisLoading = computed(() => aiStore.analysisLoading);
const planLoading = computed(() => aiStore.planLoading);
const historyLoading = computed(() => aiStore.historyLoading);

const scopeValue = computed<Scope>({
  get: () => aiStore.scope as Scope,
  set: (value) => {
    if (aiStore.scope !== value) {
      aiStore.setScope(value);
      aiStore.clearResults();
    }
  },
});

const dateValue = computed<string>({
  get: () => aiStore.selectedDate,
  set: (value) => {
    aiStore.setDate(value);
    aiStore.clearResults();
  },
});

const stageValue = computed<number | null>({
  get: () => aiStore.selectedStageId,
  set: (value) => {
    aiStore.setStage(value);
    aiStore.clearResults();
  },
});

const historyTypeValue = computed<HistoryType>({
  get: () => aiStore.historyType as HistoryType,
  set: (value) => {
    void aiStore.setHistoryType(value);
  },
});

const isStageScope = computed(() => scopeValue.value === "stage");
const datePickerType = computed(() =>
  scopeValue.value === "month" ? "month" : "date"
);
const datePlaceholder = computed(() => {
  switch (scopeValue.value) {
    case "day":
      return "选择具体日期";
    case "week":
      return "选择所在周任意日期";
    case "month":
      return "选择月份";
    default:
      return "";
  }
});

// 头部展示：当前选区信息
const scopeLabel = computed(() => scopeLabelMap[scopeValue.value]);
const currentStageLabel = computed(() => {
  if (!isStageScope.value) return "";
  const id = stageValue.value;
  const found = stageStore.stages.find((s: any) => Number(s.id) === Number(id));
  return found ? `阶段：${found.name}` : "阶段：未选择";
});

const currentPeriodLabel = computed(() => {
  if (isStageScope.value) return "";
  const d = dayjs(dateValue.value || dayjs());
  if (scopeValue.value === "day") {
    const dateStr = d.format("YYYY-MM-DD");
    return buildPeriodLabel("day", dateStr, dateStr);
  }
  if (scopeValue.value === "week") {
    const weekday = d.day();
    const monday = d.subtract((weekday + 6) % 7, "day");
    const sunday = monday.add(6, "day");
    return buildPeriodLabel(
      "week",
      monday.format("YYYY-MM-DD"),
      sunday.format("YYYY-MM-DD")
    );
  }
  // month
  const first = d.startOf("month");
  const last = d.endOf("month");
  return buildPeriodLabel(
    "month",
    first.format("YYYY-MM-DD"),
    last.format("YYYY-MM-DD")
  );
});

function renderMarkdown(text?: string) {
  if (!text) return "";
  const rawHtml = marked.parse(text) as string;
  return DOMPurify.sanitize(rawHtml);
}
const stageOptions = computed(() =>
  stageStore.stages.map((item: any) => ({
    label: item.name,
    value: Number(item.id),
  }))
);

const analysisInsight = computed(() => aiStore.analysisResult as any | null);
const planInsight = computed(() => aiStore.planResult as any | null);

const analysisHtml = computed(() =>
  renderMarkdown(analysisInsight.value?.text)
);
const planHtml = computed(() => renderMarkdown(planInsight.value?.text));

const analysisMeta = computed(() => ({
  period: analysisInsight.value?.period_label ?? "",
  generatedAt: analysisInsight.value?.generated_at ?? "",
}));

const planMeta = computed(() => ({
  period: planInsight.value?.period_label ?? "",
  nextPeriod: planInsight.value?.next_period_label ?? "",
  generatedAt: planInsight.value?.generated_at ?? "",
}));

const hasResult = computed(() => Boolean(analysisHtml.value || planHtml.value));

const previewDialogVisible = ref(false);
const datePicker = ref();
const previewDialog = ref<PreviewDialogState>({
  title: "",
  html: "",
  generatedAt: "",
  period: "",
  nextPeriod: "",
});

const historyRows = computed<HistoryRow[]>(() =>
  (aiStore.historyItems || []).map((item: any) => {
    const scope = (item.scope || "week") as Scope;
    const period =
      item.input_snapshot?.period_label ??
      buildPeriodLabel(scope, item.start_date, item.end_date);
    const nextPeriod =
      item.input_snapshot?.next_period_label ??
      buildPeriodLabel(scope, item.next_start_date, item.next_end_date);
    return {
      id: item.id,
      raw: item,
      type: item.insight_type as HistoryType,
      typeLabel: item.insight_type === "analysis" ? "分析" : "规划",
      scope,
      scopeLabel: scopeLabelMap[scope] || scope,
      period,
      nextPeriod,
      createdAt: formatDateTime(item.created_at),
    };
  })
);

function formatDateTime(value?: string) {
  if (!value) return "";
  return dayjs(value).format("YYYY-MM-DD HH:mm");
}

function openDatePicker() {
  const picker = datePicker.value as any;
  if (!picker) return;
  if (typeof picker.focus === "function") picker.focus();
  if (typeof picker.handleOpen === "function") picker.handleOpen();
}

function buildPeriodLabel(
  scope: Scope,
  start?: string | null,
  end?: string | null
) {
  if (!start && !end) return "";
  if (start && end) {
    if (start === end) {
      return `${scopeLabelMap[scope]}（${start}）`;
    }
    return `${scopeLabelMap[scope]}（${start} 至 ${end}）`;
  }
  if (start) {
    return `${scopeLabelMap[scope]}（自 ${start} 起）`;
  }
  if (end) {
    return `${scopeLabelMap[scope]}（至 ${end}）`;
  }
  return scopeLabelMap[scope];
}

async function handleGenerateAnalysis() {
  await aiStore.generateAnalysis();
}

async function handleGeneratePlan() {
  await aiStore.generatePlan();
}

function handleClear() {
  aiStore.clearResults();
}

async function handleRefreshHistory() {
  await aiStore.fetchHistory(scopeValue.value);
}

function openPreviewFromResult(type: "analysis" | "plan") {
  const insight =
    type === "analysis" ? analysisInsight.value : planInsight.value;
  if (!insight) return;
  previewDialog.value = {
    title: type === "analysis" ? "分析总结" : "规划建议",
    html: renderMarkdown(insight.text) || "",
    generatedAt: insight.generated_at
      ? formatDateTime(insight.generated_at)
      : "",
    period: insight.period_label ?? "",
    nextPeriod: insight.next_period_label ?? "",
  };
  previewDialogVisible.value = true;
}

function handlePreview(row: HistoryRow) {
  previewDialog.value = {
    title: row.type === "analysis" ? "历史分析" : "历史规划",
    html: renderMarkdown(row.raw.output_text) || "",
    generatedAt: row.createdAt,
    period: row.period,
    nextPeriod: row.nextPeriod,
  };
  previewDialogVisible.value = true;
}

onMounted(async () => {
  await aiStore.init();
});
</script>

<style scoped lang="scss">
.ios-view {
  min-height: 100%;
  background-color: transparent; /* Allow global background to show */
}

.ios-content-wrapper {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 40px;
}

/* --- iOS Card Generic --- */
.ios-card {
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  }
}

/* --- Control Panel --- */
.control-panel {
  padding: 24px;
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    
    .panel-title {
      font-size: 20px;
      font-weight: 700;
      color: #1c1c1e;
      margin: 0;
    }

    .current-status {
      display: flex;
      gap: 8px;
    }

    .status-badge {
      padding: 6px 12px;
      background: #e5e5ea; /* iOS System Gray 5 */
      color: #1c1c1e;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      
      &.secondary {
        background: #f2f2f7;
        color: #8e8e93;
      }
    }
  }

  .panel-body {
    display: flex;
    flex-wrap: wrap;
    gap: 24px;
    align-items: flex-end;
  }
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 10px;

  .group-label {
    font-size: 13px;
    font-weight: 600;
    color: #8e8e93; /* iOS System Gray */
    margin-left: 4px;
  }
}

/* iOS Segmented Control */
.ios-segmented-control {
  background: #e5e5ea;
  padding: 3px;
  border-radius: 9px;
  display: inline-flex;
  position: relative;
  
  &.small {
    padding: 2px;
    border-radius: 8px;
    
    .segment-btn {
      padding: 4px 12px;
      font-size: 12px;
    }
  }

  .segment-btn {
    border: none;
    background: transparent;
    padding: 8px 20px;
    border-radius: 7px;
    font-size: 14px;
    font-weight: 500;
    color: #1c1c1e;
    cursor: pointer;
    transition: all 0.2s ease;

    &.active {
      background: #ffffff;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.12);
      font-weight: 600;
    }
  }
}

/* iOS Picker Button */
.picker-wrapper {
  display: flex;
  align-items: center;
}

.ios-picker-btn {
  background: #f2f2f7;
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.2s;
  min-width: 220px;
  justify-content: space-between;

  &:hover {
    background: #e5e5ea;
  }

  .icon {
    font-size: 16px;
  }

  .value {
    font-size: 15px;
    font-weight: 600;
    color: #007aff; /* iOS Blue */
    flex: 1;
    text-align: left;
  }

  .arrow {
    font-size: 14px;
    color: #c7c7cc;
  }
}

.ios-select {
  width: 220px;
  
  :deep(.el-input__wrapper) {
    background-color: #f2f2f7;
    border-radius: 12px;
    box-shadow: none !important;
    padding: 4px 12px;
  }
  
  :deep(.el-input__inner) {
    font-weight: 600;
    color: #007aff;
  }
}

:deep(.hidden-date-input) {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  width: 1px;
  height: 1px;
  overflow: hidden;
}

/* Action Buttons */
.action-group {
  display: flex;
  gap: 12px;
  margin-left: auto;
}

.ios-btn {
  border: none;
  padding: 12px 24px;
  border-radius: 14px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: transform 0.1s, opacity 0.2s;

  &:active {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.primary {
    background: #007aff;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);

    &:hover:not(:disabled) {
      background: #006ce6;
    }
  }

  &.primary-alt {
    background: #34c759; /* iOS Green */
    color: white;
    box-shadow: 0 4px 12px rgba(52, 199, 89, 0.3);

    &:hover:not(:disabled) {
      background: #2db84f;
    }
  }

  &.ghost {
    background: #f2f2f7;
    color: #ff3b30; /* iOS Red */
    padding: 12px;
    
    &:hover:not(:disabled) {
      background: #e5e5ea;
    }
  }
}

/* --- Results Grid --- */
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.result-card {
  display: flex;
  flex-direction: column;
  min-height: 400px;
  
  &.is-loading {
    opacity: 0.8;
    pointer-events: none;
  }

  .card-header {
    padding: 20px 24px;
    border-bottom: 1px solid #f2f2f7;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;

    .header-left {
      display: flex;
      gap: 16px;
      align-items: center;
    }

    .icon-box {
      width: 48px;
      height: 48px;
      border-radius: 12px;
      display: grid;
      place-items: center;
      font-size: 24px;
      
      &.analysis-icon {
        background: #eaf2ff; /* Light Blue */
      }
      &.plan-icon {
        background: #e8f8f0; /* Light Green */
      }
    }

    .header-text {
      .title {
        font-size: 18px;
        font-weight: 700;
        color: #1c1c1e;
        margin: 0 0 4px 0;
      }
      
      .subtitle, .subtitle-row {
        font-size: 13px;
        color: #8e8e93;
        display: flex;
        align-items: center;
        gap: 4px;
      }
    }
  }

  .ios-tag {
    font-size: 11px;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 999px;
    text-transform: uppercase;
    letter-spacing: 0.5px;

    &.latest {
      background: #eaf2ff;
      color: #007aff;
    }
    &.plan {
      background: #e8f8f0;
      color: #34c759;
    }
  }

  .card-body {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
    background: #ffffff;
  }
}

.markdown-content {
  .timestamp {
    margin-top: 24px;
    font-size: 12px;
    color: #c7c7cc;
    text-align: right;
  }
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #c7c7cc;
  gap: 12px;

  .emoji {
    font-size: 48px;
    opacity: 0.5;
  }
  
  p {
    font-size: 15px;
    font-weight: 500;
  }
}

/* --- History Section --- */
.history-section {
  padding: 24px;

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-title {
      display: flex;
      align-items: center;
      gap: 10px;
      
      .icon { font-size: 20px; }
      h3 {
        margin: 0;
        font-size: 18px;
        font-weight: 700;
        color: #1c1c1e;
      }
    }

    .header-controls {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .icon-btn {
      background: #f2f2f7;
      border: none;
      width: 32px;
      height: 32px;
      border-radius: 50%;
      cursor: pointer;
      display: grid;
      place-items: center;
      font-size: 14px;
      color: #8e8e93;
      transition: all 0.2s;

      &:hover {
        background: #e5e5ea;
        color: #007aff;
      }
    }
  }
}

.history-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
}

.history-item {
  background: #f9f9f9; /* Very light gray */
  border-radius: 16px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: background 0.2s;

  &:hover {
    background: #f2f2f7;
  }

  .item-icon {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: grid;
    place-items: center;
    font-size: 20px;
    flex-shrink: 0;

    &.analysis { background: #eaf2ff; }
    &.plan { background: #e8f8f0; }
  }

  .item-content {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .item-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .item-title {
      font-size: 15px;
      font-weight: 600;
      color: #1c1c1e;
    }
    
    .item-date {
      font-size: 12px;
      color: #8e8e93;
    }
  }

  .item-bottom {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .item-period {
      font-size: 13px;
      color: #3a3a3c;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    .item-scope {
      font-size: 11px;
      color: #8e8e93;
      background: #ffffff;
      padding: 2px 6px;
      border-radius: 4px;
    }
  }

  .item-arrow {
    color: #c7c7cc;
    font-size: 14px;
  }
}

.empty-history {
  padding: 40px;
  text-align: center;
  color: #8e8e93;
  font-size: 14px;
}

/* --- Dialog & Markdown --- */
.ios-dialog {
  :deep(.el-dialog) {
    border-radius: 20px;
    overflow: hidden;
  }
  
  :deep(.el-dialog__header) {
    margin: 0;
    padding: 20px 24px;
    border-bottom: 1px solid #f2f2f7;
    
    .el-dialog__title {
      font-weight: 700;
      font-size: 18px;
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
    max-height: 70vh;
    overflow-y: auto;
  }
}

.dialog-meta {
  display: flex;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px dashed #e5e5ea;
  
  .meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    color: #8e8e93;
  }
}

/* Markdown Styles for iOS Theme */
:deep(.markdown-body) {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #1c1c1e;
  line-height: 1.6;
  
  h1, h2, h3 {
    border-bottom: none;
    margin-top: 24px;
    margin-bottom: 12px;
    font-weight: 700;
  }
  
  h1 { font-size: 24px; }
  h2 { font-size: 20px; }
  h3 { font-size: 17px; }
  
  p { margin-bottom: 16px; }
  
  ul, ol {
    padding-left: 24px;
    margin-bottom: 16px;
  }
  
  li { margin-bottom: 8px; }
  
  blockquote {
    border-left: 4px solid #007aff;
    background: #f2f2f7;
    padding: 12px 16px;
    border-radius: 8px;
    color: #3a3a3c;
    margin: 16px 0;
  }
  
  code {
    background: #f2f2f7;
    color: #ff2d55;
    padding: 2px 6px;
    border-radius: 6px;
    font-size: 0.9em;
  }
  
  pre {
    background: #1c1c1e;
    border-radius: 12px;
    padding: 16px;
    
    code {
      background: transparent;
      color: #ffffff;
      padding: 0;
    }
  }
}

@media (max-width: 768px) {
  .control-panel .panel-body {
    flex-direction: column;
    align-items: stretch;
  }
  
  .action-group {
    width: 100%;
    justify-content: space-between;
    
    .ios-btn {
      flex: 1;
      justify-content: center;
    }
  }
  
  .results-grid {
    grid-template-columns: 1fr;
  }
}
</style>
