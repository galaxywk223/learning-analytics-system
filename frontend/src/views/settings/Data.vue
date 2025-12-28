<template>
  <PageContainer
    :title="{ icon: '💾', text: '数据管理' }"
    subtitle="备份、恢复或清空您的学习数据"
    :custom-class="'settings-subpage'"
  >
    <div class="data-grid">
      <!-- 导出数据卡片 -->
      <div class="data-card export-card">
        <div class="card-icon">🗂️</div>
        <div class="card-text">
          <h4>导出全部数据</h4>
          <p>包含学习记录、阶段、分类、计划、成就、格言、倒计时等。</p>
        </div>
        <button
          type="button"
          class="pill-btn primary"
          :disabled="exporting"
          @click="handleExport"
        >
          <span>📦 导出 ZIP 备份</span>
        </button>
      </div>

      <!-- 导入数据卡片 -->
      <div
        class="data-card import-card"
        :class="{ dragging: dragging }"
        @dragover.prevent="dragging = true"
        @dragleave.prevent="dragging = false"
        @drop.prevent="onDrop"
      >
        <input
          ref="fileInput"
          type="file"
          accept=".zip"
          class="file-input"
          @change="onInputFile"
        />
        <div class="import-content" @click="fileInput?.click()">
          <div class="card-icon ghost">📦</div>
          <h4>导入备份数据</h4>
          <p class="desc">点击或拖拽 ZIP 文件到此处</p>
          <p class="warn">将覆盖当前所有数据且不可恢复</p>
        </div>
        <div v-if="selectedFile" class="file-info">
          <div class="file-name">{{ selectedFile.name }}</div>
          <div class="file-size">
            {{ (selectedFile.size / 1024).toFixed(1) }} KB
          </div>
          <div class="file-actions">
            <button
              class="pill-btn danger"
              type="button"
              :disabled="importing"
              @click="confirmImport"
            >
              {{ importing ? "正在导入..." : "导入并覆盖" }}
            </button>
            <button
              class="pill-btn ghost"
              type="button"
              :disabled="importing"
              @click="clearSelection"
            >
              取消
            </button>
          </div>
        </div>
      </div>

      <!-- 危险区域 -->
      <div class="danger-row">
        <div class="danger-left">
          <span class="danger-icon">🚨</span>
          <div>
            <div class="danger-title">清空所有数据</div>
            <div class="danger-desc">此操作不可恢复，请谨慎操作。</div>
          </div>
        </div>
        <button
          type="button"
          class="pill-btn danger solid"
          :disabled="clearing"
          @click="confirmClear"
        >
          🗑️ {{ clearing ? "正在清空..." : "立即清空" }}
        </button>
      </div>
    </div>
  </PageContainer>
</template>

<script setup>
import { ref } from "vue";
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus";
import PageContainer from "@/components/layout/PageContainer.vue";

defineOptions({ name: "DataSettingsView" });

const exporting = ref(false);
const importing = ref(false);
const clearing = ref(false);
const selectedFile = ref(null);
const dragging = ref(false);
const fileInput = ref(null);

function onInputFile(e) {
  const file = e.target.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".zip")) {
    ElMessage.error("仅支持 .zip 文件");
    return;
  }
  selectedFile.value = file;
}

function onDrop(e) {
  dragging.value = false;
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!file.name.toLowerCase().endsWith(".zip")) {
    ElMessage.error("仅支持 .zip 文件");
    return;
  }
  selectedFile.value = file;
}

function clearSelection() {
  selectedFile.value = null;
  if (fileInput.value) fileInput.value.value = "";
}

async function handleExport() {
  if (exporting.value) return;
  exporting.value = true;
  try {
    // 使用原生 axios 直接获取 headers + blob（不经过全局拦截器）
    const baseURL =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
    const token = localStorage.getItem("access_token");
    const res = await axios.get(baseURL + "/api/records/export", {
      responseType: "blob",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const disp = res.headers["content-disposition"] || "";
    const m = /filename\*=UTF-8''([^;]+)|filename="?([^;"]+)"?/i.exec(disp);
    const filename = decodeURIComponent(
      m?.[1] || m?.[2] || "records_backup.zip",
    );
    const blob = res.data;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    ElMessage.success("ZIP 导出已开始下载");
  } catch (e) {
    console.error(e);
    ElMessage.error("导出失败");
  } finally {
    exporting.value = false;
  }
}

