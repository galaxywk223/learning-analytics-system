/**
 * 图表与词云相关 API 封装
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
  // 后端生成图片
  getWordcloud(params) {
    return request({
      url: "/api/charts/wordcloud",
      method: "get",
      params,
      responseType: "blob",
    });
  },
  getWordcloudOptions() {
    return request({ url: "/api/charts/wordcloud/options", method: "get" });
  },
  exportCharts() {
    return request({
      url: "/api/charts/export",
      method: "get",
      responseType: "blob",
    });
  },
};
