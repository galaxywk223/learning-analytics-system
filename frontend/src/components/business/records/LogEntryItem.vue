<template>
  <!-- 主记录行 -->
  <tr class="log-entry-row" :id="`log-entry-row-${log.id}`">
    <td>
      <div class="task-cell">
        <!-- 分类标签 -->
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
    </td>
    <td class="time-slot-cell">{{ log.time_slot || "N/A" }}</td>
    <td class="duration-cell">{{ log.actual_duration }} 分钟</td>
    <td class="text-center mood-cell">
      <span class="emoji-icon">{{ moodEmoji(log.mood) }}</span>
    </td>
    <td class="text-end">
      <!-- 笔记按钮 -->
      <el-button
        v-if="log.notes"
        link
        size="small"
        @click="toggleNotes"
        title="查看笔记"
        class="action-btn"
      >
        <Icon icon="lucide:message-square" />
      </el-button>
      <!-- 编辑按钮 -->
      <el-button
        link
        size="small"
        @click="$emit('edit', log)"
        title="编辑"
        class="action-btn"
      >
        <Icon icon="lucide:pencil" />
      </el-button>
      <!-- 删除按钮 -->
      <el-button
        link
        size="small"
        type="danger"
        @click="$emit('delete', log)"
        title="删除"
        class="action-btn delete"
      >
        <Icon icon="lucide:trash-2" />
      </el-button>
    </td>
  </tr>

  <!-- 笔记行（可展开） -->
  <tr
    v-if="log.notes"
    v-show="showNotes"
    class="log-notes-row"
    :id="`notes-${log.id}`"
  >
    <td colspan="5" class="log-notes-cell">{{ log.notes }}</td>
  </tr>
</template>

<script setup>
import { ref } from "vue";
import { Icon } from "@iconify/vue";

const props = defineProps({
  log: {
    type: Object,
    required: true,
  },
});

defineEmits(["edit", "delete"]);

const showNotes = ref(false);

const toggleNotes = () => {
  showNotes.value = !showNotes.value;
};

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

<style scoped>
.task-cell {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  white-space: nowrap;
  overflow: hidden;
}

.task-cell strong {
  text-overflow: ellipsis;
  overflow: hidden;
  font-size: 1.05rem;
  font-weight: 600;
  color: #1e293b;
}

.category-tag {
  display: inline-block;
  padding: 0.35em 0.8em;
  font-size: 0.8rem;
  font-weight: 600;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
  vertical-align: baseline;
  border-radius: 50rem; /* pill shape */
  color: #fff;
  background-color: #6c757d; /* default color */
}

.category-color-0 {
  background-color: #fd7e14;
}

.category-color-1 {
  background-color: #0d6efd;
}

.category-color-2 {
  background-color: #198754;
}

.category-color-3 {
  background-color: #ffc107;
  color: #000;
}

.category-color-4 {
  background-color: #dc3545;
}

.category-color-5 {
  background-color: #6f42c1;
}

.action-btn {
  padding: 0.25rem 0.5rem;
}

.log-notes-row {
  background-color: #f9fafb;
}

.log-notes-cell {
  padding-top: 0.5rem !important;
  padding-bottom: 0.5rem !important;
  border-top: 0 !important;
  color: #6c757d;
  font-size: 0.9rem;
  white-space: normal;
}

.text-center {
  text-align: center;
}

.text-end {
  text-align: right;
}

.time-slot-cell {
  font-size: 1rem;
  font-weight: 500;
  color: #64748b;
}

.duration-cell {
  font-size: 1.05rem;
  font-weight: 600;
  color: #667eea;
}

.mood-cell {
  font-size: 1.8rem;
  line-height: 1;
}
</style>
