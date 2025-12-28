<!-- 日期卡片组件 -->
<template>
  <el-card class="day-card" shadow="hover">
    <!-- 日期卡片头部 -->
    <template #header>
      <div class="day-card-header">
        <span class="date-badge">
          <span class="weekday-icon emoji-icon">{{
            getWeekdayIcon(day.date)
          }}</span>
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

        <span class="daily-eff">
          日效率 {{ Number(day.efficiency).toFixed(2) }}
        </span>

        <!-- 快速添加按钮 -->
        <el-button
          circle
          size="small"
          title="为今天添加记录"
          @click.stop="$emit('add-record', day.date)"
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
  border: none;
  background: transparent;
  box-shadow: none;
  margin-bottom: 0;

  :deep(.el-card__header) {
    padding: 0 0 12px 0;
    background: transparent;
    border-bottom: none;
  }

  :deep(.el-card__body) {
    padding: 0;
  }

  .day-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;

    .date-badge {
      font-size: 17px;
      font-weight: 600;
      color: #000;
      display: flex;
      align-items: center;
      gap: 6px;

      .weekday-icon {
        font-size: 18px;
      }
    }

    .daily-progress-container {
      flex: 1;
      margin: 0 16px;
      max-width: 120px; /* Smaller progress bar */

      :deep(.el-progress-bar__outer) {
        background-color: rgba(118, 118, 128, 0.12);
      }
    }

    .total-duration-text {
      font-size: 17px;
      color: #8e8e93;
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 4px;
      margin-right: 12px;

      .clock-icon {
        width: 16px;
        height: 16px;
      }
    }

    .daily-eff {
      font-size: 17px;
      color: #8e8e93;
      font-weight: 500;
      margin-right: 12px;
    }

    .el-button {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: #007aff;
      color: white;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;

      &:hover {
        background: #0062cc;
      }

      :deep(.iconify) {
        width: 16px;
        height: 16px;
      }
    }
  }
}
</style>
