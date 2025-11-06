<template>
  <div class="category-trend">
    <div class="selector-card">
      <div class="selector-grid">
        <div class="selector-field">
          <span class="label">分类</span>
          <el-select
            v-model="selectedCategory"
            placeholder="选择分类"
            filterable
            clearable
            :disabled="categoryStore.loading"
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
        <div class="selector-field">
          <span class="label">子分类</span>
          <el-select
            v-model="selectedSubcategory"
            placeholder="全部子分类"
            :disabled="!selectedCategory"
            clearable
            filterable
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

    <el-card class="chart-card" v-loading="trendLoading" shadow="never">
      <template #header>
        <div class="chart-title">
          <span>学习时长趋势</span>
          <small v-if="trendMeta">{{ trendMeta }}</small>
        </div>
      </template>
      <div v-if="!trendSeries.labels.length && !trendLoading" class="empty">
        <p>当前筛选范围内没有记录。</p>
      </div>
      <v-chart
        v-else-if="isActiveTab"
        ref="chartRef"
        class="chart"
        :option="option"
        autoresize
        :update-options="{ replaceMerge: ['series', 'xAxis', 'yAxis', 'grid', 'dataZoom'] }"
        @datazoom="handleDataZoom"
        @finished="handleChartFinished"
      />
      <div v-else class="chart-placeholder">
        <p>切换到“分类趋势”即可查看图表。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick, ref, onUnmounted } from "vue";
import { use, graphic } from "echarts/core";
import { BarChart } from "echarts/charts";
import { GridComponent, TooltipComponent, DataZoomComponent } from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";
import { storeToRefs } from "pinia";
import { useCategoryStore } from "@/stores/category";
import { useChartsStore } from "@/stores/modules/charts";

use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, DataZoomComponent]);

const categoryStore = useCategoryStore();
const chartsStore = useChartsStore();

const {
  categoryTrend,
  categoryTrendLoading,
  trendCategoryId,
  trendSubcategoryId,
  activeTab,
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
      const enableZoom = len > 14;
      const sliderWindow = enableZoom ? Math.min(100, Math.round((14 / len) * 100)) : 100;
      const start = enableZoom ? Math.max(0, 100 - sliderWindow) : 0;
      const end = 100;
      zoomRange.value.start = start;
      zoomRange.value.end = end;
      calcBarWidth(end - start);
      return;
    }
  }
  calcBarWidth();
}

const option = computed(() => {
  const labels = trendSeries.value.labels || [];
  const values = (trendSeries.value.data || []).map((v) =>
    Number.isFinite(Number(v)) ? Number(v) : 0
  );
  const enableZoom = labels.length > 14;
  const sliderWindow = enableZoom
    ? Math.min(100, Math.round((14 / labels.length) * 100))
    : 100;
  const initialStart = enableZoom ? Math.max(0, 100 - sliderWindow) : 0;
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

  return {
    color: ["#6366f1"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        return `${item.name}<br/>${Number(item.value || 0).toFixed(2)} 小时`;
      },
      confine: true,
    },
    grid: {
      left: 20,
      right: 20,
      top: 16,
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
            height: 14,
            handleSize: 12,
            brushSelect: false,
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: true,
      data: labels,
      axisLabel: {
        color: "#475569",
        formatter: (value: string) => value?.slice(5),
        rotate,
      },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.35)" } },
    },
    yAxis: {
      type: "value",
      name: "学习时长 (小时)",
      min: 0,
      axisLabel: { color: "#475569" },
      splitLine: {
        lineStyle: { type: "dashed", color: "rgba(148,163,184,0.35)" },
      },
    },
    series: [
      {
        type: "bar",
        name: "学习时长",
        data: values,
        barWidth,
        barCategoryGap: "40%",
        itemStyle: {
          borderRadius: [6, 6, 0, 0],
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#6366f1" },
            { offset: 1, color: "#a5b4fc" },
          ]),
        },
        emphasis: { focus: "series" },
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
  window.addEventListener('resize', calcBarWidth);
});

watch(
  () => categoryOptions.value.length,
  (len) => {
    if (len && !trendCategoryId.value) {
      selectedCategory.value = categoryOptions.value[0].value as any;
    }
  }
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
  }
);

// 数据加载完成后再按真实数据重算一次柱宽
watch(
  () => trendSeries.value.labels.length,
  () => {
    nextTick(() => {
      const len = trendSeries.value.labels?.length || 0;
      if (len > 0) {
        if (zoomRange.value.start == null || zoomRange.value.end == null) {
          const enableZoom = len > 14;
          const sliderWindow = enableZoom ? Math.min(100, Math.round((14 / len) * 100)) : 100;
          const start = enableZoom ? Math.max(0, 100 - sliderWindow) : 0;
          const end = 100;
          zoomRange.value.start = start;
          zoomRange.value.end = end;
          calcBarWidth(end - start);
        } else {
          calcBarWidth();
        }
      } else {
        calcBarWidth();
      }
    });
  }
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
  { immediate: true }
);

onUnmounted(() => {
  window.removeEventListener('resize', calcBarWidth);
});
</script>

<style scoped>
.category-trend {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.selector-card {
  background: var(--surface-card);
  border: 1px solid var(--color-border-card);
  border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.selector-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  align-items: center;
}

.selector-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.selector-field :deep(.el-select) {
  width: 100%;
}

.label {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.chart-card {
  border-radius: 12px;
  border: 1px solid var(--color-border-card);
  min-height: 380px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

.chart-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 600;
  color: #1f2937;
}

.chart-title small {
  color: var(--color-text-secondary);
  font-weight: 400;
}

.chart {
  width: 100%;
  height: 360px;
}

.empty {
  padding: 48px 16px;
  text-align: center;
  color: var(--color-text-secondary);
}

.chart-placeholder {
  padding: 48px 16px;
  text-align: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}

@media (max-width: 768px) {
  .chart {
    height: 320px;
  }
}
</style>
