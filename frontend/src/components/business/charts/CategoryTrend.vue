<template>
  <div class="category-trend-card">
    <div class="card-header">
      <div class="header-title">
        <h3>分类趋势</h3>
        <p v-if="trendMeta">{{ trendMeta }}</p>
      </div>
      <div class="selector-group">
        <div class="selector-wrapper">
          <el-select
            v-model="selectedCategory"
            placeholder="选择分类"
            filterable
            clearable
            :disabled="categoryStore.loading"
            class="ios-select"
            @change="handleCategoryChange"
          >
            <el-option
              v-for="opt in categoryOptions"
              :key="`${opt.label}:${String(opt.value)}`"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
        <div class="selector-wrapper">
          <el-select
            v-model="selectedSubcategory"
            placeholder="全部子分类"
            :disabled="!selectedCategory"
            clearable
            filterable
            class="ios-select"
            @change="handleSubChange"
          >
            <el-option
              v-for="opt in subOptions"
              :key="`${opt.label}:${String(opt.value)}`"
              :label="opt.label"
              :value="opt.value"
            />
          </el-select>
        </div>
      </div>
    </div>

    <div v-loading="trendLoading" class="chart-container">
      <div
        v-if="!trendSeries.labels.length && !trendLoading"
        class="empty-state"
      >
        <div class="empty-icon">📊</div>
        <p>当前筛选范围内没有记录</p>
      </div>
      <v-chart
        v-else-if="isActiveTab"
        ref="chartRef"
        class="chart"
        :option="option"
        autoresize
        :update-options="{
          replaceMerge: ['series', 'xAxis', 'yAxis', 'grid', 'dataZoom'],
        }"
        @datazoom="handleDataZoom"
        @finished="handleChartFinished"
      />
      <div v-else class="chart-placeholder">
        <p>切换到“分类趋势”即可查看图表。</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick, ref, onUnmounted } from "vue";
