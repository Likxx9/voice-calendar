<template>
  <span class="intent-badge" :class="`intent-badge--${category}`">
    <span class="intent-badge__icon" aria-hidden="true">{{ icon }}</span>
    <span class="intent-badge__label">{{ label }}</span>
  </span>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { IntentType } from '@/types/contracts'

const props = withDefaults(defineProps<{
  intent?: IntentType
}>(), {
  intent: 'unknown',
})

const category = computed(() => {
  if (props.intent.includes('event')) return 'event'
  if (props.intent.includes('task')) return 'task'
  if (props.intent === 'clarification') return 'clarify'
  if (props.intent === 'cancel') return 'cancel'
  return 'unknown'
})

const icon = computed(() => {
  const icons: Record<string, string> = {
    event: '📅', task: '✅', clarify: '❓', cancel: '✖', unknown: '❔'
  }
  return icons[category.value]
})

const label = computed(() => {
  const labels: Record<IntentType, string> = {
    create_event: '创建日程', update_event: '修改日程', delete_event: '删除日程',
    create_task: '创建待办', update_task: '修改待办', delete_task: '删除待办',
    convert_task_to_event: '转为日程', clarification: '需要确认',
    cancel: '取消操作', unknown: '未识别',
  }
  return labels[props.intent]
})
</script>

<style scoped>
.intent-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  border: 1px solid;
}

.intent-badge__icon { font-size: 12px; }

.intent-badge--event {
  color: var(--vc-primary-light);
  background: hsla(224, 76%, 48%, 0.1);
  border-color: hsla(224, 76%, 48%, 0.25);
}
.intent-badge--task {
  color: var(--vc-success);
  background: var(--vc-success-soft);
  border-color: hsla(152, 68%, 46%, 0.25);
}
.intent-badge--clarify {
  color: var(--vc-warning);
  background: var(--vc-warning-soft);
  border-color: hsla(38, 92%, 50%, 0.25);
}
.intent-badge--cancel,
.intent-badge--unknown {
  color: var(--vc-text-tertiary);
  background: var(--vc-bg-elevated);
  border-color: var(--vc-border);
}
</style>
