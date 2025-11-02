<template>
  <div class="header-section">
    <div class="title-wrapper">
      <div class="icon-wrapper">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M6 2C5.44772 2 5 2.44772 5 3V9C5 9.55228 5.44772 10 6 10H10C10.5523 10 11 9.55228 11 9V3C11 2.44772 10.5523 2 10 2H6ZM14 2C13.4477 2 13 2.44772 13 3V9C13 9.55228 13.4477 10 14 10H18C18.5523 10 19 9.55228 19 9V3C19 2.44772 18.5523 2 18 2H14ZM5 15C5 14.4477 5.44772 14 6 14H10C10.5523 14 11 14.4477 11 15V21C11 21.5523 10.5523 22 10 22H6C5.44772 22 5 21.5523 5 21V15ZM14 14C13.4477 14 13 14.4477 13 15V21C13 21.5523 13.4477 22 14 22H18C18.5523 22 19 21.5523 19 21V15C19 14.4477 18.5523 14 18 14H14Z"
          />
        </svg>
      </div>
      <div>
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ subtitle }}</p>
      </div>
    </div>
    <div class="actions">
      <el-button
        type="primary"
        @click="$emit('add')"
        :icon="Plus"
        size="large"
        class="primary-btn"
      >
        {{ addButtonText }}
      </el-button>
      <el-button
        :loading="loading"
        @click="$emit('refresh')"
        :icon="Refresh"
        size="large"
        class="refresh-btn"
      >
        刷新
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { Plus, Refresh } from "@element-plus/icons-vue";

defineProps({
  title: {
    type: String,
    default: "分类管理",
  },
  subtitle: {
    type: String,
    default: "维护学习分类与子分类层级结构",
  },
  addButtonText: {
    type: String,
    default: "新增分类",
  },
  loading: {
    type: Boolean,
    default: false,
  },
});

defineEmits(["add", "refresh"]);
</script>

<style scoped>
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  padding: 24px;
  background: #ffffff;
  border-radius: 12px;
  border: 2px solid #667eea;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 20px;
}

.icon-wrapper {
  width: 56px;
  height: 56px;
  background: #e8eaf6;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-wrapper svg {
  width: 28px;
  height: 28px;
  color: #667eea;
}

.title-wrapper h1 {
  font-size: 32px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #1e293b;
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 16px;
  margin: 0;
  color: #64748b;
  font-weight: 500;
}

.actions {
  display: flex;
  gap: 12px;
}

.primary-btn {
  background: #667eea;
  border: 1px solid #667eea;
  color: #fff;
  font-weight: 600;
  height: 44px;
  padding: 0 24px;
}

.primary-btn:hover {
  background: #5568d3;
  border-color: #5568d3;
}

.refresh-btn {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  color: #667eea;
  font-weight: 600;
  height: 44px;
  padding: 0 20px;
}

.refresh-btn:hover {
  background: #f8fafc;
  border-color: #667eea;
}

@media (max-width: 768px) {
  .header-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .title-wrapper {
    flex-direction: column;
    gap: 16px;
  }

  .title-wrapper h1 {
    font-size: 28px;
  }

  .actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
