<!-- 日期卡片组件 -->
<template>
  <el-card class="day-card" shadow="hover">
    <!-- 日期卡片头部 -->
    <template #header>
      <div class="day-card-header">
        <div class="day-title-group">
          <span class="date-badge">
            <span class="weekday-icon emoji-icon">{{
              getWeekdayIcon(day.date)
            }}</span>
            {{ formatDate(day.date) }} (周{{ getWeekday(day.date) }})
          </span>
          <span class="day-log-count">{{ day.logs.length }} 条记录</span>
        </div>

        <div
          class="daily-progress-panel"
          :title="`今日总时长: ${day.total_duration} 分钟`"
        >
          <div class="progress-meta">
            <span class="progress-label">今日投入</span>
            <strong>{{ formatHours(day.total_duration) }}</strong>
          </div>
          <el-progress
            :percentage="Math.min(100, (day.total_duration / 840) * 100)"
            :show-text="false"
            :stroke-width="8"
            :color="getProgressColor(day.total_duration)"
          />
        </div>

        <div class="day-metrics">
          <span class="metric-pill">
            <Icon icon="lucide:clock-3" class="metric-icon" />
            {{ formatHours(day.total_duration) }}
          </span>
          <span class="metric-pill accent">
            <Icon icon="lucide:gauge" class="metric-icon" />
            日效率 {{ Number(day.efficiency).toFixed(2) }}
          </span>
          <el-button
            circle
            size="small"
            title="为今天添加记录"
            @click.stop="$emit('add-record', day.date)"
          >
            <Icon icon="lucide:plus" />
          </el-button>
        </div>
      </div>
    </template>

    <!-- 日志表格 -->
    <LogTable
      :logs="day.logs"
      :expanded-notes="expandedNotes"
      :color-seed="colorSeed"
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
  colorSeed: {
    type: String,
    default: "",
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

const formatHours = (duration) => `${(duration / 60).toFixed(1)}h`;

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
  border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 8%, transparent) 0%, transparent 32%),
    linear-gradient(
      180deg,
      color-mix(in srgb, var(--surface-card) 88%, rgba(255, 255, 255, 0.03)) 0%,
      color-mix(in srgb, var(--surface-card-strong) 96%, rgba(15, 23, 42, 0.1)) 100%
    );
  box-shadow:
    0 18px 36px -30px rgba(15, 23, 42, 0.42),
    inset 0 1px 0 rgba(255, 255, 255, 0.04);
  border-radius: 24px;
  margin-bottom: 0;

  :deep(.el-card__header) {
    padding: 18px 20px 16px;
    background: transparent;
    border-bottom: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
  }

  :deep(.el-card__body) {
    padding: 16px 18px 18px;
  }

  .day-card-header {
    display: grid;
    align-items: center;
    grid-template-columns: minmax(200px, auto) minmax(200px, 1fr) auto;
    gap: 16px;

    .day-title-group {
      display: flex;
      flex-direction: column;
      gap: 10px;
      min-width: 0;
    }

    .date-badge {
      font-size: 17px;
      font-weight: 700;
      color: var(--color-text-heading);
      display: flex;
      align-items: center;
      gap: 8px;

      .weekday-icon {
        font-size: 20px;
      }
    }

    .day-log-count {
      width: fit-content;
      padding: 6px 10px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--color-primary) 10%, rgba(255, 255, 255, 0.03));
      border: 1px solid color-mix(in srgb, var(--color-primary) 10%, transparent);
      color: var(--color-text-secondary);
      font-size: 13px;
      font-weight: 600;
    }

    .daily-progress-panel {
      min-width: 0;
      padding: 12px 14px;
      border-radius: 18px;
      background: color-mix(in srgb, var(--surface-card-strong) 90%, rgba(255, 255, 255, 0.02));
      border: 1px solid color-mix(in srgb, var(--color-primary) 8%, var(--stroke-soft));
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);

      .progress-meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        gap: 12px;

        .progress-label {
          font-size: 12px;
          font-weight: 600;
          letter-spacing: 0.04em;
          color: var(--color-text-secondary);
        }

        strong {
          font-size: 16px;
          color: var(--color-text-heading);
        }
      }

      :deep(.el-progress-bar__outer) {
        background-color: var(--color-bg-hover);
      }
    }

    .day-metrics {
      display: flex;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      flex-wrap: wrap;
    }

    .metric-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--surface-card-strong) 86%, rgba(255, 255, 255, 0.03));
      border: 1px solid color-mix(in srgb, var(--color-primary) 8%, var(--stroke-soft));
      color: var(--color-text-secondary);
      font-size: 14px;
      font-weight: 600;

      .metric-icon {
        width: 14px;
        height: 14px;
        color: var(--color-primary);
      }

      &.accent {
        color: var(--color-text-heading);
      }
    }

    .el-button {
      width: 34px;
      height: 34px;
      border-radius: 50%;
      background: var(--color-primary);
      color: white;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0;

      &:hover {
        background: var(--color-primary-dark);
      }

      :deep(.iconify) {
        width: 16px;
        height: 16px;
      }
    }
  }
}

@media (max-width: 960px) {
  .day-card {
    .day-card-header {
      grid-template-columns: 1fr;
      align-items: stretch;
    }

    .day-metrics {
      justify-content: flex-start;
    }
  }
}

@media (max-width: 640px) {
  .day-card {
    border-radius: 20px;

    :deep(.el-card__header) {
      padding: 16px;
    }

    :deep(.el-card__body) {
      padding: 14px;
    }

    .day-card-header .date-badge {
      font-size: 16px;
    }

    .day-card-header .metric-pill {
      font-size: 13px;
    }
  }
}
</style>
