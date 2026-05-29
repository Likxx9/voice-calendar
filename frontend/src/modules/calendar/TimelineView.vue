<template>
  <div class="timeline-view" role="list" aria-label="今日时间轴">
    <div v-for="event in sortedEvents" :key="event.id" class="timeline-view__item" role="listitem">
      <div class="timeline-view__time-col">
        <span class="timeline-view__time">{{ formatTime(event.start_time) }}</span>
        <div class="timeline-view__line" aria-hidden="true" />
      </div>
      <div class="timeline-view__content">
        <EventCard
          :title="event.title"
          :start-time="event.start_time"
          :end-time="event.end_time"
          :location="event.location"
          :color="event.color"
          @click="$emit('event-click', event.id)"
        />
      </div>
    </div>
    <div v-if="sortedEvents.length === 0" class="timeline-view__empty">
      <span class="timeline-view__empty-icon">📅</span>
      <p>今天暂无日程安排</p>
      <p class="timeline-view__empty-hint">试试说 "明天下午三点开会"</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CalendarEvent } from '@/types/contracts'
import EventCard from './EventCard.vue'

const props = withDefaults(defineProps<{
  events?: CalendarEvent[]
}>(), {
  events: () => [],
})

defineEmits<{
  'event-click': [eventId: string]
}>()

const sortedEvents = computed(() =>
  [...props.events].sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
)

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}
</script>

<style scoped>
.timeline-view {
  display: flex;
  flex-direction: column;
  gap: 0;
  padding: var(--vc-space-md);
}

.timeline-view__item {
  display: flex;
  gap: var(--vc-space-md);
}

.timeline-view__time-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 50px;
  flex-shrink: 0;
}

.timeline-view__time {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-secondary);
  font-variant-numeric: tabular-nums;
}

.timeline-view__line {
  width: 2px;
  flex: 1;
  min-height: 24px;
  background: linear-gradient(180deg, var(--vc-primary), var(--vc-accent));
  border-radius: var(--vc-radius-full);
  margin: 4px 0;
  opacity: 0.3;
}

.timeline-view__content {
  flex: 1;
  padding-bottom: var(--vc-space-md);
}

.timeline-view__empty {
  text-align: center;
  padding: var(--vc-space-3xl) var(--vc-space-lg);
  color: var(--vc-text-tertiary);
}

.timeline-view__empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: var(--vc-space-md);
}

.timeline-view__empty-hint {
  font-size: var(--vc-text-sm);
  margin-top: var(--vc-space-sm);
  color: var(--vc-primary-light);
  font-style: italic;
}
</style>
