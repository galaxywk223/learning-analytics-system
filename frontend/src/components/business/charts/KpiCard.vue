<template>
  <div class="kpi-card" :class="[color, dense ? 'dense' : '']">
    <div v-if="hasIcon" class="icon-wrapper">
      <slot name="icon">
        <span v-if="icon" class="emoji-icon" aria-hidden="true">{{
          icon
        }}</span>
      </slot>
    </div>
    <div class="content">
      <div class="label">
        <slot name="label">{{ label }}</slot>
      </div>
      <div class="value">
        <slot name="value">{{ displayValue }}</slot>
      </div>
    </div>
  </div>
</template>
<script setup>
import { computed, useSlots } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: "--" },
  color: { type: String, default: "primary" },
  icon: { type: String, default: "" },
  dense: { type: Boolean, default: false },
});

const slots = useSlots();

const hasIcon = computed(() => Boolean(props.icon || slots.icon));

const displayValue = computed(() => {
  if (props.value === null || props.value === undefined || props.value === "") {
    return "--";
  }
  return props.value;
});
</script>
<style scoped lang="scss">
@import "@/styles/components/kpi-card";
</style>
