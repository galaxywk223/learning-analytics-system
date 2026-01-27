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
          <h4>阶段列表</h4>
        </div>
        <button class="btn-create-flat" @click="openCreate">
          <span class="icon">+</span> 新建阶段
        </button>
      </div>

      <!-- Stage List (Flat Table Style) -->
      <div v-if="stages.length" class="stage-list-flat">
        <div class="list-header">
          <span class="col-name">名称</span>
          <span class="col-date">时间范围</span>
          <span class="col-actions">操作</span>
        </div>

        <div
          v-for="stage in stages"
          :key="stage.id"
          class="stage-row"
          :class="{ current: stage.id === activeStageId }"
        >
          <!-- Name Column -->
          <div class="col-name">
            <span class="stage-name">{{ stage.name }}</span>
            <span v-if="stage.id === activeStageId" class="badge-current"
              >当前</span
            >
          </div>

          <!-- Date Column -->
          <div class="col-date">
            <span class="date-text">
              {{ formatDate(stage.start_date) }}
              <span class="range-sep">~</span>
              {{ getStageEndDate(stage.id) ? formatDate(getStageEndDate(stage.id)) : "至今" }}
            </span>
          </div>

          <!-- Actions Column -->
          <div class="col-actions">
            <div class="action-group">
              <button
                v-if="stage.id !== activeStageId"
                class="action-btn"
                title="设为当前"
                :disabled="loading"
                @click="applyStage(stage)"
              >
                🚩
              </button>
              <button
                class="action-btn"
                title="编辑"
                :disabled="loading"
                @click="openEdit(stage)"
              >
                ✏️
              </button>
              <button
                class="action-btn danger"
                title="删除"
                :disabled="loading"
                @click="confirmDelete(stage)"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">📭</div>
        <p>还没有创建任何阶段</p>
        <button class="btn-create-flat" @click="openCreate">立即创建</button>
      </div>
    </div>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑阶段' : '新建阶段'"
      width="420px"
      class="ios-dialog"
      destroy-on-close
      align-center
    >
      <form class="dialog-form" @submit.prevent="handleSubmit">
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
        </div>

        <div class="dialog-footer">
          <button
            type="button"
            class="pill-btn secondary"
            @click="dialogVisible = false"
          >
            取消
          </button>
          <button type="submit" class="pill-btn primary" :disabled="loading">
            {{ loading ? "保存" : "保存" }}
          </button>
        </div>
      </form>
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useStageStore } from "@/stores/modules/stage";
import { useSettingsStore } from "@/stores/modules/settings";
import { ElMessageBox, ElMessage } from "element-plus";
import PageContainer from "@/components/layout/PageContainer.vue";

const stageStore = useStageStore();
const settingsStore = useSettingsStore();

const loading = computed(() => stageStore.loading);
const stages = computed(() => stageStore.stages);
const activeStageId = computed(
  () => settingsStore.activeStageId || stageStore.activeStage?.id,
);

const dialogVisible = ref(false);
const isEditing = ref(false);
const form = ref({
  id: null,
  name: "",
  start_date: "",
});

onMounted(async () => {
  await stageStore.fetchStages();
  if (settingsStore.activeStageId) {
    const target = stages.value.find(
      (s) => s.id === settingsStore.activeStageId,
    );
    if (target) stageStore.setActiveStage(target);
  }
});

function toLocalDate(value) {
  if (!value) return null;
  if (value instanceof Date) return value;
  if (typeof value === "string") {
    const normalized = value.length >= 10 ? value.slice(0, 10) : value;
    return new Date(`${normalized}T00:00:00`);
  }
  return new Date(value);
}

