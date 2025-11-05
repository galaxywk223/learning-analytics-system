<template>
  <div class="ai-assistant">
    <header class="ai-assistant__header">
      <h1>智能规划助手</h1>
      <p>按日、周、月或阶段梳理学习数据，生成易读的总结与下一步规划，并支持历史追溯。</p>
      <div class="meta-chips">
        <span class="chip"><span class="dot" />{{ scopeLabel }}</span>
        <span class="chip" v-if="!isStageScope">{{ currentPeriodLabel }}</span>
        <span class="chip" v-else>{{ currentStageLabel }}</span>
      </div>
    </header>

    <el-card class="control-card" shadow="never">
      <div class="control-grid">
        <div class="control-grid__item">
          <span class="control-label">分析范围</span>
          <el-radio-group v-model="scopeValue" size="small">
            <el-radio-button v-for="item in scopeOptions" :key="item.value" :label="item.value">
              {{ item.label }}
            </el-radio-button>
          </el-radio-group>
        </div>

        <div class="control-grid__item" v-if="!isStageScope">
          <span class="control-label">选择日期</span>
          <el-date-picker
            v-model="dateValue"
            :type="datePickerType"
            value-format="YYYY-MM-DD"
            :placeholder="datePlaceholder"
            :clearable="false"
          />
        </div>

        <div class="control-grid__item" v-else>
          <span class="control-label">选择阶段</span>
          <el-select v-model="stageValue" placeholder="请选择阶段" filterable>
            <el-option
              v-for="stage in stageOptions"
              :key="stage.value"
              :label="stage.label"
              :value="stage.value"
            />
          </el-select>
        </div>

        <div class="control-grid__item control-grid__item--actions">
          <el-button type="primary" :loading="analysisLoading" @click="handleGenerateAnalysis">
            生成分析
          </el-button>
          <el-button type="success" :loading="planLoading" @click="handleGeneratePlan">
            生成规划
          </el-button>
          <el-button text type="default" :disabled="!hasResult" @click="handleClear">
            清空结果
          </el-button>
        </div>
      </div>
    </el-card>

        <div class="insight-grid">
      <section class="insight-card" :class="{ 'is-loading': analysisLoading }">
        <header class="insight-card__header">
          <div>
            <span class="title">分析总结</span>
            <small v-if="analysisMeta.period">{{ analysisMeta.period }}</small>
          </div>
          <div class="insight-card__actions">
            <el-tag type="info" effect="plain" size="small">最新</el-tag>
            <el-button
              v-if="analysisHtml"
              text
              size="small"
              @click="openPreviewFromResult('analysis')"
            >
              查看详情
            </el-button>
          </div>
        </header>
        <div class="insight-card__body" v-loading="analysisLoading">
          <div v-if="analysisHtml" class="insight-content">
            <div class="markdown-body" v-html="analysisHtml"></div>
            <p v-if="analysisMeta.generatedAt" class="insight-content__time">
              生成时间：{{ formatDateTime(analysisMeta.generatedAt) }}
            </p>
          </div>
          <el-empty
            v-else
            description="暂无分析结果，点击上方按钮生成。"
          />
        </div>
      </section>

      <section class="insight-card" :class="{ 'is-loading': planLoading }">
        <header class="insight-card__header">
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
          <div class="insight-card__actions">
            <el-tag type="success" effect="plain" size="small">规划</el-tag>
            <el-button
              v-if="planHtml"
              text
              size="small"
              @click="openPreviewFromResult('plan')"
            >
              查看详情
            </el-button>
          </div>
        </header>
        <div class="insight-card__body" v-loading="planLoading">
          <div v-if="planHtml" class="insight-content">
            <div class="markdown-body" v-html="planHtml"></div>
            <p v-if="planMeta.generatedAt" class="insight-content__time">
              生成时间：{{ formatDateTime(planMeta.generatedAt) }}
            </p>
          </div>
          <el-empty
            v-else
            description="暂无规划结果，点击上方按钮生成。"
          />
        </div>
      </section>
    </div>

    <el-card class="history-card" shadow="never" v-loading="historyLoading">
      <template #header>
        <div class="history-card__header">
          <span>历史记录</span>
          <div class="history-card__controls">
            <el-radio-group v-model="historyTypeValue" size="small">
              <el-radio-button v-for="item in historyTypeOptions" :key="item.value" :label="item.value">
                {{ item.label }}
              </el-radio-button>
            </el-radio-group>
            <el-button text size="small" @click="handleRefreshHistory">刷新</el-button>
          </div>
        </div>
      </template>

      <el-empty v-if="!historyRows.length" description="暂无记录" />
      <el-timeline v-else class="history-timeline">
        <el-timeline-item
          v-for="item in historyRows"
          :key="item.id"
          :timestamp="item.createdAt"
          :type="item.type === 'plan' ? 'success' : 'primary'"
        >
          <div class="history-item">
            <div class="history-item__header">
              <el-tag
                :type="item.type === 'plan' ? 'success' : 'info'"
                effect="plain"
                size="small"
              >
                {{ item.typeLabel }}
              </el-tag>
              <span class="history-item__scope">{{ item.scopeLabel }}</span>
            </div>
            <div class="history-item__period">{{ item.period }}</div>
            <div class="history-item__actions">
              <el-button text type="primary" size="small" @click="handlePreview(item)">
                查看
              </el-button>
            </div>
          </div>
        </el-timeline-item>
      </el-timeline>
    
    <el-dialog
      v-model="previewDialogVisible"
      :title="previewDialog.title"
      width="720px"
      class="preview-dialog"
      destroy-on-close
    >
      <div class="preview-dialog__meta">
        <span v-if="previewDialog.period">{{ previewDialog.period }}</span>
        <span v-if="previewDialog.generatedAt">生成时间：{{ previewDialog.generatedAt }}</span>
        <span v-if="previewDialog.nextPeriod">下一阶段：{{ previewDialog.nextPeriod }}</span>
      </div>
      <div v-if="previewDialog.html" class="markdown-body" v-html="previewDialog.html"></div>
      <el-empty v-else description="暂无内容" />
    </el-dialog>
