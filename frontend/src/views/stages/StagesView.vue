<template>
  <div class="ios-view">
    <PageContainer
      :title="{ icon: '🚩', text: '阶段管理' }"
      subtitle="创建、切换、编辑和删除您的学习阶段。"
    >
      <div class="ios-content-wrapper">
        <!-- Create New Stage Card -->
        <div class="ios-card create-card">
          <div class="card-header">
            <h3 class="card-title">创建新阶段</h3>
          </div>
          <div class="card-body">
            <el-form
              :model="createForm"
              ref="createFormRef"
              class="ios-form"
              @submit.prevent="onCreateStage"
            >
              <div class="form-group">
                <label class="form-label">阶段名称</label>
                <el-input
                  v-model="createForm.name"
                  placeholder="例如：大三上学期"
                  maxlength="100"
                  class="ios-input"
                />
              </div>
              <div class="form-group">
                <label class="form-label">起始日期</label>
                <div class="picker-wrapper">
                  <button class="ios-picker-btn" @click="openCreateDatePicker" type="button">
                    <span class="icon">📅</span>
                    <span class="value">{{ createForm.start_date || '选择日期' }}</span>
                    <el-icon class="arrow"><ArrowRight /></el-icon>
                  </button>
                  <el-date-picker
                    ref="createDatePickerRef"
                    v-model="createForm.start_date"
                    type="date"
                    value-format="YYYY-MM-DD"
                    class="hidden-date-input"
                  />
                </div>
              </div>
              <div class="form-actions">
                <button 
                  class="ios-btn primary full-width" 
                  :disabled="creating" 
                  @click.prevent="onCreateStage"
                >
                  <span v-if="creating">创建中...</span>
                  <span v-else>创建阶段</span>
                </button>
              </div>
            </el-form>
          </div>
        </div>

        <!-- Existing Stages List -->
        <div class="ios-card list-card">
          <div class="card-header">
            <h3 class="card-title">已有阶段</h3>
          </div>
          
          <div v-if="loading" class="loading-wrapper">
            <el-skeleton :rows="3" animated />
          </div>
          <div v-else class="card-body no-padding">
            <div v-if="stages.length > 0" class="ios-list">
              <div 
                v-for="stage in stages" 
                :key="stage.id" 
                class="ios-list-item"
                :class="{ 'is-active': stage.id === activeStageId }"
              >
                <div class="item-content">
                  <div class="item-main">
                    <h4 class="item-title">{{ stage.name }}</h4>
                    <span class="item-subtitle">起始于 {{ formatDate(stage.start_date) }}</span>
                  </div>
                  <div class="item-status" v-if="stage.id === activeStageId">
                    <span class="status-badge">当前阶段</span>
                  </div>
                </div>
                
                <div class="item-actions">
                  <el-tooltip content="应用此阶段" placement="top" :show-after="500">
                    <button 
                      class="action-btn apply"
                      :disabled="stage.id === activeStageId"
                      @click="applyStage(stage)"
                    >
                      <Icon icon="lucide:flag" />
                    </button>
                  </el-tooltip>
                  
                  <el-tooltip content="编辑" placement="top" :show-after="500">
                    <button class="action-btn edit" @click="openEdit(stage)">
                      <Icon icon="lucide:pencil" />
                    </button>
                  </el-tooltip>
                  
                  <el-tooltip content="删除" placement="top" :show-after="500">
                    <button class="action-btn delete" @click="confirmDelete(stage)">
                      <Icon icon="lucide:trash-2" />
                    </button>
                  </el-tooltip>
                </div>
              </div>
            </div>
            <div v-else class="empty-state">
              <span class="emoji">📭</span>
              <p>暂无阶段数据</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Edit Dialog -->
      <el-dialog
        v-model="editDialog.visible"
        title="编辑阶段"
        width="90%"
        class="ios-dialog"
        destroy-on-close
        align-center
      >
        <el-form :model="editDialog.form" ref="editFormRef" class="ios-form">
          <div class="form-group">
            <label class="form-label">阶段名称</label>
            <el-input 
              v-model="editDialog.form.name" 
              maxlength="100" 
              class="ios-input"
            />
          </div>
          <div class="form-group">
            <label class="form-label">起始日期</label>
            <div class="picker-wrapper">
              <button class="ios-picker-btn" @click="openEditDatePicker" type="button">
                <span class="icon">📅</span>
                <span class="value">{{ editDialog.form.start_date || '选择日期' }}</span>
                <el-icon class="arrow"><ArrowRight /></el-icon>
              </button>
              <el-date-picker
                ref="editDatePickerRef"
                v-model="editDialog.form.start_date"
                type="date"
                value-format="YYYY-MM-DD"
                class="hidden-date-input"
              />
            </div>
          </div>
        </el-form>
        <template #footer>
          <div class="dialog-footer">
            <button class="ios-btn ghost" @click="editDialog.visible = false">取消</button>
            <button class="ios-btn primary" :disabled="updating" @click="onUpdateStage">
              {{ updating ? '保存中...' : '保存更改' }}
            </button>
          </div>
        </template>
      </el-dialog>
    </PageContainer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useStageStore } from "@/stores/modules/stage";
