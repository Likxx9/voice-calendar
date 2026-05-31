<template>
  <div v-if="store.modalVisible" 
       :class="store.isMobile ? 'sheet-overlay' : 'overlay'" 
       @click="closeModal"
       ref="overlayRef"
  >
    <div 
      :class="store.isMobile ? 'bottom-sheet' : 'modal'" 
      @click.stop 
      ref="sheetRef"
      @touchstart="onTouchStart"
      @touchmove="onTouchMove"
      @touchend="onTouchEnd"
    >
      <div v-if="store.isMobile" class="sheet-handle"></div>

      <div class="m-head" v-if="store.selectedEvent && !store.isMobile">
        <div class="m-tag" :class="'ec-' + store.selectedEvent.c">{{ store.selectedEvent.type }}</div>
        <button class="m-close" @click="closeModal">✕</button>
      </div>
      
      <div v-if="store.isMobile && store.selectedEvent" class="sheet-header">
        <div class="sheet-event-color-bar" :class="'bg-' + store.selectedEvent.c"></div>
        <h2 class="sheet-event-title">{{ store.selectedEvent.title }}</h2>
      </div>
      <h2 class="m-title" v-else-if="store.selectedEvent">{{ store.selectedEvent.title }}</h2>
      
      <div :class="store.isMobile ? 'sheet-body' : 'm-body'" v-if="store.selectedEvent">
        <div :class="store.isMobile ? 'sheet-detail-row' : 'm-row'">
          <div :class="store.isMobile ? 'sheet-detail-icon' : 'm-icon'">🕒</div>
          <div :class="store.isMobile ? 'sheet-detail-content' : ''">
            <div v-if="store.isMobile" class="sheet-detail-label">时间</div>
            <div :class="store.isMobile ? 'sheet-detail-value' : ''">
              <template v-if="!store.isMobile">时间: </template>
              {{ fmtTime(store.selectedEvent.s) }} - {{ fmtTime(store.selectedEvent.e) }}
            </div>
          </div>
        </div>
        
        <div :class="store.isMobile ? 'sheet-detail-row' : 'm-row'">
          <div :class="store.isMobile ? 'sheet-detail-icon' : 'm-icon'">📍</div>
          <div :class="store.isMobile ? 'sheet-detail-content' : ''">
            <div v-if="store.isMobile" class="sheet-detail-label">地点</div>
            <div :class="store.isMobile ? 'sheet-detail-value' : ''">
              <template v-if="!store.isMobile">地点: </template>
              {{ store.selectedEvent.loc }}
            </div>
          </div>
        </div>
        
        <div :class="store.isMobile ? 'sheet-detail-row' : 'm-row'">
          <div :class="store.isMobile ? 'sheet-detail-icon' : 'm-icon'">👥</div>
          <div :class="store.isMobile ? 'sheet-detail-content' : ''">
            <div v-if="store.isMobile" class="sheet-detail-label">参与人数</div>
            <div :class="store.isMobile ? 'sheet-detail-value' : ''">
              <template v-if="!store.isMobile">参与: </template>
              {{ store.selectedEvent.att || 2 }} 人
            </div>
          </div>
        </div>
      </div>
      
      <div :class="store.isMobile ? 'sheet-actions' : 'm-foot'">
        <button :class="store.isMobile ? 'sheet-btn sheet-btn-danger' : 'btn-outline'">取消日程</button>
        <button :class="store.isMobile ? 'sheet-btn sheet-btn-primary' : 'btn-primary'">进入会议</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store, closeModal } from '../services/store'

