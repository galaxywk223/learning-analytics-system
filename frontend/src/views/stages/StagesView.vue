<template>
  <PageContainer
    title="🚩 阶段管理"
    subtitle="创建、切换、编辑和删除您的学习阶段（完全对齐旧版页面）。"
    :custom-class="'stage-management'"
  >

    <!-- 创建新阶段 -->
    <el-card class="stage-card">
      <template #header>
        <div class="card-header-inner">
          <h5 class="card-title">创建新阶段</h5>
        </div>
      </template>
      <el-form
        :model="createForm"
        ref="createFormRef"
        label-width="80px"
        class="create-form"
        @submit.prevent="onCreateStage"
      >
        <div class="form-row">
          <el-form-item
            label="阶段名称"
            prop="name"
            :rules="[
              { required: true, message: '请输入阶段名称', trigger: 'blur' },
            ]"
          >
            <el-input
              v-model="createForm.name"
              placeholder="例如：大三上学期"
              maxlength="100"
            />
          </el-form-item>
          <el-form-item
            label="起始日期"
            prop="start_date"
            :rules="[
              { required: true, message: '请选择起始日期', trigger: 'change' },
            ]"
          >
            <el-date-picker
              v-model="createForm.start_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
          <div class="create-actions">
            <el-button type="primary" :loading="creating" @click="onCreateStage"
              >创建</el-button
            >
          </div>
        </div>
      </el-form>
    </el-card>

    <!-- 已有阶段列表 -->
    <el-card class="stage-card mt24">
      <template #header>
        <div class="card-header-inner">
          <h5 class="card-title">已有阶段</h5>
        </div>
      </template>

      <div v-if="loading" class="loading-wrapper">
        <el-skeleton :rows="3" animated />
      </div>
      <div v-else>
        <template v-if="stages.length > 0">
          <div class="stage-list">
            <div v-for="stage in stages" :key="stage.id" class="stage-item">
              <div class="stage-info">
                <h6
                  class="stage-name"
                  :class="{ active: stage.id === activeStageId }"
                >
                  {{ stage.name }}
                  <el-tag
                    v-if="stage.id === activeStageId"
                    size="small"
                    type="success"
                    >当前</el-tag
                  >
                </h6>
                <small class="text-muted"
                  >起始于: {{ formatDate(stage.start_date) }}</small
                >
              </div>
              <div class="item-actions">
                <!-- 应用阶段 -->
                <el-tooltip content="应用此阶段" placement="top">
                  <el-button
                    size="small"
                    type="success"
                    circle
                    @click="applyStage(stage)"
                    :disabled="stage.id === activeStageId"
                  >
                    <Icon icon="lucide:flag" />
                  </el-button>
                </el-tooltip>
                <!-- 编辑阶段名称 -->
                <el-tooltip content="编辑" placement="top">
                  <el-button
                    size="small"
                    type="info"
                    circle
                    @click="openEdit(stage)"
                  >
                    <Icon icon="lucide:pencil" />
                  </el-button>
                </el-tooltip>
                <!-- 删除阶段 -->
                <el-tooltip content="删除" placement="top">
                  <el-button
                    size="small"
                    type="danger"
                    circle
                    @click="confirmDelete(stage)"
                  >
                    <Icon icon="lucide:trash-2" />
                  </el-button>
                </el-tooltip>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="empty-placeholder">您还没有创建任何阶段。</div>
      </div>
    </el-card>

    <!-- 编辑阶段对话框 -->
    <el-dialog
      v-model="editDialog.visible"
      title="编辑阶段名称"
      width="480px"
      :close-on-click-modal="false"
    >
      <el-form :model="editDialog.form" ref="editFormRef" label-width="80px">
        <el-form-item
          label="新名称"
          prop="name"
          :rules="[
            { required: true, message: '请输入新名称', trigger: 'blur' },
          ]"
        >
          <el-input v-model="editDialog.form.name" maxlength="100" />
        </el-form-item>
        <el-form-item
          label="起始日期"
          prop="start_date"
          :rules="[
            { required: true, message: '请选择日期', trigger: 'change' },
          ]"
        >
          <el-date-picker
            v-model="editDialog.form.start_date"
            type="date"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="updating" @click="onUpdateStage"
          >保存更改</el-button
        >
      </template>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useStageStore } from "@/stores/modules/stage";
import { useSettingsStore } from "@/stores/modules/settings";
import { ElMessageBox, ElMessage } from "element-plus";
import { Icon } from "@iconify/vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const stageStore = useStageStore();
const settingsStore = useSettingsStore();

const loading = computed(() => stageStore.loading);
const stages = computed(() => stageStore.stages);
const activeStageId = computed(
  () => settingsStore.activeStageId || stageStore.activeStage?.id
);

// 创建表单
const createForm = ref({ name: "", start_date: "" });
const createFormRef = ref();
const creating = ref(false);

// 编辑对话框
const editDialog = ref({
  visible: false,
  form: { id: null, name: "", start_date: "" },
});
const editFormRef = ref();
const updating = ref(false);

onMounted(async () => {
  await stageStore.fetchStages();
  // 若 settings 中已有 activeStageId，确保 stageStore.activeStage 对齐
  if (settingsStore.activeStageId) {
    const target = stages.value.find(
      (s) => s.id === settingsStore.activeStageId
    );
    if (target) stageStore.setActiveStage(target);
  }
});

function formatDate(d) {
  if (!d) return "";
  // d 可能是 '2024-10-01' 或 ISO 字符串
  return String(d).slice(0, 10);
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
    // 重置表单
    createForm.value.name = "";
    createForm.value.start_date = "";
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
  }
}

function confirmDelete(stage) {
  ElMessageBox.confirm(
    `警告：删除阶段将永久删除其下所有学习记录！确定要删除“${stage.name}”吗？`,
    "删除确认",
    { type: "warning", confirmButtonText: "删除", cancelButtonText: "取消" }
  )
    .then(async () => {
      const ok = await stageStore.deleteStage(stage.id);
      if (ok && stage.id === settingsStore.activeStageId) {
        // 切换到新的活动阶段或清空
        const next = stages.value[0];
        if (next) {
          settingsStore.setActiveStage(next.id);
          stageStore.setActiveStage(next);
        } else {
          settingsStore.setActiveStage(0);
        }
      }
    })
    .catch(() => {});
}
</script>

<style scoped>
.stage-card {
  margin-bottom: 0.5rem;
}
.card-header-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.form-row {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
}
.create-form :deep(.el-form-item) {
  margin-bottom: 0;
}
.create-actions {
  display: flex;
  align-items: center;
  padding-bottom: 4px;
}

.mt24 {
  margin-top: 24px;
}

.stage-list {
  display: flex;
  flex-direction: column;
}
.stage-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 12px;
  border-bottom: 1px solid #f0f2f5;
}
.stage-item:last-child {
  border-bottom: none;
}
.stage-info {
  display: flex;
  flex-direction: column;
}
.stage-name {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  gap: 6px;
  align-items: center;
}
.stage-name.active {
  color: #409eff;
}
.text-muted {
  color: #888;
  font-size: 12px;
}

.item-actions {
  display: flex;
  gap: 8px;
}

.empty-placeholder {
  text-align: center;
  padding: 28px 0;
  color: #999;
  font-size: 14px;
}
.loading-wrapper {
  padding: 12px;
}

@media (max-width: 640px) {
  .form-row {
    flex-direction: column;
    align-items: stretch;
  }
  .create-actions {
    padding-left: 0;
  }
  .stage-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .item-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
