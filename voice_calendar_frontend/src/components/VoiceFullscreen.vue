<template>
  <div class="voice-fullscreen" v-if="store.showVoiceFullscreen">
    <div class="voice-close-bar">
      <div class="voice-status-text">{{ statusText }}</div>
      <button class="voice-close-btn" @click="closeVoice">✕</button>
    </div>

    <div class="voice-center">
      <div v-if="store.micError" class="mic-error-banner">
        <span v-if="store.micError === 'secure_context_required'">
          ⚠️ 移动端语音输入需要 HTTPS 安全连接。
        </span>
        <span v-else>
          ⚠️ 无法获取麦克风，请检查权限设置。
        </span>
      </div>

      <div
        class="voice-mic-main"
        :class="{
          listening: store.voiceState === 'listening',
          processing: store.voiceState === 'processing',
          awaiting: store.voiceState === 'awaiting',
          done: store.voiceState === 'done'
        }"
        @touchstart.prevent="startVoice"
        @touchend.prevent="stopVoice"
        @touchcancel.prevent="stopVoice"
        @mousedown="startVoice"
        @mouseup="stopVoice"
        @mouseleave="stopVoice"
      >
        <div v-if="store.voiceState === 'listening'" class="voice-ripple-ring"></div>
        <div v-if="store.voiceState === 'listening'" class="voice-ripple-ring"></div>
        <div v-if="store.voiceState === 'listening'" class="voice-ripple-ring"></div>

        <span v-if="store.voiceState === 'processing'">⌛</span>
        <span v-else-if="store.voiceState === 'awaiting'">👇</span>
        <span v-else-if="store.voiceState === 'done'">✓</span>
        <span v-else>🎙</span>
      </div>

      <div class="voice-query-bubble" v-if="store.currentQuery && (store.voiceState === 'listening' || store.voiceState === 'processing')">
        "{{ store.currentQuery }}"
      </div>

      <!-- Chat History -->
      <div class="voice-chat-mobile" v-if="store.alog.length" ref="logContainer">
        <div class="chat-scroll" ref="chatScroll">
          <template v-for="(log, i) in store.alog" :key="log.id">
            <div v-if="log.tagClass === 'u'" class="m-bubble m-user">
              <div class="m-bubble-body m-user-body">{{ log.text }}</div>
              <div class="m-bubble-time">{{ log.time }}</div>
            </div>
            <div v-else class="m-bubble m-agent">
              <div :class="['m-bubble-body', log.tagClass === 's' ? 'm-sys-body' : log.tagClass === 'w' ? 'm-warn-body' : 'm-agent-body']">
                {{ cleanText(log.text) }}
              </div>
              <div class="m-bubble-time">{{ log.time }}</div>
            </div>
          </template>
        </div>
      </div>

      <!-- 智能建议（交通/车次选择） -->
      <div class="mobile-suggestions" v-if="store.transportOptions || store.trainOptions || store.timeSuggestion">
        <Suggestions />
      </div>
    </div>

    <div class="quick-chips">
      <div class="chip" @click="handleChipClick('查看我今天下午有什么空闲时间')">空闲时间</div>
      <div class="chip" @click="handleChipClick('帮我查一下杭州去上海的高铁')">查高铁</div>
      <div class="chip" @click="handleChipClick('明早10点开周会')">建日程</div>
      <div class="chip" @click="handleChipClick('删除明天的周会')">删日程</div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick } from 'vue'
import { store, addLog, clearChatHistory } from '../services/store'
import { startBackendRecording, stopBackendRecording, sendVoiceInput } from '../services/socket'
import Suggestions from './Suggestions.vue'

const logContainer = ref(null)
const chatScroll = ref(null)

const statusText = computed(() => {
  if (store.voiceState === 'listening') return '正在聆听...松开结束'
  if (store.voiceState === 'processing') return 'Agent 分析中...'
  if (store.voiceState === 'awaiting') return '请在下方选择'
  if (store.voiceState === 'done') return '执行完成'
  return '按住麦克风说话'
})

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

watch(() => store.alog.length, async () => {
  await nextTick()
  if (chatScroll.value) {
    chatScroll.value.scrollTop = chatScroll.value.scrollHeight
  }
})

const closeVoice = () => {
  store.showVoiceFullscreen = false
}

const startVoice = () => {
  if (store.voiceState === 'processing') return
  store.voiceState = 'listening'
  store.currentQuery = ''
  startBackendRecording()
}

const stopVoice = () => {
  if (store.voiceState === 'listening') {
    store.voiceState = 'processing'
    stopBackendRecording()
  }
}

const handleChipClick = (text) => {
  store.currentQuery = text
  store.voiceState = 'processing'
  store.hasConflict = false
  store.conflictInfo = null
  store.timeSuggestion = null
  store.trainOptions = null
  store.transportOptions = null
  addLog(text, 'u')
  sendVoiceInput(text)
}
</script>

<style scoped>
.voice-fullscreen {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 60%, rgba(200,164,90,.06), var(--bg) 70%);
  background-color: var(--bg);
  z-index: 300;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: env(safe-area-inset-top, 0px) 0 env(safe-area-inset-bottom, 0px);
  animation: voiceSlideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  overflow-y: auto;
}

@keyframes voiceSlideUp {
  from { transform: translateY(100%); opacity: 0.5; }
  to   { transform: translateY(0);    opacity: 1; }
}

