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

      <div v-if="!leaderboard.optedIn" class="join-banner">
        <div class="join-banner__left">
          <div class="join-icon">
            <Icon icon="lucide:sparkles" />
          </div>
          <div class="join-copy">
            <div class="join-eyebrow">未加入社区排行</div>
            <div class="join-title">同步学习数据，解锁上榜资格</div>
            <div class="join-sub">加入后即可展示时长与效率，与社区一起进步。</div>
          </div>
        </div>
        <div class="join-banner__actions">
          <el-button type="primary" size="large" @click="handleJoin" :loading="joinLoading">
            立即加入
          </el-button>
          <el-button link type="primary" size="large" @click="leaderboard.initialize()">刷新数据</el-button>
        </div>
      </div>

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
  padding: 24px clamp(16px, 3vw, 32px) 48px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  background: transparent;
  min-height: 100vh;
}

.leaderboard-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  background: transparent;
  padding: 0;

  .segment-group {
    display: inline-flex;
    align-items: center;
    gap: 12px;

    .seg-label {
      color: #8e8e93;
      font-weight: 600;
      font-size: 13px;
    }
  }

  .segmented {
    display: inline-flex;
    background: #e5e5ea; /* iOS System Gray 5 */
    border-radius: 999px;
    padding: 3px;
    gap: 2px;
  }

  .seg-btn {
    border: none;
    background: transparent;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 500;
    color: #000000;
    cursor: pointer;
    transition: all 0.2s ease;
    min-width: 72px;
    box-shadow: none;

    &:hover {
      color: #000000;
    }
  }

  .seg-btn.active {
    background: #ffffff;
    color: #000000;
    font-weight: 600;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12), 0 0 1px rgba(0,0,0,0.04);
  }

  .exit-link {
    border: none;
    background: rgba(255, 255, 255, 0.8);
    border-radius: 999px;
    padding: 8px 16px;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #ff3b30; /* iOS Red */
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 13px;
    font-weight: 600;
    margin-left: auto;

    &:hover {
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }
  }
}

.join-banner {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  padding: 24px 32px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(20px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.4);
}

.join-banner__left {
  display: flex;
  align-items: center;
  gap: 20px;
  min-width: 0;
}

.join-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  color: #ffffff;
  font-size: 24px;
  box-shadow: 0 8px 16px rgba(0, 122, 255, 0.25);
}

.join-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: #1c1c1e;
}

.join-eyebrow {
  font-size: 13px;
  font-weight: 600;
  color: #007AFF;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.join-title {
  font-size: 19px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}

.join-sub {
  font-size: 15px;
  color: #8e8e93;
}

.join-banner__actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.join-banner :deep(.el-button--primary) {
  border-radius: 999px;
  padding: 10px 24px;
  height: auto;
  font-weight: 600;
  font-size: 15px;
  background: #007AFF;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);
  
  &:hover {
    background: #0062cc;
  }
}

.join-banner :deep(.el-button.is-link) {
  font-weight: 600;
  color: #8e8e93;
  font-size: 15px;
  
  &:hover {
    color: #1c1c1e;
  }
}

.podium-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
}

.podium-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 20px;

  h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #1c1c1e;
    letter-spacing: -0.5px;
  }

  p {
    margin: 0;
    color: #8e8e93;
    font-size: 14px;
  }
}

.podium-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  align-items: end;
}

.podium-slot {
  background: #f9f9f9;
  border-radius: 20px;
  padding: 20px 16px;
  text-align: center;
  position: relative;
  min-height: 160px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 8px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid transparent;

  &.empty {
    cursor: default;
    opacity: 0.5;
    background: #f2f2f7;
  }

  &:hover:not(.empty) {
    transform: translateY(-4px);
    background: #ffffff;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
    border-color: rgba(0, 0, 0, 0.04);
  }
}

.podium-slot.pos-1 {
  min-height: 200px;
  background: linear-gradient(180deg, rgba(255, 215, 0, 0.05) 0%, rgba(255, 255, 255, 0) 100%);
  border: 1px solid rgba(255, 215, 0, 0.15);
}

