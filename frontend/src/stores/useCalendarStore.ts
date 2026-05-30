/* ============================================================
 * Pinia Store — 日历事件与待办任务数据管理
 *
 * 纯数据容器：只负责存储后端下发的数据，不做任何过滤/分析。
 * 所有数据查询（今日事件、按日期筛选等）由后端 API 完成。
 * ============================================================ */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { CalendarEvent, TodoTask } from '@/types/contracts'

export const useCalendarStore = defineStore('calendar', () => {
  // ── 数据（由后端下发） ──────────────────────────────
  const events = ref<CalendarEvent[]>([])
  const tasks = ref<TodoTask[]>([])
  const currentView = ref<'month' | 'week' | 'day'>('week')
  const selectedDate = ref<string>(new Date().toISOString().split('T')[0])
  const isLoading = ref(false)

  // ── 动作：只做数据存取，不做分析 ────────────────────
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

  /** 批量替换事件列表（后端查询结果整体下发） */
  function setEvents(newEvents: CalendarEvent[]) {
    events.value = newEvents
  }

  /** 批量替换任务列表（后端查询结果整体下发） */
  function setTasks(newTasks: TodoTask[]) {
    tasks.value = newTasks
  }

  return {
    events,
    tasks,
    currentView,
    selectedDate,
    isLoading,
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
