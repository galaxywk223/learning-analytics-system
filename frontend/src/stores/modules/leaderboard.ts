import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { ElMessage } from "element-plus";
import { leaderboardAPI, type LeaderboardParams } from "@/api/modules/leaderboard";

type Period = "day" | "week" | "month";
type Metric = "duration" | "efficiency";

export const useLeaderboardStore = defineStore("leaderboard", () => {
  const loading = ref(false);
  const period = ref<Period>("week");
  const metric = ref<Metric>("duration");
  const page = ref(1);
  const pageSize = ref(20);
  const total = ref(0);
  const range = ref<{ start: string; end: string } | null>(null);
  const generatedAt = ref<string | null>(null);
  const items = ref<any[]>([]);
  const me = ref<any | null>(null);
  const optedIn = ref(false);

  const detailLoading = ref(false);
  const userDetail = ref<any | null>(null);

  let refreshTimer: number | null = null;

  const hasMore = computed(() => page.value * pageSize.value < total.value);

  const requestParams = computed<LeaderboardParams>(() => ({
    period: period.value,
    metric: metric.value,
    page: page.value,
    page_size: pageSize.value,
  }));

  async function fetchStatus() {
    try {
      const response: any = await leaderboardAPI.getStatus();
      if (response?.success && response.data) {
        optedIn.value = !!response.data.opted_in;
      }
    } catch (error) {
      console.error("Fetch leaderboard status failed:", error);
    }
  }

  async function fetchRankings(force = false) {
    if (loading.value && !force) return;
    loading.value = true;
    try {
      const response: any = await leaderboardAPI.getRankings(requestParams.value);
      if (response?.success && response.data) {
        items.value = response.data.items || [];
        me.value = response.data.me || null;
        total.value = response.data.total || 0;
        range.value = response.data.range || null;
        generatedAt.value = response.data.generated_at || null;
        optedIn.value = response.data.opted_in ?? optedIn.value;
      }
    } catch (error) {
      console.error("Fetch leaderboard rankings failed:", error);
    } finally {
      loading.value = false;
    }
  }

  async function fetchUserStats(userId: number) {
    detailLoading.value = true;
    try {
      const response: any = await leaderboardAPI.getUserStats(userId, {
        period: period.value,
      });
      if (response?.success && response.data) {
        userDetail.value = response.data;
      } else {
        userDetail.value = null;
      }
    } catch (error) {
      console.error("Fetch user leaderboard stats failed:", error);
      userDetail.value = null;
      throw error;
    } finally {
      detailLoading.value = false;
    }
  }

  function setPeriod(value: Period) {
    if (period.value === value) return;
    period.value = value;
    page.value = 1;
    fetchRankings(true);
  }

  function setMetric(value: Metric) {
    if (metric.value === value) return;
    metric.value = value;
    page.value = 1;
    fetchRankings(true);
  }

  async function changePage(newPage: number) {
    if (newPage === page.value) return;
    page.value = newPage;
    await fetchRankings(true);
  }

  async function join() {
    try {
      const response: any = await leaderboardAPI.join();
      if (response?.success) {
        optedIn.value = true;
        ElMessage.success(response.message || "已加入社区排行");
        await fetchRankings(true);
      }
    } catch (error) {
      console.error("Join leaderboard failed:", error);
    }
  }

  async function leave() {
    try {
      const response: any = await leaderboardAPI.leave();
      if (response?.success) {
        optedIn.value = false;
        ElMessage.success(response.message || "已退出社区排行");
        await fetchRankings(true);
      }
    } catch (error) {
      console.error("Leave leaderboard failed:", error);
    }
  }

  function startAutoRefresh(interval = 60000) {
    stopAutoRefresh();
    refreshTimer = window.setInterval(() => {
      fetchRankings();
    }, interval);
  }

  function stopAutoRefresh() {
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  async function initialize() {
    await fetchStatus();
    await fetchRankings(true);
    startAutoRefresh();
  }

  return {
    loading,
    period,
    metric,
    page,
    pageSize,
    total,
    range,
    generatedAt,
    items,
    me,
    optedIn,
    hasMore,
    userDetail,
    detailLoading,
    requestParams,
    fetchStatus,
    fetchRankings,
    fetchUserStats,
    setPeriod,
    setMetric,
    changePage,
    join,
    leave,
    startAutoRefresh,
    stopAutoRefresh,
    initialize,
  };
});
