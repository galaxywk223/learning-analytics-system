/**
 * 路由配置
 */
import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
} from "vue-router";
import { useAuthStore } from "@/stores";

const MainLayout = () => import("@/components/layout/MainLayout.vue");

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/dashboard" },
  {
    path: "/login",
    name: "Login",
    component: () => import("@/views/auth/LoginView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/register",
    name: "Register",
    component: () => import("@/views/auth/RegisterView.vue"),
    meta: { requiresAuth: false },
  },
  {
    path: "/",
    component: MainLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: "dashboard",
        name: "Dashboard",
        component: () => import("@/views/dashboard/DashboardView.vue"),
        meta: { title: "仪表盘" },
      },
      {
        path: "records",
        name: "Records",
        component: () => import("@/views/records/RecordsView.vue"),
        meta: { title: "学习记录" },
      },
      {
        path: "categories",
        name: "Categories",
        component: () => import("@/views/categories/CategoriesView.vue"),
        meta: { title: "分类管理" },
      },
      {
        path: "stages",
        name: "Stages",
        component: () => import("@/views/stages/StagesView.vue"),
        meta: { title: "阶段管理" },
      },
      {
        path: "todos",
        name: "Todos",
        component: () => import("@/views/todos/TodosView.vue"),
        meta: { title: "待办事项" },
      },
      {
        path: "milestones",
        name: "Milestones",
        component: () => import("@/views/milestones/MilestonesView.vue"),
        meta: { title: "里程碑" },
      },
      {
        path: "milestones/categories",
        name: "MilestoneCategories",
        component: () =>
          import("@/views/milestones/MilestoneCategoryManager.vue"),
        meta: { title: "里程碑分类管理" },
      },
      {
        path: "countdown",
        name: "Countdown",
        component: () => import("@/views/countdown/CountdownView.vue"),
        meta: { title: "倒计时" },
      },
      {
        path: "focus",
        name: "Focus",
        component: () => import("@/views/focus/FocusView.vue"),
        meta: { title: "专注模式" },
      },
      {
        path: "charts",
        name: "Charts",
        component: () => import("@/views/charts/ChartsView.vue"),
        meta: { title: "统计分析" },
      },
      {
        path: "settings",
        component: () => import("@/views/settings/SettingsLayout.vue"),
        // 旧项目默认进入账户设置页
        redirect: "/settings/account",
        children: [
          {
            path: "account",
            name: "SettingsAccount",
            component: () => import("@/views/settings/Account.vue"),
            meta: { title: "账户设置" },
          },
          {
            path: "data",
            name: "SettingsData",
            component: () => import("@/views/settings/Data.vue"),
            meta: { title: "数据管理" },
          },
          // 新增：阶段管理（与顶层 /stages 复用同一组件）
          {
            path: "stages",
            name: "SettingsStages",
            component: () => import("@/views/stages/StagesView.vue"),
            meta: { title: "阶段管理" },
          },
          // 新增：分类管理（与顶层 /categories 复用同一组件）
          {
            path: "categories",
            name: "SettingsCategories",
            component: () => import("@/views/categories/CategoriesView.vue"),
            meta: { title: "分类管理" },
          },
          // 新增：格言管理（占位组件）
          {
            path: "mottos",
            name: "SettingsMottos",
            component: () => import("@/views/settings/MottoManagement.vue"),
            meta: { title: "格言管理" },
          },
        ],
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "NotFound",
    component: () => import("@/views/error/NotFoundView.vue"),
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

router.beforeEach(async (to, _from, next) => {
  const authStore = useAuthStore();

  // 需要认证的页面
  if (to.meta.requiresAuth !== false) {
    if (!authStore.isAuthenticated) {
      return next("/login");
    }
  }

  // 已登录用户访问登录/注册页,重定向到仪表盘
  if (
    authStore.isAuthenticated &&
    (to.name === "Login" || to.name === "Register")
  ) {
    return next("/dashboard");
  }

  next();
});

export default router;
