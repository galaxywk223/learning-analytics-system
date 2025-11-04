import { defineStore } from "pinia";
import { ref } from "vue";
import dayjs from "dayjs";
import { ElMessage } from "element-plus";

import { aiAPI, type AIRequestPayload } from "@/api/modules/ai";
import { useStageStore } from "./stage";

export type Scope = "day" | "week" | "month" | "stage";
export type HistoryType = "analysis" | "plan" | "all";

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

  const analysisResult = ref<any | null>(null);
  const planResult = ref<any | null>(null);

  const analysisLoading = ref(false);
  const planLoading = ref(false);
  const historyLoading = ref(false);

  const historyItems = ref<any[]>([]);
  const historyType = ref<HistoryType>("all");

  const stageStore = useStageStore();

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
    void fetchHistory(next);
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

  async function generateAnalysis() {
    try {
      const payload = buildPayload();
      analysisLoading.value = true;
      const response: any = await aiAPI.createAnalysis(payload);
      if (response?.success) {
        analysisResult.value = response.data;
        ElMessage.success("分析总结已生成");
        await fetchHistory(scope.value);
      } else {
        throw new Error(response?.message || "生成分析失败");
      }
    } catch (error: any) {
      ElMessage.error(error.message || "生成分析失败");
    } finally {
      analysisLoading.value = false;
    }
  }

  async function generatePlan() {
    try {
      const payload = buildPayload();
      planLoading.value = true;
      const response: any = await aiAPI.createPlan(payload);
      if (response?.success) {
        planResult.value = response.data;
        ElMessage.success("规划方案已生成");
        await fetchHistory(scope.value);
      } else {
        throw new Error(response?.message || "生成规划失败");
      }
    } catch (error: any) {
      ElMessage.error(error.message || "生成规划失败");
    } finally {
      planLoading.value = false;
    }
  }

  async function fetchHistory(scopeFilter?: Scope) {
    try {
      historyLoading.value = true;
      const params: Record<string, any> = {
        limit: HISTORY_LIMIT,
      };
      if (scopeFilter) {
        params.scope = scopeFilter;
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
    await fetchHistory(scope.value);
  }

  function clearResults() {
    analysisResult.value = null;
    planResult.value = null;
  }

  return {
    scope,
    selectedDate,
    selectedStageId,
    analysisResult,
    planResult,
    analysisLoading,
    planLoading,
    historyItems,
    historyLoading,
    historyType,
    init,
    setScope,
    setDate,
    setStage,
    generateAnalysis,
    generatePlan,
    fetchHistory,
    setHistoryType,
    clearResults,
  };
});
