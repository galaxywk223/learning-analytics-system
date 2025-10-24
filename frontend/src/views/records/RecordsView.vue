<template>
  <div class="records-view">
    <!-- 页面头部 -->
    <div class="page-header-records">
      <div>
        <h1>📚 学习记录</h1>
        <p class="text-secondary mb-0">
          在这里回顾每一次努力，见证成长的每一步。
        </p>
      </div>
      <div class="d-flex align-items-center gap-2">
        <!-- 排序按钮 -->
        <el-button-group>
          <el-button
            :type="currentSort === 'desc' ? 'primary' : ''"
            size="small"
            @click="changeSort('desc')"
          >
            降序
          </el-button>
          <el-button
            :type="currentSort === 'asc' ? 'primary' : ''"
            size="small"
            @click="changeSort('asc')"
          >
            升序
          </el-button>
        </el-button-group>
        <!-- 添加记录按钮 -->
        <el-tooltip
          :disabled="canAddRecord"
          content="请先创建或选择一个阶段"
          placement="top"
        >
          <el-button
            type="primary"
            :disabled="!canAddRecord"
            @click="openAddDialog"
          >
          <el-icon><Plus /></el-icon>
          添加新记录
          </el-button>
        </el-tooltip>
      </div>
    </div>

    <!-- 加载状态 -->
    <el-skeleton v-if="loading" :rows="4" animated />

    <!-- 空状态 -->
    <div v-else-if="!structuredLogs.length" class="text-center p-5 empty-state">
      <div class="empty-icon">📝</div>
      <h3>还没有任何记录</h3>
      <p class="text-muted">
        点击右上角的"添加新记录"按钮，开始你的第一条学习日志吧！
      </p>
      <el-button
        type="primary"
        size="large"
        @click="openAddDialog"
        class="mt-3"
      >
        <el-icon><Plus /></el-icon>
        创建第一条记录
      </el-button>
    </div>

    <!-- 周折叠面板 -->
    <el-collapse v-else v-model="activeWeeks" class="weeks-accordion">
      <el-collapse-item
        v-for="week in structuredLogs"
        :key="`${week.year}-${week.week_num}`"
        :name="`${week.year}-${week.week_num}`"
      >
        <!-- 周标题 -->
        <template #title>
          <div class="week-header">
            <span class="week-icon">📅</span>
            <span class="week-title">
              {{ week.year }} 年 - 第 {{ week.week_num }} 周
            </span>
            <el-tag type="info" size="small">
              周平均效率: {{ week.efficiency }}
            </el-tag>
          </div>
        </template>

        <!-- 每周的每一天 -->
        <div class="week-days">
          <el-card
            v-for="day in week.days"
            :key="day.date"
            class="day-card"
            shadow="hover"
          >
            <!-- 日期卡片头部 -->
            <template #header>
              <div class="day-card-header">
                <span class="date-badge">
                  <span class="weekday-icon">{{
                    getWeekdayIcon(day.date)
                  }}</span>
                  {{ formatDate(day.date) }} (周{{ getWeekday(day.date) }})
                </span>

                <!-- 进度条 -->
                <div
                  class="daily-progress-container"
                  :title="`今日总时长: ${day.total_duration} 分钟`"
                >
                  <el-progress
                    :percentage="
                      Math.min(100, (day.total_duration / 840) * 100)
                    "
                    :show-text="false"
                    :stroke-width="8"
                    :color="getProgressColor(day.total_duration)"
                  />
                </div>

                <span class="total-duration-text">
                  <el-icon class="clock-icon"><Clock /></el-icon>
                  {{ (day.total_duration / 60).toFixed(1) }}h
                </span>

                <el-tag type="success" size="small">
                  日效率: {{ day.efficiency }}
                </el-tag>

                <!-- 快速添加按钮 -->
                <el-button
                  circle
                  size="small"
                  @click.stop="openAddDialog(day.date)"
                  title="为今天添加记录"
                >
                  <el-icon><Plus /></el-icon>
                </el-button>
              </div>
            </template>

            <!-- 日志表格 -->
            <el-table
              :data="day.logs"
              class="log-table"
              size="small"
              :show-header="true"
            >
              <el-table-column label="任务" width="auto">
                <template #default="{ row }">
                  <div class="task-cell">
                    <span
                      v-if="row.subcategory"
                      class="category-tag"
                      :class="`category-color-${(row.subcategory.category_id || 0) % 6}`"
                      :title="row.subcategory.category?.name || ''"
                    >
                      {{ row.subcategory.name }}
                    </span>
                    <strong>{{ row.task }}</strong>
                  </div>
                </template>
              </el-table-column>
              <el-table-column label="时间段" width="120">
                <template #default="{ row }">
                  {{ row.time_slot || "N/A" }}
                </template>
              </el-table-column>
              <el-table-column label="时长" width="100">
                <template #default="{ row }">
                  {{ row.actual_duration }} 分钟
                </template>
              </el-table-column>
              <el-table-column label="心情" width="80" align="center">
                <template #default="{ row }">
                  <span class="mood-emoji">{{ moodEmoji(row.mood) }}</span>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150" align="right">
                <template #default="{ row }">
                  <el-button
                    v-if="row.notes"
                    link
                    size="small"
                    @click="toggleNotes(row.id)"
                    title="查看笔记"
                  >
                    <el-icon><ChatDotSquare /></el-icon>
                  </el-button>
                  <el-button
                    link
                    size="small"
                    @click="openEditDialog(row)"
                    title="编辑"
                  >
                    <el-icon><Edit /></el-icon>
                  </el-button>
                  <el-button
                    link
                    size="small"
                    type="danger"
                    @click="handleDelete(row)"
                    title="删除"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </template>
              </el-table-column>
              <!-- 展开行：笔记 -->
              <template #expand="{ row }">
                <div v-if="row.notes" class="log-notes-content">
                  {{ row.notes }}
                </div>
              </template>
            </el-table>

            <!-- 笔记展开区域（使用独立的div） -->
            <div v-for="log in day.logs" :key="`notes-${log.id}`">
              <div
                v-if="log.notes && expandedNotes.includes(log.id)"
                class="log-notes-row"
              >
                <div class="log-notes-cell">{{ log.notes }}</div>
              </div>
            </div>
          </el-card>
        </div>
      </el-collapse-item>
    </el-collapse>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditing ? '编辑记录' : '添加新纪录'"
      width="800px"
      @close="handleDialogClose"
      class="modern-dialog"
    >
      <RecordForm
        :record="currentRecord"
        :default-date="defaultDate"
        :loading="submitting"
        @submit="handleSubmit"
        @cancel="dialogVisible = false"
      />
      <template #footer>
        <!-- 调试辅助：显示当前状态，用于定位“无法弹出”问题 -->
        <div style="font-size:12px;color:#64748b;" v-if="__DEV__">
          dialogVisible: {{ dialogVisible }} | currentStage: {{ currentStage?.id || 'none' }} | isEditing: {{ isEditing }}
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  ChatDotSquare,
  Edit,
  Delete,
  Clock,
} from "@element-plus/icons-vue";
import RecordForm from "@/components/business/records/RecordForm.vue";
import { useStageStore } from "@/stores/modules/stage";
import request from "@/utils/request";

