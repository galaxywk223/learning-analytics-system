<!-- 专注控制按钮组件 -->
<template>
  <div class="focus-controls">
    <template v-if="!isRunning && !isPaused">
      <div class="button-stack">
        <el-button
          class="control-btn primary-btn"
          size="large"
          :icon="VideoPlay"
          :loading="loading"
          @click="$emit('start')"
        >
          专注计时
        </el-button>
        <button class="return-link" @click="$emit('go-back')">返回</button>
      </div>
    </template>

    <template v-else-if="isRunning">
      <div class="button-stack">
        <el-button
          class="control-btn pause-btn"
          size="large"
          :icon="VideoPause"
          @click="$emit('pause')"
        >
          暂停
        </el-button>
        <el-button
          class="control-btn stop-btn"
          size="large"
          :icon="VideoPlay"
          @click="$emit('stop')"
        >
          结束专注
        </el-button>
      </div>
    </template>

    <template v-else-if="isPaused">
      <div class="button-stack">
        <el-button
          class="control-btn resume-btn"
          size="large"
          :icon="VideoPlay"
          @click="$emit('resume')"
        >
          继续
        </el-button>
        <el-button
          class="control-btn stop-btn"
          size="large"
          :icon="VideoPlay"
          @click="$emit('stop')"
        >
          结束专注
        </el-button>
        <el-button
          class="control-btn cancel-btn"
          size="large"
          plain
          @click="$emit('cancel')"
        >
          放弃记录
        </el-button>
      </div>
    </template>
  </div>
</template>

<script setup>
import { VideoPlay, VideoPause } from "@element-plus/icons-vue";

// Props
defineProps({
  isRunning: {
    type: Boolean,
    default: false,
  },
  isPaused: {
    type: Boolean,
    default: false,
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

// Emits
defineEmits(["start", "pause", "resume", "stop", "cancel", "go-back"]);
</script>

<style scoped lang="scss">
.focus-controls {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-top: 1.5rem;
}

.button-stack {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: center;
}

:deep(.control-btn) {
  width: 100%;
  height: 56px; /* iOS Large Button Height */
  font-size: 19px; /* Larger text */
  font-weight: 600;
  border-radius: 999px; /* Pill shape */
  border: none;
  box-shadow: var(--box-shadow-card);
  padding: 0 1.2rem;
  transition:
    transform 0.2s cubic-bezier(0.25, 0.8, 0.25, 1),
    box-shadow 0.2s ease;
  margin-left: 0 !important;
  letter-spacing: 0.5px;

  .el-button__content {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }

  .el-icon {
    font-size: 22px;
  }

  &:hover {
    transform: scale(1.02);
    box-shadow: var(--box-shadow-hover);
  }

  &:active {
    transform: scale(0.96);
  }
}

/* 清除 Element Plus 相邻按钮默认左间距 */
:deep(.button-stack .el-button + .el-button) {
  margin-left: 0 !important;
}

:deep(.primary-btn),
:deep(.resume-btn) {
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-dark) 100%
  );
  color: var(--color-text-inverse);
  box-shadow: var(--box-shadow-card);

  &:hover {
    background: linear-gradient(
      135deg,
      var(--color-primary-dark) 0%,
      var(--color-primary) 100%
    );
    box-shadow: var(--box-shadow-hover);
  }
}

:deep(.pause-btn) {
  background: linear-gradient(
    135deg,
    var(--color-warning) 0%,
    var(--color-accent) 100%
  );
  color: var(--color-text-inverse);
  box-shadow: var(--box-shadow-card);

  &:hover {
    box-shadow: var(--box-shadow-hover);
  }
}

:deep(.stop-btn) {
  background: linear-gradient(
    135deg,
    var(--color-error) 0%,
    var(--color-error) 100%
  );
  color: var(--color-text-inverse);
  box-shadow: var(--box-shadow-card);

  &:hover {
    box-shadow: var(--box-shadow-hover);
  }
}

:deep(.secondary-btn),
:deep(.cancel-btn) {
  background: var(--surface-card-muted);
  color: var(--color-text-heading);
  box-shadow: none;

  &:hover {
    background: var(--surface-soft);
  }
}

.return-link {
  background: transparent;
  border: none;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 17px;
  cursor: pointer;
  text-decoration: none;
  padding: 8px 16px;
  transition: color 0.2s ease;
  margin-top: 4px;

  &:hover {
    color: var(--color-text-heading);
  }
}

@media (max-width: 768px) {
  .button-stack {
    max-width: 100%;
  }
}
</style>
