<template>
  <aside class="sidebar">
    <div class="sb-logo">
      <span class="sb-logo-name">VoiCal</span>
    </div>
    <div class="sb-scroll">
      <div class="nav-section">
        <div class="nav-title">视图</div>
        <div class="nav-item" :class="{ active: store.currentView === 'day' }" @click="setView('day')">日视图</div>
        <div class="nav-item" :class="{ active: store.currentView === 'week' }" @click="setView('week')">周视图</div>
        <div class="nav-item" :class="{ active: store.currentView === 'month' }" @click="setView('month')">月视图</div>
      </div>
      <div class="nav-section">
        <div class="nav-title">我的日历</div>
        <div class="nav-item" :class="{ inactive: !store.calendars.executive }" @click="toggleCalendar('executive')">
          <span class="cal-color" style="background:var(--gold)"></span>高管日程
        </div>
        <div class="nav-item" :class="{ inactive: !store.calendars.project }" @click="toggleCalendar('project')">
          <span class="cal-color" style="background:var(--blue)"></span>项目会议
        </div>
      </div>
      
      <div class="divider"></div>
      
      <div class="mini-cal">
        <div class="mc-head">{{ miniCalHead }}</div>
        <div class="mc-grid">
          <div class="mc-day" v-for="d in ['日','一','二','三','四','五','六']" :key="d">{{ d }}</div>
          
          <div v-for="(cell, i) in miniCalCells" :key="i" 
               :class="['mc-cell', { empty: cell.empty, today: cell.isToday, selected: cell.isSelected, 'has-evt': cell.hasEvt }]"
               @click="selectDate(cell)">
            {{ cell.date || '' }}
          </div>
        </div>
      </div>
    </div>
    <div class="sb-foot">
      <div class="avatar">VP</div>
      <div class="user-info">
        <div class="uname">Executive User</div>
        <div class="ustatus"><span class="online-dot"></span>系统在线</div>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { store, setView, toggleCalendar } from '../services/store'

const miniCalHead = computed(() => {
  const d = store.currentDate
  return `${d.getFullYear()}年 ${d.getMonth() + 1}月`
})

const miniCalCells = computed(() => {
  const d = store.currentDate
  const year = d.getFullYear()
  const month = d.getMonth()
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  const cells = []
  const startEmpty = firstDay.getDay()
  
  for (let i = 0; i < startEmpty; i++) {
    cells.push({ empty: true })
  }
  
  for (let i = 1; i <= lastDay.getDate(); i++) {
    const cellDate = new Date(year, month, i)
    // mock has-evt logic based on store.events
    const hasEvt = store.events.some(e => e.col === cellDate.getDay())
    
    cells.push({
      date: i,
      fullDate: cellDate,
      empty: false,
      isToday: cellDate.toDateString() === new Date().toDateString(),
      isSelected: cellDate.toDateString() === d.toDateString(),
      hasEvt
    })
  }
  
  const totalCells = Math.ceil(cells.length / 7) * 7
  while (cells.length < totalCells) {
    cells.push({ empty: true })
  }
  
  return cells
})

const selectDate = (cell) => {
  if (cell.empty) return
  store.currentDate = cell.fullDate
}
</script>

<style scoped>
.sidebar { background: rgba(7,9,15,.4); border-right: 1px solid var(--border); display: flex; flex-direction: column; width: 220px; }
.sb-logo { padding: 24px; display: flex; align-items: center; justify-content: space-between; }
.sb-logo-name {
  font-family: var(--fd); font-size: 24px; font-weight: 500;
  background: linear-gradient(90deg, var(--gold), var(--gold2), var(--gold));
  background-size: 200% 100%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  animation: shimmer 4s linear infinite;
}
.sb-scroll { flex: 1; overflow-y: auto; padding: 0 16px; scrollbar-width: thin; scrollbar-color: var(--border) transparent; }
.nav-section { margin-bottom: 24px; }
.nav-title { font-size: 10px; color: var(--text3); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 8px; padding-left: 8px; }
.nav-item { color: var(--text2); padding: 8px 12px; border-radius: var(--r); cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
.nav-item:hover { background: var(--bg-hover); color: var(--text); }
.nav-item.active { background: var(--gold-dim); color: var(--gold); font-weight: 500; }
.nav-item.inactive { opacity: 0.35; filter: grayscale(1); }
.cal-color { width: 8px; height: 8px; border-radius: 50%; }

.divider { height: 1px; background: var(--border); margin: 16px 0; }

.mini-cal { padding: 8px; }
.mc-head { font-size: 12px; font-weight: 500; color: var(--text); margin-bottom: 12px; text-align: center; }
.mc-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; }
.mc-day { font-size: 9px; color: var(--text3); text-align: center; margin-bottom: 4px; }
.mc-cell {
  aspect-ratio: 1; display: flex; align-items: center; justify-content: center;
  font-size: 10px; color: var(--text2); border-radius: 50%; cursor: pointer; position: relative;
  transition: all .2s;
}
.mc-cell.empty { pointer-events: none; }
.mc-cell:hover:not(.today):not(.selected) { background: var(--bg-hover); color: var(--text); }
.mc-cell.today { background: var(--gold); color: #000; font-weight: 600; }
.mc-cell.selected { border: 1px solid var(--gold); color: var(--gold); }
.mc-cell.has-evt::after {
  content: ''; position: absolute; bottom: 3px; left: 50%; transform: translateX(-50%);
  width: 3px; height: 3px; border-radius: 50%; background: var(--gold);
}
.mc-cell.today.has-evt::after { background: #000; }

.sb-foot { padding: 16px; border-top: 1px solid var(--border); display: flex; align-items: center; gap: 12px; }
.avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--gold-dim); color: var(--gold); display: flex; align-items: center; justify-content: center; font-family: var(--fd); font-weight: 600; }
.uname { color: var(--text); font-weight: 500; font-size: 12px; }
.ustatus { color: var(--text2); font-size: 10px; display: flex; align-items: center; gap: 4px; margin-top: 2px; }
.online-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--teal); animation: pulse 2.2s ease-in-out infinite; }
@media (max-width: 1279px) { .sidebar { display: none; } }
</style>
