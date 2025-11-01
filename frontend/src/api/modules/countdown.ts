/**
 * 倒计时事件 API
 */
import request from "@/utils/request";

export const countdownAPI = {
  list() {
    return request({ url: "/api/countdowns", method: "get" });
  },
  get(id) {
    return request({ url: `/api/countdowns/${id}`, method: "get" });
  },
  create(data) {
    return request({ url: "/api/countdowns", method: "post", data });
  },
  update(id, data) {
    return request({ url: `/api/countdowns/${id}`, method: "put", data });
  },
  remove(id) {
    return request({ url: `/api/countdowns/${id}`, method: "delete" });
  },
};

// 向后兼容的具名导出
export const listCountdowns = countdownAPI.list;
export const createCountdown = countdownAPI.create;
export const updateCountdown = countdownAPI.update;
export const deleteCountdown = countdownAPI.remove;
