<template>
  <div class="cal-scroll" id="cal-scroll" ref="calScroll">
    
    <!-- Mobile Date Strip -->
    <div v-if="store.isMobile" class="date-strip">
      <div 
        v-for="(day, i) in weekDays" 
        :key="i"
        class="date-pill"
        :class="{ today: day.isToday, selected: day.fullDateStr === store.currentDate.toDateString() }"
        @click="selectDate(day.fullDateStr)"
      >
        <div class="date-pill-day">{{ day.label }}</div>
        <div class="date-pill-num">{{ day.date }}</div>
        <div v-if="day.hasEvents" class="date-pill-dot"></div>
      </div>
    </div>
    
    <!-- Desktop Header -->
    <div v-if="!store.isMobile && store.currentView !== 'month'" class="cal-head" id="cal-head" :class="store.currentView">
      <div class="ch-cell time-cell"></div>
      <div v-for="(day, i) in activeDays" :key="i" :class="['ch-cell', { today: day.isToday }]">
        <div class="ch-day">{{ day.label }}</div>
        <div class="ch-date">{{ day.date }}</div>
      </div>
    </div>
    
    <!-- Month View Header (Desktop only ideally, but keep for completeness) -->
    <div v-if="!store.isMobile && store.currentView === 'month'" class="cal-head month">
      <div v-for="day in ['周日','周一','周二','周三','周四','周五','周六']" :key="day" class="ch-cell">
        <div class="ch-day">{{ day }}</div>
      </div>
    </div>

    <!-- Day & Week View Grid -->
    <div v-if="store.currentView !== 'month'" 
         :class="store.isMobile ? 'cal-grid-mobile' : ['cal-grid', store.currentView]"
         @touchstart="onTouchStart"
         @touchend="onTouchEnd"
    >
      <div class="time-col">
        <div v-for="h in hours" :key="h" :class="store.isMobile ? 'mobile-time-label' : 'time-slot'">
          {{ h }}:00
        </div>
      </div>
      
      <div v-for="(day, index) in activeDays" :key="index" class="day-col">
        <div v-for="h in hours" :key="`s${h}`" class="day-slot"></div>
        
        <!-- Events -->
        <div v-for="ev in getEventsForDay(day.fullDateStr, day.colIndex)" :key="ev.id"
             :class="[store.isMobile ? 'ev-mobile' : 'ev', 'ec-' + ev.c]"
             :style="{ top: getTop(ev.s) + 'px', height: getHeight(ev.s, ev.e) + 'px' }"
             @click="openModal(ev)">
          <div class="ev-title">{{ ev.title }}</div>
          <div class="ev-time">{{ fmtTime(ev.s) }} - {{ fmtTime(ev.e) }}</div>
          <div v-if="ev.isNew" class="ev-new-badge">NEW</div>
        </div>
      </div>
      
      <!-- Current Time Indicator -->
      <div v-if="showTimeIndicator && store.currentView === 'day' && activeDays.length > 0 && activeDays[0].isToday" 
           class="ctl-full" :style="{ top: ctlTop + 'px' }">
        <div class="ctd"></div>
      </div>
    </div>
    
    <!-- Month View Grid -->
    <div v-else class="month-grid">
      <div v-for="(cell, i) in monthCells" :key="i" :class="['month-cell', { today: cell.isToday, empty: cell.empty }]">
        <div class="mc-date">{{ cell.date || '' }}</div>
        <div class="mc-events" v-if="!cell.empty">
          <div v-for="ev in getEventsForDay(cell.fullDateStr, cell.colIndex)" :key="ev.id"
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
import { store, openModal, shiftDate } from '../services/store'

const BASE_HR = 0
const HOURS = 24
const HOUR_H = store.isMobile ? 48 : 52 // Reactive or static? Assuming static on mount is fine if we reload or don't care about precise resizing on the fly
const hours = Array.from({ length: HOURS }, (_, i) => BASE_HR + i)

const hr = new Date().getHours() + new Date().getMinutes() / 60
const ctlTop = (hr - BASE_HR) * HOUR_H
const showTimeIndicator = hr >= BASE_HR && hr < BASE_HR + HOURS

