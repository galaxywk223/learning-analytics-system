<template>
  <PageContainer
    :title="{ icon: 'lucide:message-square-quote', text: '格言管理' }"
    subtitle="写下一句激励你的话语，启发每一天。"
    :custom-class="'settings-subpage'"
  >
    <div class="motto-container-flat">
      <!-- Header / Add Area -->
      <div class="motto-header">
        <div class="header-left">
          <h4>格言列表</h4>
        </div>
        <div class="add-wrapper">
          <input
            v-model="form.content"
            type="text"
            maxlength="500"
            placeholder="在此输入新的格言..."
            @keyup.enter="submitAdd"
          />
          <button
            class="pill-btn primary"
            type="button"
            style="padding: 8px 16px; min-width: auto; font-size: 14px"
            :disabled="adding || !form.content.trim()"
            @click="submitAdd"
          >
            {{ adding ? "..." : "添加" }}
          </button>
        </div>
      </div>

      <!-- Motto List -->
      <div v-if="itemsSorted.length" class="motto-list">
        <div class="list-header">
          <span class="col-content">内容</span>
          <span class="col-actions">操作</span>
        </div>

        <div v-for="m in itemsSorted" :key="m.id" class="motto-row">
          <div class="col-content">
            <span class="quote-mark">❝</span>
            <span class="motto-text">{{ m.content }}</span>
          </div>
          <div class="col-actions">
            <div class="action-group">
              <button class="action-btn" title="编辑" @click="openEdit(m)">
                ✏️
              </button>
              <button
                class="action-btn danger"
                title="删除"
                @click="confirmDelete(m.id)"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">🪶</div>
        <p>记录第一句人生格言</p>
        <p class="empty-sub">在上方输入框里写下你的灵感</p>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editVisible"
      title="编辑格言"
      width="480px"
      class="ios-dialog"
      align-center
      @opened="refreshIcons"
    >
      <form class="dialog-form" @submit.prevent="submitEdit">
        <div class="ios-input-group">
          <div class="input-row">
            <label>内容</label>
            <textarea
              v-model="editForm.content"
              rows="3"
              placeholder="在此输入新的格言..."
              maxlength="500"
            ></textarea>
          </div>
        </div>

        <div class="dialog-footer">
          <button
            type="button"
            class="pill-btn secondary"
            @click="editVisible = false"
          >
            取消
          </button>
          <button type="submit" class="pill-btn primary" :disabled="updating">
            {{ updating ? "保存中..." : "保存" }}
          </button>
        </div>
      </form>
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
  (mottoStore.items || []).slice().sort((a, b) => (b.id || 0) - (a.id || 0)),
);

async function submitAdd() {
  const content = form.value.content.trim();
  if (!content) return;
  adding.value = true;
  try {
    await mottoStore.add({ content });
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
    await ElMessageBox.confirm(
      "删除后不可恢复，确定删除这条格言吗？",
      "确认删除",
      {
        type: "warning",
        confirmButtonText: "删除",
        cancelButtonText: "取消",
      },
    );
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
.motto-container-flat {
  width: 100%;
  background: var(--surface-card);
  border-radius: 16px;
  border: 1px solid var(--stroke-soft);
  overflow: hidden;
}

.motto-header {
  padding: 16px 24px;
  background: var(--surface-card-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--stroke-soft);
  gap: 24px;
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text-heading);
  white-space: nowrap;
}

.add-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  max-width: 500px;
}

.add-wrapper input {
  flex: 1;
  height: 36px;
  background: var(--surface-card);
  border: 1px solid var(--color-border-input);
  border-radius: 8px;
  padding: 0 12px;
  font-size: 14px;
  color: var(--color-text-heading);
  outline: none;
  transition: all 0.15s ease;
}

.add-wrapper input::placeholder {
  color: var(--color-text-muted);
}

.add-wrapper input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--color-primary-light);
}

.btn-add {
  height: 36px;
  padding: 0 16px;
  background: var(--color-primary);
  color: var(--color-text-inverse);
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s ease;
  white-space: nowrap;
}

.btn-add:hover {
  background: var(--color-primary-dark);
}

.btn-add:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* List Styles */
.motto-list {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  padding: 12px 24px;
  background: var(--surface-card);
  border-bottom: 1px solid var(--stroke-soft);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.motto-row {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid var(--stroke-soft);
  transition: background-color 0.1s ease;
}

.motto-row:last-child {
  border-bottom: none;
}

.motto-row:hover {
  background: var(--surface-card-muted);
}

.col-content {
  flex: 1;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding-right: 24px;
}

.col-actions {
  width: 80px;
  display: flex;
  justify-content: flex-end;
}

.quote-mark {
  font-size: 20px;
  color: var(--color-text-muted);
  line-height: 1;
  margin-top: 2px;
}

.motto-text {
  font-family: "Georgia", "Times New Roman", serif;
  font-size: 15px;
  color: var(--color-text-heading);
  line-height: 1.5;
}

.action-group {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.motto-row:hover .action-group {
  opacity: 1;
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: var(--surface-card-muted);
  color: var(--color-text-heading);
  border-color: var(--stroke-soft);
}

.action-btn.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--color-error);
  border-color: rgba(239, 68, 68, 0.25);
}

@media (max-width: 768px) {
  .action-group {
    opacity: 1;
  }

  .list-header {
    display: none;
  }

  .motto-header {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .add-wrapper {
    max-width: none;
  }
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: var(--color-text-muted);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

.empty-sub {
  font-size: 13px;
  color: var(--color-text-muted);
}

/* Dialog Styles */
.ios-input-group {
  background: var(--surface-card-muted);
  border-radius: 12px;
  padding: 0 16px;
  border: 1px solid var(--stroke-soft);
  margin-bottom: 24px;
}

.input-row {
  display: flex;
  align-items: flex-start;
  padding: 14px 0;
}

.input-row label {
  width: 60px;
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-secondary);
  padding-top: 8px;
}

.input-row textarea {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: var(--color-text-heading);
  padding: 8px 0;
  resize: none;
  font-family: inherit;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
