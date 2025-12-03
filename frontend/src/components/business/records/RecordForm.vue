<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-position="top"
    @submit.prevent="submitForm"
    class="record-form"
  >
    <div class="ios-form-content">
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
    </div>

    <!-- 提交按钮 -->
    <div class="ios-form-actions">
      <button class="ios-btn cancel" @click.prevent="emit('cancel')">
        取消
      </button>
      <div class="divider-vertical"></div>
      <button 
        class="ios-btn confirm" 
        @click.prevent="submitForm"
        :disabled="loading"
      >
        {{ isEdit ? "更新" : "保存" }}
      </button>
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

<style scoped lang="scss">
.record-form {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.ios-form-content {
  padding: 0 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ios-form-actions {
  display: flex;
  border-top: 0.5px solid rgba(60, 60, 67, 0.29);
  margin-top: auto;
  
  .ios-btn {
    flex: 1;
    background: transparent;
    border: none;
    padding: 14px 0;
    font-size: 17px;
    color: #007aff;
    cursor: pointer;
    transition: background 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    
    &:active {
      background: rgba(0, 0, 0, 0.05);
    }
    
    &.confirm {
      font-weight: 600;
    }
    
    &.cancel {
      font-weight: 400;
    }
    
    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
  
  .divider-vertical {
    width: 0.5px;
    background: rgba(60, 60, 67, 0.29);
  }
}
</style>
