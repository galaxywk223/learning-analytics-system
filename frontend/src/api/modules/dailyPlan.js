/**
 * 每日计划 API
 */
import request from "@/utils/request";

export const dailyPlanAPI = {
  list(params) {
    return request({ url: "/api/daily-plans", method: "get", params });
  },
  create(data) {
    return request({ url: "/api/daily-plans", method: "post", data });
  },
  update(id, data) {
    return request({ url: `/api/daily-plans/${id}`, method: "put", data });
  },
  toggle(id) {
    return request({ url: `/api/daily-plans/${id}/toggle`, method: "post" });
  },
  remove(id) {
    return request({ url: `/api/daily-plans/${id}`, method: "delete" });
  },
};

// 向后兼容的具名导出
export const getDailyPlan = dailyPlanAPI.list;
export const saveDailyPlan = dailyPlanAPI.create;
