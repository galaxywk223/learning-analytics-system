<template>
  <div class="dashboard-view">
    <section class="overview-card">
      <div class="overview-copy">
        <h1>{{ dashboardHeadline }}</h1>
        <div class="overview-quote">
          <div class="overview-quote__header">
            <span>今日格言</span>
            <button
              type="button"
              class="overview-quote__refresh"
              :disabled="mottoRefreshing || mottoStore.loading"
              title="换一句"
              @click="refreshHeroMotto()"
            >
              <Icon
                icon="lucide:refresh-cw"
                :class="{ 'is-spinning': mottoRefreshing || mottoStore.loading }"
              />
            </button>
          </div>
          <p>{{ activeMotto?.content || FALLBACK_MOTTO }}</p>
        </div>
      </div>

      <div class="overview-main">
        <span class="overview-main__label">今日学习时长</span>
        <strong>{{ todayFocusDuration }}</strong>
        <p>{{ latestRecordStatus }}</p>
      </div>
    </section>

    <section class="kpi-grid">
      <article class="kpi-card">
        <span class="kpi-card__label">累计记录</span>
        <strong>{{ totalRecordsLabel }}</strong>
        <p>持续沉淀每一次练习与复盘</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-card__label">下个目标</span>
        <strong>{{ countdownDays }} 天</strong>
        <p>{{ countdownTitle }}</p>
      </article>
      <article class="kpi-card">
        <span class="kpi-card__label">里程碑</span>
        <strong>{{ milestoneCount }}</strong>
        <p>已记录的重要节点</p>
      </article>
    </section>

    <section class="content-grid">
      <router-link to="/charts" class="panel-card panel-card--chart">
        <div class="panel-card__header">
          <div>
            <h2>统计分析</h2>
            <p>近 7 天学习时长</p>
          </div>
          <Icon icon="lucide:arrow-up-right" />
        </div>

        <div v-if="hasBarData" class="chart-preview">
          <div class="bar-chart">
            <div
              v-for="(height, idx) in barHeights"
              :key="idx"
              class="bar"
              :title="`${barLabels[idx]} · ${barValues[idx]} 分钟`"
            >
              <div class="bar-fill" :style="{ height: `${height}%` }"></div>
              <span class="bar-label">{{ barLabels[idx] }}</span>
            </div>
          </div>
        </div>
        <div v-else class="panel-empty">
          <span>最近 7 天还没有学习时长</span>
          <p>开始记录后，这里会显示你的每日投入趋势。</p>
        </div>
      </router-link>

      <router-link to="/records" class="panel-card panel-card--records">
        <div class="panel-card__header">
          <div>
            <h2>学习记录</h2>
            <p>最近 5 条记录</p>
          </div>
          <Icon icon="lucide:arrow-up-right" />
        </div>

        <div v-if="recentRecords.length" class="records-list">
          <div class="records-list__head">
            <span>项目</span>
            <span>日期</span>
            <span>时长</span>
          </div>
          <div
            v-for="item in recentRecords"
            :key="item.id"
            class="records-list__row"
          >
            <div class="records-list__title">
              <strong :title="item.title">{{ item.title || "未命名记录" }}</strong>
              <small :title="item.subcategory">{{ item.subcategory }}</small>
            </div>
            <span>{{ formatRecordDate(item.date) }}</span>
            <span>{{ item.duration || "暂无时长" }}</span>
          </div>
        </div>

        <div v-else class="panel-empty">
          <span>暂无记录</span>
          <p>开始一段新的学习记录后，这里会展示最近内容。</p>
        </div>
      </router-link>
    </section>
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
const activeMotto = ref<any>(null);
const mottoRefreshing = ref(false);
const FALLBACK_MOTTO = "去设置里添加几条格言，这里会随机展示。";

const formatDuration = (minutes) => {
  if (!minutes) return "0 分钟";
  const hrs = Math.floor(minutes / 60);
  const mins = minutes % 60;
  if (hrs && mins) return `${hrs}:${mins.toString().padStart(2, "0")}`;
  return `${minutes} 分钟`;
};

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

