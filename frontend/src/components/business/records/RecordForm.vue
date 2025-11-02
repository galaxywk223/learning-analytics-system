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
});

const emit = defineEmits(["submit", "cancel"]);

// 响应式数据
const formRef = ref(null);
const categoryStore = useCategoryStore();
const form = ref(getDefaultFormData());
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
  form.value = getDefaultFormData();
}

function initializeForm() {
  if (props.initialData) {
    form.value = formatServerDataToForm(props.initialData);
  } else {
    form.value = getDefaultFormData();
  }
}

// 监听器
watch(() => props.initialData, initializeForm, { deep: true });

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
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.form-actions .el-button {
  min-width: 120px;
  height: 44px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-actions .el-button--primary {
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border: none;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
}

.form-actions .el-button--primary:hover {
  background: linear-gradient(135deg, #5855eb 0%, #7c3aed 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(99, 102, 241, 0.5);
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
