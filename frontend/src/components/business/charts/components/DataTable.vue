<template>
  <div class="data-table-wrapper">
    <div class="divider"></div>
    <div class="table-container" ref="tableContainer"></div>
    <div class="nav-controls" v-if="showNavigation">
      <button class="nav-button back-btn" @click="handleBack">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path
            d="M7.82843 10.9999H20V12.9999H7.82843L13.1924 18.3639L11.7782 19.7781L4 11.9999L11.7782 4.22168L13.1924 5.63589L7.82843 10.9999Z"
          />
        </svg>
        返回
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";

const props = defineProps({
  data: {
    type: Array,
    required: true,
  },
  totalHours: {
    type: Number,
    default: 0,
  },
  drilldownData: {
    type: Object,
    default: () => ({}),
  },
  showNavigation: {
    type: Boolean,
    default: false,
  },
  isMainView: {
    type: Boolean,
    default: true,
  },
});

const emit = defineEmits(["drill-down", "back"]);

const tableContainer = ref(null);

function handleBack() {
  emit("back");
}

function renderTable() {
  if (!tableContainer.value || !props.data?.length) return;

  let html = `
    <table class="table table-hover">
      <thead>
        <tr>
          <th>名称</th>
          <th>时长(h)</th>
          <th>占比(%)</th>
        </tr>
      </thead>
      <tbody>
  `;

  props.data.forEach((item) => {
    const pct = props.totalHours
      ? ((item.value / props.totalHours) * 100).toFixed(1)
      : "0.0";

    const hasDrilldown =
      props.isMainView &&
      props.drilldownData[item.label] &&
      props.drilldownData[item.label].labels?.length > 0;

    const drillInfo = hasDrilldown
      ? ` data-drill="${item.label}" style="cursor:pointer"`
      : "";

    html += `
      <tr${drillInfo}>
        <td>${item.label}</td>
        <td>${item.value.toFixed(1)}</td>
        <td>${pct}</td>
      </tr>
    `;
  });

  html += "</tbody></table>";
  tableContainer.value.innerHTML = html;

  // 绑定钻取事件
  if (props.isMainView) {
    tableContainer.value.querySelectorAll("tr[data-drill]").forEach((row) => {
      row.addEventListener("click", () => {
        const category = row.getAttribute("data-drill");
        emit("drill-down", category);
      });
    });
  }
}

watch(() => [props.data, props.totalHours], renderTable, { deep: true });

nextTick(() => {
  renderTable();
});
</script>

<style scoped>
.data-table-wrapper {
  width: 100%;
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.divider {
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent 0%,
    #e2e8f0 50%,
    transparent 100%
  );
  margin: 6px 0;
  flex-shrink: 0;
}

.table-container {
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.table-container :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
  background: #fff;
  margin: 0;
}

.table-container :deep(thead) {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  position: sticky;
  top: 0;
  z-index: 10;
}

.table-container :deep(thead tr th) {
  padding: 10px 16px;
  text-align: left;
  font-weight: 700;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-container :deep(tbody tr) {
  transition: all 0.2s ease;
  border-bottom: 1px solid #f1f5f9;
}

.table-container :deep(tbody tr:hover) {
  background: linear-gradient(135deg, #f8fafc 0%, #f0f9ff 100%);
  transform: scale(1.01);
}

.table-container :deep(tbody tr[data-drill]:hover) {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  cursor: pointer;
}

.table-container :deep(tbody tr td) {
  padding: 8px 16px;
  color: #4b5563;
  font-weight: 500;
  font-size: 13px;
}

.table-container :deep(tbody tr td:first-child) {
  font-weight: 600;
  color: #1f2937;
}

.table-container :deep(tbody tr td:nth-child(2)) {
  font-family: "SF Mono", "Monaco", "Cascadia Code", monospace;
  font-weight: 600;
  color: #059669;
}

.table-container :deep(tbody tr td:last-child) {
  font-family: "SF Mono", "Monaco", "Cascadia Code", monospace;
  font-weight: 600;
  color: #dc2626;
}

.nav-controls {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

.nav-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.back-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
}

.back-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(107, 114, 128, 0.5);
}

.nav-button svg {
  width: 16px;
  height: 16px;
}

@media (max-width: 768px) {
  .table-container :deep(table) {
    font-size: 13px;
  }

  .table-container :deep(thead tr th),
  .table-container :deep(tbody tr td) {
    padding: 10px 12px;
  }
}
</style>
