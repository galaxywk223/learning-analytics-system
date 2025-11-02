<template>
  <div class="form-section">
    <!-- 分类、标签 -->
    <el-row :gutter="16">
      <el-col :span="12">
        <el-form-item label="分类" prop="category_id">
          <el-select
            v-model="form.category_id"
            placeholder="请选择分类"
            style="width: 100%"
            size="large"
            @change="handleCategoryChange"
          >
            <el-option
              v-for="item in categoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-col>
      <el-col :span="12">
        <el-form-item label="标签" prop="subcategory_id">
          <el-select
            v-model="form.subcategory_id"
            placeholder="请先选择分类"
            style="width: 100%"
            size="large"
            :disabled="!subCategoryOptions.length"
          >
            <el-option
              v-for="item in subCategoryOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
const props = defineProps({
  form: {
    type: Object,
    required: true,
  },
  categoryOptions: {
    type: Array,
    default: () => [],
  },
  subCategoryOptions: {
    type: Array,
    default: () => [],
  },
});

const emit = defineEmits(["category-change"]);

function handleCategoryChange(value) {
  // 清空子分类选择
  props.form.subcategory_id = null;
  emit("category-change", value);
}
</script>

<style scoped lang="scss">
.form-section {
  margin-bottom: 0;
}
</style>
