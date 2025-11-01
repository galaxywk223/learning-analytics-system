import { defineStore } from "pinia";
import { recordAPI } from "@/api/modules/records";
import { useSettingsStore } from "@/stores/modules/settings";

export const useRecordsStore = defineStore("records", {
  state: () => ({
    loading: false,
    weeks: [], // [{ week_start, week_end, total_duration, efficiency, days:[{date, entries:[], day_duration}]}]
    lastFetched: 0,
  }),
  getters: {
    totalDuration: (state) =>
      state.weeks.reduce((sum, w) => sum + (w.total_duration || 0), 0),
    averageEfficiency: (state) => {
      const effs = state.weeks
        .map((w) => w.efficiency)
        .filter((e) => typeof e === "number");
      if (!effs.length) return 0;
      return (effs.reduce((a, b) => a + b, 0) / effs.length).toFixed(2);
    },
  },
  actions: {
    async fetch(force = false) {
      if (this.loading) return;
      if (!force && Date.now() - this.lastFetched < 60_000) return; // cache 1min
      this.loading = true;
      try {
        const settingsStore = useSettingsStore();
        if (!settingsStore.activeStageId) {
          // 没有激活阶段则不请求，保持 weeks 不变
          return;
        }
        const data = await recordAPI.getStructuredRecords({
          stage_id: settingsStore.activeStageId,
        });
        this.weeks = data.weeks || [];
        this.lastFetched = Date.now();
      } catch (e) {
        console.error("fetch structured records failed", e);
      } finally {
        this.loading = false;
      }
    },
  },
});
