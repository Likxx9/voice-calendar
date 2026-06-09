import { io } from 'socket.io-client'
import { store, addLog, fetchEvents } from './store'

const socket = io({
  reconnection: true,
  reconnectionDelay: 1000,
  reconnectionDelayMax: 5000,
  reconnectionAttempts: Infinity,
})

// --- PCM Player for TTS ---
class PCMPlayer {
  constructor(sampleRate = 16000) {
    this.sampleRate = sampleRate
    this.audioCtx = null
    this.nextStartTime = 0
  }

  init() {
    if (!this.audioCtx) {
      this.audioCtx = new (window.AudioContext || window.webkitAudioContext)()
      this.nextStartTime = this.audioCtx.currentTime
    }
    if (this.audioCtx.state === 'suspended') {
      this.audioCtx.resume()
    }
  }

  playChunk(arrayBuffer) {
    this.init()

    const int16Array = new Int16Array(arrayBuffer)
    const float32Array = new Float32Array(int16Array.length)
    for (let i = 0; i < int16Array.length; i++) {
      float32Array[i] = int16Array[i] / 32768.0
    }

    const audioBuffer = this.audioCtx.createBuffer(1, float32Array.length, this.sampleRate)
    audioBuffer.copyToChannel(float32Array, 0)

    const source = this.audioCtx.createBufferSource()
    source.buffer = audioBuffer
    source.connect(this.audioCtx.destination)

    const currentTime = this.audioCtx.currentTime
    if (this.nextStartTime < currentTime) {
      this.nextStartTime = currentTime
    }
    source.start(this.nextStartTime)
    this.nextStartTime += audioBuffer.duration
  }

  stop() {
    if (this.audioCtx) {
      try {
        this.audioCtx.close()
      } catch (e) {
        console.error(e)
      }
      this.audioCtx = null
    }
  }
}

const pcmPlayer = new PCMPlayer(16000)

// --- Browser Recording State ---
let audioContext = null
let mediaStream = null
let processorNode = null
let sourceNode = null

function downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
  if (inputSampleRate === outputSampleRate) {
    return buffer
  }
  const sampleRateRatio = inputSampleRate / outputSampleRate
  const newLength = Math.round(buffer.length / sampleRateRatio)
  const result = new Float32Array(newLength)
  for (let i = 0; i < newLength; i++) {
    const index = i * sampleRateRatio
    const left = Math.floor(index)
    const right = Math.min(buffer.length - 1, left + 1)
    const weight = index - left
    result[i] = buffer[left] * (1 - weight) + buffer[right] * weight
  }
  return result
}

function floatTo16BitPCM(output, offset, input) {
  for (let i = 0; i < input.length; i++, offset += 2) {
    let s = Math.max(-1, Math.min(1, input[i]))
    output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7FFF, true)
  }
}

async function startBrowserRecording() {
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    store.micError = 'secure_context_required'
    console.error("Browser does not support mediaDevices.getUserMedia")
    return
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        sampleRate: 16000,
        echoCancellation: true,
        noiseSuppression: true,
      }
    })

    audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const inputSampleRate = audioContext.sampleRate
    const outputSampleRate = 16000

    sourceNode = audioContext.createMediaStreamSource(mediaStream)
    processorNode = audioContext.createScriptProcessor(4096, 1, 1)

    processorNode.onaudioprocess = (e) => {
      const inputData = e.inputBuffer.getChannelData(0)
      const downsampled = downsampleBuffer(inputData, inputSampleRate, outputSampleRate)
      const buffer = new ArrayBuffer(downsampled.length * 2)
      const view = new DataView(buffer)
      floatTo16BitPCM(view, 0, downsampled)

      if (socket.connected) {
        socket.emit('audio_chunk', buffer)
      }
    }

    sourceNode.connect(processorNode)
    processorNode.connect(audioContext.destination)
    console.log("[AudioRecorder] Browser recording started, input sample rate:", inputSampleRate)
  } catch (err) {
    console.error("Failed to start browser recording:", err)
    store.micError = 'permission_denied'
  }
}

function stopBrowserRecording() {
  if (processorNode) {
    processorNode.disconnect()
    processorNode = null
  }
  if (sourceNode) {
    sourceNode.disconnect()
    sourceNode = null
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach(track => track.stop())
    mediaStream = null
  }
  if (audioContext) {
    audioContext.close()
    audioContext = null
  }
  console.log("[AudioRecorder] Browser recording stopped")
}


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
        store.hasConflict = false
        store.conflictInfo = null
        store.timeSuggestion = null
        store.trainOptions = null
        store.transportOptions = null
        
        const lastLog = store.alog[store.alog.length - 1]
        if (!lastLog || lastLog.text !== data.text || lastLog.tagClass !== 'u') {
          addLog(data.text, 'u')
        }
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
      addLog(`[日程] 已创建：${data.title}`, 's')
      if (data.start_time) {
        store.currentDate = new Date(data.start_time)
      }
      fetchEvents()
      break

    case 'event_deleted':
      console.log('[SocketIO] event_deleted received:', data)
      addLog(`[日程] 已删除：${data.title}`, 's')
      fetchEvents()
      break

    case 'event_updated':
      console.log('[SocketIO] event_updated received:', data)
      addLog(`[日程] 已修改：${data.old_title || data.title}`, 's')
      if (data.start_time) {
        store.currentDate = new Date(data.start_time)
      }
      fetchEvents()
      break

    case 'time_suggestion': {
      const sugStart = new Date(data.suggested_start)
      const timeStr = `${sugStart.getMonth() + 1}月${sugStart.getDate()}日 ${sugStart.getHours()}:${String(sugStart.getMinutes()).padStart(2, '0')}`
      const reason = data.reason || '未指定时间'
      addLog(`[智能推荐] "${data.title}"${reason}，已安排到：${timeStr}`, 's')
      if (data.alternatives && data.alternatives.length > 1) {
        const altTexts = data.alternatives.slice(1, 4).map(a => {
          const d = new Date(a.start)
          return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}(${a.duration_minutes}分钟)`
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

    case 'transport_options':
      store.transportOptions = data
      store.trainOptions = null
      addLog(`[出行] 已查询到 ${data.options.length} 种出行方式${data.is_intercity ? '（跨城，可选高铁）' : ''}`, 's')
      break

    case 'train_options':
      store.trainOptions = data
      store.transportOptions = null
      addLog(`[高铁] 查询到 ${data.trains.length} 趟可选车次`, 's')
      break

    case 'await_user_choice':
      store.voiceState = 'awaiting'
      addLog(`[Agent] ${data.message}`)
      break

    case 'tts_start':
      pcmPlayer.stop()
      break

    case 'tts_chunk':
      if (data.audio) {
        const binaryString = window.atob(data.audio)
        const len = binaryString.length
        const bytes = new Uint8Array(len)
        for (let i = 0; i < len; i++) {
          bytes[i] = binaryString.charCodeAt(i)
        }
        pcmPlayer.playChunk(bytes.buffer)
      }
      break

    case 'tts_end':
      // Done playing
      break

    case 'tts_text':
      addLog(`[Agent] ${data.text}`)
      store.voiceState = 'done'
      break

    case 'session_end':
      addLog(`[System] ${data.message}`)
      fetchEvents()
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
  store.micError = null
  pcmPlayer.stop() // Stop any current TTS playing when user starts speaking
  socket.emit('start_recording')
  startBrowserRecording()
}

export function stopBackendRecording() {
  stopBrowserRecording()
  socket.emit('stop_recording')
}

export default socket
