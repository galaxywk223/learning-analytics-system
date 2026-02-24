<!-- 专注计时器显示组件 -->
<template>
  <div class="timer-display" :class="{ 'timer-active': isActive }">
    <div class="time-circle">
      <svg class="progress-ring" :width="ringSize" :height="ringSize">
        <circle
          class="progress-ring-bg"
          :cx="center"
          :cy="center"
          :r="radius"
          fill="none"
          stroke-width="8"
        />
        <circle
          class="progress-ring-circle"
          :cx="center"
          :cy="center"
          :r="radius"
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
// Reduced size to fit inside circle better
const ringSize = 300; // Reduced from 340
const center = ringSize / 2;
const radius = center - 15; // Padding for stroke
const circumference = 2 * Math.PI * radius;

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
        stroke: var(--surface-card-strong); /* Use theme variable */
        stroke-width: 8;
        transition: stroke 0.3s ease;
      }

      &-circle {
        stroke: var(--color-primary); /* Use theme variable */
        stroke-width: 8;
        stroke-linecap: round;
        transition:
          stroke-dashoffset 0.25s ease,
          stroke 0.3s ease,
          filter 0.3s ease;
          
        [data-theme='cyberpunk'] & { 
          filter: drop-shadow(0 0 5px var(--color-primary)); 
        }
      }
    }

    .time-text {
      position: absolute;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      width: 100%; /* Ensure text centers properly */

      .time-value {
        /* Responsive font size based on container */
        font-size: clamp(2rem, 7vw, 3rem); 
        font-weight: 700;
        color: var(--color-text-heading); /* Use theme variable */
        letter-spacing: 0.05em;
        font-family: "SFMono-Regular", "JetBrains Mono", monospace;
        line-height: 1;
        transition: color 0.3s ease, text-shadow 0.3s ease;
        max-width: 75%; /* More restrictive width */
        text-align: center;
        white-space: nowrap;
        margin-bottom: 0.25rem; /* Slight optical adjustment */
        
        [data-theme='cyberpunk'] & {
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
    }
  }

  &.timer-active {
    .progress-ring-circle {
      stroke: var(--color-accent); /* Use theme variable for active state */
      
      [data-theme='cyberpunk'] & { 
        filter: drop-shadow(0 0 8px var(--color-accent)); 
      }
    }
  }
}
</style>
