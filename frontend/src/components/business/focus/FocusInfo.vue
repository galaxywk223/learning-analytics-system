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
    <div class="info-item" v-if="currentSubcategory">
      <span class="info-label">子分类</span>
      <span class="info-value">
        <el-tag size="small">{{ currentSubcategory.name }}</el-tag>
      </span>
    </div>
    <div class="info-item" v-if="formData.notes">
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
    (sub) => sub.id === props.formData.subcategoryId
  );
});
</script>

<style scoped lang="scss">
.focus-info {
  max-width: 100%;
  margin: 2rem 0;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);

  .info-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 0;

    &:not(:last-child) {
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }

    .info-label {
      font-weight: 500;
      color: rgba(255, 255, 255, 0.7);
      min-width: 100px;
      font-size: 0.95rem;
    }

    .info-value {
      flex: 1;
      text-align: right;
      color: rgba(255, 255, 255, 0.95);
      font-size: 1rem;

      :deep(.el-tag) {
        margin-left: 0.5rem;
        background: rgba(255, 255, 255, 0.15);
        border-color: rgba(255, 255, 255, 0.25);
        color: rgba(255, 255, 255, 0.9);
      }
    }
  }
}
</style>
