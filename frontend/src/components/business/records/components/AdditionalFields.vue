<template>
  <div class="form-section">
    <!-- 笔记 -->
    <el-form-item label="笔记" prop="notes">
      <el-input
        v-model="form.notes"
        type="textarea"
        :rows="4"
        placeholder="记录本次学习的内容、收获或遇到的问题..."
        resize="none"
        show-word-limit
        :maxlength="500"
      />
    </el-form-item>

    <!-- 心情 -->
    <el-form-item label="心情" prop="mood">
      <el-rate
        v-model="form.mood"
        :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
        size="large"
      />
    </el-form-item>
  </div>
</template>

<script setup>
defineProps({
  form: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped lang="scss">
.form-section {
  margin-bottom: 0;

  :deep(.el-rate) {
    height: 2.5rem;
    display: flex;
    align-items: center;
  }
}
</style>
