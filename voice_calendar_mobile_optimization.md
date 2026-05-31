# 语音日历 — 移动端页面优化方案

> **VoiCal Mobile Optimization Plan**
> 基准文档：前端页面开发文档 v1.0（桌面端）
> 优化版本：v2.0 · 移动端优先
> 目标设备：iOS 16+ · Android 12+（375px ~ 430px 主流机型）

---

## 目录

1. [现有设计问题诊断](#1-现有设计问题诊断)
2. [移动端设计核心原则](#2-移动端设计核心原则)
3. [整体布局架构重构](#3-整体布局架构重构)
4. [Design Tokens 移动端覆盖](#4-design-tokens-移动端覆盖)
5. [字体规范更新](#5-字体规范更新)
6. [模块改造规范](#6-模块改造规范)
   - 6.1 [顶部导航栏（精简版）](#61-顶部导航栏精简版)
   - 6.2 [日历视图（日视图 + 三日视图）](#62-日历视图日视图--三日视图)
   - 6.3 [悬浮语音按钮 FAB](#63-悬浮语音按钮-fab)
   - 6.4 [语音全屏交互界面](#64-语音全屏交互界面)
   - 6.5 [今日日程卡片流](#65-今日日程卡片流)
   - 6.6 [事件详情底部面板（Bottom Sheet）](#66-事件详情底部面板bottom-sheet)
   - 6.7 [底部标签栏（Tab Bar）](#67-底部标签栏tab-bar)
   - 6.8 [智能建议横向滚动条](#68-智能建议横向滚动条)
7. [触控交互规范](#7-触控交互规范)
8. [手势导航设计](#8-手势导航设计)
9. [动画规范更新](#9-动画规范更新)
10. [PWA 与性能优化](#10-pwa-与性能优化)
11. [桌面 → 移动改动对照表](#11-桌面--移动改动对照表)
12. [实现优先级与里程碑](#12-实现优先级与里程碑)

---

## 1. 现有设计问题诊断

### 1.1 布局层面问题

| 问题 | 原设计 | 移动端影响 | 严重程度 |
|------|-------|-----------|---------|
| 三栏固定宽度 | `220px + flex-1 + 308px` | 最窄 528px，超出所有手机屏宽 | 🔴 致命 |
| 侧边栏占位 | 固定 220px | 完全挤占内容区 | 🔴 致命 |
| 周视图 7 列 | `repeat(7, 1fr)` | 每列约 18px，事件文字完全不可读 | 🔴 致命 |
| 右侧语音面板 | 固定 308px 右侧栏 | 无法访问，被挤出屏幕 | 🔴 致命 |
| 弹窗居中 Modal | `width: 340px` | 需要适配安全区域、键盘遮挡 | 🟠 严重 |
| overflow:hidden | 根节点禁止滚动 | 手机无法通过双指缩放调整 | 🟠 严重 |

### 1.2 交互层面问题

| 问题 | 原设计 | 移动端影响 | 严重程度 |
|------|-------|-----------|---------|
| 依赖 `:hover` 状态 | 所有悬停效果 | 触摸设备无悬停，交互反馈缺失 | 🟠 严重 |
| 触摸目标过小 | 导航项 `padding: 8px` | 低于 44×44px 最小触摸目标 | 🟠 严重 |
| 字号过小 | Body 13px, Small 10px | 移动端最小可读字号 14px | 🟡 中等 |
| 无手势支持 | 仅按钮导航 | 缺少左右滑切日期等核心手势 | 🟡 中等 |
| 时间列宽 52px | `grid: 52px repeat(7...)` | 移动端浪费宝贵横向空间 | 🟡 中等 |
| 快捷指令竖排 | 3 个竖向按钮 | 占用过多纵向空间 | 🟡 中等 |

### 1.3 性能层面问题

| 问题 | 影响 | 建议 |
|------|------|------|
| 3 种 Google Fonts 全量加载 | 阻塞渲染，弱网卡顿 | 按需加载，添加 `font-display: swap` |
| 676px 高度时间格一次全渲染 | 首屏性能下降 | 虚拟滚动或只渲染可视区 |
| 背景网格 `body::before` CSS | 移动端低端机额外合成层 | 仅桌面端开启 |
| 无 PWA 支持 | 商务人士无法主屏添加 | 添加 Manifest + Service Worker |

---

## 2. 移动端设计核心原则

### 2.1 拇指热区理论（Thumb Zone）

```
手机屏幕拇指可达区域分析（右手单手持机）：

  ┌──────────────┐
  │ ╳ 难以触达    │  顶部区域：系统状态栏 + 最高交互内容
  │              │
  │ △ 可以触达    │  中部区域：日历主视图（浏览为主）
  │              │
  │ ✓ 最易触达    │  底部区域：Tab 栏 + FAB（核心操作）
  └──────────────┘

原则：
  - 语音 FAB → 底部右侧（最易触达）
  - Tab 导航 → 底部固定（拇指热区）
  - 日期导航 → 支持左右滑动（替代顶部按钮）
  - 危险操作（删除）→ 需二次确认，避免误触
```

### 2.2 四大设计准则

**① 单手可操作**：所有核心功能可单手完成，无需双手或切换握持方式。

**② 语音优先**：语音是移动端最高效的输入方式，FAB 在所有页面常驻，一键即达。

**③ 信息密度适配**：移动端一屏展示 3-5 条日程，不追求信息密度，追求可读性。

**④ 系统原生体验**：底部面板、触觉反馈、安全区域、深色模式均跟随系统原生规范。

---

## 3. 整体布局架构重构

### 3.1 桌面 → 移动布局对比

```
【桌面端（原设计）】
┌────────┬──────────────────┬──────────┐
│Sidebar │  Week Calendar   │  Voice   │
│ 220px  │     flex-1       │  308px   │
└────────┴──────────────────┴──────────┘

【移动端（新设计）】
┌─────────────────────────────────┐
│  Top Header（48px）             │  ← 极简化，仅保留日期 + 设置
├─────────────────────────────────┤
│                                 │
│  Calendar / Today / Tasks       │  ← 主内容区，占满可用高度
│  （随 Tab 切换内容）               │
│                                 │
│                         ⊕ FAB  │  ← 语音 FAB，固定右下角
├─────────────────────────────────┤
│  🗓 今日  📋 日程  🎙 语音  ✓ 任务  👤  │  ← Bottom Tab Bar（56px）
└─────────────────────────────────┘
│           系统安全区域             │  ← iOS Home Indicator 等
```

### 3.2 CSS 布局核心结构

```css
/* ── 移动端根布局 ── */
.app-mobile {
  display: flex;
  flex-direction: column;
  height: 100dvh;              /* dvh: 动态视口高度，处理键盘弹出 */
  overflow: hidden;
  background: var(--bg);
}

/* ── 内容区（Header 和 TabBar 之间） ── */
.mobile-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  -webkit-overflow-scrolling: touch;  /* iOS 惯性滚动 */
  overscroll-behavior-y: contain;     /* 防止触发系统级下拉刷新 */
}

/* ── 底部安全区域适配 ── */
.tab-bar {
  padding-bottom: env(safe-area-inset-bottom);
  padding-bottom: constant(safe-area-inset-bottom);  /* iOS 11 兼容 */
}

/* ── 顶部安全区域 ── */
.top-header {
  padding-top: env(safe-area-inset-top);
}
```

### 3.3 五大页面切换

```
Tab 1 ── 今日（Today）
  今日日期大标题
  今日日程卡片流（时间线）
  AI 智能建议横向滑动卡片

Tab 2 ── 日程（Calendar）
  日视图 / 三日视图 / 周视图（可切换）
  横向滑动切换日期

Tab 3 ── 语音（Voice）——中间 Tab，突出强调
  语音指令全屏界面
  Agent 日志
  快捷指令

Tab 4 ── 任务（Tasks）
  任务清单（按优先级分组）
  完成打勾

Tab 5 ── 我的（Profile）
  用户信息
  日历同步设置
  通知偏好
```

---

## 4. Design Tokens 移动端覆盖

在原有 `:root` 变量基础上，通过媒体查询覆盖移动端专用值：

```css
/* 继承桌面端 :root 所有变量 */
/* 以下仅列出需要覆盖的差异项 */

@media (max-width: 767px) {
  :root {
    /* ── 触摸目标最小尺寸 ── */
    --touch-target:  44px;        /* iOS HIG 和 Material 规范最小值 */
    --touch-target-l: 56px;       /* 大型主操作（FAB、主按钮） */

    /* ── 间距系统（移动端增大 20%）── */
    --sp-xs:  6px;                /* 桌面: 4px */
    --sp-sm:  10px;               /* 桌面: 8px */
    --sp-md:  16px;               /* 桌面: 12px */
    --sp-lg:  24px;               /* 桌面: 20px */
    --sp-xl:  32px;               /* 桌面: 28px */

    /* ── 圆角（移动端更大，更现代）── */
    --r:     12px;                /* 桌面: 9px */
    --r-lg:  20px;                /* 卡片、Bottom Sheet 顶角 */
    --r-xl:  28px;                /* FAB、大按钮 */
    --r-pill: 999px;              /* 胶囊形按钮 */

    /* ── FAB 专用 ── */
    --fab-size:   56px;
    --fab-bottom: 80px;           /* Tab Bar 高度（56px）+ 间距（24px） */
    --fab-right:  20px;

    /* ── Bottom Sheet ── */
    --sheet-radius:    24px;
    --sheet-handle-w:  40px;
    --sheet-handle-h:  4px;

    /* ── Tab Bar ── */
    --tab-height:   56px;
    --tab-icon-sz:  24px;
    --tab-label-sz: 10px;

    /* ── 日历参数（移动端）── */
    --cal-hour-h:    48px;        /* 桌面: 52px，移动端略压缩 */
    --cal-time-col:  36px;        /* 桌面: 52px，移动端缩小时间列 */
  }
}
```

---

## 5. 字体规范更新

### 5.1 字体加载优化

```html
<!-- 移动端精简字体加载：减少字重变体，添加 font-display: swap -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?
  family=Outfit:wght@400;500;600
  &family=JetBrains+Mono:wght@400
  &display=swap">
<!-- 移动端删除 Cormorant Garamond（衬线字体在小屏渲染差）→ 使用系统字体替代 -->
```

### 5.2 移动端字号规范（全面上调）

| 层级 | 桌面字号 | 移动字号 | 字重 | 用途 |
|------|---------|---------|------|------|
| Display | 24px | 28px | 600 | 页面大标题、今日日期 |
| H1 | 22-23px | 20px | 600 | 段落标题 |
| H2 | 22px | 18px | 500 | 日期数字（改用 Outfit） |
| Body | 13px | **15px** | 400 | 事件标题、描述 |
| Small | 11-11.5px | **13px** | 400 | 时间标签、地点 |
| Micro | 9-10px | **11px** | 500 | 标签、徽章文字 |
| Mono | 10px | **12px** | 400 | 时间列、Agent 日志 |

> **移动端最小字号规则**：任何用户需要阅读的文字不得小于 11px。

### 5.3 行高规范

```css
/* 移动端行高增大，提升阅读舒适度 */
@media (max-width: 767px) {
  body         { line-height: 1.6; }
  .ev-title    { line-height: 1.4; }
  .brief-title { line-height: 1.5; }
  .agent-log   { line-height: 1.8; }
}
```

---

## 6. 模块改造规范

### 6.1 顶部导航栏（精简版）

**原设计**：三段式，含日期导航、视图切换、Agent 徽章、日期显示、头像，总宽度 ~600px。

**移动端改造**：精简为两端对齐，高度 48px，仅保留最核心的上下文信息。

```
移动端 Header 布局：

┌─────────────────────────────────────────┐
│  ≡  │  2026年5月30日  周六   │  ⚙ │ 👤 │
│菜单  │    （今日标识高亮）      │设置│头像 │
└─────────────────────────────────────────┘
   40px        flex-1                40px 40px
```

```css
/* 移动端顶部导航栏 */
.mobile-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 48px;
  padding: 0 var(--sp-md);
  padding-top: env(safe-area-inset-top);
  background: rgba(7,9,15,.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
}

.mobile-header-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--text);
  font-family: var(--fu);
  letter-spacing: 0.02em;
}

.mobile-header-date-today {
  color: var(--gold);                 /* 今日高亮金色 */
}

/* 头部操作按钮（右侧） */
.mobile-header-btn {
  width: var(--touch-target);
  height: var(--touch-target);
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: var(--text2);
  cursor: pointer;
  /* 触摸反馈：按下时缩小 */
  transition: transform 0.1s ease, background 0.15s ease;
  -webkit-tap-highlight-color: transparent;
}

.mobile-header-btn:active {
  transform: scale(0.88);
  background: var(--bg-hover);
}
```

**视图切换**：从 Header 下移至日历区顶部，以横向 Segment Control 形式呈现：

```css
/* 日视图 / 三日视图 / 周视图 切换器 */
.view-segment {
  display: flex;
  background: var(--bg2);
  border-radius: var(--r-pill);
  padding: 3px;
  gap: 2px;
  margin: var(--sp-sm) var(--sp-md);
  border: 1px solid var(--border);
}

.view-seg-btn {
  flex: 1;
  height: 32px;
  border-radius: var(--r-pill);
  font-size: 13px;
  font-weight: 500;
  color: var(--text2);
  background: none;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.view-seg-btn.active {
  background: var(--gold-dim);
  color: var(--gold);
  font-weight: 600;
}
```

---

### 6.2 日历视图（日视图 + 三日视图）

**原设计**：周视图（7列）固定，时间列 52px，事件块平铺。

**移动端核心改造**：默认切换为**日视图**，支持左右滑动切换日期，采用更大触摸目标。

#### 6.2.1 日视图布局

```css
/* 移动端日视图 Grid：时间列 + 1 列内容 */
.cal-grid-mobile {
  display: grid;
  grid-template-columns: var(--cal-time-col) 1fr;  /* 36px + 全宽 */
  position: relative;
}

/* 时间标签（缩小） */
.mobile-time-label {
  height: var(--cal-hour-h);           /* 48px */
  font-size: 11px;
  font-family: var(--fm);
  color: var(--text3);
  text-align: right;
  padding-right: 8px;
  padding-top: 4px;
  letter-spacing: 0.04em;
}

/* 事件块（移动端加高最小高度，避免过小无法点击）*/
.ev-mobile {
  position: absolute;
  left: 6px;
  right: 6px;
  border-radius: 8px;
  padding: 6px 10px;
  cursor: pointer;
  border-left: 3px solid transparent;
  min-height: var(--touch-target);     /* 最小 44px，保证可点击 */
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.12s ease, filter 0.12s ease;
}

/* 点击反馈（替代 hover） */
.ev-mobile:active {
  transform: scale(0.97);
  filter: brightness(1.15);
}

/* 事件标题（移动端加大字号）*/
.ev-mobile .ev-title {
  font-size: 13px;                     /* 桌面 11px → 移动 13px */
  font-weight: 600;
  line-height: 1.3;
  /* 最多显示 2 行，超出省略 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.ev-mobile .ev-time {
  font-size: 11px;
  font-family: var(--fm);
  opacity: 0.75;
  margin-top: 3px;
}
```

#### 6.2.2 日期横向滑动导航

```css
/* 日期栏（周内7天横排，当前日高亮，左右可滑动） */
.date-strip {
  display: flex;
  overflow-x: auto;
  scrollbar-width: none;             /* 隐藏滚动条 */
  -ms-overflow-style: none;
  scroll-snap-type: x mandatory;    /* 滑动锁定 */
  padding: var(--sp-sm) var(--sp-md);
  gap: var(--sp-xs);
  border-bottom: 1px solid var(--border);
}

.date-strip::-webkit-scrollbar { display: none; }

.date-pill {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 60px;
  border-radius: 14px;
  cursor: pointer;
  scroll-snap-align: center;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
}

.date-pill-day {                      /* "一" "二" */
  font-size: 10px;
  color: var(--text2);
  font-weight: 500;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.date-pill-num {                      /* "25" "26" */
  font-size: 18px;
  font-weight: 300;
  color: var(--text);
  font-family: var(--fu);
  line-height: 1;
}

.date-pill.today {
  background: var(--gold);
}

.date-pill.today .date-pill-day,
.date-pill.today .date-pill-num {
  color: #000;
  font-weight: 700;
}

.date-pill.selected:not(.today) {
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
}

.date-pill.selected:not(.today) .date-pill-num {
  color: var(--gold);
}

/* 有事件指示点 */
.date-pill-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--gold);
  margin-top: 4px;
  opacity: 0.7;
}

.date-pill.today .date-pill-dot {
  background: #000;
  opacity: 0.5;
}
```

#### 6.2.3 日历主视图手势区域

```javascript
// 左右滑动切换日期（Touch 事件处理）
class CalendarSwipeHandler {
  constructor(container, onSwipe) {
    this.container = container;
    this.onSwipe   = onSwipe;
    this.startX    = 0;
    this.startY    = 0;
    this.threshold = 50;          // 触发滑动的最小位移（px）
    this.bind();
  }

  bind() {
    this.container.addEventListener('touchstart', this.onStart.bind(this),
      { passive: true });
    this.container.addEventListener('touchend', this.onEnd.bind(this),
      { passive: true });
  }

  onStart(e) {
    this.startX = e.touches[0].clientX;
    this.startY = e.touches[0].clientY;
  }

  onEnd(e) {
    const dx = e.changedTouches[0].clientX - this.startX;
    const dy = e.changedTouches[0].clientY - this.startY;

    // 水平滑动距离大于垂直 → 切换日期
    if (Math.abs(dx) > Math.abs(dy) && Math.abs(dx) > this.threshold) {
      this.onSwipe(dx < 0 ? 'next' : 'prev');
    }
  }
}

// 使用示例
const swipe = new CalendarSwipeHandler(
  document.getElementById('cal-content'),
  (dir) => shiftDay(dir === 'next' ? 1 : -1)
);
```

---

### 6.3 悬浮语音按钮 FAB

语音是产品核心功能，FAB 在**所有 Tab 页**常驻，确保随时可触达。

```css
/* ── 语音 FAB ── */
.voice-fab {
  position: fixed;
  bottom: var(--fab-bottom);        /* Tab Bar 上方 24px */
  right: var(--fab-right);          /* 右侧 20px */
  width: var(--fab-size);           /* 56px */
  height: var(--fab-size);
  border-radius: 50%;
  background: linear-gradient(135deg, var(--gold), #9B6B1A);
  border: none;
  cursor: pointer;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #000;
  box-shadow:
    0 4px 16px rgba(200,164,90,.35),
    0 2px 6px rgba(0,0,0,.4);
  -webkit-tap-highlight-color: transparent;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.voice-fab:active {
  transform: scale(0.92);
  box-shadow:
    0 2px 8px rgba(200,164,90,.25),
    0 1px 3px rgba(0,0,0,.4);
}

/* 聆听中状态：金色呼吸光晕 */
.voice-fab.listening {
  animation: fabGlow 1.1s ease-in-out infinite;
}

@keyframes fabGlow {
  0%, 100% { box-shadow: 0 4px 16px rgba(200,164,90,.4), 0 0 0 0 rgba(200,164,90,.3); }
  50%       { box-shadow: 0 4px 24px rgba(200,164,90,.6), 0 0 0 14px rgba(200,164,90,0); }
}

/* 处理中：蓝色脉冲 */
.voice-fab.processing {
  background: linear-gradient(135deg, var(--blue), #1a4a99);
  animation: fabProcessing 0.8s ease-in-out infinite;
}

@keyframes fabProcessing {
  0%, 100% { transform: scale(1); }
  50%       { transform: scale(1.05); }
}

/* 完成：绿色 ✓ 短暂显示 */
.voice-fab.done {
  background: linear-gradient(135deg, var(--teal), #1a6b5f);
}
```

---

### 6.4 语音全屏交互界面

点击 FAB 后弹出全屏语音交互界面（覆盖整个屏幕），取代原右侧面板设计。

```css
/* ── 语音全屏页面 ── */
.voice-fullscreen {
  position: fixed;
  inset: 0;
  background: radial-gradient(ellipse at 50% 60%, rgba(200,164,90,.06), var(--bg) 70%);
  backdrop-filter: blur(0);
  z-index: 300;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom);
  animation: voiceSlideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1);
}

@keyframes voiceSlideUp {
  from { transform: translateY(100%); opacity: 0.5; }
  to   { transform: translateY(0);    opacity: 1; }
}

/* 顶部关闭区 */
.voice-close-bar {
  width: 100%;
  padding: 16px var(--sp-md);
  display: flex;
  justify-content: flex-end;
}

.voice-close-btn {
  width: var(--touch-target);
  height: var(--touch-target);
  border-radius: 50%;
  background: var(--bg2);
  border: 1px solid var(--border);
  color: var(--text2);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

/* 中央麦克风区域 */
.voice-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 0 var(--sp-lg);
}

/* 大型麦克风按钮（移动端放大至 88px）*/
.voice-mic-main {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  background: var(--gold-dim);
  border: 2px solid var(--gold-border);
  font-size: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  cursor: pointer;
  transition: all 0.2s ease;
}

/* 波纹圈（聆听状态）*/
.voice-ripple-ring {
  position: absolute;
  inset: -16px;
  border-radius: 50%;
  border: 2px solid var(--gold);
  opacity: 0;
  animation: mobileRipple 2s ease-out infinite;
}

.voice-ripple-ring:nth-child(2) { animation-delay: 0.6s; }
.voice-ripple-ring:nth-child(3) { animation-delay: 1.2s; }

@keyframes mobileRipple {
  0%   { transform: scale(0.85); opacity: 0.6; }
  100% { transform: scale(1.6);  opacity: 0; }
}

/* 语音波形（大版本）*/
.voice-waveform-mobile {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  height: 44px;
}

.wb-mobile {
  width: 4px;
  border-radius: 3px;
  background: var(--gold);
  transform-origin: bottom;
  transition: height 0.2s ease;
}

/* 识别文字气泡 */
.voice-query-bubble {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: var(--sp-md) var(--sp-lg);
  font-size: 15px;
  color: var(--text);
  font-style: italic;
  line-height: 1.5;
  max-width: 100%;
  text-align: center;
  animation: fadeUp 0.3s ease;
}

/* Agent 日志（移动端紧凑版）*/
.voice-log-mobile {
  width: 100%;
  background: rgba(0,0,0,.45);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: var(--sp-sm);
  max-height: 150px;
  overflow-y: auto;
  font-family: var(--fm);
  font-size: 11px;
  line-height: 1.8;
}

/* 快捷指令（横向滑动胶囊）*/
.quick-chips {
  display: flex;
  gap: var(--sp-sm);
  overflow-x: auto;
  scrollbar-width: none;
  padding: 0 var(--sp-md) var(--sp-md);
  width: 100%;
}

.quick-chips::-webkit-scrollbar { display: none; }

.chip {
  flex-shrink: 0;
  padding: 9px 16px;
  border-radius: var(--r-pill);
  border: 1px solid var(--border);
  background: var(--bg2);
  font-size: 13px;
  color: var(--text2);
  cursor: pointer;
  white-space: nowrap;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.15s ease;
}

.chip:active {
  border-color: var(--gold);
  color: var(--gold);
  background: var(--gold-dim);
  transform: scale(0.97);
}
```

---

### 6.5 今日日程卡片流

**原设计**：右侧面板内的小字列表，字号 10px，行高 9px。

**移动端改造**：独立的「今日」Tab，以卡片流形式呈现，每张卡片可轻松点击。

```css
/* ── 今日 Tab 页 ── */
.today-page {
  padding: var(--sp-md);
  padding-bottom: calc(var(--tab-height) + env(safe-area-inset-bottom) + var(--sp-xl));
}

/* 今日大日期标题 */
.today-hero {
  margin-bottom: var(--sp-lg);
}

.today-date-big {
  font-size: 40px;
  font-weight: 300;
  color: var(--gold);
  font-family: var(--fu);
  line-height: 1;
}

.today-weekday {
  font-size: 16px;
  color: var(--text2);
  font-weight: 400;
  margin-top: 4px;
}

.today-summary {
  font-size: 13px;
  color: var(--text2);
  margin-top: 8px;
}

/* 时间线容器 */
.timeline {
  position: relative;
  padding-left: 20px;
}

/* 时间线竖线 */
.timeline::before {
  content: '';
  position: absolute;
  left: 6px;
  top: 0;
  bottom: 0;
  width: 1px;
  background: linear-gradient(to bottom, var(--border), transparent);
}

/* 日程卡片 */
.agenda-card {
  position: relative;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: var(--sp-md);
  margin-bottom: var(--sp-sm);
  cursor: pointer;
  transition: all 0.2s ease;
  -webkit-tap-highlight-color: transparent;
  /* 左侧色块 */
  border-left-width: 3px;
}

.agenda-card:active {
  transform: scale(0.98);
  background: var(--bg-hover);
}

/* 时间线圆点 */
.timeline-dot {
  position: absolute;
  left: -23px;
  top: 50%;
  transform: translateY(-50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--bg);
}

/* 卡片内容 */
.ac-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--sp-sm);
  margin-bottom: 6px;
}

.ac-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
  flex: 1;
}

.ac-time-tag {
  font-size: 11px;
  font-family: var(--fm);
  color: var(--text2);
  white-space: nowrap;
  background: var(--bg3);
  padding: 2px 8px;
  border-radius: var(--r-pill);
}

.ac-meta {
  display: flex;
  align-items: center;
  gap: var(--sp-sm);
  font-size: 12px;
  color: var(--text2);
}

.ac-location {
  display: flex;
  align-items: center;
  gap: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ac-attendees {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

/* 当前进行中事件：金色边框 + 脉冲 */
.agenda-card.ongoing {
  border-left-color: var(--gold) !important;
  animation: cardPulse 2.5s ease-in-out infinite;
}

@keyframes cardPulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(200,164,90,0); }
  50%       { box-shadow: 0 0 0 3px rgba(200,164,90,.12); }
}
```

---

### 6.6 事件详情底部面板（Bottom Sheet）

**原设计**：居中 Modal（340px 宽），`fadeUp` 动画。

**移动端改造**：改为从底部上滑的 Bottom Sheet，更符合移动端习惯，支持下拉关闭。

```css
/* ── Bottom Sheet 遮罩 ── */
.sheet-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.6);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 200;
  animation: overlayIn 0.3s ease;
}

@keyframes overlayIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* ── Bottom Sheet 主体 ── */
.bottom-sheet {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg2);
  border-radius: var(--r-lg) var(--r-lg) 0 0;
  z-index: 201;
  padding-bottom: env(safe-area-inset-bottom);
  max-height: 85vh;
  overflow-y: auto;
  animation: sheetSlideUp 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  /* 顶部金色描边 */
  border-top: 1px solid var(--gold-border);
  box-shadow: 0 -8px 40px rgba(0,0,0,.5);
}

@keyframes sheetSlideUp {
  from { transform: translateY(100%); }
  to   { transform: translateY(0); }
}

/* 下拉把手 */
.sheet-handle {
  width: var(--sheet-handle-w);
  height: var(--sheet-handle-h);
  border-radius: 2px;
  background: var(--text3);
  margin: 14px auto 0;
}

/* 事件标题区 */
.sheet-header {
  padding: var(--sp-lg) var(--sp-lg) var(--sp-md);
  border-bottom: 1px solid var(--border);
}

.sheet-event-color-bar {
  width: 32px;
  height: 4px;
  border-radius: 2px;
  margin-bottom: var(--sp-sm);
}

.sheet-event-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--text);
  line-height: 1.3;
  font-family: var(--fu);
}

/* 详情行 */
.sheet-body {
  padding: var(--sp-md) var(--sp-lg);
}

.sheet-detail-row {
  display: flex;
  align-items: center;
  gap: var(--sp-md);
  padding: 12px 0;
  border-bottom: 1px solid var(--border);
  min-height: var(--touch-target);
}

.sheet-detail-row:last-child { border-bottom: none; }

.sheet-detail-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: var(--bg3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.sheet-detail-content {}

.sheet-detail-label {
  font-size: 11px;
  color: var(--text2);
  margin-bottom: 2px;
  letter-spacing: 0.04em;
}

.sheet-detail-value {
  font-size: 15px;
  color: var(--text);
  font-weight: 500;
}

/* 操作按钮行 */
.sheet-actions {
  display: flex;
  gap: var(--sp-sm);
  padding: var(--sp-md) var(--sp-lg);
  padding-bottom: var(--sp-lg);
}

.sheet-btn {
  flex: 1;
  height: var(--touch-target);
  border-radius: var(--r);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  -webkit-tap-highlight-color: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.sheet-btn-primary {
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
  color: var(--gold);
}

.sheet-btn-danger {
  background: rgba(248,113,113,.1);
  border: 1px solid rgba(248,113,113,.2);
  color: var(--red);
}

.sheet-btn:active { transform: scale(0.96); }
```

**下拉关闭手势实现**：

```javascript
// Bottom Sheet 下拉关闭
class BottomSheetController {
  constructor(sheet, overlay, onClose) {
    this.sheet   = sheet;
    this.overlay = overlay;
    this.onClose = onClose;
    this.startY  = 0;
    this.currentY = 0;
    this.isDragging = false;

    this.sheet.addEventListener('touchstart', this.onStart.bind(this), { passive: true });
    this.sheet.addEventListener('touchmove',  this.onMove.bind(this),  { passive: false });
    this.sheet.addEventListener('touchend',   this.onEnd.bind(this),   { passive: true });
    this.overlay.addEventListener('click', onClose);
  }

  onStart(e) {
    this.startY     = e.touches[0].clientY;
    this.isDragging = true;
    this.sheet.style.transition = 'none';
  }

  onMove(e) {
    if (!this.isDragging) return;
    const dy = e.touches[0].clientY - this.startY;
    if (dy > 0) {
      e.preventDefault();           // 阻止页面滚动
      this.currentY = dy;
      this.sheet.style.transform = `translateY(${dy}px)`;
      // 背景随拖动渐隐
      const opacity = 1 - dy / 300;
      this.overlay.style.opacity = Math.max(opacity, 0).toString();
    }
  }

  onEnd() {
    this.isDragging = false;
    this.sheet.style.transition = 'transform 0.3s cubic-bezier(0.32, 0.72, 0, 1)';

    if (this.currentY > 120) {
      // 拖动超过 120px → 关闭
      this.sheet.style.transform = 'translateY(100%)';
      setTimeout(this.onClose, 300);
    } else {
      // 回弹
      this.sheet.style.transform = 'translateY(0)';
      this.overlay.style.opacity = '1';
    }
    this.currentY = 0;
  }
}
```

---

### 6.7 底部标签栏（Tab Bar）

```css
/* ── Tab Bar ── */
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: calc(var(--tab-height) + env(safe-area-inset-bottom));
  background: rgba(7,9,15,.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid var(--border);
  display: flex;
  align-items: flex-start;
  padding-top: 8px;
  z-index: 100;
}

/* Tab 按钮 */
.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: var(--tab-height);
  cursor: pointer;
  color: var(--text2);
  transition: color 0.2s ease;
  -webkit-tap-highlight-color: transparent;
  position: relative;
}

/* 图标容器（放大触摸区域）*/
.tab-icon-wrap {
  width: 44px;
  height: 32px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--tab-icon-sz);
  transition: background 0.2s ease, transform 0.15s ease;
}

.tab-label {
  font-size: var(--tab-label-sz);
  font-weight: 500;
  letter-spacing: 0.04em;
}

/* 激活态 */
.tab-item.active { color: var(--gold); }
.tab-item.active .tab-icon-wrap {
  background: var(--gold-dim);
  transform: scale(1.05);
}

/* 中间语音 Tab 特殊处理（无文字标签，突出图标）*/
.tab-item.voice-tab .tab-icon-wrap {
  width: 50px;
  height: 34px;
  background: var(--gold-dim);
  border: 1px solid var(--gold-border);
}

.tab-item.voice-tab.active .tab-icon-wrap {
  background: linear-gradient(135deg, rgba(200,164,90,.3), rgba(200,164,90,.15));
  border-color: var(--gold);
}

/* 按下反馈 */
.tab-item:active .tab-icon-wrap {
  transform: scale(0.9);
  background: var(--bg2);
}

/* 消息徽章 */
.tab-badge {
  position: absolute;
  top: 4px;
  right: calc(50% - 22px + 2px);
  min-width: 16px;
  height: 16px;
  border-radius: 8px;
  background: var(--red);
  color: #fff;
  font-size: 9px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  border: 1.5px solid var(--bg);
  animation: newBadge 0.3s ease;
}
```

---

### 6.8 智能建议横向滚动条

**原设计**：纵向卡片列表，需要大量垂直空间。

**移动端改造**：横向滑动卡片组，紧凑高效。

```css
/* ── AI 智能建议横向滑动 ── */
.suggestions-scroll {
  display: flex;
  gap: var(--sp-sm);
  overflow-x: auto;
  scrollbar-width: none;
  padding: var(--sp-sm) var(--sp-md);
  scroll-snap-type: x mandatory;
  /* 左右留出边距显示"还有更多" */
  padding-right: calc(var(--sp-md) + 30px);
}

.suggestions-scroll::-webkit-scrollbar { display: none; }

.sug-card-mobile {
  flex-shrink: 0;
  width: 240px;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: var(--r);
  padding: var(--sp-md);
  cursor: pointer;
  scroll-snap-align: start;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.2s ease;
}

.sug-card-mobile:active {
  transform: scale(0.97);
  border-color: var(--gold-border);
}

.sug-icon { font-size: 20px; margin-bottom: var(--sp-sm); }

.sug-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 4px;
  line-height: 1.3;
}

.sug-desc {
  font-size: 12px;
  color: var(--text2);
  line-height: 1.5;
  /* 最多 2 行 */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

---

## 7. 触控交互规范

### 7.1 触摸目标尺寸规则

所有可交互元素必须满足最小触摸目标要求：

| 类型 | 最小尺寸 | 实现方式 |
|------|---------|---------|
| 文字链接 | 44×44px | `padding` 扩展点击区域 |
| 图标按钮 | 44×44px | 外层 `div` 设定尺寸 |
| 表单控件 | 44px 高 | `height: 44px` |
| 列表行 | 48px 高 | `min-height: 48px` |
| FAB 主按钮 | 56×56px | 直接设定 |
| Tab 按钮 | 全宽 × 56px | 均分宽度 |

```css
/* 触摸目标扩展通用工具类 */
.touch-target {
  position: relative;
}

.touch-target::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  min-width: 44px;
  min-height: 44px;
}
```

### 7.2 触摸反馈规范

移动端禁用所有 `:hover` 效果，改为 `:active` + `transform` 反馈：

```css
/* 全局触摸反馈：替代 hover */
@media (hover: none) {
  /* 禁用所有 hover 效果 */
  .nav-item:hover,
  .sug:hover,
  .brief-item:hover,
  .ev:hover,
  .chip:hover {
    /* 重置 hover 样式 */
    background: unset;
    color: unset;
    transform: unset;
    filter: unset;
  }

  /* 统一触摸按下反馈 */
  .interactive:active {
    opacity: 0.75;
    transform: scale(0.97);
    transition: transform 0.1s ease, opacity 0.1s ease;
  }
}

/* 移除 iOS 点击高亮 */
* {
  -webkit-tap-highlight-color: transparent;
  -webkit-touch-callout: none;          /* 禁止长按弹出菜单（图片等）*/
}

/* 但保留文字选择（用于日程标题等）*/
.selectable-text {
  -webkit-user-select: text;
  user-select: text;
}
```

### 7.3 触觉反馈（Haptic）

```javascript
// 关键操作触发触觉反馈（iOS 支持，Android 部分支持）
const haptic = {
  light()    { navigator.vibrate?.(5);  },     // 轻触
  medium()   { navigator.vibrate?.(15); },     // 中等
  heavy()    { navigator.vibrate?.(30); },     // 重击
  success()  { navigator.vibrate?.([10, 30, 10]); },  // 成功
  error()    { navigator.vibrate?.([50, 30, 50]); },  // 错误
};

// 使用场景
voiceFab.addEventListener('touchstart', () => haptic.medium());
confirmBtn.addEventListener('click',    () => haptic.success());
deleteBtn.addEventListener('click',     () => haptic.heavy());
```

---

## 8. 手势导航设计

### 8.1 手势总览

| 手势 | 区域 | 触发效果 |
|------|------|---------|
| 左滑 | 日历主视图 | 前进到下一天/周 |
| 右滑 | 日历主视图 | 返回上一天/周 |
| 下拉（日历顶部）| 日历主视图 | 刷新同步外部日历 |
| 上滑（Bottom Sheet）| Bottom Sheet | 展开为完整视图 |
| 下拉（Bottom Sheet）| Bottom Sheet | 关闭 Bottom Sheet |
| 长按事件块 | 日历事件 | 进入快速编辑模式 |
| 左滑事件行 | 今日日程列表 | 显示快捷操作（完成/删除）|
| 右滑事件行 | 今日日程列表 | 快速标记完成 |

### 8.2 列表左滑快捷操作

```css
/* 列表项左滑露出操作按钮 */
.swipeable-row {
  position: relative;
  overflow: hidden;
}

.swipe-content {
  position: relative;
  z-index: 1;
  background: var(--bg2);
  transition: transform 0.2s ease;
  will-change: transform;
}

/* 后层操作区 */
.swipe-actions {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  display: flex;
  z-index: 0;
}

.swipe-action-btn {
  width: 72px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
}

.swipe-action-delete {
  background: var(--red);
  color: #fff;
}

.swipe-action-done {
  background: var(--teal);
  color: #fff;
}
```

```javascript
// 列表行左滑逻辑
class SwipeableRow {
  constructor(el, actions) {
    this.el         = el;
    this.content    = el.querySelector('.swipe-content');
    this.actionsEl  = el.querySelector('.swipe-actions');
    this.actions    = actions;
    this.maxSwipe   = actions.reduce((sum, a) => sum + a.width, 0);
    this.currentX   = 0;
    this.startX     = 0;
    this.bind();
  }

  bind() {
    this.content.addEventListener('touchstart', (e) => {
      this.startX = e.touches[0].clientX;
      this.content.style.transition = 'none';
    }, { passive: true });

    this.content.addEventListener('touchmove', (e) => {
      const dx = e.touches[0].clientX - this.startX;
      const target = Math.max(-this.maxSwipe, Math.min(0, this.currentX + dx));
      this.content.style.transform = `translateX(${target}px)`;
    }, { passive: true });

    this.content.addEventListener('touchend', (e) => {
      const dx = e.changedTouches[0].clientX - this.startX;
      this.content.style.transition = 'transform 0.2s ease';
      if (dx < -this.maxSwipe / 2) {
        // 完全展开操作区
        this.currentX = -this.maxSwipe;
        this.content.style.transform = `translateX(${this.currentX}px)`;
      } else {
        // 回收
        this.currentX = 0;
        this.content.style.transform = 'translateX(0)';
      }
    }, { passive: true });
  }
}
```

### 8.3 下拉刷新

```css
/* 自定义下拉刷新指示器（替代浏览器原生）*/
.pull-to-refresh-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 0;
  overflow: hidden;
  color: var(--gold);
  font-size: 13px;
  transition: height 0.2s ease;
}

.pull-to-refresh-indicator.active {
  height: 44px;
}

.refresh-spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--gold-dim);
  border-top-color: var(--gold);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}
```

---

## 9. 动画规范更新

### 9.1 性能原则

移动端动画必须遵循 **60fps 黄金法则**，只使用 GPU 加速属性：

```
✅ 允许使用（GPU 加速）：
  transform: translate / scale / rotate
  opacity
  filter（谨慎，某些设备性能差）

❌ 禁止使用（触发布局/重绘）：
  width / height
  top / left / margin / padding
  background-color（在动画中）
  box-shadow（建议仅 transition，不用 animation）
```

### 9.2 移动端动画时长规范

| 类型 | 桌面时长 | 移动端时长 | 说明 |
|------|---------|---------|------|
| 微交互（按下反馈） | 150ms | **100ms** | 更快，即时感 |
| 页面切换 | 250ms | **300ms** | 略慢，顺滑感 |
| Bottom Sheet 弹出 | N/A | **350ms** | cubic-bezier |
| 语音全屏弹出 | N/A | **350ms** | 同上 |
| 状态切换（颜色）| 180ms | **200ms** | 接近 |
| 列表项淡入 | 280ms | **200ms** | 更快 |

### 9.3 新增移动端专属动画

```css
/* 页面切换：滑入滑出 */
@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

@keyframes slideOutLeft {
  from { transform: translateX(0);     opacity: 1; }
  to   { transform: translateX(-30%);  opacity: 0; }
}

/* FAB 弹出动画（首次出现）*/
@keyframes fabBounceIn {
  0%   { transform: scale(0) rotate(-45deg); opacity: 0; }
  60%  { transform: scale(1.15) rotate(5deg); opacity: 1; }
  80%  { transform: scale(0.95) rotate(-2deg); }
  100% { transform: scale(1) rotate(0); }
}

/* 日程卡片列表顺序入场 */
@keyframes cardStagger {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 卡片错落出现（每张延迟 60ms）*/
.agenda-card:nth-child(1) { animation: cardStagger 0.3s ease 0.05s both; }
.agenda-card:nth-child(2) { animation: cardStagger 0.3s ease 0.11s both; }
.agenda-card:nth-child(3) { animation: cardStagger 0.3s ease 0.17s both; }
.agenda-card:nth-child(4) { animation: cardStagger 0.3s ease 0.23s both; }
.agenda-card:nth-child(5) { animation: cardStagger 0.3s ease 0.29s both; }

/* 系统级：减弱动画偏好支持 */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration:   0.01ms !important;
    transition-duration:  0.01ms !important;
  }
}
```

---

## 10. PWA 与性能优化

### 10.1 PWA Manifest

商务人士常将应用添加至主屏，PWA 支持提供原生 App 级体验：

```json
{
  "name": "VoiCal 语音日历",
  "short_name": "VoiCal",
  "description": "智能语音日历助手，为商务人士设计",
  "start_url": "/?source=pwa",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#07090F",
  "theme_color": "#07090F",
  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "shortcuts": [
    {
      "name": "语音指令",
      "url": "/?tab=voice",
      "icons": [{ "src": "/icons/mic-96.png", "sizes": "96x96" }]
    },
    {
      "name": "今日日程",
      "url": "/?tab=today",
      "icons": [{ "src": "/icons/today-96.png", "sizes": "96x96" }]
    }
  ]
}
```

### 10.2 Service Worker 离线支持

```javascript
// sw.js - Service Worker 离线缓存策略
const CACHE_VERSION = 'voical-v1';
const STATIC_CACHE  = [
  '/',
  '/index.html',
  '/css/main.css',
  '/js/app.js',
];

// 安装：缓存静态资源
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_VERSION).then(c => c.addAll(STATIC_CACHE))
  );
  self.skipWaiting();
});

// 请求拦截策略：
// - API 请求：Network First（优先网络，离线返回缓存）
// - 静态资源：Cache First（优先缓存）
self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);

  if (url.pathname.startsWith('/api/')) {
    // Network First with Cache Fallback
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE_VERSION).then(c => c.put(e.request, clone));
          return res;
        })
        .catch(() => caches.match(e.request))
    );
  } else {
    // Cache First
    e.respondWith(
      caches.match(e.request).then(cached => cached || fetch(e.request))
    );
  }
});
```

### 10.3 性能优化清单

```html
<!-- 1. 视口 Meta 标签（防止双击缩放）-->
<meta name="viewport"
      content="width=device-width, initial-scale=1, maximum-scale=1,
               viewport-fit=cover, user-scalable=no">

<!-- 2. 主题色（Android 状态栏）-->
<meta name="theme-color" content="#07090F"
      media="(prefers-color-scheme: dark)">

<!-- 3. iOS PWA 全屏 -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">

<!-- 4. 字体预连接 -->
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>

<!-- 5. 关键 CSS 内联（避免阻塞渲染）-->
<style>/* 首屏关键 CSS 内联 */</style>

<!-- 6. 非关键 CSS 异步加载 -->
<link rel="preload" href="/css/non-critical.css" as="style"
      onload="this.onload=null;this.rel='stylesheet'">
```

---

## 11. 桌面 → 移动改动对照表

### 11.1 组件改动

| 桌面组件 | 改动类型 | 移动端方案 | 优先级 |
|---------|---------|-----------|--------|
| 三栏 Grid 布局 | 🔴 重构 | 单列 Flex + 底部 Tab Bar | P0 |
| 侧边栏 Sidebar | 🔴 废弃 | 底部 Tab 导航 + 侧滑抽屉菜单 | P0 |
| 右侧语音面板 | 🔴 重构 | FAB + 语音全屏页面 | P0 |
| 周视图（7列） | 🟠 改造 | 日视图默认 + 三日视图可选 | P0 |
| 居中 Modal | 🟠 改造 | Bottom Sheet | P1 |
| 顶部导航栏 | 🟠 精简 | 极简顶栏（标题 + 2 操作）| P1 |
| 纵向建议卡片 | 🟡 改造 | 横向滑动卡片组 | P1 |
| `:hover` 状态 | 🟡 替换 | `:active` + transform 反馈 | P1 |
| 今日日程列表 | 🟡 改造 | 卡片流 + 时间线 | P2 |
| 快捷指令竖排 | 🟡 改造 | 横向滑动 Chip 组 | P2 |

### 11.2 设计令牌差异

| Token | 桌面值 | 移动端值 | 变化原因 |
|-------|-------|---------|---------|
| `--r` | 9px | 12px | 移动端更圆润 |
| Body 字号 | 13px | 15px | 可读性 |
| Small 字号 | 10px | 12px | 可读性 |
| 小时高度 | 52px | 48px | 屏高有限，适度压缩 |
| 时间列宽 | 52px | 36px | 节省横向空间 |

### 11.3 新增移动端专属特性

| 特性 | 说明 |
|------|------|
| 触觉反馈（Haptic） | 关键操作振动反馈 |
| 手势导航（Swipe） | 左右滑动切换日期 |
| 列表左滑操作 | 快速完成/删除日程 |
| 下拉刷新 | 同步外部日历 |
| Bottom Sheet | 替代居中 Modal |
| PWA + 离线缓存 | 主屏添加 + 网络中断可用 |
| 安全区域适配 | iPhone 刘海 / 底部 Home 条 |
| `prefers-reduced-motion` | 无障碍动画减弱 |

---

## 12. 实现优先级与里程碑

### 12.1 分阶段实施计划

**Phase 1（第 1-2 周）—— 可用性基础**
> 目标：让移动端可以正常使用，消除所有 🔴 致命问题

- [ ] 响应式布局重构：三栏 → 单列 + Tab Bar
- [ ] 底部 Tab Bar 实现（5个 Tab）
- [ ] 日视图实现（替代周视图）
- [ ] 日期横向 Strip 导航
- [ ] Modal → Bottom Sheet 改造
- [ ] 顶部 Header 精简

**Phase 2（第 3 周）—— 交互优化**
> 目标：达到原生 App 级体验

- [ ] FAB 语音按钮实现
- [ ] 语音全屏界面
- [ ] 左右滑动切换日期手势
- [ ] 触摸反馈替换 hover 状态
- [ ] Bottom Sheet 下拉关闭手势
- [ ] 列表左滑快捷操作

**Phase 3（第 4 周）—— 品质打磨**
> 目标：细节精致，体验流畅

- [ ] 卡片流动画（错落入场）
- [ ] 触觉反馈接入
- [ ] 下拉刷新实现
- [ ] 横向滑动建议卡片
- [ ] 快捷指令 Chip 组
- [ ] 字体优化（精简加载）

**Phase 4（第 5 周）—— PWA 完善**
> 目标：可安装为独立 App

- [ ] PWA Manifest 配置
- [ ] Service Worker + 离线缓存
- [ ] 主屏添加适配（iOS/Android）
- [ ] 安全区域兜底测试
- [ ] 性能测试（LCP < 2.5s，FID < 100ms）

### 12.2 验收指标

| 指标 | 目标值 | 测试工具 |
|------|-------|---------|
| Lighthouse 移动端性能分 | ≥ 85 | Chrome DevTools |
| LCP（最大内容绘制）| < 2.5s | WebPageTest |
| FID（首次输入延迟）| < 100ms | Chrome UX Report |
| CLS（布局偏移）| < 0.1 | Lighthouse |
| 触摸目标通过率 | 100% | Lighthouse |
| 最小字号合规率 | 100% | 人工检查 |
| iPhone 14 Pro + Android Pixel 7 截图验收 | 通过 | 人工测试 |

---

*文档由 VoiCal 移动端团队维护 · 基于桌面端前端文档 v1.0 进行移动端专项优化*
*设计参考：Apple Human Interface Guidelines · Material Design 3 · 微信/钉钉移动端规范*
