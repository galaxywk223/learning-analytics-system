import { defineStore } from "pinia";
import {
  listCountdowns,
  createCountdown,
  updateCountdown,
  deleteCountdown,
} from "@/api/modules/countdown";
import dayjs from "dayjs";

// 将本地北京日期+时间转换为 UTC ISO 字符串
function toUtcIso(dateStr, timeStr) {
  const [y, m, d] = dateStr.split("-").map(Number);
  const [hh, mm] = (timeStr || "00:00").split(":").map(Number);
  // 构造北京时 (UTC+8) 然后减去8小时得UTC
  const local = dayjs
    .utc()
    .year(y)
    .month(m - 1)
    .date(d)
    .hour(hh)
    .minute(mm)
    .second(0)
    .millisecond(0);
  // local 此时是 UTC 基准，需要加回8小时? dayjs.utc().year(...). 等价于构造UTC时间。我们希望: 北京 2025-01-01 10:00 => UTC 2025-01-01 02:00
  // 直接用 Date 计算更直观
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
        const data = await listCountdowns();
        this.items = data || [];
        this.lastFetched = Date.now();
      } catch (e) {
        console.error("fetch countdown failed", e);
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
      const item = await createCountdown({
        title: payload.title,
        target_datetime_utc,
      });
      if (item) this.items.unshift(item); // 新项前置
    },
    async save(id, payload) {
      const target_datetime_utc = toUtcIso(
        payload.target_date,
        payload.target_time
      );
      const updated = await updateCountdown(id, {
        title: payload.title,
        target_datetime_utc,
      });
      const idx = this.items.findIndex((i) => i.id === id);
      if (idx !== -1) this.items[idx] = updated;
    },
    async remove(id) {
      await deleteCountdown(id);
      this.items = this.items.filter((i) => i.id !== id);
    },
  },
});
