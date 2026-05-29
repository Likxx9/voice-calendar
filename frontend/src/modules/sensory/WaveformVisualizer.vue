<template>
  <canvas
    ref="canvasRef"
    class="waveform-visualizer"
    :class="{ 'waveform-visualizer--active': isActive }"
    :width="width"
    :height="height"
    :aria-label="isActive ? '音频波形正在录制' : '音频波形待机'"
    role="img"
  />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = withDefaults(defineProps<{
  isActive?: boolean
  volume?: number         // 0~1
  width?: number
  height?: number
  barCount?: number
  barColor?: string
  barActiveColor?: string
}>(), {
  isActive: false,
  volume: 0,
  width: 300,
  height: 64,
  barCount: 40,
  barColor: 'hsla(220, 15%, 40%, 0.3)',
  barActiveColor: '',
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let animationFrame = 0
let bars: number[] = []

// 初始化柱状数据
function initBars() {
  bars = Array.from({ length: props.barCount }, () => 0.05)
}

function draw() {
  const canvas = canvasRef.value
  if (!canvas) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  canvas.width = props.width * dpr
  canvas.height = props.height * dpr
  ctx.scale(dpr, dpr)

  ctx.clearRect(0, 0, props.width, props.height)

  const gap = 2
  const barWidth = (props.width - gap * (props.barCount - 1)) / props.barCount
  const maxBarHeight = props.height * 0.85
  const centerY = props.height / 2

  // 获取 CSS 变量中的颜色
  const activeColor = props.barActiveColor ||
    getComputedStyle(document.documentElement).getPropertyValue('--vc-primary-light').trim() ||
    'hsl(224, 76%, 62%)'

  for (let i = 0; i < props.barCount; i++) {
    // 平滑目标值
    if (props.isActive) {
      const targetHeight = 0.1 + props.volume * (0.5 + 0.5 * Math.sin(Date.now() / 200 + i * 0.5))
      bars[i] += (targetHeight - bars[i]) * 0.15
    } else {
      // 不活跃时，柔和衰减到静息态
      const restHeight = 0.03 + 0.02 * Math.sin(Date.now() / 1000 + i * 0.3)
      bars[i] += (restHeight - bars[i]) * 0.08
    }

    const barHeight = Math.max(2, bars[i] * maxBarHeight)
    const x = i * (barWidth + gap)
    const y = centerY - barHeight / 2
    const radius = Math.min(barWidth / 2, 3)

    ctx.fillStyle = props.isActive ? activeColor : props.barColor

    // 绘制圆角矩形
    ctx.beginPath()
    ctx.roundRect(x, y, barWidth, barHeight, radius)
    ctx.fill()
  }

  animationFrame = requestAnimationFrame(draw)
}

onMounted(() => {
  initBars()
  draw()
})

onUnmounted(() => {
  cancelAnimationFrame(animationFrame)
})

watch(() => props.barCount, initBars)
</script>

<style scoped>
.waveform-visualizer {
  display: block;
  width: 100%;
  height: auto;
  max-height: 80px;
  opacity: 0.5;
  transition: opacity var(--vc-transition-base);
}

.waveform-visualizer--active {
  opacity: 1;
}
</style>
