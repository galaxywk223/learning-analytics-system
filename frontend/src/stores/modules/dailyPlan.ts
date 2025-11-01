import { defineStore } from "pinia";
import { getDailyPlan, saveDailyPlan } from "@/api/modules/dailyPlan";

export const useDailyPlanStore = defineStore("dailyPlan", {
  state: () => ({
    loading: false,
    plan: null,
    lastFetched: 0,
  }),
  actions: {
    async fetch(dateStr, force = false) {
      if (this.loading) return;
      if (!force && Date.now() - this.lastFetched < 30_000) return;
      this.loading = true;
      try {
        this.plan = await getDailyPlan(dateStr);
        this.lastFetched = Date.now();
      } catch (e) {
        console.error("fetch daily plan failed", e);
      } finally {
        this.loading = false;
      }
    },
    async save(payload) {
      const updated = await saveDailyPlan(payload);
      this.plan = updated;
    },
  },
});
