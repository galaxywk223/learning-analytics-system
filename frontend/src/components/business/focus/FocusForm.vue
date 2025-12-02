<!-- 专注表单组件 -->
<template>
  <div class="focus-form">
    <el-form
      :model="formData"
      :rules="rules"
      ref="formRef"
      label-position="top"
    >
      <el-form-item label="记录名称" prop="name">
        <el-input
          v-model="formData.name"
          placeholder="请输入本次专注的内容"
          :maxlength="50"
          show-word-limit
          size="large"
        />
      </el-form-item>

      <div class="category-row">
        <el-form-item label="分类" prop="categoryId" class="category-item">
          <el-select
            v-model="formData.categoryId"
            placeholder="请选择分类"
            style="width: 100%"
            size="large"
            filterable
            @change="onCategoryChange"
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
            v-model="formData.subcategoryId"
            placeholder="请选择子分类"
            style="width: 100%"
            size="large"
            filterable
            :disabled="!formData.categoryId || !availableSubcategories.length"
          >
            <el-option
              v-for="subcat in availableSubcategories"
              :key="subcat.id"
              :label="subcat.name"
              :value="subcat.id"
            />
          </el-select>
          <div
            class="el-form-item__tip"
            v-if="formData.categoryId && !availableSubcategories.length"
          >
            该分类下暂无子分类
          </div>
        </el-form-item>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { computed, watch, ref } from "vue";

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
  if (!props.formData.categoryId) return [];
  return props.subcategories.filter(
    (sub) => sub.category_id === props.formData.categoryId
  );
});

// 分类变化时的处理
const onCategoryChange = () => {
  // 清空子分类选择
  const updatedForm = { ...props.formData };
  updatedForm.subcategoryId = null;
  emit("update:formData", updatedForm);
  emit("category-change", props.formData.categoryId);
};

// 监听表单数据变化
watch(
  () => props.formData,
  (newData) => {
    emit("update:formData", newData);
  },
  { deep: true }
);

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
    gap: 1.2rem;
    padding: clamp(1.8rem, 3vw, 2.1rem);
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.22);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 18px 38px rgba(15, 23, 42, 0.08);
  }

  .category-row {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1.1rem;

    @media (max-width: 768px) {
      grid-template-columns: 1fr;
    }
  }

  .category-item {
    margin-bottom: 0;
  }

  :deep(.el-form-item) {
    margin-bottom: 0;
  }

  :deep(.el-form-item__label) {
    color: #334155;
    font-weight: 600;
    font-size: 0.92rem;
    padding-bottom: 0.4rem;
  }

  :deep(.el-input__wrapper),
  :deep(.el-select .el-input__wrapper) {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 14px;
    box-shadow: none !important;
    padding: 12px 14px;
    min-height: 48px;
    transition: border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;

    &:hover {
      border-color: rgba(99, 102, 241, 0.65);
    }

    &.is-focus {
      border-color: rgba(79, 70, 229, 0.95);
      background: #ffffff !important;
      box-shadow: 0 0 0 6px rgba(99, 102, 241, 0.14) !important;
    }
  }

  :deep(.el-input__inner),
  :deep(.el-select__placeholder),
  :deep(.el-select__selected-item) {
    color: #1f2937;
    font-size: 0.98rem;

    &::placeholder {
      color: #94a3b8;
    }
  }

  :deep(.el-input__count) {
    background: transparent;
    color: #94a3b8;
    font-size: 0.78rem;
    font-weight: 500;
  }

  .el-form-item__tip {
    color: #6b7280;
    font-size: 0.82rem;
    margin-top: 0.35rem;
  }
}
</style>