.avatar-wrap {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  margin: 0 auto 8px;
  border: 4px solid #ffffff;
  background: #e5e5ea;
  display: grid;
  place-items: center;
  position: relative;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.podium-slot.pos-1 .avatar-wrap {
  width: 88px;
  height: 88px;
  border-color: #FFD700;
  box-shadow: 0 12px 32px rgba(255, 215, 0, 0.25);
}

.podium-slot.pos-2 .avatar-wrap {
  border-color: #C0C0C0;
  box-shadow: 0 8px 24px rgba(192, 192, 192, 0.25);
}

.podium-slot.pos-3 .avatar-wrap {
  border-color: #CD7F32;
  box-shadow: 0 8px 24px rgba(205, 127, 50, 0.25);
}

.crown {
  position: absolute;
  top: -24px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 32px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}

.avatar-text {
  font-weight: 700;
  color: #1c1c1e;
  font-size: 24px;
}

.podium-name {
  font-weight: 600;
  color: #1c1c1e;
  font-size: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.tag-me {
  background: #007AFF;
  color: #ffffff;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
}

.podium-value {
  font-size: 17px;
  font-weight: 800;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}

.podium-rank {
  font-size: 13px;
  color: #8e8e93;
  font-weight: 600;
  margin-top: 4px;
}

.list-card {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  overflow: hidden;
}

.list-header {
  padding: 20px 24px;
  border-bottom: 1px solid #f2f2f7;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;

  h3 {
    margin: 0;
    font-size: 17px;
    font-weight: 700;
    color: #1c1c1e;
  }

  p {
    margin: 4px 0 0;
    color: #8e8e93;
    font-size: 13px;
  }
}

.rank-list {
  display: flex;
  flex-direction: column;
  padding: 8px 16px 24px;
}

.rank-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  background: transparent;
  transition: all 0.2s ease;
  cursor: pointer;
  border-bottom: 1px solid #f2f2f7;

  &:last-child {
    border-bottom: none;
  }

  &:hover {
    background: #f9f9f9;
  }
}

.rank-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.rank-no {
  font-size: 17px;
  font-weight: 700;
  color: #8e8e93;
  width: 32px;
  text-align: center;
}

.user-block {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #e5e5ea;
  display: grid;
  place-items: center;
  font-weight: 600;
  color: #1c1c1e;
  font-size: 16px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.user-name {
  font-size: 15px;
  font-weight: 600;
  color: #1c1c1e;
  display: flex;
  align-items: center;
  gap: 8px;
}

.user-sub {
  font-size: 13px;
  color: #8e8e93;
}

.rank-right {
  text-align: right;
}

.metric-value {
  font-size: 17px;
  font-weight: 700;
  color: #1c1c1e;
  letter-spacing: -0.5px;
}

.metric-sub {
  font-size: 12px;
  color: #8e8e93;
  margin-top: 2px;
}

.table-footer {
  display: flex;
  justify-content: center;
  padding: 24px;
  border-top: 1px solid #f2f2f7;
}

// Drawer Styles
.detail-wrapper {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.detail-header {
  h3 {
    margin: 0;
    font-size: 24px;
    font-weight: 700;
    color: #1c1c1e;
  }
  
  p {
    margin: 4px 0 0;
    color: #8e8e93;
    font-size: 14px;
  }
}

.detail-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;

  :deep(.el-card) {
    border-radius: 16px;
    border: none;
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    background: #f9f9f9;
    
    .el-card__body {
      padding: 16px;
    }
  }

  .metric {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .label {
      font-size: 13px;
      color: #8e8e93;
      font-weight: 500;
    }

    .value {
      font-size: 18px;
      font-weight: 700;
      color: #1c1c1e;
    }
  }
}

@media (max-width: 768px) {
  .leaderboard-view {
    padding: 16px;
  }

  .join-banner {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
    padding: 24px;
  }

  .join-banner__left {
    flex-direction: column;
    text-align: center;
  }

  .join-banner__actions {
    justify-content: center;
    width: 100%;
    
    :deep(.el-button) {
      flex: 1;
    }
  }

  .podium-grid {
    gap: 8px;
  }

  .podium-slot {
    min-height: 120px;
    padding: 12px 8px;
  }

  .avatar-wrap {
    width: 48px;
    height: 48px;
  }
  
  .podium-slot.pos-1 .avatar-wrap {
    width: 64px;
    height: 64px;
  }

  .rank-item {
    padding: 12px;
  }
  
  .rank-left {
    gap: 12px;
  }
  
  .rank-no {
    width: 24px;
    font-size: 15px;
  }
}
</style>
```
