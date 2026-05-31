<template>
  <div class="today-brief">
    <div class="sec-title">{{ briefTitle }}</div>
    <div class="brief-list">
      <div v-for="ev in todayEvents" :key="ev.id" class="brief-item">
        <div class="btime">{{ fmtTime(ev.s) }}</div>
        <div class="bcont">
          <div class="bt">{{ ev.title }}</div>
          <div class="bloc">{{ ev.loc }}</div>
        </div>
      </div>
      <div v-if="todayEvents.length === 0" class="empty-state">
        今日暂无日程安排
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store } from '../services/store'

const briefTitle = computed(() => {
  const d = store.currentDate
  const isToday = d.toDateString() === new Date().toDateString()
  if (isToday) return '今日日程'
  return `${d.getMonth() + 1}月${d.getDate()}日 日程`
})

const todayEvents = computed(() => {
  const targetDateStr = store.currentDate.toDateString()
  return store.events.filter(e => e.dateStr === targetDateStr).sort((a, b) => a.s - b.s)
})

const fmtTime = (h) => {
  const hh = Math.floor(h)
  const mm = h % 1 === 0 ? '00' : '30'
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`
}
</script>

<style scoped>
.today-brief { background: var(--bg2); border: 1px solid var(--border); border-radius: 12px; padding: 16px; }
.sec-title { font-size: 11px; color: var(--text3); font-weight: 600; text-transform: uppercase; margin-bottom: 12px; letter-spacing: 0.05em; }
.brief-item { display: flex; gap: 10px; padding: 9px 0; border-bottom: 1px solid var(--border); cursor: pointer; transition: all .18s; }
.brief-item:last-child { border-bottom: none; }
.brief-item:hover .bt { color: var(--gold); }
.btime { font-family: var(--fm); font-size: 10px; min-width: 38px; letter-spacing: .03em; color: var(--text2); padding-top: 2px; }
.bcont { display: flex; flex-direction: column; gap: 4px; }
.bt { font-size: 12px; font-weight: 500; color: var(--text); transition: color .2s; }
.bloc { font-size: 11px; color: var(--text2); }
.empty-state { font-size: 12px; color: var(--text3); text-align: center; padding: 12px 0; }
</style>
