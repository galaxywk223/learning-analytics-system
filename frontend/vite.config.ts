import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [
    vue({
      template: {
        compilerOptions: {
          // 跳过自定义元素检查
          isCustomElement: (tag) => tag.startsWith("ion-"),
        },
      },
    }),
  ],

  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
    // 避免出现多个 Vue 实例
    dedupe: ["vue"],
  },

  css: {
    preprocessorOptions: {
      scss: {
        api: "modern-compiler",
        silenceDeprecations: ["legacy-js-api", "import"],
      },
    },
  },

  // 构建配置（⚠️ 关键：不做任何 manualChunks）
  build: {
    target: "esnext",
    minify: "esbuild",
    cssCodeSplit: true,
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    // 不写 rollupOptions.output.manualChunks，让 Vite 自己拆包
  },

  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: false,
    proxy: {
      "/api": {
        target: "http://localhost:5000",
        changeOrigin: true,
      },
    },
    warmup: {
      clientFiles: ["./src/App.vue", "./src/main.ts", "./src/router/index.ts"],
    },
  },

  // 仅影响 dev 的依赖预构建，生产构建不依赖这里；保持精简避免误导
  optimizeDeps: {
    include: [],
    exclude: ["@iconify/vue"],
  },
});
