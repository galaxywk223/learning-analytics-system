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
        :update-options="{ replaceMerge: ['series', 'xAxis', 'yAxis', 'grid'] }"
      />
      <div v-else class="chart-placeholder">
        <p>切换到“分类趋势”即可查看图表。</p>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, watch, nextTick, ref } from "vue";
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

const option = computed(() => {
  const labels = trendSeries.value.labels || [];
  const values = (trendSeries.value.data || []).map((v) =>
    Number.isFinite(Number(v)) ? Number(v) : 0
  );
  const enableZoom = labels.length > 14;
  const sliderWindow = enableZoom
    ? Math.min(100, Math.round((14 / labels.length) * 100))
    : 100;
  const sliderStart = enableZoom ? Math.max(0, 100 - sliderWindow) : 0;

  return {
    color: ["#6366f1"],
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) => {
        const item = Array.isArray(params) ? params[0] : params;
        return `${item.name}<br/>${Number(item.value || 0).toFixed(2)} 小时`;
      },
    },
    grid: {
      left: 24,
      right: 24,
      top: 20,
      bottom: enableZoom ? 56 : 28,
      containLabel: true,
    },
    dataZoom: enableZoom
      ? [
          { type: "inside", start: sliderStart, end: 100 },
          {
            type: "slider",
            start: sliderStart,
            end: 100,
            bottom: 16,
            height: 14,
            handleSize: 12,
            brushSelect: false,
          },
        ]
      : [],
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: {
        color: "#475569",
        formatter: (value: string) => value?.slice(5),
      },
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "rgba(148, 163, 184, 0.45)" } },
    },
    yAxis: {
      type: "value",
      name: "学习时长 (小时)",
      min: 0,
      axisLabel: { color: "#475569" },
      splitLine: {
        lineStyle: { type: "dashed", color: "rgba(148,163,184,0.45)" },
      },
    },
    series: [
      {
        type: "bar",
        name: "学习时长",
        data: values,
        barWidth: 24,
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

watch(
  isActiveTab,
  (active) => {
    if (active) {
      nextTick(() => {
        chartRef.value?.resize?.();
        chartsStore.fetchCategoryTrend();
      });
    }
  },
  { immediate: true }
);
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
  padding: 14px 18px;
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
  padding: 42px 16px;
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