function selectRandomMotto(excludeCurrent = false) {
  const items = Array.isArray(mottoStore.items) ? mottoStore.items : [];
  if (!items.length) {
    activeMotto.value = { id: null, content: FALLBACK_MOTTO };
    return;
  }

  const pool =
    excludeCurrent && items.length > 1 && activeMotto.value?.id
      ? items.filter((item: any) => item.id !== activeMotto.value.id)
      : items;

  const next = pool[Math.floor(Math.random() * pool.length)];
  activeMotto.value = next || { id: null, content: FALLBACK_MOTTO };
}

async function refreshHeroMotto(forceFetch = false) {
  if (mottoRefreshing.value) return;
  mottoRefreshing.value = true;
  try {
    if (forceFetch || !mottoStore.items.length) {
      await mottoStore.fetch();
    }
    selectRandomMotto(true);
  } catch (error) {
    console.error("Failed to refresh motto", error);
    activeMotto.value = { id: null, content: FALLBACK_MOTTO };
  } finally {
    mottoRefreshing.value = false;
  }
}

onMounted(async () => {
  await dashboardStore.fetchSummary();
  await fetchRecentRecords();
  await refreshHeroMotto(true);
});

onActivated(async () => {
  await dashboardStore.fetchSummary();
  await fetchRecentRecords();
  await refreshHeroMotto(true);
});

const sortedRecords = computed(() => {
  const records = allRecords.value || [];
  return records.slice().sort((a, b) => {
    const da = dayjs(a.log_date || a.date || a.created_at || 0);
    const db = dayjs(b.log_date || b.date || b.created_at || 0);
    return db.valueOf() - da.valueOf();
  });
});

const recentRecords = computed(() =>
  sortedRecords.value.slice(0, 5).map((item: any) => ({
    id: item.id ?? item.record_id ?? Math.random(),
    title:
      item.task || item.title || item.content || item.category || "未命名记录",
    date: item.log_date || item.date || item.created_at || item.updated_at,
    duration: item.actual_duration
      ? `${item.actual_duration} 分钟`
      : item.duration
        ? formatDuration(Math.round(item.duration))
        : "0 分钟",
    mood: item.mood,
    subcategory: item.subcategory?.name || item.subcategory_name || "培养阶段",
  })),
);

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

const dashboardHeadline = computed(() => {
  const hour = dayjs().hour();

  if (hour >= 5 && hour < 11) {
    return "早上好，开始今天的学习";
  }

  if (hour >= 11 && hour < 14) {
    return "中午好，继续稳步推进";
  }

  if (hour >= 14 && hour < 18) {
    return "下午好，把进度再往前推一点";
  }

  if (hour >= 18 && hour < 24) {
    return "晚上好，欢迎回来";
  }

  return "夜深了，收个尾也很好";
});

const totalRecordsLabel = computed(
  () => dashboardStore.summary?.total_records ?? 0,
);

const countdownDays = computed(() => {
  const next = dashboardStore.summary?.next_countdown;
  return Math.max(next?.remaining_days ?? 0, 0);
});

const countdownTitle = computed(
  () => dashboardStore.summary?.next_countdown?.title || "暂时没有倒计时",
);

const milestoneCount = computed(
  () => dashboardStore.summary?.milestones_count ?? 0,
);

const latestRecordStatus = computed(() => {
  const latest = dashboardStore.summary?.latest_record_date;
  return latest
    ? `最近记录于 ${dayjs(latest).format("MM/DD")}`
    : "最近还没有记录";
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
      "YYYY-MM-DD",
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

const hasBarData = computed(() =>
  barValues.value.some((value: number) => value > 0),
);

const barHeights = computed(() => {
  const data = barValues.value;
  const max = Math.max(...data, 0);
  if (max <= 0) {
    return data.map(() => 0);
  }
  return data.map((v: number) => (v > 0 ? Math.max(14, Math.round((v / max) * 100)) : 0));
});
</script>

<style scoped lang="scss">
@use "@/styles/views/dashboard/DashboardView.module.scss";
</style>
