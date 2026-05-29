<template>
  <div class="conn-status" :class="`conn-status--${state}`" role="status" :aria-label="`网络状态: ${label}`">
    <span class="conn-status__dot" aria-hidden="true" />
    <span class="conn-status__label">{{ label }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ConnectionState } from '@/types/contracts'

const props = withDefaults(defineProps<{
  state?: ConnectionState
}>(), {
  state: 'disconnected',
})

const label = computed(() => {
  const labels: Record<ConnectionState, string> = {
    connected: '已连接',
    connecting: '连接中...',
    reconnecting: '重连中...',
    disconnected: '未连接',
  }
  return labels[props.state]
})
</script>

<style scoped>
.conn-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 2px 10px;
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-tertiary);
  transition: all var(--vc-transition-base);
}

.conn-status__dot {
  width: 6px;
  height: 6px;
  border-radius: var(--vc-radius-full);
  transition: background var(--vc-transition-base);
}

.conn-status--connected { color: var(--vc-success); }
.conn-status--connected .conn-status__dot { background: var(--vc-success); }

.conn-status--connecting,
.conn-status--reconnecting { color: var(--vc-warning); }
.conn-status--connecting .conn-status__dot,
.conn-status--reconnecting .conn-status__dot {
  background: var(--vc-warning);
  animation: vc-blink 1s ease-in-out infinite;
}

.conn-status--disconnected { color: var(--vc-text-tertiary); }
.conn-status--disconnected .conn-status__dot { background: var(--vc-text-tertiary); }
</style>
