<template>
  <div class="leaderboard-view">
    <PageContainer
      :title="{ icon: '📈', text: '社区排行' }"
      subtitle="实时查看社区学习时长与效率榜单，点选用户了解详情"
    >
      <section class="leaderboard-toolbar">
        <div class="segment-group">
          <span class="seg-label">周期</span>
          <div class="segmented">
            <button
              v-for="option in periodOptions"
              :key="option.value"
              :class="['seg-btn', leaderboard.period === option.value && 'active']"
              @click="leaderboard.setPeriod(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <div class="segment-group">
          <span class="seg-label">榜单</span>
          <div class="segmented">
            <button
              v-for="option in metricOptions"
              :key="option.value"
              :class="['seg-btn', leaderboard.metric === option.value && 'active']"
              @click="leaderboard.setMetric(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <button
          v-if="leaderboard.optedIn"
          class="exit-link"
          type="button"
          @click="handleLeave"
          :disabled="leaveLoading"
        >
          <Icon icon="lucide:log-out" />
          退出
        </button>
      </section>

      <el-alert
      v-if="!leaderboard.optedIn"
      type="info"
      show-icon
      class="join-alert"
    >
      <template #title>未加入社区排行</template>
      <template #default>
        <div class="join-alert__body">
          <span>加入后即可出现在榜单中，并分享你的学习数据（时长与效率）。</span>
          <el-button type="primary" size="small" @click="handleJoin" :loading="joinLoading">
            立即加入
          </el-button>
        </div>
      </template>
    </el-alert>

      <div class="podium-card" v-if="topThree.length">
        <div class="podium-header">
          <h3>荣耀榜 · {{ currentPeriodLabel }}</h3>
          <p>{{ currentMetricLabel }}</p>
        </div>
        <div class="podium-grid">
          <div
            v-for="item in podiumSlots"
          :key="item.rank"
            class="podium-slot"
            :class="['pos-' + item.rank, !item.user && 'empty']"
            @click="item.user && openDetail(item.user)"
          >
            <div class="avatar-wrap" :style="{ borderColor: item.border }">
              <div class="crown" v-if="item.rank === 1">👑</div>
              <span v-if="item.user" class="avatar-text">
                {{ item.user.username?.charAt(0)?.toUpperCase() || "U" }}
              </span>
            </div>
            <div class="podium-name" v-if="item.user">
              {{ item.user.username }}
              <span v-if="item.user.isSelf" class="tag-me">我</span>
            </div>
            <div class="podium-value" v-if="item.user">
              {{ item.user.valueText }}
            </div>
            <div class="podium-rank">{{ item.rank }}</div>
          </div>
        </div>
      </div>

      <div class="list-card">
        <div class="list-header">
          <div>
            <h3>{{ currentMetricLabel }} · {{ currentPeriodLabel }}</h3>
            <p>更新时间：{{ generatedAtText }} · 数据范围：{{ rangeText }}</p>
          </div>
          <div class="list-actions" v-if="leaderboard.optedIn">
            <span v-if="leaderboard.loading">加载中...</span>
          </div>
        </div>

        <div class="rank-list" v-loading="leaderboard.loading">
          <div
            v-for="row in restList"
            :key="row.user_id"
            class="rank-item"
            @click="openDetail(row)"
          >
            <div class="rank-left">
              <span class="rank-no">{{ row.rank }}</span>
              <div class="user-block">
                <div class="user-avatar">
                  {{ row.username?.charAt(0)?.toUpperCase() || "U" }}
                </div>
                <div class="user-meta">
                  <div class="user-name">
                    {{ row.username }}
                    <span v-if="row.isSelf" class="tag-me">我</span>
                  </div>
                  <div class="user-sub">记录 {{ row.sessions || 0 }} 次</div>
                </div>
              </div>
            </div>
            <div class="rank-right">
              <div class="metric-value">
                <template v-if="leaderboard.metric === 'duration'">
                  {{ formatDuration(row.total_duration_minutes) }}
                </template>
                <template v-else>
                  {{ formatEfficiency(row.average_efficiency) }}
                </template>
              </div>
              <div class="metric-sub">
                最近活动：{{ row.last_activity ? formatDate(row.last_activity) : "—" }}
              </div>
            </div>
          </div>

          <el-empty v-if="!leaderboard.loading && !restList.length" description="虚位以待" />
        </div>

        <div class="table-footer">
          <el-pagination
            background
            layout="prev, pager, next"
            :page-size="leaderboard.pageSize"
            :current-page="leaderboard.page"
            :total="leaderboard.total"
            @current-change="leaderboard.changePage"
          />
        </div>
      </div>

      <el-drawer
      v-model="detailVisible"
      title="用户详细数据"
      size="45%"
      :destroy-on-close="true"
      @close="closeDetail"
    >
      <div v-loading="leaderboard.detailLoading" class="detail-wrapper">
        <template v-if="leaderboard.userDetail && !leaderboard.detailLoading">
          <div class="detail-header">
            <h3>{{ leaderboard.userDetail.user.username }}</h3>
            <p>
              数据范围：{{ formatDate(leaderboard.userDetail.range.start) }} -
              {{ formatDate(leaderboard.userDetail.range.end) }}
            </p>
          </div>

          <div class="detail-metrics">
            <el-card shadow="hover">
              <div class="metric">
                <span class="label">总时长</span>
                <span class="value">
                  {{ detailSummary.totalHours }}
                </span>
              </div>
            </el-card>
            <el-card shadow="hover">
              <div class="metric">
                <span class="label">平均效率</span>
                <span class="value">
                  {{ detailSummary.averageEfficiency }}
                </span>
              </div>
            </el-card>
            <el-card shadow="hover">
              <div class="metric">
                <span class="label">记录次数</span>
                <span class="value">{{ detailSummary.averagePerDay }}</span>
              </div>
            </el-card>
            <el-card shadow="hover">
              <div class="metric">
                <span class="label">活跃天数</span>
                <span class="value">{{ detailSummary.activeDays }}</span>
              </div>
            </el-card>
          </div>

          <el-divider content-position="left">趋势洞察</el-divider>
          <el-empty v-if="!trendChartData.length" description="暂无趋势数据" />
          <UserTrendChart v-else :data="trendChartData" />

          <el-divider content-position="left">分类占比</el-divider>
          <el-empty v-if="!categoryChartData.length" description="暂无分类数据" />
          <UserCategoryChart v-else :data="categoryChartData" />
        </template>
        <template v-else-if="!leaderboard.detailLoading">
          <el-empty description="暂无数据" />
        </template>
      </div>
    </el-drawer>
    </PageContainer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useLeaderboardStore } from "@/stores/modules/leaderboard";
