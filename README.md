# VoiCal — AI 语音智能日历助手

> 让每一句话都变成日程，让每一次出行都有规划。

---

## 一、需求分析

### 1.1 行业痛点

在快节奏的商务环境中，日程管理是效率的关键瓶颈：

- **操作成本高**：传统日历需要"打开App → 找功能 → 输入信息 → 确认保存"，一个日程至少需要 4 步操作
- **信息孤岛严重**：日历App、地图App、12306App、会议App 各自独立，用户需要在多个应用间频繁切换
- **被动记录而非主动管理**：传统日历只记录"什么时候有事"，不会主动检测冲突、推荐空闲时段、规划出行路线
- **提醒方式单一**：静音弹窗通知容易被忽略，商务人士在开车、会议中无法及时查看手机
- **多平台割裂**：钉钉管内部沟通、企业微信管客户、Google Calendar 管个人日程，日程数据分散在多个平台

### 1.2 用户场景

| 场景 | 痛点 | VoiCal 解决方案 |
|------|------|----------------|
| 开车途中想安排会议 | 无法安全操作手机 | 语音指令创建会议 + 自动生成视频链接 |
| 出差前查高铁 | 需切换地图+12306+日历三个App | 语音一句话完成：查高铁→选车次→创建出行日程 |
| 多个会议时间冲突 | 手动逐个调整 | AI 自动分析优先级，推荐空闲时段 |
| 跨平台日程不一致 | 手动同步多个平台 | 一键同步钉钉/企微/Google/Outlook |
| 会议结束跟进 | 手动记录纪要和待办 | AI 自动生成结构化纪要 + Action Items 转任务 |

---

## 二、目标人群定位

### 2.1 核心用户

**中高层商务人士** — 每日日程密集、需要频繁协调时间、对效率有极高要求的专业人群。

| 特征 | 描述 |
|------|------|
| 职业 | 企业高管、项目经理、销售总监、创业者、咨询顾问 |
| 日程密度 | 每日 5-15 个日程，涉及内外部会议、客户拜访、差旅 |
| 工具习惯 | 同时使用钉钉/企业微信 + Google Calendar/Outlook |
| 核心诉求 | **省时间、少出错、不漏事** |

### 2.2 扩展用户

- **自由职业者**：需要管理多个客户项目的交付时间线
- **行政/秘书**：需要为领导协调日程、安排会议室
- **个人用户**：希望用语音快速管理日常生活安排

---

## 三、产品定位

### 3.1 一句话定位

> **VoiCal 是一款面向商务人士的 AI 语音智能日历助手，通过大语言模型 Agent 架构，将语音交互、日程管理、出行规划、会议协作深度融合，实现"开口即管理时间"的全新体验。**

### 3.2 核心差异

| 维度 | 传统日历App | VoiCal |
|------|------------|--------|
| 交互方式 | 手动点击输入 | **语音自然语言交互** |
| 智能程度 | 被动记录 | **AI Agent 主动规划、编排、执行** |
| 功能边界 | 仅日程CRUD | **日程+出行+会议+任务 一体化** |
| 冲突处理 | 提示冲突 | **AI 自动分析+推荐解决方案** |
| 出行规划 | 需切换地图/12306 | **日历内直接查高铁+创建出行日程** |
| 多平台 | 单平台日历 | **钉钉/企微/Google/Outlook 双向同步** |

### 3.3 产品愿景

成为商务人士的 **"AI 时间管理伙伴"** — 不只是一个记录工具，而是能理解意图、规划路径、执行任务、主动提醒的智能助手。

---

## 四、产品内容

