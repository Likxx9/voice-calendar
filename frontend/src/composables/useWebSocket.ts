/* ============================================================
 * M2 组合式函数 — WebSocket 全双工通信管理器
 * 自动重连 | 心跳维持 | AudioChunk 发送 | Barge-in 打断帧
 * ============================================================ */

import { ref, onUnmounted } from 'vue'
import type { WSFrame, WSFrameType, ConnectionState } from '@/types/contracts'

export interface WebSocketOptions {
  url?: string
  heartbeatInterval?: number      // 心跳间隔 ms，默认 15000
  reconnectInterval?: number      // 重连间隔 ms，默认 3000
  maxReconnectAttempts?: number   // 最大重连次数，默认 10
  onMessage?: (frame: WSFrame) => void
  onStateChange?: (state: ConnectionState) => void
}

export function useWebSocket(options: WebSocketOptions = {}) {
  const {
    url = `ws://${window.location.host}/ws/voice`,
    heartbeatInterval = 15000,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    onMessage,
    onStateChange,
  } = options

  const state = ref<ConnectionState>('disconnected')
  const lastError = ref<string | null>(null)

  let ws: WebSocket | null = null
  let heartbeatTimer: ReturnType<typeof setInterval> | null = null
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let reconnectAttempts = 0

  function setState(newState: ConnectionState) {
    state.value = newState
    onStateChange?.(newState)
  }

  function connect(sessionId?: string) {
    if (ws?.readyState === WebSocket.OPEN) return

    const wsUrl = sessionId ? `${url}?session_id=${sessionId}` : url
    setState('connecting')

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        setState('connected')
        reconnectAttempts = 0
        lastError.value = null
        startHeartbeat()
      }

      ws.onmessage = (event) => {
        try {
          const frame = JSON.parse(event.data) as WSFrame
          onMessage?.(frame)
        } catch {
          // 二进制数据（TTS 音频流）
          onMessage?.({
            type: 'TTS_AUDIO_CHUNK',
            session_id: '',
            timestamp: new Date().toISOString(),
            payload: event.data,
          })
        }
      }

      ws.onclose = (event) => {
        stopHeartbeat()
        if (event.code !== 1000) {
          // 非正常关闭，尝试重连
          attemptReconnect()
        } else {
          setState('disconnected')
        }
      }

      ws.onerror = () => {
        lastError.value = '连接错误'
        stopHeartbeat()
      }
    } catch (err) {
      lastError.value = err instanceof Error ? err.message : '连接失败'
      setState('disconnected')
    }
  }

  function disconnect() {
    reconnectAttempts = maxReconnectAttempts // 阻止自动重连
    stopHeartbeat()
    clearReconnectTimer()
    ws?.close(1000, 'client_disconnect')
    ws = null
    setState('disconnected')
  }

  function attemptReconnect() {
    if (reconnectAttempts >= maxReconnectAttempts) {
      setState('disconnected')
      lastError.value = `已尝试 ${maxReconnectAttempts} 次重连均失败`
      return
    }

    setState('reconnecting')
    reconnectAttempts++

    const delay = reconnectInterval * Math.min(reconnectAttempts, 5)
    reconnectTimer = setTimeout(() => {
      connect()
    }, delay)
  }

  function clearReconnectTimer() {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
  }

  // ── 心跳 ────────────────────────────────────────
  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      sendFrame('HEARTBEAT', {})
    }, heartbeatInterval)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) {
      clearInterval(heartbeatTimer)
      heartbeatTimer = null
    }
  }

  // ── 发送 ────────────────────────────────────────
  function sendFrame(type: WSFrameType, payload: unknown, sessionId = '') {
    if (ws?.readyState !== WebSocket.OPEN) return false

    const frame: WSFrame = {
      type,
      session_id: sessionId,
      timestamp: new Date().toISOString(),
      payload,
    }

    ws.send(JSON.stringify(frame))
    return true
  }

  // 发送音频分片（二进制）
  function sendAudioChunk(chunk: ArrayBuffer, sessionId: string, seqNum: number, isFinal: boolean) {
    if (ws?.readyState !== WebSocket.OPEN) return false

    // 先发送元数据帧
    sendFrame('AUDIO_CHUNK', {
      session_id: sessionId,
      sequence_number: seqNum,
      is_final: isFinal,
      size: chunk.byteLength,
    }, sessionId)

    // 再发送二进制音频数据
    if (chunk.byteLength > 0) {
      ws.send(chunk)
    }

    return true
  }

  // 发送 Barge-in 打断帧
  function sendInterrupt(sessionId: string) {
    return sendFrame('WS_INTENT_INTERRUPT', {}, sessionId)
  }

  onUnmounted(() => {
    disconnect()
  })

  return {
    state,
    lastError,
    connect,
    disconnect,
    sendFrame,
    sendAudioChunk,
    sendInterrupt,
  }
}
