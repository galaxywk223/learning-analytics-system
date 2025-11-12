import { defineStore } from "pinia";
import { ref, computed } from "vue";
import dayjs from "dayjs";
import { chartsAPI } from "@/api/modules/charts";
import { stageAPI } from "@/api/modules/stage";
import { ElMessage } from "element-plus";

/**
 * 图表数据Store
 * 完全按照旧项目的逻辑实现
 */

export const useChartsStore = defineStore("charts", () => {
  // ========== 状态 ==========
  // 过滤器
  const viewType = ref("weekly"); // 'weekly' | 'daily'
  const stageId = ref("all");
  const activeTab = ref("trends"); // 'trends' | 'categories' | 'cattrend'

  // 数据状态
  const loading = ref(false);

  // 存储完整的后端返回数据（与旧项目一致）
  const rawChartData = ref({});

  // KPIs
  const kpis = ref({
    avg_daily_minutes: null,
    avg_daily_formatted: null,
    efficiency_star: null,
    weekly_trend: null,
  });

  // KPI: 近30天 Top3 子分类
  type TopSub = { label: string; parent?: string; hours: number; percent: number };
  const kpiTopSubs30d = ref<TopSub[]>([]);

  // 趋势图表数据（从rawChartData中提取）
  const trends = ref({
    weekly_duration_data: { labels: [], actuals: [], trends: [] },
    weekly_efficiency_data: { labels: [], actuals: [], trends: [] },
    daily_duration_data: { labels: [], actuals: [], trends: [] },
    daily_efficiency_data: { labels: [], actuals: [], trends: [] },
  });

  // 阶段注释
  const stageAnnotations = ref([]);

  // 分类数据
  const categoryData = ref({
    main: { labels: [], data: [] },
    drilldown: {},
  });
  const currentCategoryView = ref("main"); // 'main' | 'drilldown'
  const currentCategory = ref(""); // 当前下钻的分类名

  const categoryTrend = ref({
    labels: [] as string[],
    data: [] as number[],
    granularity: "weekly" as "weekly" | "daily",
  });
  const categoryTrendLoading = ref(false);
  const trendCategoryId = ref<number | null>(null);
  const trendSubcategoryId = ref<number | null>(null);

  // 阶段列表
  const stages = ref([]);

  // Category filter state
  const categoryRangeMode = ref<
    "all" | "stage" | "daily" | "weekly" | "monthly" | "custom"
  >("all");
  const categoryDatePoint = ref<string | null>(null); // 单点日期：日/周/月选择器
  const categoryCustomRange = ref<[string, string] | null>(null); // 自定义范围

  // ========== 计算属性 ==========
  const hasTrendsData = computed(
    () => (rawChartData.value as any).has_data === true
  );
  const hasCategoryData = computed(() => {
    return (
      (categoryData.value.main.labels &&
        categoryData.value.main.labels.length > 0) ||
      Object.keys(categoryData.value.drilldown || {}).length > 0
    );
  });

  // ========== 方法 ==========

  /**
   * 初始化阶段列表
   */
  async function initStages() {
    try {
      const res: any = await chartsAPI.getStages();
      if (res.success && res.data && res.data.stages) {
        stages.value = res.data.stages;
      } else {
        // 兼容直接返回数组的情况
        stages.value = Array.isArray(res) ? res : [];
      }
    } catch (e) {
      console.warn("获取阶段列表失败", e);
      stages.value = [];
    }
  }

  /**
   * 获取趋势数据（与旧项目 fetchDataAndRender 对应）
   */
  async function fetchTrends() {
    loading.value = true;
    try {
      const data: any = await chartsAPI.getOverview({
        view: viewType.value,
        stage_id: stageId.value,
      });

      if (!data || !data.has_data) {
        rawChartData.value = { has_data: false };
        kpis.value = {
          avg_daily_minutes: null,
          avg_daily_formatted: "--",
          efficiency_star: "--",
          weekly_trend: "--",
        };
        return;
      }

      // 保存原始数据
      rawChartData.value = data;

      // 更新KPIs
      if (data.kpis) {
        kpis.value = {
          avg_daily_minutes: data.kpis.avg_daily_minutes || 0,
          avg_daily_formatted: data.kpis.avg_daily_formatted || "--",
          efficiency_star: data.kpis.efficiency_star || "--",
          weekly_trend: data.kpis.weekly_trend || "--",
        };
      }

      // 更新趋势数据
      trends.value = {
        weekly_duration_data: data.weekly_duration_data || {
          labels: [],
          actuals: [],
          trends: [],
        },
        weekly_efficiency_data: data.weekly_efficiency_data || {
          labels: [],
          actuals: [],
          trends: [],
        },
        daily_duration_data: data.daily_duration_data || {
          labels: [],
          actuals: [],
          trends: [],
        },
        daily_efficiency_data: data.daily_efficiency_data || {
          labels: [],
          actuals: [],
          trends: [],
        },
      };

      // 更新阶段注释
      stageAnnotations.value = data.stage_annotations || [];
    } catch (error) {
      console.error("Error fetching trend data:", error);
      ElMessage.error("加载趋势图表数据失败");
      rawChartData.value = { has_data: false };
    } finally {
      loading.value = false;
    }
  }

  /**
   * 获取分类数据（与旧项目 fetchAndRenderAll 对应）
   */
  function buildCategoryRangeParams() {
    const mode = categoryRangeMode.value;
    let start: string | null = null;
    let end: string | null = null;

    if (mode === "daily" && categoryDatePoint.value) {
      const base = dayjs(categoryDatePoint.value);
      if (base.isValid()) {
        const formatted = base.format("YYYY-MM-DD");
        start = formatted;
        end = formatted;
      }
    } else if (mode === "weekly" && categoryDatePoint.value) {
      const base = dayjs(categoryDatePoint.value);
      if (base.isValid()) {
        const weekStart = base
          .startOf("day")
          .subtract((base.day() + 6) % 7, "day");
        start = weekStart.format("YYYY-MM-DD");
        end = weekStart.add(6, "day").format("YYYY-MM-DD");
      }
    } else if (mode === "monthly" && categoryDatePoint.value) {
      const base = dayjs(categoryDatePoint.value);
      if (base.isValid()) {
        start = base.startOf("month").format("YYYY-MM-DD");
        end = base.endOf("month").format("YYYY-MM-DD");
      }
    } else if (mode === "custom" && categoryCustomRange.value) {
      const [rangeStart, rangeEnd] = categoryCustomRange.value;
      if (rangeStart && rangeEnd) {
        const startDate = dayjs(rangeStart);
        const endDate = dayjs(rangeEnd);
        if (startDate.isValid() && endDate.isValid()) {
          start = startDate.format("YYYY-MM-DD");
          end = endDate.format("YYYY-MM-DD");
        }
      }
    }

    const params: Record<string, any> = {
      stage_id: stageId.value,
      range_mode: mode,
    };
    const requiresRange = ["daily", "weekly", "monthly", "custom"].includes(mode);
    if (start && end) {
      params.start_date = start;
      params.end_date = end;
    }

    return {
      params,
      valid: !requiresRange || (start && end),
    };
  }

  /**
   * 计算近30天 Top3 子分类（不影响分类页的筛选状态）
   */
  async function fetchTopSubsLast30d() {
    try {
      const today = dayjs();
      const start = today.subtract(29, "day").format("YYYY-MM-DD");
      const end = today.format("YYYY-MM-DD");
      const params: Record<string, any> = {
        range_mode: "custom",
        start_date: start,
        end_date: end,
      };
      const resp = await chartsAPI.getCategories(params);
      const payload = (resp as any).data || resp;
      const drill = (payload && (payload as any).drilldown) || {};
      const main = (payload && (payload as any).main) || { labels: [], data: [] };
      // 汇总所有子分类（名称 + 父类）
      const map = new Map<string, { label: string; parent?: string; hours: number }>();
      let total = 0;
      Object.keys(drill).forEach((catName) => {
        const ds = drill[catName] || { labels: [], data: [] };
        (ds.labels || []).forEach((subName: string, i: number) => {
          const hours = Number((ds.data || [])[i] || 0);
          total += hours;
          const key = `${catName}__${subName}`;
          const existed = map.get(key);
          if (existed) {
            existed.hours += hours;
          } else {
            map.set(key, { label: subName, parent: catName, hours });
          }
        });
      });

      // 若没有 drilldown 数据，尝试用主类作为“伪子类”（legacy 场景）
      if (map.size === 0 && Array.isArray(main?.labels)) {
        (main.labels as string[]).forEach((name: string, i: number) => {
          const hours = Number(main.data?.[i] || 0);
          total += hours;
          const label = `${name} (旧)`;
          const key = `legacy__${label}`;
          map.set(key, { label, parent: undefined, hours });
        });
      }

      const items = Array.from(map.values())
        .sort((a, b) => b.hours - a.hours)
        .slice(0, 3)
        .map((x) => ({
          ...x,
          percent: total > 0 ? Math.round((x.hours / total) * 100) : 0,
        }));
      kpiTopSubs30d.value = items;
    } catch (e) {
      // 静默失败，不影响页面其他数据
      kpiTopSubs30d.value = [];
    }
  }

  async function fetchCategories() {
    loading.value = true;
    try {
      const { params, valid } = buildCategoryRangeParams();
      if (!valid) {
        categoryData.value = {
          main: { labels: [], data: [] },
          drilldown: {},
        };
        currentCategoryView.value = "main";
        currentCategory.value = "";
        return;
      }

      console.log("[Charts Store] Fetching categories with params:", params);
      const response = await chartsAPI.getCategories(params);
      console.log("[Charts Store] Received category response:", response);

      const data = (response as any).data || response;
      console.log("[Charts Store] Extracted category data:", data);
      console.log("[Charts Store] Data main labels:", data?.main?.labels);
      console.log("[Charts Store] Data main data:", data?.main?.data);

      if (data && data.main) {
        categoryData.value = {
          main: {
            labels: data.main.labels || [],
            data: data.main.data || [],
          },
          drilldown: data.drilldown || {},
        };
        console.log("[Charts Store] Category data set:", categoryData.value);
        console.log("[Charts Store] hasCategoryData:", hasCategoryData.value);
        currentCategoryView.value = "main";
        currentCategory.value = "";
      } else {
        console.log("[Charts Store] No valid data received, setting empty structure");
        categoryData.value = {
          main: { labels: [], data: [] },
          drilldown: {},
        };
      }
    } catch (error) {
      console.error("Error fetching category data:", error);
      // 修正编码乱码
      ElMessage.error("加载分类图表数据失败");
    } finally {
      loading.value = false;
    }
  }

  async function fetchCategoryTrend() {
    // 支持“全部分类/全部子分类”场景：允许 category_id 与 subcategory_id 都为空

    const { params, valid } = buildCategoryRangeParams();
    if (!valid) {
      categoryTrend.value = { labels: [], data: [], granularity: "weekly" };
      return;
    }

    categoryTrendLoading.value = true;
    try {
      const query: Record<string, any> = {
        ...params,
        category_id: trendCategoryId.value,
        subcategory_id: trendSubcategoryId.value,
        granularity: 'daily',
      };
      console.log("[Charts Store] Fetching category trend with:", query);
      const response = await chartsAPI.getCategoryTrend(query);
      console.log("[Charts Store] Category trend raw response:", response);
      const payload = (response as any).data || response;
      console.log("[Charts Store] Category trend payload:", payload);
      // 注意：后端返回 { success, data: { labels, data, granularity, ... } }
      // 上一版错误地把 payload.data 直接当作 dataset，导致 dataset 变成纯数组
      // 这里应当把 dataset 设为 payload 本身
      const dataset = (payload && (payload as any).labels && (payload as any).data)
        ? (payload as any)
        : ((payload as any).data || {});
      console.log("[Charts Store] Category trend dataset:", dataset);
      categoryTrend.value = {
        labels: dataset.labels || [],
        data: dataset.data || [],
        granularity: (dataset.granularity as "weekly" | "daily") || "weekly",
      };
    } catch (error) {
      console.error("Error fetching category trend data:", error);
      ElMessage.error("获取分类趋势数据失败");
      categoryTrend.value = { labels: [], data: [], granularity: "weekly" };
    } finally {
      categoryTrendLoading.value = false;
    }
  }


  /**
   * 分类下钻
   */
  function drillCategory(categoryName) {
    if (
      currentCategoryView.value === "main" &&
      categoryData.value.drilldown[categoryName] &&
      categoryData.value.drilldown[categoryName].labels.length > 0
    ) {
      currentCategory.value = categoryName;
      currentCategoryView.value = "drilldown";
    }
  }

  /**
   * 返回上级分类
   */
  function backCategory() {
    currentCategoryView.value = "main";
    currentCategory.value = "";
  }

  /**
   * 刷新所有数据
   */
  async function refreshAll() {
    console.log(
      "[Charts Store] refreshAll called, activeTab:",
      activeTab.value
    );
    await fetchTrends();
    if (activeTab.value === "categories") {
      console.log(
        "[Charts Store] Active tab is categories, fetching category data..."
      );
      await fetchCategories();
    } else if (activeTab.value === "cattrend") {
      await fetchCategoryTrend();
    } else {
      console.log(
        "[Charts Store] Active tab is not categories, skipping category fetch"
      );
    }
    // 计算 Top3 子分类（近30天）
    await fetchTopSubsLast30d();
  }

  function setCategoryRangeMode(mode: typeof categoryRangeMode.value) {
    if (categoryRangeMode.value === mode) {
      return;
    }
    categoryRangeMode.value = mode;

    if (mode !== "custom") {
      categoryCustomRange.value = null;
    }
    categoryDatePoint.value = null;

    if (mode === "all" || mode === "stage") {
      fetchCategories();
      fetchCategoryTrend();
    }
  }

  function setCategoryDatePoint(value: string | null) {
    categoryDatePoint.value = value;
    if (
      value &&
      ["daily", "weekly", "monthly"].includes(categoryRangeMode.value)
    ) {
      fetchCategories();
      fetchCategoryTrend();
    }
  }

  function setCategoryCustomRange(range: [string, string] | null) {
    categoryCustomRange.value = range;
    if (
      categoryRangeMode.value === "custom" &&
      range &&
      range[0] &&
      range[1]
    ) {
      fetchCategories();
      fetchCategoryTrend();
    }
  }

  /**
   * 设置视图类型（周/日）
   */
  function setViewType(type) {
    if (viewType.value !== type) {
      viewType.value = type;
      // 视图切换不需要重新获取数据，只需要在组件中切换显示的数据
    }
  }

  /**
   * 设置阶段过滤
   */
  function setStage(id) {
    if (stageId.value !== id) {
      stageId.value = id;
      refreshAll();
      fetchCategoryTrend();
    }
  }

  /**
   * 设置活动标签页
   */
  function setActiveTab(tab) {
    console.log("[Charts Store] setActiveTab called with:", tab);
    activeTab.value = tab;
    if (tab === "categories" && categoryData.value.main.labels.length === 0) {
      console.log(
        "[Charts Store] Switching to categories tab with no data, fetching..."
      );
      fetchCategories();
    } else if (tab === "categories") {
      console.log(
        "[Charts Store] Switching to categories tab, current labels:",
        categoryData.value.main.labels
      );
    } else if (tab === "cattrend") {
      fetchCategoryTrend();
    }
  }

  function setTrendCategory(id: number | null) {
    trendCategoryId.value = id;
    if (!id) {
      trendSubcategoryId.value = null;
    }
    if (activeTab.value === "cattrend") {
      fetchCategoryTrend();
    }
  }

  function setTrendSubcategory(id: number | null) {
    trendSubcategoryId.value = id;
    if (activeTab.value === "cattrend") {
      fetchCategoryTrend();
    }
  }

  // KPI 格式化辅助（与旧项目 blueprints 中格式保持一致）
  function getFormattedAvgDailyDuration() {
    const minutes = kpis.value.avg_daily_minutes || 0;
    const h = Math.floor(minutes / 60);
    const m = Math.floor(minutes % 60);
    return `${h}小时 ${m}分钟`;
  }

  return {
    // 状态
    viewType,
    stageId,
    activeTab,
    loading,
    rawChartData,
    kpis,
    kpiTopSubs30d,
    trends,
    stageAnnotations,
    categoryData,
    categoryTrend,
    categoryTrendLoading,
    trendCategoryId,
    trendSubcategoryId,
    currentCategoryView,
    currentCategory,
    categoryRangeMode,
    categoryDatePoint,
    categoryCustomRange,
    stages,
    // 计算属性
    hasTrendsData,
    hasCategoryData,
    // 方法
    initStages,
    fetchTrends,
    fetchTopSubsLast30d,
    fetchCategories,
    fetchCategoryTrend,
    drillCategory,
    backCategory,
    refreshAll,
    setCategoryRangeMode,
    setCategoryDatePoint,
    setCategoryCustomRange,
    setViewType,
    setStage,
    setActiveTab,
    setTrendCategory,
    setTrendSubcategory,
    getFormattedAvgDailyDuration,
  };
});
