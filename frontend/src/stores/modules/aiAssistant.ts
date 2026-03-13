import { defineStore } from "pinia";
import { computed, ref } from "vue";
import dayjs from "dayjs";
import { ElMessage } from "element-plus";

import {
  aiAPI,
  type AIBriefingResult,
  type AIRequestPayload,
} from "@/api/modules/ai";
import { useStageStore } from "./stage";

export type Scope = "day" | "week" | "month" | "stage";
export type HistoryType = "analysis" | "plan" | "briefing" | "all";

const HISTORY_LIMIT = 30;

function formatDate(value: dayjs.Dayjs) {
  return value.format("YYYY-MM-DD");
}

function resolveWeekStart(value: dayjs.Dayjs) {
  const weekday = value.day();
  const diff = (weekday + 6) % 7;
  return value.subtract(diff, "day");
}

export const useAIAssistantStore = defineStore("ai-assistant", () => {
  const scope = ref<Scope>("week");
  const selectedDate = ref<string>(formatDate(dayjs()));
  const selectedStageId = ref<number | null>(null);

  const briefingResult = ref<AIBriefingResult | null>(null);
  const briefingLoading = ref(false);
  const diagnosisRefreshing = ref(false);
  const historyLoading = ref(false);
  const historyItems = ref<any[]>([]);
  const historyType = ref<HistoryType>("all");

  const stageStore = useStageStore();

  const analysisResult = computed(() => {
    if (!briefingResult.value) return null;
    return {
      text: briefingResult.value.narrative?.analysis_markdown || "",
      generated_at: briefingResult.value.meta.generated_at,
      period_label: briefingResult.value.meta.period_label,
    };
  });

  const planResult = computed(() => {
    if (!briefingResult.value) return null;
    return {
      text: briefingResult.value.narrative?.plan_markdown || "",
      generated_at: briefingResult.value.meta.generated_at,
      period_label: briefingResult.value.meta.period_label,
      next_period_label: briefingResult.value.meta.next_period_label,
    };
  });

  async function init() {
    await stageStore.ensureStages();
    if (stageStore.activeStage) {
      selectedStageId.value = Number(stageStore.activeStage.id);
    } else if (stageStore.stages.length) {
      selectedStageId.value = Number(stageStore.stages[0].id);
    }
    await fetchHistory();
  }

  function setScope(next: Scope) {
    scope.value = next;
    if (next === "stage" && !selectedStageId.value && stageStore.stages.length) {
      selectedStageId.value = Number(stageStore.stages[0].id);
    }
    if (next !== "stage") {
      selectedDate.value = formatDate(dayjs());
    }
  }

  function setDate(value: string) {
    selectedDate.value = value;
  }

  function setStage(stageId: number | null) {
    selectedStageId.value = stageId;
  }

  function buildPayload(): AIRequestPayload {
    const payload: AIRequestPayload = {
      scope: scope.value,
    };
    if (scope.value === "stage") {
      if (!selectedStageId.value) {
        throw new Error("请选择阶段");
      }
      payload.stage_id = selectedStageId.value;
    } else {
      const baseDate = dayjs(selectedDate.value || dayjs());
      if (!baseDate.isValid()) {
        throw new Error("请选择有效日期");
      }
      if (scope.value === "day") {
        payload.date = formatDate(baseDate);
      } else if (scope.value === "week") {
        payload.date = formatDate(resolveWeekStart(baseDate));
      } else if (scope.value === "month") {
        payload.date = formatDate(baseDate.startOf("month"));
      }
    }
    return payload;
  }

  async function generateBriefing() {
    try {
      const payload = buildPayload();
      briefingLoading.value = true;
      const response: any = await aiAPI.createBriefing(payload);
      if (response?.success) {
        briefingResult.value = response.data;
        ElMessage.success("复盘作战台已生成");
        await fetchHistory();
      } else {
        throw new Error(response?.message || "生成复盘作战台失败");
      }
    } catch (error: any) {
      ElMessage.error(error.message || "生成复盘作战台失败");
    } finally {
      briefingLoading.value = false;
    }
  }

  async function refreshDiagnosisOnly() {
    try {
      const payload = buildPayload();
      diagnosisRefreshing.value = true;
      const response: any = await aiAPI.createAnalysis(payload);
      if (!response?.success || !response?.data?.briefing) {
        throw new Error(response?.message || "刷新诊断失败");
      }
      const current = briefingResult.value;
      briefingResult.value = {
        ...(current || response.data.briefing),
        ...response.data.briefing,
        battle_plan: current?.battle_plan || response.data.briefing.battle_plan,
      };
      ElMessage.success("诊断已刷新");
      await fetchHistory();
    } catch (error: any) {
      ElMessage.error(error.message || "刷新诊断失败");
    } finally {
      diagnosisRefreshing.value = false;
    }
  }

  async function fetchHistory(scopeFilter?: Scope) {
    try {
      historyLoading.value = true;
      const params: Record<string, any> = { limit: HISTORY_LIMIT };
      if (scopeFilter || scope.value) {
        params.scope = scopeFilter || scope.value;
      }
      if (historyType.value !== "all") {
        params.type = historyType.value;
      }
      const response: any = await aiAPI.fetchHistory(params);
      if (response?.success) {
        historyItems.value = Array.isArray(response.data) ? response.data : [];
      }
    } catch (error) {
      console.error("获取 AI 历史记录失败:", error);
    } finally {
      historyLoading.value = false;
    }
  }

  async function setHistoryType(next: HistoryType) {
    historyType.value = next;
    await fetchHistory();
  }

  function hydrateFromHistory(item: any) {
    const snapshot = item?.input_snapshot || {};
    const diagnosis = snapshot?.diagnosis;
    const battlePlan = snapshot?.battle_plan;
    const evidence = snapshot?.evidence;
    const narrative = snapshot?.narrative;
    if (!diagnosis || !battlePlan) {
      briefingResult.value = {
        insight_id: item.id,
        meta: {
          scope: (item.scope || snapshot.scope || "week") as Scope,
          period_label: item.period_label || snapshot.period_label || "",
          next_period_label:
            item.next_period_label || snapshot.next_period_label || "",
          generated_at: item.created_at || "",
          stage_name: snapshot.stage || null,
        },
        diagnosis: {
          core_judgement: item.core_judgement || "历史记录仅包含旧版长文结果",
          status_level: (item.status_level || "yellow") as
            | "green"
            | "yellow"
            | "red",
          key_signals: ["该历史记录生成于旧版智能规划，尚未包含结构化诊断卡。"],
          risks: [],
          opportunities: [],
          strategy_bias: "建议重新生成一份新版复盘作战台，以获得结构化判断。",
        },
        battle_plan: {
          main_objective: "该历史记录没有结构化作战方案",
          secondary_objectives: [],
          resource_allocation: [],
          critical_tasks: [],
          execution_rhythm: [],
          anti_patterns: [],
          next_review_point: "重新生成新版简报后可获得完整作战方案",
        },
        evidence: {},
        narrative: {
          analysis_markdown: item.output_text || "",
          plan_markdown: item.output_text || "",
          full_markdown: item.output_text || "",
        },
      };
      return;
    }
    briefingResult.value = {
      insight_id: item.id,
      meta: {
        scope: (item.scope || snapshot.scope || "week") as Scope,
        period_label: item.period_label || snapshot.period_label || "",
        next_period_label:
          item.next_period_label || snapshot.next_period_label || "",
        generated_at: item.created_at || "",
        stage_name: snapshot.stage || null,
      },
      diagnosis,
      battle_plan: battlePlan,
      evidence: evidence || {},
      narrative:
        narrative || {
          analysis_markdown: item.output_text || "",
          plan_markdown: item.output_text || "",
          full_markdown: item.output_text || "",
        },
    };
  }

  function clearResults() {
    briefingResult.value = null;
  }

  return {
    scope,
    selectedDate,
    selectedStageId,
    briefingResult,
    analysisResult,
    planResult,
    briefingLoading,
    diagnosisRefreshing,
    historyItems,
    historyLoading,
    historyType,
    init,
    setScope,
    setDate,
    setStage,
    generateBriefing,
    refreshDiagnosisOnly,
    fetchHistory,
    setHistoryType,
    hydrateFromHistory,
    clearResults,
  };
});
