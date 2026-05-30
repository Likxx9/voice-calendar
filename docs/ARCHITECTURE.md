# 🏗️ 智能语音日历系统 - 架构设计文档

## 目录
1. [系统架构概述](#1-系统架构概述)
2. [核心模块解耦设计](#2-核心模块解耦设计)
3. [数据流设计](#3-数据流设计)
4. [API接口设计](#4-api接口设计)
5. [数据库设计](#5-数据库设计)
6. [部署架构](#6-部署架构)

---

## 1. 系统架构概述

### 1.1 架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户交互层                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   移动端     │  │   Web端     │  │   车载端     │  │   无障碍端   │  │
│  │  (iOS/Android)│ │  (Vue 3)   │  │  (Android)  │  │  (盲听模式)  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        网关层 (Gateway Layer)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │
│  │   Nginx     │  │   API       │  │  WebSocket  │                   │
│  │   反向代理   │  │   网关       │  │  长连接      │                   │
│  └─────────────┘  └─────────────┘  └─────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        服务层 (Service Layer)                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │   语音服务   │  │   AI服务    │  │  日历服务    │  │  用户服务    │  │
│  │  (STT/TTS)  │  │  (LLM)     │  │  (CRUD)     │  │  (Auth)     │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        数据层 (Data Layer)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ PostgreSQL  │  │   Redis     │  │  MinIO      │  │  ElasticSearch│ │
│  │  (主数据库)  │  │  (缓存)     │  │  (文件存储)  │  │  (搜索引擎)  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈选择

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue 3 + TypeScript | Composition API，高可维护性 |
| 后端 | Python FastAPI | 异步高性能，原生支持WebSocket |
| 数据库 | PostgreSQL | 支持TSTZRANGE，高效时间范围查询 |
| 缓存 | Redis | 会话状态管理，高性能KV存储 |
| AI模型 | Qwen-2.5-7B/14B | 中文语义理解，Function Calling |
| 语音识别 | Faster-Whisper | 高性能本地STT |
| 语音合成 | Edge-TTS | 微软TTS，高质量中文语音 |

---

## 2. 核心模块解耦设计

### 2.1 模块职责划分

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           M1: 语音感知模块                               │
│  职责：音频采集、VAD断句、TTS播放、触觉反馈                                │
│  输入：麦克风音频流                                                      │
│  输出：音频分片、播放状态                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           M2: 网关通信模块                               │
│  职责：WebSocket管理、心跳重连、消息路由、鉴权                             │
│  输入：音频分片、文本消息                                                 │
│  输出：结构化消息帧                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           M3: 语义理解模块                               │
│  职责：语音识别、语义清洗、意图识别、实体提取                              │
│  输入：原始文本                                                          │
│  输出：结构化语义输出                                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           M4: 状态机模块                                 │
│  职责：多轮对话、追问引导、冲突协商、上下文管理                            │
│  输入：语义输出 + 会话历史                                               │
│  输出：决策结果、行动指令                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           M5: 日历管理模块                               │
│  职责：事件CRUD、冲突检测、视图渲染、数据同步                              │
│  输入：事件操作指令                                                      │
│  输出：日历视图、操作结果                                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           M6: 离线同步模块                               │
│  职责：离线队列、增量同步、冲突解决、数据持久化                            │
│  输入：本地操作                                                          │
│  输出：同步状态                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块间接口契约

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
    intent: IntentType;
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

// M5 -> M6: 同步操作
interface SyncOperation {
    type: 'create' | 'update' | 'delete';
    entity: 'event' | 'task';
    data: any;
    timestamp: number;
}
```

### 2.3 解耦设计原则

1. **单一职责**：每个模块只负责一个核心功能
2. **接口隔离**：模块间通过明确定义的接口通信
3. **依赖倒置**：高层模块不依赖低层模块，都依赖抽象
4. **开闭原则**：对扩展开放，对修改关闭

---

## 3. 数据流设计

### 3.1 语音交互流程

```
用户说话
    │
    ▼
┌─────────────┐
│ M1: 音频采集 │
│ (16kHz PCM) │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M2: WebSocket│
│  传输音频    │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M3: STT识别  │
│ (Faster-Whisper)│
└─────────────┘
    │
    ▼
┌─────────────┐
│ M3: 语义清洗 │
│ (LLM纠错)   │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M3: 意图识别 │
│ (LLM理解)   │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M3: 实体提取 │
│ (时间/地点)  │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M4: 完整性   │
│  检查       │
└─────────────┘
    │
    ├── 缺失信息 ──> 追问用户 ──> 返回M1
    │
    ▼
┌─────────────┐
│ M4: 冲突检测 │
│ (查询日历)   │
└─────────────┘
    │
    ├── 有冲突 ──> 协商解决 ──> 返回M1
    │
    ▼
┌─────────────┐
│ M5: 创建事件 │
│ (写入数据库) │
└─────────────┘
    │
    ▼
┌─────────────┐
│ M1: TTS播报  │
│ (语音反馈)   │
└─────────────┘
```

### 3.2 时间解析流程

```
用户输入："提醒我下周三下午三点开会"
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 1: 注入参考时间                    │
│  当前时间: 2026-05-30 14:30:00 (周六)    │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 2: LLM提取时间实体                 │
│  - "下周三" -> 相对时间                   │
│  - "下午三点" -> 绝对时间点               │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 3: 计算绝对时间                    │
│  下周三 = 2026-06-03 (下周三)            │
│  下午三点 = 15:00:00                     │
│  合并: 2026-06-03T15:00:00              │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 4: 时区转换                        │
│  输入: Asia/Shanghai (UTC+8)            │
│  输出: 2026-06-03T15:00:00+08:00        │
│  UTC: 2026-06-03T07:00:00Z             │
└─────────────────────────────────────────┘
```

### 3.3 冲突检测流程

```
创建事件请求
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 1: 解析时间范围                    │
│  start_time: 2026-05-31 14:00:00        │
│  end_time: 2026-05-31 15:00:00          │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 2: 查询时间重叠事件                │
│  SQL: WHERE tstzrange(start, end)       │
│       && tstzrange(新事件start, 新事件end)│
└─────────────────────────────────────────┘
    │
    ├── 无冲突 ──> 直接创建
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 3: 生成冲突报告                    │
│  - 冲突事件列表                          │
│  - 时间重叠程度                          │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│  Step 4: 生成替代建议                    │
│  - 推荐1: 改到16:00 (会议结束后)         │
│  - 推荐2: 改到明天14:00                  │
│  - 推荐3: 强制创建                       │
└─────────────────────────────────────────┘
```

---

## 4. API接口设计

### 4.1 RESTful API

#### 日历事件管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/calendar/events | 获取事件列表 |
| GET | /api/calendar/events/:id | 获取单个事件 |
| POST | /api/calendar/events | 创建事件 |
| PUT | /api/calendar/events/:id | 更新事件 |
| DELETE | /api/calendar/events/:id | 删除事件 |
| GET | /api/calendar/conflicts | 检查时间冲突 |

#### 用户管理

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/register | 用户注册 |
| GET | /api/users/me | 获取当前用户 |
| PUT | /api/users/me | 更新用户信息 |

### 4.2 WebSocket API

#### 语音交互端点

```
ws://localhost:8000/ws/voice?session_id=xxx&user_id=xxx
```

#### 消息类型

| 类型 | 方向 | 说明 |
|------|------|------|
| audio_chunk | Client -> Server | 音频数据块 |
| text_input | Client -> Server | 文本输入 |
| interrupt | Client -> Server | 打断信号 |
| heartbeat | Client -> Server | 心跳 |
| transcription | Server -> Client | 转写结果 |
| semantic_output | Server -> Client | 语义理解结果 |
| clarification | Server -> Client | 追问请求 |
| conflict_detected | Server -> Client | 冲突检测结果 |
| event_created | Server -> Client | 事件创建成功 |
| tts | Server -> Client | TTS播放指令 |

### 4.3 消息帧格式

```json
{
    "type": "audio_chunk",
    "sessionId": "session_123456",
    "data": [0.1, 0.2, ...],
    "sequence": 1,
    "isFinal": false,
    "timestamp": "2026-05-30T14:30:00Z"
}
```

---

## 5. 数据库设计

### 5.1 ER图

```
┌─────────────────┐         ┌─────────────────┐
│     users       │         │ calendar_events  │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄───────│ user_id (FK)    │
│ email           │         │ id (PK)         │
│ nickname        │         │ title           │
│ avatar_url      │         │ description     │
│ address_book    │         │ location        │
│ default_timezone│         │ start_time      │
│ created_at      │         │ end_time        │
└─────────────────┘         │ timezone        │
                            │ recurrence_rule │
                            │ participants    │
                            │ is_all_day      │
                            │ color           │
                            │ reminder_minutes│
                            │ is_completed    │
                            │ created_at      │
                            │ deleted_at      │
                            └─────────────────┘
                                    │
                                    │ 1:N
                                    ▼
                            ┌─────────────────┐
                            │   todo_tasks    │
                            ├─────────────────┤
                            │ id (PK)         │
                            │ user_id (FK)    │
                            │ title           │
                            │ description     │
                            │ due_date        │
                            │ reminder_at     │
                            │ category        │
                            │ priority        │
                            │ related_event_id│
                            │ is_completed    │
                            │ created_at      │
                            └─────────────────┘
```

### 5.2 索引设计

```sql
-- 日历事件索引
CREATE INDEX idx_events_user_time 
ON calendar_events(user_id, start_time, end_time);

CREATE INDEX idx_events_timezone 
ON calendar_events(timezone);

CREATE INDEX idx_events_deleted 
ON calendar_events(deleted_at) 
WHERE deleted_at IS NOT NULL;

-- 任务索引
CREATE INDEX idx_tasks_user_due 
ON todo_tasks(user_id, due_date);

CREATE INDEX idx_tasks_priority 
ON todo_tasks(priority);
```

### 5.3 时区处理

```sql
-- 使用TSTZRANGE进行时间范围查询
SELECT * FROM calendar_events 
WHERE user_id = 'user_id'
  AND tstzrange(start_time, end_time) && 
      tstzrange('2026-05-31 14:00:00+08', '2026-05-31 15:00:00+08');
```

---

## 6. 部署架构

### 6.1 Docker Compose部署

```yaml
# docker-compose.yml
version: '3.8'
services:
  postgres:
    image: postgres:15-alpine
    # ...
  
  redis:
    image: redis:7-alpine
    # ...
  
  backend:
    build: ./backend
    # ...
  
  frontend:
    build: ./frontend
    # ...
  
  nginx:
    image: nginx:alpine
    # ...
```

### 6.2 Kubernetes部署

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: voice-calendar-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: voice-calendar-backend
  template:
    metadata:
      labels:
        app: voice-calendar-backend
    spec:
      containers:
      - name: backend
        image: voice-calendar-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### 6.3 监控与日志

```python
# 结构化日志
import logging
import json

logger = logging.getLogger("voice-calendar")

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }
        return json.dumps(log_entry)

# 性能监控
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('api_requests_total', 'Total API requests')
REQUEST_LATENCY = Histogram('api_request_latency_seconds', 'API request latency')
```

---

## 附录

### A. 环境变量说明

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| DATABASE_URL | 数据库连接URL | postgresql+asyncpg://... |
| REDIS_URL | Redis连接URL | redis://localhost:6379/0 |
| LLM_MODEL | LLM模型名称 | qwen-2.5-7b |
| STT_MODEL | STT模型名称 | faster-whisper-base |
| DEFAULT_TIMEZONE | 默认时区 | Asia/Shanghai |

### B. 错误码定义

| 错误码 | 说明 |
|--------|------|
| 400 | 请求参数错误 |
| 401 | 未授权 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 409 | 时间冲突 |
| 500 | 服务器内部错误 |

### C. 参考资料

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [PostgreSQL时区处理](https://www.postgresql.org/docs/current/datatype-datetime.html)
- [iCalendar标准 (RFC 5545)](https://tools.ietf.org/html/rfc5545)
- [ISO 8601时间格式](https://en.wikipedia.org/wiki/ISO_8601)
