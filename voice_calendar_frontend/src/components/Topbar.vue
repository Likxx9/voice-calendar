<template>
  <div class="topbar">
    <div class="tb-left">
      <button class="icon-btn" @click="shiftDate(-1)">‹</button>
      <button class="icon-btn" @click="shiftDate(1)">›</button>
      <span class="tb-date-range">{{ dateRangeText }}</span>
      <button class="btn-outline" @click="goToday">今日</button>
    </div>
    <div class="tb-right">
      <div class="ag-badge">
        <span class="ag-dot"></span>
        Agent 在线
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { store, shiftDate, goToday } from '../services/store'

const dateRangeText = computed(() => {
  const d = store.currentDate
  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const date = d.getDate()
  
  if (store.currentView === 'day') {
    return `${year}年${month}月${date}日`
  } else if (store.currentView === 'month') {
    return `${year}年${month}月`
  } else {
    const startOfYear = new Date(year, 0, 1)
    const days = Math.floor((d - startOfYear) / (24 * 60 * 60 * 1000))
    const weekNumber = Math.ceil((d.getDay() + 1 + days) / 7)
    return `${year}年${month}月 · 第${weekNumber}周`
  }
})
</script>

<style scoped>
.topbar {
  height: 60px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between;
  background: rgba(7,9,15,.85); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border);
  position: sticky; top: 0; z-index: 10;
}
.tb-left, .tb-right { display: flex; align-items: center; gap: 12px; }
.tb-date-range { font-size: 16px; font-weight: 500; margin: 0 12px; }
.icon-btn { background: none; border: 1px solid var(--border); color: var(--text); width: 32px; height: 32px; border-radius: var(--r); cursor: pointer; }
.icon-btn:hover { background: var(--bg-hover); }
.btn-outline { background: none; border: 1px solid var(--border); color: var(--text); padding: 6px 16px; border-radius: var(--r); cursor: pointer; font-family: var(--fu); }
.btn-outline:hover { background: var(--bg-hover); }
.ag-badge { background: var(--teal-dim); border: 1px solid rgba(45,212,191,.2); border-radius: 20px; color: var(--teal); padding: 4px 12px; font-size: 11px; display: flex; align-items: center; gap: 6px; }
.ag-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--teal); animation: pulse 2.2s infinite; }

@media (max-width: 767px) {
  .tb-date-range { font-size: 14px; margin: 0 8px; }
}
</style>
