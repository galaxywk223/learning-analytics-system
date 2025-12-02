<template>
  <div class="ai-assistant">
    <PageContainer
      :title="{ icon: '🤖', text: '智能规划' }"
      subtitle="按日、周、月或阶段梳理学习数据，生成易读的总结与下一步规划，并支持历史追溯。"
    >
      <div class="glass-control">
        <div class="meta-chips">
          <span class="chip"><span class="dot" />{{ scopeLabel }}</span>
          <span class="chip" v-if="!isStageScope">{{ currentPeriodLabel }}</span>
          <span class="chip" v-else>{{ currentStageLabel }}</span>
        </div>
        <div class="control-row">
          <div class="segment">
            <span class="seg-label">分析范围</span>
            <div class="segmented">
              <button
                v-for="item in scopeOptions"
                :key="item.value"
                :class="['seg-btn', scopeValue === item.value && 'active']"
                @click="scopeValue = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
          <div class="picker">
            <template v-if="!isStageScope">
              <button class="pill-picker" @click="datePicker?.focus?.()">
                <span class="emoji-icon" aria-hidden="true">📅</span>
                <span>{{ dateValue || datePlaceholder }}</span>
                <span class="caret">▾</span>
              </button>
              <el-date-picker
                ref="datePicker"
                v-model="dateValue"
                :type="datePickerType"
                value-format="YYYY-MM-DD"
                :placeholder="datePlaceholder"
                :clearable="false"
                style="display: none"
              />
            </template>
            <template v-else>
              <el-select
                v-model="stageValue"
                placeholder="请选择阶段"
                filterable
                class="minimal-select"
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
          <div class="actions">
            <button
              class="btn-primary"
              :disabled="analysisLoading || planLoading"
              @click="handleGenerateAnalysis"
            >
              ✨ 生成分析
            </button>
            <button
              class="btn-primary alt"
              :disabled="analysisLoading || planLoading"
              @click="handleGeneratePlan"
            >
              🤖 生成规划
            </button>
            <button class="btn-ghost" :disabled="!hasResult" @click="handleClear">
              🗑️ 清空
            </button>
          </div>
        </div>
      </div>

      <div class="insight-grid">
        <section
          class="glass-card insight-card"
          :class="{ 'is-loading': analysisLoading }"
        >
          <header class="insight-card__header">
            <div class="title-wrap">
              <span class="icon">📊</span>
              <div>
                <span class="title">分析总结</span>
                <small v-if="analysisMeta.period">{{ analysisMeta.period }}</small>
              </div>
            </div>
            <span class="pill latest">最新</span>
          </header>
          <div class="insight-card__body" v-loading="analysisLoading">
            <div v-if="analysisHtml" class="bubble">
              <div class="markdown-body" v-html="analysisHtml"></div>
              <p v-if="analysisMeta.generatedAt" class="insight-content__time">
                生成时间：{{ formatDateTime(analysisMeta.generatedAt) }}
              </p>
            </div>
            <div v-else class="empty-robot">
              <span class="bot">🤔</span>
              <p>等待输入数据...</p>
            </div>
          </div>
        </section>

        <section class="glass-card insight-card" :class="{ 'is-loading': planLoading }">
          <header class="insight-card__header">
            <div class="title-wrap">
              <span class="icon">🤖</span>
              <div>
                <span class="title">规划建议</span>
                <div class="result-card__sub" v-if="planMeta.period">
                  <small>{{ planMeta.period }}</small>
                  <el-icon v-if="planMeta.nextPeriod" size="14" class="result-card__arrow">
                    <ArrowRight />
                  </el-icon>
                  <small v-if="planMeta.nextPeriod">{{ planMeta.nextPeriod }}</small>
                </div>
              </div>
            </div>
            <span class="pill plan">规划</span>
          </header>
          <div class="insight-card__body" v-loading="planLoading">
            <div v-if="planHtml" class="bubble bubble-ai">
              <div class="markdown-body" v-html="planHtml"></div>
              <p v-if="planMeta.generatedAt" class="insight-content__time">
                生成时间：{{ formatDateTime(planMeta.generatedAt) }}
              </p>
            </div>
            <div v-else class="empty-robot">
              <span class="bot">💭</span>
              <p>等待输入数据...</p>
            </div>
          </div>
        </section>
      </div>

      <div class="history-stream glass-card" v-loading="historyLoading">
        <div class="history-stream__header">
          <div class="title-wrap">
            <span class="icon">🕒</span>
            <div>
              <h4>历史记录</h4>
              <p>以时间序排列你的每次生成</p>
            </div>
          </div>
          <div class="history-stream__controls">
            <el-radio-group v-model="historyTypeValue" size="small">
              <el-radio-button
                v-for="item in historyTypeOptions"
                :key="item.value"
                :label="item.value"
              >
                {{ item.label }}
              </el-radio-button>
            </el-radio-group>
            <button class="btn-ghost" @click="handleRefreshHistory">刷新</button>
          </div>
        </div>
        <div class="history-list" v-if="historyRows.length">
          <div
            class="history-card-lite"
            v-for="item in historyRows"
            :key="item.id"
            @click="handlePreview(item)"
          >
            <div class="history-meta">
              <span class="pill" :class="item.type === 'plan' ? 'plan' : 'analysis'">
                {{ item.typeLabel }}
              </span>
              <span class="scope">{{ item.scopeLabel }}</span>
            </div>
            <div class="history-period">{{ item.period }}</div>
            <div class="history-footer">
              <span class="time">{{ item.createdAt }}</span>
              <span class="arrow">›</span>
            </div>
          </div>
        </div>
        <el-empty v-else description="暂无记录" />
      </div>

        <el-dialog
          v-model="previewDialogVisible"
          :title="previewDialog.title"
          width="720px"
          class="preview-dialog"
          destroy-on-close
        >
          <div class="preview-dialog__meta">
            <span v-if="previewDialog.period">{{ previewDialog.period }}</span>
            <span v-if="previewDialog.generatedAt"
              >生成时间：{{ previewDialog.generatedAt }}</span
            >
            <span v-if="previewDialog.nextPeriod"
              >下一阶段：{{ previewDialog.nextPeriod }}</span
            >
          </div>
          <div
            v-if="previewDialog.html"
            class="markdown-body"
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
import { ArrowRight } from "@element-plus/icons-vue";
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
.ai-assistant {
  position: relative;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  isolation: isolate;
  background: transparent;

.glass-control {
  margin-top: 6px;
  background: rgba(255, 255, 255, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 24px;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.14);
  backdrop-filter: blur(14px);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 12px;

  .meta-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border: 1px solid rgba(148, 163, 184, 0.35);
      background: rgba(255, 255, 255, 0.5);
      color: #475569;
      border-radius: 999px;
      font-size: 12px;
      line-height: 1;
      backdrop-filter: blur(8px);
    }

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--color-primary);
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.12);
    }
  }

  .control-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 12px;
    align-items: center;
  }

  .segment {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
  }

  .seg-label {
    color: #475569;
    font-weight: 600;
    font-size: 13px;
  }

  .segmented {
    display: inline-flex;
    background: #f1f3f5;
    border-radius: 999px;
    padding: 4px;
    gap: 4px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
  }

  .seg-btn {
    border: none;
    background: transparent;
    padding: 10px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 86px;
  }

  .seg-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.12);
  }

  .picker {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .pill-picker {
    border: 1px solid rgba(148, 163, 184, 0.35);
    background: rgba(255, 255, 255, 0.7);
    color: #0f172a;
    padding: 10px 14px;
    border-radius: 12px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    cursor: pointer;
    transition: all 0.2s ease;
    backdrop-filter: blur(8px);

    &:hover {
      background: rgba(241, 245, 249, 0.9);
      box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
    }

    .caret {
      color: #94a3b8;
      font-weight: 700;
    }
  }

  .minimal-select {
    min-width: 180px;
  }

  .actions {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }

  .btn-primary {
    border: none;
    color: #ffffff;
    padding: 12px 16px;
    border-radius: 14px;
    font-weight: 700;
    cursor: pointer;
    background: linear-gradient(135deg, #7c3aed, #2563eb);
    box-shadow: 0 14px 32px rgba(79, 70, 229, 0.35);
    transition: transform 0.2s ease, box-shadow 0.2s ease;

    &.alt {
      background: linear-gradient(135deg, #22c55e, #06b6d4);
      box-shadow: 0 14px 32px rgba(34, 197, 94, 0.28);
    }

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 16px 36px rgba(15, 23, 42, 0.18);
    }

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
      box-shadow: none;
      transform: none;
    }
  }

  .btn-ghost {
    border: none;
    background: rgba(248, 250, 252, 0.8);
    color: #64748b;
    padding: 10px 12px;
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 10px 20px rgba(15, 23, 42, 0.06);

    &:hover {
      background: #ffffff;
      color: #0f172a;
    }
  }
}
}

.insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
}

.glass-card {
  position: relative;
  background: rgba(255, 255, 255, 0.42);
  border-radius: 24px;
  padding: 18px 20px;
  box-shadow: 0 18px 46px rgba(15, 23, 42, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.35);
  backdrop-filter: blur(14px);
}

.insight-card {
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;

  &.is-loading {
    opacity: 0.72;
  }
}

.insight-card__header {
  position: relative;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;

  .title-wrap {
    display: flex;
    gap: 10px;
    align-items: center;
  }

  .icon {
    font-size: 18px;
  }

  .title {
    font-size: 19px;
    font-weight: 700;
    display: block;
    color: #1f1d47;
  }

  small {
    color: rgba(79, 70, 229, 0.7);
    font-size: 12px;
  }
}

.pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 12px;
  background: rgba(99, 102, 241, 0.14);
  color: #4338ca;

  &.latest {
    background: rgba(59, 130, 246, 0.18);
    color: #1d4ed8;
  }

  &.plan {
    background: rgba(16, 185, 129, 0.16);
    color: #047857;
  }
}

.insight-card__body {
  min-height: 260px;
  display: flex;
  flex-direction: column;
}

.bubble {
  background: rgba(248, 250, 252, 0.8);
  border-radius: 18px;
  padding: 14px 16px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(226, 232, 240, 0.7);
}

