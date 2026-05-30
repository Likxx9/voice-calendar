<template>
  <div class="right-calendar">
    <header class="calendar-header">
      <div class="month-year">
        <h1>2026年 5月</h1>
      </div>
      <div class="segment-control">
        <button class="segment-btn">年</button>
        <button class="segment-btn">月</button>
        <button class="segment-btn active">周</button>
      </div>
    </header>

    <!-- 骨架屏占位 (仅演示) -->
    <div v-if="isLoading" class="skeleton-screen">
      <div class="skeleton-item" v-for="i in 5" :key="i"></div>
    </div>

    <!-- 核心时间线 -->
    <main v-else class="calendar-body">
      <TimelineView 
        :events="calendarStore.events"
        @event-click="onEventClick"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useCalendarStore } from '@/stores/useCalendarStore'
import TimelineView from '@/modules/calendar/TimelineView.vue'

const calendarStore = useCalendarStore()
const isLoading = ref(true)

function onEventClick(eventId: string) {
  console.log('Event clicked:', eventId)
}

onMounted(() => {
  // 模拟拉取数据时的骨架屏过渡
  setTimeout(() => {
    isLoading.value = false
  }, 800)
})
</script>

<style scoped>
.right-calendar {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  background-color: var(--vc-bg-surface);
  display: flex;
  flex-direction: column;
}

.calendar-header {
  padding: env(safe-area-inset-top) var(--vc-space-lg) var(--vc-space-md);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid var(--vc-divider);
  background: var(--vc-bg-surface);
}

.month-year h1 {
  font-size: var(--vc-text-2xl);
  font-weight: var(--vc-weight-bold);
  color: var(--vc-text-primary);
  margin: 0;
  letter-spacing: -0.5px;
}

.segment-control {
  display: flex;
  background: var(--vc-bg-base);
  border-radius: var(--vc-radius-md);
  padding: 2px;
}

.segment-btn {
  padding: 4px 12px;
  border-radius: var(--vc-radius-sm);
  font-size: var(--vc-text-xs);
  font-weight: var(--vc-weight-medium);
  color: var(--vc-text-secondary);
  transition: all var(--vc-transition-fast);
}

.segment-btn.active {
  background: var(--vc-bg-surface);
  color: var(--vc-text-primary);
  box-shadow: var(--vc-shadow-sm);
}

.calendar-body {
  flex: 1;
  overflow-y: auto;
  padding-bottom: env(safe-area-inset-bottom);
}

/* Skeleton Screen */
.skeleton-screen {
  flex: 1;
  padding: var(--vc-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--vc-space-lg);
}

.skeleton-item {
  height: 80px;
  background: linear-gradient(90deg, var(--vc-bg-base) 25%, var(--vc-divider) 50%, var(--vc-bg-base) 75%);
  background-size: 400% 100%;
  border-radius: var(--vc-radius-md);
  animation: skeleton-loading 1.5s infinite ease-in-out;
}

@keyframes skeleton-loading {
  0% { background-position: 100% 50%; }
  100% { background-position: 0 50%; }
}
</style>
