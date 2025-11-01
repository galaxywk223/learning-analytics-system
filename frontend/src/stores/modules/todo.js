import { defineStore } from "pinia";
import {
  listTodos,
  createTodo,
  updateTodo,
  deleteTodo,
} from "@/api/modules/todo";

export const useTodoStore = defineStore("todo", {
  state: () => ({
    loading: false,
    items: [],
  }),
  getters: {
    pending: (state) => state.items.filter((i) => !i.completed),
    completed: (state) => state.items.filter((i) => i.completed),
  },
  actions: {
    async fetch() {
      if (this.loading) return;
      this.loading = true;
      try {
        this.items = (await listTodos()) || [];
      } catch (e) {
        console.error("fetch todos failed", e);
      } finally {
        this.loading = false;
      }
    },
    async add(payload) {
      const item = await createTodo(payload);
      this.items.push(item);
    },
    async save(id, payload) {
      const updated = await updateTodo(id, payload);
      const idx = this.items.findIndex((i) => i.id === id);
      if (idx !== -1) this.items[idx] = updated;
    },
    async remove(id) {
      await deleteTodo(id);
      this.items = this.items.filter((i) => i.id !== id);
    },
  },
});
