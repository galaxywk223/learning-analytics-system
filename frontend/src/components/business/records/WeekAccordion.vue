<!-- 周折叠面板组件 -->
<template>
  <el-collapse
    :model-value="activeWeeks"
    @update:model-value="$emit('update:activeWeeks', $event)"
    class="weeks-accordion"
  >
    <el-collapse-item
      v-for="week in weeks"
      :key="`${week.year}-${week.week_num}`"
      :name="`${week.year}-${week.week_num}`"
    >
      <!-- 周标题 -->
      <template #title>
        <div class="week-header">
          <span class="week-icon">📅</span>
          <span class="week-title">
            {{ week.year }} 年 - 第 {{ week.week_num }} 周
          </span>
          <el-tag type="info" size="small">
            周平均效率: {{ Number(week.efficiency).toFixed(2) }}
          </el-tag>
        </div>
      </template>

      <!-- 每周的每一天 -->
      <div class="week-days">
        <DayCard
          v-for="day in week.days"
          :key="day.date"
          :day="day"
          :expanded-notes="expandedNotes"
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
});

// Emits
defineEmits([
  "add-record",
  "toggle-notes",
  "edit-record",
  "delete-record",
  "update:activeWeeks",
]);
</script>

<style scoped lang="scss">
.weeks-accordion {
  :deep(.el-collapse-item) {
    margin-bottom: 0.75rem;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    overflow: hidden;
    background: white;
  }

  :deep(.el-collapse-item__header) {
    height: 52px;
    line-height: 52px;
    padding: 0 1.25rem;
    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
    font-size: 16px;
    border-bottom: none;

    &:hover {
      background: linear-gradient(135deg, #667eea25 0%, #764ba225 100%);
    }
  }

  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
  }

  :deep(.el-collapse-item__content) {
    padding: 0;
  }

  .week-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    font-size: 16px;

    .week-icon {
      font-size: 24px;
      flex-shrink: 0;
    }

    .week-title {
      font-weight: 600;
      color: #1f2937;
      flex: 1;
      font-size: 16px;
    }

    .el-tag {
      flex-shrink: 0;
      height: 28px;
      line-height: 26px;
      padding: 0 12px;
      font-size: 14px;
      font-weight: 500;
    }
  }

  .week-days {
    padding: 0.75rem;
  }
}
</style>
