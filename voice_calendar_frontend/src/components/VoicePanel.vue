<template>
  <div class="vc">
    <div class="mic-wrap">
      <div v-if="store.voiceState === 'listening'" class="mic-ripple"></div>
      <button
        :class="['mic-btn', store.voiceState]"
        @mousedown="startRecord"
        @mouseup="stopRecord"
        @mouseleave="stopRecord"
        @touchstart.prevent="startRecord"
        @touchend.prevent="stopRecord"
      >
        <span class="mic-icon" :class="{ spin: store.voiceState === 'processing', bounce: store.voiceState === 'awaiting' }">
          {{ micIcon }}
        </span>
      </button>
    </div>

    <div class="v-status">{{ statusText }}</div>

    <div v-if="store.voiceState === 'listening'" class="wave-bars">
      <div class="wb on" v-for="i in 7" :key="i"></div>
    </div>

    <div v-if="store.currentQuery && store.voiceState === 'listening'" class="query-box">
      "{{ store.currentQuery }}"
    </div>

    <!-- Chat History -->
    <div class="chat-box" ref="chatContainer" v-if="store.alog.length > 0">
      <div class="chat-header">
        <span class="chat-title">对话记录</span>
        <button class="chat-clear-btn" @click="handleClear" title="清空记录">🗑</button>
      </div>
      <div class="chat-messages" ref="chatMessages">
        <template v-for="(log, i) in store.alog" :key="log.id">
          <!-- Session divider -->
          <div v-if="isSessionStart(log, i)" class="chat-divider">
            <span>{{ log.time }}</span>
          </div>

          <!-- User message bubble -->
          <div v-if="log.tagClass === 'u'" class="chat-bubble user">
            <div class="bubble-content user-bubble">{{ log.text }}</div>
            <div class="bubble-time">{{ log.time }}</div>
          </div>

          <!-- Agent/System message bubble -->
          <div v-else class="chat-bubble agent">
            <div :class="['bubble-content', bubbleClass(log)]">
              <span class="bubble-icon">{{ bubbleIcon(log) }}</span>
              {{ cleanText(log.text) }}
            </div>
            <div class="bubble-time">{{ log.time }}</div>
          </div>
        </template>
      </div>
    </div>

    <div class="sug-container">
      <Suggestions />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { store, clearChatHistory } from '../services/store'
import { sendVoiceInput, startBackendRecording, stopBackendRecording } from '../services/socket'
import Suggestions from './Suggestions.vue'

const chatContainer = ref(null)
const chatMessages = ref(null)

watch(() => store.alog.length, async () => {
  await nextTick()
  if (chatMessages.value) {
    chatMessages.value.scrollTop = chatMessages.value.scrollHeight
  }
})

const startRecord = () => {
  if (store.voiceState === 'idle' || store.voiceState === 'done' || store.voiceState === 'awaiting') {
    store.voiceState = 'listening'
    store.currentQuery = ''
    startBackendRecording()
  }
}

const stopRecord = () => {
  if (store.voiceState === 'listening') {
    store.voiceState = 'processing'
    stopBackendRecording()
  }
}

const micIcon = computed(() => {
  if (store.voiceState === 'processing') return '⚙️'
  if (store.voiceState === 'awaiting') return '👇'
  if (store.voiceState === 'done') return '✓'
  return '🎙️'
})

const statusText = computed(() => {
  if (store.voiceState === 'idle') return '按住麦克风说话'
  if (store.voiceState === 'listening') return '正在聆听...松开结束'
  if (store.voiceState === 'processing') return 'Agent 分析中...'
  if (store.voiceState === 'awaiting') return '请在下方选择'
  if (store.voiceState === 'done') return '执行完成'
  return ''
})

const isSessionStart = (log, index) => {
  if (index === 0) return true
  if (log.tagClass === 'u') {
    const prev = store.alog[index - 1]
    return prev.tagClass !== 'u'
  }
  return false
}

const bubbleClass = (log) => {
  if (log.tagClass === 'w') return 'warn-bubble'
  if (log.tagClass === 's') return 'sys-bubble'
  return 'agent-bubble'
}

const bubbleIcon = (log) => {
  if (log.tagClass === 'w') return '⚠️'
  if (log.tagClass === 's') return '🔧'
  if (log.text.includes('[Agent]')) return '🤖'
  return '💬'
}

const cleanText = (text) => {
  return text
    .replace(/^\[Agent\]\s*/, '')
    .replace(/^\[System\]\s*/, '')
    .replace(/^\[Tool\]\s*/, '')
    .replace(/^\[智能推荐\]\s*/, '')
    .replace(/^\[日程\]\s*/, '')
    .replace(/^\[出行\]\s*/, '')
    .replace(/^\[高铁\]\s*/, '')
    .replace(/^\[备选时段\]\s*/, '')
    .replace(/^\[⚠ 冲突\]\s*/, '')
}

const handleClear = () => {
  clearChatHistory()
}
</script>

<style scoped>
.vc {
  background: linear-gradient(135deg, rgba(200,164,90,.06), rgba(200,164,90,.02));
  border: 1px solid var(--gold-border);
  border-radius: 12px;
  padding: 18px 16px;
  display: flex; flex-direction: column; align-items: center; gap: 16px;
  flex-shrink: 0;
}

