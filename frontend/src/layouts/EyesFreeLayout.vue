<template>
  <div 
    ref="containerRef" 
    class="eyes-free-layout"
    :class="[
      `eyes-free-layout--state-${sessionStore.voiceState}`,
      { 'eyes-free-layout--active': gestureActive }
    ]"
    role="application"
    aria-label="无障碍盲听模式。全屏手势：长按录音，双击打断播放，双指左右滑动切换日程，双击顶部退出该模式。"
  >
    <!-- 顶部状态与退出控制 -->
    <header class="eyes-free-header">
      <div class="eyes-free-header__info">
        <span class="eyes-free-header__indicator">👁️❌</span>
        <h1 class="eyes-free-header__title">盲听模式</h1>
      </div>
      <button 
        class="exit-btn vc-elevated" 
        aria-label="双击此处或点击以退出盲听模式，返回标准布局"
        @click="exitEyesFree"
      >
        退出模式
      </button>
    </header>

    <!-- 巨型全屏手势感知状态区 -->
    <div class="gesture-arena">
      <div class="gesture-arena__brand">
        <div class="pulse-ring" v-if="sessionStore.isRecording" />
        <div class="avatar-ring" :class="`avatar-ring--${sessionStore.voiceState}`">
          <span class="avatar-ring__emoji">{{ stateEmoji }}</span>
        </div>
        <h2 class="gesture-arena__title">{{ stateTitle }}</h2>
        <p class="gesture-arena__tip">{{ stateSubtitle }}</p>
      </div>

      <!-- 实时识别文本展示 (巨大字号，极高对比度) -->
      <div class="transcript-display" v-if="sessionStore.partialTranscript || sessionStore.finalTranscript">
        <p class="transcript-display__text">
          {{ sessionStore.finalTranscript || sessionStore.partialTranscript }}
        </p>
      </div>

      <!-- 对话记录中的最后一条系统播报内容 -->
      <div class="latest-msg" v-else-if="latestSystemMessage">
        <p class="latest-msg__label">助手播报</p>
        <p class="latest-msg__text">{{ latestSystemMessage.content }}</p>
      </div>
    </div>

    <!-- 辅助脚页：手势说明书 -->
    <footer class="eyes-free-footer">
      <div class="instruction-grid">
        <div class="inst-item"><span class="inst-item__gesture">👆 长按</span><span class="inst-item__action">开始说话</span></div>
        <div class="inst-item"><span class="inst-item__gesture">👆👆 双击</span><span class="inst-item__action">打断播报</span></div>
        <div class="inst-item"><span class="inst-item__gesture">✌️ 左右滑</span><span class="inst-item__action">切换日程</span></div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useSessionStore } from '@/stores/useSessionStore'
import { useSettingsStore } from '@/stores/useSettingsStore'
import { useAccessibility } from '@/composables/useAccessibility'
import { useHapticFeedback } from '@/composables/useHapticFeedback'
import { useTTSPlayer } from '@/composables/useTTSPlayer'

const router = useRouter()
const sessionStore = useSessionStore()
const settingsStore = useSettingsStore()
const { vibrate } = useHapticFeedback()
const { speakText, stop: stopTTS } = useTTSPlayer()

const containerRef = ref<HTMLElement | null>(null)

// 最新的一条系统播报
const latestSystemMessage = computed(() => {
  return [...sessionStore.messages]
    .reverse()
    .find(m => m.role === 'system')
})

const stateEmoji = computed(() => {
  switch (sessionStore.voiceState) {
    case 'recording': return '🎙️'
    case 'processing': return '⏳'
    case 'tts_playing': return '🔊'
    case 'clarifying': return '❓'
    case 'conflict': return '⚠️'
    case 'success': return '✅'
    case 'error': return '❌'
    default: return '👋'
  }
})

const stateTitle = computed(() => {
  switch (sessionStore.voiceState) {
    case 'recording': return '正在倾听...'
    case 'processing': return '正在思考...'
    case 'tts_playing': return '正在播报...'
    case 'clarifying': return '需要确认信息'
    case 'conflict': return '发现时间冲突'
    case 'success': return '操作成功完成'
    case 'error': return '出了点小问题'
    default: return '长按任意位置说话'
  }
})

const stateSubtitle = computed(() => {
  switch (sessionStore.voiceState) {
    case 'recording': return '松开手指即可发送，上滑取消录音'
    case 'processing': return '智能解析中，请稍候'
    case 'tts_playing': return '双击屏幕任意位置可打断播放'
    case 'clarifying': return '请回答缺失的信息'
    case 'conflict': return '已检测到重叠日程，请确认方案'
    case 'success': return '日程已保存，双击可播放详情'
    case 'error': return '请双击重试或重新长按说话'
    default: return '盲听模式已启用，点击屏幕各处均有语音提示'
  }
})

// 无障碍大面积手势绑定
const { gestureActive } = useAccessibility(containerRef, {
  longPressThreshold: 350,
  onLongPressStart: () => {
    vibrate('recording')
    sessionStore.setVoiceState('recording')
    sessionStore.updatePartialTranscript('')
    sessionStore.setFinalTranscript('')
    stopTTS() // 长按即刻打断播放并准备倾听
  },
  onLongPressEnd: () => {
    vibrate('processing')
    sessionStore.setVoiceState('processing')
    // 模拟识别逻辑：延时返回成功
    setTimeout(() => {
      sessionStore.setFinalTranscript('明天下午三点开会')
      vibrate('success')
      sessionStore.setVoiceState('success')
      speakText('已为您生成日程：明天下午三点开会')
    }, 1500)
  },
  onDoubleTap: () => {
    vibrate('tap')
    if (sessionStore.isTTSPlaying) {
      stopTTS()
      sessionStore.setVoiceState('idle')
    } else {
      speakText('当前盲听模式运行正常，长按屏幕任意位置即可录入新日程。')
    }
  },
  onSwipeLeft: () => {
    vibrate('tap')
    speakText('切换到下一天日程')
  },
  onSwipeRight: () => {
    vibrate('tap')
    speakText('切换到上一天日程')
  }
})