import dayjs from "dayjs";
import UserTrendChart from "@/components/business/leaderboard/UserTrendChart.vue";
import UserCategoryChart from "@/components/business/leaderboard/UserCategoryChart.vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import { Icon } from "@iconify/vue";

interface DetailSummary {
  totalHours: string;
  averageEfficiency: string;
  averagePerDay: string;
  activeDays: string;
}

const leaderboard = useLeaderboardStore();
const detailVisible = ref(false);
const joinLoading = ref(false);
const leaveLoading = ref(false);

const periodOptions = [
  { label: "今日", value: "day" as const },
  { label: "近7天", value: "week" as const },
  { label: "近30天", value: "month" as const },
];

const metricOptions = [
  { label: "时长榜", value: "duration" as const },
  { label: "效率榜", value: "efficiency" as const },
];

onMounted(async () => {
  await leaderboard.initialize();
});

onUnmounted(() => {
  leaderboard.stopAutoRefresh();
});

const currentMetricLabel = computed(() => {
  return metricOptions.find((item) => item.value === leaderboard.metric)?.label || "";
});

const currentPeriodLabel = computed(() => {
  return periodOptions.find((item) => item.value === leaderboard.period)?.label || "";
});

const tableData = computed(() =>
  (leaderboard.items || []).map((item: any) => ({
    ...item,
    isSelf: leaderboard.me?.user_id === item.user_id,
  }))
);

const topThree = computed(() => tableData.value.slice(0, 3));
const restList = computed(() => tableData.value.slice(3));

const podiumSlots = computed(() => {
  const colors = ["#facc15", "#c0c4ce", "#f97316"];
  return [1, 2, 3].map((rank, idx) => {
    const user = topThree.value[idx] || null;
    const valueText =
      leaderboard.metric === "duration"
        ? formatDuration(user?.total_duration_minutes)
        : formatEfficiency(user?.average_efficiency);
    return {
      rank,
      user: user
        ? {
            ...user,
            valueText,
          }
        : null,
      border: colors[idx],
    };
  });
});

const generatedAtText = computed(() => {
  if (!leaderboard.generatedAt) return "—";
  return dayjs(leaderboard.generatedAt).format("YYYY-MM-DD HH:mm:ss");
});

