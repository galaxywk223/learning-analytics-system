<template>
  <div class="trend-chart-card">
    <div v-if="!hasData && !loading" class="trend-chart-card__empty">
      <svg
        class="trend-chart-card__empty-icon"
        viewBox="0 0 24 24"
        fill="currentColor"
        aria-hidden="true"
      >
        <path
          d="M12 2C17.5228 2 22 6.47715 22 12C22 13.7005 21.578 15.3098 20.8281 16.7241L21.8701 20.1029C22.0415 20.6692 21.6692 21.2585 21.1029 21.4299C20.8579 21.5034 20.5943 21.4713 20.3736 21.3408L17.2759 19.5149C15.8627 20.3517 14.2207 20.8 12.5 20.8C6.97715 20.8 2.5 16.3228 2.5 10.8C2.5 5.27715 6.97715 0.8 12.5 0.8V2ZM12 4C7.58172 4 4 7.58172 4 12C4 16.4183 7.58172 20 12 20C13.6666 20 15.2268 19.5368 16.541 18.7201L17.0833 18.3863L19.1681 19.6304L18.6137 17.541C19.4353 16.2269 19.9 14.6691 19.9 13C19.9 8.58172 16.3183 5 11.9 5L12 4ZM11.25 7.75H12.75V13.5H11.25V7.75ZM11.25 15.25H12.75V17.5H11.25V15.25Z"
        />
      </svg>
      <p class="trend-chart-card__empty-text">
        暂无可视化数据，记录新的学习时长后即可查看趋势。
      </p>
    </div>
    <div v-else v-loading="loading" class="trend-chart-card__panel">
      <header class="trend-chart-card__header">
        <div class="trend-chart-card__titles">
          <span class="trend-chart-card__eyebrow">Trend Forecast</span>
          <h3>学习趋势</h3>
          <p>{{ forecastMeta }}</p>
        </div>
        <div class="trend-chart-card__switch">
          <button
            class="trend-chart-card__retrain-btn"
            :disabled="loading || forecastRetraining || forecastStatus?.state === 'pending'"
            @click="emit('retrain-forecast')"
          >
            <span class="trend-chart-card__retrain-icon">
              {{ forecastRetraining ? "•••" : "↻" }}
            </span>
            <span>{{ forecastRetraining ? "重训练中" : "手动重训练" }}</span>
          </button>
          <div class="trend-chart-card__view-toggle">
            <button
              :class="['seg-btn', currentView === 'weekly' && 'active']"
              @click="switchView('weekly')"
            >
              <span class="emoji-icon" aria-hidden="true">📅</span>
              <span>周视图</span>
            </button>
            <button
              :class="['seg-btn', currentView === 'daily' && 'active']"
              @click="switchView('daily')"
            >
              <span class="emoji-icon" aria-hidden="true">📆</span>
              <span>日视图</span>
            </button>
          </div>
        </div>
      </header>
      <div class="trend-chart-card__meta-strip">
        <span
          v-for="item in forecastBadgeItems"
          :key="item.label"
          class="trend-chart-card__meta-pill"
          :class="item.emphasis ? 'trend-chart-card__meta-pill--emphasis' : ''"
        >
          <strong>{{ item.label }}</strong>
          <span>{{ item.value }}</span>
        </span>
      </div>
      <div
        v-if="forecastWarning"
        class="trend-chart-card__forecast-warning"
      >
        {{ forecastWarning }}
      </div>
      <div class="trend-chart-card__forecast-grid">
        <article
          v-for="item in forecastCards"
          :key="item.key"
          class="trend-chart-card__forecast-card"
          :class="`trend-chart-card__forecast-card--${item.tone}`"
        >
          <div class="trend-chart-card__forecast-card-head">
            <div>
              <span class="trend-chart-card__forecast-card-label">
                {{ item.title }}
              </span>
              <strong>{{ item.status }}</strong>
            </div>
            <span class="trend-chart-card__forecast-chip">
              {{ item.model }}
            </span>
          </div>
          <p class="trend-chart-card__forecast-card-summary">
            {{ item.summary }}
          </p>
          <div class="trend-chart-card__forecast-card-metrics">
            <span>{{ item.metricA }}</span>
            <span>{{ item.metricB }}</span>
          </div>
        </article>
      </div>
      <v-chart
        :key="chartRenderKey"
        class="trend-chart-card__visual"
        :option="chartOption"
        :update-options="{ notMerge: true }"
        autoresize
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from "vue";
import { use, graphic } from "echarts/core";
import { LineChart } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkAreaComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import VChart from "vue-echarts";

use([
  CanvasRenderer,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DataZoomComponent,
  MarkAreaComponent,
]);

