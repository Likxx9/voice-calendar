<template>
  <div class="timeline-view" role="list" aria-label="今日时间轴">
    <!-- 模拟当前时间线 -->
    <div class="current-time-indicator" :style="{ top: '150px' }">
      <div class="current-time-pulse"></div>
      <div class="current-time-line"></div>
    </div>

    <div v-for="(event, index) in sortedEvents" :key="event.id" class="timeline-view__item" role="listitem">
      <div class="timeline-view__time-col">
        <span class="timeline-view__time">{{ formatTime(event.start_time) }}</span>
        <!-- 不给最后一个元素显示长线 -->
        <div class="timeline-view__line" :class="{ 'timeline-view__line--last': index === sortedEvents.length - 1 }" aria-hidden="true" />
      </div>
      <div class="timeline-view__content">
        <EventCard
          :title="event.title"
          :start-time="event.start_time"
          :end-time="event.end_time"
          :location="event.location"
          :attendees="event.attendees"
          :color="event.color"
          :type="event.id === 'ev-3' ? 'commute' : 'meeting'"
          :has-reminder="event.id === 'ev-2'"
          @click="$emit('event-click', event.id)"
        />
      </div>
    </div>
    <div v-if="sortedEvents.length === 0" class="timeline-view__empty">
      <span class="timeline-view__empty-icon">📅</span>
      <p>今日暂无日程安排</p>
      <p class="timeline-view__empty-hint">您可以唤醒助手安排工作</p>
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
  padding: var(--vc-space-md) var(--vc-space-md) 100px; /* 留出底部空间 */
  position: relative;
}

/* 当前时间线指示器 */
.current-time-indicator {
  position: absolute;
  left: var(--vc-space-md);
  right: var(--vc-space-md);
  display: flex;
  align-items: center;
  z-index: var(--vc-z-card);
  pointer-events: none;
}

.current-time-pulse {
  width: 10px;
  height: 10px;
  background-color: var(--vc-accent);
  border-radius: 50%;
  margin-left: 20px; /* 对齐时间刻度右侧 */
  position: relative;
}

.current-time-pulse::after {
  content: '';
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  border: 2px solid var(--vc-accent);
  animation: pulse-ring 2s cubic-bezier(0.215, 0.61, 0.355, 1) infinite;
}

.current-time-line {
  flex: 1;
  height: 2px;
  background-color: var(--vc-accent);
  opacity: 0.8;
  margin-left: var(--vc-space-xs);
}

@keyframes pulse-ring {
  0% {
    transform: scale(0.5);
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: scale(2);
    opacity: 0;
  }
}

.timeline-view__item {
  display: flex;
  gap: var(--vc-space-md);
  position: relative;
}

.timeline-view__time-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 50px;
  flex-shrink: 0;
  margin-top: 2px; /* 对齐卡片头部 */
}

.timeline-view__time {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  font-family: var(--vc-font-mono);
}

.timeline-view__line {
  width: 2px;
  flex: 1;
  min-height: 40px;
  background-color: var(--vc-border);
  margin: var(--vc-space-xs) 0;
}

.timeline-view__line--last {
  background: linear-gradient(180deg, var(--vc-border) 0%, transparent 100%);
}

.timeline-view__content {
  flex: 1;
  padding-bottom: var(--vc-space-lg);
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
  color: var(--vc-primary);
  font-weight: var(--vc-weight-medium);
}
</style>
