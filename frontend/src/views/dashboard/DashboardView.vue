<template>
  <div class="dashboard-view">
    <!-- Header Section -->
    <header class="dashboard-header">
      <div class="header-stack">
        <h1 class="greeting-title">
          <span class="emoji-icon" aria-hidden="true">{{ greeting.icon }}</span>
          <span class="greeting-text">{{ greeting.text }}</span>
        </h1>
        <div class="motto-block">
          <p class="motto-display" :title="mottoDisplay">{{ mottoDisplay }}</p>
          <button
            class="motto-refresh"
            :disabled="mottoLoading"
            @click="refreshMotto(true)"
            aria-label="刷新格言"
          >
            <Icon
              icon="lucide:refresh-ccw"
              :class="{ spinning: mottoLoading }"
            />
          </button>
        </div>
      </div>
    </header>

    <!-- Main Grid Layout -->
    <div class="dashboard-grid">
      <!-- Row 1: Core Data (Wide Cards) -->
      <div class="grid-row-1">
        <!-- Card 1: Stats Analysis -->
        <router-link to="/charts" class="bento-card wide-card stats-card">
          <p class="card-title">统计分析</p>
          <div class="card-content">
            <div class="chart-header">
              <Icon icon="lucide:trending-up" class="card-icon" />
              <span class="trend-label">近7天学习时长</span>
            </div>
            <div class="chart-preview">
              <div class="bar-chart">
                <div
                  v-for="(bar, idx) in barHeights"
                  :key="idx"
                  class="bar"
                  :title="`${barLabels[idx]} · ${barValues[idx]} 分钟`"
                >
                  <div :class="['bar-fill', `fill-${idx}`]" :style="{ height: `${bar}%` }"></div>
                  <span class="bar-label">{{ barLabels[idx] }}</span>
                </div>
              </div>
            </div>
          </div>
        </router-link>

        <!-- Card 2: Learning Records -->
        <router-link to="/records" class="bento-card wide-card record-card">
          <p class="card-title">学习记录</p>
          <div class="card-content">
            <ul v-if="recentRecords.length" class="record-list">
              <li
                v-for="item in recentRecords"
                :key="item.id"
                class="record-row"
              >
                <span class="record-name">{{
                  item.title || "未命名记录"
                }}</span>
                <span class="record-sub">{{ item.subcategory }}</span>
                <span class="record-date">{{
                  formatRecordDate(item.date)
                }}</span>
                <span class="record-duration">{{
                  item.duration || "暂无时长"
                }}</span>
                <span class="record-mood">{{ moodEmoji(item.mood) }}</span>
              </li>
            </ul>
            <div v-else class="record-empty">
              <span class="empty-emoji">📘</span>
              <span class="empty-text">暂无记录</span>
            </div>
          </div>
        </router-link>
      </div>

      <!-- Row 2: Function Matrix (Square Cards) -->
      <div class="grid-row-2">
        <!-- Card 3: Start Focus -->
        <router-link to="/focus" class="bento-card square-card focus-card">
          <p class="card-title">专注计时</p>
          <div class="card-content centered">
            <span class="big-number">{{ todayFocusDuration }}</span>
            <span class="card-label">今日专注</span>
          </div>
        </router-link>

        <!-- Card 4: Countdown -->
        <router-link
          to="/countdown"
          class="bento-card square-card countdown-card"
        >
          <p class="card-title">倒计时</p>
          <div class="card-content centered">
            <span class="big-number">{{ countdownDays }}</span>
            <span class="card-label">{{ countdownTitle }}</span>
          </div>
        </router-link>

        <!-- Card 5: Achievements -->
        <router-link
          to="/milestones"
          class="bento-card square-card achievement-card"
        >
          <p class="card-title">成就时刻</p>
          <div class="card-content centered">
            <Icon icon="lucide:trophy" class="big-icon" />
            <span class="big-number-sm">{{ milestoneCount }}</span>
            <span class="card-label">成就时刻</span>
          </div>
        </router-link>

        <!-- Card 6: Ranking -->
        <router-link
          to="/leaderboard"
          class="bento-card square-card ranking-card"
        >
          <p class="card-title">社区排行</p>
          <div class="card-content centered">
            <span class="rank-icon">👑</span>
            <span class="status-text">{{ rankingLabel }}</span>
          </div>
        </router-link>

        <!-- Card 6: AI Plan -->
        <router-link to="/ai" class="bento-card square-card ai-card">
          <p class="card-title">智能规划</p>
          <div class="card-content centered">
            <Icon icon="lucide:sparkles" class="big-icon" />
            <span class="status-text">{{ aiPlanStatus }}</span>
          </div>
        </router-link>
      </div>
    </div>

    <!-- Floating Action Button -->
    <router-link to="/settings" class="fab-settings">
      <Icon icon="lucide:settings" />
    </router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onActivated } from "vue";
