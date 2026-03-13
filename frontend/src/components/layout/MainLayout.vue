<template>
  <div class="page-wrapper">
    <div
      v-if="mobileNavOpen"
      class="mobile-nav"
      aria-hidden="true"
      @click="mobileNavOpen = false"
    />

    <aside
      class="sidebar"
      :class="{
        'sidebar--collapsed': settingsStore.layout.sidebarCollapsed,
        'sidebar--open': mobileNavOpen,
      }"
    >
      <div class="sidebar-header">
        <div class="sidebar-header__brand">
          <Icon icon="lucide:book-marked" />
        </div>
        <div class="sidebar-header__copy">
          <span class="sidebar-header__eyebrow">Learning OS</span>
          <span class="logo-text">萤火集</span>
        </div>
      </div>

      <section class="sidebar-section">
        <span class="sidebar-section__title">Workspace</span>
        <nav class="sidebar-nav">
          <router-link
            v-for="item in navItems"
            :key="item.to"
            :to="item.to"
            class="nav-link"
            @click="mobileNavOpen = false"
          >
            <Icon :icon="item.icon" />
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </section>

      <div class="sidebar-footer">
        <p>记录、分析、规划。让学习节奏更清晰。</p>
        <p>萤火集 3.0</p>
      </div>
    </aside>

    <div class="main-shell">
      <header class="main-topbar">
        <div class="main-topbar__left">
          <button
            type="button"
            class="topbar-btn"
            aria-label="切换导航"
            @click="toggleNavigation"
          >
            <Icon :icon="mobileNavOpen ? 'lucide:x' : 'lucide:panel-left'" />
          </button>
          <div class="main-topbar__route">
            <h2 class="main-topbar__route-title">{{ currentRouteTitle }}</h2>
            <span class="main-topbar__route-subtitle">安静的学习操作系统</span>
          </div>
        </div>

        <div class="main-topbar__right">
          <button
            type="button"
            class="topbar-btn"
            aria-label="折叠侧栏"
            @click="settingsStore.setSidebarCollapsed(!settingsStore.layout.sidebarCollapsed)"
          >
            <Icon
              :icon="
                settingsStore.layout.sidebarCollapsed
                  ? 'lucide:panel-left-open'
                  : 'lucide:panel-left-close'
              "
            />
          </button>
          <ThemeSwitcher />
        </div>
      </header>

      <main class="main-content">
        <router-view v-slot="{ Component }">
          <keep-alive :max="3">
            <component :is="Component" :key="$route.fullPath" />
          </keep-alive>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { Icon } from "@iconify/vue";
import { useSettingsStore } from "@/stores/modules/settings";
import ThemeSwitcher from "@/components/common/ThemeSwitcher.vue";

const route = useRoute();
const settingsStore = useSettingsStore();
const mobileNavOpen = ref(false);

const navItems = [
  { to: "/dashboard", label: "仪表盘", icon: "lucide:layout-dashboard" },
  { to: "/focus", label: "专注模式", icon: "lucide:timer-reset" },
  { to: "/records", label: "学习记录", icon: "lucide:notebook-tabs" },
  { to: "/charts", label: "统计分析", icon: "lucide:chart-column-big" },
  { to: "/leaderboard", label: "社区排行", icon: "lucide:users-round" },
  { to: "/countdown", label: "倒计时", icon: "lucide:calendar-clock" },
  { to: "/milestones", label: "成就时刻", icon: "lucide:trophy" },
  { to: "/ai", label: "智能规划", icon: "lucide:sparkles" },
  { to: "/settings", label: "设置中心", icon: "lucide:settings-2" },
];

const currentRouteTitle = computed(() => {
  const match = navItems.find((item) => route.path.startsWith(item.to));
  return (route.meta.title as string) || match?.label || "萤火集";
});

const toggleNavigation = () => {
  if (window.innerWidth <= 960) {
    mobileNavOpen.value = !mobileNavOpen.value;
    return;
  }
  settingsStore.setSidebarCollapsed(!settingsStore.layout.sidebarCollapsed);
};

watch(
  () => route.fullPath,
  () => {
    mobileNavOpen.value = false;
  },
);

onMounted(async () => {
  await settingsStore.fetchSettings();
});
</script>
