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
    <div ref="scrollWrapper" class="bar-card__list">
      <div
        v-for="item in displayItems"
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
  Math.max(0, ...sortedData.value.map((item) => item.value)),
);

const displayItems = computed(() => {
  const max = maxValue.value || 1;
  return sortedData.value.map((item, idx) => {
    const percent = Math.max(
      0,
      Math.min(100, (Number(item.value || 0) / max) * 100),
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

<style scoped lang="scss">
.bar-card {
  background: #ffffff;
  border-radius: 24px;
  border: none;
  box-shadow: 0 16px 36px rgba(15, 23, 42, 0.08);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 280px;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  }
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
  color: #1c1c1e;

  svg {
    width: 20px;
    height: 20px;
    color: #5856d6;
  }

  h5 {
    margin: 0;
    font-size: 17px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }
}

.bar-card__list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
  margin-right: -8px;
  padding-right: 8px;
}

.bar-card__list::-webkit-scrollbar {
  width: 4px;
}

.bar-card__list::-webkit-scrollbar-thumb {
  background: rgba(142, 142, 147, 0.3);
  border-radius: 999px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 12px;
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.bar-item:hover {
  background: #f2f2f7;
}

.bar-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.bar-name {
  font-weight: 600;
  color: #1c1c1e;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bar-value {
  font-weight: 600;
  color: #8e8e93;
  font-size: 13px;
  flex-shrink: 0;
}

.bar-track {
  width: 100%;
  height: 8px;
  background: #f2f2f7;
  border-radius: 999px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
