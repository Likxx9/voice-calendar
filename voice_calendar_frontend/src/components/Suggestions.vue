<template>
  <div class="suggestions">
    <div class="sec-title">智能建议</div>
    <div class="sug-list">

      <!-- Transport mode selection (multi-mode route results) -->
      <div v-if="store.transportOptions" class="sug sug-choice">
        <div class="sug-head">
          <span class="sug-icon">🗺️</span>
          <span class="sug-title">请选择出行方式</span>
        </div>
        <div class="sug-desc">
          {{ store.transportOptions.origin }} → {{ store.transportOptions.destination }}
          <span v-if="store.transportOptions.is_intercity" class="intercity-tag">跨城</span>
        </div>
        <div class="choice-grid">
          <div
            v-for="opt in store.transportOptions.options"
            :key="opt.mode"
            class="choice-card"
            @click="handleSugClick(`我选择${modeLabel(opt.mode)}去${store.transportOptions.destination}` + (store.transportOptions.date ? `，时间是${store.transportOptions.date} ${store.transportOptions.target_time || ''}` : ''))"
          >
            <span class="choice-icon">{{ modeIcon(opt.mode) }}</span>
            <span class="choice-name">{{ modeLabel(opt.mode) }}</span>
            <span class="choice-detail">{{ opt.estimated_duration }}</span>
            <span class="choice-dist">{{ opt.distance }}</span>
          </div>
          <div
            v-if="store.transportOptions.is_intercity"
            class="choice-card choice-highlight"
            @click="handleSugClick(`我要坐高铁从${store.transportOptions.origin}去${store.transportOptions.destination}` + (store.transportOptions.date ? `，时间是${store.transportOptions.date} ${store.transportOptions.target_time || ''}` : ''))"
          >
            <span class="choice-icon">🚄</span>
            <span class="choice-name">高铁</span>
            <span class="choice-detail">推荐</span>
            <span class="choice-dist">查询车次</span>
          </div>
        </div>
      </div>

      <!-- Train schedule selection -->
      <div v-if="store.trainOptions" class="sug sug-choice">
        <div class="sug-head">
          <span class="sug-icon">🚄</span>
          <span class="sug-title">请选择车次</span>
        </div>
        <div class="sug-desc">
          {{ store.trainOptions.origin }} → {{ store.trainOptions.destination }}（{{ store.trainOptions.date }}）
        </div>
        <div class="train-list">
          <div
            v-for="(train, i) in store.trainOptions.trains.slice(0, 6)"
            :key="i"
            class="train-card"
            @click="handleSugClick(`我选${train.train_no}次列车，帮我安排到日程里`)"
          >
            <div class="train-no">{{ train.train_no }}</div>
            <div class="train-time">
              <span class="t-depart">{{ extractTime(train.depart_time) }}</span>
              <span class="t-arrow">→</span>
              <span class="t-arrive">{{ extractTime(train.arrive_time) }}</span>
            </div>
            <div class="train-dur">{{ train.duration }}</div>
            <div v-if="train.second_class_seats && train.second_class_seats !== '--'" class="train-seats">
              二等座: {{ train.second_class_seats }}
            </div>
          </div>
        </div>
      </div>

      <!-- Conflict alert -->
      <div v-if="store.hasConflict && store.conflictInfo" class="sug sug-warn">
        <div class="sug-head">
          <span class="sug-icon">⚠️</span>
          <span class="sug-title">会议冲突预警</span>
        </div>
        <div class="sug-desc">
          "{{ store.conflictInfo.new_event }}"与"{{
            store.conflictInfo.conflicting_events.map(e => e.title).join('、')
          }}"时间冲突。
        </div>
        <div v-if="store.conflictInfo.suggestion" class="sug-action">
          {{ store.conflictInfo.suggestion }}
        </div>
      </div>

      <!-- Time suggestion -->
      <div v-if="store.timeSuggestion" class="sug sug-info">
        <div class="sug-head">
          <span class="sug-icon">🕐</span>
          <span class="sug-title">智能时间推荐</span>
        </div>
        <div class="sug-desc">
          "{{ store.timeSuggestion.title }}"已安排到
          {{ formatTime(store.timeSuggestion.suggested_start) }}。
          <span v-if="store.timeSuggestion.reason">（{{ store.timeSuggestion.reason }}）</span>
        </div>
        <div v-if="altSlots.length > 0" class="sug-alts">
          <div class="alt-label">备选时段：</div>
          <div v-for="(alt, i) in altSlots" :key="i" class="alt-item"
               @click="handleAltClick(alt)">
            {{ formatTime(alt.start) }}（{{ alt.duration_minutes }}分钟）
          </div>
        </div>
      </div>

      <!-- Static suggestions -->
      <template v-if="showStaticSuggestions">
        <div class="sug" @click="handleSugClick('查看我今天下午有什么空闲时间')">
          <div class="sug-head">
            <span class="sug-icon">💡</span>
            <span class="sug-title">空闲时段查询</span>
          </div>
          <div class="sug-desc">点击查看今天下午可用的空闲时段。</div>
        </div>
        <div class="sug" @click="handleSugClick('帮我安排一个团队周会')">
          <div class="sug-head">
            <span class="sug-icon">📅</span>
            <span class="sug-title">快速创建日程</span>
          </div>
          <div class="sug-desc">语音快速创建日程，系统自动选择空闲时段。</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store, addLog } from '../services/store'
