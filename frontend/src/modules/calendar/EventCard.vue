<template>
  <div class="event-card" :class="[compact ? 'event-card--compact' : '', `event-card--${type}`]" :style="{ '--event-color': color }" @click="$emit('click')">
    <div class="event-card__color-bar" aria-hidden="true" />
    <div class="event-card__body">
      <div class="event-card__header">
        <h4 class="event-card__title">
          <span v-if="type === 'commute'" class="commute-icon">🚗</span>
          {{ title }}
        </h4>
        <span v-if="hasReminder" class="event-card__reminder-icon" title="已设置独立提醒">🔔</span>
      </div>
      <div class="event-card__meta">
        <span class="event-card__time">{{ formattedTime }}</span>
        <span v-if="location" class="event-card__location">{{ location }}</span>
      </div>
      
      <!-- 上下文增强微件 (Context Widgets) -->
      <div v-if="attendees && attendees.length > 0 && !compact" class="event-card__widgets">
        <div class="event-card__attendees">
          <span v-for="(a, i) in attendees.slice(0, 3)" :key="i" class="event-card__avatar" :title="a">
            {{ a.charAt(0).toUpperCase() }}
          </span>
          <span v-if="attendees.length > 3" class="event-card__more">+{{ attendees.length - 3 }}</span>
        </div>
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
  type?: 'meeting' | 'commute' | 'personal'
  hasReminder?: boolean
}>(), {
  title: '未命名日程',
  startTime: '',
  endTime: '',
  location: '',
  attendees: () => [],
  color: 'var(--vc-primary)',
  compact: false,
  type: 'meeting',
  hasReminder: false,
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
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-md);
  overflow: hidden;
  cursor: pointer;
  transition: all var(--vc-transition-fast);
  z-index: var(--vc-z-card);
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  border: 1px solid var(--vc-divider);
}

/* 通勤块特有的斜线阴影填充 */
.event-card--commute {
  background: repeating-linear-gradient(
    -45deg,
    var(--vc-bg-base),
    var(--vc-bg-base) 10px,
    var(--vc-bg-surface) 10px,
    var(--vc-bg-surface) 20px
  );
  border: 1px dashed var(--vc-text-tertiary);
}
.event-card--commute .event-card__color-bar {
  opacity: 0.5;
}

.event-card:hover {
  box-shadow: var(--vc-shadow-md);
  transform: translateY(-2px);
}

.event-card__color-bar {
  width: 4px;
  background: var(--event-color);
  flex-shrink: 0;
}

.event-card__body {
  flex: 1;
  padding: var(--vc-space-sm) var(--vc-space-md);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.event-card__title {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
  margin: 0;
  line-height: var(--vc-leading-tight);
  display: flex;
  align-items: center;
  gap: 4px;
}

.commute-icon {
  font-size: 14px;
}

.event-card__reminder-icon {
  font-size: 12px;
  color: var(--vc-warning);
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
  font-family: var(--vc-font-mono);
}

/* 增强微件样式 */
.event-card__widgets {
  margin-top: 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.event-card__attendees {
  display: flex;
  align-items: center;
  gap: -4px;
}

.event-card__avatar {
  width: 20px;
  height: 20px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-text-secondary);
  color: var(--vc-text-inverse);
  font-size: 10px;
  font-weight: var(--vc-weight-bold);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-left: -6px;
  border: 2px solid var(--vc-bg-surface);
}
.event-card__avatar:first-child { margin-left: 0; }

.event-card__more {
  font-size: 10px;
  color: var(--vc-text-tertiary);
  margin-left: var(--vc-space-xs);
}

/* 紧凑模式覆盖 */
.event-card--compact .event-card__body {
  padding: var(--vc-space-xs) var(--vc-space-sm);
}
.event-card--compact .event-card__title {
  font-size: var(--vc-text-xs);
}
</style>
