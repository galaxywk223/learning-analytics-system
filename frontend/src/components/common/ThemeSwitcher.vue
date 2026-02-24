<template>
  <div class="theme-switcher">
    <el-popover
      placement="bottom-end"
      :width="360"
      trigger="click"
      popper-class="theme-popper"
    >
      <template #reference>
        <el-button circle class="theme-btn">
          <Icon icon="lucide:palette" />
        </el-button>
      </template>

      <div class="theme-panel">
        <h3 class="panel-title">主题设置</h3>
        
        <div class="theme-group">
          <h4 class="group-title">浅色模式</h4>
          <div class="theme-grid">
            <div
              v-for="theme in lightThemes"
              :key="theme.id"
              class="theme-item"
              :class="{ active: currentTheme === theme.id }"
              @click="setTheme(theme.id)"
            >
              <div class="theme-preview" :style="{ background: theme.primaryColor }">
                <Icon v-if="currentTheme === theme.id" icon="lucide:check" class="check-icon" />
              </div>
              <span class="theme-name">{{ theme.name }}</span>
            </div>
          </div>
        </div>

        <div class="theme-group">
          <h4 class="group-title">深色模式</h4>
          <div class="theme-grid">
            <div
              v-for="theme in darkThemes"
              :key="theme.id"
              class="theme-item"
              :class="{ active: currentTheme === theme.id }"
              @click="setTheme(theme.id)"
            >
              <div class="theme-preview" :style="{ background: theme.primaryColor }">
                <Icon v-if="currentTheme === theme.id" icon="lucide:check" class="check-icon" />
              </div>
              <span class="theme-name">{{ theme.name }}</span>
            </div>
          </div>
        </div>
      </div>
    </el-popover>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useThemeStore } from '@/stores/modules/theme';
import { Icon } from '@iconify/vue';

const themeStore = useThemeStore();
const currentTheme = computed(() => themeStore.currentTheme);

const lightThemes = computed(() => themeStore.themes.filter(t => t.type === 'light'));
const darkThemes = computed(() => themeStore.themes.filter(t => t.type === 'dark'));

const setTheme = (id: string) => {
  themeStore.setTheme(id);
};
</script>

<style scoped lang="scss">
.theme-switcher {
  display: inline-block;
}

.theme-btn {
  width: 40px;
  height: 40px;
  font-size: 18px;
  border: none;
  background: var(--surface-card);
  color: var(--color-text-secondary);
  box-shadow: var(--box-shadow);
  transition: all 0.3s ease;

  &:hover {
    background: var(--surface-card-muted);
    color: var(--color-primary);
    transform: translateY(-2px);
  }
}

.theme-panel {
  padding: 8px;
}

.panel-title {
  margin: 0 0 16px;
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-heading);
}

.theme-group {
  margin-bottom: 20px;

  &:last-child {
    margin-bottom: 0;
  }
}

.group-title {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.theme-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.theme-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: transform 0.2s;

  &:hover {
    transform: translateY(-2px);
  }

  &.active {
    .theme-name {
      color: var(--color-primary);
      font-weight: 600;
    }
  }
}

.theme-preview {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  margin-bottom: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
  transition: all 0.2s;

  .active & {
    border-color: var(--color-primary);
    transform: scale(1.1);
  }
}

.check-icon {
  color: #fff;
  font-size: 20px;
  font-weight: bold;
  filter: drop-shadow(0 1px 2px rgba(0,0,0,0.3));
}

.theme-name {
  font-size: 12px;
  color: var(--color-text-secondary);
  text-align: center;
  line-height: 1.2;
  white-space: nowrap;
  transform: scale(0.9); /* Prevent text wrapping for longer names */
}
</style>
