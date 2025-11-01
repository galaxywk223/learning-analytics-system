import { defineStore } from "pinia";
import request from "@/utils/request";

export const useSettingsStore = defineStore("settings", {
  state: () => ({
    theme: localStorage.getItem("ll_theme") || "palette-purple",
    // pendingTheme: 临时选择但尚未保存到后端的主题
    pendingTheme: localStorage.getItem("ll_theme") || "palette-purple",
    backgroundImage: localStorage.getItem("ll_background") || "",
    activeStageId: Number(localStorage.getItem("ll_active_stage_id") || 0),
    layout: {
      sidebarCollapsed: localStorage.getItem("ll_sidebar_collapsed") === "1",
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
        const settings = await request({
          url: "/api/users/settings",
          method: "get",
        });
        if (settings) {
          if (settings.theme) {
            this.theme = settings.theme;
            this.pendingTheme = settings.theme; // 保持与已保存主题同步
            localStorage.setItem("ll_theme", settings.theme);
          }
          if (settings.background_image) {
            this.backgroundImage = settings.background_image;
            localStorage.setItem("ll_background", settings.background_image);
          }
          if (settings.active_stage_id) {
            this.activeStageId = settings.active_stage_id;
            localStorage.setItem(
              "ll_active_stage_id",
              String(settings.active_stage_id)
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
            theme: this.theme,
            background_image: this.backgroundImage,
            active_stage_id: this.activeStageId,
          },
        });
      } catch (error) {
        console.error("保存用户设置失败:", error);
        throw error;
      }
    },
    // 仅修改待提交主题，不立即保存
    setTheme(val) {
      this.pendingTheme = val;
    },
    // 提交当前 pendingTheme 为正式主题
    async applyTheme() {
      if (!this.pendingTheme) return;
      this.theme = this.pendingTheme;
      localStorage.setItem("ll_theme", this.theme);
      await this.saveSettings();
    },
    resetPendingTheme() {
      this.pendingTheme = this.theme;
    },
    setBackgroundImage(url) {
      this.backgroundImage = url;
      localStorage.setItem("ll_background", url || "");
      this.saveSettings();
    },
    async removeBackground() {
      try {
        await request({
          url: "/api/users/upload/background",
          method: "delete",
        });
        this.backgroundImage = "";
        localStorage.setItem("ll_background", "");
        await this.saveSettings();
      } catch (e) {
        console.error("删除背景失败:", e);
        throw e;
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
