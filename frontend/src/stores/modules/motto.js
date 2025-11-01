import { defineStore } from "pinia";
import {
  listMottos,
  createMotto,
  updateMotto,
  deleteMotto,
} from "@/api/modules/motto";

export const useMottoStore = defineStore("motto", {
  state: () => ({
    loading: false,
    items: [],
  }),
  actions: {
    async fetch() {
      if (this.loading) return;
      this.loading = true;
      try {
        const resp = await listMottos();
        // 后端返回 { success, mottos: [] }
        this.items = Array.isArray(resp?.mottos) ? resp.mottos : [];
      } catch (e) {
        console.error("fetch mottos failed", e);
        this.items = [];
        throw e; // 允许上层知晓失败
      } finally {
        this.loading = false;
      }
    },
    async add(payload) {
      const resp = await createMotto(payload); // { success, motto: {...} }
      if (!resp?.success || !resp?.motto) {
        throw new Error("create motto failed");
      }
      this.items.push(resp.motto);
      return resp.motto;
    },
    async save(id, payload) {
      const resp = await updateMotto(id, payload); // { success, motto: {...} }
      if (!resp?.success || !resp?.motto) {
        throw new Error("update motto failed");
      }
      const idx = this.items.findIndex((i) => i.id === id);
      if (idx !== -1) this.items[idx] = resp.motto;
      return resp.motto;
    },
    async remove(id) {
      const resp = await deleteMotto(id); // { success }
      if (!resp?.success) {
        throw new Error("delete motto failed");
      }
      this.items = this.items.filter((i) => i.id !== id);
    },
  },
});
