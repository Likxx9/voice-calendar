<template>
  <div class="calendar-shell" role="region" aria-label="日历">
    <!-- 头部：月份导航 + 视图切换 -->
    <header class="calendar-shell__header">
      <div class="calendar-shell__nav">
        <button class="calendar-shell__nav-btn" aria-label="上一个" @click="navigate(-1)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6" /></svg>
        </button>
        <h2 class="calendar-shell__title">{{ currentTitle }}</h2>
        <button class="calendar-shell__nav-btn" aria-label="下一个" @click="navigate(1)">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6" /></svg>
        </button>
      </div>

      <div class="calendar-shell__view-toggle" role="tablist">
        <button
          v-for="v in views"
          :key="v.value"
          class="calendar-shell__view-btn"
          :class="{ 'calendar-shell__view-btn--active': currentView === v.value }"
          role="tab"
          :aria-selected="currentView === v.value"
          @click="$emit('view-change', v.value)"
        >
          {{ v.label }}
        </button>
      </div>
    </header>

    <!-- 日历网格 -->
    <div class="calendar-shell__body">
      <!-- 周视图：星期头 -->
      <div v-if="currentView !== 'day'" class="calendar-shell__weekdays">
        <span v-for="day in weekDays" :key="day" class="calendar-shell__weekday">{{ day }}</span>
      </div>

      <!-- 月视图网格 -->
      <div v-if="currentView === 'month'" class="calendar-shell__month-grid">
        <button
          v-for="(cell, idx) in monthCells"
          :key="idx"
          class="calendar-shell__day-cell"
          :class="{
            'calendar-shell__day-cell--other': !cell.isCurrentMonth,
            'calendar-shell__day-cell--today': cell.isToday,
            'calendar-shell__day-cell--selected': cell.dateStr === selectedDate,
            'calendar-shell__day-cell--has-events': cell.eventCount > 0,
          }"
          @click="$emit('date-select', cell.dateStr)"
        >
          <span class="calendar-shell__day-num">{{ cell.day }}</span>
          <span v-if="cell.eventCount > 0" class="calendar-shell__event-dot" aria-hidden="true" />
        </button>
      </div>

      <!-- 周视图时间轴 -->
      <div v-else-if="currentView === 'week'" class="calendar-shell__week-grid">
        <div class="calendar-shell__time-col">
          <span v-for="h in hours" :key="h" class="calendar-shell__time-label">{{ h }}:00</span>
        </div>
        <div class="calendar-shell__days-row">
          <div v-for="d in 7" :key="d" class="calendar-shell__day-col">
            <slot name="week-events" :dayIndex="d" />
          </div>
        </div>
      </div>

      <!-- 日视图 -->
      <div v-else class="calendar-shell__day-view">
        <div class="calendar-shell__time-col">
          <span v-for="h in hours" :key="h" class="calendar-shell__time-label">{{ h }}:00</span>
        </div>
        <div class="calendar-shell__day-content">
          <slot name="day-events" />
        </div>
      </div>
    </div>

    <!-- 今日事件摘要 -->
    <div v-if="todayEventCount > 0" class="calendar-shell__today-summary">
      <span class="calendar-shell__today-badge">今天 {{ todayEventCount }} 项日程</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

const props = withDefaults(defineProps<{
  currentView?: 'month' | 'week' | 'day'
  selectedDate?: string
  todayEventCount?: number
  eventDates?: string[]    // 有事件的日期列表 ['2026-06-01', ...]
}>(), {
  currentView: 'week',
  selectedDate: () => new Date().toISOString().split('T')[0],
  todayEventCount: 0,
  eventDates: () => [],
})

defineEmits<{
  'view-change': [view: 'month' | 'week' | 'day']
  'date-select': [date: string]
  'navigate': [direction: number]
}>()

const views = [
  { value: 'month' as const, label: '月' },
  { value: 'week' as const, label: '周' },
  { value: 'day' as const, label: '日' },
]

const weekDays = ['一', '二', '三', '四', '五', '六', '日']
const hours = Array.from({ length: 14 }, (_, i) => i + 7) // 7:00 ~ 20:00

const viewDate = ref(new Date(props.selectedDate))

