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
  justify-content: flex-start;
  flex-wrap: wrap;
  gap: 0.85rem;
  margin-top: 0.75rem;

  :deep(.el-button) {
    min-width: 136px;
    height: 46px;
    font-size: 0.95rem;
    font-weight: 600;
    border-radius: 12px;
    border: none;
    box-shadow: none;
    transition: background-color 0.2s ease, transform 0.2s ease;

    &:hover {
      transform: translateY(-1px);
    }

    &:active {
      transform: translateY(0);
    }
  }

  :deep(.el-button--primary) {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff;

    &:hover {
      background: linear-gradient(135deg, #5a5eea, #7c3aed);
    }
  }

  :deep(.el-button--warning) {
    background: #f59e0b;
    color: #fff;

    &:hover {
      background: #d97706;
    }
  }

  :deep(.el-button--danger) {
    background: #ef4444;
    color: #fff;

    &:hover {
      background: #dc2626;
    }
  }

  :deep(.el-button--success) {
    background: #10b981;
    color: #fff;

    &:hover {
      background: #0f9f6e;
    }
  }

  :deep(.el-button--info),
  :deep(.el-button.is-plain),
  :deep(.el-button:not([class*="el-button--"])) {
    background: #e2e8f0;
    color: #334155;

    &:hover {
      background: #cbd5f5;
    }
  }
}

@media (max-width: 768px) {
  .focus-controls {
    justify-content: center;
  }
}
</style>
