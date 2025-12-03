<template>
  <PageContainer
    :title="{ icon: '👤', text: '账户设置' }"
    subtitle="管理个人信息与账号安全"
    :custom-class="'settings-subpage'"
  >
    <div class="account-layout">
      <aside class="profile-card">
        <div class="profile-hero"></div>
        <div class="avatar-shell">
          <div class="avatar-preview">
            {{ authStore.user?.username?.charAt(0)?.toUpperCase() || "U" }}
          </div>
          <div class="avatar-meta">
            <h3>{{ authStore.user?.username || "用户" }}</h3>
            <p>{{ authStore.user?.email || "email@example.com" }}</p>
          </div>
        </div>
      </aside>

      <section class="settings-panel">
        <div class="section">
          <div class="section-header">
            <h4>基本资料</h4>
          </div>
          <form @submit.prevent="handleProfileSubmit" class="compact-form">
            <div class="form-row">
              <label for="username">用户名</label>
              <div class="input-col">
                <input
                  id="username"
                  type="text"
                  v-model="profileForm.username"
                  placeholder="输入您的用户名"
                  :disabled="profileLoading"
                />
                <p class="hint">您的公开显示名称</p>
              </div>
            </div>
            <div class="form-row">
              <label for="email">邮箱地址</label>
              <div class="input-col">
                <input
                  id="email"
                  type="email"
                  :value="authStore.user?.email || ''"
                  readonly
                  disabled
                />
                <p class="hint">邮箱用于登录，暂不支持修改</p>
              </div>
            </div>
            <div class="form-actions">
              <button
                type="submit"
                class="btn primary"
                :disabled="profileLoading || !isProfileChanged"
              >
                {{ profileLoading ? "保存中..." : "保存更改" }}
              </button>
              <button
                v-if="isProfileChanged"
                type="button"
                class="btn ghost"
                @click="resetProfileForm"
                :disabled="profileLoading"
              >
                取消
              </button>
            </div>
          </form>
        </div>

        <div class="section">
          <div class="section-header">
            <h4>安全设置</h4>
          </div>
          <form @submit.prevent="handlePasswordSubmit" class="compact-form">
            <div class="form-row">
              <label for="current-password">当前密码</label>
              <div class="input-col">
                <input
                  id="current-password"
                  type="password"
                  v-model="passwordForm.currentPassword"
                  placeholder="输入您当前的密码"
                  autocomplete="current-password"
                  :disabled="passwordLoading"
                />
              </div>
            </div>
            <div class="form-row">
              <label for="new-password">新密码</label>
              <div class="input-col">
                <input
                  id="new-password"
                  type="password"
                  v-model="passwordForm.newPassword"
                  placeholder="输入您的新密码"
                  autocomplete="new-password"
                  :disabled="passwordLoading"
                  @input="validatePassword"
                />
                <p class="hint" :class="{ error: passwordError }">
                  {{
                    passwordError ||
                    "至少 8 位，建议包含字母、数字和特殊字符"
                  }}
                </p>
              </div>
            </div>
            <div class="form-row">
              <label for="confirm-password">确认新密码</label>
              <div class="input-col">
                <input
                  id="confirm-password"
                  type="password"
                  v-model="passwordForm.confirmPassword"
                  placeholder="再次输入您的新密码"
                  autocomplete="new-password"
                  :disabled="passwordLoading"
                  @input="validateConfirmPassword"
                />
                <p class="hint error" v-if="confirmPasswordError">
                  {{ confirmPasswordError }}
                </p>
              </div>
            </div>
            <div class="form-actions">
              <button
                type="submit"
                class="btn primary"
                :disabled="passwordLoading || !isPasswordFormValid"
              >
                {{ passwordLoading ? "修改中..." : "修改密码" }}
              </button>
              <button
                v-if="isPasswordFormFilled"
                type="button"
                class="btn ghost"
                @click="resetPasswordForm"
                :disabled="passwordLoading"
              >
                取消
              </button>
            </div>
          </form>
        </div>

        <div class="danger-row">
          <div>
            <h5>账号控制</h5>
            <p>退出登录或注销账号，谨慎操作。</p>
          </div>
          <div class="danger-actions">
            <button type="button" class="btn ghost danger" @click="handleLogout">
              退出登录
            </button>
            <button type="button" class="btn danger">注销账号</button>
          </div>
        </div>
      </section>
    </div>
  </PageContainer>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import PageContainer from "@/components/layout/PageContainer.vue";