import { sendVoiceInput } from '../services/socket'

const showStaticSuggestions = computed(() =>
  !store.hasConflict &&
  !store.timeSuggestion &&
  !store.trainOptions &&
  !store.transportOptions
)

const altSlots = computed(() => {
  if (!store.timeSuggestion || !store.timeSuggestion.alternatives) return []
  return store.timeSuggestion.alternatives.slice(1, 4)
})

const formatTime = (isoStr) => {
  const d = new Date(isoStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const extractTime = (timeStr) => {
  if (!timeStr) return '--'
  const parts = timeStr.split(' ')
  return parts.length > 1 ? parts[1] : timeStr
}

const modeIcon = (mode) => {
  const icons = { driving: '🚗', transit: '🚌', walking: '🚶', riding: '🚲' }
  return icons[mode] || '🚗'
}

const modeLabel = (mode) => {
  const labels = { driving: '驾车', transit: '公交', walking: '步行', riding: '骑行' }
  return labels[mode] || mode
}

const handleSugClick = (text) => {
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

const handleAltClick = (alt) => {
  const title = store.timeSuggestion?.title || '日程'
  const text = `帮我把${title}改到${formatTime(alt.start)}`
  handleSugClick(text)
}
</script>

<style scoped>
.suggestions { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.sec-title { font-size: 11px; color: var(--text3); font-weight: 600; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em; }
.sug-list { display: flex; flex-direction: column; gap: 10px; }
.sug { background: var(--bg); border: 1px solid var(--border); border-radius: 9px; padding: 11px 13px; transition: all .22s; cursor: pointer; }
.sug:hover { border-color: var(--gold-border); background: var(--bg-hover); }
.sug-head { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.sug-icon { font-size: 12px; }
.sug-title { font-size: 11px; color: var(--text); font-weight: 500; }
.sug-desc { font-size: 10px; color: var(--text2); line-height: 1.5; }
.sug-warn { border-color: #6b3a3a; background: rgba(200, 60, 60, 0.08); }
.sug-warn:hover { border-color: #c83c3c; }
.sug-info { border-color: #3a5a6b; background: rgba(60, 140, 200, 0.08); }
.sug-info:hover { border-color: #3c8cc8; }
.sug-choice { border-color: #4a6b3a; background: rgba(80, 180, 80, 0.06); cursor: default; }
.sug-choice:hover { border-color: #5a8b4a; background: rgba(80, 180, 80, 0.1); }
.sug-action { font-size: 10px; color: var(--gold); margin-top: 6px; font-style: italic; }
.sug-alts { margin-top: 8px; }
.alt-label { font-size: 9px; color: var(--text3); margin-bottom: 4px; }
.alt-item { font-size: 10px; color: var(--text2); padding: 4px 8px; margin-bottom: 3px; border-radius: 5px; background: var(--bg2); cursor: pointer; transition: all .18s; display: inline-block; margin-right: 6px; }
.alt-item:hover { color: var(--gold); background: var(--bg-hover); }

.intercity-tag { display: inline-block; font-size: 9px; background: rgba(255, 165, 0, 0.2); color: #ffa500; padding: 1px 5px; border-radius: 3px; margin-left: 6px; }

/* Transport mode selection grid */
.choice-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(90px, 1fr)); gap: 8px; margin-top: 10px; }
.choice-card {
  display: flex; flex-direction: column; align-items: center; gap: 3px;
  padding: 10px 6px; border-radius: 8px;
  background: var(--bg2); border: 1px solid var(--border);
  cursor: pointer; transition: all .2s; text-align: center;
}
.choice-card:hover { border-color: var(--gold); background: var(--bg-hover); transform: translateY(-1px); }
.choice-highlight { border-color: #4a8b4a; background: rgba(80, 200, 80, 0.08); }
.choice-highlight:hover { border-color: #5ab85a; background: rgba(80, 200, 80, 0.15); }
.choice-icon { font-size: 18px; }
.choice-name { font-size: 11px; color: var(--text); font-weight: 500; }
.choice-detail { font-size: 10px; color: var(--gold); }
.choice-dist { font-size: 9px; color: var(--text3); }

/* Train selection list */
.train-list { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
.train-card {
  display: grid; grid-template-columns: auto 1fr auto auto; align-items: center; gap: 8px;
  padding: 8px 10px; border-radius: 7px;
  background: var(--bg2); border: 1px solid var(--border);
  cursor: pointer; transition: all .2s;
}
.train-card:hover { border-color: var(--gold); background: var(--bg-hover); }
.train-no { font-size: 12px; color: var(--gold); font-weight: 600; min-width: 48px; }
.train-time { font-size: 11px; color: var(--text); display: flex; align-items: center; gap: 4px; }
.t-depart { font-weight: 500; }
.t-arrow { color: var(--text3); font-size: 10px; }
.t-arrive { color: var(--text2); }
.train-dur { font-size: 10px; color: var(--text2); }
.train-seats { font-size: 9px; color: var(--teal); }
</style>
