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
          <div
            class="motto-track"
            :class="{ 'is-animating': marqueeActive }"
          >
            <div class="motto-track__inner">
              <span
                v-for="(text, idx) in marqueeItems"
                :key="idx"
                class="motto-text"
              >
                {{ text }}
              </span>
            </div>
          </div>
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
        <div class="card-content">
          <div class="card-icon">
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
import dayjs from "dayjs";
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
const formatDuration = (minutes) => {
  if (!minutes) return "0 分钟";
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs && mins) return `${hrs} 小时 ${mins} 分钟`;
  if (hrs) return `${hrs} 小时`;
  return `${mins} 分钟`;
};

const focusSummary = computed(() => {
  const minutes = dashboardStore.summary?.today_duration_minutes ?? 0;
  if (!minutes) return "还没有记录今日专注时长";
  return `今日已专注 ${formatDuration(minutes)}`;
});

const recordSummary = computed(() => {
  const total = dashboardStore.summary?.total_records ?? 0;
  const latest = dashboardStore.summary?.latest_record_date;
  if (!total) return "暂无学习记录，点击进入开始记录";
  const latestText = latest ? dayjs(latest).format("YYYY/MM/DD") : "近期";
  return `共 ${total} 条 · 最近更新 ${latestText}`;
});

const chartsSummary = computed(() => {
  const total = dashboardStore.summary?.total_records ?? 0;
  if (total >= 5) return "数据已同步，可查看趋势与对比";
  if (total > 0) return "数据较少，再记录几次即可生成趋势";
  return "暂无统计数据，先去记录几次学习吧";
});

const leaderboardSummary = computed(() => "实时查看社区排行动态");

const countdownSummary = computed(() => {
  const next = dashboardStore.summary?.next_countdown;
  if (next?.title) {
    const days = next.remaining_days ?? 0;
    const dayText = days > 0 ? `${days} 天后` : "今天";
    return `${next.title} · ${dayText}`;
  }
  const total = dashboardStore.summary?.countdown_total ?? 0;
  return total > 0 ? `共有 ${total} 个倒计时事项` : "暂未添加倒计时提醒";
});

const milestoneSummary = computed(() => {
  const count = dashboardStore.summary?.milestones_count ?? 0;
  return count > 0 ? `已记录 ${count} 个高光瞬间` : "记录你的第一个高光瞬间";
});

const aiSummary = computed(() => {
  const pending = dashboardStore.summary?.pending_todos ?? 0;
  return pending > 0 ? `还有 ${pending} 项待办等待处理` : "待办已清空，轻松规划下一步";
});

/** 随机格言：统一走 store，避免与 fetch('/api/...') 冲突 */
/* Motto logic */
const mottoText = ref("正在加载今日份的鸡汤...");
const mottoLoading = ref(false);
const lastMottoLoadedAt = ref(0);

const MIN_REFRESH_INTERVAL = 5_000;

const mottoDisplay = computed(() => mottoText.value || "");
const marqueeItems = computed(() => {
  const text = mottoDisplay.value;
  return text ? [text, text] : ["", ""];
});
const marqueeActive = computed(() => marqueeItems.value[0].length > 0);




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
    title: "开始专注",
    summary: focusSummary.value,
  },
  {
    key: "records",
    to: "/records",
    class: "card-record",
    icon: "lucide:book-open",
    title: "学习记录",
    summary: recordSummary.value,
  },
  {
    key: "charts",
    to: "/charts",
    class: "card-chart",
    icon: "lucide:trending-up",
    title: "统计分析",
    summary: chartsSummary.value,
  },
  {
    key: "leaderboard",
    to: "/leaderboard",
    class: "card-leaderboard",
    icon: "lucide:users",
    title: "社区排行",
    summary: leaderboardSummary.value,
  },
  {
    key: "countdown",
    to: "/countdown",
    class: "card-countdown",
    icon: "lucide:calendar-clock",
    title: "倒计时",
    summary: countdownSummary.value,
  },
  {
    key: "milestones",
    to: "/milestones",
    class: "card-milestone",
    icon: "lucide:award",
    title: "成就时刻",
    summary: milestoneSummary.value,
  },
  {
    key: "ai",
    to: "/ai",
    class: "card-ai",
    icon: "lucide:sparkles",
    title: "智能规划",
    summary: aiSummary.value,
  },
  {
    key: "settings",
    to: "/settings",
    class: "card-settings",
    icon: "lucide:settings",
    title: "设置中心",
    summary: "配置账户、数据与偏好设置",
  },
]);

</script>

<style scoped lang="scss">
@use "@/styles/views/dashboard/DashboardView.module.scss";
</style>
