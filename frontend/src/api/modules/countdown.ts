/**
 * 倒计时事件 API
 */
import request from "@/utils/request";
import type { Countdown } from "@/types";

interface CountdownListResponse {
  success: boolean;
  countdowns: Countdown[];
}

interface CountdownResponse {
  success: boolean;
  countdown: Countdown;
}

interface CountdownDeleteResponse {
  success: boolean;
  message: string;
}

export const countdownAPI = {
  list(): Promise<CountdownListResponse> {
    return request({ url: "/api/countdowns", method: "get" });
  },
  get(id: number): Promise<CountdownResponse> {
    return request({ url: `/api/countdowns/${id}`, method: "get" });
  },
  create(data: any): Promise<CountdownResponse> {
    return request({ url: "/api/countdowns", method: "post", data });
  },
  update(id: number, data: any): Promise<CountdownResponse> {
    return request({ url: `/api/countdowns/${id}`, method: "put", data });
  },
  remove(id: number): Promise<CountdownDeleteResponse> {
    return request({ url: `/api/countdowns/${id}`, method: "delete" });
  },
};

// 向后兼容的具名导出
export const listCountdowns = countdownAPI.list;
export const createCountdown = countdownAPI.create;
export const updateCountdown = countdownAPI.update;
export const deleteCountdown = countdownAPI.remove;
