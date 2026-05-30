<template>
  <div class="cal-scroll" id="cal-scroll" ref="calScroll">
    <!-- Day & Week View Header -->
    <div v-if="store.currentView !== 'month'" class="cal-head" id="cal-head" :class="store.currentView">
      <div class="ch-cell time-cell"></div>
      <div v-for="(day, i) in activeDays" :key="i" :class="['ch-cell', { today: day.isToday }]">
        <div class="ch-day">{{ day.label }}</div>
        <div class="ch-date">{{ day.date }}</div>
      </div>
    </div>
    
    <!-- Month View Header -->
    <div v-else class="cal-head month">
      <div v-for="day in ['周日','周一','周二','周三','周四','周五','周六']" :key="day" class="ch-cell">
        <div class="ch-day">{{ day }}</div>
      </div>
    </div>

    <!-- Day & Week View Grid -->
    <div v-if="store.currentView !== 'month'" class="cal-grid" id="cal-grid" :class="store.currentView">
      <div class="time-col">
        <div v-for="h in hours" :key="h" class="time-slot">{{ h }}:00</div>
      </div>
      
      <div v-for="(day, index) in activeDays" :key="index" class="day-col">
        <div v-for="h in hours" :key="`s${h}`" class="day-slot"></div>
        
        <!-- Current Time Indicator -->
        <div v-if="day.isToday" class="ctl" :style="{ top: ctlTop + 'px' }">
          <div class="ctd"></div>
        </div>
        
        <!-- Events -->
        <div v-for="ev in getEventsForCol(day.colIndex)" :key="ev.id"
             :class="['ev', 'ec-' + ev.c]"
             :style="{ top: getTop(ev.s) + 'px', height: getHeight(ev.s, ev.e) + 'px' }"
             @click="openModal(ev)">
          <div class="ev-title">{{ ev.title }}</div>
          <div class="ev-time">{{ fmtTime(ev.s) }} - {{ fmtTime(ev.e) }}</div>
          <div v-if="ev.isNew" class="ev-new-badge">NEW</div>
        </div>
      </div>
    </div>
    
    <!-- Month View Grid -->
    <div v-else class="month-grid">
      <div v-for="(cell, i) in monthCells" :key="i" :class="['month-cell', { today: cell.isToday, empty: cell.empty }]">
        <div class="mc-date">{{ cell.date || '' }}</div>
        <div class="mc-events" v-if="!cell.empty">
          <div v-for="ev in getEventsForCol(cell.colIndex)" :key="ev.id"
               :class="['mc-ev-dot', 'ec-' + ev.c]"
               @click="openModal(ev)">
            {{ ev.title }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { store, openModal } from '../services/store'

const BASE_HR = 8
const HOURS = 13
const HOUR_H = 52
const hours = Array.from({ length: HOURS }, (_, i) => BASE_HR + i)

const hr = new Date().getHours() + new Date().getMinutes() / 60
const ctlTop = (hr - BASE_HR) * HOUR_H

const activeDays = computed(() => {
  const d = store.currentDate
  const currentDayOfWeek = d.getDay()
  const result = []
  
  if (store.currentView === 'day') {
    result.push({
      label: ['周日','周一','周二','周三','周四','周五','周六'][currentDayOfWeek],
      date: d.getDate(),
      isToday: d.toDateString() === new Date().toDateString(),
      colIndex: currentDayOfWeek
    })
  } else {
    for (let i = 0; i < 7; i++) {
      const tempDate = new Date(d)
      tempDate.setDate(d.getDate() - currentDayOfWeek + i)
      result.push({
        label: ['周日','周一','周二','周三','周四','周五','周六'][i],
        date: tempDate.getDate(),
        isToday: tempDate.toDateString() === new Date().toDateString(),
        colIndex: i
      })
    }
  }
  return result
})

const monthCells = computed(() => {
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
    cells.push({
      date: i,
      empty: false,
      isToday: cellDate.toDateString() === new Date().toDateString(),
      colIndex: cellDate.getDay() // Use col index to mock events for now
    })
  }
  
  const totalCells = Math.ceil(cells.length / 7) * 7
  while (cells.length < totalCells) {
    cells.push({ empty: true })
  }
  
  return cells
})

const calScroll = ref(null)

const getEventsForCol = (col) => store.events.filter(e => {
  if (e.col !== col) return false
  if (e.type === '项目' && !store.calendars.project) return false
  if (e.type !== '项目' && !store.calendars.executive) return false
  return true
})

const getTop = (s) => (s - BASE_HR) * HOUR_H + 2
const getHeight = (s, e) => (e - s) * HOUR_H - 4

