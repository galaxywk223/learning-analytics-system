<template>
  <div class="focus-view">
    <div class="bg-blobs"></div>
    <PageContainer
      :title="isTimerRunning ? '🎯 专注中' : '🎯 开始专注'"
      subtitle="保持专注，记录每一步的累积"
    >
      <div class="focus-layout">
        <div class="focus-layout__timer">
          <!-- 计时器显示 -->
          <FocusTimer
            :elapsed-seconds="elapsedSeconds"
            :is-active="isTimerRunning"
          />

          <!-- 控制按钮 -->
          <FocusControls
            :is-running="isTimerRunning"
            :is-paused="isPaused"
            :loading="loading"
            @start="startTimer"
            @pause="pauseTimer"
            @resume="resumeTimer"
            @stop="showStopDialog"
            @cancel="cancelSession"
            @go-back="goBack"
          />
        </div>

        <div class="focus-layout__details">
          <!-- 表单区域 -->
          <FocusForm
            v-if="!isTimerRunning && !isPaused"
            v-model:form-data="focusForm"
            :categories="categories"
            :subcategories="allSubcategories"
            @category-change="onCategoryChange"
            ref="formRef"
          />

          <!-- 已开始时显示的信息 -->
          <FocusInfo
            v-else
            :form-data="focusForm"
            :categories="categories"
            :subcategories="allSubcategories"
          />
        </div>
      </div>
      <!-- 结束专注弹窗 -->
      <el-dialog
      v-model="stopDialogVisible"
      title="保存学习记录"
      width="600px"
      :close-on-click-modal="false"
      class="stop-dialog"
    >
      <div class="dialog-content">
        <div class="time-info">
          <div class="info-item">
            <span class="label">专注时长</span>
            <span class="value">{{ formatDuration(elapsedSeconds) }}</span>
          </div>
          <div class="info-item">
            <span class="label">开始时间</span>
            <span class="value">{{ startTimeDisplay }}</span>
          </div>
          <div class="info-item">
            <span class="label">结束时间</span>
            <span class="value">{{ endTimeDisplay }}</span>
          </div>
        </div>

        <el-form :model="stopForm" label-position="top">
          <el-form-item label="学习心情">
            <el-rate
              v-model="stopForm.mood"
              :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
              size="large"
            />
          </el-form-item>

          <el-form-item label="备注（选填）">
            <el-input
              v-model="stopForm.notes"
              type="textarea"
              :rows="4"
              placeholder="记录一下本次学习的收获或感想..."
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <template #footer>
        <el-button @click="stopDialogVisible = false" size="large">
          取消
        </el-button>
        <el-button
          type="primary"
          @click="saveRecord"
          :loading="loading"
          size="large"
        >
          保存记录
        </el-button>
      </template>
      </el-dialog>
    </PageContainer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useCategoryStore } from "@/stores/category";
import { useStageStore } from "@/stores/modules/stage";
import { useAuthStore } from "@/stores/modules/auth";
import { recordApi } from "@/api/modules/records";
import { useFocusTimer } from "@/composables/useFocusTimer";
import dayjs from "dayjs";

// 组件导入
import FocusTimer from "@/components/business/focus/FocusTimer.vue";
import FocusForm from "@/components/business/focus/FocusForm.vue";
import FocusInfo from "@/components/business/focus/FocusInfo.vue";
import FocusControls from "@/components/business/focus/FocusControls.vue";
import PageContainer from "@/components/layout/PageContainer.vue";

const router = useRouter();
const categoryStore = useCategoryStore();
const stageStore = useStageStore();
const authStore = useAuthStore();

// 使用计时器 composable
const {
  isTimerRunning,
  isPaused,
  elapsedSeconds,
  startTime: focusStartTime,
  startTimer: timerStart,
  pauseTimer: timerPause,
  resumeTimer: timerResume,
  stopTimer: timerStop,
  cancelSession: timerCancel,
  restoreState,
  clearState,
} = useFocusTimer();

// 表单数据
const focusForm = ref({
  name: "",
  categoryId: null,
  subcategoryId: null,
});

// 结束弹窗数据
const stopDialogVisible = ref(false);
const stopForm = ref({
  mood: 0,
  notes: "",
});

const endTime = ref(null);

const formRef = ref(null);
const loading = ref(false);

// 分类和子分类数据
const categories = ref([]);
const allSubcategories = ref([]); // 存储所有子分类

// 格式化时间显示
const startTimeDisplay = computed(() => {
  if (!focusStartTime.value) return "--";
  return new Date(focusStartTime.value).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
});

const endTimeDisplay = computed(() => {
  if (!endTime.value) return "--";
  return new Date(endTime.value).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
});

