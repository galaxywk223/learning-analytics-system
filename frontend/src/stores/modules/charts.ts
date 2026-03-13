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
  let refreshAllPromise: Promise<void> | null = null;
  let forecastPollingTimer: ReturnType<typeof setTimeout> | null = null;
  let forecastPollingToken = 0;
  const OVERVIEW_CACHE_PREFIX = "charts:overview:";
  const TOP_SUMMARY_CACHE_PREFIX = "charts:top-summary:";
  const UI_STATE_STORAGE_KEY = "charts:ui-state";

  const defaultForecast = () => ({
    labels: [],
    prediction: [],
    lower: [],
    upper: [],
    model_name: null,
    history_points: 0,
    horizon: 0,
    trained_on: "all_history",
    confidence_level: 0.8,
    accuracy_threshold: 0.4,
    selection_strategy: "lowest_wape_then_rmse",
    validation_wape: null,
    validation_rmse: null,
    baseline_wape: null,
    baseline_rmse: null,
    model_candidates: [],
    available: false,
    reason: "",
    status: "unavailable",
  });

  const defaultTrendDataset = () => ({
    labels: [],
    actuals: [],
    trends: [],
    ongoing: false,
    ongoing_label: null,
    ongoing_value: null,
    forecast: defaultForecast(),
  });

  // ========== 状态 ==========
  // 过滤器
  const viewType = ref("weekly"); // 'weekly' | 'daily'
  const stageId = ref("all");
  const activeTab = ref("overview"); // 'overview' | 'trends' | 'categories' | 'cattrend'
  const metricMode = ref<"duration" | "efficiency">("duration"); // 新增：指标模式

  // 数据状态
  const loading = ref(false);
  const trendsLoading = ref(false);
  const trendsError = ref("");

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
  type TopSub = {
    label: string;
    parent?: string;
    hours: number;
    percent: number;
  };
  const kpiTopSubs30d = ref<TopSub[]>([]);
  const kpiTopSubsEfficiency30d = ref<TopSub[]>([]); // 效率 TOP3
  const topSummaryLoading = ref(true);

  // 趋势图表数据（从rawChartData中提取）
  const trends = ref({
    weekly_duration_data: defaultTrendDataset(),
    weekly_efficiency_data: defaultTrendDataset(),
    daily_duration_data: defaultTrendDataset(),
    daily_efficiency_data: defaultTrendDataset(),
  });
  const forecastStatus = ref({
    state: "idle",
    signature: null as string | null,
    message: "",
    updated_at: null as string | null,
    trained_for_date: null as string | null,
  });
  const forecastRetraining = ref(false);

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
    () => (rawChartData.value as any).has_data === true,
  );
  const hasCategoryData = computed(() => {
    return (
      (categoryData.value.main.labels &&
        categoryData.value.main.labels.length > 0) ||
      Object.keys(categoryData.value.drilldown || {}).length > 0
    );
  });

  function getOverviewCacheKey() {
    return `${OVERVIEW_CACHE_PREFIX}${stageId.value}`;
  }

  function getTopSummaryCacheKey() {
    return `${TOP_SUMMARY_CACHE_PREFIX}${dayjs().format("YYYY-MM-DD")}`;
  }

  function persistUiState() {
    if (typeof window === "undefined") {
      return;
    }
    try {
      sessionStorage.setItem(
        UI_STATE_STORAGE_KEY,
        JSON.stringify({
          activeTab: activeTab.value,
          viewType: viewType.value,
          stageId: stageId.value,
          metricMode: metricMode.value,
        }),
      );
    } catch (error) {
      console.warn("持久化图表 UI 状态失败", error);
    }
  }

  function persistTopSummaryCache() {
    if (typeof window === "undefined") {
      return;
    }
    if (
      kpiTopSubs30d.value.length === 0 &&
      kpiTopSubsEfficiency30d.value.length === 0
    ) {
      return;
    }
    try {
      sessionStorage.setItem(
        getTopSummaryCacheKey(),
        JSON.stringify({
          duration: kpiTopSubs30d.value,
          efficiency: kpiTopSubsEfficiency30d.value,
        }),
      );
    } catch (error) {
      console.warn("持久化 TOP3 缓存失败", error);
    }
  }

  function hydrateTopSummaryCache() {
    if (typeof window === "undefined") {
      return false;
    }
    try {
      const raw = sessionStorage.getItem(getTopSummaryCacheKey());
      if (!raw) return false;
      const parsed = JSON.parse(raw);
      kpiTopSubs30d.value = Array.isArray(parsed?.duration) ? parsed.duration : [];
      kpiTopSubsEfficiency30d.value = Array.isArray(parsed?.efficiency)
        ? parsed.efficiency
        : [];
      return (
        kpiTopSubs30d.value.length > 0 || kpiTopSubsEfficiency30d.value.length > 0
      );
    } catch (error) {
      console.warn("恢复 TOP3 缓存失败", error);
      return false;
    }
  }

  function hydrateUiState() {
    if (typeof window === "undefined") {
      return;
    }
    try {
      const raw = sessionStorage.getItem(UI_STATE_STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      if (parsed?.activeTab) {
        activeTab.value = parsed.activeTab;
      }
      if (parsed?.viewType === "daily" || parsed?.viewType === "weekly") {
        viewType.value = parsed.viewType;
      }
      if (parsed?.stageId != null) {
        stageId.value = parsed.stageId;
      }
      if (
        parsed?.metricMode === "duration" ||
        parsed?.metricMode === "efficiency"
      ) {
        metricMode.value = parsed.metricMode;
      }
    } catch (error) {
      console.warn("恢复图表 UI 状态失败", error);
    }
  }

  function persistOverviewCache(payload: any) {
    if (typeof window === "undefined" || !payload?.has_data) {
      return;
    }
    try {
      sessionStorage.setItem(
        getOverviewCacheKey(),
        JSON.stringify({
          cached_at: dayjs().toISOString(),
          payload,
        }),
      );
    } catch (error) {
      console.warn("持久化趋势缓存失败", error);
    }
  }

  function readOverviewCache() {
    if (typeof window === "undefined") {
      return null;
    }
    try {
      const raw = sessionStorage.getItem(getOverviewCacheKey());
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const payload = parsed?.payload;
      if (!payload?.has_data) return null;
      return payload;
    } catch (error) {
      console.warn("读取趋势缓存失败", error);
      return null;
    }
  }

  function applyTrendPayload(data: any) {
    rawChartData.value = data;

    if (data.kpis) {
      kpis.value = {
        avg_daily_minutes: data.kpis.avg_daily_minutes || 0,
        avg_daily_formatted: data.kpis.avg_daily_formatted || "--",
        efficiency_star: data.kpis.efficiency_star || "--",
        weekly_trend: data.kpis.weekly_trend || "--",
      };
    }

    trends.value = {
      weekly_duration_data: {
        ...defaultTrendDataset(),
        ...(data.weekly_duration_data || {}),
        forecast: {
          ...defaultForecast(),
          ...(data.weekly_duration_data?.forecast || {}),
        },
      },
      weekly_efficiency_data: {
        ...defaultTrendDataset(),
        ...(data.weekly_efficiency_data || {}),
        forecast: {
          ...defaultForecast(),
          ...(data.weekly_efficiency_data?.forecast || {}),
        },
      },
      daily_duration_data: {
        ...defaultTrendDataset(),
        ...(data.daily_duration_data || {}),
        forecast: {
          ...defaultForecast(),
          ...(data.daily_duration_data?.forecast || {}),
        },
      },
      daily_efficiency_data: {
        ...defaultTrendDataset(),
        ...(data.daily_efficiency_data || {}),
        forecast: {
          ...defaultForecast(),
          ...(data.daily_efficiency_data?.forecast || {}),
        },
      },
    };

    stageAnnotations.value = data.stage_annotations || [];
    forecastStatus.value = {
      state: data.forecast_status?.state || "idle",
      signature: data.forecast_status?.signature || null,
      message: data.forecast_status?.message || "",
      updated_at: data.forecast_status?.updated_at || null,
      trained_for_date: data.forecast_status?.trained_for_date || null,
    };
  }

  hydrateUiState();
  topSummaryLoading.value = !hydrateTopSummaryCache();

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
    trendsError.value = "";
    stopForecastPolling();
    const cachedPayload = readOverviewCache();
    if (cachedPayload) {
      applyTrendPayload(cachedPayload);
      trendsLoading.value = false;
    } else {
      trendsLoading.value = true;
    }
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
        forecastStatus.value = {
          state: "unavailable",
          signature: null,
          message: "",
          updated_at: null,
          trained_for_date: null,
        };
        return;
      }

      applyTrendPayload(data);
      persistOverviewCache(data);

      if (forecastStatus.value.state === "pending") {
        startForecastPolling();
      }
    } catch (error) {
      console.error("Error fetching trend data:", error);
      const errorMessage =
        (error as any)?.response?.data?.message ||
        (error as any)?.message ||
        (error as any)?.code ||
        "加载趋势图表数据失败";
      trendsError.value = errorMessage;
      ElMessage.error("加载趋势图表数据失败");
      rawChartData.value = { has_data: false };
      forecastStatus.value = {
        state: "error",
        signature: null,
        message: errorMessage,
        updated_at: null,
        trained_for_date: null,
      };
    } finally {
      trendsLoading.value = false;
    }
  }

  function mergeForecastBundle(forecasts: Record<string, any> | null | undefined) {
    if (!forecasts) return;
    if ((rawChartData.value as any)?.has_data) {
      rawChartData.value = {
        ...(rawChartData.value as any),
        weekly_duration_data: {
          ...(rawChartData.value as any).weekly_duration_data,
          forecast: {
            ...defaultForecast(),
            ...(forecasts.weekly_duration_data || {}),
          },
        },
        weekly_efficiency_data: {
          ...(rawChartData.value as any).weekly_efficiency_data,
          forecast: {
            ...defaultForecast(),
            ...(forecasts.weekly_efficiency_data || {}),
          },
        },
        daily_duration_data: {
          ...(rawChartData.value as any).daily_duration_data,
          forecast: {
            ...defaultForecast(),
            ...(forecasts.daily_duration_data || {}),
          },
        },
        daily_efficiency_data: {
          ...(rawChartData.value as any).daily_efficiency_data,
          forecast: {
            ...defaultForecast(),
            ...(forecasts.daily_efficiency_data || {}),
          },
        },
      };
    }
    trends.value = {
      weekly_duration_data: {
        ...trends.value.weekly_duration_data,
        forecast: {
          ...defaultForecast(),
          ...(forecasts.weekly_duration_data || {}),
        },
      },
      weekly_efficiency_data: {
        ...trends.value.weekly_efficiency_data,
        forecast: {
          ...defaultForecast(),
          ...(forecasts.weekly_efficiency_data || {}),
        },
      },
      daily_duration_data: {
        ...trends.value.daily_duration_data,
        forecast: {
          ...defaultForecast(),
          ...(forecasts.daily_duration_data || {}),
        },
      },
      daily_efficiency_data: {
        ...trends.value.daily_efficiency_data,
        forecast: {
          ...defaultForecast(),
          ...(forecasts.daily_efficiency_data || {}),
        },
      },
    };
    if ((rawChartData.value as any)?.has_data) {
      rawChartData.value = {
        ...(rawChartData.value as any),
        forecast_status: {
          ...(rawChartData.value as any).forecast_status,
          ...forecastStatus.value,
        },
      };
      persistOverviewCache({
        ...(rawChartData.value as any),
      });
    }
  }

  function stopForecastPolling() {
    forecastPollingToken += 1;
    if (forecastPollingTimer) {
      clearTimeout(forecastPollingTimer);
      forecastPollingTimer = null;
    }
  }

  function scheduleForecastPolling(runToken: number, attempt: number) {
    forecastPollingTimer = setTimeout(() => {
      pollForecastStatus(runToken, attempt).catch((error) => {
        console.warn("轮询预测状态失败", error);
      });
    }, 2500);
  }

  async function pollForecastStatus(runToken: number, attempt = 0) {
    if (runToken !== forecastPollingToken) {
      return;
    }
    const response: any = await chartsAPI.getOverviewForecast();
    const payload = response?.data || response;
    forecastStatus.value = {
      state: payload?.status || "idle",
      signature: payload?.signature || forecastStatus.value.signature,
      message: payload?.message || "",
      updated_at: payload?.updated_at || null,
      trained_for_date: payload?.trained_for_date || null,
    };
    mergeForecastBundle(payload?.forecasts);

    if (payload?.status === "ready" || payload?.status === "error") {
      forecastPollingTimer = null;
      return;
    }

    if (attempt >= 60) {
      forecastPollingTimer = null;
      forecastStatus.value = {
        ...forecastStatus.value,
        state: "error",
        message: "预测生成耗时过长，请稍后手动刷新",
      };
      return;
    }

    scheduleForecastPolling(runToken, attempt + 1);
  }

  function startForecastPolling() {
    stopForecastPolling();
    const runToken = forecastPollingToken;
    scheduleForecastPolling(runToken, 0);
  }

  async function retrainForecasts() {
    if (forecastRetraining.value) return;
    forecastRetraining.value = true;
    stopForecastPolling();
    try {
      const response: any = await chartsAPI.retrainOverviewForecast();
      const payload = response?.data || response;
      forecastStatus.value = {
        state: payload?.status || "pending",
        signature: payload?.signature || forecastStatus.value.signature,
        message: payload?.message || "已开始重新训练预测模型",
        updated_at: payload?.updated_at || null,
        trained_for_date: payload?.trained_for_date || null,
      };
      mergeForecastBundle({
        weekly_duration_data: { ...defaultForecast(), status: "pending", reason: "预测计算中，请稍后刷新" },
        weekly_efficiency_data: { ...defaultForecast(), status: "pending", reason: "预测计算中，请稍后刷新" },
        daily_duration_data: { ...defaultForecast(), status: "pending", reason: "预测计算中，请稍后刷新" },
        daily_efficiency_data: { ...defaultForecast(), status: "pending", reason: "预测计算中，请稍后刷新" },
      });
      startForecastPolling();
      ElMessage.success("已开始重新训练预测模型");
    } catch (error) {
      console.error("Error retraining forecasts:", error);
      ElMessage.error("重新训练预测失败");
    } finally {
      forecastRetraining.value = false;
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
    const requiresRange = ["daily", "weekly", "monthly", "custom"].includes(
      mode,
    );
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
      const main = (payload && (payload as any).main) || {
        labels: [],
        data: [],
      };
      // 汇总所有子分类（名称 + 父类）
      const map = new Map<
        string,
        { label: string; parent?: string; hours: number }
      >();
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
      if (items.length > 0) {
        kpiTopSubs30d.value = items;
        persistTopSummaryCache();
      }
    } catch (e) {
      console.warn("获取时长 TOP3 失败", e);
    }
  }

  /**
   * 计算近30天效率 Top3 子分类
   */
  async function fetchTopSubsEfficiencyLast30d() {
    try {
      const today = dayjs();
      const start = today.subtract(29, "day").format("YYYY-MM-DD");
      const end = today.format("YYYY-MM-DD");
      const params: Record<string, any> = {
        range_mode: "custom",
        start_date: start,
        end_date: end,
        metric_mode: "efficiency",
      };
      const resp = await chartsAPI.getCategories(params);
      const payload = (resp as any).data || resp;
      const drill = (payload && (payload as any).drilldown) || {};
      const main = (payload && (payload as any).main) || {
        labels: [],
        data: [],
      };
      // 汇总所有子分类（名称 + 父类）的效率
      const map = new Map<
        string,
        { label: string; parent?: string; hours: number; count: number }
      >();
      let total = 0;
      Object.keys(drill).forEach((catName) => {
        const ds = drill[catName] || { labels: [], data: [] };
        (ds.labels || []).forEach((subName: string, i: number) => {
          const efficiency = Number((ds.data || [])[i] || 0);
          total += efficiency;
          const key = `${catName}__${subName}`;
          const existed = map.get(key);
          if (existed) {
            existed.hours += efficiency;
            existed.count += 1;
          } else {
            map.set(key, {
              label: subName,
              parent: catName,
              hours: efficiency,
              count: 1,
            });
          }
        });
      });

      // 若没有 drilldown 数据，尝试用主类作为"伪子类"（legacy 场景）
      if (map.size === 0 && Array.isArray(main?.labels)) {
        (main.labels as string[]).forEach((name: string, i: number) => {
          const efficiency = Number(main.data?.[i] || 0);
          total += efficiency;
          const label = `${name} (旧)`;
          const key = `legacy__${label}`;
          map.set(key, {
            label,
            parent: undefined,
            hours: efficiency,
            count: 1,
          });
        });
      }

      const items = Array.from(map.values())
        .sort((a, b) => b.hours - a.hours)
        .slice(0, 3)
        .map((x) => ({
          ...x,
          percent: total > 0 ? Math.round((x.hours / total) * 100) : 0,
        }));
      if (items.length > 0) {
        kpiTopSubsEfficiency30d.value = items;
        persistTopSummaryCache();
      }
    } catch (e) {
      console.warn("获取效率 TOP3 失败", e);
    }
  }

  async function refreshTopSummaries() {
    const hasTopSummaryCache = hydrateTopSummaryCache();
    topSummaryLoading.value = !hasTopSummaryCache;
    try {
      await Promise.all([
        fetchTopSubsLast30d(),
        fetchTopSubsEfficiencyLast30d(),
      ]);
    } finally {
      topSummaryLoading.value = false;
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

      // 添加 metric_mode 参数
      params.metric_mode = metricMode.value;

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
        console.log(
          "[Charts Store] No valid data received, setting empty structure",
        );
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
        granularity: "daily",
        metric_mode: metricMode.value, // 添加 metric_mode 参数
      };
      console.log("[Charts Store] Fetching category trend with:", query);
      const response = await chartsAPI.getCategoryTrend(query);
      console.log("[Charts Store] Category trend raw response:", response);
      const payload = (response as any).data || response;
      console.log("[Charts Store] Category trend payload:", payload);
      // 注意：后端返回 { success, data: { labels, data, granularity, ... } }
      // 上一版错误地把 payload.data 直接当作 dataset，导致 dataset 变成纯数组
      // 这里应当把 dataset 设为 payload 本身
      const dataset =
        payload && (payload as any).labels && (payload as any).data
          ? (payload as any)
          : (payload as any).data || {};
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
    if (refreshAllPromise) {
      return refreshAllPromise;
    }

    console.log(
      "[Charts Store] refreshAll called, activeTab:",
      activeTab.value,
    );
    refreshAllPromise = (async () => {
      const topSummaryPromise = refreshTopSummaries();
      await fetchTrends();
      if (activeTab.value === "categories") {
        console.log(
          "[Charts Store] Active tab is categories, fetching category data...",
        );
        await fetchCategories();
      } else if (activeTab.value === "cattrend") {
        await fetchCategoryTrend();
      } else {
        console.log(
          "[Charts Store] Active tab is not categories, skipping category fetch",
        );
      }
      await topSummaryPromise;
    })();

    try {
      await refreshAllPromise;
    } finally {
      refreshAllPromise = null;
    }
  }

  function setCategoryRangeMode(mode: typeof categoryRangeMode.value) {
    if (categoryRangeMode.value === mode) {
      return;
    }
    categoryRangeMode.value = mode;
    persistUiState();

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
    persistUiState();
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
    persistUiState();
    if (categoryRangeMode.value === "custom" && range && range[0] && range[1]) {
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
      persistUiState();
      // 视图切换不需要重新获取数据，只需要在组件中切换显示的数据
    }
  }

  /**
   * 设置阶段过滤
   */
  function setStage(id) {
    if (stageId.value !== id) {
      stageId.value = id;
      persistUiState();
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
    persistUiState();
    if (tab === "categories" && categoryData.value.main.labels.length === 0) {
      console.log(
        "[Charts Store] Switching to categories tab with no data, fetching...",
      );
      fetchCategories();
    } else if (tab === "categories") {
      console.log(
        "[Charts Store] Switching to categories tab, current labels:",
        categoryData.value.main.labels,
      );
    } else if (tab === "cattrend") {
      fetchCategoryTrend();
    }
  }

  /**
   * 设置指标模式
   */
  function setMetricMode(mode: "duration" | "efficiency") {
    if (metricMode.value !== mode) {
      metricMode.value = mode;
      persistUiState();
      // 切换模式时重新加载数据
      if (activeTab.value === "categories") {
        fetchCategories();
      } else if (activeTab.value === "cattrend") {
        fetchCategoryTrend();
      }
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
    metricMode,
    loading,
    trendsLoading,
    trendsError,
    rawChartData,
    kpis,
    kpiTopSubs30d,
    kpiTopSubsEfficiency30d,
    topSummaryLoading,
    trends,
    forecastStatus,
    forecastRetraining,
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
    retrainForecasts,
    fetchTopSubsLast30d,
    fetchTopSubsEfficiencyLast30d,
    refreshTopSummaries,
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
    setMetricMode,
    setTrendCategory,
    setTrendSubcategory,
    getFormattedAvgDailyDuration,
  };
});
