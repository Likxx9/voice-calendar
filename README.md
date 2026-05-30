# 🎙️ 智能语音日历系统（Voice Calendar）

一个以语音交互为核心的智能日历管理工具，通过AI大模型实现自然语言理解、语义纠错、智能追问和冲突检测，帮助用户高效管理日程。

---

## 📋 项目概述

### 产品定位
面向商务人士、视障用户、车载驾驶场景的**智能语音日历管理系统**，通过语音交互实现日程的自然语言创建、查询、修改和删除。

### 核心价值
- **语音优先**：90%操作通过语音完成，解放双手
- **智能理解**：支持模糊时间表达、口语化表述
- **主动追问**：信息不全时智能引导补全
- **冲突检测**：创建前自动检测时间冲突
- **无障碍**：支持盲听模式，全程语音交互

---

## 🎯 解决的核心问题场景

### 场景一：时间异构与极端模糊时间（"听不懂、算不准"）

#### 问题描述
- 用户使用宽泛相对时间："下个月底"、"大后天晚上"
- 临界点歧义：23:59:30说"明天早上面试"，00:00:05收到请求时"明天"变成"今天"
- 周期性日程："隔周周三"、"每月第一个周一"

#### 解决方案

**1. 上下文时钟注入（Baseline Injecting）**
```python
# 前端在点击录音瞬间获取本地精确时间戳
current_time = "2026年5月30日 星期六 14:30:25"

# 发送给大模型时强制注入
system_prompt = f"""
当前绝对时间是 {current_time}，
请基于此基准计算相对时间。
例如：用户说"明天"，应计算为 {current_time + 1天}
"""
```

**2. 双层解析机制**
- **第一层**：LLM输出ISO 8601标准时间格式（如 `2026-06-01T14:30:00`）
- **第二层**：复杂周期性日程输出iCalendar RRULE格式
```python
# 简单事件
event_time = "2026-06-01T14:30:00"

# 周期性事件
rrule = "RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY=WE"  # 隔周周三
```

**3. 时区锁定（TZ-Locking）**
```python
# 前端捕获设备时区
timezone = "Asia/Shanghai"  # UTC+8

# 创建事件时统一携带时区
event = {
    "start_time": "2026-06-01T14:30:00+08:00",
    "timezone": "Asia/Shanghai"
}
```

---

### 场景二：语音识别同音字与噪音污染（"听错字、存错词"）

#### 问题描述
- STT将人名/地点识别错误："和张总在丽思卡尔顿吃饭" → "和赃总在历史卡儿顿吃饭"
- 口语化废话干扰："呃…那个…你帮我记一下吧，应该是…"

#### 解决方案

**1. LLM语义纠偏与降噪层**
```python
# 原始STT文本
raw_text = "呃那个和赃总在历史卡儿顿吃饭"

# 语义清洗Prompt
clean_prompt = """
请对以下语音识别文本进行语义清洗：
1. 去除口语化填充词（呃、那个、嗯等）
2. 修正明显的同音字错误
3. 保持原意不变

输入：{raw_text}
输出：
"""

# 清洗后
cleaned_text = "和张总在丽思卡尔顿吃饭"
```

**2. 业务字典关联（RAG）**
```python
# 用户联系人字典
address_book = {
    "张总": ["张总", "赃总", "张总经理"],
    "丽思卡尔顿": ["丽思卡尔顿", "历史卡儿顿", "丽思卡尔顿酒店"]
}

# 模糊匹配与实体修复
def fuzzy_match(text, dictionary):
    for canonical, variants in dictionary.items():
        for variant in variants:
            if variant in text:
                text = text.replace(variant, canonical)
    return text
```

---

### 场景三：关键要素缺失（"话没说全"）

#### 问题描述
- 只说了事件，没说时间："提醒我交房租"
- 只说了时间，没说做什么："明天下午两点帮我留个空"

#### 解决方案

**1. 基于会话状态机的智能追问**
```python
# 事件JSON Schema定义
event_schema = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "事件标题"},
        "start_time": {"type": "string", "format": "date-time", "description": "开始时间"},
        "end_time": {"type": "string", "format": "date-time", "description": "结束时间"},
        "location": {"type": "string", "description": "地点"},
        "participants": {"type": "array", "items": {"type": "string"}, "description": "参与者"}
    },
    "required": ["title", "start_time"]  # 必填字段
}

# 当必要参数缺失时，触发追问
def check_missing_fields(event_data):
    missing = []
    if not event_data.get("title"):
        missing.append("事件标题")
    if not event_data.get("start_time"):
        missing.append("开始时间")
    return missing
```

