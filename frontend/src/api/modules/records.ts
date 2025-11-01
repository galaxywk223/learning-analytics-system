/**
 * 学习记录相关API
 */
import request from "@/utils/request";

export const recordApi = {
  // 获取记录列表
  getRecords(params) {
    return request({
      url: "/api/records",
      method: "get",
      params,
    });
  },

  // 获取单条记录
  getRecord(id) {
    return request({
      url: `/api/records/${id}`,
      method: "get",
    });
  },

  // 创建记录
  createRecord(data) {
    return request({
      url: "/api/records",
      method: "post",
      data,
    });
  },

  // 更新记录
  updateRecord(id, data) {
    return request({
      url: `/api/records/${id}`,
      method: "put",
      data,
    });
  },

  // 删除记录
  deleteRecord(id) {
    return request({
      url: `/api/records/${id}`,
      method: "delete",
    });
  },

  // 获取统计数据
  getStatistics(params) {
    return request({
      url: "/api/records/statistics",
      method: "get",
      params,
    });
  },

  // 导出数据
  exportData() {
    return request({
      url: "/api/records/export",
      method: "get",
      responseType: "blob",
    });
  },

  // 导入数据
  importData(file) {
    const formData = new FormData();
    formData.append("file", file);
    return request({
      url: "/api/records/import",
      method: "post",
      data: formData,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },

  // 清空所有数据
  clearAllData(confirm = false) {
    return request({
      url: "/api/records/clear-all",
      method: "post",
      data: { confirm },
    });
  },

  // 获取结构化记录数据
  getStructuredRecords(params) {
    return request({
      url: "/api/records/structured",
      method: "get",
      params,
    });
  },
};

// 保持向后兼容
export const recordAPI = recordApi;
