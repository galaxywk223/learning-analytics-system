<template>
  <div id="app" :data-theme="currentTheme">
    <router-view v-slot="{ Component }">
      <keep-alive :max="5">
        <component :is="Component" :key="$route.fullPath" />
      </keep-alive>
    </router-view>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useAuthStore } from "@/stores/modules/auth";
import { useSettingsStore } from "@/stores/modules/settings";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();

const currentTheme = computed(() => settingsStore.theme || "palette-purple");

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
  /* Apple-style dynamic light background - Mesh Gradient */
  background-color: #f5f5f7;
  background-image: 
    radial-gradient(at 80% 0%, hsla(189,100%,96%,1) 0px, transparent 50%),
    radial-gradient(at 0% 50%, hsla(341,100%,96%,1) 0px, transparent 50%),
    radial-gradient(at 80% 50%, hsla(355,100%,96%,1) 0px, transparent 50%),
    radial-gradient(at 0% 100%, hsla(22,100%,96%,1) 0px, transparent 50%),
    radial-gradient(at 80% 100%, hsla(240,100%,96%,1) 0px, transparent 50%),
    radial-gradient(at 0% 0%, hsla(343,100%,96%,1) 0px, transparent 50%);
  background-size: cover;
}

/* 当用户上传了自定义背景时，通过settings store动态设置 */
#app.custom-bg {
  background-image: var(--custom-bg-url);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

/* 性能优化：减少动画计算 */
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
