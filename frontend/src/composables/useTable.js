/**
 * 表格通用功能组合式函数
 * 包含分页、加载状态、选择等功能
 */
import { ref, computed } from "vue";

export function useTable(options = {}) {
  const { pageSize = 10, currentPage = 1 } = options;

  const loading = ref(false);
  const tableData = ref([]);
  const total = ref(0);
  const page = ref(currentPage);
  const size = ref(pageSize);
  const selectedRows = ref([]);

  // 分页相关
  const currentPageData = computed(() => {
    const start = (page.value - 1) * size.value;
    const end = start + size.value;
    return tableData.value.slice(start, end);
  });

  const handlePageChange = (newPage) => {
    page.value = newPage;
  };

  const handleSizeChange = (newSize) => {
    size.value = newSize;
    page.value = 1; // 改变每页数量时回到第一页
  };

  // 选择相关
  const handleSelectionChange = (selection) => {
    selectedRows.value = selection;
  };

  const clearSelection = () => {
    selectedRows.value = [];
  };

  // 加载数据
  const setTableData = (data, totalCount = null) => {
    tableData.value = data;
    if (totalCount !== null) {
      total.value = totalCount;
    } else {
      total.value = data.length;
    }
  };

  return {
    loading,
    tableData,
    total,
    page,
    size,
    selectedRows,
    currentPageData,
    handlePageChange,
    handleSizeChange,
    handleSelectionChange,
    clearSelection,
    setTableData,
  };
}
