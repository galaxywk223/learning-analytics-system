<template>
  <div class="ios-form-group transparent">
    <!-- 笔记 -->
    <div class="ios-input-row column">
      <el-input
        v-model="localForm.notes"
        type="textarea"
        :rows="4"
        placeholder="备注..."
        resize="none"
        show-word-limit
        :maxlength="500"
        class="ios-textarea"
      />
    </div>

    <!-- 心情 -->
    <div class="ios-input-row center">
      <el-rate
        v-model="localForm.mood"
        :colors="['#99A9BF', '#F7BA2A', '#FF9900']"
        size="large"
        class="ios-rate"
      />
    </div>
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
  display: flex;
  flex-direction: column;
  gap: 16px;

  &.transparent {
    background: transparent;
  }
}

.ios-input-row {
  display: flex;

  &.column {
    flex-direction: column;
  }

  &.center {
    justify-content: center;
    padding: 10px 0;
  }
}

.ios-textarea {
  width: 100%;

  :deep(.el-textarea__inner) {
    background: rgba(118, 118, 128, 0.12);
    border: none;
    border-radius: 10px;
    padding: 12px;
    font-size: 15px;
    color: #000;
    font-family: inherit;

    &::placeholder {
      color: #8e8e93;
    }
  }

  :deep(.el-input__count) {
    background: transparent;
    color: #8e8e93;
    bottom: 8px;
    right: 12px;
  }
}

.ios-rate {
  height: 32px;

  :deep(.el-rate__icon) {
    font-size: 28px;
  }
}
</style>
