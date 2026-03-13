<template>
  <!-- eslint-disable vue/no-v-html -->
  <div class="briefing-view">
    <PageContainer
      :title="{ icon: '🤖', text: '智能规划' }"
      subtitle="先复盘，再作战。"
    >
      <div class="briefing-shell">
        <section class="hero-card">
          <div>
            <span class="eyebrow">AI Briefing Desk</span>
            <h2>把学习记录压缩成一份可执行的作战简报</h2>
            <p>不是玩具文案，而是围绕状态、风险、机会与下一步打法的决策台。</p>
          </div>
          <div class="hero-actions">
            <button
              class="hero-btn primary"
              :disabled="briefingLoading || diagnosisRefreshing"
              @click="handleGenerateBriefing"
            >
              {{ briefingLoading ? "生成中..." : "生成复盘作战台" }}
            </button>
            <button
              class="hero-btn secondary"
              :disabled="briefingLoading || diagnosisRefreshing || !briefingResult"
              @click="handleRefreshDiagnosis"
            >
              {{ diagnosisRefreshing ? "刷新中..." : "仅刷新诊断" }}
            </button>
            <button
              class="hero-btn ghost"
              :disabled="!briefingResult"
              @click="handleClear"
            >
              清空
            </button>
          </div>
        </section>

        <section class="panel-card">
          <div class="panel-head">
            <div>
              <span class="eyebrow">控制区</span>
              <h3>配置复盘范围</h3>
            </div>
            <div class="chip-row">
              <span class="chip">{{ scopeLabel }}</span>
              <span class="chip muted">{{ currentSelectionLabel }}</span>
            </div>
          </div>
          <div class="control-grid">
            <div class="control-block">
              <label>时间维度</label>
              <div class="segmented">
                <button
                  v-for="item in scopeOptions"
                  :key="item.value"
                  :class="['segmented-btn', scopeValue === item.value && 'active']"
                  @click="scopeValue = item.value"
                >
                  {{ item.label }}
                </button>
              </div>
            </div>
            <div class="control-block">
              <label>选择范围</label>
              <button v-if="!isStageScope" class="picker-btn" @click="openDatePicker">
                {{ dateValue || datePlaceholder }}
              </button>
              <el-date-picker
                v-if="!isStageScope"
                ref="datePicker"
                v-model="dateValue"
                :type="datePickerType"
                value-format="YYYY-MM-DD"
                :placeholder="datePlaceholder"
                :clearable="false"
                class="hidden-date-input"
              />
              <el-select
                v-else
                v-model="stageValue"
                placeholder="请选择阶段"
                filterable
                class="stage-select"
                :teleported="false"
              >
                <el-option
                  v-for="stage in stageOptions"
                  :key="stage.value"
                  :label="stage.label"
                  :value="stage.value"
                />
              </el-select>
            </div>
            <div class="control-block">
              <label>最近生成</label>
              <div class="meta-box">
                <strong>{{ latestGeneratedLabel }}</strong>
                <span>{{ latestPeriodLabel }}</span>
              </div>
            </div>
          </div>
        </section>

        <section v-if="briefingResult" class="battle-desk">
          <section class="panel-card overview-card">
            <div class="overview-main">
              <span class="status-pill" :class="`status-${statusTone}`">{{ statusLabel }}</span>
              <h3>{{ briefingResult.diagnosis.core_judgement }}</h3>
              <p>{{ briefingResult.diagnosis.strategy_bias }}</p>
            </div>
            <div class="overview-stats">
              <div class="mini-stat">
                <span>当前周期</span>
                <strong>{{ briefingResult.meta.period_label }}</strong>
              </div>
              <div class="mini-stat">
                <span>下一周期</span>
                <strong>{{ briefingResult.meta.next_period_label }}</strong>
              </div>
              <div class="mini-stat">
                <span>生成时间</span>
                <strong>{{ formatDateTime(briefingResult.meta.generated_at) }}</strong>
              </div>
            </div>
          </section>

          <div class="info-grid">
            <section class="panel-card">
              <span class="eyebrow">诊断</span>
              <h3>关键信号</h3>
              <ul class="text-list">
                <li v-for="item in briefingResult.diagnosis.key_signals" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section class="panel-card">
              <span class="eyebrow danger">风险</span>
              <h3>当前最该防的点</h3>
              <ul class="text-list danger-list">
                <li v-for="item in briefingResult.diagnosis.risks" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section class="panel-card">
              <span class="eyebrow success">机会</span>
              <h3>可以继续放大的优势</h3>
              <ul class="text-list success-list">
                <li v-for="item in briefingResult.diagnosis.opportunities" :key="item">{{ item }}</li>
              </ul>
            </section>
            <section class="panel-card">
              <span class="eyebrow">证据</span>
              <h3>决策证据</h3>
              <div class="evidence-grid">
                <div v-for="item in evidenceHighlights" :key="item.label" class="evidence-card">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                </div>
              </div>
            </section>
          </div>

          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="eyebrow">作战方案</span>
                <h3>{{ briefingResult.battle_plan.main_objective }}</h3>
              </div>
              <div class="chip-row">
                <span class="chip">{{ reviewPointLabel }}</span>
              </div>
            </div>
            <div class="plan-grid">
              <article class="sub-card">
                <strong>次级目标</strong>
                <ul class="text-list">
                  <li
                    v-for="item in briefingResult.battle_plan.secondary_objectives"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </article>
              <article class="sub-card">
                <strong>资源倾斜</strong>
                <ul class="allocation-list">
                  <li
                    v-for="item in briefingResult.battle_plan.resource_allocation"
                    :key="`${item.target}-${item.allocation_pct}`"
                  >
                    <div>
                      <b>{{ item.target }}</b>
                      <small>{{ item.reason }}</small>
                    </div>
                    <span>{{ item.allocation_pct }}%</span>
                  </li>
                </ul>
              </article>
              <article class="sub-card">
                <strong>关键任务</strong>
                <div
                  v-for="item in briefingResult.battle_plan.critical_tasks"
                  :key="item.task"
                  class="task-item"
                >
                  <b>{{ item.task }}</b>
                  <p>{{ item.focus }}</p>
                  <small>防错：{{ item.guardrail }}</small>
                </div>
              </article>
              <article class="sub-card">
                <strong>节奏与反模式</strong>
                <ul class="text-list">
                  <li
                    v-for="item in briefingResult.battle_plan.execution_rhythm"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
                <ul class="text-list danger-list">
                  <li
                    v-for="item in briefingResult.battle_plan.anti_patterns"
                    :key="item"
                  >
                    {{ item }}
                  </li>
                </ul>
              </article>
            </div>
          </section>

          <section class="panel-card">
            <div class="panel-head">
              <div>
                <span class="eyebrow">完整解读</span>
                <h3>保留完整长文，便于深读与回看</h3>
              </div>
            </div>
            <div class="segmented narrative-tabs">
              <button :class="['segmented-btn', narrativeTab === 'summary' && 'active']" @click="narrativeTab = 'summary'">整体简报</button>
              <button :class="['segmented-btn', narrativeTab === 'analysis' && 'active']" @click="narrativeTab = 'analysis'">诊断全文</button>
              <button :class="['segmented-btn', narrativeTab === 'plan' && 'active']" @click="narrativeTab = 'plan'">规划全文</button>
            </div>
            <div class="markdown-body briefing-markdown" v-html="narrativeHtml"></div>
          </section>
        </section>

        <section v-else class="panel-card empty-card">
          <div class="empty-body">
            <span class="empty-emoji">🧭</span>
            <h3>还没有生成作战简报</h3>
            <p>选定周期后生成一次，你会得到结构化诊断、风险机会判断和下一周期打法。</p>
          </div>
        </section>

        <section v-loading="historyLoading" class="panel-card">
          <div class="panel-head">
            <div>
              <span class="eyebrow">历史简报</span>
              <h3>按复盘记录回放你的策略演化</h3>
            </div>
            <div class="segmented small">
              <button
                v-for="item in historyTypeOptions"
                :key="item.value"
                :class="['segmented-btn', historyTypeValue === item.value && 'active']"
                @click="historyTypeValue = item.value"
              >
                {{ item.label }}
              </button>
            </div>
          </div>
          <div v-if="historyRows.length" class="history-grid">
            <button
              v-for="item in historyRows"
              :key="item.id"
              type="button"
              class="history-card"
              @click="handlePreview(item)"
            >
              <div class="history-top">
                <span class="status-pill" :class="`status-${item.statusLevel}`">{{ item.typeLabel }}</span>
                <small>{{ item.createdAt }}</small>
              </div>
              <strong>{{ item.coreJudgement }}</strong>
              <p>{{ item.period }}</p>
            </button>
          </div>
          <div v-else class="empty-history">暂无历史简报</div>
        </section>

        <el-dialog
          v-model="previewDialogVisible"
          :title="previewDialog.title"
          width="92%"
          destroy-on-close
          align-center
        >
          <div v-if="previewDialog.briefing">
            <div class="chip-row dialog-meta">
              <span class="chip">{{ previewDialog.briefing.meta.period_label }}</span>
              <span class="chip muted">{{ formatDateTime(previewDialog.briefing.meta.generated_at) }}</span>
            </div>
            <h3 class="dialog-title">
              {{ previewDialog.briefing.diagnosis.core_judgement }}
            </h3>
            <div
              class="markdown-body briefing-markdown"
              v-html="renderMarkdown(previewDialog.briefing.narrative?.full_markdown)"
            ></div>
          </div>
          <el-empty v-else description="暂无内容" />
        </el-dialog>
      </div>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import dayjs from "dayjs";