### 4.1 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                    VoiCal 五层架构                        │
├─────────────────────────────────────────────────────────┤
│  L0 语音采集层    │ 麦克风录音 + VAD 能量检测              │
│  L1 ASR 识别层    │ 科大讯飞 WebSocket 实时语音识别         │
│  L2 NLU 理解层    │ 智谱 GLM-4 意图识别 + 槽位抽取          │
│  L3 Agent 编排层  │ 多步任务规划 + DAG 执行计划 + 工具调度   │
│  L4 工具执行层    │ 高德路线/12306高铁/日程管理/会议协作     │
│  L5 输出聚合层    │ LLM 摘要 + 讯飞 TTS 语音合成播报        │
└─────────────────────────────────────────────────────────┘
```

### 4.2 核心功能模块

#### 语音交互

| 功能 | 说明 |
|------|------|
| 按住说话 (Push-to-Talk) | 麦克风按钮长按录音，松开发送识别 |
| 实时声波可视化 | 7 根声波条动画反馈录音状态 |
| Agent 处理日志 | 逐行显示 Agent 分析过程，增强可解释性 |
| 对话历史记录 | 完整聊天记录，用户/Agent 消息气泡区分 |
| Barge-in 打断 | TTS 播报中可随时语音打断，<100ms 响应 |

#### 日程管理

| 功能 | 说明 |
|------|------|
| 语音创建日程 | "帮我安排明天下午3点的客户会议" |
| 冲突检测 | 创建/修改时自动检测时间重叠 |
| AI 智能重排 | 冲突时 AI 分析优先级，推荐调整方案 |
| 空闲时段查询 | 计算工作时间窗口内的空闲段 |
| 模糊搜索 | 标题关键词 + 日期模糊匹配 |
| 优先级管理 | HIGH / MEDIUM / LOW 三级优先级 |
| 软删除 | 日程删除采用标记策略，数据可恢复 |
| AI 新建标识 | Agent 创建的日程显示 "NEW" 徽章 |

#### 出行规划

| 功能 | 说明 |
|------|------|
| 多模式路线对比 | 驾车/公交/步行/骑行 同时对比 |
| 跨城出行检测 | 自动判断跨城（>80km），主动推荐高铁 |
| 12306 实时查票 | 语音查询高铁/动车车次及余票 |
| 高铁日程联动 | 选定车次后自动创建出行日程 |
| 地理编码 | 高德地图 API 地名→经纬度转换 |

#### 会议协作

| 功能 | 说明 |
|------|------|
| 一键创建会议 | 创建日程 + 自动生成视频会议链接 |
| 多平台支持 | 钉钉/腾讯会议/飞书/企业微信 |
| 邀约通知 | 异步发送邮件/短信/企业消息邀请 |
| AI 会议纪要 | 基于录音转写文本生成结构化纪要 |
| Action Items 提取 | 从纪要中自动提取待办转为任务 |

#### 多端同步

| 功能 | 说明 |
|------|------|
| 四大平台适配 | 钉钉/企业微信/Google Calendar/Outlook |
| 双向同步 | VoiCal↔外部平台实时同步 |
| 冲突解决 | Last-Write-Wins 策略 |
| 同步日志 | 完整记录每次同步的方向、状态 |

#### 智能建议

| 功能 | 说明 |
|------|------|
| 交通方式卡片 | 多模式路线结果可视化展示 |
| 高铁车次列表 | 车次号、时间、时长、余票一目了然 |
| 冲突预警卡片 | 检测到冲突时展示调整建议 |
| 时间推荐卡片 | 推荐时间 + 备选时段列表 |
| 快捷指令 | 预设常用语音指令一键触发 |

### 4.3 前端体验

- **深夜指挥室风格**：极深海军蓝 + 金色点缀，专为商务决策者设计
- **三视图切换**：日/周/月视图，AI 新建事件呼吸光晕
- **响应式适配**：桌面三栏 → 平板两栏 → 手机单列 + 手势滑动
- **移动端优化**：底部 Tab 导航 + 语音悬浮按钮 (VoiceFAB) + 全屏语音界面

### 4.4 安全与容错

| 机制 | 说明 |
|------|------|
| JWT 认证 + RBAC | basic / admin / pro 三级权限控制 |
| AES-256 字段加密 | 手机号、邮箱、Token 等敏感信息加密存储 |
| 写操作确认 | 日历写入前 TTS 播报确认，10秒超时自动取消 |
| 超时熔断 | 工具并行执行，单个超时不影响整体 |
| 指数退避重试 | 工具调用失败后自动重试 |
| TTS 双引擎容灾 | 讯飞主引擎故障时自动切换阿里云备用引擎 |
| 离线消息兜底 | 网络中断时写入 Redis 队列，恢复后自动执行 |

---

## 五、技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Socket.IO Client |
| 后端 | Flask + Flask-SocketIO + FastAPI |
| AI 大模型 | 智谱 GLM-4 (ZhipuAI SDK) |
| 语音识别 (ASR) | 科大讯飞 WebSocket 实时语音听写 |
| 语音合成 (TTS) | 科大讯飞 WebSocket 语音合成 + PyAudio |
| 数据库 | PostgreSQL 16 (生产) / SQLite (开发) |
| ORM | SQLAlchemy 2.0 (async) |
| 数据库迁移 | Alembic |
| 缓存 | Redis 7 |
| 地图服务 | 高德地图 REST API |
| 高铁查询 | 12306 官方 API |
| 实时通信 | WebSocket (Socket.IO) |
| 容器化 | Docker + Docker Compose |

---

## 六、快速开始

### 6.1 环境要求

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose（可选，用于启动 PostgreSQL/Redis）
- PyAudio（需系统级音频库）

### 6.2 启动步骤

```bash
# 1. 克隆项目
git clone https://github.com/Likxx9/voice-calendar.git
cd voice-calendar

# 2. 启动基础设施（PostgreSQL + Redis）
docker-compose up -d

