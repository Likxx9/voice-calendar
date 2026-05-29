<template>
  <div class="home-view vc-anim-fade-in">
    <!-- 今日问候与快速概览 -->
    <header class="home-view__greeting">
      <h2 class="greeting-text">你好，今天是 {{ formattedToday }}</h2>
      <p class="greeting-subtext">今天有 {{ todayEvents.length }} 项日程与 {{ pendingTasks.length }} 个待办</p>
    </header>

    <!-- 主日历区 -->
    <section class="home-view__calendar">
      <CalendarShell
        :currentView="calendarStore.currentView"
        :selectedDate="calendarStore.selectedDate"
        :todayEventCount="todayEvents.length"
        :eventDates="eventDates"
        @view-change="calendarStore.setView"
        @date-select="calendarStore.setSelectedDate"
      >
        <!-- 周视图日程渲染 -->
        <template #week-events="{ dayIndex }">
          <EventCard
            v-for="event in getEventsForDayIndex(dayIndex)"
            :key="event.id"
            :title="event.title"
            :start-time="event.start_time"
            :end-time="event.end_time"
            :color="event.color"
            :compact="true"
            :style="getEventStyle(event)"
            @click="onEventClick(event.id)"
          />
        </template>

        <!-- 日视图日程渲染 -->
        <template #day-events>
          <EventCard
            v-for="event in dayViewEvents"
            :key="event.id"
            :title="event.title"
            :start-time="event.start_time"
            :end-time="event.end_time"
            :location="event.location"
            :color="event.color"
            :compact="false"
            :style="getEventStyle(event)"
            @click="onEventClick(event.id)"
          />
        </template>
      </CalendarShell>
    </section>

    <!-- 线性时间轴 & 待办看板 -->
    <div class="home-view__content-grid">
      <!-- 今日时间轴 -->
      <section class="content-panel vc-elevated">
        <h3 class="panel-title">📅 日程时间轴</h3>
        <TimelineView 
          :events="calendarStore.eventsForSelectedDate"
          @event-click="onEventClick"
        />
      </section>

      <!-- 待办任务 -->
      <section class="content-panel vc-elevated">
        <div class="panel-header">
          <h3 class="panel-title">📋 待办任务</h3>
          <span class="task-badge">{{ pendingTasks.length }} 未完成</span>
        </div>
        <div class="task-list">
          <div v-if="activeTasks.length === 0" class="task-list__empty">
            无待办任务，说 “帮我加个买牛奶的待办” 试试吧
          </div>
          <TaskItem
            v-for="task in activeTasks"
            :key="task.id"
            :title="task.title"
            :dueTime="task.due_time"
            :priority="task.priority"
            :isCompleted="task.is_completed"
            @toggle="calendarStore.toggleTaskComplete(task.id)"
            @delete="calendarStore.updateTask(task.id, { is_deleted: true })"
          />
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useCalendarStore } from '@/stores/useCalendarStore'
import CalendarShell from '@/modules/calendar/CalendarShell.vue'
import TimelineView from '@/modules/calendar/TimelineView.vue'
import TaskItem from '@/modules/calendar/TaskItem.vue'
import EventCard from '@/modules/calendar/EventCard.vue'
import type { CalendarEvent } from '@/types/contracts'

const calendarStore = useCalendarStore()

// 格式化今日日期
const formattedToday = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { weekday: 'long', month: 'long', day: 'numeric' })
})

const todayEvents = computed(() => calendarStore.todayEvents)
const pendingTasks = computed(() => calendarStore.pendingTasks)
const activeTasks = computed(() => calendarStore.activeTasks)

// 获取所有有日程的日期，用于日历小红点
const eventDates = computed(() => {
  return calendarStore.activeEvents.map(e => e.start_time.split('T')[0])
})

function onEventClick(eventId: string) {
  // 可以展示事件详情 Modal 或语音朗读
  console.log('Event clicked, ID:', eventId)
}

// ── 日历日程定位与过滤计算 ──────────────────────────

// 计算某日期所在周的周一
function getStartOfWeek(dateStr: string): Date {
  const date = new Date(dateStr)
  const day = date.getDay()
  // 将星期日(0)视为第6天，星期一(1)视为第0天进行调整
  const diff = date.getDate() - day + (day === 0 ? -6 : 1)
  return new Date(date.setDate(diff))
}