import dayjs from "dayjs";
import { Icon } from "@iconify/vue";
import { useDashboardStore } from "@/stores/modules/dashboard";
import { useMottoStore } from "@/stores/modules/motto";
import { recordApi } from "@/api/modules/records";

const dashboardStore = useDashboardStore();
const mottoStore = useMottoStore();
const allRecords = ref<any[]>([]);

/** 顶部问候语 */
const greeting = computed(() => {
  const hour = new Date().getHours();
  if (hour < 6) return { icon: "🌙", text: "夜深了，注意休息哦" };
  if (hour < 9) return { icon: "🌅", text: "早上好，新的一天开始了" };
  if (hour < 12) return { icon: "☀️", text: "上午好，保持专注" };
  if (hour < 14) return { icon: "🌞", text: "中午好，记得休息" };
  if (hour < 18) return { icon: "🌤️", text: "下午好，继续加油" };
  if (hour < 22) return { icon: "🌆", text: "晚上好，今天辛苦了" };
  return { icon: "🌙", text: "夜深了，早点休息" };
});

const formatDuration = (minutes) => {
  if (!minutes) return "0 分钟";
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs && mins) return `${hrs} 小时 ${mins} 分钟`;
  if (hrs) return `${hrs} 小时`;
  return `${mins} 分钟`;
};

/** 格言：使用个人设置里的自定义列表 */
const mottoText = ref("正在加载今日份的鸡汤...");
const mottoLoading = ref(false);
const lastMottoLoadedAt = ref(0);
const MIN_REFRESH_INTERVAL = 5_000;

const mottoPool = computed(() => {
  const personalMottos = Array.isArray(mottoStore.items)
    ? mottoStore.items
    : [];
  if (personalMottos.length) return personalMottos;
  const summaryMotto = dashboardStore.summary?.random_motto;
  return summaryMotto ? [summaryMotto] : [];
});

const mottoDisplay = computed(
  () => mottoText.value || "暂无格言，去设置里添加一句吧"
);

async function refreshMotto(force = false) {
  if (mottoLoading.value) return;
  if (!force && Date.now() - lastMottoLoadedAt.value < MIN_REFRESH_INTERVAL) {
    return;
  }

  mottoLoading.value = true;
  try {
    if (!mottoStore.items.length) {
      await mottoStore.fetch();
    }
    const pool = mottoPool.value;
    if (pool.length) {
      const random = pool[Math.floor(Math.random() * pool.length)];
      mottoText.value = random?.content || "保持热爱，奔赴山海";
      lastMottoLoadedAt.value = Date.now();
    } else {
      mottoText.value = "暂无格言，去设置里添加一句吧";
    }
  } catch (e) {
    console.error("Failed to load motto:", e);
    mottoText.value = "格言加载失败，请稍后再试";
  } finally {
    mottoLoading.value = false;
  }
}

async function fetchRecentRecords() {
  try {
    const resp = (await recordApi.getRecentRecords({ limit: 50 })) as any;
    const items =
      resp?.data?.records || resp?.data || resp?.records || resp || [];
    allRecords.value = Array.isArray(items) ? items : [];
  } catch (e) {
    console.error("Failed to fetch recent records", e);
    allRecords.value = [];
  }
}

onMounted(async () => {
  await dashboardStore.fetchSummary();
  try {
    await mottoStore.fetch();
  } catch (e) {
    console.error("Load mottos failed", e);
  }
  await refreshMotto(true);
  await fetchRecentRecords();
});

onActivated(async () => {
  await dashboardStore.fetchSummary();
  if (!mottoStore.items.length) {
    try {
      await mottoStore.fetch();
    } catch (e) {
      console.error("Load mottos failed", e);
    }
  }
  await fetchRecentRecords();
});