**2. 对话上下文继承**
```python
# 多轮对话状态管理
conversation_state = {
    "session_id": "abc123",
    "history": [
        {"role": "user", "content": "提醒我明天开会"},
        {"role": "assistant", "content": "请问几点开始？"},
        {"role": "user", "content": "下午两点"}
    ],
    "current_draft": {
        "title": "开会",
        "start_time": "2026-05-31T14:00:00"
    }
}

# 合并对话上下文
def merge_context(history, new_input):
    # 自动提取"下午两点"并合并到current_draft
    merged = extract_time_from_context(new_input, history)
    return merged
```

---

### 场景四：日程时间冲突与时区重叠（"分身乏术"）

#### 问题描述
- 创建的日程与现有日程时间冲突
- 跨时区差旅场景下时间显示错乱

#### 解决方案

**1. 原子化函数组合（Tool Chaining）**
```python
# LangChain工具链定义
tools = [
    Tool(name="query_calendar", func=query_calendar),
    Tool(name="create_event", func=create_event),
    Tool(name="update_event", func=update_event)
]

# Agent执行流程
async def handle_create_request(user_input):
    # Step 1: 解析用户意图，提取时间
    parsed = await llm.parse_intent(user_input)
    
    # Step 2: 查询时间冲突
    conflicts = await query_calendar(
        start=parsed.start_time,
        end=parsed.end_time
    )
    
    # Step 3: 根据冲突结果决策
    if conflicts:
        return {
            "action": "conflict_detected",
            "conflicts": conflicts,
            "suggestions": generate_alternatives(conflicts)
        }
    else:
        # Step 4: 无冲突，创建事件
        event = await create_event(parsed)
        return {"action": "event_created", "event": event}
```

**2. 冲突检测SQL**
```sql
-- PostgreSQL TSTZRANGE重叠检测
SELECT * FROM calendar_events 
WHERE user_id = %s 
AND tstzrange(start_time, end_time) && 
    tstzrange(%s, %s);  -- && 为重叠运算符
```

**3. 时区转换处理**
```python
from datetime import datetime
import pytz

def normalize_to_utc(local_time, timezone_str):
    """将本地时间转换为UTC"""
    local_tz = pytz.timezone(timezone_str)
    local_dt = local_tz.localize(datetime.fromisoformat(local_time))
    return local_dt.astimezone(pytz.utc)

def display_in_local(utc_time, target_timezone):
    """将UTC时间转换为目标时区显示"""
    utc_dt = datetime.fromisoformat(utc_time)
    target_tz = pytz.timezone(target_timezone)
    return utc_dt.astimezone(target_tz)
```

---

### 场景五：离线场景与网络不稳定

#### 问题描述
- 网络断开时无法使用语音功能
- 网络恢复后数据同步冲突

#### 解决方案

**1. IndexedDB离线队列**
```typescript
// 前端离线操作队列
interface OfflineOperation {
    id: string;
    type: 'create' | 'update' | 'delete';
    entity: 'event' | 'task';
    data: any;
    timestamp: number;
    syncStatus: 'pending' | 'syncing' | 'synced';
}

// 操作入队
function enqueueOperation(operation: OfflineOperation) {
    indexedDB.put('offline_queue', operation);
}

// 网络恢复时批量同步
async function syncPendingOperations() {
    const pending = await getAllPending();
    for (const op of pending) {
        await syncToServer(op);
        await markSynced(op.id);
    }
}
```

**2. 乐观更新策略**
```typescript
// 先更新本地，再同步服务器
async function createEvent(event) {
    // 1. 立即更新本地UI
    calendarStore.addEvent(event);
    
    // 2. 尝试同步服务器
    try {
        await api.createEvent(event);
    } catch (error) {
        // 3. 失败则加入离线队列
        offlineQueue.enqueue({
            type: 'create',
            entity: 'event',
            data: event
        });
    }
}
```

---

### 场景六：多轮对话状态管理

#### 问题描述
- 用户意图在多轮对话中发生变化
- 上下文丢失导致误解

#### 解决方案

**1. LangGraph状态机**
```python
from langgraph.graph import StateGraph, END

# 定义状态节点
class ConversationState(TypedDict):
    user_input: str
    intent: str
    extracted_entities: dict
    missing_fields: list
    event_draft: dict

# 构建状态图
workflow = StateGraph(ConversationState)

workflow.add_node("parse_intent", parse_intent)
workflow.add_node("extract_entities", extract_entities)
workflow.add_node("check_completeness", check_completeness)
workflow.add_node("ask_clarification", ask_clarification)
workflow.add_node("check_conflict", check_conflict)
workflow.add_node("create_event", create_event)

# 定义边
workflow.add_edge("parse_intent", "extract_entities")
workflow.add_edge("extract_entities", "check_completeness")

# 条件分支
workflow.add_conditional_edges(
    "check_completeness",
    lambda state: "complete" if not state["missing_fields"] else "incomplete",
    {
        "complete": "check_conflict",
        "incomplete": "ask_clarification"
    }
)

workflow.add_edge("check_conflict", "create_event")
workflow.add_edge("ask_clarification", "parse_intent")  # 循环追问

# 编译并执行
app = workflow.compile()
result = await app.ainvoke({"user_input": "提醒我明天开会"})
```

