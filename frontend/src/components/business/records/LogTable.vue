<!-- 日志表格组件 -->
<template>
  <div class="log-table-container">
    <!-- 日志表格 -->
    <el-table :data="logs" class="log-table" size="small" :show-header="true">
      <el-table-column label="任务" min-width="200">
        <template #default="{ row }">
          <div class="task-cell">
            <span
              v-if="row.subcategory"
              class="category-tag"
              :class="`category-color-${(row.subcategory.category_id || 0) % 6}`"
              :title="row.subcategory.category?.name || ''"
            >
              {{ row.subcategory.name }}
            </span>
            <strong>{{ row.task }}</strong>
          </div>
        </template>
      </el-table-column>

      <el-table-column label="时间段" width="100">
        <template #default="{ row }">
          {{ row.time_slot || "N/A" }}
        </template>
      </el-table-column>

      <el-table-column label="时长" width="90">
        <template #default="{ row }"> {{ row.actual_duration }} 分钟 </template>
      </el-table-column>

      <el-table-column label="心情" width="70" align="center">
        <template #default="{ row }">
          <span class="mood-emoji">{{ moodEmoji(row.mood) }}</span>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="200" align="right">
        <template #default="{ row }">
          <el-button
            v-if="row.notes"
            link
            size="small"
            @click="$emit('toggle-notes', row.id)"
            title="查看笔记"
            class="action-btn"
          >
            <Icon icon="lucide:message-square" />
          </el-button>
          <el-button
            link
            size="small"
            @click="$emit('edit-record', row)"
            title="编辑"
            class="action-btn"
          >
            <Icon icon="lucide:pencil" />
          </el-button>
          <el-button
            link
            size="small"
            type="danger"
            @click="$emit('delete-record', row)"
            title="删除"
            class="action-btn"
          >
            <Icon icon="lucide:trash-2" />
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 笔记展开区域 -->
    <div v-for="log in logs" :key="`notes-${log.id}`">
      <div
        v-if="log.notes && expandedNotes.includes(log.id)"
        class="log-notes-row"
      >
        <div class="log-notes-cell">{{ log.notes }}</div>
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

  .log-table {
    width: 100%;

    :deep(.el-table__header) {
      th {
        background: #f9fafb;
        color: #6b7280;
        font-weight: 600;
        font-size: 14px;
        padding: 10px 0;
        height: 40px;
      }
    }

    :deep(.el-table__body) {
      tr {
        &:hover > td {
          background-color: #f9fafb !important;
        }

        td {
          padding: 10px 0;
          height: 44px;
          border-bottom: 1px solid #f3f4f6;
          font-size: 15px;

          .cell {
            padding: 0 14px;
            line-height: 1.5;
          }
        }
      }
    }

    .task-cell {
      display: flex;
      align-items: center;
      gap: 0.5rem;

      .category-tag {
        font-size: 13px;
        padding: 3px 10px;
        border-radius: 4px;
        font-weight: 500;
        white-space: nowrap;
        flex-shrink: 0;
      }

      strong {
        font-weight: 500;
        color: #1f2937;
        font-size: 15px;
      }
    }

    .mood-emoji {
      font-size: 24px;
      line-height: 1;
    }

    .action-btn {
      padding: 6px;
      margin-left: 6px;

      :deep(.iconify) {
        width: 18px;
        height: 18px;
      }

      &:hover {
        :deep(.iconify) {
          transform: scale(1.15);
        }
      }
    }
  }

  .log-notes-row {
    margin: 0 14px 14px 14px;
    padding: 12px 14px;
    background-color: #f9fafb;
    border-left: 3px solid #667eea;
    border-radius: 4px;

    .log-notes-cell {
      color: #4b5563;
      font-size: 14px;
      line-height: 1.6;
      white-space: pre-wrap;
      word-break: break-word;
    }
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