// 根据周内天数索引 (1~7) 获取对应日期的日程
function getEventsForDayIndex(dayIndex: number): CalendarEvent[] {
  const startOfWeek = getStartOfWeek(calendarStore.selectedDate)
  const targetDate = new Date(startOfWeek)
  targetDate.setDate(startOfWeek.getDate() + (dayIndex - 1))
  const targetStr = targetDate.toISOString().split('T')[0]
  
  return calendarStore.activeEvents.filter(e => e.start_time.startsWith(targetStr))
}

// 获取选定日期的日程（用于单日视图）
const dayViewEvents = computed(() => {
  return calendarStore.activeEvents.filter(e => e.start_time.startsWith(calendarStore.selectedDate))
})

// 根据日程起止时间计算其在 7:00 ~ 20:00 网格中的 absolute 位置样式
function getEventStyle(event: CalendarEvent) {
  const start = new Date(event.start_time)
  const end = new Date(event.end_time)
  
  const startHour = start.getHours() + start.getMinutes() / 60
  const endHour = end.getHours() + end.getMinutes() / 60
  
  // 网格时间以 7:00 AM 开始，每小时 60px 高度
  const top = Math.max(0, (startHour - 7) * 60)
  const height = Math.max(30, (endHour - startHour) * 60) // 最低高度 30px
  
  return {
    position: 'absolute' as const,
    top: `${top}px`,
    height: `${height}px`,
    left: '2px',
    right: '2px',
    zIndex: 10
  }
}

// 模拟初始化一些精美的种子数据以便用户体验
onMounted(() => {
  if (calendarStore.events.length === 0 && calendarStore.tasks.length === 0) {
    const todayStr = new Date().toISOString().split('T')[0]
    
    // 初始化事件
    calendarStore.setEvents([
      {
        id: 'ev-1',
        title: '晨会与项目周报同步',
        start_time: `${todayStr}T09:30:00`,
        end_time: `${todayStr}T10:30:00`,
        location: '会议室 A',
        calendar_id: 'work',
        calendar_name: '工作',
        color: '#3B82F6',
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      },
      {
        id: 'ev-2',
        title: '语音日历前端架构评审',
        start_time: `${todayStr}T14:00:00`,
        end_time: `${todayStr}T15:30:00`,
        location: '虚拟腾讯会议',
        attendees: ['architect@corp.com', 'pm@corp.com'],
        calendar_id: 'work',
        calendar_name: '工作',
        color: '#8B5CF6',
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      },
      {
        id: 'ev-3',
        title: '健身房有氧训练与拉伸',
        start_time: `${todayStr}T18:30:00`,
        end_time: `${todayStr}T19:30:00`,
        location: '舒适健身房',
        calendar_id: 'personal',
        calendar_name: '生活',
        color: '#10B981',
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      }
    ])

    // 初始化任务
    calendarStore.setTasks([
      {
        id: 'task-1',
        title: '完成 M1 语音感知模块单元测试',
        priority: 'high',
        is_completed: false,
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      },
      {
        id: 'task-2',
        title: '确认 Web Speech API 中文 TTS 在 Edge 的兼容性',
        priority: 'medium',
        is_completed: false,
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      },
      {
        id: 'task-3',
        title: '设计盲听模式下的快捷交互说明书',
        priority: 'low',
        is_completed: true,
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      }
    ])
  }
})
</script>

<style scoped>
.home-view {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-lg);
}

.home-view__greeting {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.greeting-text {
  font-size: var(--vc-text-xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
}

.greeting-subtext {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
}

.home-view__calendar {
  width: 100%;
}

.home-view__content-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--vc-space-md);
}

@media (min-width: 768px) {
  .home-view__content-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.content-panel {
  padding: var(--vc-space-md);
  min-height: 280px;
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-md);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-semibold);
  color: var(--vc-text-primary);
}

.task-badge {
  font-size: var(--vc-text-xs);
  background: hsla(0, 78%, 56%, 0.1);
  color: var(--vc-danger);
  padding: 2px 8px;
  border-radius: var(--vc-radius-full);
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-sm);
  overflow-y: auto;
  max-height: 320px;
}

.task-list__empty {
  text-align: center;
  color: var(--vc-text-tertiary);
  font-size: var(--vc-text-sm);
  padding: var(--vc-space-xl) 0;
}
</style>