</el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import dayjs from "dayjs";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { ArrowRight } from "@element-plus/icons-vue";
import { useAIAssistantStore, type HistoryType, type Scope } from "@/stores/modules/aiAssistant";
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
const datePickerType = computed(() => (scopeValue.value === "month" ? "month" : "date"));
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
    return buildPeriodLabel("week", monday.format("YYYY-MM-DD"), sunday.format("YYYY-MM-DD"));
  }
  // month
  const first = d.startOf("month");
  const last = d.endOf("month");
  return buildPeriodLabel("month", first.format("YYYY-MM-DD"), last.format("YYYY-MM-DD"));
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

const analysisHtml = computed(() => renderMarkdown(analysisInsight.value?.text));
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
    const period = item.input_snapshot?.period_label ?? buildPeriodLabel(scope, item.start_date, item.end_date);
    const nextPeriod =
      item.input_snapshot?.next_period_label ?? buildPeriodLabel(scope, item.next_start_date, item.next_end_date);
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

function buildPeriodLabel(scope: Scope, start?: string | null, end?: string | null) {
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
  const insight = type === "analysis" ? analysisInsight.value : planInsight.value;
  if (!insight) return;
  previewDialog.value = {
    title: type === "analysis" ? "分析总结" : "规划建议",
    html: renderMarkdown(insight.text) || "",
    generatedAt: insight.generated_at ? formatDateTime(insight.generated_at) : "",
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
  gap: 20px;
  min-height: 100%;
  padding: 24px;
  isolation: isolate;
  background: linear-gradient(180deg, #fafbff 0%, #ffffff 100%);

  &__header {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 16px 18px;
    border-radius: 14px;
    background: #fff;
    border: 1px solid var(--color-border-card);
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);

    h1 {
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      color: #1f1d47;
    }

    p {
      margin: 0;
      color: #64748b;
      font-size: 14px;
    }
  }

  .meta-chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 4px;

    .chip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border: 1px solid var(--stroke-soft);
      background: var(--surface-card);
      color: #334155;
      border-radius: 999px;
      font-size: 12px;
      line-height: 1;
    }

    .dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--color-primary);
      box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.15);
    }
  }
}

.control-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--color-border-card);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  padding: 18px 20px;

  .control-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px 24px;
    align-items: center;

    &__item {
      display: flex;
      flex-direction: column;
      gap: 10px;

      &--actions {
        flex-direction: row;
        align-items: center;
        justify-content: flex-start;
        gap: 12px;
        flex-wrap: wrap;
      }
    }

    .control-label {
      font-size: 12px;
      color: #64748b;
      font-weight: 500;
      letter-spacing: 0.2px;
    }
  }
}


.insight-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 20px;
}

.insight-card {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  border: 1px solid var(--color-border-card);
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

  .title {
    font-size: 19px;
    font-weight: 600;
    display: block;
    color: #1f1d47;
  }

  small {
    color: rgba(79, 70, 229, 0.7);
    font-size: 12px;
  }
}

.insight-card__actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.insight-card__body {
  min-height: 260px;
  display: flex;
  flex-direction: column;
}

.history-card {
  background: #fff;
  border-radius: 14px;
  border: 1px solid var(--color-border-card);
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
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
  background: linear-gradient(135deg, rgba(248, 250, 255, 0.96), rgba(237, 233, 254, 0.92));
  border-radius: 16px;
  padding: 14px 18px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  border: 1px solid rgba(129, 140, 248, 0.16);
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