const fmtTime = (h) => {
  const hh = Math.floor(h)
  const mm = h % 1 === 0 ? '00' : '30'
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`
}

// Bottom Sheet Swipe to close
const sheetRef = ref(null)
const overlayRef = ref(null)
let startY = 0
let currentY = 0
let isDragging = false

const onTouchStart = (e) => {
  if (!store.isMobile || !sheetRef.value) return
  startY = e.touches[0].clientY
  isDragging = true
  sheetRef.value.style.transition = 'none'
}

const onTouchMove = (e) => {
  if (!isDragging) return
  const dy = e.touches[0].clientY - startY
  if (dy > 0) {
    currentY = dy
    sheetRef.value.style.transform = `translateY(${dy}px)`
    if (overlayRef.value) {
      const opacity = Math.max(1 - dy / 300, 0)
      overlayRef.value.style.opacity = opacity.toString()
    }
  }
}

const onTouchEnd = () => {
  if (!isDragging) return
  isDragging = false
  if (!sheetRef.value) return
  
  sheetRef.value.style.transition = 'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)'
  
  if (currentY > 120) {
    sheetRef.value.style.transform = 'translateY(100%)'
    setTimeout(() => {
      closeModal()
      if (sheetRef.value) sheetRef.value.style.transform = 'translateY(0)'
      if (overlayRef.value) overlayRef.value.style.opacity = '1'
      currentY = 0
    }, 300)
  } else {
    sheetRef.value.style.transform = 'translateY(0)'
    if (overlayRef.value) overlayRef.value.style.opacity = '1'
    currentY = 0
  }
}
</script>

<style scoped>
/* Desktop Modal */
.overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.75);
  backdrop-filter: blur(6px); z-index: 200; animation: fadeUp .2s ease;
  display: flex; align-items: center; justify-content: center;
}
.modal {
  background: var(--bg2); border: 1px solid var(--gold-border);
  border-radius: 14px; padding: 26px; box-shadow: 0 24px 64px rgba(0,0,0,.6);
  animation: fadeUp .25s ease; width: 340px; max-width: 90vw;
}
.m-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.m-tag { font-size: 11px; padding: 4px 8px; border-radius: 4px; font-weight: 500; }
.m-close { background: none; border: none; color: var(--text2); font-size: 16px; cursor: pointer; transition: color .2s; }
.m-close:hover { color: var(--text); }
.m-title { font-family: var(--fd); font-size: 23px; font-weight: 400; color: var(--text); margin-bottom: 24px; }
.m-row { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; color: var(--text); font-size: 13px; }
.m-icon { font-size: 16px; opacity: 0.8; }
.m-foot { margin-top: 32px; display: flex; gap: 12px; justify-content: flex-end; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); padding: 8px 16px; border-radius: var(--r); cursor: pointer; transition: all .2s; }
.btn-outline:hover { background: var(--bg-hover); border-color: var(--gold-border); color: var(--gold); }
.btn-primary { background: var(--gold-dim); border: 1px solid var(--gold-border); color: var(--gold); padding: 8px 16px; border-radius: var(--r); cursor: pointer; transition: all .2s; font-weight: 500; }
.btn-primary:hover { background: rgba(200,164,90,.2); }

/* Colors */
.ec-gold { background: var(--gold-dim); color: var(--gold); border: 1px solid var(--gold-border); }
.ec-blue { background: var(--blue-dim); color: var(--blue); border: 1px solid rgba(75,150,255,.2); }
.ec-teal { background: var(--teal-dim); color: var(--teal); border: 1px solid rgba(45,212,191,.2); }
.ec-red  { background: var(--red-dim); color: var(--red); border: 1px solid rgba(248,113,113,.2); }
.ec-amber { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(251,191,36,.2); }

.bg-gold { background: var(--gold); }
.bg-blue { background: var(--blue); }
.bg-teal { background: var(--teal); }
.bg-red  { background: var(--red); }
.bg-amber { background: var(--amber); }

/* Mobile Bottom Sheet */
.sheet-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,.6);
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
  z-index: 200; animation: overlayIn 0.3s ease;
}

@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

.bottom-sheet {
  position: fixed; left: 0; right: 0; bottom: 0;
  background: var(--bg2);
  border-radius: var(--r-lg, 24px) var(--r-lg, 24px) 0 0;
  z-index: 201;
  padding-bottom: env(safe-area-inset-bottom);
  max-height: 85vh; overflow-y: auto;
  animation: sheetSlideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  border-top: 1px solid var(--gold-border);
  box-shadow: 0 -8px 40px rgba(0,0,0,.5);
}

@keyframes sheetSlideUp {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}

.sheet-handle {
  width: var(--sheet-handle-w, 40px);
  height: var(--sheet-handle-h, 4px);
  border-radius: 2px;
  background: var(--text3);
  margin: 14px auto 0;
}

.sheet-header {
  padding: var(--sp-lg, 24px) var(--sp-lg, 24px) var(--sp-md, 16px);
  border-bottom: 1px solid var(--border);
}

.sheet-event-color-bar {
  width: 32px; height: 4px; border-radius: 2px; margin-bottom: var(--sp-sm, 10px);
}

.sheet-event-title {
  font-size: 20px; font-weight: 600; color: var(--text); line-height: 1.3; font-family: var(--fu);
}

.sheet-body {
  padding: var(--sp-md, 16px) var(--sp-lg, 24px);
}

.sheet-detail-row {
  display: flex; align-items: center; gap: var(--sp-md, 16px);
  padding: 12px 0; border-bottom: 1px solid var(--border);
  min-height: var(--touch-target, 44px);
}
.sheet-detail-row:last-child { border-bottom: none; }

.sheet-detail-icon {
  width: 36px; height: 36px; border-radius: 10px; background: var(--bg3);
  display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
}

.sheet-detail-label {
  font-size: 11px; color: var(--text2); margin-bottom: 2px; letter-spacing: 0.04em;
}

.sheet-detail-value {
  font-size: 15px; color: var(--text); font-weight: 500;
}

.sheet-actions {
  display: flex; gap: var(--sp-sm, 10px);
  padding: var(--sp-md, 16px) var(--sp-lg, 24px);
  padding-bottom: var(--sp-lg, 24px);
}

.sheet-btn {
  flex: 1; height: var(--touch-target, 44px); border-radius: var(--r, 12px);
  font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.15s ease;
  -webkit-tap-highlight-color: transparent; display: flex; align-items: center; justify-content: center; gap: 6px;
}

.sheet-btn-primary { background: var(--gold-dim); border: 1px solid var(--gold-border); color: var(--gold); }
.sheet-btn-danger { background: rgba(248,113,113,.1); border: 1px solid rgba(248,113,113,.2); color: var(--red); }
.sheet-btn:active { transform: scale(0.96); }
</style>
