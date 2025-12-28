<!-- 空状态组件 -->
<template>
  <div class="text-center p-5 empty-state">
    <div class="empty-icon">📝</div>
    <h3>还没有任何记录</h3>
    <p class="text-muted">
      点击右上角的"添加新记录"按钮，开始你的第一条学习日志吧！
    </p>
    <el-button
      type="primary"
      size="large"
      class="mt-3"
      @click="$emit('add-record')"
    >
      <Icon
        icon="lucide:plus"
        style="width: 1.3rem; height: 1.3rem; margin-right: 0.25rem"
      />
      创建第一条记录
    </el-button>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";

// Emits
defineEmits(["add-record"]);
</script>

<style scoped lang="scss">
.empty-state {
  padding: 80px 20px;
  text-align: center;
  background: white;
  border-radius: 8px;
  border: 1px solid #e5e7eb;

  .empty-icon {
    font-size: 72px;
    margin-bottom: 20px;
    line-height: 1;
  }

  h3 {
    color: #374151;
    margin: 0 0 16px 0;
    font-size: 22px;
    font-weight: 600;
  }

  .text-muted {
    color: #6b7280;
    margin: 0 0 28px 0;
    font-size: 15px;
    line-height: 1.6;
  }

  .mt-3 {
    margin-top: 20px;
  }

  .el-button {
    height: 44px;
    padding: 0 28px;
    font-size: 16px;
    font-weight: 500;

    :deep(.iconify) {
      width: 22px;
      height: 22px;
      margin-right: 8px;
    }
  }
}
</style>
