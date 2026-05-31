<template>
  <!-- Auth Gate -->
  <AuthPage v-if="!isLoggedIn()" @login-success="handleLogin" />

  <!-- Main App -->
  <div v-else :class="store.isMobile ? 'app-mobile' : 'app'">
    <!-- Desktop Layout -->
    <template v-if="!store.isMobile">
      <Sidebar @open-settings="showSettings = true" />
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
      </aside>
    </template>

    <!-- Mobile Layout -->
    <template v-else>
      <Topbar />
      <div class="mobile-content">
        <div v-show="store.mobileTab === 'today'">
          <TodayBrief />
        </div>
        <div v-show="store.mobileTab === 'calendar'" style="height: 100%">
          <CalendarGrid />
        </div>
        <div v-show="store.mobileTab === 'tasks'" style="padding: 24px; color: var(--text2); text-align: center;">
          任务页面 (开发中)
        </div>
        <div v-show="store.mobileTab === 'profile'">
          <SettingsPage @close="store.mobileTab = 'today'" />
        </div>
      </div>
      <VoiceFAB v-if="!store.showVoiceFullscreen" />
      <MobileTabBar />
      <VoiceFullscreen />
    </template>

    <!-- Settings Drawer (desktop only, overlays on right) -->
    <Transition name="drawer">
      <div v-if="showSettings && !store.isMobile" class="settings-overlay" @click.self="showSettings = false">
        <div class="settings-drawer">
          <SettingsPage @close="showSettings = false" />
        </div>
      </div>
    </Transition>

    <EventModal />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { store, loginSuccess, isLoggedIn } from './services/store'
import AuthPage from './components/AuthPage.vue'
import SettingsPage from './components/SettingsPage.vue'
import Sidebar from './components/Sidebar.vue'
import Topbar from './components/Topbar.vue'
import CalendarGrid from './components/CalendarGrid.vue'
import VoicePanel from './components/VoicePanel.vue'
import TodayBrief from './components/TodayBrief.vue'
import EventModal from './components/EventModal.vue'
import MobileTabBar from './components/MobileTabBar.vue'
import VoiceFAB from './components/VoiceFAB.vue'
import VoiceFullscreen from './components/VoiceFullscreen.vue'

const showSettings = ref(false)

const handleLogin = (user) => {
  loginSuccess(user)
}
</script>

<style scoped>
.app {
  position: relative; z-index: 1; display: grid; grid-template-columns: 220px 1fr 308px;
  height: 100vh; overflow: hidden;
}
.main { display: flex; flex-direction: column; position: relative; min-height: 0; }
.rp {
  background: var(--bg2); border-left: 1px solid var(--border);
  display: flex; flex-direction: column; padding: 16px; gap: 16px;
  height: 100vh; overflow-y: auto;
}
.rp-sec { display: flex; flex-direction: column; }

@media (max-width: 1279px) and (min-width: 768px) {
  .app { grid-template-columns: 1fr 280px; }
  .rp { width: 280px; }
}
@media (max-width: 959px) and (min-width: 768px) {
  .app { grid-template-columns: 1fr; grid-template-rows: 1fr auto; }
  .rp { flex-direction: row; height: auto; border-left: none; border-top: 1px solid var(--border); width: 100%; overflow-x: auto; }
  .rp-sec { min-width: 280px; }
}

/* Settings Drawer Overlay */
.settings-overlay {
  position: fixed;
  inset: 0;
  z-index: 500;
  background: rgba(0,0,0,.45);
  display: flex;
  justify-content: flex-end;
}

.settings-drawer {
  width: 440px;
  max-width: 90vw;
  height: 100vh;
  background: var(--bg);
  border-left: 1px solid var(--border);
  box-shadow: -8px 0 32px rgba(0,0,0,.4);
  overflow-y: auto;
}

/* Drawer transition */
.drawer-enter-active { transition: all 0.3s cubic-bezier(0.32, 0.72, 0, 1); }
.drawer-leave-active { transition: all 0.25s ease-in; }

.drawer-enter-from .settings-drawer,
.drawer-leave-to .settings-drawer {
  transform: translateX(100%);
}
.drawer-enter-from,
.drawer-leave-to {
  background: rgba(0,0,0,0);
}
</style>
