/**
 * 阶段相关API
 */
import request from "@/utils/request";

export const stageAPI = {
  // 获取所有阶段
  getAll() {
    return request({
      url: "/api/stages",
      method: "get",
    });
  },

  // 获取单个阶段
  getById(id) {
    return request({
      url: `/api/stages/${id}`,
      method: "get",
    });
  },

  // 创建阶段
  create(data) {
    return request({
      url: "/api/stages",
      method: "post",
      data,
    });
  },

  // 更新阶段
  update(id, data) {
    return request({
      url: `/api/stages/${id}`,
      method: "put",
      data,
    });
  },

  // 删除阶段
  delete(id) {
    return request({
      url: `/api/stages/${id}`,
      method: "delete",
    });
  },
};
