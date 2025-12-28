<template>
  <div class="page-container" :class="customClass">
    <header
      v-if="
        normalizedTitle.text ||
        normalizedTitle.icon ||
        $slots.actions ||
        $slots.header
      "
      class="page-header"
    >
      <div v-if="!$slots.header" class="page-header__titles">
        <h1
          v-if="normalizedTitle.text || normalizedTitle.icon"
          class="page-title"
        >
          <span
            v-if="normalizedTitle.icon"
            class="emoji-icon"
            aria-hidden="true"
          >
            {{ normalizedTitle.icon }}
          </span>
          <span>{{ normalizedTitle.text }}</span>
        </h1>
        <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
      </div>
      <div v-else class="page-header__custom">
        <slot name="header" />
      </div>
      <div v-if="$slots.actions" class="page-header__actions">
        <slot name="actions" />
      </div>
    </header>
    <div class="page-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  title?: string | { icon?: string; text: string };
  subtitle?: string;
  customClass?: string | string[] | Record<string, boolean>;
}>();

const normalizedTitle = computed(() => {
  if (!props.title) return { icon: "", text: "" };
  if (typeof props.title === "string") {
    return { icon: "", text: props.title };
  }
  return { icon: props.title.icon || "", text: props.title.text || "" };
});
</script>

<style scoped lang="scss">
.page-container {
  padding: 32px;
  min-height: 100%;
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  box-sizing: border-box;
}

.page-header {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: var(--page-header-height);
  margin: 24px 0 20px;
  text-align: center;
}

.page-header__titles,
.page-header__custom {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: center;
}

.page-title {
  margin: 0;
  font-size: clamp(2rem, 4vw, 2.4rem);
  font-weight: 700;
  line-height: 1.25;
  color: var(--color-text-heading, #1f2937);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.page-subtitle {
  margin: 0;
  font-size: 1rem;
  color: var(--color-text-secondary, #6b7280);
}

.page-header__actions {
  display: flex;
  align-items: center;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
  min-height: 40px;
}

.page-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
