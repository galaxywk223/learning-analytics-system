<template>
  <PageContainer
    :title="{ icon: '🚩', text: '阶段管理' }"
    subtitle="梳理学习阶段，设置当前阶段并管理时间跨度"
    :custom-class="'settings-subpage'"
  >
    <div class="stage-container">
      <!-- Header -->
      <div class="stage-header">
        <div class="header-left">
          <h3>阶段列表</h3>
          <p>管理您的所有学习阶段</p>
        </div>
        <button class="btn-create-compact" @click="openCreate">
          <span class="icon">+</span> 新建阶段
        </button>
      </div>

      <!-- Stage List -->
      <div class="stage-list" v-if="stages.length">
        <div
          v-for="stage in stages"
          :key="stage.id"
          class="stage-item"
          :class="{ current: stage.is_current }"
        >
          <div class="stage-info">
            <div class="stage-name-row">
              <span class="stage-name">{{ stage.name }}</span>
              <span v-if="stage.is_current" class="badge-current">当前阶段</span>
            </div>
            <div class="stage-meta">
              <span>{{ formatDate(stage.start_date) }}</span>
              <span class="separator">-</span>
              <span>{{ stage.end_date ? formatDate(stage.end_date) : "至今" }}</span>
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

      <div class="empty-state" v-else>
        <div class="empty-icon">📭</div>
        <p>还没有创建任何阶段</p>
        <button class="btn-create-compact" @click="openCreate">立即创建</button>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑阶段' : '新建阶段'"
      width="480px"
      class="ios-dialog"
      destroy-on-close
      align-center
    >
      <form @submit.prevent="handleSubmit" class="dialog-form">
        <div class="ios-input-group">
          <div class="input-row">
            <label>名称</label>
            <input
              v-model="form.name"
              type="text"
              placeholder="例如：大三上学期"
              required
              :disabled="loading"
            />
          </div>
          <div class="input-row">
            <label>开始</label>
            <input
              v-model="form.start_date"
              type="date"
              required
              :disabled="loading"
            />
          </div>
          <div class="input-row">
            <label>结束</label>
            <input
              v-model="form.end_date"
              type="date"
              :disabled="loading"
              placeholder="可选"
            />
          </div>
        </div>
        
        <div class="form-options" v-if="!isEditing">
           <label class="checkbox-label">
              <input type="checkbox" v-model="form.is_current" />
              <span>设为当前阶段</span>
           </label>
        </div>

        <div class="dialog-footer">
          <button type="button" class="btn ghost" @click="dialogVisible = false">取消</button>
          <button type="submit" class="btn primary" :disabled="loading">
            {{ loading ? "保存中..." : "保存" }}
          </button>
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
const dialogVisible = ref(false);
const isEditing = ref(false);

const form = ref({
  id: null,
  name: "",
  start_date: "",
  end_date: "",
  is_current: false,
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

function openCreate() {
  isEditing.value = false;
  form.value = {
    id: null,
    name: "",
    start_date: "",
    end_date: "",
    is_current: false,
  };
  dialogVisible.value = true;
}

function openEdit(stage) {
  isEditing.value = true;
  form.value = { ...stage };
  dialogVisible.value = true;
}

async function handleSubmit() {
  if (!form.value.name || !form.value.start_date) {
    ElMessage.warning("请填写必要信息");
    return;
  }

  loading.value = true;
  try {
    if (isEditing.value) {
      await stageAPI.update(form.value.id, {
        name: form.value.name,
        start_date: form.value.start_date,
        end_date: form.value.end_date,
      });
      ElMessage.success("更新成功");
    } else {
      await stageAPI.create(form.value);
      ElMessage.success("创建成功");
    }
    dialogVisible.value = false;
    await fetchStages();
  } catch (e) {
    console.error("Operation failed", e);
    ElMessage.error(isEditing.value ? "更新失败" : "创建失败");
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
.stage-container {
  max-width: 800px;
  margin: 0 auto;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.04);
}

.stage-header {
  padding: 24px 32px;
  background: linear-gradient(to right, #f8fafc, #ffffff);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f1f5f9;
}

.header-left h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
}

.header-left p {
  margin: 4px 0 0;
  color: #64748b;
  font-size: 13px;
}

.btn-create-compact {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-create-compact:hover {
  background: #1e293b;
  transform: translateY(-1px);
}

.stage-list {
  padding: 0;
}

.stage-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 32px;
  border-bottom: 1px solid #f1f5f9;
  transition: background-color 0.15s ease;
}

.stage-item:last-child {
  border-bottom: none;
}

.stage-item:hover {
  background: #f8fafc;
}

.stage-item.current {
  background: #f0fdf4;
}

.stage-item.current:hover {
  background: #dcfce7;
}

.stage-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.stage-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.stage-name {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
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
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.separator {
  color: #cbd5e1;
}

.stage-actions {
  display: flex;
  gap: 8px;
  opacity: 0; /* Hidden by default for cleaner look */
  transition: opacity 0.2s ease;
}

.stage-item:hover .stage-actions {
  opacity: 1;
}

/* Always show actions on mobile */
@media (max-width: 768px) {
  .stage-actions {
    opacity: 1;
  }
}

.action-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: #ffffff;
  color: #1c1c1e;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  border: 1px solid #e2e8f0;
}

.action-btn:hover {
  background: #f1f5f9;
  transform: translateY(-1px);
}

.action-btn.danger:hover {
  background: #fee2e2;
  color: #dc2626;
  border-color: #fecaca;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #94a3b8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 8px;
}

/* Dialog Styles */
.ios-input-group {
  background: #f8fafc;
  border-radius: 12px;
  padding: 0 16px;
  border: 1px solid #e2e8f0;
  margin-bottom: 20px;
}

.input-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e2e8f0;
}

.input-row:last-child {
  border-bottom: none;
}

.input-row label {
  width: 60px;
  font-size: 14px;
  font-weight: 500;
  color: #64748b;
}

.input-row input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #0f172a;
  padding: 0;
}

.form-options {
    margin-bottom: 24px;
    padding: 0 4px;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #475569;
    cursor: pointer;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 8px 20px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn.primary {
  background: #0f172a;
  color: white;
}

.btn.primary:hover {
  background: #1e293b;
}

.btn.ghost {
  background: transparent;
  color: #64748b;
}

.btn.ghost:hover {
  background: #f1f5f9;
  color: #0f172a;
}
</style>