import { use, graphic } from "echarts/core";
import { BarChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";
import { storeToRefs } from "pinia";
import { useCategoryStore } from "@/stores/category";
import { useChartsStore } from "@/stores/modules/charts";

use([
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
]);

const categoryStore = useCategoryStore();
const chartsStore = useChartsStore();

const {
  categoryTrend,
  categoryTrendLoading,
  trendCategoryId,
  trendSubcategoryId,
  activeTab,
  metricMode,
} = storeToRefs(chartsStore);

// 追加“全部分类”与“全部子分类”选项
const categoryOptions = computed(() => [
  { label: "全部分类", value: null },
  ...categoryStore.categoryOptions,
]);
const subOptions = computed(() => {
  if (!trendCategoryId.value) return [];
  return [
    { label: "全部子分类", value: null },
    ...categoryStore.getSubCategories(trendCategoryId.value),
  ];
});

const selectedCategory = computed({
  get: () => trendCategoryId.value,
  set: (val) => chartsStore.setTrendCategory(val ?? null),
});

const selectedSubcategory = computed({
  get: () => trendSubcategoryId.value,
  set: (val) => chartsStore.setTrendSubcategory(val ?? null),
});

const trendSeries = computed(() => categoryTrend.value);
const trendLoading = computed(() => categoryTrendLoading.value);
const isActiveTab = computed(() => activeTab.value === "cattrend");
const chartRef = ref<InstanceType<typeof VChart> | null>(null);
const zoomRange = ref<{ start: number | null; end: number | null }>({
  start: null,
  end: null,
});
const dynamicBarWidth = ref(22);

const trendMeta = computed(() => {
  if (!trendSeries.value.labels.length) return "";
  return trendSeries.value.granularity === "daily" ? "按日统计" : "按周统计";
});

function handleCategoryChange(val: number | null) {
  selectedCategory.value = val ?? null;
  if (!val) {
    selectedSubcategory.value = null;
  }
}

function handleSubChange(val: number | null) {
  selectedSubcategory.value = val ?? null;
}

function calcBarWidth(visiblePct?: number) {
  const labels = trendSeries.value.labels || [];
  const total = labels.length || 1;
  const pctRaw =
    typeof visiblePct === "number"
      ? visiblePct
      : zoomRange.value.end != null && zoomRange.value.start != null
        ? zoomRange.value.end - zoomRange.value.start
        : 100;
  const pct = Math.max(1, Math.min(100, pctRaw));
  const visible = Math.max(1, Math.round((total * pct) / 100));
  const container = (chartRef.value as any)?.$el as HTMLElement | undefined;
  const width = (container?.clientWidth ?? 720) - 56; // 估算左右留白
  const per = width / visible; // 每个类目区域宽
  const computedWidth = Math.floor(per * 0.6); // 取 60% 作为柱宽
  dynamicBarWidth.value = Math.max(8, Math.min(42, computedWidth));
}

function handleDataZoom(e: any) {
  if (e?.start !== undefined && e?.end !== undefined) {
    zoomRange.value.start = Math.max(0, Math.min(100, e.start));
    zoomRange.value.end = Math.max(0, Math.min(100, e.end));
  } else if (Array.isArray(e?.batch) && e.batch[0]) {
    const b = e.batch[0];
    if (b.start !== undefined)
      zoomRange.value.start = Math.max(0, Math.min(100, b.start));
    if (b.end !== undefined)
      zoomRange.value.end = Math.max(0, Math.min(100, b.end));
  }
  if (zoomRange.value.start != null && zoomRange.value.end != null) {
    calcBarWidth(zoomRange.value.end - zoomRange.value.start);
  } else {
    calcBarWidth();
  }
}

function handleChartFinished() {
  // 图表首次渲染或重新渲染完成后，按最终尺寸再计算一次柱宽
  if (zoomRange.value.start == null || zoomRange.value.end == null) {
    // 如果还没有初始化缩放范围，用与 option 相同的规则初始化一次
    const len = trendSeries.value.labels?.length || 0;
    if (len > 0) {
      zoomRange.value.start = 0;
      zoomRange.value.end = 100;
      calcBarWidth(100);
      return;
    }
  }
  calcBarWidth();
}

const option = computed(() => {
  const labels = trendSeries.value.labels || [];
  const values = (trendSeries.value.data || []).map((v) =>
    Number.isFinite(Number(v)) ? Number(v) : 0,
  );
  const enableZoom = labels.length > 14;
  const initialStart = 0; // 默认全区间
  const start =
    zoomRange.value.start !== null && zoomRange.value.start !== undefined
      ? zoomRange.value.start
      : initialStart;
  const end =
    zoomRange.value.end !== null && zoomRange.value.end !== undefined
      ? zoomRange.value.end
      : 100;
  const rotate = labels.length > 24 ? 45 : labels.length > 14 ? 30 : 0;
  const barWidth = dynamicBarWidth.value;

  const isEfficiency = metricMode.value === "efficiency";
  const yAxisName = isEfficiency ? "效率指数" : "时长 (h)";
  const tooltipUnit = isEfficiency ? "效率" : "小时";

  return {
    color: ["#5856D6"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      backgroundColor: "rgba(255, 255, 255, 0.95)",
      borderColor: "rgba(0, 0, 0, 0.05)",
      textStyle: { color: "#1c1c1e" },
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        return `<div style="font-weight:600;margin-bottom:4px">${item.name}</div>
                <div style="color:#5856D6">${Number(item.value || 0).toFixed(2)} ${tooltipUnit}</div>`;
      },
      confine: true,
      extraCssText:
        "box-shadow: 0 8px 24px rgba(0,0,0,0.12); border-radius: 12px; padding: 12px;",
    },
    grid: {
      left: 16,
      right: 16,
      top: 24,
      bottom: enableZoom ? 60 : rotate ? 44 : 28,
      containLabel: true,
    },
    dataZoom: enableZoom
      ? [
          { type: "inside", start, end, minValueSpan: 3 },
          {
            type: "slider",
            start,
            end,
            minValueSpan: 3,
            bottom: 12,
            height: 16,
            handleSize: 12,
            brushSelect: false,
            borderColor: "transparent",
            backgroundColor: "#f2f2f7",
            fillerColor: "rgba(88, 86, 214, 0.15)",
            handleStyle: {
              color: "#5856D6",
              shadowBlur: 4,
              shadowColor: "rgba(0, 0, 0, 0.2)",
            },
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: true,
      data: labels,
      axisLabel: {
        color: "#8e8e93",
        formatter: (value: string) => value?.slice(5),
        rotate,
        fontSize: 11,
      },
      axisTick: { show: false },
      axisLine: { show: false },
    },
    yAxis: {
      type: "value",
      name: yAxisName,
      nameTextStyle: {
        color: "#8e8e93",
        align: "right",
        padding: [0, 6, 0, 0],
      },
      min: 0,
      axisLabel: { color: "#8e8e93", fontSize: 11 },
      splitLine: {
        lineStyle: { type: "dashed", color: "#e5e5ea" },
      },
    },
    series: [
      {
        type: "bar",
        name: "学习时长",
        data: values,
        barWidth,
        barCategoryGap: "26%",
        itemStyle: {
          borderRadius: [6, 6, 2, 2],
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#5856D6" }, // Indigo
            { offset: 1, color: "#AF52DE" }, // Purple
          ]),
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: "rgba(88, 86, 214, 0.3)",
          },
        },
      },
    ],
  };
});

