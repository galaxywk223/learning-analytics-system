<template>
  <li class="timeline-item">
    <div class="timeline-icon"><i data-lucide="trophy"></i></div>
    <div class="timeline-content">
      <div class="timeline-content-header">
        <div>
          <span class="badge bg-primary timeline-category mb-1">{{
            categoryName
          }}</span>
          <h5 class="timeline-title">{{ item.title }}</h5>
          <p class="timeline-date mb-0">{{ formatDate(item.event_date) }}</p>
        </div>
        <div class="dropdown" v-if="enableActions">
          <el-dropdown trigger="click">
            <span class="el-dropdown-link btn-more" @click.stop>
              <i data-lucide="more-horizontal"></i>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click.stop="editItem">编辑</el-dropdown-item>
                <el-dropdown-item
                  divided
                  class="danger"
                  @click.stop="deleteItem"
                  >删除</el-dropdown-item
                >
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      <div class="timeline-description" v-html="safeDescription"></div>
      <div
        v-if="attachments.length"
        class="timeline-attachments border-top pt-3 mt-3"
      >
        <h6 class="card-subtitle mb-2 text-muted">附件:</h6>
        <div class="attachments-flex">
          <div
            v-for="att in attachments"
            :key="att.id"
            class="attachment-item"
            :id="`attachment-${att.id}`"
          >
            <a :href="downloadUrl(att)" target="_blank" class="attachment-link">
              <i data-lucide="image" style="width: 16px; height: 16px"></i>
              <span>{{ att.original_filename }}</span>
            </a>
            <button
              v-if="enableActions"
              class="attachment-delete-btn"
              title="删除此附件"
              @click.stop="deleteAttachment(att)"
            >
              <i data-lucide="x"></i>
            </button>
          </div>
        </div>
      </div>
    </div>
  </li>
</template>

<script setup>
import { computed } from "vue";
import { milestoneAPI } from "@/api/modules/milestone";

const props = defineProps({
  item: { type: Object, required: true },
  categories: { type: Array, default: () => [] },
  enableActions: { type: Boolean, default: true },
});
const emits = defineEmits(["edit", "deleted", "attachment-deleted"]);

const categoryName = computed(() => {
  const cat = props.categories.find((c) => c.id === props.item.category_id);
  return cat ? cat.name : "未分类";
});

const attachments = computed(() => props.item.attachments || []);
function formatDate(d) {
  if (!d) return "";
  const dt = new Date(d);
  return `${dt.getFullYear()}年${String(dt.getMonth() + 1).padStart(2, "0")}月${String(dt.getDate()).padStart(2, "0")}日`;
}
const safeDescription = computed(() =>
  props.item.description
    ? props.item.description
    : '<p class="text-muted">没有详细描述。</p>'
);

function editItem() {
  emits("edit", props.item);
}
async function deleteItem() {
  if (!confirm("确定要永久删除这个成就吗？")) return;
  try {
    await milestoneAPI.remove(props.item.id);
    emits("deleted", props.item.id);
  } catch (e) {
    console.error("delete milestone failed", e);
  }
}
function downloadUrl(att) {
  return `/api/milestones/attachments/${att.file_path}`;
}
async function deleteAttachment(att) {
  if (!confirm("确定要永久删除这个附件吗？")) return;
  try {
    await milestoneAPI.deleteAttachment(props.item.id, att.id);
    emits("attachment-deleted", {
      milestoneId: props.item.id,
      attachmentId: att.id,
    });
  } catch (e) {
    console.error("delete attachment failed", e);
  }
}
</script>

<style scoped src="@/styles/components/milestones/milestone-item.css"></style>
