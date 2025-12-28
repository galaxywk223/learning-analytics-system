<template>
  <div class="ios-list-container">
    <div class="ios-list">
      <div
        v-for="log in logs"
        :key="log.id"
        class="ios-list-item"
        :class="`category-bg-${(log.subcategory?.category_id || 0) % 6}`"
      >
        <div class="item-content">
          <!-- 1. Time -->
          <div class="col-time">{{ log.time_slot }}</div>

          <!-- 2. Task & Category -->
          <div class="col-main">
            <span
              v-if="log.subcategory"
              class="category-dot"
              :class="`category-color-${(log.subcategory.category_id || 0) % 6}`"
            ></span>
            <span class="task-name" :title="log.task">{{ log.task }}</span>
            <span v-if="log.subcategory" class="category-tag">
              {{ log.subcategory.name }}
            </span>
            <!-- Notes Icon (Click to toggle) -->
            <span
              v-if="log.notes"
              class="notes-icon-wrapper"
              title="查看备注"
              @click.stop="$emit('toggle-notes', log.id)"
            >
              <Icon icon="lucide:message-square" class="notes-icon" />
            </span>
          </div>

          <!-- 3. Duration -->
          <div class="col-duration">{{ log.actual_duration }} min</div>

          <!-- 4. Actions (Hover/Right) -->
          <div class="col-actions">
            <el-button
              link
              size="small"
              class="action-btn"
              title="编辑"
              @click="$emit('edit-record', log)"
            >
              <Icon icon="lucide:pencil" />
            </el-button>
            <el-button
              link
              size="small"
              type="danger"
              class="action-btn delete"
              title="删除"
              @click="$emit('delete-record', log)"
            >
              <Icon icon="lucide:trash-2" />
            </el-button>
          </div>
        </div>

        <!-- Expanded Notes -->
        <div
          v-if="log.notes && expandedNotes.includes(log.id)"
          class="expanded-notes"
        >
          {{ log.notes }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";

defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  expandedNotes: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["toggle-notes", "edit-record", "delete-record"]);
</script>

<style scoped lang="scss">
.ios-list-container {
  width: 100%;
}

.ios-list {
  display: flex;
  flex-direction: column;
  gap: 8px; /* Reduced gap */
}

.ios-list-item {
  /* background: #ffffff;  Removed to allow category-bg classes to take effect */
  border-radius: 10px; /* Slightly smaller radius */
  padding: 8px 12px; /* Compact padding */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);

    .col-actions {
      opacity: 1;
    }
  }
}

.item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 28px; /* Fixed height for consistency */
}

/* 1. Time Column */
.col-time {
  font-size: 15px; /* Increased from 13px */
  color: #8e8e93;
  width: 110px; /* Increased width to accommodate larger font */
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* 2. Main Column (Task & Category) */
.col-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0; /* Enable truncation */

  .category-dot {
    width: 8px; /* Increased from 6px */
    height: 8px; /* Increased from 6px */
    border-radius: 50%;
    flex-shrink: 0;
  }

  .task-name {
    font-size: 17px; /* Increased from 15px */
    font-weight: 600;
    color: #000;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .category-tag {
    font-size: 13px; /* Increased from 11px */
    color: #8e8e93;
    background: #f2f2f7;
    padding: 2px 8px; /* Slightly more padding */
    border-radius: 4px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .notes-icon-wrapper {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: #007aff;
    margin-left: 4px;

    &:hover {
      opacity: 0.8;
    }

    .notes-icon {
      width: 16px; /* Increased from 14px */
      height: 16px; /* Increased from 14px */
    }
  }
}

/* 3. Duration Column */
.col-duration {
  font-size: 16px; /* Increased from 14px */
  font-weight: 500;
  color: #000;
  width: 80px; /* Increased width */
  text-align: right;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* 4. Actions Column */
.col-actions {
  width: 60px;
  display: flex;
  justify-content: flex-end;
  gap: 2px;
  opacity: 0; /* Hidden by default */
  transition: opacity 0.2s ease;

  .action-btn {
    padding: 4px;
    height: 28px; /* Increased from 24px */
    width: 28px; /* Increased from 24px */
    color: #8e8e93;

    &:hover {
      color: #007aff;
      background-color: rgba(0, 122, 255, 0.1);
    }

    &.delete:hover {
      color: #ff3b30;
      background-color: rgba(255, 59, 48, 0.1);
    }

    :deep(.iconify) {
      width: 18px; /* Increased from 16px */
      height: 18px; /* Increased from 16px */
    }
  }
}

.expanded-notes {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 0.5px solid rgba(60, 60, 67, 0.1);
  font-size: 15px; /* Increased from 13px */
  color: #3c3c43;
  line-height: 1.5;
  padding-left: 122px; /* Align with task name (Time width + gap) */
}

/* Category Colors */
.category-color-0 {
  background-color: #007aff;
}
.category-color-1 {
  background-color: #ff2d55;
}
.category-color-2 {
  background-color: #34c759;
}
.category-color-3 {
  background-color: #ff9500;
}
.category-color-4 {
  background-color: #5856d6;
}
.category-color-5 {
  background-color: #ff3b30;
}

/* Category Backgrounds (Subtle/Pastel) */
.category-bg-0 {
  background-color: rgba(0, 122, 255, 0.04);
}
.category-bg-1 {
  background-color: rgba(255, 45, 85, 0.04);
}
.category-bg-2 {
  background-color: rgba(52, 199, 89, 0.04);
}
.category-bg-3 {
  background-color: rgba(255, 149, 0, 0.04);
}
.category-bg-4 {
  background-color: rgba(88, 86, 214, 0.04);
}
.category-bg-5 {
  background-color: rgba(255, 59, 48, 0.04);
}

/* Hover state remains consistent or slightly darkens */
.ios-list-item:hover {
  filter: brightness(
    0.98
  ); /* Slightly darken on hover instead of generic shadow change only */
}
</style>
