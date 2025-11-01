<template>
  <div class="kpi-card" :class="color">
    <div class="icon-wrapper">
      <slot name="icon">
        <span v-if="icon">{{ icon }}</span>
      </slot>
    </div>
    <div class="content">
      <div class="value">{{ value || "--" }}</div>
      <div class="label">{{ label }}</div>
    </div>
  </div>
</template>
<script setup>
const props = defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: "--" },
  color: { type: String, default: "primary" },
  icon: { type: String, default: "" },
});
</script>
<style scoped lang="scss">
@import "@/styles/components/kpi-card";
</style>
