<template>
  <div class="task-item" :class="{ 'task-item--completed': isCompleted }" @click="$emit('toggle')">
    <button class="task-item__checkbox" :aria-label="isCompleted ? '标记为未完成' : '标记为已完成'" @click.stop="$emit('toggle')">
      <svg v-if="isCompleted" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><polyline points="20 6 9 17 4 12" /></svg>
    </button>
    <div class="task-item__body">
      <span class="task-item__title">{{ title }}</span>
      <span v-if="dueTime" class="task-item__due">{{ formattedDue }}</span>
    </div>
    <span class="task-item__priority" :class="`task-item__priority--${priority}`">{{ priorityLabel }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  dueTime?: string
  priority?: 'low' | 'medium' | 'high'
  isCompleted?: boolean
}>(), {
  title: '未命名待办',
  dueTime: '',
  priority: 'medium',
  isCompleted: false,
})

defineEmits<{ toggle: [] }>()

const priorityLabel = computed(() => {
  const m: Record<string, string> = { low: '低', medium: '中', high: '高' }
  return m[props.priority]
})

const formattedDue = computed(() => {
  if (!props.dueTime) return ''
  try {
    return new Date(props.dueTime).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
  } catch { return props.dueTime }
})
</script>

<style scoped>
.task-item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-md);
  padding: var(--vc-space-sm) var(--vc-space-md);
  border-radius: var(--vc-radius-md);
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  cursor: pointer;
  transition: all var(--vc-transition-fast);
}
.task-item:hover { border-color: var(--vc-border-active); }

.task-item--completed { opacity: 0.5; }
.task-item--completed .task-item__title { text-decoration: line-through; }

.task-item__checkbox {
  width: 22px;
  height: 22px;
  border-radius: var(--vc-radius-sm);
  border: 2px solid var(--vc-border);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--vc-transition-fast);
  flex-shrink: 0;
  color: var(--vc-success);
}
.task-item--completed .task-item__checkbox {
  background: var(--vc-success);
  border-color: var(--vc-success);
  color: white;
}

.task-item__body { flex: 1; min-width: 0; }

.task-item__title {
  display: block;
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-primary);
}

.task-item__due {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
}

.task-item__priority {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  padding: 1px 8px;
  border-radius: var(--vc-radius-full);
}
.task-item__priority--high { background: var(--vc-danger-soft); color: var(--vc-danger); }
.task-item__priority--medium { background: var(--vc-warning-soft); color: var(--vc-warning); }
.task-item__priority--low { background: var(--vc-info-soft); color: var(--vc-info); }
</style>
