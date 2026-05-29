# 🎙️ 智能语音日历前端（Voice Calendar Client）—— 用户与技术功能指南

欢迎使用**智能语音日历前端客户端**！本客户端是一个基于 **Vue 3 + Vite + TypeScript** 打造的高颜值、模块化、高交互性的智能语音日程办公系统。

客户端专为**移动端环境**设计，聚焦高频商务、车载驾驶以及视障/盲听等多元人群，并首创了**标准（可视式）与无障碍（盲听式）双轨交互布局**，能够完美承载 M1 至 M8 八大业务子模块的前端渲染与指令感知。

---

## 📂 项目模块化目录架构

前端代码严格遵循高解耦的按业务分块模块化架构设计，各级目录作用如下：

```
d:\JAVA\voice-calendar\frontend\src\
├── App.vue                         # 应用根组件：动态布局选择器
├── main.ts                         # 应用入口：挂载 Pinia 状态管理与 Vue Router
├── router/
│   └── index.ts                    # 路由配置：包含 /login、/、/conversation、/settings 与拦截守卫
├── types/
│   └── contracts.ts                # M1-M8 核心契约数据类型声明 (强类型安全)
├── styles/
│   ├── variables.css               # 极低照度色彩设计令牌 (配色、高对比度、Haptics 配色)
│   ├── global.css                  # 全局基础重置样式、字体排版、响应式布局媒介
│   ├── animations.css              # 精细微动效类库 (旋转、脉冲、卡片滑入、流动音量环)
│   └── accessibility.css           # 无障碍阅读高对比度专用重构样式
├── stores/
│   ├── useSessionStore.ts          # Pinia: 会话生命周期、ASR 听写、对话记录流、路由鉴权状态
│   ├── useCalendarStore.ts         # Pinia: 日程/待办本地缓存、乐观更新、增量变更控制
│   └── useSettingsStore.ts         # Pinia: 用户个人偏好 (主题、语速、振动反馈、无障碍配置)
├── composables/                    # 组合式函数 (无状态业务/传感器逻辑封装)
│   ├── useAudioRecorder.ts         # M1: Web Audio 16kHz PCM 单声道低延迟流式采集器
│   ├── useVADController.ts         # M1: 端侧静音断句控制器 (响应后端超时微调帧)
│   ├── useHapticFeedback.ts        # M1: 线性马达触觉反馈控制 ( tap/recording/processing/success/conflict 专属脉冲)
│   ├── useTTSPlayer.ts            # M1: 音频流及系统 TextToSpeech 音频播报，支持最高 2.5x 自适应语速
│   ├── useAccessibility.ts         # M1: 盲听无障碍大面积全屏手势感应器 (长按录音、双击打断、双指轻扫)
│   ├── useWebSocket.ts            # M2: WebSocket 双全工心跳/重连管理 (流式传输 chunk 与打断控制)
│   └── useOfflineQueue.ts         # M6:  IndexedDB 离线数据缓存队列 (乐观并发管理)
├── modules/                        # 按业务模块划分的独立 UI 组件块
│   ├── sensory/                    # M1: 语音感知 (VoiceButton, WaveformVisualizer, VoiceStatusIndicator, TTSControlBar)
│   ├── gateway/                    # M2: 网关状态 (ConnectionStatus, StreamingTranscript)
│   ├── semantic/                   # M3: 语义展现 (IntentBadge, EntityHighlight, ConfidenceBar)
│   ├── stateMachine/               # M4: 状态机交互 (ConversationFlow, ClarificationCard, ConflictNegotiation)
│   ├── calendar/                   # M5: 日程排期 (CalendarShell, EventCard, TaskItem, TimelineView)
│   ├── sync/                       # M6: 同步监控 (SyncStatusBanner, OfflineQueuePanel)
│   └── coordination/               # M8: 协同推荐 (FreeBusyTimeline, MeetingSuggestion)
└── views/                          # 独立路由功能页面
    ├── LoginView.vue               # 3D 霓虹流光登录与个人字典绑定界面
    ├── HomeView.vue                # 首页：日历多维日程定位排期与待办看板
    ├── ConversationView.vue        # 对话页：声感流式对话、冲突解决与协同看板全景集成
    └── SettingsView.vue            # 设置页：音感调节、断句阈值与偏好注销控制
```

---

## 🌟 核心功能特性说明书

### 一、 账号鉴权与路由保护 (Login & Route Guard)
* **磨砂流光登录卡片**：登录页面配有后台持续渲染的动态星空蓝和极光紫流光球层（Glow Orbs），提供高级的 3D 毛玻璃质感表单。
* **个人字典映射**：用户输入邮箱和昵称后，登录动作会自动为用户在 `SessionStore` 中拉取个人偏好，并触发欢迎播报。
* **安全重定向**：未登录用户在强行输入首页或对话页地址时，会被路由守卫自动拦截并强制导向 `/login` 进行安全校验，已登录用户会自动引导至主页。

### 二、 日历日程 absolute 时间网格对齐 (Visual Schedule Grid)
日历排期组件不仅支持月、周、日视图的自由平滑转换，更创新地实现了**卡片在排期表网格内的物理时间对齐**：
* **智能周视图渲染**：自动读取所选天的日期，在周视图的 7 列（周一至周日）中进行过滤。
* **绝对坐标定位**：日历网格以 7:00 AM 开始，每小时跨度高度为 60px。根据日程的起止时间算得高度和顶边偏移：
  $$\text{top} = (\text{起始小时} - 7) \times 60\text{px}$$
  $$\text{height} = (\text{结束小时} - \text{起始小时}) \times 60\text{px}$$
  晨会（9:30-10:30）等事件会以 `absolute` 的方式精准漂浮排列在第 150px 高度段，展现完美的多维时间透视，便于用户快速直观排雷。

