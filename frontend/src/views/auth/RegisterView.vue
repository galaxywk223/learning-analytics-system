<template>
  <div :class="styles.registerContainer">
    <div :class="styles.registerCard">
      <div :class="styles.cardHeader">
        <div :class="styles.logoSection">
          <div :class="styles.logo">
            <el-icon><EditPen /></el-icon>
          </div>
        </div>
        <h2 :class="styles.title">学习日志管理系统</h2>
        <p :class="styles.subtitle">创建账号，开启高效学习之旅</p>
      </div>

      <div :class="styles.cardBody">
        <el-form
          ref="registerFormRef"
          :model="registerForm"
          :rules="rules"
          label-position="top"
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
              placeholder="请输入您的邮箱"
              prefix-icon="Message"
              size="large"
            />
          </el-form-item>

          <el-form-item
            label="登录密码"
            prop="password"
            :class="styles.formItem"
          >
            <el-input
              v-model="registerForm.password"
              type="password"
              placeholder="至少6位字符"
              prefix-icon="Lock"
              size="large"
              show-password
              @input="checkPasswordStrength"
            />
            <div v-if="registerForm.password" :class="styles.passwordStrength">
              <div :class="styles.strengthBar">
                <div
                  :class="[styles.strengthFill, styles[passwordStrength]]"
                ></div>
              </div>
              <span :class="[styles.strengthText, styles[passwordStrength]]">
                密码强度: {{ passwordStrengthText }}
              </span>
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
              placeholder="请再次输入密码"
              prefix-icon="Lock"
              size="large"
              show-password
              @keyup.enter="handleRegister"
            />
          </el-form-item>

          <el-form-item :class="styles.formItem">
            <el-button
              type="primary"
              :loading="loading"
              :class="styles.submitButton"
              @click="handleRegister"
            >
              {{ loading ? "注册中..." : "立即注册" }}
            </el-button>
          </el-form-item>
        </el-form>

        <div :class="styles.benefits">
          <div :class="styles.benefit">
            <div :class="styles.benefitIcon">
              <el-icon><Checked /></el-icon>
            </div>
            <div :class="styles.benefitText">完全免费，无需支付任何费用</div>
          </div>
          <div :class="styles.benefit">
            <div :class="styles.benefitIcon">
              <el-icon><Checked /></el-icon>
            </div>
            <div :class="styles.benefitText">数据安全，隐私受到严格保护</div>
          </div>
          <div :class="styles.benefit">
            <div :class="styles.benefitIcon">
              <el-icon><Checked /></el-icon>
            </div>
            <div :class="styles.benefitText">智能分析，助力学习效率提升</div>
          </div>
        </div>

        <div :class="styles.footer">
          <span :class="styles.footerText">已有账号?</span>
          <el-button type="text" :class="styles.linkButton" @click="goToLogin">
            立即登录
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "@/stores/modules/auth";
import { EditPen, Checked } from "@element-plus/icons-vue";
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
    { min: 3, max: 20, message: "用户名长度在3到20个字符", trigger: "blur" },
  ],
  email: [
    { required: true, message: "请输入邮箱", trigger: "blur" },
    { type: "email", message: "请输入正确的邮箱格式", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, message: "密码长度至少6位", trigger: "blur" },
  ],
  confirmPassword: [
    { required: true, message: "请再次输入密码", trigger: "blur" },
    { validator: validateConfirmPassword, trigger: "blur" },
  ],
};

const passwordStrengthText = computed(() => {
  const strengthMap = {
    weak: "弱",
    medium: "中",
    strong: "强",
  };
  return strengthMap[passwordStrength.value] || "";
});

const checkPasswordStrength = () => {
  const pwd = registerForm.password;
  if (!pwd) {
    passwordStrength.value = "";
    return;
  }

  let strength = 0;

  // 长度检查
  if (pwd.length >= 8) strength++;
  if (pwd.length >= 12) strength++;

  // 包含数字
  if (/\d/.test(pwd)) strength++;

  // 包含小写字母
  if (/[a-z]/.test(pwd)) strength++;

  // 包含大写字母
  if (/[A-Z]/.test(pwd)) strength++;

  // 包含特殊字符
  if (/[!@#$%^&*(),.?":{}|<>]/.test(pwd)) strength++;

  if (strength <= 2) {
    passwordStrength.value = "weak";
  } else if (strength <= 4) {
    passwordStrength.value = "medium";
  } else {
    passwordStrength.value = "strong";
  }
};

const handleRegister = async () => {
  if (!registerFormRef.value) return;

  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true;
      try {
        const { confirmPassword, ...data } = registerForm;
        const success = await authStore.register(data);
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
// 样式已移至 @/styles/views/auth/RegisterView.module.scss
</style>
