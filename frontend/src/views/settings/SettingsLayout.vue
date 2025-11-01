<template>
  <div class="settings-view">
    <div class="settings-container">
      <header class="settings-page-header">
        <h1>⚙️ 设置中心</h1>
        <p class="lead">个性化您的学习日志体验</p>
      </header>

      <div class="settings-main-content">
        <aside class="settings-sidebar">
          <nav class="settings-nav">
            <router-link to="/settings/account" class="settings-nav-item">
              <el-icon><User /></el-icon>
              <span>账户设置</span>
            </router-link>
            <router-link to="/settings/appearance" class="settings-nav-item">
              <el-icon><MagicStick /></el-icon>
              <span>外观设置</span>
            </router-link>
            <router-link to="/settings/data" class="settings-nav-item">
              <el-icon><DataLine /></el-icon>
              <span>数据管理</span>
            </router-link>
            <router-link to="/settings/stages" class="settings-nav-item">
              <el-icon><Flag /></el-icon>
              <span>阶段管理</span>
            </router-link>
            <router-link to="/settings/categories" class="settings-nav-item">
              <el-icon><Folder /></el-icon>
              <span>分类管理</span>
            </router-link>
            <router-link to="/settings/mottos" class="settings-nav-item">
              <el-icon><ChatLineSquare /></el-icon>
              <span>格言管理</span>
            </router-link>
            <router-link
              to="/settings/milestone-categories"
              class="settings-nav-item"
            >
              <el-icon><Trophy /></el-icon>
              <span>里程碑分类</span>
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
    </div>
  </div>
</template>

<script setup>
import {
  User,
  MagicStick,
  DataLine,
  Flag,
  Folder,
  ChatLineSquare,
  Trophy,
} from "@element-plus/icons-vue";
</script>

<style scoped>
@import "@/styles/views/settings/layout.css";
</style>
