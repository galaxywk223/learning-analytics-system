<template>
  <div class="ios-list-container">
    <div class="ios-list">
      <div
        v-for="log in logs"
        :key="log.id"
        class="ios-list-item"
        :style="getCategoryTheme(log)"
      >
        <div class="item-content">
          <div class="col-time">{{ log.time_slot }}</div>

          <div class="col-task">
            <span class="category-dot"></span>
            <span class="task-name" :title="log.task">{{ log.task }}</span>
          </div>

          <div class="col-category">
            <span
              class="category-path"
              :title="getCategoryPath(log)"
              :class="{ 'is-uncategorized': !log.subcategory }"
            >
              <span class="category-parent">{{ getCategoryParent(log) }}</span>
              <span class="category-separator">/</span>
              <span class="category-child">{{ getCategoryChild(log) }}</span>
            </span>
          </div>

          <div class="col-note">
            <button
              v-if="log.notes"
              type="button"
              class="notes-toggle"
              title="查看备注"
              @click.stop="$emit('toggle-notes', log.id)"
            >
              <Icon icon="lucide:message-square" class="notes-icon" />
            </button>
          </div>

          <div class="col-duration">{{ log.actual_duration }} min</div>

          <div class="col-mood" :title="moodTitle(log.mood)">
            {{ moodEmoji(log.mood) }}
          </div>

          <div class="col-actions">
            <el-button
              link
              size="small"
              class="action-btn"
              title="编辑"
              @click="$emit('edit-record', log)"
            >
              <Icon icon="lucide:pencil" />
            </el-button>
            <el-button
              link
              size="small"
              type="danger"
              class="action-btn delete"
              title="删除"
              @click="$emit('delete-record', log)"
            >
              <Icon icon="lucide:trash-2" />
            </el-button>
          </div>
        </div>

        <!-- Expanded Notes -->
        <div
          v-if="log.notes && expandedNotes.includes(log.id)"
          class="expanded-notes"
        >
          {{ log.notes }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Icon } from "@iconify/vue";

const props = defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  expandedNotes: {
    type: Array,
    default: () => [],
  },
  colorSeed: {
    type: String,
    default: "",
  },
});

defineEmits(["toggle-notes", "edit-record", "delete-record"]);

const hashString = (value) => {
  let hash = 0;
  for (let index = 0; index < value.length; index += 1) {
    hash = (hash << 5) - hash + value.charCodeAt(index);
    hash |= 0;
  }
  return Math.abs(hash);
};

const paletteFamilies = [
  { primary: 146, secondary: 112, accent: 162 },
  { primary: 15, secondary: 44, accent: 28 },
  { primary: 206, secondary: 232, accent: 194 },
  { primary: 278, secondary: 318, accent: 294 },
  { primary: 338, secondary: 8, accent: 352 },
  { primary: 88, secondary: 126, accent: 104 },
  { primary: 184, secondary: 206, accent: 170 },
  { primary: 44, secondary: 76, accent: 56 },
  { primary: 228, secondary: 256, accent: 242 },
  { primary: 354, secondary: 26, accent: 10 },
  { primary: 302, secondary: 334, accent: 316 },
  { primary: 122, secondary: 150, accent: 136 },
  { primary: 192, secondary: 220, accent: 206 },
  { primary: 58, secondary: 32, accent: 74 },
];

