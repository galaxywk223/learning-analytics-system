<template>
  <div class="ios-form-group">
    <!-- 任务名称 -->
    <el-form-item prop="task" class="ios-input-row">
      <el-input
        v-model="localForm.task"
        placeholder="任务名称"
        class="ios-input"
      />
    </el-form-item>

    <!-- 日期和时间段 (Split Row) -->
    <div class="ios-split-row">
      <!-- 日期 -->
      <el-form-item prop="log_date" class="ios-input-row half">
        <el-date-picker
          v-model="localForm.log_date"
          type="date"
          placeholder="日期"
          value-format="YYYY-MM-DD"
          class="ios-date-picker"
          :clearable="false"
        />
      </el-form-item>

      <!-- 时间段 -->
      <el-form-item class="ios-input-row half">
        <el-input
          v-model="localForm.time_slot"
          placeholder="时间段"
          class="ios-input right-align"
        />
      </el-form-item>
    </div>

    <!-- 实际时长 -->
    <el-form-item prop="actual_duration" class="ios-input-row">
      <span class="ios-label">时长</span>
      <div class="duration-group">
        <div class="duration-item">
          <el-input-number
            v-model="localForm.duration_hours"
            :min="0"
            :max="24"
            class="ios-number-input"
            placeholder=""
          />
          <span class="unit">小时</span>
        </div>
        <div class="duration-item">
          <el-input-number
            v-model="localForm.duration_minutes"
            :min="0"
            :max="59"
            class="ios-number-input"
            placeholder=""
          />
          <span class="unit">分钟</span>
        </div>
      </div>
    </el-form-item>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from "vue";

const props = defineProps({
  form: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["update:form"]);

const localForm = ref({});
const syncing = ref(false);

watch(
  () => props.form,
  (value) => {
    syncing.value = true;
    localForm.value = { ...(value || {}) };
    nextTick(() => {
      syncing.value = false;
    });
  },
  { deep: true, immediate: true },
);

watch(
  localForm,
  (value) => {
    if (syncing.value) return;
    emit("update:form", { ...(value || {}) });
  },
  { deep: true },
);
</script>

<style scoped lang="scss">
.ios-form-group {
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}

.ios-split-row {
  display: flex;
  align-items: center;
  position: relative;
  min-height: 56px;
}

.ios-input-row {
  margin-bottom: 0;
  display: flex;
  align-items: center;
  padding: 14px 16px;
  min-height: 56px;
  position: relative;
  flex: 1;

  &.half {
    flex: 1;
    min-width: 0;
    padding: 14px 16px;
  }

  :deep(.el-form-item__content) {
    flex: 1;
    display: flex;
    justify-content: space-between;
    align-items: center;
    line-height: normal;
    margin-left: 0 !important;
    min-width: 0;
  }

  /* Hide default error message */
  :deep(.el-form-item__error) {
    display: none;
  }
}

.ios-label {
  font-size: 17px;
  color: #000;
  margin-right: 8px;
  white-space: nowrap;
  font-weight: 400;
}

.ios-input {
  width: 100%;

  :deep(.el-input__wrapper) {
    background-color: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    border: none !important;
  }

  :deep(.el-input__inner) {
    font-size: 17px;
    color: #000;
    height: auto;
    line-height: normal;
    text-align: left;
    padding: 0 !important;
    border: none !important;
  }

  &.right-align :deep(.el-input__inner) {
    text-align: right;
    color: #8e8e93;
  }
}

.ios-date-picker {
  width: auto;
  flex: 1;

  :deep(.el-input__wrapper) {
    background-color: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    justify-content: flex-end;
  }

  :deep(.el-input__inner) {
    font-size: 17px;
    color: #007aff;
    text-align: right;
    cursor: pointer;
    height: auto;
    padding: 0 !important;
  }

  :deep(.el-input__prefix) {
    display: none;
  }
}

.duration-group {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  flex: 1;
  align-items: center;
}

.duration-item {
  display: flex;
  align-items: center;
  gap: 4px;

  .unit {
    font-size: 15px;
    color: #8e8e93;
  }
}

.ios-number-input {
  width: 100px; /* 增加宽度以容纳按钮 */

  :deep(.el-input__wrapper) {
    background-color: rgba(118, 118, 128, 0.12) !important;
    box-shadow: none !important;
    padding: 0 !important;
    border-radius: 8px;
  }

  :deep(.el-input__inner) {
    text-align: center;
    height: 32px;
    line-height: 32px;
    font-size: 16px;
    color: #000;
    padding: 0 !important;
  }

  :deep(.el-input-number__decrease),
  :deep(.el-input-number__increase) {
    background: transparent;
    border: none;
    color: #007aff;
    width: 28px;

    &:hover {
      color: #0056b3;
      background: rgba(0, 0, 0, 0.05);
    }
  }
}
</style>
