import { defineStore } from "pinia";
import { getDashboardSummary } from "@/api/modules/dashboard";

export const useDashboardStore = defineStore("dashboard", {
  state: () => ({
    loading: false,
    summary: {
      today_duration_minutes: 0,
      today_duration_formatted: "0m",
      total_records: 0,
      latest_record_date: null,
      next_countdown: null,
      countdown_total: 0,
      pending_todos: 0,
      milestones_count: 0,
      daily_plan: { completed: 0, total: 0 },
      random_motto: null,
    },
    lastFetched: 0,
  }),
  actions: {
    async fetch(force = false) {
      if (this.loading) return;
      if (!force && Date.now() - this.lastFetched < 30_000) return;
      this.loading = true;
      try {
        const response = (await getDashboardSummary()) as any;
        // 后端返回格式: { success: true, data: { ... } }
        if (response && response.success && response.data) {
          this.summary = response.data;
        }
        this.lastFetched = Date.now();
      } catch (e) {
        console.error("fetch dashboard summary failed", e);
      } finally {
        this.loading = false;
      }
    },
    // 别名，保持向后兼容
    async fetchSummary(force = false) {
      return this.fetch(force);
    },
  },
});