function formatDate(d) {
  const date = toLocalDate(d);
  if (!date || Number.isNaN(date.getTime())) return "";
  return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(date.getDate()).padStart(2, "0")}`;
}

function addDays(dateValue, days) {
  const date = toLocalDate(dateValue);
  if (!date || Number.isNaN(date.getTime())) return null;
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}

function getStageEndDate(stageId) {
  const list = stages.value;
  const index = list.findIndex((s) => `${s.id}` === `${stageId}`);
  if (index <= 0) return null;
  const nextStart = list[index - 1]?.start_date;
  return nextStart ? addDays(nextStart, -1) : null;
}

function openCreate() {
  isEditing.value = false;
  form.value = {
    id: null,
    name: "",
    start_date: "",
  };
  dialogVisible.value = true;
}

function openEdit(stage) {
  isEditing.value = true;
  form.value = {
    id: stage.id,
    name: stage.name,
    start_date: String(stage.start_date).slice(0, 10),
  };
  dialogVisible.value = true;
}

async function handleSubmit() {
  if (!form.value.name || !form.value.start_date) {
    ElMessage.warning("请填写必要信息");
    return;
  }

  try {
    let ok = false;
    if (isEditing.value) {
      ok = await stageStore.updateStage(form.value.id, {
        name: form.value.name.trim(),
        start_date: form.value.start_date,
      });
      if (ok) ElMessage.success("更新成功");
    } else {
      ok = await stageStore.createStage({
        name: form.value.name.trim(),
        start_date: form.value.start_date,
      });
      if (ok) ElMessage.success("创建成功");
    }

    if (ok) {
      dialogVisible.value = false;
    }
  } catch (e) {
    console.error("Operation failed", e);
    ElMessage.error(isEditing.value ? "更新失败" : "创建失败");
  }
}

function applyStage(stage) {
  if (!stage) return;
  settingsStore.setActiveStage(stage.id);
  stageStore.setActiveStage(stage);
  ElMessage.success(`已切换到阶段："${stage.name}"`);
}

function confirmDelete(stage) {
  ElMessageBox.confirm(
    `确定要删除“${stage.name}”吗？这将删除其下所有记录。`,
    "删除确认",
    {
      type: "warning",
      confirmButtonText: "删除",
      cancelButtonText: "取消",
    },
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

<style scoped>
.stage-container {
  width: 100%; /* Full width */
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb; /* Flat border */
  overflow: hidden;
}

.stage-header {
  padding: 16px 24px;
  background: #f9fafb; /* Very light gray */
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e5e7eb;
}

.header-left h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #111827;
}

.btn-create-flat {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #ffffff;
  color: #111827;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.btn-create-flat:hover {
  background: #f3f4f6;
  border-color: #9ca3af;
}

/* Flat List Styles */
.stage-list-flat {
  display: flex;
  flex-direction: column;
}

.list-header {
  display: flex;
  padding: 12px 24px;
  background: #ffffff;
  border-bottom: 1px solid #f3f4f6;
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stage-row {
  display: flex;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.1s ease;
}

.stage-row:last-child {
  border-bottom: none;
}

.stage-row:hover {
  background: #f9fafb;
}

.stage-row.current {
  background: #f0fdf4; /* Very subtle green */
}

/* Columns */
.col-name {
  flex: 2;
  display: flex;
  align-items: center;
  gap: 8px;
}

.col-date {
  flex: 3;
  display: flex;
  align-items: center;
  gap: 8px;
  color: #4b5563;
  font-size: 14px;
}

.col-actions {
  flex: 1;
  display: flex;
  justify-content: flex-end;
}

/* Elements */
.stage-name {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.badge-current {
  font-size: 11px;
  font-weight: 600;
  color: #059669;
  background: #d1fae5;
  padding: 2px 8px;
  border-radius: 4px; /* Less rounded */
}

.separator {
  color: #9ca3af;
  font-size: 12px;
}

.date-text {
  font-variant-numeric: tabular-nums;
}

.text-present {
  color: #059669;
  font-weight: 500;
}

.action-group {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.15s ease;
}

.stage-row:hover .action-group {
  opacity: 1;
}

@media (max-width: 768px) {
  .action-group {
    opacity: 1;
  }

  .list-header {
    display: none; /* Hide header on mobile */
  }

  .stage-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .col-name,
  .col-date,
  .col-actions {
    width: 100%;
    flex: none;
  }

  .col-actions {
    justify-content: flex-start;
    margin-top: 4px;
  }
}

.action-btn {
  width: 28px;
  height: 28px;
  border-radius: 4px;
  border: 1px solid transparent;
  background: transparent;
  color: #6b7280;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s ease;
}

.action-btn:hover {
  background: #f3f4f6;
  color: #111827;
  border-color: #d1d5db;
}

.action-btn.danger:hover {
  background: #fef2f2;
  color: #dc2626;
  border-color: #fecaca;
}

.empty-state {
  text-align: center;
  padding: 60px 0;
  color: #9ca3af;
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
  background: #f9fafb;
  border-radius: 8px;
  padding: 0 16px;
  border: 1px solid #e5e7eb;
  margin-bottom: 20px;
}

.input-row {
  display: flex;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #e5e7eb;
}

.input-row:last-child {
  border-bottom: none;
}

.input-row label {
  width: 60px;
  font-size: 14px;
  font-weight: 500;
  color: #6b7280;
}

.input-row input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  color: #111827;
  padding: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
