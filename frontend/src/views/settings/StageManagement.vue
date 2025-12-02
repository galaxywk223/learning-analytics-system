<template>
  <PageContainer
    title="🚩 阶段管理"
    subtitle="管理学习阶段（与旧版导航对齐）"
    :custom-class="'settings-subpage'"
  >
    <div class="placeholder-card card">
      <div class="card-header">
        <h5 class="card-title mb-0">阶段列表 (占位)</h5>
      </div>
      <div class="card-body">
        <p class="text-muted">此页面待复制旧项目阶段管理具体功能。</p>
      </div>
    </div>
  </PageContainer>
</template>
<script setup>
// TODO: 后续添加与后端阶段 CRUD API 交互逻辑
import PageContainer from "@/components/layout/PageContainer.vue";
</script>
<style scoped>
.placeholder-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}
.card-header {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f0f0f0;
}
.card-body {
  padding: 1rem;
}
</style>