const rangeText = computed(() => {
  if (!leaderboard.range) return "—";
  return `${formatDate(leaderboard.range.start)} 至 ${formatDate(leaderboard.range.end)}`;
});

const trendChartData = computed(() => leaderboard.userDetail?.daily_trend ?? []);

const categoryChartData = computed(() => {
  const categories = leaderboard.userDetail?.categories?.main;
  if (!categories || !Array.isArray(categories.labels) || !Array.isArray(categories.data)) return [];
  return categories.labels.map((label: string, idx: number) => ({
    name: label,
    hours: Number(categories.data[idx]) || 0,
  }));
});

const detailSummary = computed<DetailSummary>(() => {
  const summary = leaderboard.userDetail?.summary;
  if (!summary) {
    return {
      totalHours: '--',
      averageEfficiency: '--',
      averagePerDay: '--',
      activeDays: '--',
    };
  }
  const totalMinutes = Number(summary.total_duration_minutes ?? 0);
  const totalHours = totalMinutes / 60;
  const activeDays = Number(summary.days_active ?? 0);
  const averagePerDay = activeDays > 0 ? totalHours / activeDays : 0;
  return {
    totalHours: `${totalHours.toFixed(2)} 小时`,
    averageEfficiency:
      summary.average_efficiency !== null && summary.average_efficiency !== undefined
        ? Number(summary.average_efficiency).toFixed(2)
        : '--',
    averagePerDay: `${averagePerDay.toFixed(2)} 小时/天`,
    activeDays: `${activeDays} 天`,
  };
});

function formatDuration(minutes: number | null | undefined) {
  if (!minutes) return "0 分钟";
  if (minutes < 60) return `${minutes} 分钟`;
  const hours = minutes / 60;
  return `${hours.toFixed(2)} 小时`;
}

function formatEfficiency(value: number | null | undefined) {
  if (value === null || value === undefined) return "—";
  return `${Number(value).toFixed(2)}`;
}

function formatDate(value: string | null | undefined) {
  if (!value) return "—";
  return dayjs(value).format("YYYY-MM-DD");
}

async function openDetail(row: any) {
  detailVisible.value = true;
  try {
    await leaderboard.fetchUserStats(row.user_id);
    if (!leaderboard.userDetail) {
      ElMessage.info("该用户暂未公开详细数据");
    }
  } catch (error) {
    detailVisible.value = false;
    ElMessage.warning("无法获取该用户的公开数据");
  }
}

function closeDetail() {
  detailVisible.value = false;
  leaderboard.userDetail = null;
}

async function handleJoin() {
  joinLoading.value = true;
  try {
    await leaderboard.join();
  } finally {
    joinLoading.value = false;
  }
}

async function handleLeave() {
  leaveLoading.value = true;
  try {
    await leaderboard.leave();
  } finally {
    leaveLoading.value = false;
  }
}
</script>

<style scoped lang="scss">
.leaderboard-view {
  padding: 20px clamp(16px, 3vw, 32px) 32px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  background: transparent;
}

.leaderboard-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
  background: transparent;
  padding: 6px 0 10px;

  .segment-group {
    display: inline-flex;
    align-items: center;
    gap: 10px;

    .seg-label {
      color: #475569;
      font-weight: 600;
      font-size: 0.95rem;
    }
  }

  .segmented {
    display: inline-flex;
    background: #f1f3f5;
    border-radius: 999px;
    padding: 4px;
    gap: 4px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65);
  }

  .seg-btn {
    border: none;
    background: transparent;
    padding: 10px 16px;
    border-radius: 999px;
    font-size: 14px;
    font-weight: 700;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 90px;
    box-shadow: none;
  }

  .seg-btn.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 8px 22px rgba(15, 23, 42, 0.12);
  }

  .exit-link {
    border: none;
    background: rgba(248, 250, 252, 0.9);
    border-radius: 12px;
    padding: 10px 12px;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);

    &:hover {
      color: #111827;
      background: #ffffff;
    }
  }
}

.join-alert {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 12px;
  border: 1px solid rgba(199, 210, 254, 0.6);
  background: rgba(238, 242, 255, 0.4);
  backdrop-filter: blur(10px);
}

.join-alert__body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.card {
  background: rgba(255, 255, 255, 0.42);
  border-radius: 14px;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.35);
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  position: relative;
  backdrop-filter: blur(14px);

  &::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: #2563eb;
    border-radius: 14px 14px 0 0;
    opacity: 0.6;
    pointer-events: none;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;
    padding: 18px 22px;
    border-bottom: 1px solid #e5e7eb;

    h2 {
      margin: 0;
      font-size: 1.2rem;
      font-weight: 600;
      color: #111827;
    }

    .card-subtitle {
      margin: 6px 0 0;
      color: #6b7280;
      font-size: 0.85rem;
    }
  }
}

