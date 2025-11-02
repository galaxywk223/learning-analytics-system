<!-- 专注控制按钮组件 -->
<template>
  <div class="focus-controls">
    <template v-if="!isRunning && !isPaused">
      <el-button
        type="primary"
        size="large"
        :icon="VideoPlay"
        @click="$emit('start')"
        :loading="loading"
      >
        开始专注
      </el-button>
      <el-button size="large" @click="$emit('go-back')"> 返回 </el-button>
    </template>

    <template v-else-if="isRunning">
      <el-button
        type="warning"
        size="large"
        :icon="VideoPause"
        @click="$emit('pause')"
      >
        暂停
      </el-button>
      <el-button
        type="danger"
        size="large"
        :icon="VideoPlay"
        @click="$emit('stop')"
      >
        结束专注
      </el-button>
    </template>

    <template v-else-if="isPaused">
      <el-button
        type="success"
        size="large"
        :icon="VideoPlay"
        @click="$emit('resume')"
      >
        继续
      </el-button>
      <el-button
        type="danger"
        size="large"
        :icon="VideoPlay"
        @click="$emit('stop')"
      >
        结束专注
      </el-button>
      <el-button type="info" size="large" plain @click="$emit('cancel')">
        放弃记录
      </el-button>
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
  display: flex;
  justify-content: center;
  gap: 0.875rem;
  margin: 1.5rem 0 0.5rem;
  flex-wrap: wrap;

  :deep(.el-button) {
    min-width: 130px;
    height: 44px;
    font-size: 0.95rem;
    font-weight: 500;
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.3);
    background: rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    transition: all 0.2s;

    &:hover {
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.5);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }

    &:active {
      transform: translateY(0);
    }

    // Primary 按钮
    &.el-button--primary {
      background: rgba(102, 126, 234, 0.3);
      border-color: rgba(102, 126, 234, 0.5);

      &:hover {
        background: rgba(102, 126, 234, 0.5);
        border-color: rgba(102, 126, 234, 0.7);
      }
    }

    // Warning 按钮
    &.el-button--warning {
      background: rgba(245, 158, 11, 0.3);
      border-color: rgba(245, 158, 11, 0.5);

      &:hover {
        background: rgba(245, 158, 11, 0.5);
        border-color: rgba(245, 158, 11, 0.7);
      }
    }

    // Danger 按钮
    &.el-button--danger {
      background: rgba(239, 68, 68, 0.3);
      border-color: rgba(239, 68, 68, 0.5);

      &:hover {
        background: rgba(239, 68, 68, 0.5);
        border-color: rgba(239, 68, 68, 0.7);
      }
    }

    // Success 按钮
    &.el-button--success {
      background: rgba(16, 185, 129, 0.3);
      border-color: rgba(16, 185, 129, 0.5);

      &:hover {
        background: rgba(16, 185, 129, 0.5);
        border-color: rgba(16, 185, 129, 0.7);
      }
    }

    // Info/Plain 按钮
    &.el-button--info,
    &.is-plain {
      background: rgba(255, 255, 255, 0.05);
      border-color: rgba(255, 255, 255, 0.2);

      &:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: rgba(255, 255, 255, 0.3);
      }
    }
  }
}
</style>
