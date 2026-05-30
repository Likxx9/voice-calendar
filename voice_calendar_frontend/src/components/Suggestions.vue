<template>
  <div class="suggestions">
    <div class="sec-title">智能建议</div>
    <div class="sug-list">
      <!-- Dynamic conflict alert -->
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

      <!-- Dynamic time suggestion -->
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

      <!-- Static suggestions (show when no dynamic ones) -->
      <template v-if="!store.hasConflict && !store.timeSuggestion">
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
import { store } from '../services/store'
import { sendVoiceInput } from '../services/socket'

const altSlots = computed(() => {
  if (!store.timeSuggestion || !store.timeSuggestion.alternatives) return []
  return store.timeSuggestion.alternatives.slice(1, 4)
})

const formatTime = (isoStr) => {
  const d = new Date(isoStr)
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}

const handleSugClick = (text) => {
  store.currentQuery = text
  store.voiceState = 'processing'
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
.sug-action { font-size: 10px; color: var(--gold); margin-top: 6px; font-style: italic; }
.sug-alts { margin-top: 8px; }
.alt-label { font-size: 9px; color: var(--text3); margin-bottom: 4px; }
.alt-item { font-size: 10px; color: var(--text2); padding: 4px 8px; margin-bottom: 3px; border-radius: 5px; background: var(--bg2); cursor: pointer; transition: all .18s; display: inline-block; margin-right: 6px; }
.alt-item:hover { color: var(--gold); background: var(--bg-hover); }
</style>