import { useAuthStore } from "@/stores/modules/auth";
import { ElMessage } from "element-plus";
import axios from "axios";

const authStore = useAuthStore();

// 个人资料表单
const profileForm = ref({
  username: "",
});
const profileLoading = ref(false);

// 密码表单
const passwordForm = ref({
  currentPassword: "",
  newPassword: "",
  confirmPassword: "",
});
const passwordLoading = ref(false);
const passwordError = ref("");
const confirmPasswordError = ref("");

// 初始化表单
onMounted(() => {
  profileForm.value.username = authStore.user?.username || "";
});

// 计算属性
const isProfileChanged = computed(() => {
  return profileForm.value.username !== (authStore.user?.username || "");
});

const isPasswordFormFilled = computed(() => {
  return (
    passwordForm.value.currentPassword ||
    passwordForm.value.newPassword ||
    passwordForm.value.confirmPassword
  );
});

const handleLogout = () => {
  authStore.logout();
};

const isPasswordFormValid = computed(() => {
  return (
    passwordForm.value.currentPassword &&
    passwordForm.value.newPassword &&
    passwordForm.value.confirmPassword &&
    !passwordError.value &&
    !confirmPasswordError.value &&
    passwordForm.value.newPassword === passwordForm.value.confirmPassword
  );
});

// 验证密码
const validatePassword = () => {
  const password = passwordForm.value.newPassword;
  if (!password) {
    passwordError.value = "";
    return;
  }

  if (password.length < 8) {
    passwordError.value = "密码长度至少8位";
  } else if (!/[a-zA-Z]/.test(password)) {
    passwordError.value = "密码应包含字母";
  } else if (!/[0-9]/.test(password)) {
    passwordError.value = "密码应包含数字";
  } else {
    passwordError.value = "";
  }

  // 同时验证确认密码
  validateConfirmPassword();
};

// 验证确认密码
const validateConfirmPassword = () => {
  if (!passwordForm.value.confirmPassword) {
    confirmPasswordError.value = "";
    return;
  }

  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    confirmPasswordError.value = "两次输入的密码不一致";
  } else {
    confirmPasswordError.value = "";
  }
};

// 重置个人资料表单
const resetProfileForm = () => {
  profileForm.value.username = authStore.user?.username || "";
};

// 重置密码表单
const resetPasswordForm = () => {
  passwordForm.value = {
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  };
  passwordError.value = "";
  confirmPasswordError.value = "";
};

// 提交个人资料
const handleProfileSubmit = async () => {
  if (!isProfileChanged.value) {
    ElMessage.warning("没有需要保存的更改");
    return;
  }

  profileLoading.value = true;
  try {
    const response = await axios.put(
      "/api/users/profile",
      {
        username: profileForm.value.username,
      },
      {
        headers: {
          Authorization: `Bearer ${authStore.accessToken}`,
        },
      }
    );

    if (response.data.success) {
      // 更新store中的用户信息
      authStore.user.username = profileForm.value.username;
      ElMessage.success("个人资料更新成功");
    } else {
      ElMessage.error(response.data.message || "更新失败");
    }
  } catch (error) {
    console.error("更新个人资料失败:", error);
    ElMessage.error(error.response?.data?.message || "更新失败，请稍后重试");
  } finally {
    profileLoading.value = false;
  }
};

// 提交密码修改
const handlePasswordSubmit = async () => {
  if (!isPasswordFormValid.value) {
    ElMessage.warning("请检查表单填写");
    return;
  }

  passwordLoading.value = true;
  try {
    const response = await axios.post(
      "/api/auth/change-password",
      {
        current_password: passwordForm.value.currentPassword,
        new_password: passwordForm.value.newPassword,
      },
      {
        headers: {
          Authorization: `Bearer ${authStore.accessToken}`,
        },
      }
    );

    if (response.data.success) {
      ElMessage.success("密码修改成功，请重新登录");
      resetPasswordForm();
      // 可选：自动登出
      setTimeout(() => {
        authStore.logout();
      }, 1500);
    } else {
      ElMessage.error(response.data.message || "密码修改失败");
    }
  } catch (error) {
    console.error("修改密码失败:", error);
    ElMessage.error(error.response?.data?.message || "修改失败，请稍后重试");
  } finally {
    passwordLoading.value = false;
  }
};
</script>

<style scoped>
@import "@/styles/views/settings/account.scss";
</style>
