<template>
  <div :class="styles.registerContainer">
    <div :class="styles.registerCard">
      <div :class="styles.header">
        <div :class="styles.logo">
          <Icon icon="lucide:user-plus" />
        </div>
        <div :class="styles.headerText">
          <h2>加入萤火集</h2>
          <p>三步完成注册，点亮你的学习旅程</p>
        </div>
      </div>

      <el-form
        ref="registerFormRef"
        :model="registerForm"
        :rules="rules"
        label-position="top"
        :class="styles.form"
        @submit.prevent="handleRegister"
      >
        <el-form-item label="用户名" prop="username" :class="styles.formItem">
          <el-input
            v-model="registerForm.username"
            placeholder="请输入用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>

        <el-form-item label="邮箱地址" prop="email" :class="styles.formItem">
          <el-input
            v-model="registerForm.email"
            placeholder="请输入邮箱"
            prefix-icon="Message"
            size="large"
          />
        </el-form-item>

        <el-form-item label="登录密码" prop="password" :class="styles.formItem">
          <el-input
            v-model="registerForm.password"
            type="password"
            placeholder="请设置登录密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @input="checkPasswordStrength"
          />
          <div v-if="passwordStrength" :class="styles.passwordStrength">
            <div
              :class="[styles.strengthIndicator, styles[passwordStrength]]"
            ></div>
            <span>{{ passwordStrengthText }}</span>
          </div>
        </el-form-item>

        <el-form-item
          label="确认密码"
          prop="confirmPassword"
          :class="styles.formItem"
        >
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            placeholder="再次输入密码"
            prefix-icon="Lock"
            size="large"
            show-password
            @keyup.enter="handleRegister"
          />
        </el-form-item>

        <el-button
          type="primary"
          :loading="loading"
          :class="styles.submitButton"
          @click="handleRegister"
        >
          {{ loading ? "注册中..." : "完成注册" }}
        </el-button>
      </el-form>

      <div :class="styles.footer">
        <span>已经有账号？</span>
        <el-button type="text" :class="styles.linkButton" @click="goToLogin">
          去登录
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/modules/auth";
import { Icon } from "@iconify/vue";
import styles from "@/styles/views/auth/RegisterView.module.scss";

const router = useRouter();
const authStore = useAuthStore();

const registerFormRef = ref();
const loading = ref(false);
const passwordStrength = ref("");

const registerForm = reactive({
  username: "",
  email: "",
  password: "",
  confirmPassword: "",
});

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== registerForm.password) {
    callback(new Error("两次输入的密码不一致"));
  } else {
    callback();
  }
};

const rules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 20, message: "用户名需为 3-20 个字符", trigger: "blur" },
  ],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请设置登录密码", trigger: "blur" },
    { min: 6, message: "密码长度至少 6 位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请再次输入密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" },
  ],
};

const passwordStrengthText = computed(() => {
  const map = {
    weak: "密码强度：较弱",
    medium: "密码强度：中等",
    strong: "密码强度：很强",
  };
  return map[passwordStrength.value] || "";
});

const checkPasswordStrength = () => {
  const pwd = registerForm.password;
  if (!pwd) {
    passwordStrength.value = "";
    return;
  }

  let score = 0;
  if (pwd.length >= 8) score += 1;
  if (pwd.length >= 12) score += 1;
  if (/[0-9]/.test(pwd)) score += 1;
  if (/[a-z]/.test(pwd)) score += 1;
  if (/[A-Z]/.test(pwd)) score += 1;
  if (/[^0-9a-zA-Z]/.test(pwd)) score += 1;

  if (score <= 2) passwordStrength.value = "weak";
  else if (score <= 4) passwordStrength.value = "medium";
  else passwordStrength.value = "strong";
};

const handleRegister = async () => {
  if (!registerFormRef.value) return;

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const { confirmPassword, ...payload } = registerForm;
        const success = await authStore.register(payload);
        if (success) {
          router.push("/login");
        }
      } finally {
        loading.value = false;
      }
    }
  });
};

const goToLogin = () => {
  router.push("/login");
};
</script>

<style scoped lang="scss">
/* 样式提取自模块文件 */
</style>