.mic-wrap { position: relative; width: 62px; height: 62px; }
.mic-btn {
  width: 100%; height: 100%; border-radius: 50%;
  border: 1.5px solid var(--gold-border);
  background: var(--gold-dim); color: var(--text);
  font-size: 24px; cursor: pointer; position: relative; z-index: 2;
  transition: all 0.3s; display: flex; align-items: center; justify-content: center;
}
.mic-btn:hover { background: rgba(200,164,90,.15); }
.mic-btn.listening {
  border-color: var(--gold); background: rgba(200,164,90,.18);
  animation: glowGold 1.1s ease-in-out infinite;
}
.mic-btn.processing { border-color: var(--blue); background: var(--blue-dim); }
.mic-btn.awaiting { border-color: var(--gold); background: rgba(200,164,90,.15); animation: glowGold 2s ease-in-out infinite; }
.mic-btn.done { border-color: var(--teal); background: var(--teal-dim); }
.mic-icon.spin { animation: spin 1s linear infinite; display: inline-block; }
.mic-icon.bounce { animation: bounce 1.5s ease-in-out infinite; display: inline-block; }
@keyframes bounce { 0%,100% { transform: translateY(0); } 50% { transform: translateY(4px); } }

.mic-ripple {
  position: absolute; inset: -10px; border-radius: 50%;
  border: 1.5px solid var(--gold); animation: ripple 1.9s ease-out infinite; z-index: 1;
}
.v-status { font-size: 13px; color: var(--gold); text-align: center; }

.wave-bars { display: flex; gap: 4px; align-items: center; height: 24px; }
.wb { width: 3px; border-radius: 2px; background: var(--gold); height: 4px; }
.wb.on:nth-child(1) { animation: waveBar .7s ease-in-out 0.00s infinite; }
.wb.on:nth-child(2) { animation: waveBar .7s ease-in-out 0.09s infinite; }
.wb.on:nth-child(3) { animation: waveBar .7s ease-in-out 0.18s infinite; }
.wb.on:nth-child(4) { animation: waveBar .7s ease-in-out 0.27s infinite; }
.wb.on:nth-child(5) { animation: waveBar .7s ease-in-out 0.18s infinite; }
.wb.on:nth-child(6) { animation: waveBar .7s ease-in-out 0.09s infinite; }
.wb.on:nth-child(7) { animation: waveBar .7s ease-in-out 0.00s infinite; }

.query-box {
  width: 100%; background: rgba(0,0,0,.3); padding: 12px;
  border-radius: 8px; font-size: 13px;
  border: 1px solid var(--border); animation: fadeUp .2s ease;
  font-style: italic; color: var(--gold);
}

/* Chat Interface */
.chat-box {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: rgba(0,0,0,.35);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border-bottom: 1px solid var(--border);
  background: rgba(0,0,0,.2);
}
.chat-title { font-size: 11px; color: var(--text3); font-weight: 600; letter-spacing: 0.05em; }
.chat-clear-btn {
  background: none; border: none; cursor: pointer; font-size: 12px; opacity: 0.5;
  transition: opacity 0.2s;
  padding: 2px 4px;
}
.chat-clear-btn:hover { opacity: 1; }

.chat-messages {
  max-height: 320px;
  overflow-y: auto;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  scroll-behavior: smooth;
}

.chat-divider {
  text-align: center;
  padding: 6px 0 2px;
}
.chat-divider span {
  font-size: 9px;
  color: var(--text3);
  background: rgba(0,0,0,.3);
  padding: 2px 10px;
  border-radius: 8px;
}

.chat-bubble {
  display: flex;
  flex-direction: column;
  max-width: 92%;
  animation: fadeUp 0.15s ease;
}
.chat-bubble.user { align-self: flex-end; align-items: flex-end; }
.chat-bubble.agent { align-self: flex-start; align-items: flex-start; }

.bubble-content {
  padding: 7px 11px;
  border-radius: 10px;
  font-size: 12px;
  line-height: 1.6;
  word-break: break-word;
}

.user-bubble {
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
  color: var(--gold);
  border-bottom-right-radius: 3px;
  font-weight: 500;
}

.agent-bubble {
  background: rgba(255,255,255,.04);
  border: 1px solid var(--border);
  color: var(--text2);
  border-bottom-left-radius: 3px;
}

.sys-bubble {
  background: rgba(60,140,200,.08);
  border: 1px solid rgba(60,140,200,.2);
  color: var(--blue);
  border-bottom-left-radius: 3px;
}

.warn-bubble {
  background: rgba(200,60,60,.08);
  border: 1px solid rgba(200,60,60,.2);
  color: #ff8888;
  border-bottom-left-radius: 3px;
}

.bubble-icon { font-size: 10px; margin-right: 4px; }

.bubble-time {
  font-size: 9px;
  color: var(--text3);
  margin-top: 2px;
  padding: 0 4px;
}

.sug-container { width: 100%; margin-top: 8px; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
</style>
