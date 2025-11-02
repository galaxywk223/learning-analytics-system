import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/es/locale/lang/zh-cn";

// 导入统一的样式入口
import "./styles/index.scss";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);

// 性能优化：使用 Pinia 并启用开发工具（仅开发环境）
const pinia = createPinia();
app.use(pinia);
app.use(router);

// Element Plus 配置优化
app.use(ElementPlus, {
  locale: zhCn,
  size: "default",
  zIndex: 3000,
});

// 性能优化：设置 Vue 性能追踪（仅开发环境）
if (import.meta.env.DEV) {
  app.config.performance = true;
}

app.mount("#app");

// 全局错误日志，辅助排查空白页
window.addEventListener("error", (ev) => {
  console.error("Global error:", ev.error || ev.message);
});
window.addEventListener("unhandledrejection", (ev) => {
  console.error("Unhandled promise rejection:", ev.reason);
});
