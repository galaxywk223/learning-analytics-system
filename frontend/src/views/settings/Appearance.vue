<template>
  <section class="appearance-settings">
    <form @submit.prevent="saveTheme">
      <!-- 主题选择 -->
      <div class="card settings-card mb-4">
        <div class="card-header d-flex align-items-center gap-2">
          <Icon icon="lucide:palette" />
          <h5 class="card-title mb-0">主题选择</h5>
        </div>
        <div class="card-body">
          <div class="theme-selector">
            <label
              v-for="opt in themeOptions"
              :key="opt.value"
              class="theme-card"
              :class="{ selected: pendingTheme === opt.value }"
            >
              <input
                type="radio"
                :value="opt.value"
                v-model="pendingTheme"
                class="d-none"
              />
              <div
                class="color-swatch"
                :style="{ backgroundColor: opt.color }"
              ></div>
              <span class="theme-name">{{ opt.label }}</span>
              <Icon icon="lucide:check-circle-2" class="check-icon" />
            </label>
          </div>
        </div>
      </div>
      <!-- 背景图片 -->
      <div class="card settings-card">
        <div class="card-header d-flex align-items-center gap-2">
          <Icon icon="lucide:image" />
          <h5 class="card-title mb-0">背景图片</h5>
        </div>
        <div class="card-body">
          <div class="background-grid">
            <div class="background-preview-col">
              <p class="mb-2 small text-muted">当前背景</p>
              <div class="background-preview-box">
                <img
                  v-if="settingsStore.backgroundImage"
                  :src="resolveBackgroundUrl(settingsStore.backgroundImage)"
                  class="background-preview-img"
                  alt="当前背景"
                />
                <div v-else class="text-center text-muted py-5">
                  <p>当前为默认背景</p>
                </div>
                <button
                  v-if="settingsStore.backgroundImage"
                  type="button"
                  class="btn btn-sm btn-outline-danger w-100"
                  @click="removeBackground"
                >
                  <Icon
                    icon="lucide:trash-2"
                    class="me-2"
                    style="width: 16px"
                  />
                  移除背景
                </button>
              </div>
            </div>
            <div class="background-upload-col">
              <p class="mb-2 small text-muted">上传新背景</p>
              <label for="background_image" class="custom-file-upload">
                <Icon icon="lucide:upload-cloud" class="upload-icon" />
                <p class="mb-0 fw-bold">点击或拖拽图片到此</p>
                <small>支持 JPG, PNG, GIF</small>
              </label>
              <input
                ref="fileInput"
                type="file"
                id="background_image"
                accept="image/*"
                class="d-none"
                @change="handleFileChange"
              />
              <div v-if="uploadError" class="text-danger mt-2 small">
                {{ uploadError }}
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="mt-4 text-center">
        <button
          type="submit"
          name="save_theme"
          class="btn btn-primary btn-lg"
          :disabled="saving"
        >
          {{ saving ? "保存中..." : "保存主题设置" }}
        </button>
      </div>
    </form>
  </section>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { useSettingsStore } from "@/stores/modules/settings";
