<!-- 日志表格组件 -->
<template>
  <div class="log-table-container">
    <div class="log-table">
      <div class="log-row log-row__header">
        <div class="col task">任务</div>
        <div class="col timeslot">时间段</div>
        <div class="col duration">时长</div>
        <div class="col mood">心情</div>
        <div class="col actions">操作</div>
      </div>

      <div v-for="log in logs" :key="log.id" class="log-entry">
        <div class="log-row">
          <div class="col task">
            <div class="task-cell">
              <span
                v-if="log.subcategory"
                class="category-tag"
                :class="`category-color-${(log.subcategory.category_id || 0) % 6}`"
                :title="log.subcategory.category?.name || ''"
              >
                {{ log.subcategory.name }}
              </span>
              <strong>{{ log.task }}</strong>
            </div>
          </div>
          <div class="col timeslot">{{ log.time_slot || "N/A" }}</div>
          <div class="col duration">{{ log.actual_duration }} 分钟</div>
          <div class="col mood">
            <span class="mood-emoji">{{ moodEmoji(log.mood) }}</span>
          </div>
          <div class="col actions">
            <el-button
              v-if="log.notes"
              link
              size="small"
              @click="$emit('toggle-notes', log.id)"
              title="查看笔记"
              class="action-btn"
            >
              <Icon icon="lucide:message-square" />
            </el-button>
            <el-button
              link
              size="small"
              @click="$emit('edit-record', log)"
              title="编辑"
              class="action-btn"
            >
              <Icon icon="lucide:pencil" />
            </el-button>
            <el-button
              link
              size="small"
              type="danger"
              @click="$emit('delete-record', log)"
              title="删除"
              class="action-btn"
            >
              <Icon icon="lucide:trash-2" />
            </el-button>
          </div>
        </div>

        <div
          v-if="log.notes && expandedNotes.includes(log.id)"
          class="log-notes-row"
        >
          <div class="log-notes-cell">{{ log.notes }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";

// Props
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

// Emits
defineEmits(["toggle-notes", "edit-record", "delete-record"]);

// 心情表情
const moodEmoji = (mood) => {
  const moods = {
    5: "😃",
    4: "😊",
    3: "😐",
    2: "😟",
    1: "😠",
  };
  return moods[mood] || "⚪️";
};
</script>

<style scoped lang="scss">
.log-table-container {
  width: 100%;
}

.log-table {
  width: 100%;
  display: flex;
  flex-direction: column;
  border: none;
  border-radius: 18px;
  overflow: hidden;
  background: #ffffff;
}

.log-row {
  display: grid;
  grid-template-columns: minmax(200px, 2fr) 1fr 0.8fr 0.6fr 1fr;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f1f5;
  font-size: 0.96rem;
  color: #1f2937;

  .col {
    display: flex;
    align-items: center;
  }

  &__header {
    background: #f9fafb;
    font-weight: 700;
    color: #475569;
    font-size: 0.88rem;

    .col {
      justify-content: center;
    }

    .col.task {
      justify-content: flex-start;
    }
  }
}

.log-entry:last-child .log-row {
  border-bottom: none;
}

.task-cell {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-width: 0;

  .category-tag {
    font-size: 12px;
    padding: 3px 10px;
    border-radius: 999px;
    font-weight: 600;
    white-space: nowrap;
    flex-shrink: 0;
  }

  strong {
    font-weight: 500;
    color: #1f2937;
    font-size: 0.95rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.col.timeslot,
.col.duration,
.col.mood {
  color: #475569;
  font-size: 0.94rem;
  justify-content: center;
}

.col.actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

.mood-emoji {
  font-size: 20px;
  line-height: 1;
}

.action-btn {
  padding: 4px;
  margin-left: 2px;
  color: #9ca3af;

  :deep(.iconify) {
    width: 18px;
    height: 18px;
  }
}

.log-notes-row {
  padding: 12px 16px 16px 16px;
  border-top: 1px solid #e5e7eb;
  background-color: #f9fafb;

  .log-notes-cell {
    color: #4b5563;
    font-size: 0.9rem;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }
}

.log-row:hover {
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.04), rgba(99, 102, 241, 0.02));
}

@media (max-width: 900px) {
  .log-row {
    grid-template-columns: minmax(160px, 2fr) repeat(2, 1fr) 0.6fr 1fr;
  }
}

@media (max-width: 768px) {
  .log-row,
  .log-row__header {
    grid-template-columns: 1fr 0.8fr 0.6fr 0.6fr;
    gap: 10px;
  }

  .log-row .col.actions,
  .log-row__header .col.actions {
    grid-column: span 4;
    justify-content: flex-end;
  }

  .log-row .col.task {
    grid-column: span 4;
  }

  .log-row__header .col.task {
    grid-column: span 4;
  }
}

@media (max-width: 520px) {
  .log-row,
  .log-row__header {
    grid-template-columns: 1fr 1fr;
  }

  .log-row .col.task,
  .log-row__header .col.task,
  .log-row .col.actions,
  .log-row__header .col.actions {
    grid-column: span 2;
  }
}

/* 分类颜色 */
.category-color-0 {
  background-color: #dbeafe;
  color: #1e40af;
}
.category-color-1 {
  background-color: #fce7f3;
  color: #be185d;
}
.category-color-2 {
  background-color: #dcfce7;
  color: #15803d;
}
.category-color-3 {
  background-color: #fef3c7;
  color: #a16207;
}
.category-color-4 {
  background-color: #e0e7ff;
  color: #4338ca;
}
.category-color-5 {
  background-color: #fed7aa;
  color: #c2410c;
}
</style>
