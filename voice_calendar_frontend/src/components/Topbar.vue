<template>
  <div v-if="store.isMobile" class="mobile-header">
    <div class="mobile-nav">
      <button class="mobile-nav-btn" @click="shiftDate(-1)">‹</button>
      <button class="mobile-today-btn" :class="{ highlight: !isToday }" @click="goToday">今日</button>
      <button class="mobile-nav-btn" @click="shiftDate(1)">›</button>
    </div>
    <div class="mobile-header-title" @click="goToday">
      <span :class="{ 'mobile-header-date-today': isToday }">{{ dateRangeText }}</span>
    </div>
    <div class="ag-badge-mobile">
      <span class="ag-dot"></span>
    </div>
  </div>

  <div v-else class="topbar">
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

const isToday = computed(() => {
  const d = store.currentDate
  const today = new Date()
  return d.getDate() === today.getDate() &&
         d.getMonth() === today.getMonth() &&
         d.getFullYear() === today.getFullYear()
})

const dateRangeText = computed(() => {
  const d = store.currentDate
  const year = d.getFullYear()
  const month = d.getMonth() + 1
  const date = d.getDate()

  if (store.isMobile) {
    const days = ['周日','周一','周二','周三','周四','周五','周六']
    return `${month}月${date}日 ${days[d.getDay()]}`
  }

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
/* Desktop Topbar */
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

/* Mobile Header */
.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 8px;
  padding-top: env(safe-area-inset-top);
  background: rgba(7,9,15,.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.mobile-nav {
  display: flex;
  align-items: center;
  gap: 2px;
}

.mobile-nav-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--text);
  background: transparent;
  border: 1px solid var(--border);
  font-size: 18px;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.12s ease;
}
.mobile-nav-btn:active {
  transform: scale(0.88);
  background: var(--bg-hover);
}

.mobile-today-btn {
  padding: 4px 12px;
  height: 30px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 500;
  color: var(--text2);
  background: transparent;
  border: 1px solid var(--border);
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.15s ease;
}
.mobile-today-btn.highlight {
  color: var(--gold);
  border-color: var(--gold-border);
  background: var(--gold-dim);
}
.mobile-today-btn:active {
  transform: scale(0.93);
}

.mobile-header-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--fu);
  letter-spacing: 0.02em;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.mobile-header-date-today {
  color: var(--gold);
}

.ag-badge-mobile {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