const fmtTime = (h) => {
  const hh = Math.floor(h)
  const mm = h % 1 === 0 ? '00' : '30'
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`
}

watch(() => store.currentView, (newView) => {
  if (newView !== 'month') {
    setTimeout(() => {
      if(calScroll.value) {
        calScroll.value.scrollTop = (9 - BASE_HR) * HOUR_H - 16
      }
    }, 50)
  }
})

onMounted(() => {
  setTimeout(() => {
    if(calScroll.value && store.currentView !== 'month') {
      calScroll.value.scrollTop = (9 - BASE_HR) * HOUR_H - 16
    }
  }, 100)
})
</script>

<style scoped>
.cal-scroll { flex: 1; overflow-y: auto; position: relative; scroll-behavior: smooth; }
.cal-head {
  display: grid; 
  position: sticky; top: 0; background: var(--bg); z-index: 10;
  border-bottom: 1px solid var(--border);
}
.cal-head.week { grid-template-columns: 52px repeat(7, 1fr); }
.cal-head.day { grid-template-columns: 52px 1fr; }
.cal-head.month { grid-template-columns: repeat(7, 1fr); }

.ch-cell { padding: 12px 8px; text-align: center; border-right: 1px solid var(--border); }
.time-cell { border-right: 1px solid var(--border); }
.ch-day { font-size: 11px; color: var(--text2); text-transform: uppercase; }
.ch-date { font-family: var(--fd); font-size: 22px; margin-top: 4px; }
.ch-cell.today .ch-date { color: var(--gold); font-weight: 600; }

.cal-grid { display: grid; background: var(--bg); min-height: 100%; }
.cal-grid.week { grid-template-columns: 52px repeat(7, 1fr); }
.cal-grid.day { grid-template-columns: 52px 1fr; }

.time-col { border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.time-slot {
  height: 52px; border-bottom: 1px solid var(--border); color: var(--text3);
  font-family: var(--fm); font-size: 10px; display: flex; justify-content: center; padding-top: 4px;
}
.day-col { border-right: 1px solid var(--border); display: flex; flex-direction: column; position: relative; }
.day-slot { height: 52px; border-bottom: 1px solid var(--border); }

.ev {
  position: absolute; left: 4px; right: 4px; border-radius: 6px; padding: 6px 8px;
  cursor: pointer; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.2); transition: transform 0.2s;
}
.ev:hover { transform: translateY(-2px); }
.ev-title { font-weight: 500; font-size: 12px; margin-bottom: 2px; }
.ev-time { font-family: var(--fm); font-size: 10px; opacity: 0.8; }

.ec-gold { background: var(--gold-dim); border-left: 3px solid var(--gold); color: var(--gold); }
.ec-blue { background: var(--blue-dim); border-left: 3px solid var(--blue); color: var(--blue); }
.ec-teal { background: var(--teal-dim); border-left: 3px solid var(--teal); color: var(--teal); }
.ec-red  { background: var(--red-dim); border-left: 3px solid var(--red); color: var(--red); }
.ec-amber { background: var(--amber-dim); border-left: 3px solid var(--amber); color: var(--amber); animation: glowGold 2s infinite; }

.ev-new-badge {
  position: absolute; top: 4px; right: 5px; background: var(--amber); color: #000;
  font-size: 8px; font-weight: 700; padding: 1px 4px; border-radius: 3px; animation: newBadge .4s ease;
}

.ctl { position: absolute; left: 0; right: 0; height: 1.5px; background: var(--gold); z-index: 5; }
.ctd {
  position: absolute; left: -4px; top: -4px; width: 8px; height: 8px; border-radius: 50%;
  background: var(--gold); animation: pulse 1.6s ease-in-out infinite;
}

/* Month Grid */
.month-grid { display: grid; grid-template-columns: repeat(7, 1fr); min-height: 100%; border-left: 1px solid var(--border); }
.month-cell { min-height: 100px; border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); padding: 8px; }
.month-cell.empty { background: rgba(255,255,255,0.01); }
.mc-date { font-family: var(--fd); font-size: 16px; color: var(--text2); margin-bottom: 8px; text-align: right; }
.month-cell.today .mc-date { color: var(--gold); font-weight: 600; }
.mc-events { display: flex; flex-direction: column; gap: 4px; }
.mc-ev-dot { 
  font-size: 10px; padding: 2px 6px; border-radius: 3px; cursor: pointer; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  border-left-width: 2px; border-left-style: solid;
}
.mc-ev-dot:hover { filter: brightness(1.2); }

@media (max-width: 767px) {
  .cal-head.week { grid-template-columns: 40px repeat(7, 1fr); }
  .cal-grid.week { grid-template-columns: 40px repeat(7, 1fr); }
  .ch-day { font-size: 9px; }
  .ch-date { font-size: 16px; }
}
</style>
