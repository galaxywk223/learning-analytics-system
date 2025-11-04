<template>
  <div
    class="page-wrapper"
    :data-theme="currentTheme"
    :class="{ 'sidebar-collapsed': true }"
  >
    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{ 'sidebar--collapsed': settingsStore.layout.sidebarCollapsed }"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <div class="sidebar-header">
        <img
          src="/logo.svg"
          alt="萤火集 Logo"
          class="logo-img"
          loading="lazy"
        />
        <span class="logo-text">萤火集</span>
      </div>

      <nav class="sidebar-nav">
        <el-tooltip content="仪表盘" placement="right">
          <router-link to="/dashboard" class="nav-link">
            <Icon icon="lucide:layout-dashboard" />
            <span>仪表盘</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="学习记录" placement="right">
          <router-link to="/records" class="nav-link">
            <Icon icon="lucide:notebook-pen" />
            <span>学习记录</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="统计分析" placement="right">
          <router-link to="/charts" class="nav-link">
            <Icon icon="lucide:bar-chart-3" />
            <span>统计分析</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="排行榜" placement="right">
          <router-link to="/leaderboard" class="nav-link">
            <Icon icon="lucide:users" />
            <span>排行榜</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="智能规划" placement="right">
          <router-link to="/ai" class="nav-link">
            <Icon icon="lucide:sparkles" />
            <span>智能规划</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="倒计时" placement="right">
          <router-link to="/countdown" class="nav-link">
            <Icon icon="lucide:timer" />
            <span>倒计时</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="专注模式" placement="right">
          <router-link to="/focus" class="nav-link">
            <Icon icon="lucide:target" />
            <span>专注模式</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="成就时刻" placement="right">
          <router-link to="/milestones" class="nav-link">
            <Icon icon="lucide:trophy" />
            <span>成就时刻</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="设置" placement="right">
          <router-link to="/settings" class="nav-link">
            <Icon icon="lucide:settings" />
            <span>设置</span>
          </router-link>
        </el-tooltip>
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

    <!-- 主内容区 - 添加 keep-alive 缓存 -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <keep-alive :max="3">
          <component :is="Component" :key="$route.fullPath" />
        </keep-alive>
      </router-view>
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
  if (!settingsStore.layout.sidebarCollapsed) {
    settingsStore.setSidebarCollapsed(true);
  }
  const backgroundImage = settingsStore.backgroundImage;
  if (backgroundImage) {
    document.body.style.backgroundImage = `url(${backgroundImage})`;
  }
});

const toggleSidebar = () => {
  settingsStore.setSidebarCollapsed(!settingsStore.layout.sidebarCollapsed);
};

// 鼠标悬停事件（保留用于未来扩展）
const handleMouseEnter = () => {};
const handleMouseLeave = () => {};
</script>

<style scoped>
/* 组件特定样式，主要样式已在全局CSS中定义 */
.page-wrapper {
  min-height: 100vh;
}
</style>
