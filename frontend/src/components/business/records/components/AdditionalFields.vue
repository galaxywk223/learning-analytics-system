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
        :colors="[
          'var(--color-text-muted)',
          'var(--color-warning)',
          'var(--color-warning)',
        ]"
        size="large"
        class="ios-rate"
      />
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
});

const emit = defineEmits(["update:form"]);
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
  () => [localForm.notes, localForm.mood],
  () => {
    if (syncing.value) return;
    emit("update:form", { ...localForm });
  },
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
    background: var(--surface-card-muted);
    border: 1px solid var(--color-border-input);
    border-radius: 10px;
    padding: 12px;
    font-size: 15px;
    color: var(--color-text-heading);
    font-family: inherit;

    &::placeholder {
      color: var(--color-text-muted);
    }
  }

  :deep(.el-input__count) {
    background: transparent;
    color: var(--color-text-muted);
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