import { marked } from "marked";
import DOMPurify from "dompurify";
import PageContainer from "@/components/layout/PageContainer.vue";
import {
  useAIAssistantStore,
  type HistoryType,
  type Scope,
} from "@/stores/modules/aiAssistant";
import { useStageStore } from "@/stores/modules/stage";
import type { AIBriefingResult } from "@/api/modules/ai";

marked.setOptions({ breaks: true, gfm: true });

interface HistoryRow {
  id: number;
  raw: any;
  typeLabel: string;
  statusLevel: "green" | "yellow" | "red";
  coreJudgement: string;
  period: string;
  createdAt: string;
}

const scopeLabelMap: Record<Scope, string> = {
  day: "日度",
  week: "周度",
  month: "月度",
  stage: "阶段",
};

const statusLabelMap: Record<string, string> = {
  green: "状态良好",
  yellow: "需要纠偏",
  red: "高风险",
};

const aiStore = useAIAssistantStore();
const stageStore = useStageStore();
const narrativeTab = ref<"summary" | "analysis" | "plan">("summary");
const datePicker = ref();
const previewDialogVisible = ref(false);
const previewDialog = ref<{ title: string; briefing: AIBriefingResult | null }>({
  title: "",
  briefing: null,
});

const scopeOptions: Array<{ value: Scope; label: string }> = [
  { value: "day", label: "日度" },
  { value: "week", label: "周度" },
  { value: "month", label: "月度" },
  { value: "stage", label: "阶段" },
];