---

## 🏗️ 核心模块解耦架构

### 系统分层架构

```
┌─────────────────────────────────────────────────────────────┐
│                      前端展示层 (Client Layer)                │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 日历视图  │ │ 语音交互  │ │ 对话管理  │ │ 设置管理  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ WebSocket
┌─────────────────────────────────────────────────────────────┐
│                    网关层 (Gateway Layer)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │ 连接管理  │ │ 消息路由  │ │ 鉴权校验  │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    AI中枢层 (AI Core Layer)                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ 语义理解  │ │ 时间解析  │ │ 冲突检测  │ │ 会话管理  │      │
│  │ (LLM)   │ │ (LLM)   │ │ (SQL)   │ │ (Redis)  │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    数据层 (Data Layer)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                   │
│  │PostgreSQL│ │  Redis   │ │ IndexedDB│                   │
│  │ (日历)   │ │ (会话)   │ │ (离线)   │                   │
│  └──────────┘ └──────────┘ └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 模块职责划分

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **M1: 语音感知** | 音频采集、VAD断句、TTS播放 | 麦克风流 | 音频分片/文本 |
| **M2: 网关通信** | WebSocket管理、心跳重连 | 音频分片 | 结构化消息 |
| **M3: 语义理解** | 意图识别、实体提取、纠偏降噪 | 原始文本 | 结构化意图 |
| **M4: 状态机** | 多轮对话、追问引导、冲突协商 | 意图+上下文 | 决策/行动 |
| **M5: 日历管理** | 事件CRUD、冲突检测、视图渲染 | 事件数据 | 日历视图 |
| **M6: 离线同步** | 离线队列、增量同步、冲突解决 | 本地操作 | 同步状态 |

### 接口契约定义

```typescript
// M1 -> M2: 音频数据
interface AudioChunk {
    sessionId: string;
    sequence: number;
    data: ArrayBuffer;  // 16kHz 16bit PCM
    isFinal: boolean;
}

// M2 -> M3: 转写结果
interface TranscriptionResult {
    text: string;
    confidence: number;
    language: string;
    isPartial: boolean;
}

// M3 -> M4: 语义输出
interface SemanticOutput {
    intent: IntentType;  // create_event | query_event | delete_event | ...
    entities: {
        title?: string;
        startTime?: string;
        endTime?: string;
        location?: string;
        participants?: string[];
    };
    confidence: number;
    rawText: string;
    cleanedText: string;
}

// M4 -> M5: 事件操作
interface EventOperation {
    action: 'create' | 'update' | 'delete';
    eventId?: string;
    data: CalendarEvent;
    conflictCheck: boolean;
}
```

---

## 🛠️ 技术栈

### 前端技术栈
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | ^3.5.34 | 前端框架（Composition API） |
| TypeScript | ~6.0.2 | 类型系统 |
| Vite | ^8.0.12 | 构建工具 |
| Pinia | ^3.0.4 | 状态管理 |
| Vue Router | ^4.6.4 | 路由管理 |
| Web Audio API | - | 音频采集与播放 |
| Canvas API | - | 波形可视化 |

### 后端技术栈
| 技术 | 用途 |
|------|------|
| Python 3.11+ | 后端语言 |
| FastAPI | Web框架 |
| WebSocket | 实时通信 |
| LangChain/LangGraph | LLM编排 |
| 讯飞/SenseVoice | 语音识别 (云端) |
| FunASR/Paraformer | 语音识别 (离线) |
| PostgreSQL | 日历数据存储 |
| Redis | 会话状态缓存 |
| SQLAlchemy | ORM |

### AI模型
| 模型 | 用途 |
|------|------|
| Qwen-2.5-7B/14B | 语义理解、意图识别 |
| SenseVoice/FunASR | 语音转文本 |
| 火山引擎/ChatTTS | 文本转语音 |

---

## 📁 项目结构

```
voice-calendar/
├── frontend/                    # 前端Vue 3应用
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   ├── composables/         # 组合式函数
│   │   ├── modules/             # 业务模块组件
│   │   │   ├── sensory/         # M1: 语音感知
│   │   │   ├── gateway/         # M2: 网关通信
│   │   │   ├── semantic/        # M3: 语义展现
│   │   │   ├── stateMachine/    # M4: 状态机
│   │   │   ├── calendar/        # M5: 日历管理
│   │   │   └── sync/            # M6: 同步监控
│   │   ├── stores/              # Pinia状态
│   │   ├── types/               # 类型定义
│   │   └── styles/              # 样式体系
│   └── package.json
│
├── backend/                     # 后端FastAPI应用
│   ├── app/
│   │   ├── api/                 # API路由
│   │   ├── core/                # 核心配置
│   │   ├── models/              # 数据模型
│   │   ├── services/            # 业务服务
│   │   │ ├── llm_service.py     # LLM交互
│   │   │ ├── stt_service.py     # 语音识别
│   │   │ ├── calendar_service.py # 日历操作
│   │   │ └── session_service.py # 会话管理
│   │   └── websocket/           # WebSocket处理
│   ├── alembic/                 # 数据库迁移
│   └── requirements.txt
│
└── docker-compose.yml           # 容器编排
```

---

## 🚀 快速开始

### 环境要求
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### 1. 启动后端
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```

