import { fileURLToPath, URL } from "node:url";
import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

const resolvePackageName = (id: string) => {
  const normalized = id.replace(/\\/g, "/");
  const parts = normalized.split("node_modules/")[1];

  if (!parts) return "";

  const segments = parts.split("/");
  return segments[0].startsWith("@") ? `${segments[0]}/${segments[1]}` : segments[0];
};

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

  // 构建配置（手动分包降低 chunk 体积）
  build: {
    target: "esnext",
    minify: "esbuild",
    cssCodeSplit: true,
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        // 分包策略：大库独立，Vue 生态合并，其余放通用 vendor
        manualChunks: (id) => {
          if (!id.includes("node_modules")) return;

          const pkgName = resolvePackageName(id);

          // 大库单独拆包，避免和业务、其他依赖混在一起
          if (pkgName === "echarts" || pkgName === "vue-echarts") return "echarts";
          if (pkgName === "element-plus") return "element-plus";
          if (pkgName === "chart.js" || pkgName === "chartjs-plugin-datalabels") return "chartjs";

          // 核心 Vue 生态合并成一个稳定的 vendor
          if (["vue", "vue-router", "pinia", "@vue", "@vueuse"].includes(pkgName)) return "vendor-vue";

          // 其余三方依赖统一打到 vendor，和业务代码分离
          return "vendor";
        },
      },
    },
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
