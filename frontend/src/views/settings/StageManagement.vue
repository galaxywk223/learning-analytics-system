<template>
  <PageContainer
    :title="{ icon: '🚩', text: '阶段管理' }"
    subtitle="梳理学习阶段，设置当前阶段并管理时间跨度"
    :custom-class="'settings-subpage'"
  >
    <div class="stage-layout">
      <!-- Left Column: Create New Stage -->
      <div class="create-card">
        <div class="card-header">
          <h3>新建阶段</h3>
          <p>开启一个新的学习旅程</p>
        </div>
        <form @submit.prevent="handleAddStage" class="create-form">
          <div class="form-group">
            <label>阶段名称</label>
            <input
              v-model="newStage.name"
              type="text"
              placeholder="例如：大三上学期"
              :disabled="loading"
            />
          </div>
          <div class="form-group">
            <label>起始日期</label>
            <input
              v-model="newStage.start_date"
              type="date"
              :disabled="loading"
            />
          </div>
          <div class="form-group">
            <label>结束日期 (可选)</label>
            <input
              v-model="newStage.end_date"
              type="date"
              :disabled="loading"
            />
          </div>
          <div class="form-group checkbox-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="newStage.is_current" />
              <span class="checkbox-text">设为当前阶段</span>
            </label>
          </div>
          <button type="submit" class="btn-create" :disabled="loading || !isValidNewStage">
            {{ loading ? "创建中..." : "创建阶段" }}
          </button>
        </form>
      </div>

      <!-- Right Column: Existing Stages -->
      <div class="list-card">
        <div class="card-header">
          <h3>已有阶段</h3>
          <p>管理您的所有学习阶段</p>
        </div>

        <div class="stage-list" v-if="stages.length">
          <div
            v-for="stage in stages"
            :key="stage.id"
            class="stage-item"
            :class="{ current: stage.is_current }"
          >
            <div class="stage-content">
              <div class="stage-main">
                <div class="stage-title-row">
                  <span class="stage-name">{{ stage.name }}</span>
                  <span v-if="stage.is_current" class="badge-current">当前</span>
                </div>
                <div class="stage-meta">
                  <span>{{ formatDate(stage.start_date) }}</span>
                  <span v-if="stage.end_date"> - {{ formatDate(stage.end_date) }}</span>
                  <span v-else> - 至今</span>
                </div>
              </div>
              
              <div class="stage-actions">
                <button
                  v-if="!stage.is_current"
                  class="action-btn"
                  title="设为当前"
                  @click="handleSetCurrent(stage)"
                  :disabled="loading"
                >
                  🚩
                </button>
                <button
                  class="action-btn"
                  title="编辑"
                  @click="openEdit(stage)"
                  :disabled="loading"
                >
                  ✏️
                </button>
                <button
                  class="action-btn danger"
                  title="删除"
                  @click="handleDelete(stage)"
                  :disabled="loading"
                >
                  🗑️
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="empty-state" v-else>
          <div class="empty-icon">📭</div>
          <p>还没有创建任何阶段</p>
        </div>
      </div>
    </div>

    <!-- Edit Dialog -->
    <el-dialog
      v-model="editVisible"
      title="编辑阶段"
      width="500px"
      class="edit-dialog"
      destroy-on-close
    >
      <form @submit.prevent="handleUpdateStage" class="edit-form">
        <div class="form-group">
          <label>阶段名称</label>
          <input v-model="editForm.name" type="text" required />
        </div>
        <div class="form-group">
          <label>起始日期</label>
          <input v-model="editForm.start_date" type="date" required />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="editForm.end_date" type="date" />
        </div>
        <div class="dialog-footer">
          <button type="button" class="btn-cancel" @click="editVisible = false">取消</button>
          <button type="submit" class="btn-save" :disabled="loading">保存</button>
        </div>
      </form>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, onMounted, computed } from "vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import { stageAPI } from "@/api/modules/stage";
import { ElMessage, ElMessageBox } from "element-plus";

const stages = ref([]);
const loading = ref(false);
const editVisible = ref(false);

const newStage = ref({
  name: "",
  start_date: "",
  end_date: "",
  is_current: false,
});

const editForm = ref({
  id: null,
  name: "",
  start_date: "",
  end_date: "",
});

const isValidNewStage = computed(() => {
  return newStage.value.name && newStage.value.start_date;
});

onMounted(() => {
  fetchStages();
});

async function fetchStages() {
  loading.value = true;
  try {
    const res = await stageAPI.getAll();
    stages.value = res.stages || [];
  } catch (e) {
    console.error("Failed to fetch stages", e);
    ElMessage.error("获取阶段列表失败");
  } finally {
    loading.value = false;
  }
}

async function handleAddStage() {
  if (!isValidNewStage.value) return;
  loading.value = true;
  try {
    await stageAPI.create(newStage.value);
    ElMessage.success("创建成功");
    newStage.value = { name: "", start_date: "", end_date: "", is_current: false };
    await fetchStages();
  } catch (e) {
    console.error("Create stage failed", e);
    ElMessage.error("创建失败");
  } finally {
    loading.value = false;
  }
}