async function confirmImport() {
  if (!selectedFile.value) return;
  try {
    await ElMessageBox.confirm(
      "此操作将覆盖您当前的所有数据，且无法撤销。确定继续吗？",
      "确认导入",
      { type: "warning", confirmButtonText: "继续", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  importing.value = true;
  try {
    const baseURL =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
    const token = localStorage.getItem("access_token");
    const formData = new FormData();
    formData.append("file", selectedFile.value);
    const res = await axios.post(
      baseURL + "/api/records/import_zip",
      formData,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      },
    );
    if (res.data?.success) {
      ElMessage.success(res.data.message || "导入成功");
      selectedFile.value = null;
      setTimeout(() => window.location.reload(), 1200);
    } else {
      ElMessage.error(res.data?.message || "导入失败");
    }
  } catch (e) {
    console.error("导入错误:", e);
    const errorMsg =
      e?.response?.data?.message || e?.message || "导入失败，请检查文件格式";
    ElMessage.error(errorMsg);
  } finally {
    importing.value = false;
  }
}

async function confirmClear() {
  try {
    await ElMessageBox.confirm(
      "最后警告：确定要永久清空账户的所有数据吗？此操作无法恢复！",
      "清空数据",
      {
        type: "error",
        confirmButtonText: "是的，清空",
        cancelButtonText: "取消",
        confirmButtonClass: "el-button--danger",
      },
    );
  } catch {
    return;
  }
  clearing.value = true;
  try {
    const baseURL =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
    const token = localStorage.getItem("access_token");
    const res = await axios.post(
      baseURL + "/api/records/clear_data",
      {},
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      },
    );
    if (res.data?.success) {
      ElMessage.success(res.data?.message || "数据已清空");
    } else {
      ElMessage.error(res.data?.message || "清空失败");
    }
    ElMessage.success("数据已清空");
    // 可选：跳转或刷新页面
  } catch (e) {
    console.error(e);
    ElMessage.error("清空失败");
  } finally {
    clearing.value = false;
  }
}
</script>

<style scoped>
.data-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
  align-items: stretch;
}

.data-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  padding: 18px 18px 16px;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 240px;
}

.data-card h4 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: #0f172a;
}

.data-card p {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}

.card-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  background: rgba(59, 130, 246, 0.12);
  font-size: 28px;
  color: #2563eb;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
}

.card-icon.ghost {
  background: rgba(99, 102, 241, 0.08);
  color: #4f46e5;
}

.card-text {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  justify-content: center;
}

.pill-btn {
  border: none;
  border-radius: 999px;
  padding: 12px 16px;
  font-weight: 800;
  font-size: 14px;
  cursor: pointer;
  transition:
    transform 0.15s ease,
    box-shadow 0.2s ease,
    opacity 0.15s ease;
  align-self: stretch;
}

.pill-btn.primary {
  background: linear-gradient(135deg, #6d7cff, #4f46e5);
  color: #ffffff;
  box-shadow: 0 12px 26px rgba(79, 70, 229, 0.28);
}

.pill-btn.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  box-shadow: none;
}

.pill-btn.ghost {
  background: #f8fafc;
  color: #475569;
  border: 1px solid #e5e7eb;
}

.pill-btn.danger {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
  border: 1px solid rgba(239, 68, 68, 0.25);
}

.pill-btn.danger.solid {
  background: #ef4444;
  color: #ffffff;
  border: none;
  box-shadow: 0 10px 22px rgba(239, 68, 68, 0.25);
}

.import-card {
  background: #f9fafb;
  border: 2px dashed rgba(99, 102, 241, 0.35);
  justify-content: center;
  position: relative;
  overflow: hidden;
}

.import-card.dragging {
  border-color: #4f46e5;
  background: rgba(79, 70, 229, 0.04);
}

.file-input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

.import-content {
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.import-content h4 {
  font-size: 17px;
  margin: 0;
}

.import-content .desc {
  font-size: 13px;
  color: #6b7280;
}

.import-content .warn {
  font-size: 12px;
  color: #f59e0b;
}

.file-info {
  margin-top: auto;
  background: #fff;
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  z-index: 10;
}

.file-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.danger-row {
  grid-column: span 2;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 16px;
  padding: 14px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.danger-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.danger-icon {
  font-size: 22px;
}

.danger-title {
  font-weight: 800;
  color: #b91c1c;
  font-size: 15px;
}

.danger-desc {
  color: #6b7280;
  font-size: 13px;
}

@media (max-width: 900px) {
  .data-grid {
    grid-template-columns: 1fr;
  }

  .danger-row {
    grid-column: span 1;
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
