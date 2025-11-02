<template>
  <section class="data-settings-wrapper">
    <!-- 导出数据卡片 -->
    <div class="settings-card card mb-4">
      <div class="card-header d-flex align-items-center gap-2">
        <Icon icon="lucide:archive" />
        <h5 class="card-title mb-0">导出全部数据</h5>
      </div>
      <div class="card-body">
        <p class="desc">
          打包您账户下的所有内容为
          <code>.zip</code
          >：学习记录、阶段、分类、计划、成就、格言、倒计时、附件等。
        </p>
        <button
          type="button"
          class="btn btn-primary"
          :disabled="exporting"
          @click="handleExport"
        >
          <span v-if="!exporting">导出 ZIP 备份</span>
          <span v-else>正在导出...</span>
        </button>
      </div>
    </div>

    <!-- 导入数据卡片 -->
    <div class="settings-card card mb-4">
      <div class="card-header d-flex align-items-center gap-2">
        <Icon icon="lucide:upload" />
        <h5 class="card-title mb-0">导入备份数据</h5>
      </div>
      <div class="card-body">
        <p class="desc">
          从之前生成的 <code>.zip</code> 备份恢复。此操作将
          <strong class="text-danger">覆盖</strong> 当前所有数据并且
          <strong class="text-danger">不可撤销</strong>。
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
            class="d-none"
            @change="onInputFile"
          />
          <Icon icon="lucide:file-archive" class="zone-icon" />
          <p class="mb-1"><strong>点击或拖拽 ZIP 到此</strong></p>
          <small>仅支持单个 .zip 备份文件</small>
        </label>
        <div v-if="selectedFile" class="file-meta mt-2">
          已选文件：{{ selectedFile.name }} ({{
            (selectedFile.size / 1024).toFixed(1)
          }}
          KB)
        </div>
        <div class="import-actions mt-3">
          <button
            type="button"
            class="btn btn-danger"
            :disabled="!selectedFile || importing"
            @click="confirmImport"
          >
            {{ importing ? "正在导入..." : "导入并覆盖" }}
          </button>
          <button
            type="button"
            class="btn btn-outline-secondary"
            :disabled="!selectedFile || importing"
            @click="clearSelection"
          >
            清除选择
          </button>
        </div>
      </div>
    </div>

    <!-- 危险区域 -->
    <div class="settings-card card danger-zone">
      <div class="card-header d-flex align-items-center gap-2">
        <Icon icon="lucide:alert-triangle" class="text-danger" />
        <h5 class="card-title mb-0 text-danger">危险区域</h5>
      </div>
      <div class="card-body">
        <h6 class="fw-bold mb-2">清空所有数据</h6>
        <p class="desc mb-3">
          该操作将
          <strong class="text-danger">永久删除</strong>
          您账户下的全部内容（包括学习记录、阶段、分类、计划、成就、格言、倒计时、附件等），且无法恢复。
        </p>
        <button
          type="button"
          class="btn btn-outline-danger"
          :disabled="clearing"
          @click="confirmClear"
        >
          <span v-if="!clearing">立即清空</span>
          <span v-else>正在清空...</span>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
/**
 * Data Settings Page
 * 重现原始 Flask 模板的三大功能：导出、导入、清空。
 * - 导出：GET /export/zip (返回 ZIP Blob)
 * - 导入：POST /import/zip (multipart, file 字段) 覆盖数据
 * - 清空：POST /clear_data
 */
import { ref, onMounted } from "vue";
import axios from "axios";
import { ElMessage, ElMessageBox } from "element-plus"; // 保留消息组件

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
    const res = await axios.get(baseURL + "/api/records/export_zip", {
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
onMounted(() => {
  import("lucide").then((m) => m.createIcons()).catch(() => {});
});
</script>

<style scoped>
.data-settings-wrapper {
  max-width: 960px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
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
  font-size: 1rem;
  font-weight: 600;
}
.card-body {
  padding: 1.1rem 1.2rem 1.3rem;
}
.desc {
  font-size: 0.8rem;
  color: #555;
  line-height: 1.5;
}
code {
  background: #f6f6f6;
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.7rem;
}
.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
  padding: 1.2rem;
  text-align: center;
  cursor: pointer;
  transition: 0.2s;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.upload-zone.dragging {
  background: #f8fafc;
  border-color: #6366f1;
}
.zone-icon {
  width: 40px;
  height: 40px;
  color: #64748b;
  margin-bottom: 0.6rem;
}
.file-meta {
  font-size: 0.7rem;
  color: #555;
}
.import-actions {
  display: flex;
  gap: 0.75rem;
}
.danger-zone {
  border-color: #dc3545;
}
.danger-zone .card-header {
  background-color: #f8d7da;
  color: #58151c;
}
.btn {
  font-size: 0.8rem;
}
@media (max-width: 680px) {
  .data-settings-wrapper {
    padding-bottom: 2rem;
  }
}
</style>
