import { defineStore } from "pinia";
import {
  listCountdowns,
  createCountdown,
  updateCountdown,
  deleteCountdown,
} from "@/api/modules/countdown";

// 将本地北京日期+时间转换为 UTC ISO 字符串
function toUtcIso(dateStr: string, timeStr?: string): string {
  const [y, m, d] = dateStr.split("-").map(Number);
  const [hh, mm] = (timeStr || "00:00").split(":").map(Number);
  // 构造北京时间 (UTC+8)，然后转为 UTC
  // 北京 2025-01-01 10:00 => UTC 2025-01-01 02:00
  const dt = new Date(Date.UTC(y, m - 1, d, hh - 8, mm, 0));
  return dt.toISOString();
}

export const useCountdownStore = defineStore("countdown", {
  state: () => ({
    loading: false,
    items: [],
    lastFetched: 0,
  }),
  getters: {
    active: (state) => state.items.filter((i) => !i.is_expired),
    expired: (state) => state.items.filter((i) => i.is_expired),
  },
  actions: {
    async fetch(force = false) {
      if (this.loading) return;
      if (!force && Date.now() - this.lastFetched < 60_000) return;
      this.loading = true;
      try {
        const resp = await listCountdowns();
        // 后端返回 { success, countdowns: [] }
        this.items = Array.isArray(resp?.countdowns) ? resp.countdowns : [];
        this.lastFetched = Date.now();
      } catch (e) {
        console.error("fetch countdown failed", e);
        this.items = [];
      } finally {
        this.loading = false;
      }
    },
    async add(payload) {
      // payload: { title, target_date, target_time }
      const target_datetime_utc = toUtcIso(
        payload.target_date,
        payload.target_time
      );
      const resp = await createCountdown({
        title: payload.title,
        target_datetime_utc,
      });
      // 后端返回 { success, countdown: {...} }
      if (resp?.success && resp?.countdown) {
        this.items.unshift(resp.countdown); // 新项前置
        return resp.countdown;
      }
    },
    async save(id, payload) {
      const target_datetime_utc = toUtcIso(
        payload.target_date,
        payload.target_time
      );
      const resp = await updateCountdown(id, {
        title: payload.title,
        target_datetime_utc,
      });
      // 后端返回 { success, countdown: {...} }
      if (resp?.success && resp?.countdown) {
        const idx = this.items.findIndex((i) => i.id === id);
        if (idx !== -1) this.items[idx] = resp.countdown;
        return resp.countdown;
      }
    },
    async remove(id) {
      const resp = await deleteCountdown(id);
      // 后端返回 { success }
      if (resp?.success) {
        this.items = this.items.filter((i) => i.id !== id);
      }
    },
  },
});
