<template>
  <div class="settings-shell">
    <PageContainer
      :title="{ icon: '⚙️', text: '设置中心' }"
      subtitle="个性化您的萤火集体验"
      :custom-class="'settings-layout-container'"
      :max-width="1400"
    >
      <div class="settings-main-content">
        <aside class="settings-sidebar">
          <nav class="settings-nav">
            <router-link to="/settings/account" class="settings-nav-item">
              <Icon icon="lucide:user-circle" />
              <span>账户设置</span>
            </router-link>
            <router-link to="/settings/data" class="settings-nav-item">
              <Icon icon="lucide:database" />
              <span>数据管理</span>
            </router-link>
            <router-link to="/settings/stages" class="settings-nav-item">
              <Icon icon="lucide:flag" />
              <span>阶段管理</span>
            </router-link>
            <router-link to="/settings/categories" class="settings-nav-item">
              <Icon icon="lucide:folder" />
              <span>分类管理</span>
            </router-link>
            <router-link to="/settings/mottos" class="settings-nav-item">
              <Icon icon="lucide:message-square-quote" />
              <span>格言管理</span>
            </router-link>
          </nav>
        </aside>
        <main class="settings-content">
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </main>
      </div>
    </PageContainer>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";
import PageContainer from "@/components/layout/PageContainer.vue";
</script>

<style scoped>
@import "@/styles/views/settings/layout.scss";
</style>
