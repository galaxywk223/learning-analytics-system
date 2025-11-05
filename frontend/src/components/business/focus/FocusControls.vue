<!-- 专注控制按钮组件 -->
<template>
  <div class="focus-controls">
    <template v-if="!isRunning && !isPaused">
      <div class="button-stack">
        <el-button
          class="control-btn primary-btn"
          size="large"
          :icon="VideoPlay"
          @click="$emit('start')"
          :loading="loading"
        >
          开始专注
        </el-button>
        <el-button
          class="control-btn secondary-btn"
          size="large"
          @click="$emit('go-back')"
        >
          返回
        </el-button>
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
  margin-top: 0.75rem;
}

.button-stack {
  width: 100%;
  max-width: 360px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

:deep(.control-btn) {
  width: 100%;
  height: 48px;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 16px;
  border: none;
  box-shadow: none;
  padding: 0 1.2rem;
  transition: transform 0.18s ease, background-color 0.18s ease;
  margin-left: 0 !important;

  .el-button__content {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
  }

  .el-icon {
    font-size: 1.05rem;
  }

  &:hover {
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
}

/* 清除 Element Plus 相邻按钮默认左间距，防止纵向堆叠时右偏 */
:deep(.button-stack .el-button + .el-button) {
  margin-left: 0 !important;
}

:deep(.primary-btn),
:deep(.resume-btn) {
  background: linear-gradient(135deg, rgba(98, 106, 230, 0.96), rgba(129, 140, 248, 0.96));
  color: var(--color-text-light);
  border: 1px solid rgba(98, 106, 230, 0.9);

  &:hover {
    background: linear-gradient(135deg, rgba(79, 86, 220, 1), rgba(129, 140, 248, 1));
  }
}

:deep(.pause-btn) {
  background: linear-gradient(135deg, rgba(250, 189, 73, 0.95), rgba(245, 158, 11, 0.95));
  color: var(--color-text-light);
  border: 1px solid rgba(245, 158, 11, 0.85);

  &:hover {
    background: linear-gradient(135deg, rgba(234, 147, 6, 0.98), rgba(245, 158, 11, 0.98));
  }
}

:deep(.stop-btn) {
  background: linear-gradient(135deg, rgba(248, 113, 113, 0.92), rgba(244, 114, 182, 0.9));
  color: var(--color-text-light);
  border: 1px solid rgba(248, 113, 113, 0.75);

  &:hover {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(236, 72, 153, 0.95));
  }
}

:deep(.secondary-btn),
:deep(.cancel-btn) {
  background: var(--surface-card-muted);
  color: var(--color-text-heading);
  border: 1px solid var(--stroke-soft);

  &:hover {
    background: var(--surface-card);
  }
}

@media (max-width: 768px) {
  .button-stack {
    max-width: 100%;
  }
}
</style>