const historyTypeOptions: Array<{ value: HistoryType; label: string }> = [
  { value: "all", label: "全部" },
  { value: "briefing", label: "简报" },
  { value: "analysis", label: "诊断" },
  { value: "plan", label: "规划" },
];

const briefingResult = computed(() => aiStore.briefingResult);
const briefingLoading = computed(() => aiStore.briefingLoading);
const diagnosisRefreshing = computed(() => aiStore.diagnosisRefreshing);
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
  if (scopeValue.value === "day") return "选择具体日期";
  if (scopeValue.value === "week") return "选择所在周任意日期";
  if (scopeValue.value === "month") return "选择月份";
  return "";
});
const scopeLabel = computed(() => scopeLabelMap[scopeValue.value]);
const currentSelectionLabel = computed(() => {
  if (isStageScope.value) {
    const found = stageStore.stages.find((item: any) => Number(item.id) === Number(stageValue.value));
    return found ? found.name : "未选择阶段";
  }
  return dateValue.value || datePlaceholder.value;
});
const latestGeneratedLabel = computed(() =>
  briefingResult.value?.meta.generated_at ? formatDateTime(briefingResult.value.meta.generated_at) : "还未生成",
);
const latestPeriodLabel = computed(() => briefingResult.value?.meta.period_label || "等待生成第一份简报");
const statusTone = computed(() => briefingResult.value?.diagnosis.status_level || "yellow");
const statusLabel = computed(() => statusLabelMap[statusTone.value] || "需要判断");
const reviewPointLabel = computed(() => briefingResult.value?.battle_plan.next_review_point || "等待生成");
const stageOptions = computed(() =>
  stageStore.stages.map((item: any) => ({ label: item.name, value: Number(item.id) })),
);
const evidenceHighlights = computed(() => {
  const metrics = briefingResult.value?.evidence?.metrics || {};
  return [
    { label: "总时长", value: `${metrics.total_hours ?? "--"}h` },
    { label: "平均效率", value: `${metrics.average_efficiency ?? "--"}` },
    {
      label: "活跃率",
      value: metrics.active_ratio == null ? "--" : `${(Number(metrics.active_ratio) * 100).toFixed(1)}%`,
    },
    { label: "连击", value: `${metrics.streak_current ?? 0} 天` },
  ];
});
const narrativeHtml = computed(() => {
  const result = briefingResult.value?.narrative;
  if (!result) return "";
  if (narrativeTab.value === "analysis") return renderMarkdown(result.analysis_markdown);
  if (narrativeTab.value === "plan") return renderMarkdown(result.plan_markdown);
  return renderMarkdown(result.full_markdown);
});
const historyRows = computed<HistoryRow[]>(() =>
  (aiStore.historyItems || []).map((item: any) => ({
    id: item.id,
    raw: item,
    typeLabel:
      item.workflow_type === "briefing" ? "复盘简报" : item.insight_type === "plan" ? "规划" : "分析",
    statusLevel: (item.status_level || "yellow") as "green" | "yellow" | "red",
    coreJudgement: item.core_judgement || "历史记录",
    period: item.period_label || item.input_snapshot?.period_label || "未标记周期",
    createdAt: formatDateTime(item.created_at),
  })),
);

