<template>
  <div class="vc">
    <div class="mic-wrap">
      <div v-if="store.voiceState === 'listening'" class="mic-ripple"></div>
      <button :class="['mic-btn', store.voiceState]" @click="toggleMic">
        <span class="mic-icon" :class="{ spin: store.voiceState === 'processing' }">
          {{ micIcon }}
        </span>
      </button>
    </div>
    
    <div class="v-status">{{ statusText }}</div>
    
    <div v-if="store.voiceState === 'listening'" class="wave-bars">
      <div class="wb on" v-for="i in 7" :key="i"></div>
    </div>
    
    <div v-if="store.currentQuery && store.voiceState !== 'idle'" class="query-box">
      "{{ store.currentQuery }}"
    </div>
    
    <div v-if="store.alog.length > 0 && store.voiceState !== 'idle'" class="alog" ref="alogContainer">
      <div v-for="log in store.alog" :key="log.id">
        <span class="al-tag" :class="log.tagClass">[{{ log.tagClass === 's' ? 'Tool' : log.tagClass === 'd' ? 'Done' : 'Info' }}]</span> 
        {{ log.text }}
      </div>
    </div>
    
    <div class="qps" v-if="store.voiceState === 'idle'">
      <button class="qp" @click="runPrompt('今天下午有什么安排？')">今天下午有什么安排？</button>
      <button class="qp" @click="runPrompt('帮我安排明天上午10点和李总的会议。')">帮我安排明天上午10点...</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { store } from '../services/store'
import { sendVoiceInput, startBackendRecording } from '../services/socket'

const alogContainer = ref(null)

watch(() => store.alog.length, async () => {
  await nextTick()
  if (alogContainer.value) {
    alogContainer.value.scrollTop = alogContainer.value.scrollHeight
  }
})

const toggleMic = () => {
  if (store.voiceState === 'idle') {
    store.voiceState = 'listening'
    store.currentQuery = ''
    startBackendRecording()
  } else if (store.voiceState === 'listening') {
    // 录音由后端控制结束，前端这里暂时只能重置状态或不处理
    // 实际讯飞录音会在静音后自动停止
  } else if (store.voiceState === 'done') {
    store.voiceState = 'idle'
  }
}

const runPrompt = (text) => {
  store.currentQuery = text
  store.voiceState = 'processing'
  sendVoiceInput(text)
}

const micIcon = computed(() => {
  if (store.voiceState === 'processing') return '⚙️'
  if (store.voiceState === 'done') return '✓'
  return '🎙️'
})

const statusText = computed(() => {
  if (store.voiceState === 'idle') return '点击麦克风开始'
  if (store.voiceState === 'listening') return '正在聆听...'
  if (store.voiceState === 'processing') return 'Agent 分析中...'
  if (store.voiceState === 'done') return '执行完成'
  return ''
})
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
.mic-btn.done { border-color: var(--teal); background: var(--teal-dim); }
.mic-icon.spin { animation: spin 1s linear infinite; display: inline-block; }

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
  border-radius: 8px; font-size: 13px; color: var(--text);
  border: 1px solid var(--border); animation: fadeUp .2s ease;
  font-style: italic; color: var(--gold);
}

.alog {
  width: 100%; background: rgba(0,0,0,.5); border: 1px solid var(--border);
  border-radius: 8px; max-height: 165px; overflow-y: auto;
  font-family: var(--fm); font-size: 10px; line-height: 1.75; padding: 8px 12px;
  color: var(--text2); text-align: left;
}
.al-tag { color: var(--teal); margin-right: 4px; }
.al-tag.s { color: var(--blue); }
.al-tag.d { color: var(--gold); }

.qps { display: flex; flex-direction: column; gap: 8px; width: 100%; }
.qp {
  border: 1px solid var(--border); border-radius: 7px; background: none;
  color: var(--text2); padding: 8px; font-size: 11px; cursor: pointer; transition: all .18s;
  text-align: left;
}
.qp:hover { border-color: var(--gold); color: var(--text); background: var(--gold-dim); }
</style>
