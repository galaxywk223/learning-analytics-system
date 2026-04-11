<template>
  <div
    class="page-container"
    :class="[
      customClass,
      { 'page-container--fill-height': fillHeight },
      `page-container--${resolvedMaxWidth}`,
      `page-container--${density}`,
      `page-container--header-${headerAlign}`,
      `page-container--variant-${headerVariant}`,
    ]"
    :style="containerStyle"
  >
    <header
      v-if="
        normalizedTitle.text ||
        normalizedTitle.icon ||
        subtitle ||
        $slots.header ||
        $slots.actions ||
        $slots.filters
      "
      class="page-header"
      :class="{ 'page-header--sticky': stickyActions && ($slots.actions || $slots.filters) }"
    >
      <div v-if="!$slots.header" class="page-header__main">
        <div class="page-header__titles">
          <div
            v-if="normalizedTitle.text || normalizedTitle.icon"
            class="page-title-wrap"
          >
            <span v-if="normalizedTitle.icon" class="page-title__icon">
              <Icon
                v-if="normalizedTitle.iconKind === 'iconify'"
                :icon="normalizedTitle.icon"
              />
              <span v-else aria-hidden="true">{{ normalizedTitle.icon }}</span>
            </span>
            <div class="page-title__copy">
              <h1 class="page-title">{{ normalizedTitle.text }}</h1>
              <p v-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
            </div>
          </div>
          <p v-else-if="subtitle" class="page-subtitle">{{ subtitle }}</p>
        </div>

        <div v-if="$slots.actions" class="page-header__actions">
          <slot name="actions" />
        </div>
      </div>

      <div v-else class="page-header__custom">
        <slot name="header" />
      </div>

      <div v-if="$slots.filters" class="page-header__filters">
        <slot name="filters" />
      </div>
    </header>

    <div class="page-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Icon } from "@iconify/vue";

type MaxWidth = number | "narrow" | "default" | "wide" | "full";
type HeaderAlign = "left" | "center";
type HeaderVariant = "default" | "hero" | "compact";
type Density = "comfortable" | "compact";

const props = withDefaults(
  defineProps<{
    title?: string | { icon?: string; text: string };
    subtitle?: string;
    customClass?: string | string[] | Record<string, boolean>;
    maxWidth?: MaxWidth;
    headerAlign?: HeaderAlign;
    headerVariant?: HeaderVariant;
    density?: Density;
    stickyActions?: boolean;
    fillHeight?: boolean;
  }>(),
  {
    maxWidth: "default",
    headerAlign: "left",
    headerVariant: "default",
    density: "comfortable",
    stickyActions: false,
    fillHeight: false,
  },
);

const normalizedTitle = computed(() => {
  if (!props.title) {
    return { icon: "", iconKind: "emoji", text: "" } as const;
  }

  if (typeof props.title === "string") {
    return { icon: "", iconKind: "emoji", text: props.title } as const;
  }

  const icon = props.title.icon || "";
  return {
    icon,
    iconKind: icon.includes(":") ? "iconify" : "emoji",
    text: props.title.text || "",
  } as const;
});

const resolvedMaxWidth = computed(() =>
  typeof props.maxWidth === "number" ? "custom" : props.maxWidth,
);

const containerStyle = computed(() =>
  typeof props.maxWidth === "number"
    ? { "--page-container-max-width": `${props.maxWidth}px` }
    : undefined,
);
</script>

<style scoped lang="scss">
.page-container {
  --page-container-max-width: var(--page-max-width-default);
  width: min(100%, var(--page-container-max-width));
  margin: 0 auto;
  padding: var(--page-padding-y) var(--page-padding-x) calc(var(--page-padding-y) + 20px);
}

.page-container--fill-height {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.page-container--narrow {
  --page-container-max-width: var(--page-max-width-narrow);
}

.page-container--wide {
  --page-container-max-width: var(--page-max-width-wide);
}

.page-container--full {
  --page-container-max-width: 100%;
}

.page-container--compact {
  padding-top: 18px;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 22px;
}

.page-header--sticky {
  position: sticky;
  top: calc(var(--topbar-height) + 10px);
  z-index: 12;
}

.page-header__main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px 24px;
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-subtle);
  background:
    radial-gradient(circle at top right, color-mix(in srgb, var(--brand-primary) 9%, transparent) 0%, transparent 26%),
    linear-gradient(180deg, color-mix(in srgb, var(--bg-elevated) 92%, white) 0%, var(--bg-surface) 100%);
  box-shadow: var(--shadow-2);
}

.page-container--variant-compact .page-header__main {
  padding: 18px 20px;
  border-radius: var(--radius-lg);
}

.page-container--variant-hero .page-header__main {
  padding: clamp(24px, 4vw, 34px);
}

.page-header__titles,
.page-header__custom {
  min-width: 0;
}

.page-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  min-width: 0;
}

.page-title__icon {
  width: 44px;
  height: 44px;
  border-radius: 15px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: color-mix(in srgb, var(--brand-primary) 14%, var(--bg-surface));
  color: var(--brand-primary);
  box-shadow: inset 0 1px 0 var(--glass-line);
}

.page-title__icon :deep(svg) {
  width: 20px;
  height: 20px;
}

.page-title__copy {
  min-width: 0;
}

.page-title {
  margin: 0;
  color: var(--text-primary);
  font-size: clamp(1.55rem, 2.8vw, 2.25rem);
  line-height: 1.1;
  letter-spacing: -0.04em;
}

.page-subtitle {
  margin: 8px 0 0;
  color: var(--text-secondary);
  font-size: 0.98rem;
  line-height: 1.55;
}

.page-header__actions,
.page-header__filters {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.page-header__actions {
  justify-content: flex-end;
}

.page-header__filters {
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
  background: color-mix(in srgb, var(--bg-surface) 86%, var(--brand-primary-soft));
  box-shadow: var(--shadow-1);
}

.page-body {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.page-container--fill-height .page-body {
  flex: 1;
  min-height: 0;
}

.page-container--header-center .page-header__main,
.page-container--header-center .page-header__custom {
  text-align: center;
  justify-content: center;
}

.page-container--header-center .page-title-wrap {
  justify-content: center;
}

.page-container--header-center .page-header__actions {
  justify-content: center;
}

@media (max-width: 900px) {
  .page-header__main {
    flex-direction: column;
    align-items: flex-start;
  }

  .page-header__actions {
    width: 100%;
    justify-content: flex-start;
  }

  .page-header--sticky {
    position: static;
  }
}
</style>
