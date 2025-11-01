// 简单 API URL 构造工具
// 使用环境变量 VITE_API_BASE_URL (与 request.js 保持一致)
export function getApiUrl(path = "") {
  const base = import.meta.env.VITE_API_BASE_URL || "http://localhost:5000";
  if (!path) return base;
  if (path.startsWith("http")) return path;
  return base.replace(/\/$/, "") + "/" + path.replace(/^\//, "");
}
