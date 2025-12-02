<template>
  <PageContainer
    title="📒 学习记录"
    subtitle="在这里回顾每一次努力，见证成长的每一步。"
    :custom-class="'records-view'"
  >
    <template #actions>
      <div class="record-actions">
        <el-button-group>
          <el-button
            :type="currentSort === 'desc' ? 'primary' : ''"
            size="small"
            @click="changeSort('desc')"
          >
            降序
          </el-button>
          <el-button
            :type="currentSort === 'asc' ? 'primary' : ''"
            size="small"
            @click="changeSort('asc')"
          >
            升序
          </el-button>
        </el-button-group>
        <el-tooltip
          :disabled="canAddRecord"
          content="请先创建或选择一个阶段"
          placement="top"
        >
          <el-button
            type="primary"
            :disabled="!canAddRecord"
            @click="openAddDialog()"
          >
            添加新记录
          </el-button>
        </el-tooltip>
      </div>
    </template>

    <el-skeleton v-if="loading" :rows="4" :animated="false" />

    <EmptyState
      v-else-if="!structuredLogs.length"
      @add-record="openAddDialog"
    />

    <WeekAccordion
      v-else
      :weeks="structuredLogs"
      :active-weeks="activeWeeks"
      :expanded-notes="expandedNotes"
      @add-record="openAddDialog"
      @toggle-notes="toggleNotes"
      @edit-record="openEditDialog"
      @delete-record="handleDelete"
    />

    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '✏️ 编辑记录' : '➕ 添加新记录'"
      width="900px"
      @close="handleDialogClose"
      class="record-dialog"
      :append-to-body="true"
      :destroy-on-close="false"
      :close-on-click-modal="false"
    >
      <RecordForm
        ref="recordFormRef"
        :initial-data="currentRecord"
        :is-edit="isEditing"
        :loading="submitting"
        :default-date="defaultDate"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
    </el-dialog>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted, onActivated, watch } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
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
      await request.put(`/api/records/${currentRecord.value.id}`, {
        ...formData,
        stage_id: currentStage.value.id,
      });
      ElMessage.success("记录更新成功!");
    } else {
      // 创建新记录
      await request.post("/api/records", {
        ...formData,
        stage_id: currentStage.value.id,
      });
      ElMessage.success("记录添加成功!");
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
  }
);
</script>

<style scoped lang="scss">
.record-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.record-dialog {
  :deep(.el-dialog) {
    border-radius: 12px;
    overflow: hidden;
  }

  :deep(.el-dialog__header) {
    padding: 20px 24px;
    margin: 0;
    border-bottom: 1px solid #e5e7eb;
    background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  }

  :deep(.el-dialog__title) {
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }

  :deep(.el-dialog__body) {
    padding: 20px 24px;
  }

  :deep(.el-dialog__footer) {
    padding: 16px 24px;
    border-top: 1px solid #e5e7eb;
  }
}
</style>
