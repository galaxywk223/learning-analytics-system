<!-- 专注信息显示组件 -->
<template>
  <div class="focus-info">
    <div class="info-item">
      <span class="info-label">记录名称</span>
      <span class="info-value">{{ formData.name }}</span>
    </div>
    <div class="info-item">
      <span class="info-label">分类</span>
      <span class="info-value">
        <span :style="{ color: currentCategory?.color }">● </span>
        {{ currentCategory?.name }}
      </span>
    </div>
    <div v-if="currentSubcategory" class="info-item">
      <span class="info-label">子分类</span>
      <span class="info-value">
        <el-tag size="small">{{ currentSubcategory.name }}</el-tag>
      </span>
    </div>
    <div v-if="formData.notes" class="info-item">
      <span class="info-label">备注</span>
      <span class="info-value">{{ formData.notes }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

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

// 计算属性
const currentCategory = computed(() => {
  return props.categories.find((cat) => cat.id === props.formData.categoryId);
});

const currentSubcategory = computed(() => {
  return props.subcategories.find(
    (sub) => sub.id === props.formData.subcategoryId,
  );
});
</script>

<style scoped lang="scss">
.focus-info {
  max-width: 100%;
  margin-top: 1.5rem;
  padding: 1.75rem;
  border-radius: 18px;
  background: var(--surface-card);
  border: 1px solid var(--stroke-soft);
  box-shadow: var(--box-shadow-card);

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.9rem 0;

    &:not(:last-child) {
      border-bottom: 1px solid var(--stroke-soft);
    }

    .info-label {
      font-weight: 600;
      color: var(--color-text-secondary);
      font-size: 0.95rem;
      letter-spacing: 0.01em;
    }

    .info-value {
      flex: 1;
      text-align: right;
      color: var(--color-text-heading);
      font-size: 1rem;
      font-weight: 500;

      :deep(.el-tag) {
        margin-left: 0.6rem;
        background: var(--color-primary-light);
        border-color: var(--stroke-soft);
        color: var(--color-primary-dark);
      }
    }
  }
}
</style>