const getCategoryTheme = (log) => {
  const parentCategoryId = log?.subcategory?.category_id || 0;
  const parentCategoryName = getCategoryParent(log);
  const seedBase = `${props.colorSeed}:${parentCategoryId}:${parentCategoryName}`;
  const seed = hashString(seedBase);
  const family = paletteFamilies[seed % paletteFamilies.length];
  const variant = Math.floor(seed / paletteFamilies.length);
  const saturationBoost = variant % 6;
  const lightnessShift = variant % 5;

  const primarySaturation = 72 + saturationBoost;
  const secondarySaturation = 68 + ((variant + 2) % 7);
  const accentSaturation = 78 + ((variant + 1) % 5);
  return {
    "--record-accent": `hsl(${family.accent} ${accentSaturation}% 55%)`,
    "--record-accent-soft": `hsla(${family.accent}, ${accentSaturation}%, 55%, 0.18)`,
    "--record-border": `hsla(${family.primary}, ${primarySaturation - 14}%, 50%, 0.2)`,
    "--record-border-strong": `hsla(${family.accent}, ${accentSaturation}%, 62%, 0.32)`,
    "--record-bg-start": `hsla(${family.primary}, ${primarySaturation}%, ${97 - lightnessShift * 0.4}%, 0.98)`,
    "--record-bg-end": `hsla(${family.secondary}, ${secondarySaturation}%, ${93 - lightnessShift * 0.5}%, 0.96)`,
    "--record-bg-dark-start": `hsla(${family.primary}, ${primarySaturation}%, ${18 + lightnessShift}%, 0.9)`,
    "--record-bg-dark-end": `hsla(${family.secondary}, ${secondarySaturation}%, ${12 + lightnessShift}%, 0.94)`,
    "--record-border-dark": `hsla(${family.accent}, ${accentSaturation}%, 66%, 0.28)`,
    "--record-glow": `hsla(${family.accent}, ${accentSaturation}%, 58%, 0.22)`,
    "--record-chip-bg": `hsla(${family.primary}, ${primarySaturation - 14}%, 97%, 0.78)`,
    "--record-chip-border": `hsla(${family.accent}, ${accentSaturation - 6}%, 52%, 0.34)`,
    "--record-chip-parent": `hsl(${family.accent} ${accentSaturation}% 46%)`,
    "--record-chip-child": `hsl(${family.secondary} ${secondarySaturation - 10}% 33%)`,
    "--record-chip-separator": `hsla(${family.primary}, ${primarySaturation - 12}%, 32%, 0.72)`,
    "--record-chip-parent-dark": `hsl(${family.accent} ${accentSaturation}% 76%)`,
    "--record-chip-child-dark": `hsla(${family.secondary}, ${secondarySaturation - 6}%, 88%, 0.92)`,
    "--record-chip-separator-dark": `hsla(${family.secondary}, ${secondarySaturation - 8}%, 82%, 0.72)`,
    "--record-shadow": `0 18px 36px -28px hsla(${family.primary}, ${primarySaturation}%, 12%, 0.62)`,
  };
};

const getCategoryParent = (log) =>
  log?.subcategory?.category?.name || "未分类";

const getCategoryChild = (log) => log?.subcategory?.name || "未分类";

const getCategoryPath = (log) => {
  return `${getCategoryParent(log)} / ${getCategoryChild(log)}`;
};

const moodEmoji = (mood) => {
  const moods = {
    5: "😃",
    4: "😊",
    3: "😐",
    2: "😟",
    1: "😠",
  };
  return moods[mood] || "⚪️";
};

const moodTitle = (mood) => {
  if (!mood) return "心情：未记录";
  return `心情：${mood}/5`;
};
</script>

<style scoped lang="scss">
.ios-list-container {
  width: 100%;
}

