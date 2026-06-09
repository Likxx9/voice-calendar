import { reactive } from 'vue'

// 从 localStorage 恢复聊天历史
function loadChatHistory() {
  try {
    const saved = localStorage.getItem('voical_chat_history')
    if (saved) {
      const parsed = JSON.parse(saved)
      if (Array.isArray(parsed)) return parsed.slice(-200) // 最多保留200条
    }
  } catch (e) {}
  return []
}

// 恢复登录状态
function loadAuthState() {
  try {
    const token = localStorage.getItem('voical_token')
    const user = localStorage.getItem('voical_user')
    if (token && user) return { token, user: JSON.parse(user) }
  } catch (e) {}
  return { token: null, user: null }
}

const savedAuth = loadAuthState()

function loadSettings() {
  try {
    const s = localStorage.getItem('voical_settings')
    if (s) return JSON.parse(s)
  } catch (e) {}
  return {}
}
const savedSettings = loadSettings()

export const store = reactive({
  // Auth
  authToken: savedAuth.token,
  currentUser: savedAuth.user,

  // Settings
  settings: {
    ttsSpeed: savedSettings.ttsSpeed ?? 50,
    ttsVoice: savedSettings.ttsVoice ?? 'xiaoyan',
    asrLanguage: savedSettings.asrLanguage ?? 'zh_cn',
    wakeWord: savedSettings.wakeWord ?? '',
    defaultView: savedSettings.defaultView ?? 'week',
    workHourStart: savedSettings.workHourStart ?? 9,
    workHourEnd: savedSettings.workHourEnd ?? 18,
    weekStartDay: savedSettings.weekStartDay ?? 0,
    reminderDefault: savedSettings.reminderDefault ?? 15,
    theme: savedSettings.theme ?? 'dark',
  },

  events: [],
  alog: loadChatHistory(),
  voiceState: 'idle', // idle, listening, processing, done
  currentQuery: '',
  hasConflict: false,
  conflictInfo: null,
  timeSuggestion: null,
  trainOptions: null,
  transportOptions: null,
  micError: null,

  // Calendar Interactivity State
  currentDate: new Date(),
  currentView: window.innerWidth <= 767 ? 'day' : 'week',
  modalVisible: false,
  selectedEvent: null,
  calendars: {
    executive: true,
    project: true
  },

  // Mobile specific state
  isMobile: window.innerWidth <= 767,
  mobileTab: 'today', // today, calendar, voice, tasks, profile
  showVoiceFullscreen: false
})

window.addEventListener('resize', () => {
  const isMobile = window.innerWidth <= 767;
  if (store.isMobile !== isMobile) {
    store.isMobile = isMobile;
    store.currentView = isMobile ? 'day' : 'week';
  }
})

export function addLog(text, tagClass = '') {
  const now = new Date()
  store.alog.push({
    id: Date.now() + Math.random(),
    text,
    tagClass,
    time: `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}`,
  })
  // 持久化到 localStorage
  try {
    const toSave = store.alog.slice(-200)
    localStorage.setItem('voical_chat_history', JSON.stringify(toSave))
  } catch (e) {}
}

export function clearChatHistory() {
  store.alog = []
  try { localStorage.removeItem('voical_chat_history') } catch (e) {}
}

// 剥掉时区后缀，强制当作本地时间解析，避免 UTC 时差导致幽灵日程
function parseLocalTime(iso) {
  if (!iso) return null
  // 去掉 Z / +08:00 / -05:00 等后缀
  const s = String(iso).replace(/[Zz]$/, '').replace(/[+-]\d{2}:\d{2}$/, '')
  const d = new Date(s)
  return isNaN(d.getTime()) ? null : d
}

