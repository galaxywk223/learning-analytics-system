<template>
  <PageContainer
    :title="{ icon: '💬', text: '格言管理' }"
    subtitle="写下一句激励你的话语，启发每一天。"
    :custom-class="'settings-subpage'"
  >
    <div class="motto-shell">
      <div class="motto-card">
        <header class="motto-header">
          <div class="header-icon">💬</div>
          <div>
            <h2>格言管理</h2>
            <p>写下一句激励你的话语，启发每一天。</p>
          </div>
        </header>

        <div class="add-row" @keyup.enter="submitAdd">
          <input
            v-model="form.content"
            type="text"
            maxlength="500"
            placeholder="在此输入新的格言..."
          />
          <button
            class="pill-btn primary"
            type="button"
            :disabled="adding || !form.content.trim()"
            @click="submitAdd"
          >
            {{ adding ? "添加中..." : "添加" }}
          </button>
        </div>

        <div v-if="itemsSorted.length" class="motto-list">
          <div
            v-for="m in itemsSorted"
            :key="m.id"
            class="motto-item"
          >
            <div class="quote-mark">❝</div>
            <div class="motto-text">
              <p>{{ m.content }}</p>
            </div>
            <div class="motto-actions">
              <button class="ghost-btn" title="编辑" @click="openEdit(m)">✏️</button>
              <button class="ghost-btn danger" title="删除" @click="confirmDelete(m.id)">🗑️</button>
            </div>
          </div>
        </div>
        <div v-else class="empty-state">
          <div class="empty-illustration">🪶</div>
          <p class="empty-title">记录第一句人生格言</p>
          <p class="empty-sub">在上方输入框里写下你的灵感</p>
        </div>
      </div>
    </div>

    <el-dialog
      v-model="editVisible"
      title="编辑格言"
      width="520px"
      @opened="refreshIcons"
    >
      <el-form :model="editForm">
        <el-form-item prop="content">
          <el-input
            v-model="editForm.content"
            type="textarea"
            :autosize="{ minRows: 3, maxRows: 6 }"
            placeholder="在此输入新的格言..."
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useMottoStore } from "@/stores/modules/motto";
import PageContainer from "@/components/layout/PageContainer.vue";

const mottoStore = useMottoStore();
const form = ref({ content: "" });
const editForm = ref({ id: null, content: "" });
const adding = ref(false);
const updating = ref(false);
const editVisible = ref(false);

const itemsSorted = computed(() =>
  (mottoStore.items || []).slice().sort((a, b) => (b.id || 0) - (a.id || 0))
);

async function submitAdd() {
  const content = form.value.content.trim();
  if (!content) return;
  adding.value = true;
  try {
    await mottoStore.add(content);
    form.value.content = "";
    ElMessage.success("添加成功");
  } catch (e) {
    ElMessage.error(e?.message || "添加失败");
  } finally {
    adding.value = false;
  }
}

function openEdit(motto) {
  editForm.value = { ...motto };
  editVisible.value = true;
}

async function submitEdit() {
  const content = editForm.value.content.trim();
  if (!content) {
    ElMessage.warning("请输入格言内容");
    return;
  }
  updating.value = true;
  try {
    await mottoStore.update(editForm.value.id, content);
    ElMessage.success("更新成功");
    editVisible.value = false;
  } catch (e) {
    ElMessage.error(e?.message || "更新失败");
  } finally {
    updating.value = false;
  }
}

async function confirmDelete(id) {
  try {
    await ElMessageBox.confirm("删除后不可恢复，确定删除这条格言吗？", "确认删除", {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  try {
    await mottoStore.remove(id);
    ElMessage.success("已删除");
  } catch (e) {
    ElMessage.error(e?.message || "删除失败");
  }
}

function refreshIcons() {
  /* no-op for Iconify in dialog */
}

onMounted(() => {
  mottoStore.fetch();
});
</script>

<style scoped>
.motto-shell {
  display: flex;
  justify-content: center;
}

.motto-card {
  width: 100%;
  max-width: 820px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #e5e7eb;
  border-radius: 24px;
  box-shadow: 0 18px 40px rgba(15, 23, 42, 0.08);
  padding: 18px 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.motto-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: rgba(79, 70, 229, 0.1);
  color: #4f46e5;
  font-size: 22px;
}

.motto-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #0f172a;
}

.motto-header p {
  margin: 4px 0 0;
  color: #6b7280;
  font-size: 13px;
}

.add-row {
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 10px;
  align-items: center;
}

.add-row input {
  height: 44px;
  border: none;
  border-radius: 12px;
  background: #f3f4f6;
  padding: 0 14px;
  font-size: 14px;
  outline: none;
  transition: all 0.15s ease;
}

.add-row input:focus {
  background: #ffffff;
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.12);
}

.motto-list {
  display: flex;
  flex-direction: column;
}

.motto-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 16px 4px;
  border-bottom: 1px solid #eef1f5;
  transition: background 0.12s ease;
}

.motto-item:last-of-type {
  border-bottom: none;
}

.motto-item:hover {
  background: #f9fafb;
}

.quote-mark {
  font-size: 28px;
  color: #cbd5e1;
  padding-left: 6px;
}

.motto-text p {
  margin: 0;
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 16px;
  color: #111827;
  line-height: 1.6;
}

.motto-actions {
  display: flex;
  gap: 8px;
  opacity: 0;
  transition: opacity 0.12s ease;
}

.motto-item:hover .motto-actions {
  opacity: 1;
}

.ghost-btn {
  border: none;
  background: rgba(0, 0, 0, 0.05);
  border-radius: 10px;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 14px;
  color: #4b5563;
  transition: background 0.15s ease, color 0.15s ease;
}

.ghost-btn:hover {
  background: rgba(79, 70, 229, 0.12);
  color: #111827;
}

.ghost-btn.danger:hover {
  background: rgba(239, 68, 68, 0.12);
  color: #dc2626;
}

.ghost-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pill-btn {
  border: none;
  border-radius: 12px;
  padding: 12px 16px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.2s ease, opacity 0.15s ease;
}

.pill-btn.primary {
  background: linear-gradient(135deg, #6d7cff, #4f46e5);
  color: #ffffff;
  box-shadow: 0 12px 26px rgba(79, 70, 229, 0.28);
}

.pill-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.empty-state {
  text-align: center;
  color: #6b7280;
  padding: 24px 0 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.empty-illustration {
  font-size: 36px;
}

.empty-title {
  margin: 0;
  font-weight: 800;
  color: #0f172a;
}

.empty-sub {
  margin: 0;
  font-size: 13px;
  color: #9ca3af;
}

@media (max-width: 768px) {
  .add-row {
    grid-template-columns: 1fr;
  }

  .motto-item {
    grid-template-columns: auto 1fr;
    grid-template-areas:
      "quote text"
      "actions actions";
    row-gap: 6px;
  }

  .motto-actions {
    grid-area: actions;
    justify-content: flex-end;
  }
}
</style>
