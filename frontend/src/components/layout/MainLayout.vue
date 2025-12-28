<template>
  <div class="page-wrapper" :class="{ 'sidebar-collapsed': true }">
    <!-- 侧边栏 -->
    <aside
      class="sidebar"
      :class="{ 'sidebar--collapsed': settingsStore.layout.sidebarCollapsed }"
      @mouseenter="handleMouseEnter"
      @mouseleave="handleMouseLeave"
    >
      <div class="sidebar-header">
        <span class="logo-text">萤火集</span>
      </div>

      <nav class="sidebar-nav">
        <el-tooltip content="仪表盘" placement="right">
          <router-link to="/dashboard" class="nav-link">
            <Icon icon="lucide:layout-dashboard" />
            <span>仪表盘</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="专注模式" placement="right">
          <router-link to="/focus" class="nav-link">
            <Icon icon="lucide:target" />
            <span>专注模式</span>
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

        <el-tooltip content="社区排行" placement="right">
          <router-link to="/leaderboard" class="nav-link">
            <Icon icon="lucide:users" />
            <span>社区排行</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="倒计时" placement="right">
          <router-link to="/countdown" class="nav-link">
            <Icon icon="lucide:timer" />
            <span>倒计时</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="成就时刻" placement="right">
          <router-link to="/milestones" class="nav-link">
            <Icon icon="lucide:trophy" />
            <span>成就时刻</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="智能规划" placement="right">
          <router-link to="/ai" class="nav-link">
            <Icon icon="lucide:sparkles" />
            <span>智能规划</span>
          </router-link>
        </el-tooltip>

        <el-tooltip content="设置中心" placement="right">
          <router-link to="/settings" class="nav-link">
            <Icon icon="lucide:settings" />
            <span>设置中心</span>
          </router-link>
        </el-tooltip>
      </nav>

      <div class="sidebar-footer">
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
import { Icon } from "@iconify/vue";
import { useSettingsStore } from "@/stores/modules/settings";

const settingsStore = useSettingsStore();

// 应用背景图片
onMounted(async () => {
  await settingsStore.fetchSettings();
  if (!settingsStore.layout.sidebarCollapsed) {
    settingsStore.setSidebarCollapsed(true);
  }
  // Removed imperative background setting to prevent FOUC. Handled in App.vue/global styles.
});

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