# 3. 创建并激活虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# 4. 安装依赖
pip install -r backend_requirements.txt
pip install flask flask-socketio zhipuai websocket-client pyaudio aiosqlite nest-asyncio python-dotenv

# 5. 配置环境变量
copy .env.example .env
# 编辑 .env 填入以下必填项：
#   ZHIPUAI_API_KEY    — 智谱 AI API Key
#   AMAP_API_KEY       — 高德地图 API Key
#   XUNFEI_APPID       — 讯飞应用 ID
#   XUNFEI_API_KEY     — 讯飞 API Key
#   XUNFEI_API_SECRET  — 讯飞 API Secret

# 6. 启动后端服务器
python server.py

# 7. 启动前端开发服务器
cd voice_calendar_frontend
npm install
npm run dev
```

### 6.3 访问地址

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost:5173 |
| 后端 API | http://localhost:5000 |
| FastAPI 文档 | http://localhost:5000/api/docs |

---

## 七、环境变量配置

在项目根目录创建 `.env` 文件（从 `.env.example` 复制），填入以下必填项：

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `ZHIPUAI_API_KEY` | 智谱 AI API Key（GLM-4 大模型） | **是** |
| `AMAP_API_KEY` | 高德地图 REST API Key | **是** |
| `XUNFEI_APPID` | 科大讯飞应用 ID（ASR + TTS 共用） | **是** |
| `XUNFEI_API_KEY` | 科大讯飞 API Key | **是** |
| `XUNFEI_API_SECRET` | 科大讯飞 API Secret | **是** |
| `JWT_SECRET_KEY` | JWT 签名密钥（生产环境务必修改） | 建议修改 |
| `DATABASE_URL` | 数据库连接串 | 默认 SQLite |
| `REDIS_URL` | Redis 地址 | 默认 localhost |

---

## 八、项目结构

```
voice-calendar/
├── .env.example                  # 环境变量模板
├── .gitignore
├── alembic.ini                   # Alembic 数据库迁移配置
├── alembic/                      # 迁移脚本
├── server.py                     # ★ 主入口 — Flask + SocketIO 服务器
├── backend_requirements.txt      # 后端 Python 依赖
├── docker-compose.yml            # Docker Compose (PostgreSQL + Redis)
│
├── app/                          # 后端应用包
│   ├── config.py                 # 配置管理 (pydantic-settings)
│   ├── database.py               # SQLAlchemy 引擎、会话工厂
│   ├── main.py                   # FastAPI 应用
│   ├── core/
│   │   ├── notifier.py           # 全局事件总线
│   │   └── security.py           # JWT、密码哈希、AES 加密
│   ├── models/                   # 数据模型 (8 个 ORM 模型)
│   ├── schemas/                  # Pydantic Schema
│   ├── services/
│   │   ├── agent.py              # ★ Agent 核心 — LLM 推理 + 工具编排
│   │   ├── tools.py              # ★ 工具定义 — 高德/12306/日程/会议
│   │   ├── tool_registry.py      # 并行工具调度器
│   │   ├── biz_dispatcher.py     # 业务意图分发
│   │   ├── schedule_service.py   # 日程 CRUD + 冲突检测
│   │   ├── meeting_service.py    # 在线会议创建
│   │   ├── task_service.py       # 任务管理
│   │   ├── ai_service.py         # AI 建议
│   │   └── output_aggregator.py  # L5 输出聚合
│   └── speech/
│       ├── asr.py                # 讯飞语音识别
│       └── tts.py                # 讯飞语音合成
│
└── voice_calendar_frontend/      # 前端 Vue 3 项目
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── components/           # 12 个 Vue 组件
        └── services/
            ├── socket.js         # Socket.IO 客户端
            └── store.js          # 状态管理
```

---

## 九、API 接口

### REST API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录（返回 JWT） |
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/profile` | 更新用户资料 |
| POST | `/api/auth/password` | 修改密码 |
| GET | `/api/events` | 查询日程列表 |

### WebSocket 事件

**客户端 → 服务端：**

| 事件 | 功能 |
|------|------|
| `voice_input` | 发送文字输入 |
| `start_recording` | 开始麦克风录音 |
| `stop_recording` | 停止录音 |

**服务端 → 客户端：**

| 事件 | 功能 |
|------|------|
| `asr_interim` / `asr_result` | 语音识别结果 |
| `agent_thinking` | Agent 正在思考 |
| `tool_call` / `tool_result` | 工具调用状态 |
| `transport_options` | 出行方式对比 |
| `train_options` | 高铁车次列表 |
| `conflict_detected` | 冲突检测结果 |
| `time_suggestion` | 空闲时段推荐 |
| `tts_text` | TTS 播报文本 |
| `event_created` / `event_updated` / `event_deleted` | 日程变更通知 |
| `session_end` | 本轮对话结束 |

---

## 十、License

MIT License
