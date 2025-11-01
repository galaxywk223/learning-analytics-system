/**
 * 仪表盘汇总 API
 */
import request from "@/utils/request";

export const dashboardAPI = {
  summary() {
    return request({ url: "/api/users/dashboard/summary", method: "get" });
  },
};

// 向后兼容的具名导出
export const getDashboardSummary = dashboardAPI.summary;
