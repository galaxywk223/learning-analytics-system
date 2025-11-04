<template>
  <div class="leaderboard-view">
    <section class="header">
      <div class="title-group">
        <h1>📈 学习排行榜</h1>
        <p class="subtitle">实时查看全站学习时长与效率榜单，点选用户了解详情</p>
      </div>
      <div class="controls">
        <div class="control-group">
          <span class="label">周期</span>
          <div class="btn-group">
            <button
              v-for="option in periodOptions"
              :key="option.value"
              :class="['btn', leaderboard.period === option.value && 'active']"
              @click="leaderboard.setPeriod(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <div class="control-group">
          <span class="label">榜单</span>
          <div class="btn-group">
            <button
              v-for="option in metricOptions"
              :key="option.value"
              :class="['btn', leaderboard.metric === option.value && 'active']"
              @click="leaderboard.setMetric(option.value)"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
      </div>
    </section>

    <el-alert
      v-if="!leaderboard.optedIn"
      type="info"
      show-icon
      class="join-alert"
    >
      <template #title>未加入排行榜</template>
      <template #default>
        <div class="join-alert__body">
          <span>加入后即可出现在榜单中，并分享你的学习数据（时长与效率）。</span>
          <el-button type="primary" size="small" @click="handleJoin" :loading="joinLoading">
            立即加入
          </el-button>
        </div>
      </template>
    </el-alert>

    <div class="card">
      <div class="card-header">
        <div>
          <h2>{{ currentMetricLabel }} · {{ currentPeriodLabel }}</h2>
          <p class="card-subtitle">
            更新时间：{{ generatedAtText }} · 数据范围：{{ rangeText }}
          </p>
        </div>
        <div class="card-actions" v-if="leaderboard.optedIn">
          <el-button text type="danger" size="small" @click="handleLeave" :loading="leaveLoading">
            退出排行榜
          </el-button>
        </div>
      </div>

      <el-table
        v-loading="leaderboard.loading"
        :data="tableData"
        border
        stripe
        size="large"
        class="leaderboard-table"
        @row-click="openDetail"
      >
        <el-table-column prop="rank" label="排名" width="90" align="center" />
        <el-table-column prop="username" label="用户名">
          <template #default="{ row }">
            <span>
              {{ row.username }}
              <el-tag v-if="row.isSelf" type="success" size="small" effect="plain">我</el-tag>
            </span>
          </template>
        </el-table-column>
        <el-table-column :label="currentMetricLabel" align="center">
          <template #default="{ row }">
            <span v-if="leaderboard.metric === 'duration'">
              {{ formatDuration(row.total_duration_minutes) }}
            </span>
            <span v-else>
              {{ formatEfficiency(row.average_efficiency) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="sessions" label="记录次数" width="120" align="center" />
        <el-table-column prop="last_activity" label="最近活动" width="160" align="center">
          <template #default="{ row }">
            {{ row.last_activity ? formatDate(row.last_activity) : "—" }}
          </template>
        </el-table-column>
      </el-table>

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
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ElMessage } from "element-plus";
import { useLeaderboardStore } from "@/stores/modules/leaderboard";
import dayjs from "dayjs";
import UserTrendChart from "@/components/business/leaderboard/UserTrendChart.vue";
import UserCategoryChart from "@/components/business/leaderboard/UserCategoryChart.vue";

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
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;

  .title-group {
    h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 700;
    }

    .subtitle {
      margin: 4px 0 0;
      color: #6b7280;
    }
  }

  .controls {
    display: flex;
    gap: 16px;
    flex-wrap: wrap;

    .control-group {
      display: flex;
      align-items: center;
      gap: 12px;

      .label {
        color: #6b7280;
        font-size: 14px;
      }

      .btn-group {
        display: inline-flex;
        background: #f5f5f5;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
        border: 1px solid #e0e0e0;
      }
    }
  }
}

.btn {
  border: none;
  background: transparent;
  padding: 6px 14px;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  font-weight: 500;
  transition: all 0.2s ease;

  &:hover {
    background: #ede9fe;
    color: #5b21b6;
  }

  &.active {
    background: #5b21b6;
    color: #fff;
  }
}

.join-alert {
  display: flex;
  justify-content: space-between;
  align-items: center;
}


.join-alert__body {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 12px;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }

    .card-subtitle {
      margin: 4px 0 0;
      color: #6b7280;
      font-size: 13px;
    }
  }
}

.leaderboard-table {
  cursor: pointer;
}

.table-footer {
  display: flex;
  justify-content: flex-end;
}

.detail-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;

  .detail-header {
    h3 {
      margin: 0;
      font-size: 22px;
      font-weight: 600;
    }

    p {
      margin: 4px 0 0;
      color: #6b7280;
      font-size: 13px;
    }
  }
}

.detail-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;

  .metric {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .label {
      color: #6b7280;
      font-size: 13px;
    }

    .value {
      font-size: 20px;
      font-weight: 600;
      color: #111827;
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
