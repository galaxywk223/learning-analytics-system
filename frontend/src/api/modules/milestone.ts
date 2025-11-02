/**
 * 里程碑与附件 API
 */
import request from "@/utils/request";

export const milestoneAPI = {
  list(params: any = {}) {
    return request({ url: "/api/milestones", method: "get", params });
  },
  get(id) {
    return request({ url: `/api/milestones/${id}`, method: "get" });
  },
  create(data) {
    return request({ url: "/api/milestones", method: "post", data });
  },
  update(id, data) {
    return request({ url: `/api/milestones/${id}`, method: "put", data });
  },
  remove(id) {
    return request({ url: `/api/milestones/${id}`, method: "delete" });
  },
  categories() {
    return request({ url: "/api/milestones/categories", method: "get" });
  },
  createCategory(data) {
    return request({ url: "/api/milestones/categories", method: "post", data });
  },
  updateCategory(id, data) {
    return request({
      url: `/api/milestones/categories/${id}`,
      method: "put",
      data,
    });
  },
  deleteCategory(id) {
    return request({
      url: `/api/milestones/categories/${id}`,
      method: "delete",
    });
  },
  uploadAttachment(milestoneId, file) {
    const form = new FormData();
    form.append("file", file);
    return request({
      url: `/api/milestones/${milestoneId}/attachments`,
      method: "post",
      data: form,
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  deleteAttachment(milestoneId, attachmentId) {
    return request({
      url: `/api/milestones/${milestoneId}/attachments/${attachmentId}`,
      method: "delete",
    });
  },
};

// 向后兼容的具名导出
export const listMilestones = milestoneAPI.list;
export const createMilestone = milestoneAPI.create;
export const updateMilestone = milestoneAPI.update;
export const deleteMilestone = milestoneAPI.remove;
