/**
 * 图表颜色工具函数
 */
export function buildColors(count: number): string[] {
  const palette = [
    "#60A5FA",
    "#F87171",
    "#FBBF24",
    "#4ADE80",
    "#A78BFA",
    "#2DD4BF",
    "#F472B6",
    "#818CF8",
    "#FB923C",
    "#34D399",
  ];

  if (count <= palette.length) {
    return palette.slice(0, count);
  }

  // 如果需要更多颜色，生成随机颜色
  const colors = [...palette];
  while (colors.length < count) {
    colors.push("#" + Math.random().toString(16).slice(2, 8));
  }

  return colors;
}

/**
 * 数据转换工具函数
 */
interface ChartData {
  labels: string[];
  data: number[];
}

interface CombinedItem {
  label: string;
  value: number;
}

export function transformDataForChart(
  sourceData?: ChartData,
  topN: number = 10,
): ChartData {
  if (!sourceData?.labels || !sourceData?.data) {
    return { labels: [], data: [] };
  }

  // 组合标签和数据
  const combined: CombinedItem[] = sourceData.labels.map((label, index) => ({
    label,
    value: sourceData.data[index] || 0,
  }));

  // 按数值排序并取前N个
  const sorted = combined.sort((a, b) => b.value - a.value).slice(0, topN);

  return {
    labels: sorted.map((item) => item.label),
    data: sorted.map((item) => item.value),
  };
}

/**
 * 计算总时长
 */
export function calculateTotalHours(data?: ChartData): number {
  if (!data?.data || !Array.isArray(data.data)) {
    return 0;
  }
  return data.data.reduce((sum, value) => sum + (value || 0), 0);
}

/**
 * 格式化表格数据
 */
export function formatTableData(sourceData?: ChartData): CombinedItem[] {
  if (!sourceData?.labels || !sourceData?.data) {
    return [];
  }

  return sourceData.labels.map((label, index) => ({
    label,
    value: sourceData.data[index] || 0,
  }));
}
