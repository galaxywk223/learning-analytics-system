<!-- 日期卡片组件 -->
<template>
  <el-card class="day-card" shadow="hover">
    <!-- 日期卡片头部 -->
    <template #header>
      <div class="day-card-header">
        <span class="date-badge">
          <span class="weekday-icon">{{ getWeekdayIcon(day.date) }}</span>
          {{ formatDate(day.date) }} (周{{ getWeekday(day.date) }})
        </span>

        <!-- 进度条 -->
        <div
          class="daily-progress-container"
          :title="`今日总时长: ${day.total_duration} 分钟`"
        >
          <el-progress
            :percentage="Math.min(100, (day.total_duration / 840) * 100)"
            :show-text="false"
            :stroke-width="8"
            :color="getProgressColor(day.total_duration)"
          />
        </div>

        <span class="total-duration-text">
          <Icon icon="lucide:clock" class="clock-icon" />
          {{ (day.total_duration / 60).toFixed(1) }}h
        </span>

        <el-tag type="success" size="small">
          日效率: {{ Number(day.efficiency).toFixed(2) }}
        </el-tag>

        <!-- 快速添加按钮 -->
        <el-button
          circle
          size="small"
          @click.stop="$emit('add-record', day.date)"
          title="为今天添加记录"
        >
          <Icon icon="lucide:plus" />
        </el-button>
      </div>
    </template>

    <!-- 日志表格 -->
    <LogTable
      :logs="day.logs"
      :expanded-notes="expandedNotes"
      @toggle-notes="$emit('toggle-notes', $event)"
      @edit-record="$emit('edit-record', $event)"
      @delete-record="$emit('delete-record', $event)"
    />
  </el-card>
</template>

<script setup>
import { Icon } from "@iconify/vue";
import LogTable from "./LogTable.vue";

// Props
defineProps({
  day: {
    type: Object,
    required: true,
  },
  expandedNotes: {
    type: Array,
    default: () => [],
  },
});

// Emits
defineEmits(["add-record", "toggle-notes", "edit-record", "delete-record"]);

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
};

// 获取星期几
const getWeekday = (dateStr) => {
  const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
  const date = new Date(dateStr);
  return weekdays[date.getDay()];
};

// 获取星期几的图标
const getWeekdayIcon = (dateStr) => {
  const icons = ["🌞", "🌙", "🔥", "⚡", "🌟", "💫", "🎯"];
  const date = new Date(dateStr);
  return icons[date.getDay()];
};

// 获取进度条颜色
const getProgressColor = (duration) => {
  const percentage = (duration / 840) * 100;
  if (percentage >= 80) return "#10b981"; // green
  if (percentage >= 50) return "#667eea"; // purple
  if (percentage >= 30) return "#fbbf24"; // yellow
  return "#ef4444"; // red
};
</script>

<style scoped lang="scss">
.day-card {
  margin-bottom: 0.75rem;
  border: 1px solid #e5e7eb;
  border-radius: 8px;

  :deep(.el-card__header) {
    padding: 12px 18px;
    background: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
  }

  :deep(.el-card__body) {
    padding: 0;
  }

  .day-card-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;

    .date-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-weight: 600;
      color: #1f2937;
      font-size: 15px;
      min-width: 190px;

      .weekday-icon {
        font-size: 24px;
      }
    }

    .daily-progress-container {
      flex: 1;
      min-width: 100px;
      max-width: 200px;

      :deep(.el-progress__text) {
        display: none;
      }
    }

    .total-duration-text {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      font-weight: 600;
      color: #374151;
      font-size: 15px;
      min-width: 60px;

      .clock-icon {
        width: 18px;
        height: 18px;
      }
    }

    .el-tag {
      height: 28px;
      line-height: 26px;
      padding: 0 12px;
      font-size: 14px;
      font-weight: 500;
    }

    .el-button {
      width: 36px;
      height: 36px;
      padding: 0;
      font-size: 18px;

      :deep(.iconify) {
        width: 18px;
        height: 18px;
      }
    }
  }
}
</style>
