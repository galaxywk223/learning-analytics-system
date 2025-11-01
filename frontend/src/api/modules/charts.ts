/**
 * 图表相关 API 封装
 */
import request from "@/utils/request";

export const chartsAPI = {
  // view: 'weekly' | 'daily', stage_id: number | 'all'
  getOverview(params) {
    return request({ url: "/api/charts/overview", method: "get", params });
  },
  getCategories(params) {
    return request({ url: "/api/charts/categories", method: "get", params });
  },
  getStages() {
    return request({ url: "/api/charts/stages", method: "get" });
  },
  exportCharts() {
    return request({
      url: "/api/charts/export",
      method: "get",
      responseType: "blob",
    });
  },
};