const sortedRecords = computed(() => {
  const records = allRecords.value || [];
  return records.slice().sort((a, b) => {
    const da = dayjs(a.log_date || a.date || a.created_at || 0);
    const db = dayjs(b.log_date || b.date || b.created_at || 0);
    if (db.isSame(da)) {
      return (
        dayjs(b.created_at || b.updated_at || 0).valueOf() -
        dayjs(a.created_at || a.updated_at || 0).valueOf()
      );
    }
    return db.valueOf() - da.valueOf();
  });
});

const recentRecords = computed(() => {
  const groupedByDay: Record<string, any[]> = {};
  sortedRecords.value.forEach((item: any) => {
    const key = dayjs(item.log_date || item.date || item.created_at).format(
      "YYYY-MM-DD"
    );
    groupedByDay[key] = groupedByDay[key] || [];
    groupedByDay[key].push(item);
  });

  const ordered: any[] = [];
  Object.keys(groupedByDay)
    .sort((a, b) => dayjs(b).valueOf() - dayjs(a).valueOf())
    .forEach((day) => {
      groupedByDay[day].forEach((item: any) => {
        ordered.push(item);
      });
    });

  return ordered.slice(0, 5).map((item: any) => ({
    id: item.id ?? item.record_id ?? Math.random(),
    title:
      item.task || item.title || item.content || item.category || "未命名记录",
    date: item.log_date || item.date || item.created_at || item.updated_at,
    duration: item.actual_duration
      ? `${item.actual_duration} 分钟`
      : item.duration
        ? formatDuration(Math.round(item.duration))
        : item.duration_text || "",
    mood: item.mood,
    subcategory: item.subcategory?.name || item.subcategory_name || "未分类",
  }));
});

const formatRecordDate = (value?: string) =>
  value ? dayjs(value).format("YYYY-MM-DD") : "时间未知";

const todayFocusDuration = computed(() => {
  const minutes = dashboardStore.summary?.today_duration_minutes ?? 0;
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hrs.toString().padStart(2, "0")}:${mins
    .toString()
    .padStart(2, "0")}`;
});

const countdownDays = computed(() => {
  const next = dashboardStore.summary?.next_countdown;
  return Math.max(next?.remaining_days ?? 0, 0);
});
const countdownTitle = computed(
  () => dashboardStore.summary?.next_countdown?.title || "暂无目标"
);

const milestoneCount = computed(
  () => dashboardStore.summary?.milestones_count ?? 0
);

const rankingLabel = computed(
  () => (dashboardStore.summary as any)?.ranking_label || "Top 5%"
);

const aiPlanStatus = computed(() => {
  const pending = dashboardStore.summary?.pending_todos ?? 0;
  return pending > 0 ? `待办 ${pending} 项` : "已生成今日计划";
});

const last7Days = computed(() => {
  const today = dayjs().startOf("day");
  return Array.from({ length: 7 }, (_, i) => today.subtract(6 - i, "day"));
});

const barValues = computed(() => {
  const map = new Map<string, number>();
  last7Days.value.forEach((d) => map.set(d.format("YYYY-MM-DD"), 0));

  sortedRecords.value.forEach((item: any) => {
    const dayKey = dayjs(item.log_date || item.date || item.created_at).format(
      "YYYY-MM-DD"
    );
    if (map.has(dayKey)) {
      const current = map.get(dayKey) || 0;
      const duration = Number(item.actual_duration || item.duration || 0);
      map.set(dayKey, current + (Number.isFinite(duration) ? duration : 0));
    }
  });

  return last7Days.value.map((d) => map.get(d.format("YYYY-MM-DD")) || 0);
});

const barLabels = computed(() => last7Days.value.map((d) => d.format("MM/DD")));

const barHeights = computed(() => {
  const data = barValues.value;
  const max = Math.max(...data, 1);
  return data.map((v: number) => Math.max(6, Math.round((v / max) * 100)));
});

const moodEmoji = (mood?: number) => {
  const moods: Record<number, string> = {
    5: "😃",
    4: "😊",
    3: "😐",
    2: "😟",
    1: "😠",
  };
  return moods[mood ?? 0] || "⚪️";
};
</script>

<style scoped lang="scss">
@use "@/styles/views/dashboard/DashboardView.module.scss";
</style>
