<template>
  <div class="event-card" :class="{ 'event-card--compact': compact }" :style="{ '--event-color': color }" @click="$emit('click')">
    <div class="event-card__color-bar" aria-hidden="true" />
    <div class="event-card__body">
      <h4 class="event-card__title">{{ title }}</h4>
      <div class="event-card__meta">
        <span class="event-card__time">🕐 {{ formattedTime }}</span>
        <span v-if="location" class="event-card__location">📍 {{ location }}</span>
      </div>
      <div v-if="attendees && attendees.length > 0 && !compact" class="event-card__attendees">
        <span v-for="(a, i) in attendees.slice(0, 3)" :key="i" class="event-card__avatar" :title="a">
          {{ a.charAt(0).toUpperCase() }}
        </span>
        <span v-if="attendees.length > 3" class="event-card__more">+{{ attendees.length - 3 }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(defineProps<{
  title?: string
  startTime?: string
  endTime?: string
  location?: string
  attendees?: string[]
  color?: string
  compact?: boolean
}>(), {
  title: '未命名日程',
  startTime: '',
  endTime: '',
  location: '',
  attendees: () => [],
  color: 'var(--vc-primary)',
  compact: false,
})

defineEmits<{ click: [] }>()

const formattedTime = computed(() => {
  try {
    const fmt = (s: string) => new Date(s).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    if (props.startTime && props.endTime) return `${fmt(props.startTime)} - ${fmt(props.endTime)}`
    if (props.startTime) return fmt(props.startTime)
    return '时间待定'
  } catch { return '时间待定' }
})
</script>

<style scoped>
.event-card {
  --event-color: var(--vc-primary);
  display: flex;
  gap: 0;
  background: var(--vc-bg-elevated);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--vc-transition-fast);
}

.event-card:hover {
  border-color: var(--event-color);
  box-shadow: var(--vc-shadow-sm);
  transform: translateY(-1px);
}

.event-card__color-bar {
  width: 4px;
  background: var(--event-color);
  flex-shrink: 0;
}

.event-card__body {
  flex: 1;
  padding: var(--vc-space-sm) var(--vc-space-md);
}

.event-card__title {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
  margin-bottom: 2px;
}

.event-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--vc-space-sm);
}

.event-card__time,
.event-card__location {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-secondary);
}

.event-card__attendees {
  display: flex;
  align-items: center;
  gap: -4px;
  margin-top: var(--vc-space-xs);
}

.event-card__avatar {
  width: 22px;
  height: 22px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-accent);
  color: white;
  font-size: 10px;
  font-weight: var(--vc-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: -4px;
  border: 2px solid var(--vc-bg-elevated);
}
.event-card__avatar:first-child { margin-left: 0; }

.event-card__more {
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  margin-left: var(--vc-space-xs);
}

.event-card--compact .event-card__body {
  padding: var(--vc-space-xs) var(--vc-space-sm);
}
.event-card--compact .event-card__title {
  font-size: var(--vc-text-xs);
}
</style>