import { useAuthStore } from "@/stores/modules/auth";
import { getApiUrl } from "@/utils/api";
const settingsStore = useSettingsStore();
const authStore = useAuthStore();
const pendingTheme = ref(settingsStore.theme);
const saving = ref(false);
const uploadError = ref("");
const fileInput = ref(null);
const themeOptions = [
  { value: "palette-purple", label: "淡雅紫", color: "#A78BFA" },
  { value: "palette-green", label: "活力绿", color: "#4ADE80" },
  { value: "palette-blue", label: "商务蓝", color: "#60A5FA" },
  { value: "palette-yellow", label: "暖阳黄", color: "#FACC15" },
  { value: "palette-red", label: "热情红", color: "#F87171" },
];
function resolveBackgroundUrl(path) {
  if (!path) return "";
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
  return `${base}/static/uploads/backgrounds/${path}`;
}
async function saveTheme() {
  if (!pendingTheme.value) return;
  saving.value = true;
  try {
    settingsStore.theme = pendingTheme.value;
    await settingsStore.saveSettings();
  } catch (e) {
    console.error("保存主题失败", e);
  } finally {
    saving.value = false;
  }
}
async function removeBackground() {
  if (!confirm("确定要移除自定义背景吗？")) return;
  try {
    const base = getApiUrl("/users/upload/background");
    const headers = authStore?.accessToken
      ? { Authorization: `Bearer ${authStore.accessToken}` }
      : {};
    const res = await fetch(base, { method: "DELETE", headers });
    if (!res.ok) throw new Error("删除失败");
    settingsStore.setBackgroundImage("");
  } catch (e) {
    console.error("删除背景失败", e);
  }
}
async function handleFileChange(e) {
  uploadError.value = "";
  const file = e.target.files[0];
  if (!file) return;
  const allowed = ["png", "jpg", "jpeg", "gif"];
  const ext = file.name.split(".").pop().toLowerCase();
  if (!allowed.includes(ext)) {
    uploadError.value = "不支持的文件格式";
    return;
  }
  try {
    const formData = new FormData();
    formData.append("file", file);
    const uploadUrl = getApiUrl("/users/upload/background");
    const headers = authStore?.accessToken
      ? { Authorization: `Bearer ${authStore.accessToken}` }
      : {};
    const res = await fetch(uploadUrl, {
      method: "POST",
      headers,
      body: formData,
    });
    const json = await res.json();
    if (!res.ok) {
      uploadError.value = json.message || "上传失败";
      return;
    }
    const bg =
      json.background_image || json.data?.background_image || json.data?.url;
    if (bg) {
      settingsStore.setBackgroundImage(bg);
      await saveTheme();
    } else {
      uploadError.value = "服务器未返回路径";
    }
  } catch (err) {
    uploadError.value = err.message || "上传异常";
  } finally {
    if (fileInput.value) fileInput.value.value = "";
  }
}
</script>
<style scoped>
.appearance-settings {
  max-width: 1000px;
  margin: 0 auto;
}
.settings-card {
  border: 1px solid #dee2e6;
  border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  background: #fff;
}
.card-header {
  padding: 0.85rem 1.1rem;
  border-bottom: 1px solid #f1f3f5;
}
.card-title {
  font-family: "Poppins", sans-serif;
  font-size: 1rem;
}
.theme-selector {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1rem;
}
.theme-card {
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 8px;
  padding: 1rem;
  text-align: center;
  position: relative;
  background: #fafafa;
  transition: 0.2s;
}
.theme-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
}
.theme-card.selected {
  border-color: var(--color-primary-dark, #6366f1);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25);
}
.color-swatch {
  width: 100%;
  height: 60px;
  border-radius: 6px;
  margin-bottom: 0.75rem;
}
.check-icon {
  display: none;
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  background: var(--color-primary-dark, #6366f1);
  color: #fff;
  border-radius: 50%;
  padding: 4px;
}
.theme-card.selected .check-icon {
  display: block;
}
.background-grid {
  display: flex;
  gap: 1.5rem;
}
.background-preview-col,
.background-upload-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.background-preview-box,
.custom-file-upload {
  border: 1px solid #dee2e6;
  border-radius: 8px;
  padding: 1rem;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.background-preview-img {
  width: 100%;
  height: 150px;
  object-fit: cover;
  border-radius: 6px;
  margin-bottom: 1rem;
}
.custom-file-upload {
  border: 2px dashed #dee2e6;
  align-items: center;
  justify-content: center;
  text-align: center;
  cursor: pointer;
  transition: 0.2s;
  display: flex;
  flex-direction: column;
}
.custom-file-upload:hover {
  border-color: var(--color-primary, #6366f1);
  background: #f8f9fa;
}
.upload-icon {
  width: 48px;
  height: 48px;
  color: #64748b;
  margin-bottom: 1rem;
}
.mt-4 {
  margin-top: 1.5rem;
}
@media (max-width: 780px) {
  .background-grid {
    flex-direction: column;
  }
}
</style>
