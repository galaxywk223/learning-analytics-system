<template>
  <div
    v-if="!expired"
    :id="`countdown-${event.id}`"
    class="countdown-card"
    :class="statusClass"
  >
    <div class="card-header">
      <span class="event-title">{{ event.title }}</span>
    </div>
    <div class="card-body">
      <div class="progress-ring-container">
        <svg
          class="progress-ring-svg"
          width="120"
          height="120"
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
              <stop offset="0%" style="stop-color: #2563eb; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #3b82f6; stop-opacity: 1"
              />
            </linearGradient>
            <linearGradient
              id="gradient-warning"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" style="stop-color: #fcd34d; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #f59e0b; stop-opacity: 1"
              />
            </linearGradient>
            <linearGradient
              id="gradient-urgent"
              x1="0%"
              y1="0%"
              x2="100%"
              y2="100%"
            >
              <stop offset="0%" style="stop-color: #fb7185; stop-opacity: 1" />
              <stop
                offset="100%"
                style="stop-color: #dc2626; stop-opacity: 1"
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
    <div class="card-footer">
      <span class="target-date">目标: {{ beijingString }}</span>
      <div class="actions">
        <el-button
          link
          size="small"
          :title="'编辑'"
          @click.stop="$emit('edit')"
        >
          <Icon icon="lucide:edit-3" />
        </el-button>
        <el-button
          link
          size="small"
          type="danger"
          :title="'删除'"
          @click.stop="$emit('delete')"
        >
          <Icon icon="lucide:trash-2" />
        </el-button>
      </div>
    </div>
  </div>
  <div v-else class="expired-card">
    <div class="icon-wrapper">✔</div>
    <h5 class="expired-title">{{ event.title }}</h5>
    <p class="text-muted">完成于 {{ beijingDateOnly }}</p>
    <div class="actions">
      <el-button link size="small" :title="'编辑'" @click="$emit('edit')">
        <Icon icon="lucide:edit-3" />
      </el-button>
      <el-button
        link
        size="small"
        type="danger"
        :title="'删除'"
        @click="$emit('delete')"
      >
        <Icon icon="lucide:trash-2" />
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from "vue";
import { Icon } from "@iconify/vue";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
dayjs.extend(utc);
dayjs.extend(timezone);
const props = defineProps({
  event: { type: Object, required: true },
  expired: { type: Boolean, default: false },
});
defineEmits(["edit", "delete"]);
const progressCircle = ref(null);
let timer = null;

// 派生状态（若后端未给 card_status，则按剩余天数推断）
const derivedStatus = computed(() => {
  if (props.expired) return "expired";
  const status = props.event.card_status;
  if (status === "warning" || status === "urgent" || status === "normal") {
    return status;
  }
  const target = beijingDate.value ? beijingDate.value.valueOf() : null;
  if (target) {
    const diffDays = (target - Date.now()) / (1000 * 60 * 60 * 24);
    if (diffDays <= 3) return "urgent";
    if (diffDays <= 7) return "warning";
  }
  return "normal";
});

const statusClass = computed(() => `status-${derivedStatus.value}`);
const strokeId = computed(() => {
  switch (derivedStatus.value) {
    case "warning":
      return "gradient-warning";
    case "urgent":
      return "gradient-urgent";
    default:
      return "gradient-normal";
  }
});
const strokeColor = computed(() => {
  switch (derivedStatus.value) {
    case "warning":
      return "#f59e0b";
    case "urgent":
      return "#dc2626";
    case "expired":
      return "#9ca3af";
    default:
      return "#2563eb";
  }
});

// 固定以北京时区显示
const beijingDate = computed(() => {
  if (!props.event.target_datetime_utc) return null;
  // 后端给的是 UTC ISO，先按 UTC 解析，再转 Asia/Shanghai
  return dayjs.utc(props.event.target_datetime_utc).tz("Asia/Shanghai");
});
const beijingString = computed(() =>
  beijingDate.value ? beijingDate.value.format("YYYY-MM-DD HH:mm") : "",
);
const beijingDateOnly = computed(() =>
  beijingDate.value ? beijingDate.value.format("YYYY-MM-DD") : "",
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
  let p = Number(props.event.progress_percentage);
  if (!Number.isFinite(p)) {
    const target = beijingDate.value ? beijingDate.value.valueOf() : null;
    const created = props.event.created_at_utc
      ? dayjs.utc(props.event.created_at_utc).valueOf()
      : null;
    if (target && created && target > created) {
      const span = target - created;
      p = ((Date.now() - created) / span) * 100;
    } else {
      p = 100; // 缺省时显示满圈颜色
    }
  }
  p = Math.min(100, Math.max(0, p));
  if (p === 0) p = 2; // 最小可见段
  const circle = progressCircle.value;
  const r = circle.r.baseVal.value;
  const circumference = 2 * Math.PI * r;
  const offset = circumference - (p / 100) * circumference;
  circle.style.strokeDasharray = `${circumference} ${circumference}`;
  circle.style.strokeDashoffset = offset;
  const strokeUrl = `url(#${strokeId.value})`;
  circle.setAttribute("stroke", strokeUrl);
  circle.style.stroke = strokeUrl;
  // 兜底纯色，避免渐变失效时变灰
  circle.style.setProperty("--fallback-stroke", strokeColor.value);
  circle.style.setProperty("strokeFallback", strokeColor.value);
}

onMounted(() => {
  setProgress();
  updateRemaining();
  timer = setInterval(() => {
    updateRemaining();
  }, 1000);
});
watch(
  () => [
    props.event.progress_percentage,
    props.event.target_datetime_utc,
    props.event.created_at_utc,
  ],
  () => setProgress(),
  { deep: false },
);
onBeforeUnmount(() => {
  if (timer) clearInterval(timer);
});
</script>

<style scoped src="@/styles/views/countdown/countdown-item.scss"></style>
