<template>
  <div class="not-found">
    <div class="not-found__card">
      <span class="not-found__code">404</span>
      <h1>这个页面不在你的学习路径里</h1>
      <p>链接可能已经变更，或者你想访问的页面目前不存在。</p>
      <el-button type="primary" size="large" @click="goHome">返回仪表盘</el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from "vue-router";

const router = useRouter();

const goHome = () => {
  router.push("/dashboard");
};
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at top, color-mix(in srgb, var(--brand-primary) 18%, transparent) 0%, transparent 34%),
    linear-gradient(180deg, var(--bg-page) 0%, color-mix(in srgb, var(--bg-page) 84%, white) 100%);
}

.not-found__card {
  width: min(100%, 560px);
  padding: 36px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--bg-elevated) 92%, white) 0%, var(--bg-surface) 100%);
  box-shadow: var(--shadow-3);
  text-align: center;
}

.not-found__code {
  display: inline-flex;
  margin-bottom: 12px;
  color: var(--brand-primary);
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.not-found h1 {
  margin: 0 0 10px;
  color: var(--text-primary);
  font-size: clamp(2rem, 4vw, 2.8rem);
  line-height: 1.08;
  letter-spacing: -0.05em;
}

.not-found p {
  margin: 0 0 24px;
  color: var(--text-secondary);
  font-size: 1rem;
  line-height: 1.65;
}
</style>
