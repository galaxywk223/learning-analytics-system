/**
 * 数据备份/恢复/清空相关 API 封装
 * 后端对应 Flask blueprint: records_bp
 * 原始模板使用的端点:
 *  - GET /export/zip        -> 导出打包 ZIP (Content-Disposition attachment)
 *  - POST /import/zip       -> 导入 ZIP 完全覆盖现有数据 (表单字段名: file)
 *  - POST /clear_data       -> 清空所有个人数据
 * 假设：这些端点在 API 模式下无需 CSRF（如仍开启 CSRF 需在请求头附加 X-CSRFToken）。
 * 基地址由 axios 实例 request.js 统一处理 (VITE_API_BASE_URL)。
 */
import request from "@/utils/request";

// 根据后端 blueprint 注册: app.register_blueprint(records_bp, url_prefix="/records")
// 旧模板直接访问 /records/... ; 日志显示 /api/records 404, 说明 /api 前缀并未代理该蓝图, 改为直接 /records
const BASE = "/records";

let csrfTokenCache = null;
async function fetchCsrfTokenFromSettingsPage() {
  if (csrfTokenCache) return csrfTokenCache;
  try {
    const baseURL =
      import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
    const res = await fetch(baseURL + BASE + "/settings/data", {
      credentials: "include",
    });
    if (!res.ok) return null;
    const html = await res.text();
    // 匹配隐藏字段 name="csrf_token" value="..."
    const m = html.match(/name=["']csrf_token["'][^>]*value=["']([^"']+)["']/i);
    if (m) {
      csrfTokenCache = m[1];
      return csrfTokenCache;
    }
  } catch (e) {
    console.warn("[data-api] 获取 csrf_token 失败", e);
  }
  return null;
}

async function ensureCsrfToken() {
  if (csrfTokenCache) return csrfTokenCache;
  return fetchCsrfTokenFromSettingsPage();
}

// 解析 Content-Disposition 获取文件名
function extractFilename(disposition) {
  if (!disposition) return "backup.zip";
  const match = /filename\*=UTF-8''([^;]+)|filename="?([^;"]+)"?/i.exec(
    disposition
  );
  return decodeURIComponent(match?.[1] || match?.[2] || "backup.zip");
}

// 导出 ZIP: 直接使用原生 axios (要拿到二进制) 而不是我们拦截后被改写的数据
// (移除未使用的 exportDataZip，统一使用下方 downloadDataZipRaw 保留 headers)

// 重新实现不经过统一 response 拦截器的下载（保留 headers）
import axios from "axios";
export async function downloadDataZipRaw() {
  const baseURL = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
  const token = localStorage.getItem("access_token");
  const res = await axios.get(baseURL + BASE + "/export/zip", {
    responseType: "blob",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  const filename = extractFilename(res.headers["content-disposition"]);
  return { blob: res.data, filename };
}

export async function importDataZip(file) {
  const formData = new FormData();
  formData.append("file", file);
  const csrf = await ensureCsrfToken();
  if (csrf) formData.append("csrf_token", csrf);
  return request.post(BASE + "/import/zip", formData, {
    headers: { "Content-Type": "multipart/form-data" },
    maxBodyLength: Infinity,
  });
}

export async function clearAllData() {
  const csrf = await ensureCsrfToken();
  const formData = new FormData();
  if (csrf) formData.append("csrf_token", csrf);
  return request.post(BASE + "/clear_data", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
}

export function triggerBlobDownload(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export default {
  downloadDataZipRaw,
  importDataZip,
  clearAllData,
  triggerBlobDownload,
};