### 三、 声震全景语音工作区 (Conversation Workspace)
双侧气泡流式对话页搭载了全套 AI 编排状态机，支持以下高保真业务流转模拟：
1. **实时逐字转写与波形可视化**：
   * 录音时，麦克风按钮产生红色呼吸气泡，音量指示器（Circumference Ring）随输入分段，底部的 Canvas 实时动态跳动绿色频谱波形。
   * **[StreamingTranscript](file:///d:/JAVA/voice-calendar/frontend/src/modules/gateway/StreamingTranscript.vue)** 支持 ASR 听写结果实时逐字呈递，并以浅色半透明标记未确定的局部结果。
2. **缺失追问卡片 (ClarificationCard)**：
   * 用户若只说“*帮我加个日程*”，AI 检测到缺失“标题”或“时间”等关键要素，自动变换为黄色警告态，展示缺失属性标签，播报提示词。用户可点击“跳过”或长按话筒进行语音答复补全。
3. **日程冲突协商卡片 (ConflictNegotiation)**：
   * 若新建日程与既有日程（如“*前端评审会*”）冲突，状态机自动展示红色时间占用警告。
   * 给出多套改期推荐（如*“改期至 15:30”*或*“改期至明天同一时间”*），支持语音交互口述选项、点击改期或强制覆盖创建。
4. **多方协同忙闲标尺 (FreeBusyTimeline & MeetingSuggestion)**：
   * 若查询多人忙闲，卡片将同时展示所有参与者的忙碌色块段，并把最完美的空闲交集窗口渲染为绿色可点块。
   * 智能匹配度推荐面板根据时间冲突度算出推荐匹配率（如 `95% 匹配度`）与相应匹配度横条，点击任一匹配度即可一键为多位联系人协调建立日历事件。

---

## ♿ 颠覆性无障碍体验：双轨交互布局

客户端在最底层集成了无障碍交互设计，通过系统偏好一键无缝转换布局：

| 交互维度 | 标准可视模式 (`DefaultLayout`) | 盲听无障碍模式 (`EyesFreeLayout`) |
| :--- | :--- | :--- |
| **主要人群** | 常规移动端用户、偏好可视排期排错 | 盲人/视障人群、车载驾驶中、户外跑步分心场景 |
| **视觉版式** | 毛玻璃底部 Tab 导航、精细图标、月历网格 | 纯黑强对比背景（对比度 > 1:7）、全屏超大字号展示、中央巨型状态指示环 |
| **触控交互** | 精细卡片点击、下拉框、滑动视图切换 | **全屏无焦点手势**：屏幕任意区域均可接受触控，无细小点击死角 |
| **手势系统** | 默认点击手势 | **长按**：开始倾听；**松手**：发送解析；**双击**：打断 TTS 播报/语音导航；**双指左右滑动**：切换日程 |
| **感官反馈** | 纯视觉状态胶囊、文字提示 | **线性马达立体反馈**：tap/recording/success 专属多态震动；**系统语音合成**：全程智能耳旁指引，支持最高 2.5x 疾速播报 |

---

## 🛠️ 本地运行与开发编译部署

### 1. 依赖安装与准备
在项目根目录 `d:\JAVA\voice-calendar\frontend` 下，执行终端指令安装所需前端生态依赖包：
```bash
npm install
```

### 2. 本地开发服务器启动
启动带有模块热重载（HMR）的前端调试服务器：
```bash
npm run dev
```
> [!NOTE]
> 针对部分 Windows 环境中 Powershell 默认执行策略被限（`PSSecurityException`）的问题，可使用 CMD 快速通道运行：
> `cmd.exe /c "npm run dev"`
> 服务运行成功后，访问本地调试地址：👉 **[http://localhost:5173/](http://localhost:5173/)**

### 3. 生产环境静态打包
执行生产代码混淆、死代码清理（Tree-shaking）及 chunk 预分析：
```bash
npm run build
```
打包物将被完美输出至 `dist/` 文件夹中，以极佳的传输速率用于生产线上托管与部署。

---

## 🎙️ 仿真场景体验测试流程

您可以在浏览器中，按照以下测试路径对八大模块的协同进行完美预览：

```
[登录页面 (LoginView)]
  └── 输入 邮箱: pm@corp.com、昵称: 产品经理 
  └── 点击“立即开启智能日程”，触发成功振动 tap 和智能欢迎 TTS 播报
        │
[首页日历 (HomeView)]
  └── 自动载入种子日程，此时切换“周”或“日”视图，晨会等卡片已经完美绝对定位对齐在网格上
  └── 点击底部中央高亮发光的“🎙️”按钮，平滑过渡进入全屏语音工作区
        │
[语音对话区 (ConversationView)]
  └── 页面加载自动播报系统向导 TTS 
  └── 点击下方的快捷建议词，触发全套交互流程仿真：
        ├── 点击 “明天下午三点开会”
        │     └── AI 解析成功 -> 触发“success”成功振动 -> 自动往日历添加事件并进行 TTS 成功播报 -> 自动切回 idle
        ├── 点击 “明天下午两点开会”
        │     └── AI 提示冲突 -> 触发“conflict”三连震 -> 挂载 ConflictNegotiation 冲突警告卡片 -> 提供改期选项
        └── 点击 “查询大家明天的忙闲”
              └── 触发 FreeBusyTimeline 协同忙闲聚合尺 -> 推荐 95% 匹配的空闲交集 -> 提供 MeetingSuggestion 时间一键选取
```
