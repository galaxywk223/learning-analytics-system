import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/es/locale/lang/zh-cn";
import * as ElementPlusIconsVue from "@element-plus/icons-vue";

// 导入统一的样式入口
import "./styles/index.scss";

import App from "./App.vue";
import { createIcons } from "lucide";
import router from "./router";

const app = createApp(App);

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component);
}

app.use(createPinia());
app.use(router);
app.use(ElementPlus, {
  locale: zhCn,
});

app.mount("#app");

// 初始化 lucide 图标（替换 Element Plus 图标在仪表盘中的使用）
try {
  createIcons();
} catch (e) {
  console.error("Lucide init failed", e);
}

// 每次路由切换后重新渲染图标，避免动态内容未渲染
router.afterEach(() => {
  try {
    createIcons();
  } catch (e) {
    console.error("Lucide refresh failed", e);
  }
});

// 全局错误日志，辅助排查空白页
window.addEventListener("error", (ev) => {
  console.error("Global error:", ev.error || ev.message);
});
window.addEventListener("unhandledrejection", (ev) => {
  console.error("Unhandled promise rejection:", ev.reason);
});
