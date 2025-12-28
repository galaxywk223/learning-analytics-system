import { defineStore } from "pinia";
import request from "@/utils/request";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    activeStageId: Number(localStorage.getItem("ll_active_stage_id") || 0),
    layout: {
      // 默认折叠侧边栏，仅在用户明确设为 "0" 时展开
      sidebarCollapsed: localStorage.getItem("ll_sidebar_collapsed") !== "0",
    },
  }),
  actions: {
    async fetchSettings() {
      try {
        // 未登录（无 token）时不请求受保护接口，避免 401 重定向闪烁
        const token = localStorage.getItem("access_token");
        if (!token) {
          return; // 可选择触发一个默认设置加载逻辑
        }
        const settings = (await request({
          url: "/api/users/settings",
          method: "get",
        })) as any;
        if (settings) {
          if (settings.active_stage_id) {
            this.activeStageId = settings.active_stage_id;
            localStorage.setItem(
              "ll_active_stage_id",
              String(settings.active_stage_id),
            );
          }
        }
      } catch (error) {
        console.error("获取用户设置失败:", error);
      }
    },
    async saveSettings() {
      try {
        const token = localStorage.getItem("access_token");
        if (!token) {
          // 未登录状态下只在本地存储，不向后端提交
          return;
        }
        await request({
          url: "/api/users/settings",
          method: "post",
          data: {
            active_stage_id: this.activeStageId,
          },
        });
      } catch (error) {
        console.error("保存用户设置失败:", error);
        throw error;
      }
    },
    setActiveStage(stageId) {
      this.activeStageId = stageId;
      localStorage.setItem("ll_active_stage_id", String(stageId || 0));
      this.saveSettings();
    },
    setSidebarCollapsed(collapsed) {
      this.layout.sidebarCollapsed = collapsed;
      localStorage.setItem("ll_sidebar_collapsed", collapsed ? "1" : "0");
    },
  },
});
