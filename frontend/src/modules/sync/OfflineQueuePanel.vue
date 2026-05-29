<template>
  <div class="offline-panel vc-elevated" role="region" aria-label="离线操作队列">
    <h3 class="offline-panel__title">📋 离线操作队列</h3>
    <p class="offline-panel__desc">以下操作将在网络恢复后自动同步</p>

    <div v-if="operations.length > 0" class="offline-panel__list">
      <div
        v-for="op in operations"
        :key="op.operation_id"
        class="offline-panel__item"
      >
        <span class="offline-panel__item-icon">{{ actionIcon(op.action) }}</span>
        <div class="offline-panel__item-body">
          <span class="offline-panel__item-action">{{ actionLabel(op.action) }}{{ entityLabel(op.entity_type) }}</span>
          <span class="offline-panel__item-time">{{ formatTime(op.executed_at) }}</span>
        </div>
      </div>
    </div>

    <div v-else class="offline-panel__empty">
      暂无离线操作
    </div>
  </div>
</template>

<script setup lang="ts">
import type { OfflineOperation } from '@/types/contracts'

withDefaults(defineProps<{
  operations?: OfflineOperation[]
}>(), {
  operations: () => [],
})

function actionIcon(action: string): string {
  const m: Record<string, string> = { create: '➕', update: '✏️', delete: '🗑️' }
  return m[action] || '📝'
}

function actionLabel(action: string): string {
  const m: Record<string, string> = { create: '创建', update: '修改', delete: '删除' }
  return m[action] || action
}

function entityLabel(type: string): string {
  return type === 'event' ? '日程' : '待办'
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch { return '' }
}
</script>

<style scoped>
.offline-panel {
  padding: var(--vc-space-lg);
}

.offline-panel__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  margin-bottom: var(--vc-space-xs);
}

.offline-panel__desc {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-tertiary);
  margin-bottom: var(--vc-space-md);
}

.offline-panel__list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.offline-panel__item {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
  padding: var(--vc-space-sm);
  border-radius: var(--vc-radius-sm);
  background: var(--vc-bg-surface);
}

.offline-panel__item-icon { font-size: 16px; }

.offline-panel__item-body {
  display: flex;
  flex-direction: column;
}

.offline-panel__item-action {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
}

.offline-panel__item-time {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.offline-panel__empty {
  text-align: center;
  padding: var(--vc-space-xl);
  color: var(--vc-text-tertiary);
  font-size: var(--vc-text-sm);
}
</style>
