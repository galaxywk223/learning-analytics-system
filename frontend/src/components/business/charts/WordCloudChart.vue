<template>
  <div class="wordcloud-wrapper">
    <transition name="fade">
      <img
        v-if="imageUrl && !loading"
        :src="imageUrl"
        alt="词云"
        class="wordcloud-image"
      />
    </transition>
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p class="hint">✨ 正在生成词云，请稍候...</p>
    </div>
    <div v-else-if="!imageUrl" class="no-data">暂无词云数据</div>
  </div>
</template>

<script setup>
const props = defineProps({
  imageUrl: { type: String, default: "" },
  loading: { type: Boolean, default: false },
});
</script>

<style scoped lang="scss">
@import "@/styles/components/chart-components";

// 加载和过渡效果
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  color: #64748b;

  .hint {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 500;
  }
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e2e8f0;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
