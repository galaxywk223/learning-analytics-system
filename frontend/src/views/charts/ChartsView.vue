<template>
  <div class="charts-view">
    <div class="page-header">
      <div class="header-content">
        <h1>📊 统计分析</h1>
        <p class="lead">通过数据洞察学习模式，掌握成长轨迹</p>
      </div>
    </div>

    <div class="toolbar-container">
      <div class="toolbar-left">
        <!-- Tabs 按钮组 -->
        <div class="btn-group tab-switch">
          <button
            :class="['btn', charts.activeTab === 'trends' && 'active']"
            @click="charts.setActiveTab('trends')"
          >
            📈 趋势分析
          </button>
          <button
            :class="['btn', charts.activeTab === 'categories' && 'active']"
            @click="charts.setActiveTab('categories')"
          >
            🎯 分类占比
          </button>
          <button
            :class="['btn', charts.activeTab === 'wordcloud' && 'active']"
            @click="charts.setActiveTab('wordcloud')"
          >
            ☁️ 词云分析
          </button>
        </div>
        <!-- 周/日视图切换，仅在趋势分析 tab 显示 -->
        <div class="btn-group view-switch" v-if="charts.activeTab === 'trends'">
          <button
            :class="['btn', charts.viewType === 'weekly' && 'active']"
            @click="charts.setViewType('weekly')"
          >
            📅 周视图
          </button>
          <button
            :class="['btn', charts.viewType === 'daily' && 'active']"
            @click="charts.setViewType('daily')"
          >
            📆 日视图
          </button>
        </div>
        <!-- 阶段下拉，仅在分类占比与词云分析显示 -->
        <select
          v-if="charts.activeTab !== 'trends'"
          class="stage-select"
          v-model="stageSelected"
          @change="charts.setStage(stageSelected)"
        >
          <option value="all">全部历史</option>
          <option v-for="s in charts.stages" :key="s.id" :value="s.id">
            {{ s.name }}
          </option>
        </select>
      </div>
      <div class="toolbar-right">
        <button class="export-btn" @click="handleExport" :disabled="exporting">
          <span v-if="!exporting">📥 导出全部图表</span>
          <span v-else>⏳ 导出中...</span>
        </button>
      </div>
    </div>
    <div class="tab-panels">
      <div v-show="charts.activeTab === 'trends'" class="panel">
        <!-- KPI 仅在趋势分析面板内部显示，符合旧项目布局 -->
        <div class="kpi-grid" v-loading="charts.loading">
          <KpiCard
            label="平均每日时长"
            :value="charts.kpis.avg_daily_formatted || '--'"
            color="primary"
          >
            <template #icon>⏱️</template>
          </KpiCard>
          <KpiCard
            label="效率之星"
            :value="charts.kpis.efficiency_star || '--'"
            color="amber"
          >
            <template #icon>⭐</template>
          </KpiCard>
          <KpiCard
            label="本周趋势 (vs 上周)"
            :value="charts.kpis.weekly_trend || '--'"
            color="green"
          >
            <template #icon>📊</template>
          </KpiCard>
        </div>
        <!-- 无数据/初始化提示 -->
        <div v-if="!charts.loading && !charts.hasTrendsData" class="alert-box">
          <div
            v-if="charts.rawChartData?.setup_needed"
            class="alert alert-info"
          >
            尚未创建阶段或学习记录，暂时无法生成趋势图表。请先添加学习日志。
          </div>
          <div v-else class="alert alert-info">
            暂无学习数据，无法生成趋势图表。
          </div>
        </div>
        <TrendsChart
          :weekly-duration-data="charts.trends.weekly_duration_data"
          :weekly-efficiency-data="charts.trends.weekly_efficiency_data"
          :daily-duration-data="charts.trends.daily_duration_data"
          :daily-efficiency-data="charts.trends.daily_efficiency_data"
          :stage-annotations="charts.stageAnnotations"
          :has-data="charts.hasTrendsData"
          :loading="charts.loading"
          :initial-view="charts.viewType"
        />
      </div>
      <div v-show="charts.activeTab === 'categories'" class="panel">
        <div
          v-if="!charts.loading && !charts.hasCategoryData"
          class="category-empty-alert alert alert-info text-center"
        >
          当前筛选范围内没有找到任何带分类的学习记录。
        </div>
        <div class="category-header" v-if="charts.categoryPath?.length">
          <el-button
            size="small"
            text
            type="primary"
            @click="charts.backCategory"
            >⬅️ 返回上级</el-button
          >
          <span class="path"
            >当前层级：
            <span v-for="(p, idx) in charts.categoryPath" :key="p.id">
              <span class="crumb" @click="jumpTo(idx)">{{ p.name }}</span>
              <span v-if="idx < charts.categoryPath.length - 1"> / </span>
            </span>
          </span>
        </div>
        <CategoryComposite
          :main="charts.categoryData.main"
          :drilldown="charts.categoryData.drilldown"
          :loading="charts.loading"
          @sliceClick="onCategorySlice"
          @back="charts.backCategory"
        />
      </div>
      <div
        v-show="charts.activeTab === 'wordcloud'"
        class="panel wordcloud-panel"
      >
        <div class="wordcloud-controls">
          <div class="mask-grid" v-if="charts.wordcloudOptions.masks?.length">
            <div
              v-for="m in charts.wordcloudOptions.masks"
              :key="m.file"
              :class="['mask-item', currentMask === m.file && 'active']"
              @click="selectMask(m.file)"
              :title="m.name"
            >
              <img
                v-if="m.file !== 'random'"
                :src="getMaskImage(m.file)"
                :alt="m.name"
              />
              <span v-else class="random-icon">🔀</span>
            </div>
          </div>
          <el-select
            v-model="currentPalette"
            placeholder="🎨 调色板"
            size="default"
            style="width: 160px"
            @change="selectPalette"
          >
            <el-option
              v-for="p in charts.wordcloudOptions.palettes || []"
              :key="p.name"
              :label="p.label || p.name"
              :value="p.name"
            />
          </el-select>
          <button
            class="export-btn"
            style="padding: 0.5rem 1rem; font-size: 0.85rem"
            @click="refreshWordcloud"
            :disabled="charts.loading"
          >
            <span v-if="!charts.loading">🔄 刷新词云</span>
            <span v-else>⏳ 生成中...</span>
          </button>
        </div>
        <div class="wordcloud-display" v-loading="charts.wordcloudLoading">
          <div
            v-if="!charts.wordcloudLoading && !charts.wordcloudImageUrl"
            class="alert alert-light text-center"
          >
            {{ charts.wordcloudMessage || "暂无词云数据，请调整筛选后重试。" }}
          </div>
          <WordCloudChart
            :imageUrl="charts.wordcloudImageUrl"
            :loading="charts.wordcloudLoading"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useChartsStore } from "@/stores/modules/charts";
