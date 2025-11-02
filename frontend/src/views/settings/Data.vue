<template>
  <section class="data-settings">
    <header class="settings-section-header">
      <h2>数据管理</h2>
      <p>备份、恢复或清空您的学习数据</p>
    </header>

    <!-- 导出数据卡片 -->
    <div class="settings-card">
      <div class="card-header">
        <Icon icon="lucide:download" />
        <h5 class="card-title">导出全部数据</h5>
      </div>
      <div class="card-body">
        <p class="card-desc">
          打包您账户下的所有内容为 <span class="code-tag">.zip</span>
          文件：学习记录、阶段、分类、计划、成就、格言、倒计时等。
        </p>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="exporting"
          @click="handleExport"
        >
          <Icon
            icon="lucide:archive"
            :style="{ width: '18px', height: '18px' }"
          />
          <span v-if="!exporting">导出 ZIP 备份</span>
          <span v-else>正在导出...</span>
        </button>
      </div>
    </div>

    <!-- 导入数据卡片 -->
    <div class="settings-card">
      <div class="card-header">
        <Icon icon="lucide:upload" />
        <h5 class="card-title">导入备份数据</h5>
      </div>
      <div class="card-body">
        <p class="card-desc">
          从之前生成的 <span class="code-tag">.zip</span> 备份恢复。
          <span class="text-warning">此操作将覆盖当前所有数据且不可撤销。</span>
        </p>

        <label
          class="upload-zone"
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
          <div class="zone-content">
            <Icon icon="lucide:file-archive" class="zone-icon" />
            <p class="zone-title">点击或拖拽 ZIP 到此</p>
            <p class="zone-hint">仅支持单个 .zip 备份文件</p>
          </div>
        </label>

        <div v-if="selectedFile" class="file-info">
          <Icon icon="lucide:file-check" class="file-icon" />
          <div class="file-details">
            <div class="file-name">{{ selectedFile.name }}</div>
            <div class="file-size">
              {{ (selectedFile.size / 1024).toFixed(1) }} KB
            </div>
          </div>
          <button
            type="button"
            class="btn-remove"
            @click="clearSelection"
            :disabled="importing"
          >
            <Icon icon="lucide:x" />
          </button>
        </div>

        <div class="form-actions" v-if="selectedFile">
          <button
            type="button"
            class="btn btn-danger"
            :disabled="!selectedFile || importing"
            @click="confirmImport"
          >
            <Icon
              icon="lucide:upload"
              :style="{ width: '18px', height: '18px' }"
            />
            {{ importing ? "正在导入..." : "导入并覆盖" }}
          </button>
          <button
            type="button"
            class="btn btn-secondary"
            :disabled="!selectedFile || importing"
            @click="clearSelection"
          >
            取消
          </button>
        </div>
      </div>
    </div>

    <!-- 危险区域 -->
    <div class="settings-card danger-card">
      <div class="card-header danger-header">
        <Icon icon="lucide:alert-triangle" />
        <h5 class="card-title">危险区域</h5>
      </div>
      <div class="card-body">
        <h6 class="danger-title">清空所有数据</h6>
        <p class="card-desc">
          该操作将<span class="text-danger">永久删除</span
          >您账户下的全部内容（包括学习记录、阶段、分类、计划、成就、格言、倒计时等），
          <span class="text-danger">且无法恢复</span>。
        </p>
        <button
          type="button"
          class="btn btn-danger"
          :disabled="clearing"
          @click="confirmClear"
        >
          <Icon
            icon="lucide:trash-2"
            :style="{ width: '18px', height: '18px' }"
          />
          <span v-if="!clearing">立即清空</span>
          <span v-else>正在清空...</span>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref } from "vue";
import { Icon } from "@iconify/vue";
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus";

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
      m?.[1] || m?.[2] || "records_backup.zip"
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
      { type: "warning", confirmButtonText: "继续", cancelButtonText: "取消" }
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
      }
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
      }
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
      }
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
@import "@/styles/views/settings/account.scss";

/* 数据管理特定样式 */
.data-settings {
  max-width: 900px;
}

/* 上传区域 */
.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
  padding: 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  display: block;
  background: #fafafa;
  margin: 1rem 0;
}

.upload-zone:hover {
  border-color: #667eea;
  background: #f8f9ff;
}

.upload-zone.dragging {
  border-color: #667eea;
  background: #f0f2ff;
  transform: scale(1.01);
}

.file-input {
  display: none;
}

.zone-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
}

.zone-icon {
  width: 48px;
  height: 48px;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.zone-title {
  font-size: 1rem;
  font-weight: 600;
  color: #334155;
  margin: 0;
}

.zone-hint {
  font-size: 0.825rem;
  color: #64748b;
  margin: 0;
}

/* 文件信息 */
.file-info {
  display: flex;
  align-items: center;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  margin: 1rem 0;
}

.file-icon {
  width: 32px;
  height: 32px;
  color: #667eea;
  flex-shrink: 0;
}

.file-details {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-size: 0.9rem;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-size {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.125rem;
}

.btn-remove {
  width: 28px;
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  color: #64748b;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

.btn-remove:hover:not(:disabled) {
  background: #e2e8f0;
  color: #1e293b;
}

.btn-remove:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 危险卡片 */
.danger-card {
  border-color: #fecaca;
}

.danger-header {
  background: #fef2f2;
  color: #991b1b;
  border-bottom-color: #fecaca;
}

.danger-header .card-title {
  color: #991b1b;
}

.danger-header svg {
  color: #dc2626;
}

.danger-title {
  font-size: 1rem;
  font-weight: 600;
  color: #991b1b;
  margin: 0 0 0.5rem 0;
}

.card-desc {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 1.25rem;
}

.code-tag {
  background: #f1f5f9;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: "Monaco", "Menlo", "Courier New", monospace;
  font-size: 0.825rem;
  color: #475569;
  font-weight: 500;
}

.text-warning {
  color: #f59e0b;
  font-weight: 500;
}

.text-danger {
  color: #dc2626;
  font-weight: 500;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
}

.btn-danger:hover:not(:disabled) {
  background: #b91c1c;
}

/* 响应式 */
@media (max-width: 768px) {
  .upload-zone {
    padding: 1.5rem 1rem;
  }

  .zone-icon {
    width: 40px;
    height: 40px;
  }

  .file-info {
    flex-wrap: wrap;
  }
}
</style>
