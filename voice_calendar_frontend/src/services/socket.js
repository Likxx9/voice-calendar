import { io } from 'socket.io-client'
import { store, addLog, addEvent } from './store'

const socket = io({
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: Infinity,
})

socket.on('connect', () => {
  console.log('[SocketIO] 连接成功')
})

socket.on('disconnect', () => {
  console.log('[SocketIO] 连接断开')
})

socket.on('server_event', (msg) => {
  const { type, data } = msg

  switch (type) {
    case 'listening_start':
      store.voiceState = 'listening'
      break

    case 'listening_stop':
      if (store.voiceState === 'listening') {
        store.voiceState = 'processing'
      }
      break

    case 'asr_interim':
      if (store.voiceState !== 'listening') store.voiceState = 'listening'
      store.currentQuery = data.text
      break

    case 'asr_result':
      if (data.final && data.text.trim()) {
        store.currentQuery = data.text
        store.voiceState = 'processing'
        store.alog = []
        store.hasConflict = false
        store.conflictInfo = null
        store.timeSuggestion = null
        addLog('[ASR] 识别完成：' + data.text)
      }
      break

    case 'agent_thinking':
      if (store.voiceState !== 'processing') store.voiceState = 'processing'
      addLog(`[Agent] ${data.message}`)
      break

    case 'tool_call':
      addLog(`[Tool] 调用 ${data.tool}`, 's')
      break

    case 'tool_result':
      addLog(`[Tool] 执行完成`, 's')
      break

    case 'event_created':
      console.log('[SocketIO] event_created received:', data)
      addEvent({
        title: data.title,
        start_time: data.start_time,
        end_time: data.end_time,
      })
      addLog(`[日程] 已创建：${data.title}`, 's')
      break

    case 'event_updated': {
      console.log('[SocketIO] event_updated received:', data)
      const oldTitle = data.old_title || data.title
      const idx = store.events.findIndex(e => e.title === oldTitle)
      if (idx !== -1) {
        store.events.splice(idx, 1)
      }
      addEvent({
        title: data.title,
        start_time: data.start_time,
        end_time: data.end_time,
      })
      addLog(`[日程] 已修改：${oldTitle} → ${new Date(data.start_time).getMonth()+1}月${new Date(data.start_time).getDate()}日 ${new Date(data.start_time).getHours()}:${String(new Date(data.start_time).getMinutes()).padStart(2,'0')}`, 's')
      break
    }

    case 'time_suggestion': {
      const sugStart = new Date(data.suggested_start)
      const timeStr = `${sugStart.getMonth()+1}月${sugStart.getDate()}日 ${sugStart.getHours()}:${String(sugStart.getMinutes()).padStart(2,'0')}`
      const reason = data.reason || '未指定时间'
      addLog(`[智能推荐] "${data.title}"${reason}，已安排到：${timeStr}`, 's')
      if (data.alternatives && data.alternatives.length > 1) {
        const altTexts = data.alternatives.slice(1, 4).map(a => {
          const d = new Date(a.start)
          return `${d.getMonth()+1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}(${a.duration_minutes}分钟)`
        })
        addLog(`[备选时段] ${altTexts.join('、')}`)
      }
      store.timeSuggestion = data
      break
    }

    case 'conflict_detected':
      addLog(`[⚠ 冲突] "${data.new_event}"与"${data.conflicting_events.map(e => e.title).join('、')}"时间冲突，正在自动调整...`, 'w')
      store.hasConflict = true
      store.conflictInfo = data
      break

    case 'tts_text':
      addLog(`[Agent] ${data.text}`)
      store.voiceState = 'done'
      break

    case 'session_end':
      addLog(`[System] ${data.message}`)
      setTimeout(() => {
        store.voiceState = 'idle'
        store.currentQuery = ''
      }, 5000)
      break
  }
})

export function sendVoiceInput(text) {
  if (text.trim()) {
    socket.emit('voice_input', { text: text.trim() })
  }
}

export function startBackendRecording() {
  socket.emit('start_recording')
}

export default socket
