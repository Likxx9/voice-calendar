<template>
  <div v-if="store.modalVisible" class="overlay" @click="closeModal">
    <div class="modal" @click.stop>
      <div class="m-head" v-if="store.selectedEvent">
        <div class="m-tag" :class="'ec-' + store.selectedEvent.c">{{ store.selectedEvent.type }}</div>
        <button class="m-close" @click="closeModal">✕</button>
      </div>
      <h2 class="m-title" v-if="store.selectedEvent">{{ store.selectedEvent.title }}</h2>
      
      <div class="m-body" v-if="store.selectedEvent">
        <div class="m-row">
          <span class="m-icon">🕒</span>
          <span>时间: {{ fmtTime(store.selectedEvent.s) }} - {{ fmtTime(store.selectedEvent.e) }}</span>
        </div>
        <div class="m-row">
          <span class="m-icon">📍</span>
          <span>地点: {{ store.selectedEvent.loc }}</span>
        </div>
        <div class="m-row">
          <span class="m-icon">👥</span>
          <span>参与: {{ store.selectedEvent.att || 2 }} 人</span>
        </div>
      </div>
      
      <div class="m-foot">
        <button class="btn-outline">重新安排</button>
        <button class="btn-primary">进入会议</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { store, closeModal } from '../services/store'

const fmtTime = (h) => {
  const hh = Math.floor(h)
  const mm = h % 1 === 0 ? '00' : '30'
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`
}
</script>

<style scoped>
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

.ec-gold { background: var(--gold-dim); color: var(--gold); border: 1px solid var(--gold-border); }
.ec-blue { background: var(--blue-dim); color: var(--blue); border: 1px solid rgba(75,150,255,.2); }
.ec-teal { background: var(--teal-dim); color: var(--teal); border: 1px solid rgba(45,212,191,.2); }
.ec-red  { background: var(--red-dim); color: var(--red); border: 1px solid rgba(248,113,113,.2); }
.ec-amber { background: var(--amber-dim); color: var(--amber); border: 1px solid rgba(251,191,36,.2); }
</style>
