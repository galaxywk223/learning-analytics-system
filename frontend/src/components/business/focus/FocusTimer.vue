<!-- 专注计时器显示组件 -->
<template>
  <div class="timer-display" :class="{ 'timer-active': isActive }">
    <div class="time-circle">
      <svg class="progress-ring" width="280" height="280">
        <circle
          class="progress-ring-bg"
          cx="140"
          cy="140"
          r="130"
          fill="none"
          stroke-width="8"
        />
        <circle
          class="progress-ring-circle"
          cx="140"
          cy="140"
          r="130"
          fill="none"
          stroke-width="8"
          :stroke-dasharray="circumference"
          :stroke-dashoffset="progressOffset"
        />
      </svg>
      <div class="time-text">
        <span class="time-value">{{ formattedTime }}</span>
        <span class="time-label">{{ timeLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

// Props
const props = defineProps({
  elapsedSeconds: {
    type: Number,
    default: 0,
  },
  isActive: {
    type: Boolean,
    default: false,
  },
});

// 计算属性
const circumference = 2 * Math.PI * 130;

const progressOffset = computed(() => {
  // 以1小时为一个周期
  const maxSeconds = 3600; // 1小时
  const progress = Math.min(props.elapsedSeconds / maxSeconds, 1);
  return circumference - progress * circumference;
});

const formattedTime = computed(() => {
  const hours = Math.floor(props.elapsedSeconds / 3600);
  const minutes = Math.floor((props.elapsedSeconds % 3600) / 60);
  const seconds = props.elapsedSeconds % 60;
  return [hours, minutes, seconds].map((unit) => unit.toString().padStart(2, "0")).join(":");
});

const timeLabel = computed(() => {
  return "时 : 分 : 秒";
});
</script>

<style scoped lang="scss">
.timer-display {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;

  .time-circle {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;

    .progress-ring {
      transform: rotate(-90deg);

      &-bg {
        stroke: rgba(129, 140, 248, 0.18);
        stroke-width: 5;
      }

      &-circle {
        stroke: #6366f1;
        stroke-width: 5;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.25s ease, stroke 0.25s ease;
      }
    }

    .time-text {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .time-value {
        font-size: clamp(2.4rem, 4vw, 2.8rem);
        font-weight: 600;
        color: #1f2937;
        letter-spacing: 0.08em;
        font-family: "SFMono-Regular", "JetBrains Mono", monospace;
      }

      .time-label {
        font-size: 0.85rem;
        color: #64748b;
        margin-top: 0.35rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
      }
    }
  }

  &.timer-active {
    .progress-ring-circle {
      stroke: #4c51bf;
    }
  }
}
</style>