const currentTitle = computed(() => {
  const d = viewDate.value
  if (props.currentView === 'month') {
    return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月`
  }
  return `${d.getFullYear()} 年 ${d.getMonth() + 1} 月 ${d.getDate()} 日`
})

// 月视图单元格数据
const monthCells = computed(() => {
  const d = viewDate.value
  const year = d.getFullYear()
  const month = d.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  const startOffset = (firstDay.getDay() + 6) % 7 // 周一开始
  const cells = []
  const today = new Date().toISOString().split('T')[0]

  // 上月补位
  for (let i = startOffset - 1; i >= 0; i--) {
    const date = new Date(year, month, -i)
    const dateStr = date.toISOString().split('T')[0]
    cells.push({
      day: date.getDate(),
      dateStr,
      isCurrentMonth: false,
      isToday: dateStr === today,
      eventCount: props.eventDates.filter(e => e === dateStr).length,
    })
  }

  // 当月
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const date = new Date(year, month, i)
    const dateStr = date.toISOString().split('T')[0]
    cells.push({
      day: i,
      dateStr,
      isCurrentMonth: true,
      isToday: dateStr === today,
      eventCount: props.eventDates.filter(e => e === dateStr).length,
    })
  }

  // 下月补位
  const remaining = 42 - cells.length
  for (let i = 1; i <= remaining; i++) {
    const date = new Date(year, month + 1, i)
    const dateStr = date.toISOString().split('T')[0]
    cells.push({
      day: i,
      dateStr,
      isCurrentMonth: false,
      isToday: dateStr === today,
      eventCount: props.eventDates.filter(e => e === dateStr).length,
    })
  }

  return cells
})

function navigate(dir: number) {
  const d = viewDate.value
  if (props.currentView === 'month') {
    viewDate.value = new Date(d.getFullYear(), d.getMonth() + dir, 1)
  } else if (props.currentView === 'week') {
    viewDate.value = new Date(d.getTime() + dir * 7 * 86400000)
  } else {
    viewDate.value = new Date(d.getTime() + dir * 86400000)
  }
}
</script>

<style scoped>
.calendar-shell {
  display: flex;
  flex-direction: column;
  background: var(--vc-bg-surface);
  border: 1px solid var(--vc-border);
  border-radius: var(--vc-radius-lg);
  overflow: hidden;
}

.calendar-shell__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--vc-space-md) var(--vc-space-lg);
  border-bottom: 1px solid var(--vc-divider);
}

.calendar-shell__nav {
  display: flex;
  align-items: center;
  gap: var(--vc-space-md);
}

.calendar-shell__nav-btn {
  width: 32px;
  height: 32px;
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--vc-text-secondary);
  transition: all var(--vc-transition-fast);
}
.calendar-shell__nav-btn:hover {
  background: var(--vc-bg-elevated);
  color: var(--vc-text-primary);
}

.calendar-shell__title {
  font-size: var(--vc-text-lg);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
  min-width: 160px;
  text-align: center;
}

.calendar-shell__view-toggle {
  display: flex;
  background: var(--vc-bg-elevated);
  border-radius: var(--vc-radius-full);
  padding: 2px;
}

.calendar-shell__view-btn {
  padding: 4px 14px;
  border-radius: var(--vc-radius-full);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-tertiary);
  transition: all var(--vc-transition-fast);
}
.calendar-shell__view-btn--active {
  background: var(--vc-primary);
  color: white;
}

/* 星期头 */
.calendar-shell__weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  padding: var(--vc-space-sm) var(--vc-space-md);
  border-bottom: 1px solid var(--vc-divider);
}

.calendar-shell__weekday {
  text-align: center;
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-tertiary);
  text-transform: uppercase;
}

/* 月网格 */
.calendar-shell__month-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  padding: var(--vc-space-xs);
}

.calendar-shell__day-cell {
  position: relative;
  aspect-ratio: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border-radius: var(--vc-radius-sm);
  transition: all var(--vc-transition-fast);
  cursor: pointer;
}

.calendar-shell__day-cell:hover {
  background: var(--vc-bg-elevated);
}

.calendar-shell__day-cell--other {
  opacity: 0.3;
}

.calendar-shell__day-cell--today .calendar-shell__day-num {
  background: var(--vc-primary);
  color: white;
  width: 28px;
  height: 28px;
  border-radius: var(--vc-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.calendar-shell__day-cell--selected {
  background: hsla(224, 76%, 48%, 0.1);
  border: 1px solid var(--vc-border-active);
}

.calendar-shell__day-num {
  font-size: var(--vc-text-sm);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-primary);
}

.calendar-shell__event-dot {
  width: 5px;
  height: 5px;
  border-radius: var(--vc-radius-full);
  background: var(--vc-primary);
  margin-top: 2px;
}

/* 周/日视图 */
.calendar-shell__week-grid,
.calendar-shell__day-view {
  display: flex;
  flex: 1;
  overflow-y: auto;
  max-height: 500px;
}

.calendar-shell__time-col {
  width: 50px;
  flex-shrink: 0;
  border-right: 1px solid var(--vc-divider);
}

.calendar-shell__time-label {
  display: block;
  height: 60px;
  padding: 2px 8px 0;
  font-size: var(--vc-text-xs);
  color: var(--vc-text-tertiary);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.calendar-shell__days-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  flex: 1;
}

.calendar-shell__day-col {
  border-right: 1px solid var(--vc-divider);
  position: relative;
}
.calendar-shell__day-col:last-child { border-right: none; }

.calendar-shell__day-content {
  flex: 1;
  position: relative;
}

/* 今日摘要 */
.calendar-shell__today-summary {
  padding: var(--vc-space-sm) var(--vc-space-md);
  border-top: 1px solid var(--vc-divider);
  text-align: center;
}

.calendar-shell__today-badge {
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-primary-light);
  background: hsla(224, 76%, 48%, 0.1);
  padding: 2px 12px;
  border-radius: var(--vc-radius-full);
}
</style>
