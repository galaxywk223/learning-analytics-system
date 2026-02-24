<template>
  <div class="focus-form">
    <el-form
      ref="formRef"
      :model="localForm"
      :rules="rules"
      label-position="top"
    >
      <el-form-item label="记录名称" prop="name">
        <template #label>
           <span class="required-star">*</span> 记录名称
        </template>
        <el-input
          v-model="localForm.name"
          placeholder="请输入本次专注的内容"
          :maxlength="50"
          show-word-limit
          size="large"
        />
      </el-form-item>

      <div class="category-row">
        <el-form-item label="分类" prop="categoryId" class="category-item">
          <template #label>
             <span class="required-star">*</span> 分类
          </template>
          <el-select
            v-model="localForm.categoryId"
            placeholder="请选择分类"
            style="width: 100%"
            size="large"
            filterable
            @change="onCategoryChange"
            popper-class="dark-dropdown"
          >
            <el-option
              v-for="cat in categories"
              :key="cat.id"
              :label="cat.name"
              :value="cat.id"
            >
              <span :style="{ color: cat.color }">● </span>
              <span>{{ cat.name }}</span>
            </el-option>
          </el-select>
        </el-form-item>

        <el-form-item label="子分类" prop="subcategoryId" class="category-item">
          <el-select
            v-model="localForm.subcategoryId"
            placeholder="请选择子分类"
            class="subcategory-select"
            style="width: 100%"
            size="large"
            filterable
            :disabled="!localForm.categoryId || !availableSubcategories.length"
          >
            <el-option
              v-for="subcat in availableSubcategories"
              :key="subcat.id"
              :label="subcat.name"
              :value="subcat.id"
            />
          </el-select>
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { computed, watch, ref, nextTick, reactive } from "vue";

// Refs
const formRef = ref(null);

// Props
const props = defineProps({
  formData: {
    type: Object,
    required: true,
  },
  categories: {
    type: Array,
    default: () => [],
  },
  subcategories: {
    type: Array,
    default: () => [],
  },
});

// Emits
const emit = defineEmits(["update:formData", "category-change"]);

const localForm = reactive({
  name: "",
  categoryId: null,
  subcategoryId: null,
});
const syncing = ref(false);

watch(
  () => props.formData,
  (value) => {
    syncing.value = true;
    Object.assign(localForm, value || {});
    nextTick(() => {
      syncing.value = false;
    });
  },
  { immediate: true },
);

watch(
  () => [localForm.name, localForm.categoryId, localForm.subcategoryId],
  () => {
    if (syncing.value) return;
    emit("update:formData", { ...localForm });
  },
  { deep: true }
);

// 表单验证规则
const rules = {
  name: [
    { required: true, message: "请输入记录名称", trigger: "blur" },
    { min: 1, max: 50, message: "长度在 1 到 50 个字符", trigger: "blur" },
  ],
  categoryId: [{ required: true, message: "请选择分类", trigger: "change" }],
};

// 可用的子分类
const availableSubcategories = computed(() => {
  if (!localForm.categoryId) return [];
  return props.subcategories.filter(
    (sub) => sub.category_id === localForm.categoryId,
  );
});

// 分类变化时的处理
const onCategoryChange = () => {
  // 清空子分类选择，仅通知父组件分类已变更
  localForm.subcategoryId = null;
  emit("category-change", localForm.categoryId);
};

// 暴露验证方法给父组件
defineExpose({
  validate: () => formRef.value?.validate(),
});
</script>

<style scoped lang="scss">
.focus-form {
  width: 100%;
  margin: 0;

  :deep(.el-form) {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 2rem;
    border-radius: var(--border-radius-lg);
    background: var(--surface-card);
    border: 1px solid var(--color-border-card);
    box-shadow: var(--box-shadow-card);
    transition: all 0.3s ease;
  }

  .category-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.5rem;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .category-item {
    margin-bottom: 0;

    :deep(.el-input__wrapper) {
      background: var(--surface-page) !important;
      border-color: var(--color-border-input);

      .el-input__inner { color: var(--color-text-base); }
      .el-input__suffix { color: var(--color-text-secondary); }
    }
  }
  
  .required-star {
      color: var(--color-error);
      margin-right: 4px;
      font-weight: bold;
  }

  :deep(.el-form-item) {
    margin-bottom: 0;
  }

  :deep(.el-form-item__label) {
    color: var(--color-text-heading);
    font-weight: 700;
    font-size: 0.95rem;
    padding-bottom: 0.5rem;
    line-height: 1.2;
  }

  /* Input Styles */
  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper) {
    background: var(--surface-page) !important;
    border: 1px solid var(--color-border-input);
    border-radius: var(--border-radius-md);
    box-shadow: none !important;
    padding: 8px 12px;
    min-height: 42px;
    transition: all 0.2s ease;

    &:hover {
      border-color: var(--color-border-hover);
    }

    &.is-focus {
      border-color: var(--color-primary);
      box-shadow: 0 0 0 1px var(--color-primary) !important;
    }
  }
  
  /* Text colors */
  :deep(.el-input__inner) {
    color: var(--color-text-base);
    font-size: 0.95rem;
    
    &::placeholder {
      color: var(--color-text-muted);
    }
  }

  /* Keep disabled select consistent with themed form surface */
  :deep(.subcategory-select) {
    --el-fill-color-light: var(--surface-page);
    --el-fill-color-blank: var(--surface-page);
    --el-select-disabled-border: var(--color-border-input);
    --el-disabled-border-color: var(--color-border-input);
    --el-disabled-bg-color: var(--surface-page);
    --el-disabled-text-color: var(--color-text-muted);
  }

  :deep(.subcategory-select .el-input.is-disabled .el-input__wrapper),
  :deep(.subcategory-select .el-input__wrapper.is-disabled),
  :deep(.subcategory-select .el-select__wrapper.is-disabled) {
    background: var(--surface-page) !important;
    border-color: var(--color-border-input) !important;
    box-shadow: 0 0 0 1px var(--color-border-input) inset !important;
    cursor: not-allowed;
    opacity: 0.72;
  }

  :deep(.subcategory-select .el-input.is-disabled .el-input__inner),
  :deep(.subcategory-select .el-input__inner:disabled),
  :deep(.subcategory-select .el-select__wrapper.is-disabled .el-select__selected-item),
  :deep(.subcategory-select .el-select__wrapper.is-disabled .el-select__placeholder) {
    -webkit-text-fill-color: var(--color-text-muted) !important;
    color: var(--color-text-muted) !important;
  }

  :deep(.subcategory-select .el-input.is-disabled .el-input__inner::placeholder),
  :deep(.subcategory-select .el-input__inner:disabled::placeholder),
  :deep(.subcategory-select .el-select__wrapper.is-disabled .el-select__placeholder.is-transparent) {
    color: var(--color-text-muted) !important;
  }

  :deep(.subcategory-select .el-select__caret),
  :deep(.subcategory-select .el-select__wrapper.is-disabled .el-select__caret) {
    color: var(--color-text-muted) !important;
  }

  :deep(.el-input__count) {
    background: transparent;
    color: var(--color-text-muted);
    font-size: 0.8rem;
  }
}
</style>