### 3. 访问应用
- 前端：http://localhost:5173
- 后端API：http://localhost:8000/docs
- WebSocket：ws://localhost:8000/api/v1/voice/stream

---

## 📊 核心算法

### 时间解析算法
```python
def parse_relative_time(text: str, reference_time: datetime) -> datetime:
    """
    解析相对时间表达
    输入: "明天下午三点", reference_time=2026-05-30 14:00:00
    输出: 2026-05-31 15:00:00
    """
    # 1. LLM提取时间实体
    time_entities = llm.extract_time_entities(text)
    
    # 2. 基于参考时间计算绝对时间
    absolute_time = calculate_absolute(time_entities, reference_time)
    
    # 3. 格式化为ISO 8601
    return absolute_time.isoformat()
```

### 冲突检测算法
```sql
-- PostgreSQL时间范围重叠检测
SELECT 
    id, title, start_time, end_time,
    tstzrange(start_time, end_time) && 
    tstzrange(%s, %s) as has_conflict
FROM calendar_events
WHERE user_id = %s 
  AND deleted_at IS NULL
HAVING has_conflict = true;
```

### 语义纠错算法
```python
def semantic_correction(raw_text: str, context: dict) -> str:
    """
    语义纠偏：结合上下文和业务字典
    """
    # 1. 去除口语化填充词
    cleaned = remove_fillers(raw_text)
    
    # 2. LLM语义理解
    corrected = llm.correct_with_context(
        text=cleaned,
        address_book=context.get('address_book', {}),
        history=context.get('history', [])
    )
    
    return corrected
```

---

## 🧪 测试场景

### 场景1：模糊时间创建
```
用户："提醒我下周三下午开会"
系统：[解析时间] 2026-06-03T14:00:00
系统：[检查冲突] 无冲突
系统：[创建事件] ✅ 已创建"开会"，时间：下周三14:00
```

### 场景2：信息不全追问
```
用户："提醒我交房租"
系统：[检测缺失] 缺少时间
系统：[追问] 请问什么时候交房租？
用户："月底"
系统：[合并信息] 标题：交房租，时间：2026-05-31
系统：[创建事件] ✅ 已创建"交房租"，时间：月底
```

### 场景3：冲突检测
```
用户："明天下午两点开会"
系统：[查询日历] 发现已有"产品评审会"（14:00-15:00）
系统：[冲突提示] 您明天14:00已有"产品评审会"
系统：[提供方案] 1. 改到15:00 2. 改到后天 3. 强制创建
用户："改到15:00"
系统：[更新时间] ✅ 已创建"开会"，时间：明天15:00
```

### 场景4：语义纠错
```
用户："和赃总在历史卡儿顿吃饭"
系统：[语义清洗] 和张总在丽思卡尔顿吃饭
系统：[联系人匹配] 张总 → 张总经理
系统：[创建事件] ✅ 已创建"和张总经理在丽思卡尔顿酒店吃饭"
```

---

## 📝 待办事项

- [ ] 完成后端FastAPI框架搭建
- [ ] 实现WebSocket实时通信
- [ ] 集成SenseVoice/FunASR语音识别
- [ ] 集成Qwen-2.5大模型
- [ ] 实现PostgreSQL数据库设计
- [ ] 实现Redis会话状态管理
- [ ] 完成前后端联调
- [ ] 编写单元测试和集成测试
- [ ] 部署Docker容器化方案

---

## 📄 License

MIT License

---

## 🤝 贡献

欢迎提交Issue和Pull Request！
