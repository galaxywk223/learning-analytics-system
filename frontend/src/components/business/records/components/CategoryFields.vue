<template>
  <div class="ios-form-group">
    <!-- 分类和子分类 (Split Row) -->
    <div class="ios-split-row">
      <!-- 分类 -->
      <el-form-item prop="category_id" class="ios-input-row half">
        <span class="ios-label">分类</span>
        <el-select
          v-model="localForm.category_id"
          placeholder=""
          class="ios-select"
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

      <!-- 子分类 -->
      <el-form-item prop="subcategory_id" class="ios-input-row half">
        <span class="ios-label">子分类</span>
        <el-select
          v-model="localForm.subcategory_id"
          placeholder=""
          class="ios-select"
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
    </div>
  </div>
</template>

<script setup>
import { reactive, watch, nextTick, ref } from "vue";

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

const emit = defineEmits(["update:form", "category-change"]);

const localForm = reactive({});
const syncing = ref(false);

watch(
  () => props.form,
  (value) => {
    syncing.value = true;
    Object.assign(localForm, value || {});
    nextTick(() => {
      syncing.value = false;
    });
  },
  { immediate: true },
);

watch(
  () => [localForm.category_id, localForm.subcategory_id],
  () => {
    if (syncing.value) return;
    emit("update:form", { ...localForm });
  },
);

function handleCategoryChange(value) {
  // 清空子分类选择
  localForm.subcategory_id = null;
  emit("category-change", value);
}
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

.ios-select {
  flex: 1;

  :deep(.el-input__wrapper) {
    background-color: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
  }

  :deep(.el-input__inner) {
    font-size: 17px;
    color: #007aff;
    text-align: right;
    height: auto;
    line-height: normal;
  }

  :deep(.el-select__caret) {
    color: #c7c7cc;
    margin-left: 4px;
    font-size: 14px;
  }
}
</style>