function exitEyesFree() {
  vibrate('recording')
  settingsStore.updateSetting('layout_mode', 'default')
  router.push('/')
}
</script>

<style scoped>
.eyes-free-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
  width: 100vw;
  background-color: #050B14; /* 极致纯黑深蓝，降低视觉干扰，提升强对比度 */
  color: #FFFFFF;
  padding: var(--vc-space-lg);
  overflow: hidden;
  user-select: none;
  touch-action: none;
  transition: background-color var(--vc-transition-slow);
}

/* 顶部栏 */
.eyes-free-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 60px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.15);
}

.eyes-free-header__info {
  display: flex;
  align-items: center;
  gap: var(--vc-space-sm);
}

.eyes-free-header__indicator {
  font-size: 28px;
}

.eyes-free-header__title {
  font-size: var(--vc-text-xl);
  font-weight: var(--vc-weight-bold);
  letter-spacing: 0.5px;
}

.exit-btn {
  background: #FF453A;
  color: white;
  font-weight: var(--vc-weight-bold);
  font-size: var(--vc-text-base);
  padding: var(--vc-space-sm) var(--vc-space-lg);
  border-radius: var(--vc-radius-lg);
  border: 2px solid white;
  transition: all var(--vc-transition-base);
}

.exit-btn:active {
  transform: scale(0.92);
  background: #D32F2F;
}

/* 巨型手势交互中心 */
.gesture-arena {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  position: relative;
  gap: var(--vc-space-xl);
  padding: var(--vc-space-xl) 0;
}

.gesture-arena__brand {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 2;
}

.avatar-ring {
  width: 130px;
  height: 130px;
  border-radius: var(--vc-radius-full);
  background: rgba(255, 255, 255, 0.05);
  border: 4px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--vc-space-lg);
  transition: all var(--vc-transition-spring);
}

.avatar-ring__emoji {
  font-size: 64px;
  transition: transform var(--vc-transition-spring);
}

/* 状态色彩高对比度映射 */
.avatar-ring--recording {
  border-color: #FF453A;
  background: rgba(255, 69, 58, 0.15);
  box-shadow: 0 0 40px rgba(255, 69, 58, 0.4);
}
.avatar-ring--recording .avatar-ring__emoji {
  transform: scale(1.15);
}

.avatar-ring--processing {
  border-color: #FFD60A;
  background: rgba(255, 214, 10, 0.15);
  box-shadow: 0 0 40px rgba(255, 214, 10, 0.3);
  animation: rotateSpin 2s linear infinite;
}

@keyframes rotateSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.avatar-ring--success {
  border-color: #30D158;
  background: rgba(48, 209, 88, 0.15);
  box-shadow: 0 0 40px rgba(48, 209, 88, 0.4);
}

.gesture-arena__title {
  font-size: var(--vc-text-3xl);
  font-weight: var(--vc-weight-bold);
  margin-bottom: var(--vc-space-sm);
  letter-spacing: 0.5px;
}

.gesture-arena__tip {
  font-size: var(--vc-text-lg);
  color: #BFBFBF;
  max-width: 320px;
  line-height: 1.4;
}

/* 高对比度转写与最后一条播报 */
.transcript-display,
.latest-msg {
  width: 100%;
  max-width: 480px;
  background: rgba(255, 255, 255, 0.08);
  border: 2px solid rgba(255, 255, 255, 0.15);
  border-radius: var(--vc-radius-lg);
  padding: var(--vc-space-lg);
  margin-top: var(--vc-space-md);
}

.transcript-display__text,
.latest-msg__text {
  font-size: var(--vc-text-xl);
  font-weight: var(--vc-weight-bold);
  line-height: 1.5;
  color: #FFFFFF;
}

.latest-msg__label {
  font-size: var(--vc-text-xs);
  color: #FFD60A;
  font-weight: var(--vc-weight-bold);
  margin-bottom: var(--vc-space-xs);
  text-transform: uppercase;
}

/* 巨型录音脉冲环 */
.pulse-ring {
  position: absolute;
  top: 10px;
  width: 110px;
  height: 110px;
  border-radius: var(--vc-radius-full);
  border: 4px solid #FF453A;
  animation: pulseRipple 1.8s infinite cubic-bezier(0.25, 0, 0, 1);
  pointer-events: none;
}

@keyframes pulseRipple {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.6); opacity: 0; }
}

/* 底部手势快捷说明 */
.eyes-free-footer {
  border-top: 2px solid rgba(255, 255, 255, 0.15);
  padding-top: var(--vc-space-md);
  height: 80px;
}

.instruction-grid {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.inst-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.inst-item__gesture {
  font-size: var(--vc-text-base);
  font-weight: var(--vc-weight-bold);
  color: #FFD60A;
}

.inst-item__action {
  font-size: var(--vc-text-sm);
  color: #D1D1D6;
}

/* 屏幕全局触控反馈 */
.eyes-free-layout--active {
  background-color: #0B1E36;
}
</style>