.ios-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ios-list-item {
  position: relative;
  overflow: hidden;
  border-radius: 16px;
  padding: 12px 14px;
  border: 1px solid var(--record-border, transparent);
  background:
    radial-gradient(circle at top left, var(--record-accent-soft, rgba(99, 102, 241, 0.16)) 0%, transparent 34%),
    linear-gradient(118deg, var(--record-bg-start, rgba(255, 255, 255, 0.96)) 0%, var(--record-bg-end, rgba(248, 250, 252, 0.96)) 100%);
  box-shadow: var(--record-shadow, 0 16px 32px -28px rgba(15, 23, 42, 0.45));
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;

  &::before {
    content: "";
    position: absolute;
    left: 0;
    top: 11px;
    bottom: 11px;
    width: 4px;
    border-radius: 999px;
    background: linear-gradient(
      180deg,
      var(--record-accent, var(--color-primary)) 0%,
      color-mix(in srgb, var(--record-accent, var(--color-primary)) 65%, #ffffff) 100%
    );
    opacity: 0.95;
  }

  &::after {
    content: "";
    position: absolute;
    inset: 0;
    pointer-events: none;
    background: linear-gradient(
      180deg,
      rgba(255, 255, 255, 0.08) 0%,
      rgba(255, 255, 255, 0) 38%
    );
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow:
      0 24px 44px -30px rgba(15, 23, 42, 0.48),
      var(--record-shadow, 0 16px 32px -28px rgba(15, 23, 42, 0.45));
    border-color: var(--record-border-strong, var(--record-border, transparent));

    .col-actions {
      opacity: 1;
    }
  }
}

.item-content {
  display: grid;
  align-items: center;
  grid-template-columns: 148px minmax(180px, 1.15fr) minmax(220px, 0.92fr) 40px 92px 50px 66px;
  column-gap: 14px;
  min-height: 42px;
  padding-left: 8px;
}

.col-time {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.col-task {
  min-width: 0;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  column-gap: 12px;

  .category-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--record-accent, var(--color-primary));
    box-shadow:
      0 0 0 6px var(--record-accent-soft, rgba(99, 102, 241, 0.16)),
      0 0 18px -8px var(--record-accent, var(--color-primary));
  }

  .task-name {
    font-size: 17px;
    font-weight: 700;
    color: var(--color-text-base);
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.col-category {
  min-width: 0;

  .category-path {
    font-size: 14px;
    min-width: 0;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    gap: 8px;
    width: 100%;
    padding: 8px 14px;
    border-radius: 999px;
    white-space: nowrap;
    overflow: hidden;
    background: var(--record-chip-bg, rgba(99, 102, 241, 0.12));
    border: 1px solid var(--record-chip-border, rgba(99, 102, 241, 0.24));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.1),
      0 10px 20px -22px var(--record-glow, rgba(99, 102, 241, 0.25));

    &.is-uncategorized {
      opacity: 0.82;
    }
  }

  .category-parent,
  .category-child,
  .category-separator {
    display: inline-block;
    min-width: 0;
  }

  .category-parent {
    color: var(--record-chip-parent, var(--record-accent, var(--color-primary)));
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .category-separator {
    color: var(--record-chip-separator, color-mix(in srgb, var(--record-chip-parent, var(--record-accent)) 48%, var(--color-text-muted)));
    flex-shrink: 0;
  }

  .category-child {
    color: var(--record-chip-child, var(--color-text-secondary));
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.col-note {
  display: flex;
  justify-content: center;

  .notes-toggle {
    width: 32px;
    height: 32px;
    border-radius: 10px;
    border: 1px solid var(--record-chip-border, rgba(99, 102, 241, 0.24));
    background: color-mix(
      in srgb,
      var(--record-chip-bg, rgba(99, 102, 241, 0.12)) 82%,
      transparent
    );
    color: var(--record-accent, var(--color-primary));
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition:
      transform 0.18s ease,
      border-color 0.18s ease,
      background-color 0.18s ease;

    &:hover {
      transform: translateY(-1px);
      border-color: var(--record-border-strong, var(--record-chip-border));
      background: color-mix(
        in srgb,
        var(--record-accent-soft, rgba(99, 102, 241, 0.18)) 80%,
        rgba(255, 255, 255, 0.05)
      );
    }

    .notes-icon {
      width: 16px;
      height: 16px;
    }
  }
}

.col-duration {
  font-size: 17px;
  font-weight: 700;
  color: var(--color-text-base);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.col-mood {
  text-align: center;
  font-size: 24px;
  line-height: 1;
}

.col-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s ease;

  .action-btn {
    padding: 4px;
    height: 30px;
    width: 30px;
    border-radius: 10px;
    color: var(--color-text-secondary);

    &:hover {
      color: var(--color-primary);
      background-color: color-mix(
        in srgb,
        var(--record-accent-soft, rgba(99, 102, 241, 0.16)) 88%,
        rgba(255, 255, 255, 0.06)
      );
    }

    &.delete:hover {
      color: var(--color-error);
      background-color: rgba(255, 59, 48, 0.1);
    }

    :deep(.iconify) {
      width: 18px;
      height: 18px;
    }
  }
}

.expanded-notes {
  margin-top: 10px;
  margin-left: 156px;
  padding: 12px 14px;
  border: 1px solid var(--record-chip-border, rgba(99, 102, 241, 0.2));
  border-radius: 14px;
  background: color-mix(
    in srgb,
    var(--record-chip-bg, rgba(99, 102, 241, 0.12)) 74%,
    rgba(15, 23, 42, 0.08)
  );
  font-size: 14px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.ios-list-item:hover {
  filter: brightness(0.99);
}

[data-theme="dark"] .ios-list-item {
  background:
    radial-gradient(circle at top left, var(--record-accent-soft, rgba(99, 102, 241, 0.16)) 0%, transparent 34%),
    linear-gradient(
      118deg,
      var(--record-bg-dark-start, rgba(51, 65, 85, 0.72)) 0%,
      var(--record-bg-dark-end, rgba(30, 41, 59, 0.62)) 100%
    );
  border-color: var(--record-border-dark, rgba(148, 163, 184, 0.2));
}

[data-theme="dark"] .col-category .category-path,
[data-theme="dark"] .col-note .notes-toggle,
[data-theme="dark"] .expanded-notes {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.04),
    0 12px 24px -24px var(--record-glow, rgba(99, 102, 241, 0.22));
}

[data-theme="dark"] .col-time,
[data-theme="dark"] .category-child {
  color: rgba(226, 232, 240, 0.78);
}

[data-theme="dark"] .col-category .category-parent {
  color: var(--record-chip-parent-dark, var(--record-chip-parent, var(--record-accent)));
}

[data-theme="dark"] .col-category .category-child {
  color: var(--record-chip-child-dark, rgba(226, 232, 240, 0.78));
}

[data-theme="dark"] .col-category .category-separator {
  color: var(--record-chip-separator-dark, rgba(226, 232, 240, 0.62));
}

@media (max-width: 1280px) {
  .item-content {
    grid-template-columns: 132px minmax(160px, 1fr) minmax(180px, 0.9fr) 40px 84px 48px 58px;
    column-gap: 12px;
  }

  .col-duration {
    font-size: 16px;
  }
}

@media (max-width: 960px) {
  .item-content {
    grid-template-columns: 116px minmax(0, 1fr) 78px 40px;
    grid-template-areas:
      "time task duration mood"
      "category category note actions";
    row-gap: 10px;
  }

  .col-time {
    grid-area: time;
  }

  .col-task {
    grid-area: task;
  }

  .col-category {
    grid-area: category;
  }

  .col-note {
    grid-area: note;
    justify-content: flex-end;
  }

  .col-duration {
    grid-area: duration;
  }

  .col-mood {
    grid-area: mood;
  }

  .col-actions {
    grid-area: actions;
    opacity: 1;
  }

  .expanded-notes {
    margin-left: 0;
  }
}

@media (max-width: 640px) {
  .ios-list-item {
    padding: 12px;
  }

  .item-content {
    grid-template-columns: minmax(0, 1fr) auto auto;
    grid-template-areas:
      "task duration mood"
      "time note actions"
      "category category category";
    padding-left: 6px;
  }

  .col-time {
    font-size: 14px;
  }

  .col-task .task-name {
    font-size: 16px;
  }

  .col-category .category-path {
    padding: 7px 12px;
    font-size: 13px;
  }
}
</style>
