<!-- 周折叠面板组件 -->
<template>
  <el-collapse
    :collapse-transition="false"
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
          <span class="week-title">
            <span class="emoji-icon" aria-hidden="true">📅</span>
            <span>{{ week.year }} 年 · 第 {{ week.week_num }} 周</span>
          </span>
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
    border: none;
    border-radius: 18px;
    overflow: hidden;
    background: #ffffff;
    box-shadow: 0 16px 40px rgba(15, 23, 42, 0.08);
  }

  :deep(.el-collapse-item__header) {
    height: 44px;
    line-height: 44px;
    padding: 0 1.2rem;
    background: transparent;
    font-size: 14px;
    border-bottom: 1px solid #f0f1f5;
    color: #6b7280;

    .el-collapse-item__arrow {
      display: none;
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
    gap: 10px;
    width: 100%;
    font-size: 14px;
    color: #6b7280;
    font-weight: 600;

    .week-title {
      font-weight: 700;
      color: #374151;
      display: inline-flex;
      align-items: center;
      gap: 8px;
    }

    .week-eff {
      font-weight: 500;
      color: #9ca3af;
    }
  }

  .week-days {
    padding: 0.75rem;
    background: #ffffff;
  }
}
</style>
