<template>
  <div class="dashboard-view">
    <!-- 顶部问候区域 -->
    <div class="greeting-section">
      <div class="greeting-content">
        <h1 class="greeting-title">{{ greeting }}</h1>
        <p class="greeting-subtitle">让每一天的学习都充满意义</p>
      </div>
    </div>

    <!-- 格言卡片 -->
    <div class="motto-section">
      <div class="motto-card">
        <div class="motto-icon">
          <Icon icon="lucide:sparkles" />
        </div>
        <div class="motto-content">
          <p class="motto-text">{{ mottoText }}</p>
        </div>
        <button
          class="motto-refresh"
          @click="refreshMotto(true)"
          :disabled="mottoLoading"
          :class="{ spinning: mottoLoading }"
        >
          <Icon icon="lucide:refresh-cw" />
        </button>
      </div>
    </div>

    <!-- 功能卡片网格 -->
    <div class="cards-grid">
      <router-link
        v-for="card in cards"
        :key="card.key"
        :to="card.to"
        class="feature-card"
        :class="card.class"
      >
        <div class="card-background"></div>
        <div class="card-content">
          <div class="card-icon" :class="card.iconClass">
            <Icon :icon="card.icon" />
          </div>
          <h3 class="card-title">{{ card.title }}</h3>
          <p class="card-description">{{ card.summary }}</p>
        </div>
        <div class="card-arrow">
          <Icon icon="lucide:arrow-right" />
        </div>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onActivated } from "vue";
import { Icon } from "@iconify/vue";
import { useDashboardStore } from "@/stores/modules/dashboard";
import { useAuthStore } from "@/stores/modules/auth";
import axios from "axios";

const dashboardStore = useDashboardStore();
const authStore = useAuthStore();

/** 顶部问候语 */
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return "🌙 夜深了，注意休息哦";
  if (hour < 9) return "🌅 早上好，新的一天开始了";
  if (hour < 12) return "☀️ 上午好，保持专注";
  if (hour < 14) return "🌞 中午好，记得休息";
  if (hour < 18) return "🌤️ 下午好，继续加油";
  if (hour < 22) return "🌆 晚上好，今天辛苦了";
  return "🌙 夜深了，早点休息";
});

/** 各卡片摘要（统一从 store.summary 取值，若无则给默认文案） */
const recordSummary = computed(() => {
  const count = dashboardStore.summary?.records_count ?? 0;
  const duration = dashboardStore.summary?.total_duration ?? 0;
  return `已记录 ${count} 条 · 累计 ${duration} 小时`;
});

const chartSummary = computed(() => "查看学习统计与趋势分析");
const leaderboardSummary = computed(() => "实时查看全站学习排行榜");

const countdownSummary = computed(() => {
  const count = dashboardStore.summary?.countdown_count ?? 0;
  return `${count} 个重要日期正在倒计时`;
});

const milestoneSummary = computed(() => {
  const count = dashboardStore.summary?.milestones_count ?? 0;
  return `已记录 ${count} 个重要时刻`;
});

/** 随机格言：统一走 store，避免与 fetch('/api/...') 冲突 */
/* Motto logic */
const mottoText = ref("正在加载今日份的鸡汤...");
const mottoLoading = ref(false);
const lastMottoLoadedAt = ref(0);

const MIN_REFRESH_INTERVAL = 5_000;

async function refreshMotto(force = false) {
  if (!authStore.accessToken) {
    mottoText.value = "δ��¼���޷���ȡ����";
    return;
  }
  if (mottoLoading.value) {
    return;
  }
  if (!force && Date.now() - lastMottoLoadedAt.value < MIN_REFRESH_INTERVAL) {
    return;
  }

  mottoLoading.value = true;
  try {
    // Pinia auth store ʹ�� accessToken ���ԣ������� token
    const resp = await axios.get("/api/mottos/random", {
      headers: { Authorization: `Bearer ${authStore.accessToken}` },
    });
    if (resp.data.success) {
      // ��˼��ݾɸ�ʽ������ content �ֶΣ����� motto �������� content ��Ϊ fallback
      if (resp.data.content) {
        mottoText.value = resp.data.content;
      } else if (resp.data.motto && resp.data.motto.content) {
        mottoText.value = resp.data.motto.content;
      } else {
        mottoText.value = "û�п��õĸ���";
      }
      lastMottoLoadedAt.value = Date.now();
    } else {
      mottoText.value = "û�п��õĸ���";
    }
  } catch (e) {
    console.error("Failed to load motto:", e);
    mottoText.value = "����ʧ�ܣ����Ժ�����";
  } finally {
    mottoLoading.value = false;
  }
}

onMounted(async () => {
  await dashboardStore.fetchSummary();
  // 若 dashboard summary 已包含 random_motto 则直接展示以减少一次网络请求
  const summaryMotto = dashboardStore.summary?.random_motto;
  if (summaryMotto && summaryMotto.content) {
    mottoText.value = summaryMotto.content;
    lastMottoLoadedAt.value = Date.now();
  } else {
    await refreshMotto();
  }
});

onActivated(async () => {
  await dashboardStore.fetchSummary();
  const summaryMotto = dashboardStore.summary?.random_motto;
  if (summaryMotto?.content) {
    mottoText.value = summaryMotto.content;
    lastMottoLoadedAt.value = Date.now();
  } else {
    await refreshMotto();
  }
});

const cards = computed(() => [
  {
    key: "focus",
    to: "/focus",
    class: "card-focus",
    icon: "lucide:timer",
    iconClass: "icon-focus",
    title: "开始专注",
    summary: "进入专注模式并记录学习时长",
  },
  {
    key: "records",
    to: "/records",
    class: "card-record",
    icon: "lucide:book-open",
    iconClass: "icon-record",
    title: "学习记录",
    summary: recordSummary.value,
  },
  {
    key: "charts",
    to: "/charts",
    class: "card-chart",
    icon: "lucide:trending-up",
    iconClass: "icon-chart",
    title: "统计分析",
    summary: chartSummary.value,
  },
  {
    key: "leaderboard",
    to: "/leaderboard",
    class: "card-leaderboard",
    icon: "lucide:users",
    iconClass: "icon-leaderboard",
    title: "排行榜",
    summary: leaderboardSummary.value,
  },
  {
    key: "countdown",
    to: "/countdown",
    class: "card-countdown",
    icon: "lucide:calendar-clock",
    iconClass: "icon-countdown",
    title: "倒计时",
    summary: countdownSummary.value,
  },
  {
    key: "milestones",
    to: "/milestones",
    class: "card-milestone",
    icon: "lucide:award",
    iconClass: "icon-milestone",
    title: "里程碑",
    summary: milestoneSummary.value,
  },
  {
    key: "ai",
    to: "/ai",
    class: "card-ai",
    icon: "lucide:sparkles",
    iconClass: "icon-ai",
    title: "智能规划",
    summary: "生成分析与规划建议",
  },
  {
    key: "settings",
    to: "/settings",
    class: "card-settings",
    icon: "lucide:settings",
    iconClass: "icon-settings",
    title: "系统设置",
    summary: "配置账户与系统偏好",
  },
]);

</script>

<style scoped lang="scss">
@use "@/styles/views/dashboard/DashboardView.module.scss";
</style>