import { useSettingsStore } from "@/stores/modules/settings";
import { ElMessageBox, ElMessage } from "element-plus";
import { Icon } from "@iconify/vue";
import { ArrowRight } from "@element-plus/icons-vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const stageStore = useStageStore();
const settingsStore = useSettingsStore();

const loading = computed(() => stageStore.loading);
const stages = computed(() => stageStore.stages);
const activeStageId = computed(
  () => settingsStore.activeStageId || stageStore.activeStage?.id
);

// Create Form
const createForm = ref({ name: "", start_date: "" });
const createFormRef = ref();
const createDatePickerRef = ref();
const creating = ref(false);

// Edit Dialog
const editDialog = ref({
  visible: false,
  form: { id: null, name: "", start_date: "" },
});
const editFormRef = ref();
const editDatePickerRef = ref();
const updating = ref(false);

onMounted(async () => {
  await stageStore.fetchStages();
  if (settingsStore.activeStageId) {
    const target = stages.value.find(
      (s) => s.id === settingsStore.activeStageId
    );
    if (target) stageStore.setActiveStage(target);
  }
});

function formatDate(d) {
  if (!d) return "";
  return String(d).slice(0, 10);
}

function openCreateDatePicker() {
  createDatePickerRef.value?.focus();
  createDatePickerRef.value?.handleOpen();
}

function openEditDatePicker() {
  editDatePickerRef.value?.focus();
  editDatePickerRef.value?.handleOpen();
}

async function onCreateStage() {
  if (!createForm.value.name || !createForm.value.start_date) {
    ElMessage.error("阶段名称和起始日期均不能为空。");
    return;
  }
  creating.value = true;
  const ok = await stageStore.createStage({
    name: createForm.value.name.trim(),
    start_date: createForm.value.start_date,
  });
  creating.value = false;
  if (ok) {
    createForm.value.name = "";
    createForm.value.start_date = "";
    ElMessage.success("创建成功");
  }
}

function applyStage(stage) {
  if (!stage) return;
  settingsStore.setActiveStage(stage.id);
  stageStore.setActiveStage(stage);
  ElMessage.success(`已切换到阶段："${stage.name}"`);
}

function openEdit(stage) {
  editDialog.value.form.id = stage.id;
  editDialog.value.form.name = stage.name;
  editDialog.value.form.start_date = formatDate(stage.start_date);
  editDialog.value.visible = true;
}

async function onUpdateStage() {
  const { id, name, start_date } = editDialog.value.form;
  if (!name) {
    ElMessage.error("阶段名称不能为空。");
    return;
  }
  updating.value = true;
  const ok = await stageStore.updateStage(id, {
    name: name.trim(),
    start_date,
  });
  updating.value = false;
  if (ok) {
    editDialog.value.visible = false;
    ElMessage.success("更新成功");
  }
}

function confirmDelete(stage) {
  ElMessageBox.confirm(
    `警告：删除阶段将永久删除其下所有学习记录！确定要删除“${stage.name}”吗？`,
    "删除确认",
    { 
      type: "warning", 
      confirmButtonText: "删除", 
      cancelButtonText: "取消",
      confirmButtonClass: "el-button--danger"
    }
  )
    .then(async () => {
      const ok = await stageStore.deleteStage(stage.id);
      if (ok) {
        ElMessage.success("删除成功");
        if (stage.id === settingsStore.activeStageId) {
          const next = stages.value[0];
          if (next) {
            settingsStore.setActiveStage(next.id);
            stageStore.setActiveStage(next);
          } else {
            settingsStore.setActiveStage(0);
          }
        }
      }
    })
    .catch(() => {});
}
</script>

<style scoped lang="scss">
.ios-view {
  min-height: 100%;
  background-color: transparent; /* Allow global background to show */
}

.ios-content-wrapper {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding-bottom: 40px;
}

