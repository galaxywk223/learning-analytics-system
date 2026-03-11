<!-- 周折叠面板组件 -->
<template>
  <el-collapse
    :collapse-transition="false"
    :model-value="activeWeeks"
    class="weeks-accordion"
    @update:model-value="$emit('update:activeWeeks', $event)"
  >
    <el-collapse-item
      v-for="week in weeks"
      :key="`${week.year}-${week.week_num}`"
      :name="`${week.year}-${week.week_num}`"
    >
      <!-- 周标题 -->
      <template #title>
        <div class="week-header">
          <div class="week-title-block">
            <span class="week-title">
              <span class="emoji-icon" aria-hidden="true">📅</span>
              <span>{{ week.year }} 年 · 第 {{ week.week_num }} 周</span>
            </span>
            <div class="week-meta">
              <span class="week-chip">{{ getWeekRecordCount(week) }} 条记录</span>
              <span class="week-chip">{{ formatWeekDuration(week) }}</span>
            </div>
          </div>
          <span class="week-eff">
            平均效率 {{ Number(week.efficiency).toFixed(2) }}
          </span>
        </div>
      </template>

      <!-- 每周的每一天 -->
      <div class="week-days">
        <DayCard
          v-for="day in week.days"
          :key="day.date"
          :day="day"
          :expanded-notes="expandedNotes"
          :color-seed="colorSeed"
          @add-record="$emit('add-record', $event)"
          @toggle-notes="$emit('toggle-notes', $event)"
          @edit-record="$emit('edit-record', $event)"
          @delete-record="$emit('delete-record', $event)"
        />
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup>
import DayCard from "./DayCard.vue";

// Props
defineProps({
  weeks: {
    type: Array,
    default: () => [],
  },
  activeWeeks: {
    type: Array,
    default: () => [],
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
defineEmits([
  "add-record",
  "toggle-notes",
  "edit-record",
  "delete-record",
  "update:activeWeeks",
]);

const getWeekRecordCount = (week) =>
  week.days.reduce((count, day) => count + (day.logs?.length || 0), 0);

const formatWeekDuration = (week) => {
  const totalMinutes = week.days.reduce(
    (sum, day) => sum + (day.total_duration || 0),
    0,
  );
  if (!totalMinutes) return "0h";
  return `${(totalMinutes / 60).toFixed(totalMinutes >= 600 ? 0 : 1)}h`;
};
</script>

<style scoped lang="scss">
.weeks-accordion {
  :deep(.el-collapse) {
    border: none;
  }

  :deep(.el-collapse-item) {
    margin-bottom: 1.25rem;
    padding: 24px;
    border-radius: 28px;
    border: 1px solid color-mix(in srgb, var(--color-primary) 10%, var(--stroke-soft));
    background:
      radial-gradient(circle at top right, color-mix(in srgb, var(--color-primary) 10%, transparent) 0%, transparent 28%),
      linear-gradient(
        180deg,
        color-mix(in srgb, var(--surface-card) 92%, rgba(255, 255, 255, 0.03)) 0%,
        color-mix(in srgb, var(--surface-card-strong) 96%, rgba(15, 23, 42, 0.12)) 100%
      );
    box-shadow:
      0 22px 44px -34px rgba(15, 23, 42, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  :deep(.el-collapse-item__header) {
    height: auto;
    line-height: normal;
    padding: 0 0 1rem 0;
    background: transparent;
    border-bottom: none;
    margin-bottom: 0.5rem;

    .el-collapse-item__arrow {
      display: none;
    }
  }

  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
    background: transparent;
  }

  :deep(.el-collapse-item__content) {
    padding: 0;
    background: transparent;
  }

  .week-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 18px;
    width: 100%;
  }

  .week-title-block {
    display: flex;
    flex-direction: column;
    gap: 12px;
    min-width: 0;

    .week-title {
      font-size: 24px;
      font-weight: 800;
      color: var(--color-text-heading);
      letter-spacing: -0.04em;
      display: flex;
      align-items: center;
      gap: 10px;

      .emoji-icon {
        font-size: 22px;
      }
    }
  }

  .week-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
  }

  .week-chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 12px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--color-primary) 10%, rgba(255, 255, 255, 0.03));
    border: 1px solid color-mix(in srgb, var(--color-primary) 12%, transparent);
    color: var(--color-text-secondary);
    font-size: 13px;
    font-weight: 600;
  }

  .week-eff {
    flex-shrink: 0;
    padding: 10px 16px;
    border-radius: 999px;
    background: linear-gradient(
      135deg,
      color-mix(in srgb, var(--color-primary) 14%, rgba(255, 255, 255, 0.03)) 0%,
      color-mix(in srgb, var(--color-primary-dark) 10%, rgba(255, 255, 255, 0.02)) 100%
    );
    border: 1px solid color-mix(in srgb, var(--color-primary) 16%, transparent);
    font-size: 15px;
    color: var(--color-text-heading);
    font-weight: 700;
  }

  .week-days {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }
}

@media (max-width: 768px) {
  .weeks-accordion {
    :deep(.el-collapse-item) {
      padding: 18px;
      border-radius: 24px;
    }

    .week-header {
      flex-direction: column;
      align-items: flex-start;
    }

    .week-title-block .week-title {
      font-size: 21px;
    }

    .week-eff {
      align-self: flex-start;
    }
  }
}
</style>
