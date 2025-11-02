<template>
  <div class="page-wrapper" :data-theme="currentTheme">
    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <img src="/logo.svg" alt="萤火集 Logo" class="logo-img" />
        <span class="logo-text">萤火集</span>
      </div>

      <nav class="sidebar-nav">
        <router-link to="/dashboard" class="nav-link">
          <Icon icon="lucide:layout-dashboard" />
          <span>仪表盘</span>
        </router-link>

        <router-link to="/records" class="nav-link">
          <Icon icon="lucide:notebook-pen" />
          <span>学习记录</span>
        </router-link>

        <router-link to="/charts" class="nav-link">
          <Icon icon="lucide:bar-chart-3" />
          <span>统计分析</span>
        </router-link>

        <router-link to="/countdown" class="nav-link">
          <Icon icon="lucide:timer" />
          <span>倒计时</span>
        </router-link>

        <router-link to="/milestones" class="nav-link">
          <Icon icon="lucide:trophy" />
          <span>成就时刻</span>
        </router-link>

        <router-link to="/settings" class="nav-link">
          <Icon icon="lucide:settings" />
          <span>设置</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div v-if="authStore.user" class="user-info">
          <Icon icon="lucide:user-circle-2" />
          <span>你好, {{ authStore.user.username }}</span>
        </div>
        <a
          v-if="authStore.isAuthenticated"
          @click="handleLogout"
          class="logout-link"
        >
          <Icon icon="lucide:log-out" />
          <span>登出</span>
        </a>
        <p>&copy; wangk227@ahut.edu.cn</p>
      </div>
    </aside>

    <!-- 主内容区 -->
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { Icon } from "@iconify/vue";
import { useAuthStore } from "@/stores/modules/auth";
import { useSettingsStore } from "@/stores/modules/settings";

const authStore = useAuthStore();
const settingsStore = useSettingsStore();
const router = useRouter();

// 获取当前主题
const currentTheme = computed(() => settingsStore.theme || "palette-purple");

// 退出登录
const handleLogout = async () => {
  await authStore.logout();
  router.push("/login");
};

// 应用背景图片
onMounted(async () => {
  await settingsStore.fetchSettings();
  const backgroundImage = settingsStore.backgroundImage;
  if (backgroundImage) {
    document.body.style.backgroundImage = `url(${backgroundImage})`;
  }
});
</script>

<style scoped>
/* 组件特定样式，主要样式已在全局CSS中定义 */
.page-wrapper {
  min-height: 100vh;
}
</style>