/* --- iOS Card Generic --- */
.ios-card {
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  overflow: hidden;
  
  .card-header {
    padding: 20px 24px;
    border-bottom: 1px solid #f2f2f7;
    
    .card-title {
      margin: 0;
      font-size: 18px;
      font-weight: 700;
      color: #1c1c1e;
    }
  }
  
  .card-body {
    padding: 24px;
    
    &.no-padding {
      padding: 0;
    }
  }
}

/* --- Form Styles --- */
.ios-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  
  .form-label {
    font-size: 13px;
    font-weight: 600;
    color: #8e8e93;
    margin-left: 4px;
  }
}

.ios-input {
  :deep(.el-input__wrapper) {
    background-color: #f2f2f7;
    border-radius: 12px;
    box-shadow: none !important;
    padding: 8px 16px;
    height: 44px;
  }
  
  :deep(.el-input__inner) {
    font-weight: 500;
    color: #1c1c1e;
  }
}

.picker-wrapper {
  position: relative;
}

.ios-picker-btn {
  background: #f2f2f7;
  border: none;
  padding: 10px 16px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.2s;
  width: 100%;
  height: 44px;

  &:hover {
    background: #e5e5ea;
  }

  .icon {
    font-size: 16px;
  }

  .value {
    font-size: 15px;
    font-weight: 500;
    color: #007aff;
    flex: 1;
    text-align: left;
  }

  .arrow {
    font-size: 14px;
    color: #c7c7cc;
  }
}

:deep(.hidden-date-input) {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  opacity: 0;
  pointer-events: none;
  
  .el-input__wrapper {
    padding: 0;
  }
}

/* --- Buttons --- */
.ios-btn {
  border: none;
  padding: 12px 24px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.1s, opacity 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  &:active {
    transform: scale(0.98);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &.primary {
    background: #007aff;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 122, 255, 0.3);

    &:hover:not(:disabled) {
      background: #006ce6;
    }
  }
  
  &.ghost {
    background: #f2f2f7;
    color: #8e8e93;
    
    &:hover:not(:disabled) {
      background: #e5e5ea;
      color: #1c1c1e;
    }
  }

  &.full-width {
    width: 100%;
  }
}

/* --- List Styles --- */
.ios-list {
  display: flex;
  flex-direction: column;
}

.ios-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #f2f2f7;
  transition: background 0.2s;
  
  &:last-child {
    border-bottom: none;
  }
  
  &:hover {
    background-color: #f9f9f9;
  }
  
  &.is-active {
    background-color: #f0f7ff;
    
    .item-title {
      color: #007aff;
    }
  }
}

.item-content {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.item-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  
  .item-title {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #1c1c1e;
  }
  
  .item-subtitle {
    font-size: 13px;
    color: #8e8e93;
  }
}

.status-badge {
  padding: 4px 10px;
  background: #34c759;
  color: white;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
}

.item-actions {
  display: flex;
  gap: 8px;
  margin-left: 16px;
}

.action-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: none;
  display: grid;
  place-items: center;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
  
  &.apply {
    background: #e8f8f0;
    color: #34c759;
    &:hover:not(:disabled) { background: #34c759; color: white; }
    &:disabled { opacity: 0.3; cursor: default; }
  }
  
  &.edit {
    background: #f2f2f7;
    color: #007aff;
    &:hover { background: #007aff; color: white; }
  }
  
  &.delete {
    background: #fff2f2;
    color: #ff3b30;
    &:hover { background: #ff3b30; color: white; }
  }
}

.empty-state {
  padding: 48px;
  text-align: center;
  color: #c7c7cc;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  
  .emoji {
    font-size: 48px;
    opacity: 0.5;
  }
  
  p {
    font-size: 15px;
    font-weight: 500;
  }
}

/* --- Dialog --- */
.ios-dialog {
  :deep(.el-dialog) {
    border-radius: 20px;
    overflow: hidden;
  }
  
  :deep(.el-dialog__header) {
    margin: 0;
    padding: 20px 24px;
    border-bottom: 1px solid #f2f2f7;
    
    .el-dialog__title {
      font-weight: 700;
      font-size: 18px;
    }
  }
  
  :deep(.el-dialog__body) {
    padding: 24px;
  }
  
  :deep(.el-dialog__footer) {
    padding: 20px 24px;
    border-top: 1px solid #f2f2f7;
  }
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

@media (max-width: 640px) {
  .ios-list-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }
  
  .item-actions {
    width: 100%;
    justify-content: flex-end;
    margin-left: 0;
    padding-top: 12px;
    border-top: 1px dashed #f2f2f7;
  }
}
</style>
