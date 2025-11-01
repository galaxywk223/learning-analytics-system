<template>
  <section class="account-settings">
    <!-- 用户头像区域 -->
    <div class="avatar-section">
      <div class="avatar-preview">
        {{ authStore.user?.username?.charAt(0)?.toUpperCase() || "U" }}
      </div>
      <div class="avatar-info">
        <h3>{{ authStore.user?.username || "用户" }}</h3>
        <p>{{ authStore.user?.email || "email@example.com" }}</p>
      </div>
    </div>

    <!-- 个人资料卡片 -->
    <div class="settings-card">
      <div class="card-header">
        <i data-lucide="user-circle"></i>
        <h5 class="card-title">个人资料</h5>
      </div>
      <div class="card-body">
        <form @submit.prevent="handleProfileSubmit">
          <div class="form-group">
            <div class="form-row">
              <label for="username" class="form-label">用户名</label>
              <div class="form-input-wrapper">
                <input
                  type="text"
                  class="form-control"
                  id="username"
                  :value="authStore.user?.username || ''"
                  placeholder="输入您的用户名"
                />
                <p class="form-text">您的公开显示名称</p>
              </div>
            </div>
          </div>

          <div class="form-group">
            <div class="form-row">
              <label for="email" class="form-label">邮箱地址</label>
              <div class="form-input-wrapper">
                <input
                  type="email"
                  class="form-control"
                  id="email"
                  :value="authStore.user?.email || ''"
                  readonly
                  disabled
                />
                <p class="form-text">
                  <span class="badge badge-info">不可修改</span>
                  邮箱地址用于登录，暂时无法修改
                </p>
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" disabled>
              <i data-lucide="save" style="width: 18px; height: 18px"></i>
              保存更改
            </button>
            <span class="badge badge-warning">功能开发中</span>
          </div>
        </form>
      </div>
    </div>

    <!-- 安全设置卡片 -->
    <div class="settings-card">
      <div class="card-header">
        <i data-lucide="shield-check"></i>
        <h5 class="card-title">安全设置</h5>
      </div>
      <div class="card-body">
        <form @submit.prevent="handlePasswordSubmit">
          <div class="form-group">
            <div class="form-row">
              <label for="current-password" class="form-label">当前密码</label>
              <div class="form-input-wrapper">
                <input
                  type="password"
                  class="form-control"
                  id="current-password"
                  placeholder="输入您当前的密码"
                  autocomplete="current-password"
                />
              </div>
            </div>
          </div>

          <div class="form-group">
            <div class="form-row">
              <label for="new-password" class="form-label">新密码</label>
              <div class="form-input-wrapper">
                <input
                  type="password"
                  class="form-control"
                  id="new-password"
                  placeholder="输入您的新密码"
                  autocomplete="new-password"
                />
                <p class="form-text">
                  密码长度至少8位，建议包含字母、数字和特殊字符
                </p>
              </div>
            </div>
          </div>

          <div class="form-group">
            <div class="form-row">
              <label for="confirm-password" class="form-label"
                >确认新密码</label
              >
              <div class="form-input-wrapper">
                <input
                  type="password"
                  class="form-control"
                  id="confirm-password"
                  placeholder="再次输入您的新密码"
                  autocomplete="new-password"
                />
              </div>
            </div>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-primary" disabled>
              <i data-lucide="key-round" style="width: 18px; height: 18px"></i>
              修改密码
            </button>
            <span class="badge badge-warning">功能开发中</span>
          </div>
        </form>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted } from "vue";
import { useAuthStore } from "@/stores/modules/auth";

const authStore = useAuthStore();

const handleProfileSubmit = () => {
  // TODO: 实现个人资料更新逻辑
  console.log("保存个人资料");
};

const handlePasswordSubmit = () => {
  // TODO: 实现密码修改逻辑
  console.log("修改密码");
};

onMounted(() => {
  import("lucide").then((m) => m.createIcons()).catch(() => {});
});
</script>

<style scoped>
@import "@/styles/views/settings/account.scss";
</style>
