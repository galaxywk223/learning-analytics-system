<template>
  <div class="theme-switcher">
    <el-popover
      placement="bottom-end"
      :width="320"
      trigger="click"
      popper-class="theme-popper"
    >
      <template #reference>
        <button type="button" class="theme-trigger" aria-label="切换主题">
          <Icon icon="lucide:palette" />
        </button>
      </template>

      <div class="theme-panel">
        <div class="theme-panel__header">
          <p class="app-kicker">Theme</p>
          <h3>工作台外观</h3>
          <p>统一结构，只切换材质和气氛。</p>
        </div>

        <div class="theme-list">
          <button
            v-for="theme in themes"
            :key="theme.id"
            type="button"
            class="theme-option"
            :class="{ active: currentTheme === theme.id }"
            @click="setTheme(theme.id)"
          >
            <span
              class="theme-option__preview"
              :style="{ background: theme.preview }"
            />
            <span class="theme-option__copy">
              <strong>{{ theme.name }}</strong>
              <small>{{ theme.description }}</small>
            </span>
            <Icon
              v-if="currentTheme === theme.id"
              icon="lucide:check"
              class="theme-option__check"
            />
          </button>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Icon } from "@iconify/vue";
import { useThemeStore } from "@/stores/modules/theme";

const themeStore = useThemeStore();

const currentTheme = computed(() => themeStore.currentTheme);
const themes = computed(() => themeStore.themes);

const setTheme = (id: string) => themeStore.setTheme(id);
</script>

<style scoped lang="scss">
.theme-trigger {
  width: 42px;
  height: 42px;
  border: 1px solid var(--border-subtle);
  border-radius: 14px;
  background: color-mix(in srgb, var(--bg-surface) 88%, white);
  color: var(--text-primary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: var(--shadow-1);
}

.theme-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.theme-panel__header {
  display: flex;
  flex-direction: column;
  gap: 4px;

  h3,
  p {
    margin: 0;
  }

  h3 {
    color: var(--text-primary);
    font-size: 1.05rem;
  }

  p:last-child {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }
}

.theme-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.theme-option {
  display: grid;
  grid-template-columns: 46px minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  background: color-mix(in srgb, var(--bg-surface) 90%, white);
  cursor: pointer;
  text-align: left;
}

.theme-option.active {
  border-color: color-mix(in srgb, var(--brand-primary) 30%, var(--border-subtle));
  background: color-mix(in srgb, var(--brand-primary-soft) 48%, var(--bg-elevated));
}

.theme-option__preview {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.36);
}

.theme-option__copy {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;

  strong {
    color: var(--text-primary);
    font-size: 0.95rem;
  }

  small {
    color: var(--text-secondary);
    line-height: 1.4;
  }
}

.theme-option__check {
  color: var(--brand-primary);
}
</style>
