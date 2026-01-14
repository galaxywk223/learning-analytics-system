<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <keep-alive :max="5">
        <component :is="Component" :key="$route.fullPath" />
      </keep-alive>
    </router-view>
  </div>
</template>

<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/modules/auth";
import { useSettingsStore } from "@/stores/modules/settings";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();

onMounted(() => {
  // 应用加载时检查登录状态
  authStore.checkAuth();
  // 加载用户设置
  if (authStore.isAuthenticated) {
    settingsStore.fetchSettings();
  }
});
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html,
body {
  height: 100%;
  font-family:
    "Inter", "Helvetica Neue", Helvetica, "PingFang SC", "Hiragino Sans GB",
    "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
  /* 性能优化：启用硬件加速 */
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

/* 性能优化：减少动画计算（用户系统级偏好） */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
