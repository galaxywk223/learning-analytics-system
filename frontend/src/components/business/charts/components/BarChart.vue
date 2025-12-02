<template>
  <div class="bar-card">
    <header class="bar-card__header">
      <div class="bar-card__title">
        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M3 13h5v8H3v-8Zm6-6h5v14h-5V7Zm6 4h6v10h-6V11Z" />
        </svg>
        <h5>{{ title }}</h5>
      </div>
    </header>
    <div class="bar-card__list" ref="scrollWrapper">
      <div
        v-for="(item, idx) in displayItems"
        :key="item.name"
        class="bar-item"
        @click="emitClick(item.name)"
        @mouseenter="emitHover(item.name)"
        @mouseleave="emitLeave"
      >
        <div class="bar-info">
          <span class="bar-name">{{ item.name }}</span>
          <span class="bar-value">{{ formatValue(item.value) }}h</span>
        </div>
        <div class="bar-track">
          <div
            class="bar-fill"
            :style="{
              width: item.percent + '%',
              backgroundColor: item.color,
            }"
          ></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from "vue";

const props = defineProps({
  data: { type: Object, required: true },
  title: { type: String, default: "High Frequency Categories" },
  colors: { type: Array, default: () => [] },
});

const emit = defineEmits(["bar-click", "bar-hover", "bar-leave"]);
const scrollWrapper = ref(null);

function scrollToTop(smooth = true) {
  const el = scrollWrapper.value;
  if (!el) return;
  if (typeof el.scrollTo === "function") {
    el.scrollTo({ top: 0, behavior: smooth ? "smooth" : "auto" });
  } else {
    el.scrollTop = 0;
  }
}
defineExpose({ scrollToTop });

const normalized = computed(() => {
  const labels = Array.isArray(props.data?.labels) ? props.data.labels : [];
  const values = Array.isArray(props.data?.data) ? props.data.data : [];

  return labels.map((label, idx) => {
    const hasLabel = typeof label === "string" && label.trim().length > 0;
    const name = hasLabel ? label.trim() : `分类 ${idx + 1}`;
    const rawValue = values[idx];
    const numeric = Number(rawValue ?? 0);
    return { name, value: Number.isFinite(numeric) ? numeric : 0 };
  });
});

const sortedData = computed(() => {
  const items = [...normalized.value];
  return items.sort((a, b) => {
    if (b.value === a.value) {
      return a.name.localeCompare(b.name);
    }
    return b.value - a.value;
  });
});

const barColors = computed(() => {
  if (props.colors?.length) {
    return props.colors;
  }
  return [
    "#6366f1",
    "#22d3ee",
    "#f97316",
    "#0ea5e9",
    "#facc15",
    "#10b981",
    "#f472b6",
    "#fb7185",
    "#14b8a6",
    "#8b5cf6",
  ];
});

const maxValue = computed(() =>
  Math.max(0, ...sortedData.value.map((item) => item.value))
);

const displayItems = computed(() => {
  const max = maxValue.value || 1;
  return sortedData.value.map((item, idx) => {
    const percent = Math.max(
      0,
      Math.min(100, (Number(item.value || 0) / max) * 100)
    );
    return {
      ...item,
      color: barColors.value[idx % barColors.value.length],
      percent: Number(percent.toFixed(2)),
    };
  });
});

const formatValue = (val) => Number(val ?? 0).toFixed(1);

const emitClick = (name) => {
  if (typeof name === "string" && name.trim()) emit("bar-click", name);
};
const emitHover = (name) => {
  if (typeof name === "string" && name.trim()) emit("bar-hover", name);
};
const emitLeave = () => emit("bar-leave");
</script>

<style scoped>
.bar-card {
  background: #ffffff;
  border-radius: 24px;
  border: none;
  box-shadow: 0 18px 44px rgba(15, 23, 42, 0.08);
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 280px;
}

.bar-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.bar-card__title {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1f1d47;

  svg {
    width: 20px;
    height: 20px;
    color: #6366f1;
  }

  h5 {
    margin: 0;
    font-size: 15px;
    font-weight: 700;
  }
}

.bar-card__list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-height: 420px;
  overflow-y: auto;
  margin-right: -6px;
  padding-right: 6px;
}

.bar-card__list::-webkit-scrollbar {
  width: 6px;
}

.bar-card__list::-webkit-scrollbar-thumb {
  background: rgba(99, 102, 241, 0.3);
  border-radius: 999px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 12px;
  transition: background-color 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.bar-item:hover {
  background: #f8fafc;
  box-shadow: inset 0 0 0 1px rgba(226, 232, 240, 0.9);
}

.bar-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.bar-name {
  font-weight: 700;
  color: #0f172a;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-value {
  font-weight: 600;
  color: #475569;
  font-size: 13px;
  flex-shrink: 0;
}

.bar-track {
  width: 100%;
  height: 16px;
  background: #f3f4f6;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 1s ease-out;
}
</style>
