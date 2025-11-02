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

  if (hours > 0) {
    return `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  } else {
    return `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;
  }
});

const timeLabel = computed(() => {
  const hours = Math.floor(props.elapsedSeconds / 3600);
  return hours > 0 ? "小时:分钟:秒" : "分钟:秒";
});
</script>

<style scoped lang="scss">
.timer-display {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 1.5rem 0;

  .time-circle {
    position: relative;
    display: flex;
    justify-content: center;
    align-items: center;

    .progress-ring {
      transform: rotate(-90deg);
      filter: drop-shadow(0 0 8px rgba(255, 255, 255, 0.1));

      &-bg {
        stroke: rgba(255, 255, 255, 0.15);
        stroke-width: 5;
      }

      &-circle {
        stroke: rgba(255, 255, 255, 0.8);
        stroke-width: 5;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.3s ease;
      }
    }

    .time-text {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;

      .time-value {
        font-size: 2.75rem;
        font-weight: 300;
        color: rgba(255, 255, 255, 0.95);
        font-family: "Courier New", monospace;
        letter-spacing: 0.1em;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
      }

      .time-label {
        font-size: 0.8rem;
        color: rgba(255, 255, 255, 0.6);
        margin-top: 0.5rem;
        letter-spacing: 0.05em;
      }
    }
  }

  &.timer-active {
    .progress-ring-circle {
      stroke: rgba(255, 255, 255, 0.95);
      animation: pulse 2s ease-in-out infinite alternate;
      filter: drop-shadow(0 0 12px rgba(255, 255, 255, 0.5));
    }
  }
}

@keyframes pulse {
  from {
    stroke-opacity: 0.8;
  }
  to {
    stroke-opacity: 1;
  }
}
</style>
