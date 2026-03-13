<template>
  <PageContainer
    :title="{ icon: 'lucide:notebook-tabs', text: '学习记录' }"
    subtitle="在这里回顾每一次努力，见证成长的每一步。"
    :custom-class="'records-view'"
    max-width="wide"
    sticky-actions
  >
    <template #actions>
      <div class="records-toolbar desktop-actions">
        <span class="records-stage-chip">
          {{ currentStage?.name || "未选择阶段" }}
        </span>
        <button class="pill-btn secondary" type="button" @click="shuffleCategoryColors">
          <Icon icon="lucide:shuffle" />
          打乱色系
        </button>
        <button class="pill-btn secondary" type="button" @click="toggleSort">
          <Icon icon="lucide:arrow-up-down" />
          {{ currentSort === "desc" ? "最新优先" : "最早优先" }}
        </button>
        <button
          class="pill-btn primary"
          type="button"
          :disabled="!canAddRecord"
          @click="openAddDialog()"
        >
          <Icon icon="lucide:plus" />
          添加记录
        </button>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="4" :animated="false" />

    <EmptyState
      v-else-if="!structuredLogs.length"
      @add-record="openAddDialog"
    />

    <template v-else>
      <div class="records-shell">
        <WeekAccordion
          :weeks="structuredLogs"
          :active-weeks="activeWeeks"
          :expanded-notes="expandedNotes"
          :color-seed="colorSeed"
          @add-record="openAddDialog"
          @toggle-notes="toggleNotes"
          @edit-record="openEditDialog"
          @delete-record="handleDelete"
        />
      </div>
    </template>

    <el-dialog
      v-model="dialogVisible"
      :show-close="false"
      width="600px"
      class="ios-dialog-modal"
      align-center
      destroy-on-close
      :close-on-click-modal="false"
      @close="handleDialogClose"
    >
      <div class="ios-dialog-content">
        <div class="ios-dialog-header">
          <h3 class="ios-dialog-title">
            {{ isEditing ? "编辑记录" : "添加新记录" }}
          </h3>
        </div>

        <RecordForm
          ref="recordFormRef"
          :initial-data="currentRecord"
          :is-edit="isEditing"
          :loading="submitting"
          :default-date="defaultDate"
          @submit="handleSubmit"
          @cancel="dialogVisible = false"
        />
      </div>
    </el-dialog>

    <div class="floating-actions">
      <button
        class="fab fab-shuffle"
        type="button"
        title="打乱分类色系"
        @click="shuffleCategoryColors"
      >
        <Icon icon="lucide:shuffle" />
      </button>
      <button
        class="fab fab-sort"
        type="button"
        title="切换排序"
        @click="toggleSort"
      >
        <Icon icon="lucide:arrow-up-down" />
      </button>
      <button
        class="fab fab-add"
        type="button"
        :disabled="!canAddRecord"
        title="添加记录"
        @click="openAddDialog()"
      >
        <Icon icon="lucide:plus" />
      </button>
    </div>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Icon } from "@iconify/vue";
import RecordForm from "@/components/business/records/RecordForm.vue";
import EmptyState from "@/components/business/records/EmptyState.vue";
import WeekAccordion from "@/components/business/records/WeekAccordion.vue";
import { useStageStore } from "@/stores/modules/stage";
import request from "@/utils/request";
import PageContainer from "@/components/layout/PageContainer.vue";

const stagesStore = useStageStore();

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const currentRecord = ref(null);
const defaultDate = ref(null);
const structuredLogs = ref([]);
const currentSort = ref("desc");
const activeWeeks = ref([]);
const expandedNotes = ref([]); // 记录展开的笔记ID
const recordFormRef = ref(null);
const categoryColorSeedStorageKey = "records-category-color-seed";