onMounted(async () => {
  await categoryStore.ensureLoaded();
  if (!trendCategoryId.value && categoryOptions.value.length) {
    // 默认选择“全部分类”
    selectedCategory.value = categoryOptions.value[0].value as any;
  }
  calcBarWidth();
  // 为了通过TS校验，包装一个无参的监听函数
  window.addEventListener("resize", onResize);
});

watch(
  () => categoryOptions.value.length,
  (len) => {
    if (len && !trendCategoryId.value) {
      selectedCategory.value = categoryOptions.value[0].value as any;
    }
  },
);

watch(
  () => subOptions.value,
  (options) => {
    if (
      trendSubcategoryId.value &&
      !options.some((opt) => opt.value === trendSubcategoryId.value)
    ) {
      selectedSubcategory.value = null;
    }
  },
);

// 数据加载完成后再按真实数据重算一次柱宽
watch(
  () => trendSeries.value.labels.length,
  () => {
    nextTick(() => {
      const len = trendSeries.value.labels?.length || 0;
      if (len > 0) {
        if (zoomRange.value.start == null || zoomRange.value.end == null) {
          zoomRange.value.start = 0;
          zoomRange.value.end = 100;
          calcBarWidth(100);
        } else {
          calcBarWidth();
        }
      } else {
        calcBarWidth();
      }
    });
  },
);

watch(
  isActiveTab,
  (active) => {
    if (active) {
      nextTick(() => {
        chartRef.value?.resize?.();
        chartsStore.fetchCategoryTrend();
        calcBarWidth();
      });
    }
  },
  { immediate: true },
);

onUnmounted(() => {
  window.removeEventListener("resize", onResize);
});

function onResize() {
  calcBarWidth();
}
</script>

<style scoped lang="scss">
.category-trend-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  min-height: 420px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  }
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.header-title {
  display: flex;
  flex-direction: column;
  gap: 4px;

  h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 700;
    color: #1c1c1e;
    letter-spacing: -0.5px;
  }

  p {
    margin: 0;
    font-size: 13px;
    color: #8e8e93;
  }
}

.selector-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.selector-wrapper {
  min-width: 160px;
}

/* iOS Style Select */
:deep(.ios-select) {
  .el-input__wrapper {
    background: #f2f2f7;
    border-radius: 10px;
    box-shadow: none !important;
    padding: 4px 12px;
    transition: all 0.2s ease;

    &:hover {
      background: #e5e5ea;
    }

    &.is-focus {
      background: #ffffff;
      box-shadow: 0 0 0 2px rgba(88, 86, 214, 0.2) !important;
    }
  }

  .el-input__inner {
    font-weight: 500;
    color: #1c1c1e;
  }
}

.chart-container {
  flex: 1;
  position: relative;
  min-height: 360px;
}

.chart {
  width: 100%;
  height: 380px;
}

.empty-state {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  color: #8e8e93;
  min-height: 300px;
  background: #f9f9f9;
  border-radius: 18px;

  .empty-icon {
    font-size: 48px;
    opacity: 0.5;
  }

  p {
    margin: 0;
    font-size: 15px;
    font-weight: 500;
  }
}

.chart-placeholder {
  padding: 48px 16px;
  text-align: center;
  color: #8e8e93;
  font-size: 13px;
}

@media (max-width: 768px) {
  .category-trend-card {
    padding: 20px;
  }

  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .selector-group {
    width: 100%;
  }

  .selector-wrapper {
    flex: 1;
    min-width: 0;
  }

  .chart {
    height: 320px;
  }
}
</style>
