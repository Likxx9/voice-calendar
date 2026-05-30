# 语音日历 — 前端页面开发文档

> **VoiCal · Executive Voice Calendar**  
> 版本：v1.0 · 商务风格前端规范  
> 适用框架：HTML / CSS / Vanilla JS（可迁移至 React）

---

## 目录

1. [设计方向与视觉语言](#1-设计方向与视觉语言)
2. [页面整体布局](#2-页面整体布局)
3. [设计令牌（Design Tokens）](#3-设计令牌design-tokens)
4. [字体规范](#4-字体规范)
5. [模块详细规范](#5-模块详细规范)
   - 5.1 [侧边栏 Sidebar](#51-侧边栏-sidebar)
   - 5.2 [顶部导航栏 Topbar](#52-顶部导航栏-topbar)
   - 5.3 [周视图日历 Week Grid](#53-周视图日历-week-grid)
   - 5.4 [语音指令面板 Voice Panel](#54-语音指令面板-voice-panel)
   - 5.5 [今日日程 Today Brief](#55-今日日程-today-brief)
   - 5.6 [智能建议 Suggestions](#56-智能建议-suggestions)
   - 5.7 [事件详情 Modal](#57-事件详情-modal)
6. [动画规范](#6-动画规范)
7. [状态机：语音交互](#7-状态机语音交互)
8. [事件数据结构](#8-事件数据结构)
9. [交互行为规范](#9-交互行为规范)
10. [响应式适配说明](#10-响应式适配说明)
11. [完整源码](#11-完整源码)

---

## 1. 设计方向与视觉语言

### 1.1 设计定位

**主题**：深夜指挥室（Dark Executive Command Center）

针对商务决策者的日历工具，视觉语言传达三个核心信号：

| 信号 | 设计手法 |
|------|---------|
| 沉稳权威 | 极深海军蓝底色 + 克制的金色点缀 |
| 精密高效 | 52px 等距背景网格 + Mono 字体显示时间数据 |
| 智能现代 | 琥珀色 AI 事件呼吸光晕 + 实时 Agent 日志 |

### 1.2 背景纹理

全局使用 CSS 网格背景叠加，不影响内容层级：

```css
body::before {
  content: '';
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background-image:
    linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px);
  background-size: 52px 52px;
}
```

### 1.3 色彩哲学

主色调仅金色（`#C8A45A`）一种暖色，其余蓝/青/红/绿仅用于事件分类标签，绝不与金色竞争视觉权重。所有彩色背景均为低饱和度 `rgba` 形式，保持整体克制感。

---

## 2. 页面整体布局

### 2.1 三栏 Grid 布局

```
┌─────────────────────────────────────────────────────────┐
│  Sidebar (220px)  │  Main Calendar (flex-1)  │ Right (308px) │
│                   │                          │              │
│  Logo             │  Topbar                  │ Voice Panel  │
│  Navigation       │  Week Calendar Grid      │ Today Brief  │
│  Mini Calendar    │                          │ Suggestions  │
│  User Profile     │                          │              │
└─────────────────────────────────────────────────────────┘
```

```css
.app {
  display: grid;
  grid-template-columns: 220px 1fr 308px;
  height: 100vh;
  overflow: hidden;
}
```

### 2.2 层级 z-index

| 层级 | z-index | 用途 |
|------|---------|------|
| 背景网格 | 0 | `body::before` 纹理 |
| 主内容 | 1 | `.app` 所有内容 |
| 日历头部 | 10 | sticky 吸顶行 |
| Topbar | 10 | 毛玻璃吸顶 |
| 事件 | 5 | 当前时间线压事件 |
| Modal 遮罩 | 200 | 全屏覆盖 |

---

## 3. 设计令牌（Design Tokens）

所有颜色、字体、圆角通过 CSS 自定义属性统一管理，禁止在组件内硬编码色值。

```css
:root {
  /* ── 背景 ── */
  --bg:       #07090F;   /* 主背景，极深海军蓝 */
  --bg2:      #0C1020;   /* 卡片背景 */
  --bg3:      #111827;   /* 次级背景 */
  --bg-hover: #121A2E;   /* 悬停态背景 */

  /* ── 主色调：金色 ── */
  --gold:        #C8A45A;
  --gold2:       #E2C07A;               /* 高亮金 */
  --gold-dim:    rgba(200,164,90,.10);  /* 金色填充背景 */
  --gold-border: rgba(200,164,90,.18);  /* 金色描边 */

  /* ── 事件分类色 ── */
  --blue:      #4B96FF;
  --blue-dim:  rgba(75,150,255,.10);
  --teal:      #2DD4BF;
  --teal-dim:  rgba(45,212,191,.10);
  --red:       #F87171;
  --red-dim:   rgba(248,113,113,.10);
  --amber:     #FBBF24;
  --amber-dim: rgba(251,191,36,.10);
  --green:     #4ADE80;
  --green-dim: rgba(74,222,128,.10);

  /* ── 文字 ── */
  --text:  #EBE5DC;   /* 主文字，暖白 */
  --text2: #8A8FA8;   /* 次级文字 */
  --text3: #3A3F52;   /* 弱化文字，分隔符 */

  /* ── 边框 ── */
  --border: rgba(255,255,255,.055);

  /* ── 字体族 ── */
  --fd: 'Cormorant Garamond', Georgia, serif;   /* 展示字体 */
  --fu: 'Outfit', system-ui, sans-serif;         /* UI 字体 */
  --fm: 'JetBrains Mono', 'Courier New', monospace; /* 等宽字体 */

  /* ── 圆角 ── */
  --r: 9px;
}
```

---

## 4. 字体规范

### 4.1 字体加载

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?
  family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400
  &family=Outfit:wght@300;400;500;600;700
  &family=JetBrains+Mono:wght@300;400;500
  &display=swap">
```

### 4.2 字体使用场景

| 字体 | 变量 | 用途 | 示例 |
|------|------|------|------|
| Cormorant Garamond | `--fd` | 日历日期数字、Logo、Modal 标题 | `22`、`VoiCal`、事件名称 |
| Outfit | `--fu` | 所有 UI 文字、按钮、标签 | 导航项、状态文字 |
| JetBrains Mono | `--fm` | 时间显示、Agent 日志 | `09:00`、`[ASR] 识别完成` |

### 4.3 字号规范

| 层级 | 字号 | 字重 | 用途 |
|------|------|------|------|
| Display | 24px | 500 | Logo 名称 |
| H1 | 22–23px | 400 | Modal 标题（Cormorant） |
| H2 | 22px（日历） | 300 | 日期数字（Cormorant） |
| Body | 13px | 400 | 导航、描述 |
| Small | 11–11.5px | 400/500 | 元数据、时间标签 |
| Micro | 9–10px | 500–600 | 区块标题、上边框标签 |

---

## 5. 模块详细规范

### 5.1 侧边栏 Sidebar

**宽度**：220px，固定，不滚动外框

**结构**：

```
Sidebar
├── Logo Block
├── Scroll Area (flex-1, overflow-y: auto)
│   ├── Navigation Section — 视图
│   ├── Navigation Section — 我的日历
│   ├── Divider
│   └── Mini Calendar
└── Footer (User Profile + Status)
```

**Logo 金色 Shimmer 动画**：

```css
.sb-logo-name {
  background: linear-gradient(90deg, var(--gold), var(--gold2), var(--gold));
  background-size: 200% 100%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: shimmer 4s linear infinite;
}

@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}
```

**导航项状态**：

```css
/* 默认 */
.nav-item { color: var(--text2); }

/* 悬停 */
.nav-item:hover {
  background: var(--bg-hover);
  color: var(--text);
}

/* 激活 */
.nav-item.active {
  background: var(--gold-dim);
  color: var(--gold);
  font-weight: 500;
}
```

**迷你日历**：

- 布局：`display: grid; grid-template-columns: repeat(7, 1fr)`
- 日期单元格为圆形，`aspect-ratio: 1`，悬停背景 `var(--bg-hover)`
- 今日：实心金色圆背景，黑色文字
- 当前周：浅金色底 `rgba(200,164,90,.06)`
- 有事件日期：底部 3px 金色圆点指示器（`.has-evt::after`）

**用户状态指示器**：

```css
.online-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--teal);
  animation: pulse 2.2s ease-in-out infinite;
}
```

---

### 5.2 顶部导航栏 Topbar

**高度**：约 50px，`position: sticky`，毛玻璃效果

```css
.topbar {
  background: rgba(7,9,15,.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}
```

**三段式布局**：

```
[ ‹ › ] [ 2026年5月·第22周 ] [ 今日 ]    [ 日 周 月 ]    [ Agent在线 ] [ 日期 ] [ 头像 ]
  LEFT                                    CENTER              RIGHT
```

**视图切换 Tab**：

```css
.view-tabs {
  display: flex;
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 3px;
}

.vt.on {
  background: var(--gold-dim);
  color: var(--gold);
}
```

**Agent 在线状态徽章**：

```html
<div class="ag-badge">
  <span class="ag-dot"></span>
  Agent 在线
</div>
```

```css
.ag-badge {
  background: var(--teal-dim);
  border: 1px solid rgba(45,212,191,.2);
  border-radius: 20px;
  color: var(--teal);
}
```

---

### 5.3 周视图日历 Week Grid

**核心参数**：

```js
const HOUR_H   = 52;    // 每小时高度（px）
const BASE_HR  = 8;     // 起始时间（8:00）
const HOURS    = 13;    // 显示时间段数（8:00 ~ 20:00）
const TOTAL_H  = HOURS * HOUR_H;  // = 676px
```

**Grid 结构**：

```css
.cal-grid {
  display: grid;
  grid-template-columns: 52px repeat(7, 1fr);
}
```

第一列（52px）为时间标签列，后 7 列为每天内容列。

**事件定位公式**：

```js
// 绝对定位于 .day-col 内
const top    = (event.startHour - BASE_HR) * HOUR_H + 2;   // +2px 间距
const height = (event.endHour - event.startHour) * HOUR_H - 4; // -4px 间距
```

**事件色彩系统**（6 类）：

| 类名 | 颜色变量 | 适用场景 |
|------|---------|---------|
| `.ec-gold` | `--gold` | 重要会议、客户会面 |
| `.ec-blue` | `--blue` | 远程/在线会议 |
| `.ec-teal` | `--teal` | 社交、午餐 |
| `.ec-red` | `--red` | 战略、重大事项 |
| `.ec-green` | `--green` | 站会、日常 |
| `.ec-amber` | `--amber` | **AI 新建事件**（有呼吸光晕） |

**当前时间指示器**：

```css
.ctl {
  position: absolute;
  left: 0; right: 0;
  height: 1.5px;
  background: var(--gold);
  z-index: 5;
}

.ctd {   /* 左侧圆点 */
  position: absolute;
  left: -4px; top: -4px;
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--gold);
  animation: pulse 1.6s ease-in-out infinite;
}
```

定位计算：

```js
ctl.style.top = (NOW_HOUR - BASE_HR) * HOUR_H + 'px';
```

**AI 新建事件标识**：

```css
.ev-new-badge {
  position: absolute;
  top: 4px; right: 5px;
  background: var(--amber);
  color: #000;
  font-size: 8px;
  font-weight: 700;
  padding: 1px 4px;
  border-radius: 3px;
  animation: newBadge .4s ease;
}
```

---

### 5.4 语音指令面板 Voice Panel

语音面板是右侧栏的核心模块，覆盖四种状态：

**容器样式**：

```css
.vc {
  background: linear-gradient(135deg, rgba(200,164,90,.06), rgba(200,164,90,.02));
  border: 1px solid var(--gold-border);
  border-radius: 12px;
  padding: 18px 16px;
}
```

**麦克风按钮**（62×62px，圆形）：

```css
/* 默认 */
.mic-btn {
  border: 1.5px solid var(--gold-border);
  background: var(--gold-dim);
}

/* 聆听中 */
.mic-btn.listening {
  border-color: var(--gold);
  background: rgba(200,164,90,.18);
  animation: glowGold 1.1s ease-in-out infinite;
}

/* 处理中 */
.mic-btn.processing {
  border-color: var(--blue);
  background: var(--blue-dim);
}

/* 完成 */
.mic-btn.done {
  border-color: var(--teal);
  background: var(--teal-dim);
}
```

**波纹扩散动画**（聆听状态专属）：

```css
.mic-ripple {
  position: absolute;
  inset: -10px;
  border-radius: 50%;
  border: 1.5px solid var(--gold);
  animation: ripple 1.9s ease-out infinite;
}

@keyframes ripple {
  0%   { transform: scale(1);   opacity: .55; }
  100% { transform: scale(2.6); opacity: 0;   }
}
```

**声波波形条**（7 根）：

```css
.wb { width: 3px; border-radius: 2px; background: var(--gold); height: 4px; }

/* 激活时 */
.wb.on:nth-child(1) { animation: waveBar .7s ease-in-out 0.00s infinite; }
.wb.on:nth-child(2) { animation: waveBar .7s ease-in-out 0.09s infinite; }
.wb.on:nth-child(3) { animation: waveBar .7s ease-in-out 0.18s infinite; }
.wb.on:nth-child(4) { animation: waveBar .7s ease-in-out 0.27s infinite; }
.wb.on:nth-child(5) { animation: waveBar .7s ease-in-out 0.18s infinite; }
.wb.on:nth-child(6) { animation: waveBar .7s ease-in-out 0.09s infinite; }
.wb.on:nth-child(7) { animation: waveBar .7s ease-in-out 0.00s infinite; }

@keyframes waveBar {
  0%, 100% { transform: scaleY(.12); }
  50%       { transform: scaleY(1);   }
}
```

中央最高（第4根），两侧对称递减，模拟真实声纹形态。

**Agent 处理日志**：

```css
.alog {
  background: rgba(0,0,0,.5);
  border: 1px solid var(--border);
  border-radius: 8px;
  max-height: 165px;
  overflow-y: auto;
  font-family: var(--fm);
  font-size: 10px;
  line-height: 1.75;
}

/* 日志行颜色 */
.al-tag       { color: var(--teal); }   /* 默认标签：ASR/NLU/Agent */
.al-tag.s     { color: var(--blue); }   /* 搜索/地图 */
.al-tag.d     { color: var(--gold); }   /* 完成状态 */
```

每行通过 `setTimeout` 间隔 420ms 逐行追加，配合 `scrollTop = scrollHeight` 自动滚底。

**快捷指令按钮**：

```css
.qp {
  border: 1px solid var(--border);
  border-radius: 7px;
  background: none;
  color: var(--text2);
  transition: all .18s;
}

.qp:hover {
  border-color: var(--gold);
  color: var(--text);
  background: var(--gold-dim);
}
```

---

### 5.5 今日日程 Today Brief

每条日程行：时间 + 色点 + 标题/地点

```css
.brief-item {
  display: flex;
  gap: 10px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: all .18s;
}

.brief-item:hover .bt { color: var(--gold); }

.btime {
  font-family: var(--fm);
  font-size: 10px;
  min-width: 38px;
  letter-spacing: .03em;
  color: var(--text2);
}
```

---

### 5.6 智能建议 Suggestions

```css
.sug {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 9px;
  padding: 11px 13px;
  transition: all .22s;
}

.sug:hover {
  border-color: var(--gold-border);
  background: var(--bg-hover);
}
```

---

### 5.7 事件详情 Modal

**遮罩层**：

```css
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.75);
  backdrop-filter: blur(6px);
  z-index: 200;
  animation: fadeUp .2s ease;
}
```

**Modal 卡片**（340px，居中）：

```css
.modal {
  background: var(--bg2);
  border: 1px solid var(--gold-border);
  border-radius: 14px;
  padding: 26px;
  box-shadow: 0 24px 64px rgba(0,0,0,.6);
  animation: fadeUp .25s ease;
}
```

**标题字体**：Cormorant Garamond 23px，字重 400，传递优雅感而非视觉冲击。

---

## 6. 动画规范

项目使用 8 个关键帧动画，均定义在全局 CSS：

```css
/* 1. 声波条高度震荡 */
@keyframes waveBar {
  0%, 100% { transform: scaleY(.12); }
  50%       { transform: scaleY(1);   }
}

/* 2. 呼吸脉冲（今日圆点、在线状态、当前时间点） */
@keyframes pulse {
  0%, 100% { opacity: .5; transform: scale(1);   }
  50%       { opacity: 1; transform: scale(1.1); }
}

/* 3. 波纹扩散（聆听状态麦克风外圈） */
@keyframes ripple {
  0%   { transform: scale(1);   opacity: .55; }
  100% { transform: scale(2.6); opacity: 0;   }
}

/* 4. 向上淡入（Modal、日志行、结果卡片） */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(7px); }
  to   { opacity: 1; transform: translateY(0);   }
}

/* 5. 金色呼吸光晕（AI 新建事件、聆听中麦克风） */
@keyframes glowGold {
  0%, 100% { box-shadow: 0 0 10px rgba(200,164,90,.25); }
  50%       { box-shadow: 0 0 26px rgba(200,164,90,.55); }
}

/* 6. 旋转加载（处理中麦克风图标） */
@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 7. Logo 金色流光 */
@keyframes shimmer {
  0%   { background-position: -200% 0; }
  100% { background-position:  200% 0; }
}

/* 8. NEW 徽章弹入 */
@keyframes newBadge {
  0%   { opacity: 0; transform: scale(.7); }
  100% { opacity: 1; transform: scale(1);  }
}
```

---

## 7. 状态机：语音交互

语音面板存在四种状态，状态转移如下：

```
         点击麦克风
  idle ────────────► listening
   ▲                     │ 2.2s 后自动
   │                     ▼
  reset ◄── done ◄── processing
   │          │          │
   │    结果展示      逐行打印日志
   │                  420ms/行
   └──────── 点击重置随时回到 idle
```

**状态对应 UI 变化**：

| 状态 | 麦克风样式 | 波形 | 波纹 | 状态文字 |
|------|-----------|------|------|---------|
| `idle` | 默认金色边框 | 静止 4px | 隐藏 | 点击开始指令 |
| `listening` | 金色光晕 | 7 根动态 | 循环扩散 | 正在聆听... |
| `processing` | 蓝色边框 + 旋转 | 静止 | 隐藏 | Agent 分析中... |
| `done` | 青色边框 + ✓ | 静止 | 隐藏 | 指令执行完成 |

---

## 8. 事件数据结构

```js
const event = {
  col:   1,              // 列索引（0=周日, 6=周六）
  id:    1,              // 唯一 ID
  title: '董事会季度汇报', // 显示标题
  s:     9,              // 开始时间（小时，支持 .5 表示半小时）
  e:     10.5,           // 结束时间
  c:     'gold',         // 颜色标识：gold|blue|teal|red|amber|green
  loc:   '15F 会议室 A', // 地点
  att:   8,              // 参与人数
  type:  '会议',          // 事件类型（中文标签）
  isNew: false,          // 是否为 AI 新建（显示 NEW 徽章 + 光晕）
};
```

**时间格式化工具函数**：

```js
/**
 * 将小数时间转为 HH:MM 字符串
 * @param {number} h - 如 9.5 → "09:30"，10 → "10:00"
 */
function fmtTime(h) {
  const hh = Math.floor(h);
  const mm = h % 1 === 0 ? '00' : '30';
  return `${hh < 10 ? '0' : ''}${hh}:${mm}`;
}
```

---

## 9. 交互行为规范

### 9.1 事件点击

- 点击 `.ev` 调用 `openModal(event)`
- Modal 遮罩区域点击关闭（`e.stopPropagation` 保护卡片）
- 进入/离开动画：`fadeUp 0.2s`

### 9.2 语音触发路径

```
用户点击麦克风 / 快捷指令按钮
  → voiceState = 'listening'
  → 2200ms 延迟（模拟 ASR 识别）
  → 显示 query-box（用户指令文字）
  → voiceState = 'processing'
  → setInterval 每 420ms 追加一条 Agent 日志
  → 所有日志完成后 400ms → voiceState = 'done'
  → 展示 result-c（结果卡片）
```

### 9.3 日历周导航

- `‹ ›` 按钮调用 `shiftWeek(-1 / +1)`，重新渲染 7 列日期
- `今日` 按钮调用 `goToday()`，滚动定位至当前时间：

```js
function goToday() {
  document.getElementById('cal-scroll').scrollTop =
    Math.max(0, (NOW_HOUR - BASE_HR - 1) * HOUR_H);
}
```

### 9.4 初始化滚动位置

页面加载后自动滚动至上午 9 点（商务时间起点）：

```js
setTimeout(() => {
  document.getElementById('cal-scroll').scrollTop = (9 - BASE_HR) * HOUR_H - 16;
}, 100);
```

---

## 10. 响应式适配说明

当前版本面向桌面端（≥1280px），以下为移动端降级策略：

| 断点 | 布局变化 |
|------|---------|
| `≥ 1280px` | 三栏完整布局 |
| `960px ~ 1279px` | 隐藏侧边栏，右侧栏缩至 280px |
| `768px ~ 959px` | 右侧栏折叠为底部抽屉（Drawer） |
| `< 768px` | 单列布局，日历切换为日视图，语音面板为全屏 Modal |

移动端语音面板建议全屏展示，利用设备麦克风权限直接调用 `Web Speech API`。

---

## 11. 完整源码

### 11.1 HTML 结构骨架

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <!-- Google Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?
    family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;0,600;1,300;1,400
    &family=Outfit:wght@300;400;500;600;700
    &family=JetBrains+Mono:wght@300;400;500
    &display=swap">
  <style>/* 见 §3 设计令牌 + 各模块 CSS */</style>
</head>
<body>

  <div class="app">

    <!-- 侧边栏 -->
    <aside class="sidebar">
      <div class="sb-logo">...</div>
      <div class="sb-scroll">
        <!-- 导航 + 迷你日历 -->
      </div>
      <div class="sb-foot"><!-- 用户信息 --></div>
    </aside>

    <!-- 主日历区 -->
    <main class="main">
      <div class="topbar">...</div>
      <div class="cal-scroll" id="cal-scroll">
        <div class="cal-head" id="cal-head"></div>
        <div class="cal-grid" id="cal-grid"></div>
      </div>
    </main>

    <!-- 右侧面板 -->
    <aside class="rp">
      <!-- 语音指令 -->
      <div class="rp-sec">
        <div class="vc">
          <div class="mic-wrap">...</div>
          <!-- query-box / alog / result-c / qps -->
        </div>
      </div>
      <!-- 今日日程 -->
      <div class="rp-sec" id="today-brief-sec">...</div>
      <!-- 智能建议 -->
      <div class="rp-sec">...</div>
    </aside>

  </div>

  <!-- 事件详情 Modal -->
  <div class="overlay" id="modal">
    <div class="modal">...</div>
  </div>

  <script>/* 见 §8 数据结构 + §7 状态机逻辑 */</script>
</body>
</html>
```

### 11.2 关键 JavaScript 函数清单

```js
// 构建函数
buildCalendar()   // 渲染日历头部 + 事件网格 + 今日简报
buildMiniCal()    // 渲染侧边栏迷你日历（6行×7列）

// 语音交互
handleMic()          // 麦克风点击入口
runPrompt(idx)       // 执行第 idx 条快捷指令（0/1/2）
resetVoice()         // 重置所有语音状态

// 事件交互
openModal(event)     // 打开事件详情弹窗
closeModal()         // 关闭弹窗

// 日历导航
shiftWeek(delta)     // 前 / 后移一周（delta = ±1）
goToday()            // 滚动到今日当前时间位置
setView(v)           // 切换视图：'day' | 'week' | 'month'

// 工具函数
fmtTime(h)           // 数值小时 → "HH:MM" 字符串
```

---

*文档由 VoiCal 前端团队维护，如有更新请同步修改 Design Tokens 与各模块规范章节。*