const createCategoryColorSeed = () =>
  `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

const readCategoryColorSeed = () => {
  if (typeof window === "undefined") {
    return createCategoryColorSeed();
  }
  return (
    window.localStorage.getItem(categoryColorSeedStorageKey) ||
    createCategoryColorSeed()
  );
};

const colorSeed = ref(readCategoryColorSeed());

const isEditing = computed(() => !!currentRecord.value?.id);
// 是否可以添加记录（阶段已加载并选定）
const canAddRecord = computed(() => {
  return !!currentStage.value?.id && !stagesStore.loading;
});

// 获取当前活动阶段
const currentStage = computed(() => stagesStore.activeStage);

// 加载结构化记录
const stageWarningShown = ref(false);
const lastLoadedAt = ref(0);
const initialized = ref(false);

const loadRecords = async (force = false) => {
  if (!currentStage.value?.id) {
    if (!stageWarningShown.value) {
      ElMessage.warning("请先创建一个学习阶段");
      stageWarningShown.value = true;
    }
    return;
  }

  if (!force && Date.now() - lastLoadedAt.value < 10_000) {
    return;
  }

  loading.value = true;
  try {
    const response = await request.get("/api/records/structured", {
      params: {
        stage_id: currentStage.value.id,
        sort: currentSort.value,
      },
    });

    if (response.success) {
      structuredLogs.value = response.data || [];
      if (structuredLogs.value.length > 0) {
        const firstWeek = structuredLogs.value[0];
        activeWeeks.value = [`${firstWeek.year}-${firstWeek.week_num}`];
      } else {
        activeWeeks.value = [];
      }
      lastLoadedAt.value = Date.now();
    }
  } catch (error) {
    console.error("加载记录失败:", error);
    ElMessage.error("加载记录失败");
  } finally {
    loading.value = false;
  }
};

// 改变排序
const changeSort = (sort) => {
  currentSort.value = sort;
  loadRecords(true);
};

const toggleSort = () => {
  currentSort.value = currentSort.value === "desc" ? "asc" : "desc";
  loadRecords(true);
};

const shuffleCategoryColors = () => {
  colorSeed.value = createCategoryColorSeed();
  if (typeof window !== "undefined") {
    window.localStorage.setItem(categoryColorSeedStorageKey, colorSeed.value);
  }
  ElMessage.success("分类色系已重新打乱");
};

// 归一化日期（过滤事件对象）
const normalizeDate = (raw) => {
  if (!raw) return null;
  if (typeof raw === "object" && raw instanceof Event) return null; // 忽略事件
  return raw;
};

// 打开添加对话框
const openAddDialog = (date = null) => {
  if (!currentStage.value?.id) {
    ElMessage.warning("请先创建或选择一个学习阶段再添加记录");
    return;
  }
  currentRecord.value = null;
  defaultDate.value = normalizeDate(date);
  dialogVisible.value = true;
  if (recordFormRef.value?.resetForm) {
    recordFormRef.value.resetForm();
  }
};

// 打开编辑对话框
const openEditDialog = async (record) => {
  dialogVisible.value = true;
  defaultDate.value = null;
  currentRecord.value = null;

  try {
    const detail = await request.get(`/api/records/${record.id}`);
    if (detail?.success && detail.data) {
      currentRecord.value = detail.data;
    } else {
      currentRecord.value = { ...record };
    }
  } catch (error) {
    console.error("获取记录详情失败:", error);
    currentRecord.value = { ...record };
  }
};

// 关闭对话框时重置状态
const handleDialogClose = () => {
  currentRecord.value = null;
  defaultDate.value = null;
};

// 提交表单
const handleSubmit = async (formData) => {
  submitting.value = true;
  try {
    if (isEditing.value) {
      // 更新记录
      const response = await request.put(`/api/records/${currentRecord.value.id}`, {
        ...formData,
      });
      ElMessage.success("记录更新成功!");
      const resolvedStageId = response?.data?.stage_id || response?.data?.stage?.id;
      if (resolvedStageId && `${resolvedStageId}` !== `${currentStage.value.id}`) {
        if (!stagesStore.stages.length) {
          await stagesStore.fetchStages(true);
        }
        let targetStage = stagesStore.stages.find(
          (stage) => `${stage.id}` === `${resolvedStageId}`,
        );
        if (!targetStage) {
          await stagesStore.fetchStages(true);
          targetStage = stagesStore.stages.find(
            (stage) => `${stage.id}` === `${resolvedStageId}`,
          );
        }
        if (targetStage) {
          stagesStore.setActiveStage(targetStage);
          ElMessage.info(`该记录已按日期归类到阶段：${targetStage.name}`);
        }
      }
    } else {
      // 创建新记录
      const response = await request.post("/api/records", {
        ...formData,
      });
      ElMessage.success("记录添加成功!");
      const resolvedStageId = response?.data?.stage_id || response?.data?.stage?.id;
      if (resolvedStageId && `${resolvedStageId}` !== `${currentStage.value.id}`) {
        if (!stagesStore.stages.length) {
          await stagesStore.fetchStages(true);
        }
        let targetStage = stagesStore.stages.find(
          (stage) => `${stage.id}` === `${resolvedStageId}`,
        );
        if (!targetStage) {
          await stagesStore.fetchStages(true);
          targetStage = stagesStore.stages.find(
            (stage) => `${stage.id}` === `${resolvedStageId}`,
          );
        }
        if (targetStage) {
          stagesStore.setActiveStage(targetStage);
          ElMessage.info(`该记录已按日期归类到阶段：${targetStage.name}`);
        }
      }
    }
    dialogVisible.value = false;
    loadRecords(true);
  } catch (error) {
    console.error("保存失败:", error);
    ElMessage.error("操作失败，请重试");
  } finally {
    submitting.value = false;
  }
};

// 删除记录
const handleDelete = async (record) => {
  try {
    await ElMessageBox.confirm(`确定删除该条记录？`, "提示", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    });
    const response = await request.delete(`/api/records/${record.id}`);
    if (response.success) {
      ElMessage.success("删除成功");
      loadRecords(true);
    }
  } catch (error) {
    console.error("删除失败:", error);
    if (error !== "cancel") {
      ElMessage.error("删除失败");
    }
  }
};

// 切换笔记展开
const toggleNotes = (recordId) => {
  const index = expandedNotes.value.indexOf(recordId);
  if (index === -1) {
    expandedNotes.value.push(recordId);
  } else {
    expandedNotes.value.splice(index, 1);
  }
};

onMounted(async () => {
  await stagesStore.fetchStages();
  initialized.value = true;
  if (stagesStore.activeStage?.id) {
    loadRecords(true);
  }
});

onActivated(() => {
  if (!loading.value && currentStage.value?.id) {
    loadRecords(false);
  }
});

watch(
  () => currentStage.value?.id,
  (id, previous) => {
    if (!id || !initialized.value) return;
    if (id !== previous) {
      stageWarningShown.value = false;
      loadRecords(true);
    }
  },
);
</script>

<style scoped lang="scss">
.records-toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.records-stage-chip {
  display: inline-flex;
  align-items: center;
  min-height: 40px;
  padding: 0 14px;
  border-radius: var(--radius-pill);
  border: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--bg-surface) 88%, var(--brand-primary-soft));
  color: var(--text-secondary);
  font-weight: 600;
}

.record-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* iOS Dialog Styles */
:deep(.ios-dialog-modal) {
  .el-dialog {
    background: var(--surface-card);
    border: 1px solid var(--stroke-soft);
    border-radius: 14px;
    box-shadow: var(--box-shadow-hover);
    padding: 0;
    overflow: hidden;

    .el-dialog__header {
      display: none;
    }

    .el-dialog__body {
      padding: 0;
    }
  }
}

.ios-dialog-content {
  display: flex;
  flex-direction: column;
}

.ios-dialog-header {
  padding: 20px 20px 10px;
  text-align: center;

  .ios-dialog-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--color-text-heading);
    margin: 0;
  }
}

.records-shell {
  position: relative;
}

.floating-actions {
  position: fixed;
  right: clamp(18px, 3vw, 36px);
  bottom: clamp(18px, 3vw, 36px);
  display: flex;
  flex-direction: column-reverse;
  align-items: center;
  gap: 10px;
  padding: 12px 10px;
  border-radius: 26px;
  border: 1px solid color-mix(in srgb, var(--color-primary) 12%, var(--color-border-card));
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--surface-card) 92%, rgba(255, 255, 255, 0.04)) 0%,
    color-mix(in srgb, var(--surface-card-strong) 96%, rgba(15, 23, 42, 0.12)) 100%
  );
  box-shadow:
    0 18px 38px -26px rgba(15, 23, 42, 0.58),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(16px);
  z-index: 1200;
}

.desktop-actions {
  display: flex;
}

.fab {
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  backdrop-filter: blur(12px);
  transition:
    transform 0.18s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
}

.fab-add {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: linear-gradient(
    135deg,
    var(--color-primary) 0%,
    var(--color-primary-dark) 100%
  );
  color: var(--color-text-light);
  box-shadow: var(--box-shadow-hover);
  border: 1px solid var(--stroke-strong);

  &:hover {
    transform: translateY(-2px);
    box-shadow: var(--box-shadow-hover);
    filter: brightness(1.05);
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
    transform: none;
    box-shadow: var(--box-shadow);
    filter: none;
  }

  :deep(svg) {
    width: 26px;
    height: 26px;
  }
}

.fab-sort {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-card) 88%, rgba(255, 255, 255, 0.04));
  color: var(--color-text-base);
  border: 1px solid var(--color-border-card);
  box-shadow: var(--box-shadow);

  &:hover {
    transform: translateY(-1px);
    box-shadow: var(--box-shadow-hover);
    color: var(--color-primary);
  }

  :deep(svg) {
    width: 18px;
    height: 18px;
  }
}

.fab-shuffle {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface-card) 88%, rgba(255, 255, 255, 0.04));
  color: var(--color-text-base);
  border: 1px solid var(--color-border-card);
  box-shadow: var(--box-shadow);

  &:hover {
    transform: translateY(-1px);
    box-shadow: var(--box-shadow-hover);
    color: var(--color-primary);
  }

  :deep(svg) {
    width: 18px;
    height: 18px;
  }
}

@media (max-width: 640px) {
  .desktop-actions {
    display: none;
  }

  .floating-actions {
    right: 16px;
    bottom: 16px;
  }
}

@media (min-width: 641px) {
  .floating-actions {
    display: none;
  }
}
</style>
