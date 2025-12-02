<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    @submit.prevent="submitForm"
    class="record-form"
  >
    <!-- 基本信息 -->
    <BasicInfoFields :form="form" />

    <!-- 分类标签 -->
    <CategoryFields
      :form="form"
      :category-options="categoryStore.categoryOptions"
      :sub-category-options="subCategoryOptions"
      @category-change="onCategoryChange"
    />

    <!-- 附加信息 -->
    <AdditionalFields :form="form" />

    <!-- 提交按钮 -->
    <div class="form-actions">
      <el-button @click="emit('cancel')" size="large"> 取消 </el-button>
      <el-button
        type="primary"
        @click="submitForm"
        :loading="loading"
        size="large"
      >
        {{ isEdit ? "更新记录" : "添加记录" }}
      </el-button>
    </div>
  </el-form>
</template>

<script setup>
import { ref, computed, watch, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { useCategoryStore } from "@/stores/category";
import BasicInfoFields from "./components/BasicInfoFields.vue";
import CategoryFields from "./components/CategoryFields.vue";
import AdditionalFields from "./components/AdditionalFields.vue";
import {
  formRules,
  getDefaultFormData,
  validateFormData,
  formatFormDataForSubmit,
  formatServerDataToForm,
} from "@/utils/form/recordForm";

const props = defineProps({
  initialData: {
    type: Object,
    default: null,
  },
  isEdit: {
    type: Boolean,
    default: false,
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

// 响应式数据
const formRef = ref(null);
const categoryStore = useCategoryStore();
const form = ref(getDefaultFormData(props.defaultDate));
const rules = formRules;

// 计算属性
const subCategoryOptions = computed(() => {
  if (!form.value.category_id) return [];
  return categoryStore.getSubCategories(form.value.category_id);
});

// 监听时长变化，自动计算 actual_duration（分钟）
watch(
  () => [form.value.duration_hours, form.value.duration_minutes],
  ([hours, minutes]) => {
    form.value.actual_duration = (hours || 0) * 60 + (minutes || 0);
  },
  { immediate: true }
);

// 方法
function onCategoryChange(categoryId) {
  // 当分类改变时，清空子分类选择
  form.value.subcategory_id = null;
}

async function submitForm() {
  if (!formRef.value) return;

  try {
    // 表单验证
    const valid = await formRef.value.validate();
    if (!valid) return;

    // 额外的数据验证
    const errors = validateFormData(form.value);
    if (errors.length > 0) {
      ElMessage.error(errors[0]);
      return;
    }

    // 格式化并提交数据
    const submitData = formatFormDataForSubmit(form.value);
    emit("submit", submitData);
  } catch (error) {
    console.error("表单验证失败:", error);
    ElMessage.error("请检查表单数据");
  }
}

function resetForm() {
  if (formRef.value) {
    formRef.value.resetFields();
  }
  form.value = getDefaultFormData(props.defaultDate);
}

function initializeForm() {
  if (props.initialData) {
    form.value = formatServerDataToForm(props.initialData, props.defaultDate);
  } else {
    form.value = getDefaultFormData(props.defaultDate);
  }
}

// 监听器
watch(() => [props.initialData, props.defaultDate], initializeForm, {
  deep: true,
});

// 生命周期
onMounted(async () => {
  // 确保分类数据已加载
  if (!categoryStore.tree.length) {
    await categoryStore.fetchCategories();
  }
  initializeForm();
});

// 暴露方法给父组件
defineExpose({
  resetForm,
  validateForm: () => formRef.value?.validate(),
  getFormData: () => form.value,
});
</script>

<style scoped>
.record-form {
  max-width: 820px;
  margin: 0 auto;
  padding: 24px 8px 12px;

  :deep(.el-form-item__label) {
    font-weight: 600;
    color: #0f172a;
    margin-bottom: 8px;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper),
  :deep(.el-date-editor .el-input__wrapper),
  :deep(.el-textarea__inner) {
    background: #f3f4f6;
    border: 1px solid transparent;
    border-radius: 12px;
    box-shadow: none;
    transition: all 0.2s ease;
  }

  :deep(.el-input__inner),
  :deep(.el-textarea__inner) {
    font-size: 15px;
    color: #111827;
  }

  :deep(.el-input__wrapper.is-focus),
  :deep(.el-select .el-input__wrapper.is-focus),
  :deep(.el-date-editor.is-active .el-input__wrapper),
  :deep(.el-textarea__inner:focus) {
    background: #ffffff;
    border-color: #a5b4fc;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.18);
  }

  :deep(.el-input-number) {
    width: 100%;
    background: #f3f4f6;
    border-radius: 14px;
    border: 1px solid transparent;
    display: flex;
    align-items: center;
    height: 46px;
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
    padding: 0 14px;
    min-width: 0;
    position: relative;
    box-sizing: border-box;
  }

  :deep(.el-input-number__increase),
  :deep(.el-input-number__decrease) {
    display: none;
  }

  :deep(.el-input-number__inner) {
    font-weight: 700;
    color: #111827;
    text-align: center;
    height: 100%;
    line-height: 46px;
  }

  :deep(.el-rate) {
    --el-rate-icon-size: 28px;
  }

  :deep(.el-rate__icon) {
    color: #e5e7eb;
  }

  :deep(.el-rate__icon.is-active) {
    color: #fbbf24;
  }
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-top: 24px;
  padding-top: 12px;
  border-top: 1px solid rgba(15, 23, 42, 0.06);
}

.form-actions .el-button {
  min-width: 132px;
  height: 48px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 999px;
  border: none;
}

.form-actions .el-button:not(.el-button--primary) {
  background: transparent;
  color: #6b7280;
}

.form-actions .el-button--primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  box-shadow: 0 15px 30px rgba(99, 102, 241, 0.35);
}

.form-actions .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 18px 36px rgba(99, 102, 241, 0.45);
}

@media (max-width: 768px) {
  .record-form {
    padding: 16px;
  }

  .form-actions {
    flex-direction: column;
  }

  .form-actions .el-button {
    width: 100%;
  }
}
</style>
