/**
 * 座右铭 API
 */
import request from "@/utils/request";

export const mottoAPI = {
  list() {
    return request({ url: "/api/mottos", method: "get" });
  },
  get(id) {
    return request({ url: `/api/mottos/${id}`, method: "get" });
  },
  random() {
    return request({ url: "/api/mottos/random", method: "get" });
  },
  create(data) {
    return request({ url: "/api/mottos", method: "post", data });
  },
  update(id, data) {
    return request({ url: `/api/mottos/${id}`, method: "put", data });
  },
  remove(id) {
    return request({ url: `/api/mottos/${id}`, method: "delete" });
  },
};

// 向后兼容的具名导出
export const listMottos = mottoAPI.list;
export const createMotto = mottoAPI.create;
export const updateMotto = mottoAPI.update;
export const deleteMotto = mottoAPI.remove;
