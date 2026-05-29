/* ============================================================
 * Pinia Store — 日历事件与待办任务数据管理
 * 支持本地缓存、乐观更新、离线操作日志
 * ============================================================ */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CalendarEvent, TodoTask } from '@/types/contracts'

export const useCalendarStore = defineStore('calendar', () => {
  // ── 数据 ─────────────────────────────────────────
  const events = ref<CalendarEvent[]>([])
  const tasks = ref<TodoTask[]>([])
  const currentView = ref<'month' | 'week' | 'day'>('week')
  const selectedDate = ref<string>(new Date().toISOString().split('T')[0])
  const isLoading = ref(false)

  // ── 计算属性 ─────────────────────────────────────
  const activeEvents = computed(() =>
    events.value.filter((e: CalendarEvent) => !e.is_deleted)
  )

  const activeTasks = computed(() =>
    tasks.value.filter((t: TodoTask) => !t.is_deleted)
  )

  const pendingTasks = computed(() =>
    activeTasks.value.filter((t: TodoTask) => !t.is_completed)
  )

  const todayEvents = computed(() => {
    const today = new Date().toISOString().split('T')[0]
    return activeEvents.value.filter((e: CalendarEvent) => e.start_time.startsWith(today))
  })

  const eventsForSelectedDate = computed(() => {
    return activeEvents.value.filter((e: CalendarEvent) =>
      e.start_time.startsWith(selectedDate.value)
    )
  })

  // ── 动作 ─────────────────────────────────────────
  function addEvent(event: CalendarEvent) {
    const existingIdx = events.value.findIndex((e: CalendarEvent) => e.id === event.id)
    if (existingIdx >= 0) {
      events.value[existingIdx] = event
    } else {
      events.value.push(event)
    }
  }

  function updateEvent(eventId: string, updates: Partial<CalendarEvent>) {
    const idx = events.value.findIndex((e: CalendarEvent) => e.id === eventId)
    if (idx >= 0) {
      events.value[idx] = { ...events.value[idx], ...updates }
    }
  }

  function removeEvent(eventId: string) {
    const idx = events.value.findIndex((e: CalendarEvent) => e.id === eventId)
    if (idx >= 0) {
      events.value[idx].is_deleted = true
    }
  }

  function addTask(task: TodoTask) {
    const existingIdx = tasks.value.findIndex((t: TodoTask) => t.id === task.id)
    if (existingIdx >= 0) {
      tasks.value[existingIdx] = task
    } else {
      tasks.value.push(task)
    }
  }

  function updateTask(taskId: string, updates: Partial<TodoTask>) {
    const idx = tasks.value.findIndex((t: TodoTask) => t.id === taskId)
    if (idx >= 0) {
      tasks.value[idx] = { ...tasks.value[idx], ...updates }
    }
  }

  function toggleTaskComplete(taskId: string) {
    const idx = tasks.value.findIndex((t: TodoTask) => t.id === taskId)
    if (idx >= 0) {
      tasks.value[idx].is_completed = !tasks.value[idx].is_completed
    }
  }

  function setView(view: 'month' | 'week' | 'day') {
    currentView.value = view
  }

  function setSelectedDate(date: string) {
    selectedDate.value = date
  }

  function setEvents(newEvents: CalendarEvent[]) {
    events.value = newEvents
  }

  function setTasks(newTasks: TodoTask[]) {
    tasks.value = newTasks
  }

  return {
    events,
    tasks,
    currentView,
    selectedDate,
    isLoading,
    activeEvents,
    activeTasks,
    pendingTasks,
    todayEvents,
    eventsForSelectedDate,
    addEvent,
    updateEvent,
    removeEvent,
    addTask,
    updateTask,
    toggleTaskComplete,
    setView,
    setSelectedDate,
    setEvents,
    setTasks,
  }
})