const stagesStore = useStageStore();

const loading = ref(false);
const submitting = ref(false);
const dialogVisible = ref(false);
const currentRecord = ref(null);
const defaultDate = ref(null);
const structuredLogs = ref([]);
const currentSort = ref("desc");
const activeWeeks = ref([]);
const expandedNotes = ref([]); // 记录展开的笔记ID

const isEditing = computed(() => !!currentRecord.value?.id);
// 是否可以添加记录（阶段已加载并选定）
const canAddRecord = computed(() => !!currentStage.value?.id && !stagesStore.loading);

// 获取当前活动阶段
const currentStage = computed(() => stagesStore.activeStage);

// 加载结构化记录
const loadRecords = async () => {
  if (!currentStage.value?.id) {
    ElMessage.warning("请先创建一个学习阶段");
    return;
  }

  loading.value = true;
  try {
    const response = await request.get("/api/records/structured", {
      params: {
        stage_id: currentStage.value.id,
        sort: currentSort.value,
      },
    });

    if (response.success) {
      structuredLogs.value = response.structured_logs || [];
      // 默认展开第一周
      if (structuredLogs.value.length > 0) {
        const firstWeek = structuredLogs.value[0];
        activeWeeks.value = [`${firstWeek.year}-${firstWeek.week_num}`];
      }
    }
  } catch (error) {
    console.error("加载记录失败:", error);
    ElMessage.error("加载记录失败");
  } finally {
    loading.value = false;
  }
};

