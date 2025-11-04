import request from "@/utils/request";

export interface AIRequestPayload {
  scope: "day" | "week" | "month" | "stage";
  date?: string;
  stage_id?: number;
}

export interface AIHistoryParams {
  limit?: number;
  offset?: number;
  scope?: string;
  type?: "analysis" | "plan" | "all";
}

export const aiAPI = {
  createAnalysis(data: AIRequestPayload) {
    return request({
      url: "/api/ai/analysis",
      method: "post",
      data,
      timeout: 60000,
    });
  },
  createPlan(data: AIRequestPayload) {
    return request({
      url: "/api/ai/plan",
      method: "post",
      data,
      timeout: 60000,
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
