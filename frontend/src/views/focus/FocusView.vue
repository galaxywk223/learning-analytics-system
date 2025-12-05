<template>
  <div class="focus-view">

    <PageContainer
      :title="{ icon: '🎯', text: isTimerRunning ? '专注中' : '专注计时' }"
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
        :show-close="false"
        width="320px"
        class="ios-dialog-modal"
        align-center
        destroy-on-close
      >
        <div class="ios-dialog-content">
          <div class="ios-dialog-header">
            <h3 class="ios-dialog-title">保存学习记录</h3>
            <p class="ios-dialog-subtitle">本次专注已结束</p>
          </div>

          <div class="ios-summary-card">
            <div class="summary-row">
              <div class="summary-item">
                <span class="label">时长</span>
                <span class="value highlight">{{ formatDuration(elapsedSeconds) }}</span>
              </div>
              <div class="divider-vertical"></div>
              <div class="summary-item">
                <span class="label">时间段</span>
                <span class="value">{{ startTimeDisplay }} - {{ endTimeDisplay }}</span>
              </div>
            </div>
          </div>

          <div class="ios-form-group">
            <div class="form-row">
              <span class="row-label">心情</span>
              <el-rate
                v-model="stopForm.mood"
                :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
                size="large"
                class="ios-rate"
              />
            </div>
            <div class="form-row column">
              <textarea
                v-model="stopForm.notes"
                class="ios-textarea"
                rows="3"
                placeholder="写点什么..."
                maxlength="200"
              ></textarea>
            </div>
          </div>

          <div class="form-footer">
            <div class="pill-btn-group-horizontal">
              <button class="pill-btn secondary" @click="stopDialogVisible = false">
                取消
              </button>
              <button class="pill-btn primary" @click="saveRecord" :disabled="loading">
                保存
              </button>
            </div>
          </div>
        </div>
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
    return `${hours}h ${minutes}m`;
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  } else {
    return `${secs}s`;
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
  background: transparent;
  overflow: hidden;

  &::after {
    display: none;
  }
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

/* iOS Dialog Styles */
:deep(.ios-dialog-modal) {
  .el-dialog {
    background: rgba(255, 255, 255, 0.98);
    border-radius: 14px;
    box-shadow: 0 0 0 1px rgba(0,0,0,0.05), 0 20px 40px rgba(0,0,0,0.2);
    padding: 0;
    overflow: hidden;
    
    .el-dialog__header {
      display: none; /* Hide default header */
    }
    
    .el-dialog__body {
      padding: 0;
    }
  }
}

.ios-dialog-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.ios-dialog-header {
  padding: 24px 16px 16px;
  
  .ios-dialog-title {
    font-size: 17px;
    font-weight: 600;
    color: #000;
    margin: 0 0 4px;
    line-height: 1.3;
  }
  
  .ios-dialog-subtitle {
    font-size: 13px;
    color: #8e8e93;
    margin: 0;
  }
}

.ios-summary-card {
  width: 100%;
  padding: 0 16px;
  margin-bottom: 20px;
  
  .summary-row {
    background: rgba(118, 118, 128, 0.12);
    border-radius: 10px;
    padding: 12px;
    display: flex;
    justify-content: space-around;
    align-items: center;
  }
  
  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 2px;
    
    .label {
      font-size: 11px;
      color: #8e8e93;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    
    .value {
      font-size: 15px;
      font-weight: 500;
      color: #000;
      
      &.highlight {
        color: #007aff;
        font-weight: 600;
      }
    }
  }
  
  .divider-vertical {
    width: 1px;
    height: 24px;
    background: rgba(60, 60, 67, 0.18);
  }
}

.ios-form-group {
  width: 100%;
  padding: 0 16px;
  margin-bottom: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  
  .form-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    &.column {
      flex-direction: column;
      align-items: stretch;
    }
    
    .row-label {
      font-size: 15px;
      color: #000;
    }
  }
}

.ios-textarea {
  width: 100%;
  background: rgba(118, 118, 128, 0.12);
  border: none;
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 15px;
  color: #000;
  resize: none;
  outline: none;
  font-family: inherit;
  
  &::placeholder {
    color: #8e8e93;
  }
  
  &:focus {
    background: rgba(118, 118, 128, 0.18);
  }
}

.form-footer {
  padding: 16px 24px 24px;
  background: white;
  border-top: 1px solid #f3f4f6;
  margin-top: auto;
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
}
</style>
