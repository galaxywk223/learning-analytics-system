<template>
  <div id="app" :data-theme="currentTheme">
    <router-view />
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
}

#app {
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
}

/* 当用户上传了自定义背景时，通过settings store动态设置 */
#app.custom-bg {
  background-image: var(--custom-bg-url);
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
</style>