// 格式化时长
const formatDuration = (seconds) => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}小时${minutes}分钟${secs}秒`;
  } else if (minutes > 0) {
    return `${minutes}分钟${secs}秒`;
  } else {
    return `${secs}秒`;
  }
};

// 表单验证规则
const rules = {
  name: [
    { required: true, message: "请输入记录名称", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
  categoryId: [{ required: true, message: "请选择分类", trigger: "change" }],
  subcategoryId: [
    { required: true, message: "请选择子分类", trigger: "change" },
  ],
};

// 当前分类下可用的子分类
const availableSubcategories = computed(() => {
  if (!focusForm.value.categoryId) return [];
  return allSubcategories.value.filter(
    (sub) => sub.category_id === focusForm.value.categoryId
  );
});

// 加载数据
const loadData = async () => {
  try {
    console.log("开始加载数据...");

    // 检查登录状态
    if (!authStore.isAuthenticated) {
      console.error("用户未登录，重定向到登录页");
      ElMessage.error("请先登录");
      router.push("/login");
      return;
    }

    // 加载学习阶段
    await stageStore.fetchStages();
    console.log("当前激活阶段:", stageStore.activeStage);

    // 检查是否有激活的阶段
    if (!stageStore.activeStage) {
      ElMessage.warning("请先在阶段管理中创建并激活一个学习阶段");
      return;
    }

    // 加载分类数据（用于获取子分类）
    await categoryStore.fetchCategories();
    console.log("categoryStore.tree:", categoryStore.tree);
    categories.value = categoryStore.tree;
    console.log("categories.value:", categories.value);

    // 加载所有子分类
    await loadSubcategories();
  } catch (error) {
    console.error("加载数据失败:", error);
    ElMessage.error("加载数据失败");
  }
};

// 加载所有子分类
const loadSubcategories = async () => {
  try {
    console.log("开始加载子分类...");
    console.log("categories.value:", categories.value);

    // 从已加载的分类数据中提取所有子分类
    const subcategories = [];
    categories.value.forEach((category) => {
      console.log(`处理分类 ${category.name} (id: ${category.id})`);

      // 处理 subcategories 或 children 字段
      const subs = category.subcategories || category.children || [];
      console.log(`  子分类数量: ${subs.length}`, subs);

      if (subs.length > 0) {
        subs.forEach((sub) => {
          subcategories.push({
            id: sub.id,
            name: sub.name,
            category_id: category.id, // 使用父分类的ID作为category_id
          });
        });
      }
    });

    allSubcategories.value = subcategories;
    console.log("所有子分类:", allSubcategories.value);
  } catch (error) {
    console.error("加载子分类失败:", error);
    ElMessage.warning("加载子分类失败，但不影响其他功能");
  }
};

// 分类切换时重置子分类
const onCategoryChange = () => {
  focusForm.value.subcategoryId = null;
};

// 开始计时
const startTimer = async () => {
  try {
    await formRef.value?.validate();
    timerStart(focusForm.value);
    ElMessage.success("开始专注！保持专注，加油！");
  } catch (error) {
    console.error("表单验证失败:", error);
  }
};

// 暂停计时
const pauseTimer = () => {
  timerPause(focusForm.value);
  ElMessage.info("已暂停");
};

// 继续计时
const resumeTimer = () => {
  timerResume(focusForm.value);
  ElMessage.success("继续专注！");
};

// 显示停止确认弹窗
const showStopDialog = () => {
  endTime.value = new Date();
  timerStop();
  stopDialogVisible.value = true;
};

// 保存学习记录
const saveRecord = async () => {
  try {
    loading.value = true;

    // 检查是否有激活的阶段
    if (!stageStore.activeStage) {
      ElMessage.error("请先在阶段管理中创建并激活一个学习阶段");
      loading.value = false;
      return;
    }

    // 计算持续时间（分钟）
    const durationMinutes = Math.ceil(elapsedSeconds.value / 60);

    // 格式化时间段
    const timeSlot = `${startTimeDisplay.value}-${endTimeDisplay.value}`;

    // 保存学习记录
    const recordData = {
      stage_id: stageStore.activeStage.id,
      task: focusForm.value.name,
      subcategory_id: focusForm.value.subcategoryId,
      actual_duration: durationMinutes,
      log_date: dayjs().format("YYYY-MM-DD"),
      time_slot: timeSlot,
      mood: stopForm.value.mood,
      notes: stopForm.value.notes || "",
    };

    console.log("准备保存记录，数据:", recordData);

    const response = await recordApi.createRecord(recordData);
    console.log("保存成功，响应:", response);

    // 关闭弹窗并重置状态
    stopDialogVisible.value = false;
    stopForm.value = {
      mood: 3,
      notes: "",
    };
    focusStartTime.value = null;
    endTime.value = null;
    clearState();

    ElMessage.success("专注记录已保存！");

    setTimeout(() => {
      router.push("/records");
    }, 1500);
  } catch (error) {
    console.error("保存记录失败，完整错误:", error);
    console.error("错误详情:", {
      message: error.message,
      response: error.response,
      request: error.request,
    });

    let errorMessage = "保存记录失败";
    if (error.response) {
      // 服务器返回了错误响应
      errorMessage =
        error.response.data?.message || `服务器错误: ${error.response.status}`;
    } else if (error.request) {
      // 请求已发出但没有收到响应
      errorMessage = "网络连接失败，请检查网络或后端服务";
    } else {
      // 请求配置错误
      errorMessage = error.message || "未知错误";
    }

    ElMessage.error(errorMessage);
    loading.value = false;
  }
};

// 放弃当前专注会话
const cancelSession = async () => {
  try {
    const hours = Math.floor(elapsedSeconds.value / 3600);
    const minutes = Math.floor((elapsedSeconds.value % 3600) / 60);
    const seconds = elapsedSeconds.value % 60;
    const timeDisplay =
      hours > 0
        ? `${hours}:${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`
        : `${minutes}:${seconds.toString().padStart(2, "0")}`;

    await ElMessageBox.confirm(
      `确认放弃当前专注记录？已专注 ${timeDisplay}，数据将不会保存。`,
      "放弃记录",
      {
        confirmButtonText: "确认放弃",
        cancelButtonText: "取消",
        type: "warning",
      }
    );

    timerCancel();

    // 重置表单
    focusForm.value = {
      name: "",
      categoryId: null,
      subcategoryId: null,
      notes: "",
    };

    ElMessage.info("已放弃专注记录");
  } catch (error) {
    // 用户取消操作
    console.log("取消放弃");
  }
};

// 返回
const goBack = () => {
  router.back();
};

// 生命周期
onMounted(async () => {
  await loadData();

  // 尝试恢复之前的专注状态
  const savedFormData = restoreState();
  if (savedFormData) {
    focusForm.value = savedFormData;
    ElMessage.success("已恢复上次的专注记录");
  }
});
</script>

<style scoped lang="scss">
.focus-view {
  position: relative;
  min-height: 100vh;
  padding: clamp(1.5rem, 3vw, 3rem);
  background: var(--surface-page);
  overflow: hidden;
}

.bg-blobs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(600px at 20% 20%, rgba(99, 102, 241, 0.08), transparent 55%),
    radial-gradient(520px at 80% 70%, rgba(56, 189, 248, 0.08), transparent 55%);
  z-index: 0;
}

.focus-layout {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(320px, 360px) minmax(420px, 1fr);
  gap: clamp(1.8rem, 3vw, 3rem);
  align-items: center;
  justify-content: center;
  margin-top: clamp(1rem, 3vw, 1.5rem);

  &__timer {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    align-items: center;
  }

  &__details {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
    max-width: 620px;
    width: 100%;
  }
}

:deep(.stop-dialog) {
  .el-dialog {
    background: #ffffff;
    border: 1px solid rgba(203, 213, 225, 0.6);
    border-radius: 18px;
    box-shadow: 0 18px 44px rgba(15, 23, 42, 0.12);
  }

  .el-dialog__header {
    padding: 1.5rem 2rem;
    border-bottom: 1px solid rgba(229, 231, 235, 0.9);
  }

  .el-dialog__title {
    font-size: 1.28rem;
    font-weight: 600;
    color: #1f2937;
  }

  .el-dialog__body {
    padding: 2rem;
  }

  .el-dialog__footer {
    padding: 1.2rem 2rem;
    border-top: 1px solid rgba(229, 231, 235, 0.9);
  }
}

.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;

  .time-info {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
    padding: 1.5rem;
    border-radius: 16px;
    background: rgba(99, 102, 241, 0.08);

    .info-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.4rem;

      .label {
        font-size: 0.9rem;
        color: #55607a;
        font-weight: 500;
      }

      .value {
        font-size: 1.15rem;
        font-weight: 600;
        color: #3730a3;
        letter-spacing: 0.01em;
      }
    }
  }

  .el-form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;

    .el-form-item {
      margin-bottom: 0;
    }

    .el-form-item__label {
      font-weight: 600;
      color: #1f2937;
      margin-bottom: 0.35rem;
    }

    .el-rate {
      height: 2.6rem;
      display: flex;
      align-items: center;
    }
  }
}

@media (max-width: 768px) {
  .focus-view {
    padding: 1.5rem;
  }

  .focus-container {
    padding: 2rem 1.5rem;
  }

  .focus-layout {
    grid-template-columns: 1fr;
  }

  .dialog-content .time-info {
    grid-template-columns: 1fr;
  }
}
</style>