async function handleSetCurrent(stage) {
  loading.value = true;
  try {
    await stageAPI.update(stage.id, { is_current: true });
    ElMessage.success("已更新当前阶段");
    await fetchStages();
  } catch (e) {
    console.error("Set current failed", e);
    ElMessage.error("设置失败");
  } finally {
    loading.value = false;
  }
}

function openEdit(stage) {
  editForm.value = { ...stage };
  editVisible.value = true;
}

async function handleUpdateStage() {
  loading.value = true;
  try {
    await stageAPI.update(editForm.value.id, {
      name: editForm.value.name,
      start_date: editForm.value.start_date,
      end_date: editForm.value.end_date,
    });
    ElMessage.success("更新成功");
    editVisible.value = false;
    await fetchStages();
  } catch (e) {
    console.error("Update stage failed", e);
    ElMessage.error("更新失败");
  } finally {
    loading.value = false;
  }
}

async function handleDelete(stage) {
  try {
    await ElMessageBox.confirm("确定要删除这个阶段吗？", "提示", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    
    loading.value = true;
    await stageAPI.delete(stage.id);
    ElMessage.success("删除成功");
    await fetchStages();
  } catch (e) {
    if (e !== "cancel") {
      console.error("Delete stage failed", e);
      ElMessage.error("删除失败");
    }
  } finally {
    loading.value = false;
  }
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  const d = new Date(dateStr);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}
</script>

<style scoped>
.stage-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  gap: 24px;
  align-items: start;
  width: 100%;
}

/* ... (unchanged styles) ... */

@media (max-width: 768px) {
  .stage-layout {
    grid-template-columns: 1fr;
  }
  
  .create-card {
    position: static;
  }
}

/* Cards */
.create-card,
.list-card {
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  border: 1px solid rgba(0, 0, 0, 0.02);
}

.create-card {
  position: sticky;
  top: 32px;
}

.card-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #1c1c1e;
}

.card-header p {
  margin: 6px 0 0;
  color: #8e8e93;
  font-size: 14px;
}

/* Form */
.create-form,
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 14px;
  font-weight: 600;
  color: #1c1c1e;
  margin-left: 4px;
}

.form-group input[type="text"],
.form-group input[type="date"] {
  height: 48px;
  background: #f2f2f7;
  border: none;
  border-radius: 12px;
  padding: 0 16px;
  font-size: 16px;
  color: #1c1c1e;
  outline: none;
  transition: all 0.2s ease;
  font-family: inherit;
}

.form-group input:focus {
  background: #ffffff;
  box-shadow: 0 0 0 2px #007AFF;
}

.checkbox-group {
  flex-direction: row;
  align-items: center;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-text {
  font-size: 14px;
  color: #1c1c1e;
  font-weight: 500;
}

.btn-create {
  height: 48px;
  background: linear-gradient(135deg, #007AFF, #5856D6);
  border: none;
  border-radius: 999px;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 8px 20px rgba(0, 122, 255, 0.3);
  margin-top: 8px;
}

.btn-create:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 24px rgba(0, 122, 255, 0.4);
}

.btn-create:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* List */
.stage-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.stage-item {
  background: #ffffff;
  border: 1px solid #f2f2f7;
  border-radius: 16px;
  padding: 16px 20px;
  transition: all 0.2s ease;
}

.stage-item:hover {
  border-color: #e5e5ea;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
  transform: translateY(-1px);
}

.stage-item.current {
  background: #f0fdf4;
  border-color: #bbf7d0;
}

.stage-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.stage-main {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stage-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stage-name {
  font-size: 16px;
  font-weight: 700;
  color: #1c1c1e;
}

.badge-current {
  font-size: 11px;
  font-weight: 700;
  color: #15803d;
  background: #dcfce7;
  padding: 2px 8px;
  border-radius: 999px;
}

.stage-meta {
  font-size: 13px;
  color: #8e8e93;
}

.stage-actions {
  display: flex;
  gap: 8px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  border: none;
  background: #f2f2f7;
  color: #1c1c1e;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.action-btn:hover {
  background: #e5e5ea;
  transform: scale(1.05);
}

.action-btn.danger:hover {
  background: #fee2e2;
  color: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: #8e8e93;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

/* Dialog Styles */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel {
  padding: 10px 20px;
  border-radius: 999px;
  border: none;
  background: #f2f2f7;
  color: #1c1c1e;
  font-weight: 600;
  cursor: pointer;
}

.btn-save {
  padding: 10px 24px;
  border-radius: 999px;
  border: none;
  background: #007AFF;
  color: #ffffff;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 768px) {
  .stage-layout {
    grid-template-columns: 1fr;
  }
  
  .create-card {
    position: static;
  }
}
</style>
