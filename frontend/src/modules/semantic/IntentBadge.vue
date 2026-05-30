<template>
  <span class="intent-badge" :class="`intent-badge--${displayCategory}`">
    <span class="intent-badge__icon" aria-hidden="true">{{ displayIcon }}</span>
    <span class="intent-badge__label">{{ displayLabel }}</span>
  </span>
</template>

<script setup lang="ts">
/**
 * 意图徽章 — 纯展示组件
 *
 * 支持两种模式：
 *   1. 后端下发 display 对象（推荐）: { category, icon, label }
 *   2. 仅传入 intent 类型（兼容旧模式，使用 fallback 映射）
 *
 * 前端不做意图分析，仅渲染后端提供的展示数据。
 */
import { computed } from 'vue'
import type { IntentType } from '@/types/contracts'

const props = withDefaults(defineProps<{
  intent?: IntentType | string
  display?: { category: string; icon: string; label: string }
}>(), {
  intent: 'unknown',
})

const displayCategory = computed(() => props.display?.category || 'unknown')
const displayIcon = computed(() => props.display?.icon || '❔')
const displayLabel = computed(() => props.display?.label || String(props.intent))
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
.intent-badge--search {
  color: var(--vc-accent-light);
  background: hsla(270, 72%, 56%, 0.1);
  border-color: hsla(270, 72%, 56%, 0.25);
}
.intent-badge--plan {
  color: var(--vc-accent-light);
  background: hsla(270, 72%, 56%, 0.1);
  border-color: hsla(270, 72%, 56%, 0.25);
}
.intent-badge--cancel,
.intent-badge--unknown {
  color: var(--vc-text-tertiary);
  background: var(--vc-bg-elevated);
  border-color: var(--vc-border);
}
</style>
