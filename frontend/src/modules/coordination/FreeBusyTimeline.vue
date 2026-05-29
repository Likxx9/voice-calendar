<template>
  <div class="freebusy-timeline vc-elevated" role="region" aria-label="参与者忙闲时间轴">
    <h3 class="freebusy-timeline__title">📊 多方忙闲时间轴</h3>

    <div class="freebusy-timeline__grid">
      <!-- 时间标尺 -->
      <div class="freebusy-timeline__ruler">
        <span class="freebusy-timeline__ruler-label" />
        <div class="freebusy-timeline__hours">
          <span v-for="h in hours" :key="h" class="freebusy-timeline__hour">{{ h }}</span>
        </div>
      </div>

      <!-- 每个参与者一行 -->
      <div
        v-for="attendee in attendees"
        :key="attendee.email"
        class="freebusy-timeline__row"
      >
        <span class="freebusy-timeline__name" :title="attendee.email">
          {{ extractName(attendee.email) }}
        </span>
        <div class="freebusy-timeline__bar">
          <div
            v-for="(period, idx) in attendee.busy_periods"
            :key="idx"
            class="freebusy-timeline__busy-block"
            :style="blockStyle(period.start, period.end)"
            :title="`忙碌: ${formatTime(period.start)} - ${formatTime(period.end)}`"
          />
        </div>
      </div>

      <!-- 空闲窗口 -->
      <div v-if="freeWindows.length" class="freebusy-timeline__free-row">
        <span class="freebusy-timeline__name freebusy-timeline__name--free">🟢 空闲</span>
        <div class="freebusy-timeline__bar">
          <div
            v-for="(w, idx) in freeWindows"
            :key="idx"
            class="freebusy-timeline__free-block"
            :style="blockStyle(w.start, w.end)"
            :title="`空闲: ${formatTime(w.start)} - ${formatTime(w.end)}`"
            @click="$emit('select-window', w)"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { FreeBusySlot } from '@/types/contracts'

const props = withDefaults(defineProps<{
  attendees?: FreeBusySlot[]
  freeWindows?: Array<{ start: string; end: string; score: number }>
  dayStart?: number   // 小时，默认 8
  dayEnd?: number     // 小时，默认 20
}>(), {
  attendees: () => [],
  freeWindows: () => [],
  dayStart: 8,
  dayEnd: 20,
})

defineEmits<{
  'select-window': [window: { start: string; end: string; score: number }]
}>()

const hours = Array.from({ length: props.dayEnd - props.dayStart + 1 }, (_, i) => `${props.dayStart + i}:00`)

function extractName(email: string): string {
  return email.split('@')[0] || email
}

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  } catch { return '' }
}

function blockStyle(start: string, end: string): Record<string, string> {
  const totalHours = props.dayEnd - props.dayStart
  const s = new Date(start)
  const e = new Date(end)
  const startHour = s.getHours() + s.getMinutes() / 60 - props.dayStart
  const endHour = e.getHours() + e.getMinutes() / 60 - props.dayStart
  const left = Math.max(0, (startHour / totalHours) * 100)
  const width = Math.min(100 - left, ((endHour - startHour) / totalHours) * 100)
  return { left: `${left}%`, width: `${width}%` }
}
</script>

<style scoped>
.freebusy-timeline {
  padding: var(--vc-space-lg);
}

.freebusy-timeline__title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  margin-bottom: var(--vc-space-md);
}

.freebusy-timeline__grid {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
}

.freebusy-timeline__ruler,
.freebusy-timeline__row,
.freebusy-timeline__free-row {
  display: flex;
  align-items: center;
  gap: var(--vc-space-md);
}

.freebusy-timeline__name {
  width: 80px;
  flex-shrink: 0;
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-secondary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.freebusy-timeline__name--free { color: var(--vc-success); }

.freebusy-timeline__ruler-label { width: 80px; flex-shrink: 0; }

.freebusy-timeline__hours {
  flex: 1;
  display: flex;
  justify-content: space-between;
}

.freebusy-timeline__hour {
  font-size: 10px;
  color: var(--vc-text-tertiary);
  font-variant-numeric: tabular-nums;
}

.freebusy-timeline__bar {
  flex: 1;
  height: 24px;
  background: var(--vc-bg-surface);
  border-radius: var(--vc-radius-sm);
  position: relative;
  overflow: hidden;
}

.freebusy-timeline__busy-block {
  position: absolute;
  top: 2px;
  bottom: 2px;
  background: var(--vc-danger);
  opacity: 0.6;
  border-radius: 3px;
}

.freebusy-timeline__free-block {
  position: absolute;
  top: 2px;
  bottom: 2px;
  background: var(--vc-success);
  opacity: 0.5;
  border-radius: 3px;
  cursor: pointer;
  transition: opacity var(--vc-transition-fast);
}
.freebusy-timeline__free-block:hover {
  opacity: 0.9;
}
</style>
