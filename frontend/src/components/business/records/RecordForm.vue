<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    @submit.prevent="submitForm"
    class="record-form"
  >
    <!-- 基本信息卡片 -->
    <div class="form-section">
      <div class="section-title">
        <Icon icon="lucide:file-text" class="section-icon" />
        <span>基本信息</span>
      </div>

      <!-- 任务名称 -->
      <el-form-item label="任务名称" prop="task">
        <el-input
          v-model="form.task"
          placeholder="例如：学习 Vue Router"
          size="large"
          clearable
        >
          <template #prefix>
            <Icon icon="lucide:check-square" />
          </template>
        </el-input>
      </el-form-item>

      <!-- 日期、时间段、时长 -->
      <el-row :gutter="16">
        <el-col :span="8">
          <el-form-item label="日期" prop="log_date">
            <el-date-picker
              v-model="form.log_date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              style="width: 100%"
              size="large"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="时间段" prop="time_slot">
            <el-input
              v-model="form.time_slot"
              placeholder="例如：9:00-11:00"
              size="large"
              clearable
            >
              <template #prefix>
                <Icon icon="lucide:clock" />
              </template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="实际时长">
            <div class="duration-inputs">
              <div class="duration-item">
                <el-input-number
                  v-model="form.duration_hours"
                  :min="0"
                  :max="24"
                  controls-position="right"
                  size="large"
                />
                <span class="duration-unit">小时</span>
              </div>
              <div class="duration-item">
                <el-input-number
                  v-model="form.duration_minutes"
                  :min="0"
                  :max="59"
                  controls-position="right"
                  size="large"
                />
                <span class="duration-unit">分钟</span>
              </div>
            </div>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 分类信息卡片 -->
    <div class="form-section">
      <div class="section-title">
        <Icon icon="lucide:folder-tree" class="section-icon" />
        <span>分类信息</span>
      </div>

      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="分类" prop="category_id">
            <el-select
              v-model="form.category_id"
              placeholder="请选择分类"
              style="width: 100%"
              size="large"
              @change="onCategoryChange"
            >
              <template #prefix>
                <Icon icon="lucide:folder" />
              </template>
              <el-option
                v-for="item in categoryStore.categoryOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="标签" prop="subcategory_id">
            <el-select
              v-model="form.subcategory_id"
              placeholder="请选择标签"
              style="width: 100%"
              size="large"
              :disabled="!subCategoryOptions.length"
            >
              <template #prefix>
                <Icon icon="lucide:tag" />
              </template>
              <el-option
                v-for="item in subCategoryOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </div>

    <!-- 附加信息卡片 -->
    <div class="form-section">
      <div class="section-title">
        <Icon icon="lucide:message-square-text" class="section-icon" />
        <span>附加信息</span>
      </div>

      <!-- 心情 -->
      <el-form-item label="心情" prop="mood">
        <el-radio-group v-model="form.mood" size="large" class="mood-radios">
          <el-radio :label="5" border>
            <span class="mood-item">
              <span class="mood-emoji">😃</span>
              <span class="mood-label">很开心</span>
            </span>
          </el-radio>
          <el-radio :label="4" border>
            <span class="mood-item">
              <span class="mood-emoji">😊</span>
              <span class="mood-label">开心</span>
            </span>
          </el-radio>
          <el-radio :label="3" border>
            <span class="mood-item">
              <span class="mood-emoji">😐</span>
              <span class="mood-label">一般</span>
            </span>
          </el-radio>
          <el-radio :label="2" border>
            <span class="mood-item">
              <span class="mood-emoji">😟</span>
              <span class="mood-label">不太好</span>
            </span>
          </el-radio>
          <el-radio :label="1" border>
            <span class="mood-item">
              <span class="mood-emoji">😠</span>
              <span class="mood-label">很糟糕</span>
            </span>
          </el-radio>
        </el-radio-group>
      </el-form-item>

      <!-- 笔记 -->
      <el-form-item label="笔记" prop="notes">
        <el-input
          v-model="form.notes"
          type="textarea"
          :rows="5"
          placeholder="记录一些想法、收获或遇到的问题..."
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
    </div>

    <!-- 按钮 -->
    <div class="dialog-footer">
      <el-button size="large" @click="$emit('cancel')">
        <Icon icon="lucide:x" class="btn-icon" />
        取消
      </el-button>
      <el-button
        size="large"
        type="primary"
        @click="submitForm"
        :loading="loading"
      >
        <Icon
          v-if="!loading"
          :icon="isEditing ? 'lucide:save' : 'lucide:plus-circle'"
          class="btn-icon"
        />
        {{ isEditing ? "更新记录" : "添加记录" }}
      </el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { useCategoryStore } from "@/stores/modules/category";
