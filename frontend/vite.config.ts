import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 性能优化：跳过某些元素的检查
          isCustomElement: (tag) => tag.startsWith("ion-"),
        },
      },
    }),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      scss: {
        api: "modern-compiler", // 使用现代Sass编译器API
        silenceDeprecations: ["legacy-js-api", "import"], // 暂时静默这些弃用警告
      },
    },
  },
  // 性能优化配置
  build: {
    target: "esnext",
    minify: "esbuild",
    cssCodeSplit: true,
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          "element-plus": ["element-plus"],
          "vue-vendor": ["vue", "vue-router", "pinia"],
          charts: ["chart.js", "vue-echarts", "echarts"],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  // 开发服务器优化
  server: {
    host: "127.0.0.1", // 只监听本地
    port: 5173, // 使用 Vite 默认端口
    strictPort: false, // 如果端口被占用,自动尝试下一个可用端口
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
    // 性能优化：预热常用文件
    warmup: {
      clientFiles: ["./src/App.vue", "./src/main.ts", "./src/router/index.ts"],
    },
  },
  // 性能优化：优化依赖预构建
  optimizeDeps: {
    include: ["vue", "vue-router", "pinia", "element-plus", "axios"],
    exclude: ["@iconify/vue"],
  },
});
