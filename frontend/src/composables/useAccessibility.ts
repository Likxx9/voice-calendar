/* ============================================================
 * M1 组合式函数 — 无障碍手势控制
 * 全屏大范围手势 | 长按录音 | 双击打断 | 双指轻扫
 * ============================================================ */

import { ref, onMounted, onUnmounted } from 'vue'

export interface AccessibilityOptions {
  longPressThreshold?: number    // 长按判定阈值 ms，默认 400
  doubleTapThreshold?: number    // 双击判定间隔 ms，默认 300
  swipeThreshold?: number        // 滑动判定距离 px，默认 50
  onLongPressStart?: () => void   // 长按开始（录音开始）
  onLongPressEnd?: () => void     // 长按结束（录音结束）
  onDoubleTap?: () => void        // 双击（打断 TTS）
  onSwipeLeft?: () => void        // 左滑（下一条日程）
  onSwipeRight?: () => void       // 右滑（上一条日程）
}

export function useAccessibility(
  elementRef: { value: HTMLElement | null },
  options: AccessibilityOptions = {}
) {
  const {
    longPressThreshold = 400,
    doubleTapThreshold = 300,
    swipeThreshold = 50,
    onLongPressStart,
    onLongPressEnd,
    onDoubleTap,
    onSwipeLeft,
    onSwipeRight,
  } = options

  const isLongPressing = ref(false)
  const gestureActive = ref(false)

  let longPressTimer: ReturnType<typeof setTimeout> | null = null
  let lastTapTime = 0
  let touchStartX = 0
  let touchStartY = 0
  let touchFingers = 0

  function handleTouchStart(e: TouchEvent) {
    touchFingers = e.touches.length
    touchStartX = e.touches[0].clientX
    touchStartY = e.touches[0].clientY

    // 双击检测
    const now = Date.now()
    if (now - lastTapTime < doubleTapThreshold && touchFingers === 1) {
      e.preventDefault()
      onDoubleTap?.()
      lastTapTime = 0
      return
    }
    lastTapTime = now

    // 长按检测（单指）
    if (touchFingers === 1) {
      longPressTimer = setTimeout(() => {
        isLongPressing.value = true
        gestureActive.value = true
        onLongPressStart?.()
      }, longPressThreshold)
    }
  }

  function handleTouchMove() {
    // 如果正在长按录音，不处理滑动
    if (isLongPressing.value) return

    // 取消长按定时器（移动了手指）
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }
  }

  function handleTouchEnd(e: TouchEvent) {
    // 清除长按定时器
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }

    // 长按结束
    if (isLongPressing.value) {
      isLongPressing.value = false
      gestureActive.value = false
      onLongPressEnd?.()
      return
    }

    // 双指滑动检测
    if (touchFingers === 2 && e.changedTouches.length > 0) {
      const deltaX = e.changedTouches[0].clientX - touchStartX
      const deltaY = e.changedTouches[0].clientY - touchStartY

      if (Math.abs(deltaX) > swipeThreshold && Math.abs(deltaX) > Math.abs(deltaY)) {
        if (deltaX > 0) {
          onSwipeRight?.()
        } else {
          onSwipeLeft?.()
        }
      }
    }

    touchFingers = 0
  }

  function handleTouchCancel() {
    if (longPressTimer) {
      clearTimeout(longPressTimer)
      longPressTimer = null
    }
    if (isLongPressing.value) {
      isLongPressing.value = false
      gestureActive.value = false
      onLongPressEnd?.()
    }
    touchFingers = 0
  }

  onMounted(() => {
    const el = elementRef.value
    if (!el) return

    el.addEventListener('touchstart', handleTouchStart, { passive: false })
    el.addEventListener('touchmove', handleTouchMove, { passive: true })
    el.addEventListener('touchend', handleTouchEnd, { passive: true })
    el.addEventListener('touchcancel', handleTouchCancel, { passive: true })
  })

  onUnmounted(() => {
    const el = elementRef.value
    if (!el) return

    el.removeEventListener('touchstart', handleTouchStart)
    el.removeEventListener('touchmove', handleTouchMove)
    el.removeEventListener('touchend', handleTouchEnd)
    el.removeEventListener('touchcancel', handleTouchCancel)
  })

  return {
    isLongPressing,
    gestureActive,
  }
}