.voice-close-bar {
  width: 100%;
  padding: 16px var(--sp-md, 16px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-shrink: 0;
}

.voice-status-text {
  font-size: 14px;
  color: var(--gold);
  font-weight: 500;
}

.voice-close-btn {
  width: var(--touch-target, 44px);
  height: var(--touch-target, 44px);
  border-radius: 50%;
  background: var(--bg2);
  border: 1px solid var(--border);
  color: var(--text2);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.voice-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
  padding: 16px var(--sp-lg, 24px);
  width: 100%;
  overflow-y: auto;
}

.voice-mic-main {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--gold-dim);
  border: 2px solid var(--gold-border);
  font-size: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
  user-select: none;
  -webkit-user-select: none;
  -webkit-touch-callout: none;
  flex-shrink: 0;
}

.voice-mic-main:active { transform: scale(0.9); }
.voice-mic-main.listening { border-color: var(--gold); background: rgba(200,164,90,.18); }
.voice-mic-main.processing { background: linear-gradient(135deg, var(--blue), #1a4a99); border-color: transparent; animation: fabProcessing 0.8s ease-in-out infinite; }
.voice-mic-main.awaiting { border-color: var(--gold); background: rgba(200,164,90,.15); animation: fabGlow 2s ease-in-out infinite; }
.voice-mic-main.done { background: var(--teal-dim); border-color: var(--teal); }

@keyframes fabProcessing { 0%,100% { transform: scale(1); } 50% { transform: scale(1.05); } }
@keyframes fabGlow { 0%,100% { box-shadow: 0 4px 16px rgba(200,164,90,.4); } 50% { box-shadow: 0 4px 24px rgba(200,164,90,.6), 0 0 0 14px rgba(200,164,90,0); } }

.voice-ripple-ring {
  position: absolute;
  inset: -16px;
  border-radius: 50%;
  border: 2px solid var(--gold);
  opacity: 0;
  animation: mobileRipple 2s ease-out infinite;
}
.voice-ripple-ring:nth-child(2) { animation-delay: 0.6s; }
.voice-ripple-ring:nth-child(3) { animation-delay: 1.2s; }

@keyframes mobileRipple {
  0%   { transform: scale(0.85); opacity: 0.6; }
  100% { transform: scale(1.6);  opacity: 0; }
}

.voice-query-bubble {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--r-lg, 20px);
  padding: 12px 20px;
  font-size: 15px;
  color: var(--gold);
  font-style: italic;
  line-height: 1.5;
  max-width: 100%;
  text-align: center;
  animation: fadeUp 0.3s ease;
  flex-shrink: 0;
}

@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

.voice-log-mobile {
  width: 100%;
  background: rgba(0,0,0,.45);
  border: 1px solid var(--border);
  border-radius: var(--r, 12px);
  padding: 10px;
  max-height: 180px;
  overflow-y: auto;
  font-family: var(--fm);
  font-size: 11px;
  line-height: 1.75;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}
.log-line { display: flex; align-items: flex-start; gap: 6px; }
.log-line.u { color: var(--text); font-weight: 500; font-style: italic; }
.log-tag { color: var(--teal); flex-shrink: 0; font-size: 10px; }
.log-line.s .log-tag { color: var(--blue); }
.log-line.u .log-tag { color: var(--gold); }
.log-line.w .log-tag { color: #ff6b6b; }

/* Mobile Chat Bubbles */
.voice-chat-mobile {
  width: 100%;
  background: rgba(0,0,0,.35);
  border: 1px solid var(--border);
  border-radius: var(--r, 12px);
  overflow: hidden;
  flex-shrink: 0;
}
.chat-scroll {
  max-height: 240px;
  overflow-y: auto;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  scroll-behavior: smooth;
}
.m-bubble { display: flex; flex-direction: column; max-width: 85%; animation: fadeUp 0.15s ease; }
.m-bubble.m-user { align-self: flex-end; align-items: flex-end; }
.m-bubble.m-agent { align-self: flex-start; align-items: flex-start; }
.m-bubble-body { padding: 8px 12px; border-radius: 12px; font-size: 13px; line-height: 1.6; word-break: break-word; }
.m-user-body { background: var(--gold-dim); border: 1px solid var(--gold-border); color: var(--gold); border-bottom-right-radius: 3px; font-weight: 500; }
.m-agent-body { background: rgba(255,255,255,.04); border: 1px solid var(--border); color: var(--text2); border-bottom-left-radius: 3px; }
.m-sys-body { background: rgba(60,140,200,.08); border: 1px solid rgba(60,140,200,.2); color: var(--blue); border-bottom-left-radius: 3px; }
.m-warn-body { background: rgba(200,60,60,.08); border: 1px solid rgba(200,60,60,.2); color: #ff8888; border-bottom-left-radius: 3px; }
.m-bubble-time { font-size: 9px; color: var(--text3); margin-top: 2px; padding: 0 4px; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }

.mobile-suggestions {
  width: 100%;
  flex-shrink: 0;
}

.quick-chips {
  display: flex;
  gap: var(--sp-sm, 10px);
  overflow-x: auto;
  scrollbar-width: none;
  padding: 12px var(--sp-md, 16px) calc(24px + env(safe-area-inset-bottom, 0px));
  width: 100%;
  flex-shrink: 0;
}
.quick-chips::-webkit-scrollbar { display: none; }

.chip {
  flex-shrink: 0;
  padding: 9px 16px;
  border-radius: var(--r-pill);
  border: 1px solid var(--border);
  background: var(--bg2);
  font-size: 13px;
  color: var(--text2);
  cursor: pointer;
  white-space: nowrap;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.15s ease;
}
.chip:active {
  border-color: var(--gold);
  color: var(--gold);
  background: var(--gold-dim);
  transform: scale(0.97);
}

.mic-error-banner {
  font-size: 11px;
  color: #ff6b6b;
  text-align: center;
  background: rgba(255,107,107,0.1);
  border: 1px solid rgba(255,107,107,0.2);
  padding: 8px 14px;
  border-radius: 8px;
  max-width: 90%;
  margin-bottom: 10px;
  animation: fadeUp 0.2s ease;
}
</style>
