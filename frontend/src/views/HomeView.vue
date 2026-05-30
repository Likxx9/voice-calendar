<template>
  <div class="home-view vc-anim-fade-in">
    <!-- 极简今日问候 -->
    <header class="home-view__header">
      <h2 class="greeting-text">你好，今天是 {{ formattedToday }}</h2>
      <p class="greeting-subtext">接下来的 48 小时，您有 {{ upcomingEventsCount }} 项日程</p>
    </header>

    <!-- 沉浸式智能日程流视图 -->
    <main class="home-view__timeline">
      <TimelineView 
        :events="calendarStore.activeEvents"
        @event-click="onEventClick"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useCalendarStore } from '@/stores/useCalendarStore'
import TimelineView from '@/modules/calendar/TimelineView.vue'

const calendarStore = useCalendarStore()

const formattedToday = computed(() => {
  return new Date().toLocaleDateString('zh-CN', { month: 'long', day: 'numeric', weekday: 'long' })
})

const upcomingEventsCount = computed(() => {
  // 简易计算：仅作为演示，实际可结合过滤逻辑
  return calendarStore.activeEvents.length
})

function onEventClick(eventId: string) {
  console.log('Event clicked, ID:', eventId)
}

// 模拟初始化一些精美的种子数据以便用户体验
onMounted(() => {
  if (calendarStore.events.length === 0 && calendarStore.tasks.length === 0) {
    const todayStr = new Date().toISOString().split('T')[0]
    
    calendarStore.setEvents([
      {
        id: 'ev-1',
        title: '晨会与项目周报同步',
        start_time: `${todayStr}T09:30:00`,
        end_time: `${todayStr}T10:30:00`,
        location: '会议室 A',
        calendar_id: 'work',
        calendar_name: '工作',
        color: 'var(--vc-primary)',
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
        attendees: ['architect@corp.com', 'pm@corp.com', 'design@corp.com', 'test@corp.com'],
        calendar_id: 'work',
        calendar_name: '工作',
        color: '#8B5CF6',
        is_deleted: false,
        version_tag: 'v1',
        created_at: new Date().toISOString()
      },
      {
        id: 'ev-3',
        title: '商务晚宴',
        start_time: `${todayStr}T18:30:00`,
        end_time: `${todayStr}T20:30:00`,
        location: '丽思卡尔顿酒店',
        calendar_id: 'work',
        calendar_name: '工作',
        color: '#F56A00',
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
  height: 100%;
}

.home-view__header {
  padding: var(--vc-space-md) 0 var(--vc-space-sm);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.greeting-text {
  font-size: var(--vc-text-xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  letter-spacing: -0.5px;
  margin: 0;
}

.greeting-subtext {
  font-size: var(--vc-text-sm);
  color: var(--vc-text-secondary);
  margin: 0;
}

.home-view__timeline {
  flex: 1;
  margin-top: var(--vc-space-md);
  position: relative;
  /* 取消边框，融入背景 */
  background: transparent;
  border: none;
  box-shadow: none;
}
</style>
