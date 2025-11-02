<template>
  <div class="form-section">
    <!-- 任务名称 -->
    <el-form-item label="任务" prop="task">
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
          <el-row :gutter="8">
            <el-col :span="12">
              <el-input-number
                v-model="form.duration_hours"
                :min="0"
                :max="24"
                placeholder="小时"
                style="width: 100%"
                size="large"
              />
            </el-col>
            <el-col :span="12">
              <el-input-number
                v-model="form.duration_minutes"
                :min="0"
                :max="59"
                placeholder="分钟"
                style="width: 100%"
                size="large"
              />
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
}
</style>
