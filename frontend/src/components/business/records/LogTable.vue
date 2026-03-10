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
          <!-- 1. Time -->
          <div class="col-time">{{ log.time_slot }}</div>

          <!-- 2. Task & Category -->
          <div class="col-main">
            <span v-if="log.subcategory" class="category-dot"></span>
            <span class="task-name" :title="log.task">{{ log.task }}</span>
            <span
              v-if="log.subcategory"
              class="category-path"
              :title="getCategoryPath(log)"
            >
              <span class="category-parent">
                {{ log.subcategory.category?.name || "未分类" }}
              </span>
              <span class="category-separator">/</span>
              <span class="category-child">{{ log.subcategory.name }}</span>
            </span>
            <!-- Notes Icon (Click to toggle) -->
            <span
              v-if="log.notes"
              class="notes-icon-wrapper"
              title="查看备注"
              @click.stop="$emit('toggle-notes', log.id)"
            >
              <Icon icon="lucide:message-square" class="notes-icon" />
            </span>
          </div>

          <!-- 3. Duration -->
          <div class="col-duration">{{ log.actual_duration }} min</div>

          <!-- 3.5 Mood -->
          <div class="col-mood" :title="moodTitle(log.mood)">
            {{ moodEmoji(log.mood) }}
          </div>

          <!-- 4. Actions (Hover/Right) -->
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

const getCategoryTheme = (log) => {
  const categoryName =
    log?.subcategory?.category?.name ||
    log?.subcategory?.name ||
    "未分类";
  const seedBase = `${props.colorSeed}:${log?.subcategory?.category_id || 0}:${categoryName}`;
  const seed = hashString(seedBase);

  const hue = seed % 360;
  const accentHue = (hue + 18 + (seed % 37)) % 360;
  const tagLightness = 46 + (seed % 8);
  const tagTextColor = hue >= 42 && hue <= 78 ? "#3a2b00" : "#ffffff";

  return {
    "--record-accent": `hsl(${hue} 74% 46%)`,
    "--record-accent-soft": `hsla(${hue}, 82%, 52%, 0.18)`,
    "--record-border": `hsla(${hue}, 58%, 48%, 0.16)`,
    "--record-bg-start": `hsla(${hue}, 85%, 97%, 0.98)`,
    "--record-bg-end": `hsla(${accentHue}, 90%, 93%, 0.92)`,
    "--record-bg-dark-start": `hsla(${hue}, 66%, 22%, 0.46)`,
    "--record-bg-dark-end": `hsla(${accentHue}, 72%, 27%, 0.34)`,
    "--record-border-dark": `hsla(${hue}, 78%, 64%, 0.24)`,
    "--record-tag-start": `hsl(${hue} 76% ${tagLightness}%)`,
    "--record-tag-end": `hsl(${accentHue} 72% ${Math.max(tagLightness - 6, 38)}%)`,
    "--record-tag-text": tagTextColor,
  };
};

const getCategoryPath = (log) => {
  const parent = log?.subcategory?.category?.name || "未分类";
  const child = log?.subcategory?.name || "未分类";
  return `${parent} / ${child}`;
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
  gap: 8px; /* Reduced gap */
}

.ios-list-item {
  position: relative;
  border-radius: 10px; /* Slightly smaller radius */
  padding: 8px 12px; /* Compact padding */
  border: 1px solid var(--record-border, transparent);
  background:
    linear-gradient(135deg, var(--record-bg-start, rgba(255, 255, 255, 0.96)) 0%, var(--record-bg-end, rgba(248, 250, 252, 0.96)) 100%);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;

  &::before {
    content: "";
    position: absolute;
    left: 0;
    top: 10px;
    bottom: 10px;
    width: 4px;
    border-radius: 999px;
    background: linear-gradient(
      180deg,
      var(--record-accent, var(--color-primary)) 0%,
      var(--record-tag-end, var(--color-primary-dark)) 100%
    );
    opacity: 0.95;
  }

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
    border-color: color-mix(
      in srgb,
      var(--record-accent, var(--color-primary)) 18%,
      transparent
    );

    .col-actions {
      opacity: 1;
    }
  }
}

.item-content {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 28px; /* Fixed height for consistency */
  padding-left: 4px;
}

