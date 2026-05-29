<template>
  <Transition name="vc-slide-down">
    <div v-if="visible" class="sync-banner" :class="`sync-banner--${state}`" role="status" :aria-label="`同步状态: ${label}`">
      <span class="sync-banner__icon" aria-hidden="true">{{ icon }}</span>
      <span class="sync-banner__label">{{ label }}</span>
      <span v-if="pendingCount > 0" class="sync-banner__count">{{ pendingCount }} 项待同步</span>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { SyncState } from '@/types/contracts'

const props = withDefaults(defineProps<{
  state?: SyncState
  pendingCount?: number
}>(), {
  state: 'online',
  pendingCount: 0,
})

const visible = computed(() => props.state !== 'online' || props.pendingCount > 0)

const label = computed(() => {
  const m: Record<SyncState, string> = {
    online: '已连接', offline: '离线模式', syncing: '同步中...', sync_error: '同步失败'
  }
  return m[props.state]
})

const icon = computed(() => {
  const m: Record<SyncState, string> = {
    online: '🟢', offline: '📴', syncing: '🔄', sync_error: '❌'
  }
  return m[props.state]
})
</script>

<style scoped>
.sync-banner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--vc-space-sm);
  padding: var(--vc-space-xs) var(--vc-space-md);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  text-align: center;
}

.sync-banner--offline {
  background: var(--vc-warning-soft);
  color: var(--vc-warning);
}
.sync-banner--syncing {
  background: var(--vc-info-soft);
  color: var(--vc-info);
}
.sync-banner--sync_error {
  background: var(--vc-danger-soft);
  color: var(--vc-danger);
}
.sync-banner--online {
  background: var(--vc-success-soft);
  color: var(--vc-success);
}

.sync-banner__count {
  padding: 1px 8px;
  border-radius: var(--vc-radius-full);
  background: hsla(0, 0%, 100%, 0.15);
  font-variant-numeric: tabular-nums;
}
</style>