// 改变排序
const changeSort = (sort) => {
  currentSort.value = sort;
  loadRecords();
};

// 打开添加对话框
const openAddDialog = (date = null) => {
  // 阶段未选择时直接提示
  if (!currentStage.value?.id) {
    ElMessage.warning("请先创建或选择一个学习阶段再添加记录");
    return;
  }
  currentRecord.value = null;
  defaultDate.value = date;
  dialogVisible.value = true;
  // 调试日志便于排查“没有反应”问题
  console.debug("打开添加记录对话框", { date });
};

// 打开编辑对话框
const openEditDialog = (record) => {
  currentRecord.value = record;
  defaultDate.value = null;
  dialogVisible.value = true;
};

// 关闭对话框时重置状态
const handleDialogClose = () => {
  currentRecord.value = null;
  defaultDate.value = null;
};

// 提交表单
const handleSubmit = async (formData) => {
  submitting.value = true;
  try {
    if (isEditing.value) {
      // 更新记录
      await request.put(`/api/records/${currentRecord.value.id}`, {
        ...formData,
        stage_id: currentStage.value.id,
      });
      ElMessage.success("记录更新成功!");
    } else {
      // 创建记录
      await request.post("/api/records", {
        ...formData,
        stage_id: currentStage.value.id,
      });
      ElMessage.success("新纪录添加成功!");
    }

    dialogVisible.value = false;
    loadRecords();
  } catch (error) {
    console.error("提交失败:", error);
    ElMessage.error(error.response?.data?.message || "操作失败");
  } finally {
    submitting.value = false;
  }
};

// 删除记录
const handleDelete = async (record) => {
  try {
    await ElMessageBox.confirm(`确定要删除"${record.task}"吗？`, "警告", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });

    await request.delete(`/api/records/${record.id}`);
    ElMessage.success("记录已删除。");
    loadRecords();
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
      ElMessage.error("删除失败");
    }
  }
};

// 切换笔记展开
const toggleNotes = (logId) => {
  const index = expandedNotes.value.indexOf(logId);
  if (index > -1) {
    expandedNotes.value.splice(index, 1);
  } else {
    expandedNotes.value.push(logId);
  }
};

// 心情表情
const moodEmoji = (mood) => {
  const moods = {
    5: "😃",
    4: "😊",
    3: "😐",
    2: "😟",
    1: "😠",
  };
  return moods[mood] || "⚪️";
};

// 格式化日期
const formatDate = (dateStr) => {
  const date = new Date(dateStr);
  return date.toLocaleDateString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
};

// 获取星期几
const getWeekday = (dateStr) => {
  const weekdays = ["日", "一", "二", "三", "四", "五", "六"];
  const date = new Date(dateStr);
  return weekdays[date.getDay()];
};

// 获取星期几的图标
const getWeekdayIcon = (dateStr) => {
  const icons = ["🌞", "🌙", "🔥", "⚡", "🌟", "💫", "🎯"];
  const date = new Date(dateStr);
  return icons[date.getDay()];
};

// 获取进度条颜色
const getProgressColor = (duration) => {
  const percentage = (duration / 840) * 100;
  if (percentage >= 80) return "#10b981"; // green
  if (percentage >= 50) return "#667eea"; // purple
  if (percentage >= 30) return "#fbbf24"; // yellow
  return "#ef4444"; // red
};

onMounted(() => {
  stagesStore.fetchStages().then(() => {
    loadRecords();
  });
});
</script>

<style scoped lang="scss">
@use "@/styles/views/records/RecordsView.module.scss";

/* 分类颜色 */
@for $i from 0 through 5 {
  .category-color-#{$i} {
    background-color: var(--category-color-#{$i}, #eee);
    color: var(--category-text-color-#{$i}, #333);
  }
}
</style>
