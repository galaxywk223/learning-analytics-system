<template>
  <div class="form-section">
    <!-- 任务名称 -->
    <el-form-item prop="task" class="no-label">
      <el-input
        v-model="form.task"
        placeholder="请输入任务名称"
        size="large"
        clearable
      />
    </el-form-item>

    <!-- 日期、时间段、时长 -->
    <el-row :gutter="16">
      <el-col :span="8">
        <el-form-item label="日期" prop="log_date">
          <el-date-picker
            v-model="form.log_date"
            type="date"
            placeholder="选择日期"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            size="large"
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="时间段">
          <el-input
            v-model="form.time_slot"
            placeholder="选填，如：早上、下午、9-11点"
            size="large"
            clearable
          />
        </el-form-item>
      </el-col>
      <el-col :span="8">
        <el-form-item label="实际时长" prop="actual_duration">
          <el-row :gutter="8" class="duration-row">
            <el-col :span="12">
              <div class="duration-input">
                <el-input-number
                  v-model="form.duration_hours"
                  :min="0"
                  :max="24"
                  placeholder="0"
                  size="large"
                  :controls="false"
                />
                <span class="unit-label">小时</span>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="duration-input">
                <el-input-number
                  v-model="form.duration_minutes"
                  :min="0"
                  :max="59"
                  placeholder="0"
                  size="large"
                  :controls="false"
                />
                <span class="unit-label">分钟</span>
              </div>
            </el-col>
          </el-row>
        </el-form-item>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
defineProps({
  form: {
    type: Object,
    required: true,
  },
});
</script>

<style scoped lang="scss">
.form-section {
  margin-bottom: 0;

  :deep(.el-form-item__label) {
    font-weight: 500;
    color: #333;
    margin-bottom: 8px;
  }

  .no-label {
    margin-bottom: 4px;

    :deep(.el-form-item__label) {
      display: none;
    }
  }

  .duration-row {
    width: 100%;
  }

  .duration-input {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .duration-input :deep(.el-input-number) {
    flex: 1;
    min-width: 0;
  }

  .unit-label {
    color: #6b7280;
    font-weight: 600;
    font-size: 14px;
    line-height: 1;
    white-space: nowrap;
  }
}
</style>
