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
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  padding: 0 1.2rem;
  transition: transform 0.2s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.2s ease;
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
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
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
  /* Purple Gradient */
  background: linear-gradient(135deg, #7C73FF 0%, #5856D6 100%);
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(88, 86, 214, 0.3);

  &:hover {
    background: linear-gradient(135deg, #8E86FF 0%, #6A67E6 100%);
    box-shadow: 0 12px 24px rgba(88, 86, 214, 0.4);
  }
}

:deep(.pause-btn) {
  background: linear-gradient(135deg, #FFD60A 0%, #FF9F0A 100%);
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(255, 159, 10, 0.3);

  &:hover {
    background: linear-gradient(135deg, #FFE033 0%, #FFB333 100%);
  }
}

:deep(.stop-btn) {
  background: linear-gradient(135deg, #FF453A 0%, #FF3B30 100%);
  color: #ffffff;
  box-shadow: 0 8px 20px rgba(255, 59, 48, 0.3);

  &:hover {
    background: linear-gradient(135deg, #FF6961 0%, #FF5E55 100%);
  }
}

:deep(.secondary-btn),
:deep(.cancel-btn) {
  background: rgba(118, 118, 128, 0.12);
  color: #000000;
  box-shadow: none;
  backdrop-filter: blur(10px);

  &:hover {
    background: rgba(118, 118, 128, 0.24);
  }
}

.return-link {
  background: transparent;
  border: none;
  color: #8E8E93;
  font-weight: 500;
  font-size: 17px;
  cursor: pointer;
  text-decoration: none;
  padding: 8px 16px;
  transition: color 0.2s ease;
  margin-top: 4px;

  &:hover {
    color: #000000;
  }
}

@media (max-width: 768px) {
  .button-stack {
    max-width: 100%;
  }
}
</style>
