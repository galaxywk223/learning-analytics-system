import { defineStore } from "pinia";
import {
  listMilestones,
  createMilestone,
  updateMilestone,
  deleteMilestone,
} from "@/api/modules/milestone";

export const useMilestoneStore = defineStore("milestone", {
  state: () => ({
    loading: false,
    items: [],
  }),
  actions: {
    async fetch() {
      if (this.loading) return;
      this.loading = true;
      try {
        this.items = (await listMilestones()) || [];
      } catch (e) {
        console.error("fetch milestones failed", e);
      } finally {
        this.loading = false;
      }
    },
    async add(payload) {
      const item = await createMilestone(payload);
      this.items.push(item);
    },
    async save(id, payload) {
      const updated = await updateMilestone(id, payload);
      const idx = this.items.findIndex((i) => i.id === id);
      if (idx !== -1) this.items[idx] = updated;
    },
    async remove(id) {
      await deleteMilestone(id);
      this.items = this.items.filter((i) => i.id !== id);
    },
  },
});