import { chartsAPI } from "@/api/modules/charts";
import TrendsChart from "@/components/business/charts/TrendsChart.vue";
import CategoryChart from "@/components/business/charts/CategoryChart.vue";
import WordCloudChart from "@/components/business/charts/WordCloudChart.vue";
import KpiCard from "@/components/business/charts/KpiCard.vue";
import { ElMessage } from "element-plus";

const charts = useChartsStore();
const stageSelected = ref("all");
const exporting = ref(false);
// 词云当前选择（与旧项目逻辑保持）
const currentMask = ref("random");
const currentPalette = ref("default");

function selectMask(maskFile) {
  currentMask.value = maskFile;
  charts.setWordcloudMask(maskFile);
}
function selectPalette(pName) {
  currentPalette.value = pName;
  charts.setWordcloudPalette(pName);
}
function getMaskImage(file) {
  // 使用前端 public 下的 images/masks 资源（旧项目静态结构复制）
  return `/images/masks/${file}`;
}

async function handleExport() {
  exporting.value = true;
  try {
    const response = await chartsAPI.exportCharts();
    const dispo = response.headers?.["content-disposition"];
    let filename = "charts_export.zip";
    if (dispo) {
      const match = /filename=([^;]+)/i.exec(dispo);
      if (match) filename = match[1].replace(/"/g, "");
    }
    const blob = response.data instanceof Blob ? response.data : response;
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    ElMessage.success(`已下载：${filename}`);
  } catch (e) {
    ElMessage.error("导出失败");
  } finally {
    exporting.value = false;
  }
}

function refreshWordcloud() {
  charts.fetchWordcloud({
    palette: currentPalette.value,
    mask: currentMask.value,
  });
}

function onCategorySlice(cat) {
  if (!cat) return;
  charts.drillCategory(cat);
}

function jumpTo(index) {
  // 回退到路径中某一层
  if (index < 0) return;
  while (charts.categoryPath.length > index + 1) {
    charts.backCategory();
  }
}

onMounted(async () => {
  await charts.initStages();
  await charts.fetchWordcloudOptions();
  await charts.refreshAll();
});
</script>

<style scoped lang="scss">
@import "@/styles/views/charts/charts-view";
</style>