.leaderboard-table {
  cursor: pointer;
  border-top: none;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
  padding: 12px 22px 20px;
}

.podium-card {
  background: rgba(255, 255, 255, 0.6);
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.8);
  padding: 18px 20px 12px;
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
}

.podium-header {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 12px;

  h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 700;
    color: #0f172a;
  }

  p {
    margin: 0;
    color: #6b7280;
    font-size: 0.9rem;
  }
}

.podium-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  align-items: end;
}

.podium-slot {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(248, 250, 252, 0.88));
  border-radius: 16px;
  padding: 12px;
  text-align: center;
  position: relative;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  min-height: 140px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 6px;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;

  &.empty {
    cursor: default;
  }

  &:hover:not(.empty) {
    transform: translateY(-2px);
    box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
  }
}

.podium-slot.empty {
  opacity: 0.6;
}

.podium-slot.pos-1 {
  min-height: 170px;
}

.avatar-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  margin: 0 auto;
  border: 3px solid #facc15;
  background: #fff;
  display: grid;
  place-items: center;
  position: relative;
  box-shadow: 0 10px 24px rgba(250, 204, 21, 0.22);
}

.podium-slot.pos-2 .avatar-wrap {
  width: 64px;
  height: 64px;
  border-color: #c0c4ce;
  box-shadow: 0 8px 20px rgba(192, 196, 206, 0.2);
}

.podium-slot.pos-3 .avatar-wrap {
  width: 64px;
  height: 64px;
  border-color: #f97316;
  box-shadow: 0 8px 20px rgba(249, 115, 22, 0.2);
}

.crown {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 18px;
}

.avatar-text {
  font-weight: 800;
  color: #111827;
  font-size: 22px;
}

.podium-name {
  font-weight: 700;
  color: #0f172a;
  font-size: 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tag-me {
  background: rgba(99, 102, 241, 0.15);
  color: #4f46e5;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
}

.podium-value {
  font-size: 15px;
  font-weight: 700;
  color: #475569;
}

.podium-rank {
  font-size: 13px;
  color: #cbd5e1;
  font-weight: 700;
}

.list-card {
  margin-top: 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 18px;
  border: 1px solid rgba(226, 232, 240, 0.85);
  box-shadow: 0 18px 42px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.list-header {
  padding: 18px 20px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;

  h3 {
    margin: 0;
    font-size: 1.05rem;
    font-weight: 700;
    color: #0f172a;
  }

  p {
    margin: 4px 0 0;
    color: #6b7280;
    font-size: 0.9rem;
  }
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 14px 16px 6px;
}

.rank-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.8);
  transition: background 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.rank-item:hover {
  background: rgba(241, 245, 249, 0.9);
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.9);
}

.rank-left {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.rank-no {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #e2e8f0;
  display: grid;
  place-items: center;
  font-weight: 700;
  color: #334155;
  flex-shrink: 0;
}

.user-block {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}

.user-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid #e5e7eb;
  display: grid;
  place-items: center;
  font-weight: 800;
  color: #111827;
  flex-shrink: 0;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08);
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.user-name {
  font-weight: 700;
  color: #0f172a;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.user-sub {
  color: #94a3b8;
  font-size: 0.88rem;
}

.rank-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-value {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
}

.metric-sub {
  color: #94a3b8;
  font-size: 0.85rem;
}

.detail-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .detail-header {
    h3 {
      margin: 0;
      font-size: 1.4rem;
      font-weight: 600;
      color: #111827;
    }

    p {
      margin: 6px 0 0;
      color: #6b7280;
      font-size: 0.85rem;
    }
  }
}

.detail-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;

  .metric {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 12px 14px;
    border: 1px solid rgba(255, 255, 255, 0.32);
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.35);
    backdrop-filter: blur(10px);

    .label {
      color: #475569;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
    }

    .value {
      font-size: 1.1rem;
      font-weight: 600;
      color: #1f2937;
    }
  }
}

.mini-table {
  border-radius: 8px;
  overflow: hidden;
}

@media (max-width: 768px) {
  .leaderboard-view {
    padding: 16px;
  }

  .header {
    flex-direction: column;
    align-items: flex-start;
  }

  .card {
    padding: 12px;
  }
}
</style>
