/**
 * API Service
 * 后端API服务
 */

const API_BASE_URL = 'http://localhost:8000'

export interface CalendarEvent {
  id?: string
  user_id: string
  title: string
  description?: string
  location?: string
  start_time: string
  end_time: string
  timezone?: string
  color?: string
  reminder_minutes?: number
}

export interface ConflictResult {
  has_conflict: boolean
  conflicts: CalendarEvent[]
}

// 创建日历事件
export async function createEvent(event: CalendarEvent): Promise<CalendarEvent> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/events?user_id=${event.user_id}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(event),
  })
  
  if (!response.ok) {
    throw new Error('创建事件失败')
  }
  
  const data = await response.json()
  return data.event
}

// 获取事件列表
export async function getEvents(userId: string, startDate?: string, endDate?: string): Promise<CalendarEvent[]> {
  const params = new URLSearchParams({ user_id: userId })
  if (startDate) params.append('start_date', startDate)
  if (endDate) params.append('end_date', endDate)
  
  const response = await fetch(`${API_BASE_URL}/api/calendar/events?${params}`)
  
  if (!response.ok) {
    throw new Error('获取事件失败')
  }
  
  const data = await response.json()
  return data.events
}

// 检查时间冲突
export async function checkConflicts(
  userId: string,
  startTime: string,
  endTime: string
): Promise<ConflictResult> {
  const params = new URLSearchParams({
    user_id: userId,
    start_time: startTime,
    end_time: endTime,
  })
  
  const response = await fetch(`${API_BASE_URL}/api/calendar/conflicts?${params}`)
  
  if (!response.ok) {
    throw new Error('检查冲突失败')
  }
  
  return await response.json()
}

// 删除事件
export async function deleteEvent(eventId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/calendar/events/${eventId}`, {
    method: 'DELETE',
  })
  
  if (!response.ok) {
    throw new Error('删除事件失败')
  }
}

// 健康检查
export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/health`)
    return response.ok
  } catch {
    return false
  }
}