const props = defineProps({
  weeklyDurationData: { type: Object, required: true },
  weeklyEfficiencyData: { type: Object, required: true },
  dailyDurationData: { type: Object, required: true },
  dailyEfficiencyData: { type: Object, required: true },
  forecastStatus: { type: Object, default: () => ({}) },
  forecastRetraining: { type: Boolean, default: false },
  stageAnnotations: { type: Array, default: () => [] },
  hasData: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
  initialView: { type: String, default: "weekly" },
});

const emit = defineEmits(["view-change", "retrain-forecast"]);

const currentView = ref(props.initialView === "daily" ? "daily" : "weekly");
const themeVersion = ref(0);
let themeObserver = null;

const readThemeVar = (name, fallback) => {
  if (typeof window === "undefined") return fallback;
  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
  return value || fallback;
};

const themeTokens = computed(() => {
  themeVersion.value;
  return {
    textBase: readThemeVar("--color-text-base", "#1c1c1e"),
    textSecondary: readThemeVar("--color-text-secondary", "#8e8e93"),
    textHeading: readThemeVar("--color-text-heading", "#1c1c1e"),
    card: readThemeVar("--surface-card", "#ffffff"),
    subtle: readThemeVar("--surface-subtle", "#f2f2f7"),
    border: readThemeVar("--color-border-card", "#e5e5ea"),
    primary: readThemeVar("--color-primary", "#5856D6"),
    primaryDark: readThemeVar("--color-primary-dark", "#AF52DE"),
    warning: readThemeVar("--color-warning", "#FF9500"),
    success: readThemeVar("--color-success", "#30D158"),
    info: readThemeVar("--color-info", "#64D2FF"),
    warningSoft: "rgba(255, 149, 0, 0.18)",
    primarySoft: readThemeVar("--color-primary-light", "rgba(88, 86, 214, 0.2)"),
    inverse: readThemeVar("--color-text-inverse", "#ffffff"),
  };
});

watch(
  () => props.initialView,
  (newView) => {
    if (!newView || newView === currentView.value) return;
    currentView.value = newView === "daily" ? "daily" : "weekly";
  },
);

const sanitizeSeries = (values, { allowZero = true } = {}) => {
  if (!Array.isArray(values)) return [];
  return values.map((val) => {
    if (val === null || val === undefined || Number.isNaN(Number(val))) {
      return allowZero ? 0 : null;
    }
    const num = Number(val);
    if (!Number.isFinite(num)) {
      return allowZero ? 0 : null;
    }
    return Number(num.toFixed(2));
  });
};

const normalizeForecast = (forecast) => ({
  labels: Array.isArray(forecast?.labels) ? forecast.labels : [],
  prediction: sanitizeSeries(forecast?.prediction, { allowZero: true }),
  lower: sanitizeSeries(forecast?.lower, { allowZero: true }),
  upper: sanitizeSeries(forecast?.upper, { allowZero: true }),
  modelName: forecast?.model_name || "",
  historyPoints: Number(forecast?.history_points || 0),
  horizon: Number(forecast?.horizon || 0),
  trainedOn: forecast?.trained_on || "all_history",
  confidenceLevel: Number(forecast?.confidence_level || 0.8),
  accuracyThreshold: Number(forecast?.accuracy_threshold || 0.4),
  selectionStrategy: forecast?.selection_strategy || "lowest_wape_then_rmse",
  validationWape:
    forecast?.validation_wape == null
      ? null
      : Number(forecast.validation_wape),
  validationRmse:
    forecast?.validation_rmse == null
      ? null
      : Number(forecast.validation_rmse),
  baselineWape:
    forecast?.baseline_wape == null ? null : Number(forecast.baseline_wape),
  baselineRmse:
    forecast?.baseline_rmse == null ? null : Number(forecast.baseline_rmse),
  modelCandidates: Array.isArray(forecast?.model_candidates)
    ? forecast.model_candidates
    : [],
  status:
    typeof forecast?.status === "string"
      ? forecast.status
      : forecast?.available
        ? "ready"
        : "unavailable",
  available:
    Boolean(forecast?.available) &&
    Array.isArray(forecast?.labels) &&
    Array.isArray(forecast?.prediction) &&
    forecast.labels.length > 0 &&
    forecast.prediction.length > 0,
  reason: typeof forecast?.reason === "string" ? forecast.reason : "",
});

const formatPercent = (value, digits = 1) => {
  if (value == null || Number.isNaN(Number(value))) return "--";
  return `${(Number(value) * 100).toFixed(digits)}%`;
};