.bubble-ai {
  background: linear-gradient(135deg, rgba(124, 58, 237, 0.12), rgba(37, 99, 235, 0.12));
  border: 1px solid rgba(124, 58, 237, 0.2);
}

.empty-robot {
  flex: 1;
  display: grid;
  place-items: center;
  color: #94a3b8;
  gap: 8px;

  .bot {
    font-size: 28px;
  }
}

.history-card {
  background: rgba(255, 255, 255, 0.4);
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(12px);
  padding: 18px;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.history-timeline {
  padding-left: 6px;

  .el-timeline-item__content {
    width: 100%;
  }
}

.history-item {
  background: rgba(255, 255, 255, 0.35);
  border-radius: 16px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
}

.history-item__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.history-item__scope {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.history-item__period {
  font-size: 14px;
  color: #111827;
  font-weight: 500;
}

.history-item__actions {
  display: flex;
  justify-content: flex-end;
}

.history-stream {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;

  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
  }

  .title-wrap {
    display: flex;
    align-items: center;
    gap: 10px;

    h4 {
      margin: 0;
      font-size: 1rem;
      font-weight: 700;
      color: #0f172a;
    }

    p {
      margin: 2px 0 0;
      color: #6b7280;
      font-size: 0.88rem;
    }
  }

  .icon {
    font-size: 18px;
  }

  &__controls {
    display: flex;
    align-items: center;
    gap: 10px;
  }
}

.history-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.history-card-lite {
  background: rgba(255, 255, 255, 0.78);
  border-radius: 16px;
  padding: 12px 14px;
  border: 1px solid rgba(226, 232, 240, 0.7);
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 16px 36px rgba(15, 23, 42, 0.12);
  }
}

.history-meta {
  display: flex;
  align-items: center;
  gap: 8px;

  .scope {
    color: #475569;
    font-weight: 600;
    font-size: 13px;
  }
}

.history-period {
  font-weight: 700;
  color: #0f172a;
  font-size: 14px;
}

.history-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #94a3b8;
  font-size: 12px;

  .arrow {
    font-weight: 800;
    color: #64748b;
  }
}

.preview-dialog__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-bottom: 12px;
}

.preview-dialog .markdown-body {
  max-height: 480px;
  overflow-y: auto;
}

.insight-content {
  display: flex;
  flex-direction: column;
  gap: 12px;

  .markdown-body {
    font-size: 14px;
    line-height: 1.7;
    display: flex;
    flex-direction: column;
    gap: 12px;

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
      margin: 0;
      font-weight: 600;
      line-height: 1.4;
    }

    h2 {
      font-size: 18px;
    }

    h3 {
      font-size: 16px;
    }

    p {
      margin: 0;
      white-space: pre-wrap;
    }

    ul,
    ol {
      margin: 0;
      padding-left: 20px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    li {
      line-height: 1.6;
    }

    hr {
      border: none;
      border-top: 1px solid var(--el-border-color-lighter);
      margin: 8px 0;
    }

    code {
      background-color: var(--el-fill-color-light);
      padding: 0 4px;
      border-radius: 4px;
      font-size: 90%;
    }

    strong {
      font-weight: 600;
    }
  }

  &__time {
    margin: 0;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
}

@media (max-width: 768px) {
  .control-card .control-grid {
    grid-template-columns: 1fr;
  }
}
</style>
