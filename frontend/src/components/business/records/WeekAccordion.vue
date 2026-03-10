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
</script>

<style scoped lang="scss">
.weeks-accordion {
  :deep(.el-collapse) {
    border: none;
  }

  :deep(.el-collapse-item) {
    margin-bottom: 1.5rem;
    border: none;
    background: transparent;

    /* Remove default shadow/border */
    box-shadow: none;
  }

  :deep(.el-collapse-item__header) {
    height: auto;
    line-height: normal;
    padding: 0 0 0.5rem 0;
    background: transparent;
    border-bottom: none;
    margin-bottom: 0.5rem;

    /* Disable default arrow rotation if we hide it, but we hide it below */
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
    align-items: baseline;
    width: 100%;

    .week-title {
      font-size: 22px;
      font-weight: 700;
      color: var(--color-text-heading);
      letter-spacing: -0.5px;
      display: flex;
      align-items: center;
      gap: 8px;

      .emoji-icon {
        font-size: 20px;
      }
    }

    .week-eff {
      font-size: 17px;
      color: var(--color-text-secondary);
      font-weight: 500;
    }
  }

  .week-days {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
}
</style>