/* 1. Time Column */
.col-time {
  font-size: 15px; /* Increased from 13px */
  color: var(--color-text-secondary);
  width: 110px; /* Increased width to accommodate larger font */
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

/* 2. Main Column (Task & Category) */
.col-main {
  flex: 1;
  display: grid;
  grid-template-columns: auto minmax(0, 1.15fr) minmax(150px, 0.95fr) auto;
  align-items: center;
  column-gap: 10px;
  min-width: 0; /* Enable truncation */

  .category-dot {
    width: 8px; /* Increased from 6px */
    height: 8px; /* Increased from 6px */
    border-radius: 50%;
    flex-shrink: 0;
    background: var(--record-accent, var(--color-primary));
    box-shadow: 0 0 0 4px var(--record-accent-soft, rgba(99, 102, 241, 0.16));
  }

  .task-name {
    font-size: 17px; /* Increased from 15px */
    font-weight: 600;
    color: var(--color-text-base);
    min-width: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .category-path {
    font-size: 13px; /* Increased from 11px */
    min-width: 0;
    display: inline-flex;
    align-items: center;
    justify-content: flex-start;
    gap: 6px;
    padding: 4px 10px;
    border-radius: 999px;
    white-space: nowrap;
    overflow: hidden;
    background: color-mix(
      in srgb,
      var(--record-accent-soft, rgba(99, 102, 241, 0.16)) 72%,
      white
    );
    border: 1px solid
      color-mix(
        in srgb,
        var(--record-accent, var(--color-primary)) 22%,
        transparent
      );
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
  }

  .category-parent,
  .category-child,
  .category-separator {
    display: inline-block;
    min-width: 0;
  }

  .category-parent {
    color: color-mix(
      in srgb,
      var(--record-accent, var(--color-primary)) 72%,
      var(--color-text-base)
    );
    font-weight: 700;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .category-separator {
    color: var(--color-text-muted);
    flex-shrink: 0;
  }

  .category-child {
    color: var(--color-text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .notes-icon-wrapper {
    display: flex;
    align-items: center;
    cursor: pointer;
    color: var(--color-primary);
    margin-left: 4px;

    &:hover {
      opacity: 0.8;
    }

    .notes-icon {
      width: 16px; /* Increased from 14px */
      height: 16px; /* Increased from 14px */
    }
  }
}

/* 3. Duration Column */
.col-duration {
  font-size: 16px; /* Increased from 14px */
  font-weight: 500;
  color: var(--color-text-base);
  width: 80px; /* Increased width */
  text-align: right;
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

/* 3.5 Mood Column */
.col-mood {
  width: 40px;
  text-align: center;
  flex-shrink: 0;
  font-size: 18px;
  line-height: 1;
}

/* 4. Actions Column */
.col-actions {
  width: 60px;
  display: flex;
  justify-content: flex-end;
  gap: 2px;
  opacity: 0; /* Hidden by default */
  transition: opacity 0.2s ease;

  .action-btn {
    padding: 4px;
    height: 28px; /* Increased from 24px */
    width: 28px; /* Increased from 24px */
    color: var(--color-text-secondary);

    &:hover {
      color: var(--color-primary);
      background-color: var(--color-primary-light);
    }

    &.delete:hover {
      color: var(--color-error);
      background-color: rgba(255, 59, 48, 0.1); /* Keep this or use variable */
    }

    :deep(.iconify) {
      width: 18px; /* Increased from 16px */
      height: 18px; /* Increased from 16px */
    }
  }
}

.expanded-notes {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 0.5px solid
    color-mix(
      in srgb,
      var(--record-accent, var(--color-primary)) 14%,
      var(--color-border-card)
    );
  font-size: 15px; /* Increased from 13px */
  color: var(--color-text-secondary);
  line-height: 1.5;
  padding-left: 122px; /* Align with task name (Time width + gap) */
}

/* Hover state remains consistent or slightly darkens */
.ios-list-item:hover {
  filter: brightness(
    0.98
  ); /* Slightly darken on hover instead of generic shadow change only */
}

[data-theme="dark"] .ios-list-item {
  background: linear-gradient(
    135deg,
    var(--record-bg-dark-start, rgba(51, 65, 85, 0.72)) 0%,
    var(--record-bg-dark-end, rgba(30, 41, 59, 0.62)) 100%
  );
  border-color: var(--record-border-dark, rgba(148, 163, 184, 0.2));
}

[data-theme="dark"] .col-main .category-path {
  background: color-mix(
    in srgb,
    var(--record-accent-soft, rgba(99, 102, 241, 0.16)) 44%,
    rgba(15, 23, 42, 0.78)
  );
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
}

</style>
