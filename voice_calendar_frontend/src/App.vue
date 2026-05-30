<template>
  <div class="app">
    <Sidebar />
    <main class="main">
      <Topbar />
      <CalendarGrid />
    </main>
    <aside class="rp">
      <div class="rp-sec">
        <VoicePanel />
      </div>
      <div class="rp-sec" id="today-brief-sec">
        <TodayBrief />
      </div>
      <div class="rp-sec">
        <Suggestions />
      </div>
    </aside>
    
    <EventModal />
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
import CalendarGrid from './components/CalendarGrid.vue'
import VoicePanel from './components/VoicePanel.vue'
import TodayBrief from './components/TodayBrief.vue'
import Suggestions from './components/Suggestions.vue'
import EventModal from './components/EventModal.vue'
</script>

<style scoped>
.app {
  position: relative; z-index: 1; display: grid; grid-template-columns: 220px 1fr 308px;
  height: 100vh; overflow: hidden;
}
.main { display: flex; flex-direction: column; position: relative; }
.rp {
  background: var(--bg2); border-left: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 16px; gap: 16px;
  height: 100vh; overflow-y: auto;
}
.rp-sec { display: flex; flex-direction: column; }

@media (max-width: 1279px) {
  .app { grid-template-columns: 1fr 280px; }
  .rp { width: 280px; }
}
@media (max-width: 959px) {
  .app { grid-template-columns: 1fr; grid-template-rows: 1fr auto; }
  .rp { flex-direction: row; height: auto; border-left: none; border-top: 1px solid var(--border); width: 100%; overflow-x: auto; }
  .rp-sec { min-width: 280px; }
}
@media (max-width: 767px) {
  .app { display: flex; flex-direction: column; }
  .rp { position: fixed; bottom: 0; left: 0; right: 0; background: rgba(12, 16, 32, 0.95); backdrop-filter: blur(10px); border-top: 1px solid var(--gold-border); flex-direction: column; padding: 24px; z-index: 100; max-height: 80vh; overflow-y: auto; }
  .rp-sec { min-width: 100%; }
}
</style>