function renderMarkdown(text?: string) {
  if (!text) return "";
  return DOMPurify.sanitize(marked.parse(text) as string);
}

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

async function handleGenerateBriefing() {
  await aiStore.generateBriefing();
  narrativeTab.value = "summary";
}

async function handleRefreshDiagnosis() {
  await aiStore.refreshDiagnosisOnly();
  narrativeTab.value = "analysis";
}

function handleClear() {
  aiStore.clearResults();
}

function handlePreview(row: HistoryRow) {
  aiStore.hydrateFromHistory(row.raw);
  previewDialog.value = { title: row.typeLabel, briefing: aiStore.briefingResult };
  previewDialogVisible.value = true;
}

onMounted(async () => {
  await aiStore.init();
});
</script>

<style scoped lang="scss">
.briefing-shell { max-width: 1280px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; padding-bottom: 40px; }
.hero-card, .panel-card { border-radius: 28px; padding: 22px 24px; border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft)); background: linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02)), color-mix(in srgb, var(--surface-card) 92%, rgba(255,255,255,.02)); box-shadow: 0 24px 48px -36px rgba(15,23,42,.55), inset 0 1px 0 rgba(255,255,255,.04); }
.hero-card { display: flex; justify-content: space-between; gap: 20px; align-items: end; }
.eyebrow { font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--color-primary); }
.eyebrow.danger { color: #f87171; }
.eyebrow.success { color: #34d399; }
.hero-card h2, .panel-head h3, .overview-main h3 { color: var(--color-text-heading); }
.hero-card h2 { margin: 8px 0 10px; font-size: clamp(28px, 4vw, 42px); line-height: 1.08; }
.hero-card p, .overview-main p { margin: 0; color: var(--color-text-secondary); line-height: 1.7; }
.hero-actions, .chip-row { display: flex; flex-wrap: wrap; gap: 10px; }
.hero-btn, .segmented-btn { border: none; cursor: pointer; font-weight: 700; }
.hero-btn { border-radius: 999px; padding: 12px 18px; transition: transform .18s ease, opacity .2s ease; }
.hero-btn:not(:disabled):hover { transform: translateY(-1px); }
.hero-btn:disabled { opacity: .55; cursor: not-allowed; }
.hero-btn.primary { background: linear-gradient(135deg, #4f6df5, #7d5cff); color: #fff; }
.hero-btn.secondary { background: color-mix(in srgb, var(--color-primary) 16%, rgba(255,255,255,.03)); color: var(--color-text-heading); }
.hero-btn.ghost { background: color-mix(in srgb, var(--surface-card) 88%, rgba(255,255,255,.02)); color: var(--color-text-secondary); }
.panel-head { display: flex; justify-content: space-between; align-items: start; gap: 14px; margin-bottom: 18px; }
.panel-head h3 { margin: 6px 0 0; font-size: 22px; }
.chip { display: inline-flex; align-items: center; padding: 7px 12px; border-radius: 999px; background: color-mix(in srgb, var(--color-primary) 12%, rgba(255,255,255,.02)); color: var(--color-text-heading); font-size: 12px; font-weight: 700; }
.chip.muted { background: color-mix(in srgb, var(--surface-card) 82%, rgba(255,255,255,.02)); color: var(--color-text-secondary); }
.control-grid, .info-grid, .plan-grid, .history-grid { display: grid; gap: 16px; }
.control-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.info-grid, .plan-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.history-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.control-block { display: flex; flex-direction: column; gap: 12px; }
.control-block label { font-size: 13px; font-weight: 700; color: var(--color-text-secondary); }
.segmented { display: inline-flex; flex-wrap: wrap; gap: 6px; padding: 6px; border-radius: 16px; background: color-mix(in srgb, var(--surface-card) 82%, rgba(255,255,255,.02)); }
.segmented.small .segmented-btn { padding: 8px 12px; font-size: 12px; }
.segmented-btn { padding: 10px 16px; border-radius: 12px; background: transparent; color: var(--color-text-secondary); }
.segmented-btn.active { background: color-mix(in srgb, var(--color-primary) 18%, rgba(255,255,255,.04)); color: var(--color-text-heading); }
.picker-btn, .meta-box, .sub-card, .history-card, .evidence-card, .mini-stat { width: 100%; border-radius: 18px; background: color-mix(in srgb, var(--surface-card) 84%, rgba(255,255,255,.02)); border: 1px solid color-mix(in srgb, var(--color-primary) 8%, transparent); }
.picker-btn { min-height: 54px; padding: 14px 16px; text-align: left; color: var(--color-text-heading); }
.meta-box { min-height: 92px; padding: 14px 16px; display: flex; flex-direction: column; justify-content: center; gap: 6px; }
.meta-box strong { color: var(--color-text-heading); }
.meta-box span { color: var(--color-text-secondary); font-size: 13px; }
.stage-select { width: 100%; }
.stage-select :deep(.el-input__wrapper) { min-height: 54px; border-radius: 16px; background: color-mix(in srgb, var(--surface-card) 84%, rgba(255,255,255,.02)); box-shadow: none !important; }
:deep(.hidden-date-input) { position: absolute; opacity: 0; pointer-events: none; width: 1px; height: 1px; }
.battle-desk { display: flex; flex-direction: column; gap: 18px; }
.overview-card { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); gap: 16px; }
.overview-main h3 { margin: 12px 0 10px; font-size: 28px; line-height: 1.18; }
.overview-stats { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; }
.mini-stat, .evidence-card, .sub-card, .history-card { padding: 16px; }
.mini-stat span, .evidence-card span { display: block; color: var(--color-text-secondary); font-size: 12px; margin-bottom: 8px; }
.mini-stat strong, .evidence-card strong { color: var(--color-text-heading); }
.evidence-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.status-pill { display: inline-flex; align-items: center; padding: 7px 12px; border-radius: 999px; font-size: 12px; font-weight: 800; }
.status-green { background: rgba(52,211,153,.16); color: #6ee7b7; }
.status-yellow { background: rgba(251,191,36,.16); color: #fcd34d; }
.status-red { background: rgba(248,113,113,.16); color: #fca5a5; }
.text-list { margin: 14px 0 0; padding-left: 18px; display: grid; gap: 10px; color: var(--color-text-base); line-height: 1.7; }
.danger-list li { color: #fecaca; }
.success-list li { color: #bbf7d0; }
.allocation-list { list-style: none; margin: 14px 0 0; padding: 0; display: grid; gap: 12px; }
.allocation-list li { display: flex; justify-content: space-between; gap: 12px; padding-bottom: 12px; border-bottom: 1px solid color-mix(in srgb, var(--color-primary) 8%, transparent); }
.allocation-list b, .task-item b, .history-card strong { color: var(--color-text-heading); }
.allocation-list small, .task-item small, .history-card p, .empty-history, .empty-body p { color: var(--color-text-secondary); }
.allocation-list span { color: #a5b4fc; font-weight: 800; }
.task-item { padding: 14px 0; border-bottom: 1px solid color-mix(in srgb, var(--color-primary) 8%, transparent); }
.task-item p { margin: 8px 0 0; color: var(--color-text-base); line-height: 1.65; }
.history-card { border: none; text-align: left; cursor: pointer; }
.history-top { display: flex; justify-content: space-between; gap: 10px; align-items: center; }
.history-top small { color: var(--color-text-muted); }
.history-card strong { display: block; margin: 12px 0 10px; line-height: 1.55; }
.empty-card, .empty-history { min-height: 220px; display: flex; align-items: center; justify-content: center; }
.empty-body { text-align: center; color: var(--color-text-secondary); }
.empty-body h3 { color: var(--color-text-heading); }
.empty-emoji { font-size: 44px; display: block; margin-bottom: 12px; }
.dialog-meta { margin-bottom: 14px; }
.dialog-title { margin: 0 0 16px; color: var(--color-text-heading); font-size: 24px; }
:deep(.markdown-body) { color: var(--color-text-base); line-height: 1.8; }
:deep(.markdown-body h2), :deep(.markdown-body h3) { color: var(--color-text-heading); margin-top: 22px; }
:deep(.markdown-body code) { background: rgba(148,163,184,.14); padding: 2px 6px; border-radius: 6px; }
@media (max-width: 1024px) { .hero-card, .overview-card, .control-grid, .info-grid, .plan-grid, .history-grid { display: grid; grid-template-columns: 1fr; } .hero-card { align-items: start; } .overview-stats { grid-template-columns: 1fr; } }
@media (max-width: 720px) { .briefing-shell { gap: 16px; } .hero-card, .panel-card { padding: 18px; border-radius: 22px; } .hero-actions { justify-content: start; } .evidence-grid { grid-template-columns: 1fr; } }
</style>