const formatMetric = (value, digits = 2) => {
  if (value == null || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
};

const formatImprovement = (baseline, current) => {
  if (
    baseline == null ||
    current == null ||
    Number.isNaN(Number(baseline)) ||
    Number.isNaN(Number(current)) ||
    Number(baseline) <= 0
  ) {
    return "";
  }
  const improvement = (Number(baseline) - Number(current)) / Number(baseline);
  const prefix = improvement >= 0 ? "+" : "";
  return `${prefix}${(improvement * 100).toFixed(1)}%`;
};

const normalizeLabel = (value) => {
  if (value == null) return "";
  return String(value).trim();
};

const findLabelIndex = (labels, label) => {
  if (!Array.isArray(labels)) return -1;
  const target = normalizeLabel(label);
  return labels.findIndex((item) => normalizeLabel(item) === target);
};

const getSeriesValueByLabel = (labels, values, label) => {
  if (!Array.isArray(labels) || !Array.isArray(values) || !label) {
    return null;
  }
  const index = findLabelIndex(labels, label);
  if (index < 0) {
    return null;
  }
  const value = values[index];
  if (value == null || Number.isNaN(Number(value))) {
    return null;
  }
  return Number(value);
};

const renderTooltipRow = (color, label, value) =>
  `<div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
    <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;"></span>
    <span>${label}</span>
    <strong style="margin-left:auto;">${Number(value).toFixed(2)}</strong>
  </div>`;

const switchView = (view) => {
  const normalized = view === "daily" ? "daily" : "weekly";
  if (normalized === currentView.value) return;
  currentView.value = normalized;
  emit("view-change", normalized);
};

const durationLegendLabel = "时长";
const efficiencyLegendLabel = "效率";

const durationSeriesLabel = computed(() =>
  currentView.value === "weekly" ? "平均学习时长" : "学习时长",
);

const currentForecasts = computed(() => {
  const isWeekly = currentView.value === "weekly";
  return {
    duration: normalizeForecast(
      isWeekly
        ? props.weeklyDurationData?.forecast
        : props.dailyDurationData?.forecast,
    ),
    efficiency: normalizeForecast(
      isWeekly
        ? props.weeklyEfficiencyData?.forecast
        : props.dailyEfficiencyData?.forecast,
    ),
  };
});

const currentDatasets = computed(() => {
  const isWeekly = currentView.value === "weekly";
  return {
    duration: isWeekly ? props.weeklyDurationData : props.dailyDurationData,
    efficiency: isWeekly ? props.weeklyEfficiencyData : props.dailyEfficiencyData,
  };
});

const hasOngoingPeriod = computed(() => {
  const { duration, efficiency } = currentDatasets.value;
  return Boolean(duration?.ongoing || efficiency?.ongoing);
});

const forecastMeta = computed(() => {
  const { duration, efficiency } = currentForecasts.value;
  const hasPending =
    duration.status === "pending" || efficiency.status === "pending";
  const activeForecast = duration.available ? duration : efficiency;
  const threshold = formatPercent(activeForecast.accuracyThreshold || 0.4);
  if (hasPending) {
    return `基于全部历史训练 · 预测后台生成中 · 精度门槛 WAPE <= ${threshold}`;
  }
  if (!activeForecast.available) {
    return `预测基于全部历史训练 · 精度门槛 WAPE <= ${threshold}`;
  }
  const unit = currentView.value === "weekly" ? "周" : "天";
  const ongoingSuffix = hasOngoingPeriod.value ? " · 含当前进行中周期" : "";
  return `基于全部历史训练 · 未来 ${activeForecast.horizon}${unit}预测${ongoingSuffix} · 精度门槛 WAPE <= ${threshold}`;
});

const lastTrainingLabel = computed(() => {
  const trainedForDate = props.forecastStatus?.trained_for_date;
  if (!trainedForDate) {
    return "尚未完成今日训练";
  }
  return `最近训练 ${trainedForDate}`;
});

const forecastWarning = computed(() => {
  const { duration, efficiency } = currentForecasts.value;
  const pending = [duration, efficiency].some(
    (forecast) => forecast.status === "pending",
  );
  if (pending) {
    return "预测正在后台生成，历史趋势已先展示，结果完成后会自动补齐。";
  }
  const missing = [];
  if (!duration.available) missing.push("时长");
  if (!efficiency.available) missing.push("效率");
  if (!missing.length) return "";
  if (missing.length === 2) {
    return duration.reason || efficiency.reason || "历史数据不足，暂不提供预测";
  }
  return `${missing[0]}${duration.reason || efficiency.reason || "历史数据不足，暂不提供预测"}`;
});

const forecastBadgeItems = computed(() => {
  const { duration, efficiency } = currentForecasts.value;
  const activeForecast = duration.available ? duration : efficiency;
  const unit = currentView.value === "weekly" ? "周" : "天";
  const items = [
    {
      label: "训练范围",
      value: "全部历史",
      emphasis: false,
    },
    {
      label: "预测长度",
      value: activeForecast.horizon ? `${activeForecast.horizon}${unit}` : "--",
      emphasis: true,
    },
    {
      label: "当前周期",
      value: hasOngoingPeriod.value ? "含进行中" : "仅完整周期",
      emphasis: false,
    },
    {
      label: "训练状态",
      value:
        props.forecastStatus?.state === "pending"
          ? "后台重算中"
          : lastTrainingLabel.value,
      emphasis: props.forecastStatus?.state === "ready",
    },
    {
      label: "拦截门槛",
      value: `WAPE <= ${formatPercent(activeForecast.accuracyThreshold || 0.4)}`,
      emphasis: false,
    },
  ];
  return items;
});

const forecastCards = computed(() => {
  const items = [
    {
      key: "duration",
      title: "时长预测",
      forecast: currentForecasts.value.duration,
    },
    {
      key: "efficiency",
      title: "效率预测",
      forecast: currentForecasts.value.efficiency,
    },
  ];

  return items.map(({ key, title, forecast }) => {
    const pending = forecast.status === "pending";
    const blocked =
      !pending && !forecast.available && forecast.reason?.includes("误差较高");
    const tone = pending ? "pending" : forecast.available ? "ready" : blocked ? "blocked" : "idle";
    const status = pending
      ? "后台生成中"
      : forecast.available
        ? "预测已启用"
        : blocked
          ? "已因误差拦截"
          : "暂未启用";
    const model = pending ? "等待结果" : forecast.modelName || "无模型";
    const summary = pending
      ? "先展示历史与进行中数据，预测完成后自动补齐。"
      : blocked
        ? forecast.reason || "历史回测误差较高，暂不显示预测。"
        : forecast.reason || "已按当前最优模型输出预测。";
    const improvement = formatImprovement(
      forecast.baselineWape,
      forecast.validationWape,
    );

    return {
      key,
      title,
      tone,
      status,
      model,
      summary,
      metricA: `WAPE ${formatPercent(forecast.validationWape)}`,
      metricB:
        forecast.baselineWape != null
          ? improvement
            ? `相对基线 ${improvement}`
            : `基线 ${formatPercent(forecast.baselineWape)}`
          : `RMSE ${formatMetric(forecast.validationRmse)}`,
    };
  });
});

const buildForecastLayer = (labels, actualSeries, forecast) => {
  const mergedLabels = [...labels];
  (forecast.labels || []).forEach((label) => {
    if (!mergedLabels.includes(label)) {
      mergedLabels.push(label);
    }
  });

  const actualValues = Array.isArray(actualSeries) ? actualSeries : [];
  const actualMap = new Map(labels.map((label, index) => [label, actualValues[index] ?? null]));
  const extendedActual = mergedLabels.map((label) => actualMap.get(label) ?? null);

  if (!forecast.available || !forecast.labels?.length) {
    return {
      labels: mergedLabels,
      actual: extendedActual,
      prediction: Array.from({ length: mergedLabels.length }, () => null),
      lower: Array.from({ length: mergedLabels.length }, () => null),
      band: Array.from({ length: mergedLabels.length }, () => null),
    };
  }

  const predictionMap = new Map(
    forecast.labels.map((label, index) => [label, forecast.prediction[index] ?? null]),
  );
  const lowerMap = new Map(
    forecast.labels.map((label, index) => [label, forecast.lower[index] ?? null]),
  );
  const upperMap = new Map(
    forecast.labels.map((label, index) => [label, forecast.upper[index] ?? null]),
  );
  const prediction = mergedLabels.map((label) =>
    predictionMap.has(label) ? predictionMap.get(label) : null,
  );
  const lower = mergedLabels.map((label) =>
    lowerMap.has(label) ? lowerMap.get(label) : null,
  );
  const band = mergedLabels.map((label) => {
    if (!upperMap.has(label) || !lowerMap.has(label)) {
      return null;
    }
    return Math.max(
      0,
      Number(upperMap.get(label) ?? 0) - Number(lowerMap.get(label) ?? 0),
    );
  });

  const lastHistoricalLabel = labels[labels.length - 1];
  if (
    lastHistoricalLabel &&
    !predictionMap.has(lastHistoricalLabel) &&
    actualMap.has(lastHistoricalLabel)
  ) {
    const tailIndex = mergedLabels.indexOf(lastHistoricalLabel);
    if (tailIndex >= 0) {
      prediction[tailIndex] = actualMap.get(lastHistoricalLabel);
    }
  }

  return {
    labels: mergedLabels,
    actual: extendedActual,
    prediction,
    lower,
    band,
  };
};

const buildOngoingLayer = (labels, actualSeries, dataset) => {
  const ongoingLabel = dataset?.ongoing_label;
  if (!dataset?.ongoing || !ongoingLabel) {
    return Array.from({ length: labels.length }, () => null);
  }
  const ongoingIndex = labels.indexOf(ongoingLabel);
  if (ongoingIndex < 0) {
    return Array.from({ length: labels.length }, () => null);
  }
  const series = Array.from({ length: labels.length }, () => null);
  if (ongoingIndex > 0) {
    series[ongoingIndex - 1] = actualSeries[ongoingIndex - 1] ?? null;
  }
  series[ongoingIndex] = actualSeries[ongoingIndex] ?? dataset?.ongoing_value ?? null;
  return series;
};

const buildOngoingPointLayer = (labels, actualSeries, dataset) => {
  const ongoingLabel = dataset?.ongoing_label;
  if (!dataset?.ongoing || !ongoingLabel) {
    return Array.from({ length: labels.length }, () => null);
  }
  const ongoingIndex = labels.indexOf(ongoingLabel);
  if (ongoingIndex < 0) {
    return Array.from({ length: labels.length }, () => null);
  }
  const series = Array.from({ length: labels.length }, () => null);
  series[ongoingIndex] = actualSeries[ongoingIndex] ?? dataset?.ongoing_value ?? null;
  return series;
};

const removeOngoingFromActual = (labels, actualSeries, dataset) => {
  const normalized = Array.isArray(actualSeries) ? [...actualSeries] : [];
  const ongoingLabel = dataset?.ongoing_label;
  if (!dataset?.ongoing || !ongoingLabel) {
    return normalized;
  }
  const ongoingIndex = labels.indexOf(ongoingLabel);
  if (ongoingIndex >= 0) {
    normalized[ongoingIndex] = null;
  }
  return normalized;
};

const buildForecastDisplaySeries = (
  labels,
  predictionSeries,
  dataset,
  actualSeries,
  fallbackAnchorValue,
) => {
  const normalized = Array.isArray(predictionSeries) ? [...predictionSeries] : [];
  const ongoingLabel = dataset?.ongoing_label;
  if (!dataset?.ongoing || !ongoingLabel) {
    return normalized;
  }
  const ongoingIndex = labels.indexOf(ongoingLabel);
  if (ongoingIndex < 0) {
    return normalized;
  }
  if (ongoingIndex > 0) {
    const historyAnchor = actualSeries?.[ongoingIndex - 1] ?? null;
    if (historyAnchor != null) {
      normalized[ongoingIndex - 1] = historyAnchor;
    }
  }
  if (normalized[ongoingIndex] == null) {
    const anchorValue = dataset?.ongoing_value ?? fallbackAnchorValue ?? null;
    if (anchorValue != null) {
      normalized[ongoingIndex] = anchorValue;
    }
  }
  return normalized;
};

const viewSource = computed(() => {
  const isWeekly = currentView.value === "weekly";
  const duration = isWeekly
    ? props.weeklyDurationData
    : props.dailyDurationData;
  const efficiency = isWeekly
    ? props.weeklyEfficiencyData
    : props.dailyEfficiencyData;

  const labels = Array.isArray(duration?.labels) ? duration.labels : [];
  const durationActual = sanitizeSeries(duration?.actuals, { allowZero: true });
  const efficiencyActual = sanitizeSeries(efficiency?.actuals, {
    allowZero: true,
  });
  const { duration: durationForecast, efficiency: efficiencyForecast } =
    currentForecasts.value;
  const durationLayer = buildForecastLayer(labels, durationActual, durationForecast);
  const efficiencyLayer = buildForecastLayer(
    labels,
    efficiencyActual,
    efficiencyForecast,
  );
  const mergedLabels = [...durationLayer.labels];
  efficiencyLayer.labels.forEach((label) => {
    if (!mergedLabels.includes(label)) {
      mergedLabels.push(label);
    }
  });
  const alignToLabels = (seriesLabels, values) =>
    mergedLabels.map((label) => {
      const index = seriesLabels.indexOf(label);
      return index >= 0 ? values[index] ?? null : null;
  });
  const durationOngoing = buildOngoingLayer(labels, durationActual, duration);
  const efficiencyOngoing = buildOngoingLayer(labels, efficiencyActual, efficiency);
  const durationOngoingPoint = buildOngoingPointLayer(
    labels,
    durationActual,
    duration,
  );
  const efficiencyOngoingPoint = buildOngoingPointLayer(
    labels,
    efficiencyActual,
    efficiency,
  );
  const alignedDurationPrediction = alignToLabels(
    durationLayer.labels,
    durationLayer.prediction,
  );
  const alignedEfficiencyPrediction = alignToLabels(
    efficiencyLayer.labels,
    efficiencyLayer.prediction,
  );

  return {
    labels: mergedLabels,
    historicalLabels: labels,
    durationActual: alignToLabels(
      durationLayer.labels,
      removeOngoingFromActual(durationLayer.labels, durationLayer.actual, duration),
    ),
    efficiencyActual: alignToLabels(
      efficiencyLayer.labels,
      removeOngoingFromActual(efficiencyLayer.labels, efficiencyLayer.actual, efficiency),
    ),
    durationPrediction: buildForecastDisplaySeries(
      mergedLabels,
      alignedDurationPrediction,
      duration,
      alignToLabels(durationLayer.labels, durationLayer.actual),
      duration?.ongoing_value,
    ),
    efficiencyPrediction: buildForecastDisplaySeries(
      mergedLabels,
      alignedEfficiencyPrediction,
      efficiency,
      alignToLabels(efficiencyLayer.labels, efficiencyLayer.actual),
      efficiency?.ongoing_value,
    ),
    durationLower: alignToLabels(durationLayer.labels, durationLayer.lower),
    durationBand: alignToLabels(durationLayer.labels, durationLayer.band),
    efficiencyLower: alignToLabels(efficiencyLayer.labels, efficiencyLayer.lower),
    efficiencyBand: alignToLabels(efficiencyLayer.labels, efficiencyLayer.band),
    durationOngoing: alignToLabels(labels, durationOngoing),
    efficiencyOngoing: alignToLabels(labels, efficiencyOngoing),
    durationOngoingPoint: alignToLabels(labels, durationOngoingPoint),
    efficiencyOngoingPoint: alignToLabels(labels, efficiencyOngoingPoint),
    durationForecast,
    efficiencyForecast,
    durationDataset: duration,
    efficiencyDataset: efficiency,
  };
});

const stageMarkArea = computed(() => {
  if (currentView.value !== "weekly") return [];
  const labels = viewSource.value.labels;
  if (!labels.length) return [];

  const labelSet = new Set(labels);
  return (props.stageAnnotations || [])
    .filter(
      (item) =>
        item &&
        labelSet.has(item.start_week_label) &&
        labelSet.has(item.end_week_label),
    )
    .map((item) => [
      {
        name: item.name,
        xAxis: item.start_week_label,
        itemStyle: { opacity: 0.04 }, // Even more subtle
        label: {
          color: themeTokens.value.primary,
          fontWeight: 600,
          fontSize: 12,
        },
      },
      { xAxis: item.end_week_label },
    ]);
});

const showStageHelper = computed(
  () => currentView.value === "weekly" && stageMarkArea.value.length > 0,
);

const chartRenderKey = computed(() => {
  const source = viewSource.value;
  return [
    currentView.value,
    source.labels.length,
    source.durationDataset?.ongoing_label || "",
    source.efficiencyDataset?.ongoing_label || "",
    source.durationForecast.labels?.[0] || "",
    source.efficiencyForecast.labels?.[0] || "",
    source.durationForecast.prediction?.[0] ?? "",
    source.efficiencyForecast.prediction?.[0] ?? "",
    themeVersion.value,
  ].join("|");
});

const chartOption = computed(() => {
  const {
    labels,
    durationActual,
    efficiencyActual,
    durationPrediction,
    efficiencyPrediction,
    durationLower,
    durationBand,
    efficiencyLower,
    efficiencyBand,
    durationOngoing,
    efficiencyOngoing,
    durationOngoingPoint,
    efficiencyOngoingPoint,
    durationForecast,
    efficiencyForecast,
  } = viewSource.value;
  const windowSize = currentView.value === "weekly" ? 26 : 90;
  const enableZoom = labels.length > windowSize;
  const startIndex = Math.max(0, labels.length - windowSize);
  const zoomStartValue = labels[startIndex];
  const zoomEndValue = labels[labels.length - 1];

  const token = themeTokens.value;

  // Apple-style Colors
  const colors = {
    duration: {
      line: token.primary,
      areaStart: token.primarySoft,
      areaEnd: "rgba(88, 86, 214, 0.02)",
      ongoing: token.success,
    },
    efficiency: {
      line: token.warning,
      areaStart: token.warningSoft,
      areaEnd: "rgba(255, 149, 0, 0.02)",
      ongoing: token.info,
    },
  };

  return {
    color: [colors.duration.line, colors.efficiency.line],
    tooltip: {
      trigger: "axis",
      backgroundColor: token.card,
      borderColor: token.border,
      borderWidth: 1,
      padding: [12, 16],
      textStyle: {
        color: token.textBase,
        fontSize: 13,
        fontFamily:
          '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      },
      extraCssText:
        "box-shadow: 0 4px 12px rgba(0,0,0,0.12); border-radius: 12px;",
      formatter: (params) => {
        const rows = Array.isArray(params) ? params : [params];
        const axisValue = rows[0]?.axisValue ?? rows[0]?.name ?? rows[0]?.axisValueLabel ?? "";
        const axisLabel = normalizeLabel(axisValue);
        const axisTitle = rows[0]?.axisValueLabel || axisLabel;
        let content = `<div style="font-weight:600;margin-bottom:6px;">${axisTitle}</div>`;
        const durationActualValue = getSeriesValueByLabel(
          labels,
          durationActual,
          axisLabel,
        );
        const efficiencyActualValue = getSeriesValueByLabel(
          labels,
          efficiencyActual,
          axisLabel,
        );
        const durationLiveValue = getSeriesValueByLabel(
          labels,
          durationOngoingPoint,
          axisLabel,
        );
        const efficiencyLiveValue = getSeriesValueByLabel(
          labels,
          efficiencyOngoingPoint,
          axisLabel,
        );
        const durationForecastIndex = findLabelIndex(durationForecast.labels, axisLabel);
        const efficiencyForecastIndex = findLabelIndex(efficiencyForecast.labels, axisLabel);
        const durationPredictionValue =
          durationForecastIndex >= 0
            ? durationForecast.prediction[durationForecastIndex] ?? null
            : null;
        const efficiencyPredictionValue =
          efficiencyForecastIndex >= 0
            ? efficiencyForecast.prediction[efficiencyForecastIndex] ?? null
            : null;

        const resolvedDurationActual =
          durationLiveValue ?? durationActualValue;
        const resolvedEfficiencyActual =
          efficiencyLiveValue ?? efficiencyActualValue;

        if (resolvedDurationActual != null) {
          const label =
            durationLiveValue != null
              ? `当前${durationSeriesLabel.value}`
              : durationSeriesLabel.value;
          content += renderTooltipRow(colors.duration.line, label, resolvedDurationActual);
        }
        if (resolvedEfficiencyActual != null) {
          const label =
            efficiencyLiveValue != null ? "当前学习效率" : "学习效率";
          content += renderTooltipRow(
            colors.efficiency.line,
            label,
            resolvedEfficiencyActual,
          );
        }
        if (durationPredictionValue != null) {
          content += renderTooltipRow(
            colors.duration.line,
            "时长预测",
            durationPredictionValue,
          );
        }
        if (efficiencyPredictionValue != null) {
          content += renderTooltipRow(
            colors.efficiency.line,
            "效率预测",
            efficiencyPredictionValue,
          );
        }

        if (durationForecast.available && durationForecastIndex >= 0) {
          const idx = durationForecastIndex;
          content += `<div style="margin-top:6px;color:${token.textSecondary};">时长区间：${durationForecast.lower[idx].toFixed(2)} - ${durationForecast.upper[idx].toFixed(2)}</div>`;
          content += `<div style="color:${token.textSecondary};">时长模型：${durationForecast.modelName}</div>`;
          content += `<div style="color:${token.textSecondary};">时长WAPE：${formatPercent(durationForecast.validationWape)}</div>`;
          content += `<div style="color:${token.textSecondary};">时长RMSE：${formatMetric(durationForecast.validationRmse)}</div>`;
        }
        if (efficiencyForecast.available && efficiencyForecastIndex >= 0) {
          const idx = efficiencyForecastIndex;
          content += `<div style="margin-top:6px;color:${token.textSecondary};">效率区间：${efficiencyForecast.lower[idx].toFixed(2)} - ${efficiencyForecast.upper[idx].toFixed(2)}</div>`;
          content += `<div style="color:${token.textSecondary};">效率模型：${efficiencyForecast.modelName}</div>`;
          content += `<div style="color:${token.textSecondary};">效率WAPE：${formatPercent(efficiencyForecast.validationWape)}</div>`;
          content += `<div style="color:${token.textSecondary};">效率RMSE：${formatMetric(efficiencyForecast.validationRmse)}</div>`;
        }
        return content;
      },
    },
    legend: {
      top: 12,
      icon: "circle",
      itemGap: 24,
      textStyle: {
        color: token.textSecondary,
        fontSize: 13,
      },
      data: [
        durationLegendLabel,
        efficiencyLegendLabel,
      ],
    },
    grid: {
      left: 20,
      right: 20,
      top: 80,
      bottom: enableZoom ? 60 : 20,
      containLabel: true,
      borderColor: token.border,
    },
    dataZoom: enableZoom
      ? [
          {
            type: "inside",
            startValue: zoomStartValue,
            endValue: zoomEndValue,
          },
          {
            type: "slider",
            startValue: zoomStartValue,
            endValue: zoomEndValue,
            bottom: 16,
            height: 4, // Thinner slider
            borderRadius: 2,
            brushSelect: false,
            handleSize: 16,
            handleStyle: {
              color: token.card,
              borderColor: token.border,
              shadowBlur: 2,
              shadowColor: "rgba(0,0,0,0.1)",
            },
            fillerColor: token.primarySoft,
            borderColor: "transparent",
            backgroundColor: token.subtle,
            showDataShadow: false,
            showDetail: false,
          },
        ]
      : [],
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: labels,
      axisLabel: {
        color: token.textSecondary,
        fontSize: 12,
        margin: 12,
        formatter: (value) => value.slice(5),
      },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: "value",
        name: "学习时长 (小时)",
        min: 0,
        nameTextStyle: { color: token.textSecondary, padding: [0, 0, 0, 20] },
        axisLabel: { color: token.textSecondary, fontSize: 12 },
        splitLine: {
          lineStyle: { type: "dashed", color: token.border },
        },
      },
      {
        type: "value",
        name: "效率指数",
        min: 0,
        nameTextStyle: { color: token.textSecondary, padding: [0, 20, 0, 0] },
        axisLabel: { color: token.textSecondary, fontSize: 12 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: durationLegendLabel,
        type: "line",
        smooth: 0.4,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 8,
        data: durationActual,
        itemStyle: {
          color: colors.duration.line,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 3,
          shadowColor: "rgba(88, 86, 214, 0.3)",
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors.duration.areaStart },
            { offset: 1, color: colors.duration.areaEnd },
          ]),
        },
        markArea: stageMarkArea.value.length
          ? { silent: true, data: stageMarkArea.value }
          : undefined,
      },
      {
        name: durationLegendLabel,
        type: "line",
        smooth: 0.25,
        showSymbol: false,
        yAxisIndex: 0,
        data: durationOngoing,
        tooltip: { show: false },
        lineStyle: {
          width: 3,
          opacity: 0.95,
          color: colors.duration.line,
        },
      },
      {
        name: durationLegendLabel,
        type: "line",
        smooth: 0,
        showSymbol: true,
        symbol: "circle",
        symbolSize: 9,
        yAxisIndex: 0,
        data: durationOngoingPoint,
        tooltip: { show: false },
        itemStyle: {
          color: colors.duration.ongoing,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 0,
          opacity: 0,
        },
      },
      {
        name: durationLegendLabel,
        type: "line",
        yAxisIndex: 0,
        showSymbol: false,
        silent: true,
        data: durationLower,
        stack: "duration-forecast-band",
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        tooltip: { show: false },
      },
      {
        name: durationLegendLabel,
        type: "line",
        yAxisIndex: 0,
        showSymbol: false,
        silent: true,
        data: durationBand,
        stack: "duration-forecast-band",
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: "rgba(88, 86, 214, 0.12)",
        },
        tooltip: { show: false },
      },
      {
        name: durationLegendLabel,
        type: "line",
        smooth: 0.25,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 6,
        yAxisIndex: 0,
        data: durationPrediction,
        itemStyle: {
          color: colors.duration.line,
        },
        lineStyle: {
          width: 2.5,
          type: "dashed",
          color: colors.duration.line,
        },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        smooth: 0.4,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 8,
        yAxisIndex: 1,
        data: efficiencyActual,
        itemStyle: {
          color: colors.efficiency.line,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 3,
          color: colors.efficiency.line,
          shadowColor: "rgba(255, 149, 0, 0.3)",
          shadowBlur: 10,
          shadowOffsetY: 4,
        },
        areaStyle: {
          color: new graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: colors.efficiency.areaStart },
            { offset: 1, color: colors.efficiency.areaEnd },
          ]),
        },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        smooth: 0.25,
        showSymbol: false,
        yAxisIndex: 1,
        data: efficiencyOngoing,
        tooltip: { show: false },
        lineStyle: {
          width: 3,
          opacity: 0.95,
          color: colors.efficiency.line,
        },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        smooth: 0,
        showSymbol: true,
        symbol: "circle",
        symbolSize: 9,
        yAxisIndex: 1,
        data: efficiencyOngoingPoint,
        tooltip: { show: false },
        itemStyle: {
          color: colors.efficiency.ongoing,
          borderWidth: 2,
          borderColor: token.card,
        },
        lineStyle: {
          width: 0,
          opacity: 0,
        },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        yAxisIndex: 1,
        showSymbol: false,
        silent: true,
        data: efficiencyLower,
        stack: "efficiency-forecast-band",
        lineStyle: { opacity: 0 },
        areaStyle: { opacity: 0 },
        tooltip: { show: false },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        yAxisIndex: 1,
        showSymbol: false,
        silent: true,
        data: efficiencyBand,
        stack: "efficiency-forecast-band",
        lineStyle: { opacity: 0 },
        areaStyle: {
          color: "rgba(255, 149, 0, 0.12)",
        },
        tooltip: { show: false },
      },
      {
        name: efficiencyLegendLabel,
        type: "line",
        smooth: 0.25,
        showSymbol: false,
        symbol: "circle",
        symbolSize: 6,
        yAxisIndex: 1,
        data: efficiencyPrediction,
        itemStyle: {
          color: colors.efficiency.line,
        },
        lineStyle: {
          width: 2.5,
          type: "dashed",
          color: colors.efficiency.line,
        },
      },
    ],
  };
});

onMounted(() => {
  if (typeof window === "undefined" || !window.MutationObserver) return;
  themeObserver = new MutationObserver(() => {
    themeVersion.value += 1;
  });
  themeObserver.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["data-theme", "class", "style"],
  });
});

onUnmounted(() => {
  if (themeObserver) {
    themeObserver.disconnect();
    themeObserver = null;
  }
});
</script>

<style scoped lang="scss">
@import "@/styles/components/trends-chart";
</style>