import { ElMessage } from "element-plus";
import { Icon } from "@iconify/vue";

const props = defineProps({
  record: {
    type: Object,
    default: null,
  },
  loading: {
    type: Boolean,
    default: false,
  },
  defaultDate: {
    type: String,
    default: null,
  },
});

const emit = defineEmits(["submit", "cancel"]);

const categoryStore = useCategoryStore();
const formRef = ref(null);

const isEditing = computed(() => !!props.record?.id);

const form = reactive({
  id: null,
  log_date: "",
  time_slot: "",
  task: "",
  duration_hours: 0,
  duration_minutes: 0,
  category_id: null,
  subcategory_id: null,
  mood: 3,
  notes: "",
});

const rules = {
  task: [{ required: true, message: "请输入任务名称", trigger: "blur" }],
  log_date: [{ required: true, message: "请选择日期", trigger: "change" }],
  category_id: [{ required: true, message: "请选择分类", trigger: "change" }],
  subcategory_id: [
    { required: true, message: "请选择标签", trigger: "change" },
  ],
};

const subCategoryOptions = computed(() => {
  if (!form.category_id) return [];
  return categoryStore.getSubCategoryOptions(form.category_id);
});

function onCategoryChange() {
  console.log("Category changed to:", form.category_id);
  const options = categoryStore.getSubCategoryOptions(form.category_id);
  console.log("Available subcategories:", options);
  form.subcategory_id = null;
}

function setFormValues(record) {
  if (!record) {
    formRef.value?.resetFields();
    form.id = null;
    form.log_date = props.defaultDate || new Date().toISOString().split("T")[0];
    form.time_slot = "";
    form.task = "";
    form.duration_hours = 0;
    form.duration_minutes = 0;
    form.category_id = null;
    form.subcategory_id = null;
    form.mood = 3;
    form.notes = "";
  } else {
    form.id = record.id;
    form.log_date = record.log_date;
    form.time_slot = record.time_slot || "";
    form.task = record.task;

    // 将 actual_duration (分钟) 转换为小时和分钟
    const totalMinutes = record.actual_duration || 0;
    form.duration_hours = Math.floor(totalMinutes / 60);
    form.duration_minutes = totalMinutes % 60;

    // 从 subcategory 获取 category_id
    if (record.subcategory) {
      form.category_id = record.subcategory.category_id;
      setTimeout(() => {
        form.subcategory_id = record.subcategory_id;
      }, 50);
    } else {
      form.category_id = null;
      form.subcategory_id = null;
    }

    form.mood = record.mood || 3;
    form.notes = record.notes || "";
  }
}

watch(
  () => props.record,
  (newRecord) => {
    setFormValues(newRecord);
  },
  { immediate: true }
);

watch(
  () => props.defaultDate,
  (newDate) => {
    if (newDate && !isEditing.value) {
      form.log_date = newDate;
    }
  }
);

onMounted(() => {
  console.log("RecordForm mounted, fetching categories...");
  categoryStore.fetchCategories().then(() => {
    console.log("Categories loaded:", categoryStore.categoryOptions);
    console.log("Full tree:", categoryStore.tree);
  });
  if (!isEditing.value) {
    form.log_date = props.defaultDate || new Date().toISOString().split("T")[0];
  }
});

const submitForm = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();

    // 检查是否选择了标签
    if (!form.subcategory_id) {
      ElMessage.error("请先选择分类和标签");
      return;
    }

    // 构建提交数据，只包含有效字段
    const submitData = {
      task: form.task,
      log_date: form.log_date,
      time_slot: form.time_slot || null,
      duration_hours: form.duration_hours || 0,
      duration_minutes: form.duration_minutes || 0,
      subcategory_id: form.subcategory_id,
      mood: form.mood || 3,
      notes: form.notes || null,
    };

    // 如果是编辑模式，添加ID
    if (isEditing.value) {
      submitData.id = form.id;
    }

    console.log("Submitting form data:", submitData);
    emit("submit", submitData);
  } catch (error) {
    console.error("Form validation error:", error);
    ElMessage.error("请检查表单输入");
  }
};
</script>

