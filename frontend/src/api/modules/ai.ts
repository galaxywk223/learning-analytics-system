import request from "@/utils/request";

export interface AIRequestPayload {
  scope: "day" | "week" | "month" | "stage";
  date?: string;
  stage_id?: number;
}

export interface AIDiagnosis {
  core_judgement: string;
  status_level: "green" | "yellow" | "red";
  key_signals: string[];
  risks: string[];
  opportunities: string[];
  strategy_bias: string;
  score?: number;
}

export interface AIResourceAllocationItem {
  target: string;
  allocation_pct: number;
  reason: string;
}

export interface AICriticalTaskItem {
  task: string;
  focus: string;
  guardrail: string;
}

export interface AIBattlePlan {
  main_objective: string;
  secondary_objectives: string[];
  resource_allocation: AIResourceAllocationItem[];
  critical_tasks: AICriticalTaskItem[];
  execution_rhythm: string[];
  anti_patterns: string[];
  next_review_point: string;
  budget_hours?: number;
}

export interface AIEvidence {
  scope?: string;
  stage_name?: string | null;
  period_label?: string;
  next_period_label?: string;
  metrics?: Record<string, any>;
  category_focus?: Array<Record<string, any>>;
  task_focus?: Array<Record<string, any>>;
  cadence?: Record<string, any>;
  countdown_context?: Record<string, any>;
}

export interface AINarrative {
  analysis_markdown?: string;
  plan_markdown?: string;
  full_markdown?: string;
}

export interface AIBriefingResult {
  insight_id?: number;
  meta: {
    scope: "day" | "week" | "month" | "stage";
    period_label: string;
    next_period_label: string;
    generated_at: string;
    stage_name?: string | null;
  };
  diagnosis: AIDiagnosis;
  battle_plan: AIBattlePlan;
  evidence: AIEvidence;
  narrative: AINarrative;
}

export interface AIHistoryParams {
  limit?: number;
  offset?: number;
  scope?: string;
  type?: "analysis" | "plan" | "briefing" | "all";
}

export const aiAPI = {
  createBriefing(data: AIRequestPayload) {
    return request({
      url: "/api/ai/briefing",
      method: "post",
      data,
      timeout: 120000,
    });
  },
  createAnalysis(data: AIRequestPayload) {
    return request({
      url: "/api/ai/analysis",
      method: "post",
      data,
      timeout: 120000,
    });
  },
  createPlan(data: AIRequestPayload) {
    return request({
      url: "/api/ai/plan",
      method: "post",
      data,
      timeout: 120000,
    });
  },
  fetchHistory(params: AIHistoryParams = {}) {
    return request({
      url: "/api/ai/history",
      method: "get",
      params,
    });
  },
};
