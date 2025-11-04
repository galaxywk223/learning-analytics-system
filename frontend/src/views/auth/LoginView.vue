<template>
  <div :class="styles.loginContainer">
    <div :class="styles.loginCard">
      <div :class="styles.header">
        <div :class="styles.logo">
          <Icon icon="lucide:book-open" />
        </div>
        <div :class="styles.headerText">
          <h2>学习日志管理系统</h2>
          <p>多端同步 Â· 数据可视 Â· 智能规划</p>
        </div>
      </div>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="rules"
        label-position="top"
        :class="styles.form"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="邮箱地址" prop="email" :class="styles.formItem">
          <el-input
            v-model="loginForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item label="登录密码" prop="password" :class="styles.formItem">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          :class="styles.submitButton"
          @click="handleLogin"
        >
          {{ loading ? "登录中..." : "立即登录" }}
        </el-button>
      </el-form>

      <div :class="styles.meta">
        <span>记住密码以便快速进入学习空间</span>
      </div>

      <div :class="styles.footer">
        <span>还没有账号？</span>
        <el-button type="text" :class="styles.linkButton" @click="goToRegister">
          去注册
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/modules/auth";
import { Icon } from "@iconify/vue";
import styles from "@/styles/views/auth/LoginView.module.scss";

const router = useRouter();
const authStore = useAuthStore();

const loginFormRef = ref();
const loading = ref(false);

const loginForm = reactive({
  email: "",
  password: "",
});

const rules = {
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度至少 6 位", trigger: "blur" },
  ],
};

const handleLogin = async () => {
  if (!loginFormRef.value) return;

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const success = await authStore.login(loginForm);
        if (success) {
          router.push("/dashboard");
        }
      } finally {
        loading.value = false;
      }
    }
  });
};

const goToRegister = () => {
  router.push("/register");
};
</script>

<style scoped lang="scss">
/* 样式提取自模块文件 */
</style>
