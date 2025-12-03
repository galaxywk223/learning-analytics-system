<template>
  <div class="ios-list-container">
    <div class="ios-list">
      <div v-for="log in logs" :key="log.id" class="ios-list-item">
        <div class="item-content">
          <!-- Left: Category & Task -->
          <div class="item-main">
            <div class="task-row">
              <span
                v-if="log.subcategory"
                class="category-dot"
                :class="`category-color-${(log.subcategory.category_id || 0) % 6}`"
              ></span>
              <span class="task-name">{{ log.task }}</span>
            </div>
            <div class="sub-row">
              <span class="category-name" v-if="log.subcategory">
                {{ log.subcategory.name }}
              </span>
              <!-- Notes Icon (Click to toggle) -->
              <span 
                v-if="log.notes" 
                class="notes-icon-wrapper"
                @click.stop="$emit('toggle-notes', log.id)"
              >
                <Icon icon="lucide:message-square" class="notes-icon" />
              </span>
            </div>
          </div>

          <!-- Right: Time & Duration -->
          <div class="item-meta">
            <div class="duration-badge">
              {{ log.actual_duration }} min
            </div>
            <div class="time-slot">
              {{ log.time_slot }}
            </div>
          </div>
          
          <!-- Actions (Hover/Right) -->
          <div class="item-actions">
             <el-button
              link
              size="small"
              @click="$emit('edit-record', log)"
              class="action-btn"
            >
              <Icon icon="lucide:pencil" />
            </el-button>
             <el-button
              link
              size="small"
              type="danger"
              @click="$emit('delete-record', log)"
              class="action-btn delete"
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

defineProps({
  logs: {
    type: Array,
    default: () => [],
  },
  expandedNotes: {
    type: Array,
    default: () => [],
  },
});

defineEmits(["toggle-notes", "edit-record", "delete-record"]);
</script>

<style scoped lang="scss">
.ios-list-container {
  width: 100%;
}

.ios-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ios-list-item {
  background: #ffffff;
  border-radius: 12px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  }
}

.item-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.item-main {
  flex: 1;
  min-width: 0;
  
  .task-row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
    
    .category-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    
    .task-name {
      font-size: 17px; /* Increased */
      font-weight: 600;
      color: #000;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
  
  .sub-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px; /* Increased */
    color: #8e8e93;
    height: 20px;
    
    .category-name {
      font-weight: 500;
    }
    
    .notes-icon-wrapper {
      display: flex;
      align-items: center;
      cursor: pointer;
      color: #007aff;
      
      &:hover {
        opacity: 0.8;
      }
      
      .notes-icon {
        width: 16px;
        height: 16px;
      }
    }
  }
}

.item-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  
  .duration-badge {
    font-size: 17px; /* Increased */
    font-weight: 600;
    color: #000;
  }
  
  .time-slot {
    font-size: 14px; /* Increased */
    color: #8e8e93;
  }
}

.item-actions {
  display: flex;
  gap: 4px;
  opacity: 0; /* Hidden by default */
  transition: opacity 0.2s ease;
  
  .action-btn {
    padding: 4px;
    color: #8e8e93;
    
    &:hover {
      color: #007aff;
    }
    
    &.delete:hover {
      color: #ff3b30;
    }
    
    :deep(.iconify) {
      width: 18px;
      height: 18px;
    }
  }
}

.ios-list-item:hover .item-actions {
  opacity: 1;
}

.expanded-notes {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 0.5px solid rgba(60, 60, 67, 0.1);
  font-size: 14px;
  color: #3c3c43;
  line-height: 1.5;
}

/* Category Colors */
.category-color-0 { background-color: #007aff; }
.category-color-1 { background-color: #ff2d55; }
.category-color-2 { background-color: #34c759; }
.category-color-3 { background-color: #ff9500; }
.category-color-4 { background-color: #5856d6; }
.category-color-5 { background-color: #ff3b30; }
</style>
