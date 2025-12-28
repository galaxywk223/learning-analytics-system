<!-- 专注计时器显示组件 -->
<template>
  <div class="timer-display" :class="{ 'timer-active': isActive }">
    <div class="time-circle">
      <svg class="progress-ring" width="340" height="340">
        <circle
          class="progress-ring-bg"
          cx="170"
          cy="170"
          r="155"
          fill="none"
          stroke-width="8"
        />
        <circle
          class="progress-ring-circle"
          cx="170"
          cy="170"
          r="155"
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
const RADIUS = 155;
const circumference = 2 * Math.PI * RADIUS;

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
  return [hours, minutes, seconds]
    .map((unit) => unit.toString().padStart(2, "0"))
    .join(":");
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
  position: relative;
  min-height: 360px;

  &::before {
    display: none;
  }

  .time-circle {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;

    .progress-ring {
      transform: rotate(-90deg);

      &-bg {
        stroke: rgba(99, 102, 241, 0.12);
        stroke-width: 12;
      }

      &-circle {
        stroke: #4f46e5;
        stroke-width: 12;
        stroke-linecap: round;
        transition:
          stroke-dashoffset 0.25s ease,
          stroke 0.25s ease;
      }
    }

    .time-text {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .time-value {
        font-size: clamp(2.8rem, 5.4vw, 3.4rem);
        font-weight: 700;
        color: #0f172a;
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
      stroke: #4338ca;
    }
  }
}
</style>
