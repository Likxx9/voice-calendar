import { reactive } from 'vue'

export const store = reactive({
  events: [
    { col: 1, id: 1, title: '高管周会', s: 9.5, e: 11, c: 'gold', loc: '会议室A', type: '会议', isNew: false, att: 8 },
    { col: 2, id: 2, title: '产品评审', s: 13, e: 15, c: 'blue', loc: '线上会议', type: '项目', isNew: false, att: 12 },
    { col: 3, id: 3, title: '战略研讨会', s: 10, e: 12.5, c: 'red', loc: 'CEO办公室', type: '战略', isNew: false, att: 4 },
  ],
  alog: [], // Agent 终端日志
  voiceState: 'idle', // idle, listening, processing, done
  currentQuery: '',
  hasConflict: false,
  conflictInfo: null,
  timeSuggestion: null,
  
  // Calendar Interactivity State
  currentDate: new Date(),
  currentView: 'week',
  modalVisible: false,
  selectedEvent: null,
  calendars: {
    executive: true,
    project: true
  }
})

export function addLog(text, tagClass = '') {
  store.alog.push({
    id: Date.now() + Math.random(),
    text,
    tagClass
  })
}

export function addEvent(eventData) {
  let col = new Date().getDay()
  let s = 14
  let e = 15
  let st = new Date()

  try {
    if (eventData.start_time) {
      st = new Date(eventData.start_time)
      col = st.getDay()
      s = st.getHours() + st.getMinutes() / 60
    }
    if (eventData.end_time) {
      const et = new Date(eventData.end_time)
      e = et.getHours() + et.getMinutes() / 60
    }
  } catch (err) {}

  const newEvent = {
    col,
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
    calScroll.scrollTop = Math.max(0, (hr - 8 - 1) * 52)
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
