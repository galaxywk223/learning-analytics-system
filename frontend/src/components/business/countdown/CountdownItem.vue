<template>
  <div
    class="countdown-card"
    :id="`countdown-${event.id}`"
    :class="statusClass"
    v-if="!expired"
  >
    <div class="card-header">
      <span class="event-title">{{ event.title }}</span>
      <div class="actions">
        <el-button link size="small" @click="$emit('edit')">编辑</el-button>
        <el-button link size="small" type="danger" @click="$emit('delete')"
          >删除</el-button
        >
      </div>
    </div>
    <div class="card-body">
      <div class="progress-ring-container">
        <svg
          class="progress-ring-svg"
          width="180"
          height="180"
          viewBox="0 0 120 120"
        >
          <defs>
            <linearGradient
              id="gradient-normal"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" style="stop-color: #667eea; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #764ba2; stop-opacity: 1"
              />
            </linearGradient>
            <linearGradient
              id="gradient-warning"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" style="stop-color: #f093fb; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #f5576c; stop-opacity: 1"
              />
            </linearGradient>
            <linearGradient
              id="gradient-urgent"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" style="stop-color: #fa709a; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #fee140; stop-opacity: 1"
              />
            </linearGradient>
          </defs>
          <circle
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke="#e6e6e6"
            stroke-width="12"
          />
          <circle
            ref="progressCircle"
            class="progress-ring-circle"
            cx="60"
            cy="60"
            r="54"
            fill="none"
            stroke-width="12"
          />
        </svg>
        <div class="progress-ring-text">
          <div class="days-remaining">{{ remaining.days }}</div>
          <div class="days-label">天</div>
        </div>
      </div>
      <div class="live-timer">{{ remaining.hms }}</div>
    </div>
    <div class="card-footer">目标: {{ beijingString }}</div>
  </div>
  <div v-else class="expired-card">
    <div class="icon-wrapper">✔</div>
    <h5 class="expired-title">{{ event.title }}</h5>
    <p class="text-muted">完成于 {{ beijingDateOnly }}</p>
    <div class="actions">
      <el-button link size="small" @click="$emit('edit')">查看/编辑</el-button>
      <el-button link size="small" type="danger" @click="$emit('delete')"
        >删除</el-button
      >
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from "vue";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
dayjs.extend(utc);
dayjs.extend(timezone);
const props = defineProps({
  event: { type: Object, required: true },
  expired: { type: Boolean, default: false },
});
const progressCircle = ref(null);
let timer = null;

// 固定以北京时区显示
const beijingDate = computed(() => {
  if (!props.event.target_datetime_utc) return null;
  // 后端给的是 UTC ISO，先按 UTC 解析，再转 Asia/Shanghai
  return dayjs.utc(props.event.target_datetime_utc).tz("Asia/Shanghai");
});
const beijingString = computed(() =>
  beijingDate.value ? beijingDate.value.format("YYYY-MM-DD HH:mm") : ""
);
const beijingDateOnly = computed(() =>
  beijingDate.value ? beijingDate.value.format("YYYY-MM-DD") : ""
);

// 已改用 dayjs 格式化，上面 computed 中完成

// 剩余时间对象
const remaining = ref({ days: 0, hms: "00:00:00" });

function updateRemaining() {
  if (!props.event.target_datetime_utc) return;
  const target = new Date(props.event.target_datetime_utc).getTime();
  const now = Date.now();
  let diff = target - now;
  if (diff <= 0) {
    remaining.value = { days: 0, hms: "00:00:00" };
    clearInterval(timer);
    timer = null;
    return;
  }
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));
  const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((diff % (1000 * 60)) / 1000);
  remaining.value = {
    days,
    hms: [hours, minutes, seconds]
      .map((n) => String(n).padStart(2, "0"))
      .join(":"),
  };
}

function setProgress() {
  if (!progressCircle.value) return;
  const p = props.event.progress_percentage ?? 0;
  const circle = progressCircle.value;
  const r = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (p / 100) * circumference;
  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = offset;
}

const statusClass = computed(() => {
  const status = props.event.card_status;
  if (!status || props.expired) return "status-expired";
  return `status-${status}`;
});

onMounted(() => {
  setProgress();
  updateRemaining();
  timer = setInterval(() => {
    updateRemaining();
  }, 1000);
});
onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped src="@/styles/views/countdown/countdown-item.scss"></style>