export function addEvent(eventData) {
  let s = 14
  let e = 15
  let st = new Date()

  try {
    if (eventData.start_time) {
      st = parseLocalTime(eventData.start_time) || new Date()
      s = st.getHours() + st.getMinutes() / 60
    }
    if (eventData.end_time) {
      const et = parseLocalTime(eventData.end_time) || st
      e = et.getHours() + et.getMinutes() / 60
    }
  } catch (err) { }

  const newEvent = {
    col: st.getDay(),
    dateStr: st.toDateString(),
    id: Date.now(),
    title: eventData.title || '新日程',
    s,
    e,
    c: 'amber',
    loc: eventData.location || '',
    type: '新事件',
    isNew: true,
    att: 2
  }
  console.log('[Store] addEvent:', newEvent)
  store.events.push(newEvent)

  // 跳转日历视图到新建事件的日期
  store.currentDate = st
}

// Calendar Actions
export function shiftDate(delta) {
  const newDate = new Date(store.currentDate)
  if (store.currentView === 'day') {
    newDate.setDate(newDate.getDate() + delta)
  } else if (store.currentView === 'week') {
    newDate.setDate(newDate.getDate() + delta * 7)
  } else if (store.currentView === 'month') {
    newDate.setMonth(newDate.getMonth() + delta)
  }
  store.currentDate = newDate
}

export function goToday() {
  store.currentDate = new Date()
  const calScroll = document.getElementById('cal-scroll')
  if (calScroll) {
    const hr = new Date().getHours()
    calScroll.scrollTop = Math.max(0, (hr - 6 - 1) * 52)
  }
}

export function setView(view) {
  store.currentView = view
}

export function openModal(event) {
  store.selectedEvent = event
  store.modalVisible = true
}

export function closeModal() {
  store.modalVisible = false
  store.selectedEvent = null
}

export function toggleCalendar(key) {
  store.calendars[key] = !store.calendars[key]
}

// ── Auth ────────────────────────────────────────────────
export function loginSuccess(user) {
  store.currentUser = user
  store.authToken = localStorage.getItem('voical_token')
  fetchEvents()
}

export function logout() {
  store.authToken = null
  store.currentUser = null
  store.events = []
  localStorage.removeItem('voical_token')
  localStorage.removeItem('voical_user')
}

export function saveSettings() {
  try {
    localStorage.setItem('voical_settings', JSON.stringify(store.settings))
  } catch (e) {}
}

export function updateUser(userData) {
  store.currentUser = { ...store.currentUser, ...userData }
  localStorage.setItem('voical_user', JSON.stringify(store.currentUser))
}

export function isLoggedIn() {
  return !!(store.authToken && store.currentUser)
}

// ── 从后端加载真实日程 ──────────────────────────────────
export async function fetchEvents() {
  try {
    const resp = await fetch('/api/events')
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(`HTTP ${resp.status}: ${text.slice(0, 200)}`)
    }
    const data = await resp.json()

    const events = data.map(ev => {
      const st = parseLocalTime(ev.start_time) || new Date(ev.start_time)
      const et = ev.end_time ? (parseLocalTime(ev.end_time) || new Date(ev.end_time)) : null
      return {
        ...ev,
        dateStr: st.toDateString(),
        col: st.getDay(),
        s: ev.s ?? (st.getHours() + st.getMinutes() / 60),
        e: ev.e ?? (et ? et.getHours() + et.getMinutes() / 60 : st.getHours() + 1),
      }
    })

    store.events = events
    console.log(`[Store] 从后端加载了 ${events.length} 条日程`, events)
  } catch (err) {
    console.error('[Store] 加载日程失败:', err)
  }
}

export async function deleteEvent(eventId) {
  try {
    const resp = await fetch(`/api/events/${eventId}`, {
      method: 'DELETE'
    })
    if (!resp.ok) {
      const text = await resp.text()
      throw new Error(`HTTP ${resp.status}: ${text.slice(0, 200)}`)
    }
    console.log(`[Store] 成功删除日程 ${eventId}`)
    await fetchEvents()
    addLog(`[System] 日程已取消`, 's')
  } catch (err) {
    console.error('[Store] 删除日程失败:', err)
  }
}

// 启动时如果已登录则加载日程
if (store.authToken) {
  fetchEvents()
}
