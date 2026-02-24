<!-- 专注计时器显示组件 -->
<template>
  <div class="timer-display" :class="{ 'timer-active': isActive }">
    <div class="time-circle">
      <svg class="progress-ring" :width="ringSize" :height="ringSize">
        <circle
          class="progress-ring-bg outer"
          :cx="center"
          :cy="center"
          :r="outerRadius"
          fill="none"
          stroke-width="10"
        />
        <circle
          class="progress-ring-circle outer"
          :cx="center"
          :cy="center"
          :r="outerRadius"
          fill="none"
          stroke-width="10"
          :stroke-dasharray="outerCircumference"
          :stroke-dashoffset="outerProgressOffset"
        />
        <circle
          class="progress-ring-bg inner"
          :cx="center"
          :cy="center"
          :r="innerRadius"
          fill="none"
          stroke-width="6"
        />
        <circle
          class="progress-ring-circle inner"
          :cx="center"
          :cy="center"
          :r="innerRadius"
          fill="none"
          stroke-width="6"
          :stroke-dasharray="innerCircumference"
          :stroke-dashoffset="innerProgressOffset"
        />
      </svg>
      <div class="time-text">
        <span class="time-value">{{ formattedTime }}</span>
        <span class="time-label">{{ timeLabel }}</span>
        <span class="time-hint">{{ progressHint }}</span>
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
const ringSize = 300;
const center = ringSize / 2;
const outerRadius = center - 14;
const innerRadius = center - 34;
const outerCircumference = 2 * Math.PI * outerRadius;
const innerCircumference = 2 * Math.PI * innerRadius;

const innerCycleSeconds = 60 * 60; // 内环：每 60 分钟一圈
const outerCycleSeconds = 12 * 60 * 60; // 外环：每 12 小时一圈

function calcCycleOffset(elapsed, cycle, circumference) {
  if (elapsed <= 0) {
    return circumference;
  }
  const remainder = elapsed % cycle;
  const progress = remainder === 0 ? 1 : remainder / cycle;
  return circumference - progress * circumference;
}

const innerProgressOffset = computed(() => {
  return calcCycleOffset(
    props.elapsedSeconds,
    innerCycleSeconds,
    innerCircumference,
  );
});

const outerProgressOffset = computed(() => {
  return calcCycleOffset(
    props.elapsedSeconds,
    outerCycleSeconds,
    outerCircumference,
  );
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

const progressHint = computed(() => {
  return "内环 1h · 外环 12h";
});
</script>

<style scoped lang="scss">
.timer-display {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
  position: relative;
  min-height: 320px; /* Adjusted height */

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
        transition: stroke 0.3s ease;

        &.outer {
          stroke: var(--surface-soft);
        }

        &.inner {
          stroke: var(--surface-card-strong);
        }
      }

      &-circle {
        stroke-linecap: round;
        transition: stroke 0.3s ease;

        &.outer {
          stroke: var(--color-primary);
          transition:
            stroke-dashoffset 0.25s ease,
            stroke 0.3s ease,
            filter 0.3s ease;

          [data-theme="cyberpunk"] & {
            filter: drop-shadow(0 0 5px var(--color-primary));
          }
        }

        &.inner {
          stroke: var(--color-accent);
          transition:
            stroke-dashoffset 0.2s linear,
            stroke 0.3s ease,
            filter 0.3s ease;

          [data-theme="cyberpunk"] & {
            filter: drop-shadow(0 0 6px var(--color-accent));
          }
        }
      }
    }

    .time-text {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 68%;
      padding: 0 6px;

      .time-value {
        /* 预留圆环内安全边距，避免数字与内环重叠 */
        font-size: clamp(1.75rem, 5.8vw, 2.45rem);
        font-weight: 700;
        color: var(--color-text-heading); /* Use theme variable */
        letter-spacing: 0.03em;
        font-family: "SFMono-Regular", "JetBrains Mono", monospace;
        line-height: 1;
        transition: color 0.3s ease, text-shadow 0.3s ease;
        max-width: 100%;
        text-align: center;
        white-space: nowrap;
        margin-bottom: 0.25rem; /* Slight optical adjustment */

        [data-theme="cyberpunk"] & {
          text-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
        }
      }

      .time-label {
        font-size: 0.85rem;
        color: var(--color-text-muted); /* Use theme variable */
        margin-top: 0.5rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        transition: color 0.3s ease;
      }

      .time-hint {
        margin-top: 0.4rem;
        font-size: 0.72rem;
        color: var(--color-text-muted);
        letter-spacing: 0.05em;
      }
    }
  }

  &.timer-active {
    .progress-ring-circle.outer {
      stroke: var(--color-accent);
      [data-theme="cyberpunk"] & {
        filter: drop-shadow(0 0 8px var(--color-accent));
      }
    }

    .progress-ring-circle.inner {
      stroke: var(--color-primary-dark);
      [data-theme="cyberpunk"] & {
        filter: drop-shadow(0 0 8px var(--color-primary-dark));
      }
    }
  }
}
</style>
