import { defineStore } from "pinia";
import { ref, computed } from "vue";
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
  const activeTab = ref("trends"); // 'trends' | 'categories' | 'wordcloud'

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

  // 词云
  const wordcloudImageUrl = ref("");
  const wordcloudOptions = ref({ masks: [], palettes: [] });
  const currentMask = ref("random");
  const currentPalette = ref("default");
  const wordcloudLoading = ref(false);
  const wordcloudMessage = ref("");

  // 阶段列表
  const stages = ref([]);

  // ========== 计算属性 ==========
  const hasTrendsData = computed(() => rawChartData.value.has_data === true);
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
      const res = await chartsAPI.getStages();
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
      const data = await chartsAPI.getOverview();

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
  async function fetchCategories() {
    try {
      const data = await chartsAPI.getCategories({ stage_id: stageId.value });

      if (data) {
        categoryData.value = data;
        // 重置视图状态
        currentCategoryView.value = "main";
        currentCategory.value = "";
      } else {
        categoryData.value = {
          main: { labels: [], data: [] },
          drilldown: {},
        };
      }
    } catch (error) {
      console.error("Error fetching category data:", error);
      ElMessage.error("加载分类图表数据失败");
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
   * 获取词云（与旧项目 loadWordCloud 对应）
   */
  async function fetchWordcloud(params = {}) {
    wordcloudLoading.value = true;
    try {
      const timestamp = new Date().getTime();
      const response = await chartsAPI.getWordcloud({
        stage_id: stageId.value,
        mask: params.mask || currentMask.value,
        palette: params.palette || currentPalette.value,
        t: timestamp,
      });
      // 204 无内容
      if (response.status === 204) {
        wordcloudMessage.value =
          "在当前筛选的范围内没有找到任何笔记内容来生成词云。";
        if (wordcloudImageUrl.value)
          URL.revokeObjectURL(wordcloudImageUrl.value);
        wordcloudImageUrl.value = "";
        return;
      }
      const blob = response.data instanceof Blob ? response.data : response;
      if (wordcloudImageUrl.value) {
        URL.revokeObjectURL(wordcloudImageUrl.value);
      }
      if (blob && blob.size > 0) {
        wordcloudImageUrl.value = URL.createObjectURL(blob);
        wordcloudMessage.value = "";
      } else {
        wordcloudImageUrl.value = "";
        wordcloudMessage.value = "暂无词云数据，请调整筛选后重试。";
      }
    } catch (error) {
      console.error("Error loading wordcloud:", error);
      if (wordcloudImageUrl.value) URL.revokeObjectURL(wordcloudImageUrl.value);
      wordcloudImageUrl.value = "";
      wordcloudMessage.value = "加载词云时发生网络错误，请稍后重试。";
    } finally {
      wordcloudLoading.value = false;
    }
  }

  /**
   * 获取词云选项
   */
  async function fetchWordcloudOptions() {
    try {
      const res = await chartsAPI.getWordcloudOptions();
      if (res && res.success) {
        wordcloudOptions.value = {
          masks: res.masks || [],
          palettes: res.palettes || [],
        };
      }
    } catch (e) {
      console.warn("获取词云选项失败", e);
    }
  }

  /**
   * 刷新所有数据
   */
  async function refreshAll() {
    await fetchTrends();
    if (activeTab.value === "categories") {
      await fetchCategories();
    } else if (activeTab.value === "wordcloud") {
      await fetchWordcloud();
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
    }
  }

  /**
   * 设置活动标签页
   */
  function setActiveTab(tab) {
    activeTab.value = tab;
    if (tab === "categories" && categoryData.value.main.labels.length === 0) {
      fetchCategories();
    } else if (tab === "wordcloud" && !wordcloudImageUrl.value) {
      fetchWordcloud();
    }
  }

  /**
   * 设置词云遮罩
   */
  function setWordcloudMask(mask) {
    currentMask.value = mask;
    fetchWordcloud();
  }

  /**
   * 设置词云调色板
   */
  function setWordcloudPalette(palette) {
    currentPalette.value = palette;
    fetchWordcloud();
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
    trends,
    stageAnnotations,
    categoryData,
    currentCategoryView,
    currentCategory,
    wordcloudImageUrl,
    wordcloudOptions,
    currentMask,
    currentPalette,
    wordcloudLoading,
    wordcloudMessage,
    stages,
    // 计算属性
    hasTrendsData,
    hasCategoryData,
    // 方法
    initStages,
    fetchTrends,
    fetchCategories,
    drillCategory,
    backCategory,
    fetchWordcloud,
    fetchWordcloudOptions,
    refreshAll,
    setViewType,
    setStage,
    setActiveTab,
    setWordcloudMask,
    setWordcloudPalette,
    getFormattedAvgDailyDuration,
  };
});
