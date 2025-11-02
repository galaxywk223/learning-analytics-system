<!-- 学习记录页面头部组件 -->
<template>
  <div class="page-header-records">
    <div>
      <h1>📚 学习记录</h1>
      <p class="text-secondary mb-0">
        在这里回顾每一次努力，见证成长的每一步。
      </p>
    </div>
    <div class="d-flex align-items-center gap-2">
      <!-- 排序按钮 -->
      <el-button-group>
        <el-button
          :type="currentSort === 'desc' ? 'primary' : ''"
          size="small"
          @click="$emit('sort-change', 'desc')"
        >
          降序
        </el-button>
        <el-button
          :type="currentSort === 'asc' ? 'primary' : ''"
          size="small"
          @click="$emit('sort-change', 'asc')"
        >
          升序
        </el-button>
      </el-button-group>
      <!-- 添加记录按钮 -->
      <el-tooltip
        :disabled="canAddRecord"
        content="请先创建或选择一个阶段"
        placement="top"
      >
        <el-button
          type="primary"
          :disabled="!canAddRecord"
          @click="$emit('add-record')"
        >
          <Icon
            icon="lucide:plus"
            style="width: 1.2rem; height: 1.2rem; margin-right: 0.25rem"
          />
          添加新记录
        </el-button>
      </el-tooltip>
    </div>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";

// Props
defineProps({
  currentSort: {
    type: String,
    default: "desc",
  },
  canAddRecord: {
    type: Boolean,
    default: false,
  },
});

// Emits
defineEmits(["sort-change", "add-record"]);
</script>

<style scoped lang="scss">
.page-header-records {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding: 18px 24px;
  background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%);
  border-radius: 8px;
  border: 1px solid #e5e7eb;

  h1 {
    margin: 0 0 6px 0;
    color: #1f2937;
    font-size: 28px;
    font-weight: 700;
    line-height: 1.2;
  }

  .text-secondary {
    color: #6b7280;
    font-size: 15px;
    margin: 0;
    line-height: 1.4;
  }

  .d-flex {
    display: flex;

    &.align-items-center {
      align-items: center;
    }

    &.gap-2 {
      gap: 10px;
    }
  }

  .el-button-group {
    :deep(.el-button) {
      height: 40px;
      padding: 0 18px;
      font-size: 15px;
      font-weight: 500;
    }
  }

  .el-button {
    height: 40px;
    padding: 0 24px;
    font-size: 15px;
    font-weight: 500;

    :deep(.iconify) {
      width: 20px;
      height: 20px;
      margin-right: 6px;
    }
  }
}
</style>