const weekDays = computed(() => {
  const d = store.currentDate
  const currentDayOfWeek = d.getDay()
  const result = []
  for (let i = 0; i < 7; i++) {
    const tempDate = new Date(d)
    tempDate.setDate(d.getDate() - currentDayOfWeek + i)
    const dateStr = tempDate.toDateString()
    result.push({
      label: ['日','一','二','三','四','五','六'][i],
      date: tempDate.getDate(),
      fullDateStr: dateStr,
      isToday: dateStr === new Date().toDateString(),
      colIndex: i,
      hasEvents: store.events.some(e => e.dateStr === dateStr)
    })
  }
  return result
})

const activeDays = computed(() => {
  const d = store.currentDate
  const currentDayOfWeek = d.getDay()
  const result = []
  
  if (store.currentView === 'day') {
    result.push({
      label: ['周日','周一','周二','周三','周四','周五','周六'][currentDayOfWeek],
      date: d.getDate(),
      fullDateStr: d.toDateString(),
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
        fullDateStr: tempDate.toDateString(),
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
      fullDateStr: cellDate.toDateString(),
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

const getEventsForDay = (dateStr, col) => store.events.filter(e => {
  if (e.dateStr && e.dateStr !== dateStr) return false
  if (!e.dateStr && e.col !== col) return false // fallback
  if (e.type === '项目' && !store.calendars.project) return false
  if (e.type !== '项目' && !store.calendars.executive) return false
  return true
})

const getTop = (s) => (s - BASE_HR) * HOUR_H + (store.isMobile ? 0 : 2)
const getHeight = (s, e) => (e - s) * HOUR_H - (store.isMobile ? 2 : 4)

const fmtTime = (h) => {
  const hh = Math.floor(h)
  const mm = h % 1 === 0 ? '00' : '30'
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`
}

const selectDate = (dateStr) => {
  store.currentDate = new Date(dateStr)
}

// Swipe support
let touchStartX = 0
let touchStartY = 0

const onTouchStart = (e) => {
  if (!store.isMobile) return
  touchStartX = e.touches[0].clientX
  touchStartY = e.touches[0].clientY
}

const onTouchEnd = (e) => {
  if (!store.isMobile) return
  const dx = e.changedTouches[0].clientX - touchStartX
  const dy = e.changedTouches[0].clientY - touchStartY
  
  if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > 50) {
    shiftDate(dx < 0 ? 1 : -1) // dx < 0 means swipe left (next day)
  }
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
.cal-scroll { flex: 1; min-height: 0; overflow-y: auto; position: relative; scroll-behavior: smooth; }

/* Desktop Grid & Head */
.cal-head {
  display: grid; 
  position: sticky; top: 0; background: var(--bg); z-index: 10;
  border-bottom: 1px solid var(--border);
}
.cal-head.week { grid-template-columns: var(--cal-time-col, 52px) repeat(7, 1fr); }
.cal-head.day { grid-template-columns: var(--cal-time-col, 52px) 1fr; }
.cal-head.month { grid-template-columns: repeat(7, 1fr); }

.ch-cell { padding: 12px 8px; text-align: center; border-right: 1px solid var(--border); }
.time-cell { border-right: 1px solid var(--border); }
.ch-day { font-size: 11px; color: var(--text2); text-transform: uppercase; }
.ch-date { font-family: var(--fd); font-size: 22px; margin-top: 4px; }
.ch-cell.today .ch-date { color: var(--gold); font-weight: 600; }

.cal-grid { display: grid; background: var(--bg); min-height: 100%; position: relative; }
.cal-grid.week { grid-template-columns: var(--cal-time-col, 52px) repeat(7, 1fr); }
.cal-grid.day { grid-template-columns: var(--cal-time-col, 52px) 1fr; }

/* Mobile Grid */
.cal-grid-mobile {
  display: grid;
  grid-template-columns: var(--cal-time-col, 36px) 1fr;
  position: relative;
  background: var(--bg); min-height: 100%;
}

.mobile-time-label {
  height: var(--cal-hour-h, 48px);
  font-size: 11px;
  font-family: var(--fm);
  color: var(--text3);
  text-align: right;
  padding-right: 8px;
  padding-top: 4px;
  letter-spacing: 0.04em;
}

.time-col { border-right: 1px solid var(--border); display: flex; flex-direction: column; }
.time-slot {
  height: var(--cal-hour-h, 52px); border-bottom: 1px solid var(--border); color: var(--text3);
  font-family: var(--fm); font-size: 10px; display: flex; justify-content: center; padding-top: 4px;
}
.day-col { border-right: 1px solid var(--border); display: flex; flex-direction: column; position: relative; }
.day-slot { height: var(--cal-hour-h, 52px); border-bottom: 1px solid var(--border); }

/* Events */
.ev {
  position: absolute; left: 4px; right: 4px; border-radius: 6px; padding: 6px 8px;
  cursor: pointer; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.2); transition: transform 0.2s;
}
.ev-mobile {
  position: absolute; left: 6px; right: 6px; border-radius: 8px; padding: 6px 10px;
  cursor: pointer; border-left: 3px solid transparent; min-height: var(--touch-target, 44px);
  -webkit-tap-highlight-color: transparent; transition: transform 0.12s ease, filter 0.12s ease;
  overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,.15);
}
.ev-mobile:active { transform: scale(0.97); filter: brightness(1.15); }
.ev:hover { transform: translateY(-2px); }

.ev-title { font-weight: 500; font-size: 12px; margin-bottom: 2px; }
.ev-mobile .ev-title { font-size: 13px; font-weight: 600; line-height: 1.3; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

.ev-time { font-family: var(--fm); font-size: 10px; opacity: 0.8; }
.ev-mobile .ev-time { font-size: 11px; margin-top: 3px; opacity: 0.75; }

.ec-gold { background: var(--gold-dim); border-left: 3px solid var(--gold); color: var(--gold); }
.ec-blue { background: var(--blue-dim); border-left: 3px solid var(--blue); color: var(--blue); }
.ec-teal { background: var(--teal-dim); border-left: 3px solid var(--teal); color: var(--teal); }
.ec-red  { background: var(--red-dim); border-left: 3px solid var(--red); color: var(--red); }
.ec-amber { background: var(--amber-dim); border-left: 3px solid var(--amber); color: var(--amber); animation: glowGold 2s infinite; }

.ev-new-badge {
  position: absolute; top: 4px; right: 5px; background: var(--amber); color: #000;
  font-size: 8px; font-weight: 700; padding: 1px 4px; border-radius: 3px; animation: newBadge .4s ease;
}

.ctl-full { position: absolute; left: 52px; right: 0; height: 1.5px; background: rgba(200, 164, 90, 0.4); z-index: 5; pointer-events: none; }
@media (max-width: 767px) {
  .ctl-full { left: 36px; }
}
.ctl-full .ctd {
  position: absolute; left: -4px; top: -4px; width: 8px; height: 8px; border-radius: 50%;
  background: var(--gold); animation: pulse 1.6s ease-in-out infinite; box-shadow: 0 0 6px rgba(200, 164, 90, 0.6);
}

/* Mobile Date Strip */
.date-strip {
  display: flex; overflow-x: auto; scrollbar-width: none; -ms-overflow-style: none; scroll-snap-type: x mandatory;
  padding: var(--sp-sm, 10px) var(--sp-md, 16px); gap: var(--sp-xs, 6px); border-bottom: 1px solid var(--border);
}
.date-strip::-webkit-scrollbar { display: none; }
.date-pill {
  flex-shrink: 0; display: flex; flex-direction: column; align-items: center; justify-content: center;
  width: 44px; height: 60px; border-radius: 14px; cursor: pointer; scroll-snap-align: center;
  transition: all 0.2s ease; -webkit-tap-highlight-color: transparent;
}
.date-pill-day { font-size: 10px; color: var(--text2); font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; margin-bottom: 4px; }
.date-pill-num { font-size: 18px; font-weight: 300; color: var(--text); font-family: var(--fu); line-height: 1; }
.date-pill.today { background: var(--gold); }
.date-pill.today .date-pill-day, .date-pill.today .date-pill-num { color: #000; font-weight: 700; }
.date-pill.selected:not(.today) { background: var(--gold-dim); border: 1px solid var(--gold-border); }
.date-pill.selected:not(.today) .date-pill-num { color: var(--gold); }
.date-pill-dot { width: 4px; height: 4px; border-radius: 50%; background: var(--gold); margin-top: 4px; opacity: 0.7; }
.date-pill.today .date-pill-dot { background: #000; opacity: 0.5; }

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
</style>
