<template>
  <div
    class="list-group-item motto-item"
    :id="`motto-${motto.id}`"
  >
    <p class="motto-content">
      <span class="quote-mark left">“</span>
      <span class="text">{{ motto.content }}</span>
      <span class="quote-mark right">”</span>
    </p>
    <div class="item-actions">
      <el-button
        size="small"
        type="default"
        class="btn-icon edit-motto-btn"
        :title="'编辑'"
        @click="onEdit"
      >
        <Icon icon="lucide:pencil" class="icon-sm" />
      </el-button>
      <el-button
        size="small"
        type="danger"
        plain
        class="btn-icon delete-motto-btn"
        :title="'删除'"
        @click="onDelete"
        :loading="deleting"
      >
        <Icon icon="lucide:trash-2" class="icon-sm" />
      </el-button>
    </div>
  </div>
</template>
<script setup>
import { ref } from "vue";
import { Icon } from "@iconify/vue";
import { useMottoStore } from "@/stores";
import { ElMessageBox, ElMessage } from "element-plus";

const props = defineProps({
  motto: { type: Object, required: true },
});
const emit = defineEmits(["edit"]);
const deleting = ref(false);
const store = useMottoStore();

function onEdit() {
  emit("edit", props.motto);
}

async function onDelete() {
  if (deleting.value) return;
  try {
    await ElMessageBox.confirm("确定要删除这条格言吗？", "删除确认", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  deleting.value = true;
  try {
    await store.remove(props.motto.id);
    // 动画淡出
    const el = document.getElementById(`motto-${props.motto.id}`);
    if (el) {
      el.style.transition = "opacity 0.3s ease";
      el.style.opacity = "0";
      setTimeout(() => {
        if (el && el.parentNode) el.parentNode.removeChild(el);
      }, 320);
    }
    ElMessage.success("格言已删除。");
  } catch (e) {
    console.error("delete motto failed", e);
    ElMessage.error("删除失败");
  } finally {
    deleting.value = false;
  }
}
</script>
<style scoped>
.motto-item {
  padding: 1rem 1.25rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.75rem;
  align-items: center;
  transition: background-color 0.2s ease-in-out, border-color 0.2s ease-in-out;
}
.motto-item:hover {
  background-color: var(--surface-card-muted);
}
.item-actions {
  display: flex;
  gap: 0.5rem;
  opacity: 0;
  transition: opacity 0.2s ease-in-out;
}
.motto-item:hover .item-actions {
  opacity: 1;
}
.btn-icon {
  padding: 0.2rem 0.5rem;
}
.icon-sm {
  width: 16px;
  height: 16px;
}
.motto-content {
  margin: 0;
  font-size: 1rem;
  line-height: 1.7;
  color: var(--color-text-heading);
  display: flex;
  align-items: baseline;
  gap: 6px;
}
.motto-content .quote-mark { color: #94a3b8; font-size: 1.25rem; }
.motto-content .text { color: var(--color-text-secondary); }
</style>