<style scoped lang="scss">
.record-form {
  padding: 1rem 0;
  max-height: 70vh;
  overflow-y: auto;

  /* 自定义滚动条 */
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: #f1f5f9;
    border-radius: 10px;
  }

  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 10px;

    &:hover {
      background: #94a3b8;
    }
  }
}

/* 表单分区 */
.form-section {
  background: #ffffff;
  border-radius: 16px;
  padding: 1.75rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e2e8f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s ease;

  &:hover {
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.08);
    border-color: #cbd5e1;
  }
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f1f5f9;

  .section-icon {
    width: 1.5rem;
    height: 1.5rem;
    color: #667eea;
  }

  span {
    font-size: 1.1rem;
    font-weight: 700;
    color: #1e293b;
    letter-spacing: 0.5px;
  }
}

/* 时长输入 */
.duration-inputs {
  display: flex;
  gap: 12px;
  width: 100%;
}

.duration-item {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  transition: all 0.3s ease;

  &:hover {
    background: #ffffff;
    border-color: #cbd5e1;
  }
}

.duration-unit {
  color: #64748b;
  font-weight: 600;
  font-size: 0.9rem;
  white-space: nowrap;
  min-width: 42px;
}

/* 心情选择器 */
.mood-radios {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: space-between;
}

.mood-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.mood-emoji {
  font-size: 2rem;
  line-height: 1;
}

.mood-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
  white-space: nowrap;
}

/* 底部按钮 */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #f1f5f9;
}

.btn-icon {
  width: 1.2rem;
  height: 1.2rem;
  margin-right: 0.5rem;
}

/* Element Plus 组件深度样式 */
:deep(.el-form-item) {
  margin-bottom: 1.5rem;
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: #334155;
  font-size: 0.95rem;
  margin-bottom: 0.75rem;
  line-height: 1.5;
}

:deep(.el-input__wrapper) {
  border-radius: 12px;
  padding: 10px 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  border: 1px solid #e2e8f0;
  background: #ffffff;
}

:deep(.el-input__wrapper):hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

:deep(.el-input--large .el-input__wrapper) {
  padding: 12px 16px;
  font-size: 1rem;
}

:deep(.el-input__prefix) {
  color: #94a3b8;
  margin-right: 8px;

  svg {
    width: 1.2rem;
    height: 1.2rem;
  }
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-textarea__inner) {
  border-radius: 12px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  font-size: 0.95rem;
  line-height: 1.6;
  background: #ffffff;
}

:deep(.el-textarea__inner):hover {
  border-color: #cbd5e1;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

:deep(.el-textarea__inner):focus {
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
}

:deep(.el-input-number) {
  width: 100%;

  .el-input__wrapper {
    padding: 8px 12px;
  }
}

:deep(.el-date-editor) {
  width: 100%;
}

/* 单选按钮 - 心情 */
:deep(.el-radio.is-bordered) {
  flex: 1;
  min-width: 90px;
  border-radius: 14px;
  padding: 16px 12px;
  border: 2px solid #e2e8f0;
  background: #ffffff;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
  margin: 0;

  .el-radio__label {
    padding-left: 0;
  }

  .el-radio__inner {
    display: none;
  }

  &:hover {
    border-color: #667eea;
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);

    .mood-label {
      color: #667eea;
    }
  }

  &.is-checked {
    border-color: #667eea;
    background: linear-gradient(
      135deg,
      rgba(102, 126, 234, 0.08) 0%,
      rgba(118, 75, 162, 0.08) 100%
    );
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.25);
    transform: translateY(-3px) scale(1.02);

    .mood-label {
      color: #667eea;
      font-weight: 700;
    }
  }
}

/* 底部按钮样式 */
:deep(.dialog-footer .el-button) {
  padding: 13px 32px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  min-width: 130px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

:deep(.dialog-footer .el-button--default) {
  border: 2px solid #e2e8f0;
  background: #ffffff;
  color: #64748b;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
    color: #475569;
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
}

:deep(.dialog-footer .el-button--primary) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);

  &:hover {
    background: linear-gradient(135deg, #5568d3 0%, #63398e 100%);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(102, 126, 234, 0.45);
  }

  &:active {
    transform: translateY(0);
  }
}

/* 行和列间距 */
:deep(.el-row) {
  margin-left: -8px !important;
  margin-right: -8px !important;
}

:deep(.el-col) {
  padding-left: 8px !important;
  padding-right: 8px !important;
}
</style>
