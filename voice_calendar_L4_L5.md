# 语音日历 — L4 工具执行层 & L5 输出层

> **VoiCal · 语音交互引擎末端模块**
> 版本：v1.0 · 国内云服务集成方案
> 适用层级：L4（工具执行·并行调度）· L5（结果聚合·TTS·Barge-in）

---

## 目录

1. [模块定位与依赖关系](#1-模块定位与依赖关系)
2. [L4 工具执行层](#2-l4-工具执行层)
   - 2.1 [工具注册表设计](#21-工具注册表设计)
   - 2.2 [联网搜索工具](#22-联网搜索工具)
   - 2.3 [日历读写工具](#23-日历读写工具)
   - 2.4 [地图导航工具](#24-地图导航工具)
   - 2.5 [提醒推送工具](#25-提醒推送工具)
   - 2.6 [并行调度实现](#26-并行调度实现)
   - 2.7 [L4 接口定义](#27-l4-接口定义)
   - 2.8 [L4 开发里程碑](#28-l4-开发里程碑)
3. [L5 输出层](#3-l5-输出层)
   - 3.1 [结果聚合与响应生成](#31-结果聚合与响应生成)
   - 3.2 [TTS 语音合成](#32-tts-语音合成)
   - 3.3 [Barge-in 打断机制](#33-barge-in-打断机制)
   - 3.4 [场景模式适配](#34-场景模式适配)
   - 3.5 [日历写入确认流程](#35-日历写入确认流程)
   - 3.6 [L5 接口定义](#36-l5-接口定义)
   - 3.7 [L5 开发里程碑](#37-l5-开发里程碑)
4. [L4 → L5 联调规范](#4-l4--l5-联调规范)
5. [性能指标与监控](#5-性能指标与监控)
6. [成本估算](#6-成本估算)
7. [附录：完整代码示例](#7-附录完整代码示例)

---

## 1. 模块定位与依赖关系

### 1.1 在整体架构中的位置

```
L3 Agent 编排层（已完成）
        │
        │  TaskGroup[]（DAG 执行计划）
        ▼
┌───────────────────────────────────────────────────┐
│  L4 工具执行层                                     │  ← 本文档
│                                                   │
│  ┌──────────┐ ┌──────────┐ ┌────────┐ ┌────────┐ │
│  │ 联网搜索  │ │ 日历 API │ │ 地图   │ │ 提醒   │ │
│  │ 百度/    │ │ 钉钉/    │ │ 高德   │ │ 极光   │ │
│  │ Tavily   │ │ 企业微信 │ │ 地图   │ │ 推送   │ │
│  └──────────┘ └──────────┘ └────────┘ └────────┘ │
│                                                   │
│            并行调度器（Promise.allSettled）          │
└───────────────────────┬───────────────────────────┘
                        │  ToolResult[]
                        ▼
┌───────────────────────────────────────────────────┐
│  L5 输出层                                        │  ← 本文档
│                                                   │
│  ┌────────────┐ ┌──────────┐ ┌───────────────┐   │
│  │ 结果聚合   │ │ TTS 合成  │ │ Barge-in 检测 │   │
│  │ 响应生成   │ │ 讯飞/    │ │ 场景适配      │   │
│  │           │ │ 阿里云   │ │               │   │
│  └────────────┘ └──────────┘ └───────────────┘   │
└───────────────────────┬───────────────────────────┘
                        │
              语音播报 + 日历写入 + 通知推送
```

### 1.2 模块间数据契约

| 接口 | 格式 | 说明 |
|------|------|------|
| L3 → L4 | `ExecutionPlan`（DAG） | 含工具列表、并行/串行标记、上下文 |
| L4 → L5 | `ToolResult[]` | 每个工具的返回数据、状态、耗时 |
| L5 → 用户 | 语音流（PCM/Opus）+ 结构化确认 | TTS 播报 + 可选的界面更新 |

---

## 2. L4 工具执行层

### 2.1 工具注册表设计

所有工具实现统一的 `Tool` 接口，由注册表管理，支持运行时动态注册和按名查找：

```typescript
// tools/tool-registry.ts

export interface Tool<P = any, R = any> {
    name:        string;
    description: string;
    schema:      ToolSchema;        // JSON Schema，供 L3 Agent LLM 工具调用使用
    execute(params: P, ctx: ToolContext): Promise<ToolResult<R>>;
    timeout:     number;            // 超时毫秒数
    retries:     number;            // 最大重试次数
}

export interface ToolContext {
    groupId:    string;             // 任务组 ID（隔离上下文）
    userId:     string;
    sessionId:  string;
    store:      Map<string, unknown>; // 组内共享 KV
}

export interface ToolResult<T = unknown> {
    toolName:   string;
    success:    boolean;
    data?:      T;
    error?:     string;
    latencyMs:  number;
    needsConfirm?: boolean;         // 写操作前是否需要用户确认
    confirmText?:  string;          // 确认话术
}

export interface ToolSchema {
    type:       'object';
    properties: Record<string, { type: string; description: string; required?: boolean }>;
    required:   string[];
}

export class ToolRegistry {
    private tools = new Map<string, Tool>();

    register(tool: Tool): void {
        this.tools.set(tool.name, tool);
    }

    get(name: string): Tool {
        const tool = this.tools.get(name);
        if (!tool) throw new Error(`未注册的工具: ${name}`);
        return tool;
    }

    /** 导出所有工具的 Schema，供 L3 LLM 工具调用时使用 */
    exportSchemas(): Array<{ name: string; description: string; parameters: ToolSchema }> {
        return Array.from(this.tools.values()).map(t => ({
            name:        t.name,
            description: t.description,
            parameters:  t.schema,
        }));
    }

    listNames(): string[] {
        return Array.from(this.tools.keys());
    }
}

/** 全局注册表单例 */
export const registry = new ToolRegistry();
```

### 2.2 联网搜索工具

#### 2.2.1 国内搜索服务选型

| 服务 | 适用场景 | 免费额度 | 单价 | 说明 |
|------|---------|---------|------|------|
| **百度搜索 API** | 中文内容、国内活动 | 1000次/天 | ¥0.03/次 | 结果最贴合国内用户 |
| **必应搜索 API（中国版）** | 综合搜索 | 1000次/月 | ¥0.05/次 | 结构化结果好 |
| **Tavily AI Search** | AI 摘要、结构化返回 | 1000次/月 | $0.005/次 | 已预处理摘要，减少二次解析 |
| **SerpAPI（百度引擎）** | 国内场景主备 | 100次/月 | $0.05/次 | 支持切换百度/必应 |

**策略**：Tavily 作主引擎（返回结构化摘要，减少 LLM 二次解析成本），百度搜索 API 作备引擎（国内活动信息更完整）。

#### 2.2.2 Tavily 搜索工具实现

```typescript
// tools/search/tavily-search.ts
import { Tool, ToolContext, ToolResult, registry } from '../tool-registry';

export interface SearchParams {
    query:      string;             // 搜索关键词
    maxResults: number;             // 最大结果数（1-10）
    searchDepth?: 'basic' | 'advanced';  // advanced 更准确但慢
    includeDomains?: string[];      // 限定搜索域名
}

export interface SearchResultItem {
    title:   string;
    url:     string;
    content: string;                // Tavily 预处理摘要
    score:   number;                // 相关度分
}

export interface SearchResult {
    query:    string;
    results:  SearchResultItem[];
    answer?:  string;               // Tavily AI 综合答案
}

class TavilySearchTool implements Tool<SearchParams, SearchResult> {
    name        = 'web_search';
    description = '联网搜索外部信息，适合查询活动时间、场馆地址、票务等实时数据';
    timeout     = 6000;
    retries     = 2;

    schema = {
        type: 'object' as const,
        properties: {
            query:      { type: 'string',  description: '搜索关键词，应简洁具体' },
            maxResults: { type: 'number',  description: '返回结果数，默认 5' },
        },
        required: ['query'],
    };

    private readonly API_KEY = process.env.TAVILY_API_KEY!;
    private readonly BASE_URL = 'https://api.tavily.com/search';

    async execute(params: SearchParams, ctx: ToolContext): Promise<ToolResult<SearchResult>> {
        const start = Date.now();
        try {
            const body = {
                api_key:      this.API_KEY,
                query:        params.query,
                search_depth: params.searchDepth || 'advanced',
                max_results:  params.maxResults || 5,
                include_answer: true,           // 获取 AI 综合答案
                include_raw_content: false,
                include_domains: params.includeDomains || [],
                // 中文内容优化参数
                include_answer_context: true,
            };

            const response = await fetch(this.BASE_URL, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify(body),
                signal:  AbortSignal.timeout(this.timeout),
            });

            if (!response.ok) {
                throw new Error(`Tavily HTTP ${response.status}`);
            }

            const data = await response.json();

            const result: SearchResult = {
                query:   params.query,
                results: data.results.map((r: any) => ({
                    title:   r.title,
                    url:     r.url,
                    content: r.content,
                    score:   r.score,
                })),
                answer: data.answer,
            };

            // 写入组内共享上下文，供后续工具使用
            ctx.store.set('search_result', result);

            return {
                toolName:  this.name,
                success:   true,
                data:      result,
                latencyMs: Date.now() - start,
            };
        } catch (err: any) {
            return {
                toolName:  this.name,
                success:   false,
                error:     err.message,
                latencyMs: Date.now() - start,
            };
        }
    }
}

/** 百度搜索 API 备用实现 */
class BaiduSearchTool implements Tool<SearchParams, SearchResult> {
    name        = 'web_search_baidu';
    description = '百度搜索备用引擎，国内活动和政务信息更全面';
    timeout     = 5000;
    retries     = 2;

    schema = {
        type: 'object' as const,
        properties: {
            query:      { type: 'string',  description: '搜索关键词' },
            maxResults: { type: 'number',  description: '最大结果数' },
        },
        required: ['query'],
    };

    private readonly API_KEY    = process.env.BAIDU_SEARCH_API_KEY!;
    private readonly CUSTOM_ID  = process.env.BAIDU_SEARCH_CUSTOM_ID!;
    // 百度定制搜索 API 地址
    private readonly BASE_URL   = 'https://aip.baidubce.com/rest/2.0/customsearch/siteSearch';

    async execute(params: SearchParams, ctx: ToolContext): Promise<ToolResult<SearchResult>> {
        const start = Date.now();
        try {
            const token = await this.getToken();
            const url = `${this.BASE_URL}?access_token=${token}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({
                    query:       params.query,
                    customMeta:  this.CUSTOM_ID,
                    pn:          '1',
                    rn:          String(params.maxResults || 5),
                }).toString(),
                signal: AbortSignal.timeout(this.timeout),
            });

            const data = await response.json();
            const results: SearchResultItem[] = (data.result || []).map((r: any) => ({
                title:   r.title,
                url:     r.url,
                content: r.desc || '',
                score:   0.8,
            }));

            return {
                toolName:  this.name,
                success:   true,
                data:      { query: params.query, results },
                latencyMs: Date.now() - start,
            };
        } catch (err: any) {
            return {
                toolName:  this.name,
                success:   false,
                error:     err.message,
                latencyMs: Date.now() - start,
            };
        }
    }

    private async getToken(): Promise<string> {
        // 与百度 UNIT 共用 Access Token（见 L2 文档）
        return process.env.BAIDU_ACCESS_TOKEN || '';
    }
}

// 注册工具
registry.register(new TavilySearchTool());
registry.register(new BaiduSearchTool());
```

#### 2.2.3 搜索结果结构化提取

搜索结果返回后，需要用 LLM 或规则提取结构化字段（活动时间、地址等）：

```typescript
// tools/search/search-extractor.ts

export interface EventInfo {
    name?:      string;
    startDate?: string;         // ISO 8601
    endDate?:   string;
    venue?:     string;
    city?:      string;
    ticketUrl?: string;
    price?:     string;
    source:     string;         // 来源 URL
    confidence: number;
}

export class SearchExtractor {
    /**
     * 从搜索结果中提取活动信息
     * 优先使用 Tavily AI answer，降级到规则提取
     */
    extractEventInfo(result: SearchResult): EventInfo | null {
        // 优先使用 Tavily AI 综合答案
        if (result.answer) {
            const extracted = this.extractFromText(result.answer, result.results[0]?.url || '');
            if (extracted.confidence > 0.7) return extracted;
        }

        // 遍历各条结果，取最高置信度
        let best: EventInfo | null = null;
        for (const item of result.results) {
            const extracted = this.extractFromText(item.content, item.url);
            if (!best || extracted.confidence > best.confidence) {
                best = extracted;
            }
        }
        return best;
    }

    private extractFromText(text: string, source: string): EventInfo {
        const info: EventInfo = { source, confidence: 0 };

        // 日期提取（国内常见格式）
        const datePattern = /(\d{4})年(\d{1,2})月(\d{1,2})(?:日|号)?(?:\s*[-至~到]\s*(\d{1,2})(?:日|号)?)?/g;
        const dateMatches = [...text.matchAll(datePattern)];
        if (dateMatches.length > 0) {
            const m = dateMatches[0];
            info.startDate = `${m[1]}-${m[2].padStart(2,'0')}-${m[3].padStart(2,'0')}`;
            if (m[4]) {
                info.endDate = `${m[1]}-${m[2].padStart(2,'0')}-${m[4].padStart(2,'0')}`;
            }
            info.confidence += 0.35;
        }

        // 场馆提取
        const venuePattern = /(?:举办地点|展馆|场馆|地址|举办城市)?[：:]?\s*([^\n，。,]{3,20}(?:中心|展馆|广场|会展|大厦|体育馆|剧院|博览中心))/;
        const venueMatch = text.match(venuePattern);
        if (venueMatch) {
            info.venue = venueMatch[1].trim();
            info.confidence += 0.2;
        }

        // 城市提取
        const cityPattern = /(?:在|于)?(北京|上海|广州|深圳|杭州|成都|重庆|武汉|西安|南京|苏州|天津|青岛|厦门|宁波)/;
        const cityMatch = text.match(cityPattern);
        if (cityMatch) {
            info.city = cityMatch[1];
            info.confidence += 0.15;
        }

        // 活动名称提取（通常在标题中）
        if (text.length > 0) {
            info.name = text.split(/[。\n]/)[0].slice(0, 30).trim();
            info.confidence += 0.1;
        }

        return info;
    }
}
```

### 2.3 日历读写工具

#### 2.3.1 国内日历服务选型

| 平台 | API 类型 | 免费额度 | 适用场景 |
|------|---------|---------|---------|
| **钉钉开放平台** | REST API + Webhook | 免费 | 企业钉钉用户 |
| **企业微信** | REST API | 免费 | 企业微信用户 |
| **Google Calendar** | REST API | 免费（个人） | 个人用户国际化 |
| **Microsoft Graph（Outlook）** | REST API | 免费 | 企业 365 用户 |

采用**多适配器模式**，通过统一接口屏蔽各平台差异：

#### 2.3.2 日历适配器接口

```typescript
// tools/calendar/calendar-adapter.ts

export interface CalendarEvent {
    id?:          string;
    title:        string;
    startTime:    string;           // ISO 8601
    endTime:      string;
    isAllDay?:    boolean;
    location?:    string;
    description?: string;
    attendees?:   Attendee[];
    recurrence?:  string;           // iCal RRULE
    reminders?:   Reminder[];
    platform:     CalendarPlatform;
}

export interface Attendee {
    name?:  string;
    email?: string;
    mobile?: string;
    status: 'accepted' | 'declined' | 'pending';
}

export interface Reminder {
    method:  'notification' | 'sms' | 'email';
    minutes: number;                // 提前多少分钟
}

export type CalendarPlatform = 'dingtalk' | 'wecom' | 'google' | 'outlook';

export interface ICalendarAdapter {
    platform:     CalendarPlatform;
    createEvent(event: CalendarEvent): Promise<string>;           // 返回事件 ID
    updateEvent(id: string, event: Partial<CalendarEvent>): Promise<void>;
    deleteEvent(id: string): Promise<void>;
    listEvents(startTime: string, endTime: string): Promise<CalendarEvent[]>;
    getFreeSlots(startTime: string, endTime: string, duration: number): Promise<string[]>;
}
```

#### 2.3.3 钉钉日历适配器

```typescript
// tools/calendar/dingtalk-adapter.ts
import crypto from 'crypto';

export class DingtalkCalendarAdapter implements ICalendarAdapter {
    platform = 'dingtalk' as const;

    private readonly APP_KEY    = process.env.DINGTALK_APP_KEY!;
    private readonly APP_SECRET = process.env.DINGTALK_APP_SECRET!;
    private readonly BASE_URL   = 'https://api.dingtalk.com/v1.0';
    private accessToken: string = '';
    private tokenExpiry: number = 0;

    /** 创建日历事件 */
    async createEvent(event: CalendarEvent): Promise<string> {
        const token = await this.getToken();
        const body = {
            summary:     event.title,
            description: event.description || '',
            start: {
                dateTime: event.startTime,
                timeZone: 'Asia/Shanghai',
            },
            end: {
                dateTime: event.endTime,
                timeZone: 'Asia/Shanghai',
            },
            location: event.location || '',
            // 参会人（钉钉使用 unionId）
            attendees: (event.attendees || []).map(a => ({
                id: a.email || '',  // 钉钉用 unionId，此处简化
            })),
            // 提醒设置
            reminders: (event.reminders || [{ method: 'notification', minutes: 15 }]).map(r => ({
                method:  r.method === 'notification' ? 'notification' : 'email',
                minutes: r.minutes,
            })),
            // 重复规则（iCal 格式）
            recurrence: event.recurrence ? {
                pattern: this.parseRRule(event.recurrence),
            } : undefined,
        };

        const response = await fetch(
            `${this.BASE_URL}/calendar/users/me/calendars/primary/events`,
            {
                method:  'POST',
                headers: {
                    'Content-Type':       'application/json',
                    'x-acs-dingtalk-access-token': token,
                },
                body: JSON.stringify(body),
            }
        );

        const data = await response.json();
        if (!response.ok) {
            throw new Error(`钉钉创建事件失败: ${data.message}`);
        }
        return data.id;
    }

    /** 查询空闲时段 */
    async getFreeSlots(
        startTime: string, endTime: string, durationMinutes: number,
    ): Promise<string[]> {
        const token = await this.getToken();
        const response = await fetch(
            `${this.BASE_URL}/calendar/users/me/query/freebusy`,
            {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-acs-dingtalk-access-token': token,
                },
                body: JSON.stringify({ timeMin: startTime, timeMax: endTime }),
            }
        );

        const data = await response.json();
        const busySlots: Array<{ start: string; end: string }> = data.busy || [];

        // 计算空闲时段
        return this.calcFreeSlots(startTime, endTime, busySlots, durationMinutes);
    }

    /** 查询时间范围内的日程列表 */
    async listEvents(startTime: string, endTime: string): Promise<CalendarEvent[]> {
        const token = await this.getToken();
        const params = new URLSearchParams({
            timeMin:    startTime,
            timeMax:    endTime,
            maxResults: '50',
        });

        const response = await fetch(
            `${this.BASE_URL}/calendar/users/me/calendars/primary/events?${params}`,
            { headers: { 'x-acs-dingtalk-access-token': token } }
        );

        const data = await response.json();
        return (data.items || []).map((item: any): CalendarEvent => ({
            id:        item.id,
            title:     item.summary,
            startTime: item.start?.dateTime || item.start?.date,
            endTime:   item.end?.dateTime   || item.end?.date,
            isAllDay:  !item.start?.dateTime,
            location:  item.location,
            platform:  'dingtalk',
        }));
    }

    async updateEvent(id: string, event: Partial<CalendarEvent>): Promise<void> {
        const token = await this.getToken();
        await fetch(
            `${this.BASE_URL}/calendar/users/me/calendars/primary/events/${id}`,
            {
                method:  'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'x-acs-dingtalk-access-token': token,
                },
                body: JSON.stringify({
                    summary:  event.title,
                    start:    event.startTime ? { dateTime: event.startTime, timeZone: 'Asia/Shanghai' } : undefined,
                    end:      event.endTime   ? { dateTime: event.endTime,   timeZone: 'Asia/Shanghai' } : undefined,
                    location: event.location,
                }),
            }
        );
    }

    async deleteEvent(id: string): Promise<void> {
        const token = await this.getToken();
        await fetch(
            `${this.BASE_URL}/calendar/users/me/calendars/primary/events/${id}`,
            {
                method:  'DELETE',
                headers: { 'x-acs-dingtalk-access-token': token },
            }
        );
    }

    /**
     * 计算空闲时段算法
     * 给定忙碌区间，找出满足指定时长的连续空闲窗口
     */
    private calcFreeSlots(
        rangeStart:  string,
        rangeEnd:    string,
        busy:        Array<{ start: string; end: string }>,
        minDuration: number,   // 分钟
    ): string[] {
        const start  = new Date(rangeStart).getTime();
        const end    = new Date(rangeEnd).getTime();
        const minMs  = minDuration * 60_000;
        const workHourStart = 9;  // 工作时间 9:00
        const workHourEnd   = 18; // 工作时间 18:00

        const sortedBusy = busy
            .map(b => ({ s: new Date(b.start).getTime(), e: new Date(b.end).getTime() }))
            .sort((a, b) => a.s - b.s);

        const freeSlots: string[] = [];
        let cursor = start;

        for (const slot of sortedBusy) {
            if (slot.s - cursor >= minMs) {
                // 找到足够长的空闲窗口
                const slotStart = new Date(cursor);
                const slotHour  = slotStart.getHours();
                // 只推荐工作时间内的空闲
                if (slotHour >= workHourStart && slotHour < workHourEnd) {
                    freeSlots.push(new Date(cursor).toISOString());
                }
            }
            cursor = Math.max(cursor, slot.e);
        }

        // 检查最后一段
        if (end - cursor >= minMs) {
            const slotStart = new Date(cursor);
            if (slotStart.getHours() >= workHourStart && slotStart.getHours() < workHourEnd) {
                freeSlots.push(new Date(cursor).toISOString());
            }
        }

        return freeSlots.slice(0, 5);  // 最多返回 5 个推荐时段
    }

    private parseRRule(rrule: string): any {
        // 将标准 iCal RRULE 格式转换为钉钉格式（简化实现）
        // RRULE:FREQ=WEEKLY;BYDAY=MO → { type: 'weekly', daysOfWeek: [1] }
        const freq = rrule.match(/FREQ=(\w+)/)?.[1];
        return { type: freq?.toLowerCase() || 'daily' };
    }

    private async getToken(): Promise<string> {
        if (this.accessToken && Date.now() < this.tokenExpiry) return this.accessToken;

        const response = await fetch('https://api.dingtalk.com/v1.0/oauth2/accessToken', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify({ appKey: this.APP_KEY, appSecret: this.APP_SECRET }),
        });
        const data = await response.json();
        this.accessToken = data.accessToken;
        this.tokenExpiry = Date.now() + data.expireIn * 1000 * 0.9;
        return this.accessToken;
    }
}
```

#### 2.3.4 日历工具 Tool 封装

```typescript
// tools/calendar/calendar-tool.ts

class CalendarReadTool implements Tool {
    name        = 'calendar_read';
    description = '读取用户日历，查询日程列表或空闲时段';
    timeout     = 3000;
    retries     = 3;

    schema = {
        type: 'object' as const,
        properties: {
            operation:  { type: 'string', description: 'list_events | get_free_slots' },
            startTime:  { type: 'string', description: 'ISO 8601 开始时间' },
            endTime:    { type: 'string', description: 'ISO 8601 结束时间' },
            duration:   { type: 'number', description: '所需空闲时长（分钟），get_free_slots 专用' },
        },
        required: ['operation', 'startTime', 'endTime'],
    };

    async execute(params: any, ctx: ToolContext): Promise<ToolResult> {
        const start   = Date.now();
        const adapter = this.getAdapter(ctx);
        try {
            let data: any;
            if (params.operation === 'list_events') {
                data = await adapter.listEvents(params.startTime, params.endTime);
            } else {
                data = await adapter.getFreeSlots(params.startTime, params.endTime, params.duration || 60);
            }
            ctx.store.set('calendar_result', data);
            return { toolName: this.name, success: true, data, latencyMs: Date.now() - start };
        } catch (err: any) {
            return { toolName: this.name, success: false, error: err.message, latencyMs: Date.now() - start };
        }
    }

    private getAdapter(ctx: ToolContext): ICalendarAdapter {
        // 根据用户绑定的平台选择适配器
        const platform = (ctx.store.get('calendar_platform') as CalendarPlatform) || 'dingtalk';
        const adapters: Record<CalendarPlatform, ICalendarAdapter> = {
            dingtalk: new DingtalkCalendarAdapter(),
            wecom:    new WeComCalendarAdapter(),      // 企业微信适配器（实现同上）
            google:   new GoogleCalendarAdapter(),
            outlook:  new OutlookCalendarAdapter(),
        };
        return adapters[platform];
    }
}

class CalendarWriteTool implements Tool {
    name        = 'calendar_write';
    description = '创建、修改或删除日历事件（需用户确认）';
    timeout     = 4000;
    retries     = 2;

    schema = {
        type: 'object' as const,
        properties: {
            operation:  { type: 'string', description: 'create | update | delete' },
            eventId:    { type: 'string', description: '事件 ID，update/delete 必填' },
            event:      { type: 'object', description: 'CalendarEvent 对象，create/update 必填' },
        },
        required: ['operation'],
    };

    async execute(params: any, ctx: ToolContext): Promise<ToolResult> {
        const start   = Date.now();
        const adapter = this.getAdapter(ctx);

        // 写操作需要 L5 层在播报后获得用户确认
        const confirmText = this.buildConfirmText(params);
        try {
            let data: any;
            if (params.operation === 'create') {
                data = { eventId: await adapter.createEvent(params.event) };
            } else if (params.operation === 'update') {
                await adapter.updateEvent(params.eventId, params.event);
                data = { eventId: params.eventId };
            } else {
                await adapter.deleteEvent(params.eventId);
                data = { deleted: true };
            }
            return {
                toolName:    this.name,
                success:     true,
                data,
                latencyMs:   Date.now() - start,
                needsConfirm: true,
                confirmText,
            };
        } catch (err: any) {
            return { toolName: this.name, success: false, error: err.message, latencyMs: Date.now() - start };
        }
    }

    private buildConfirmText(params: any): string {
        const op  = params.operation;
        const ev  = params.event;
        if (op === 'create') {
            return `为您创建日程「${ev?.title}」于 ${ev?.startTime ? new Date(ev.startTime).toLocaleString('zh-CN') : ''}，是否确认？`;
        }
        if (op === 'update') return `已更新日程，是否确认？`;
        return `已删除该日程，是否确认？`;
    }

    private getAdapter(ctx: ToolContext): ICalendarAdapter {
        const platform = (ctx.store.get('calendar_platform') as CalendarPlatform) || 'dingtalk';
        return new DingtalkCalendarAdapter(); // 简化，实际同上
    }
}

registry.register(new CalendarReadTool());
registry.register(new CalendarWriteTool());
```

### 2.4 地图导航工具

#### 2.4.1 高德地图 API 集成

高德地图开放平台是国内最主流的地图服务，拥有最全的 POI 数据和路线规划能力：

```typescript
// tools/maps/amap-tool.ts

export interface RouteParams {
    origin:      string;            // 出发地（地名或经纬度 "116.481028,39.989643"）
    destination: string;            // 目的地
    mode:        'driving' | 'transit' | 'walking' | 'riding';
    departTime?: string;            // 出发时间 ISO 8601（transit 预约出发使用）
}

export interface RouteResult {
    duration:    number;            // 预计时长（分钟）
    distance:    number;            // 距离（千米）
    summary:     string;            // 路线简述（如"京沪高速 → G1234"）
    steps:       RouteStep[];
    trainNo?:    string;            // 高铁/列车车次
    departTime?: string;            // 实际出发时间
    arriveTime?: string;            // 预计到达时间
}

export interface RouteStep {
    instruction: string;
    distance:    number;
    duration:    number;
}

class AMapRouteTool implements Tool<RouteParams, RouteResult> {
    name        = 'maps_route';
    description = '高德地图路线规划，支持驾车、公交、高铁、步行，返回时长和路线摘要';
    timeout     = 4000;
    retries     = 1;

    schema = {
        type: 'object' as const,
        properties: {
            origin:      { type: 'string', description: '出发地名称或经纬度' },
            destination: { type: 'string', description: '目的地名称或经纬度' },
            mode:        { type: 'string', description: 'driving|transit|walking|riding' },
            departTime:  { type: 'string', description: '出发时间 ISO 8601，可选' },
        },
        required: ['origin', 'destination', 'mode'],
    };

    private readonly API_KEY  = process.env.AMAP_API_KEY!;
    private readonly BASE_URL = 'https://restapi.amap.com/v3';

    async execute(params: RouteParams, ctx: ToolContext): Promise<ToolResult<RouteResult>> {
        const start = Date.now();
        try {
            // 步骤 1：地理编码（地名 → 经纬度）
            const [originCoord, destCoord] = await Promise.all([
                this.geocode(params.origin),
                this.geocode(params.destination),
            ]);

            // 步骤 2：路线规划
            const route = await this.planRoute(originCoord, destCoord, params);

            ctx.store.set('route_result', route);
            return { toolName: this.name, success: true, data: route, latencyMs: Date.now() - start };
        } catch (err: any) {
            return { toolName: this.name, success: false, error: err.message, latencyMs: Date.now() - start };
        }
    }

    /** 地理编码：地名 → 经纬度字符串 */
    private async geocode(address: string): Promise<string> {
        // 如果已是经纬度格式，直接返回
        if (/^[\d.]+,[\d.]+$/.test(address)) return address;

        const url = `${this.BASE_URL}/geocode/geo?address=${encodeURIComponent(address)}&key=${this.API_KEY}`;
        const res  = await fetch(url);
        const data = await res.json();

        if (data.status !== '1' || !data.geocodes?.length) {
            throw new Error(`高德地理编码失败：${address}`);
        }
        return data.geocodes[0].location;  // "经度,纬度"
    }

    /** 路线规划 */
    private async planRoute(
        origin: string, destination: string, params: RouteParams,
    ): Promise<RouteResult> {
        const apiMap: Record<string, string> = {
            driving: '/direction/driving',
            transit: '/direction/transit/integrated',
            walking: '/direction/walking',
            riding:  '/direction/bicycling',
        };
        const endpoint = apiMap[params.mode] || '/direction/driving';

        const queryParams = new URLSearchParams({
            origin,
            destination,
            key:    this.API_KEY,
            output: 'json',
            ...(params.departTime ? { time: this.toTimestamp(params.departTime) } : {}),
        });

        const url  = `${this.BASE_URL}${endpoint}?${queryParams}`;
        const res  = await fetch(url);
        const data = await res.json();

        if (data.status !== '1') {
            throw new Error(`高德路线规划失败: ${data.info}`);
        }

        return this.parseRouteResponse(data, params.mode);
    }

    private parseRouteResponse(data: any, mode: string): RouteResult {
        if (mode === 'transit') {
            const route = data.route?.transits?.[0];
            const segments = route?.segments || [];
            const trainSegment = segments.find((s: any) => s.bus?.buslines?.[0]?.type?.includes('高铁'));

            return {
                duration:   Math.round((route?.duration || 0) / 60),
                distance:   (route?.distance || 0) / 1000,
                summary:    this.buildTransitSummary(segments),
                steps:      [],
                trainNo:    trainSegment?.bus?.buslines?.[0]?.name,
                departTime: route?.segments?.[0]?.departure_stop?.time,
                arriveTime: route?.segments?.at(-1)?.arrival_stop?.time,
            };
        }

        const route = data.route?.paths?.[0];
        return {
            duration: Math.round((route?.duration || 0) / 60),
            distance: (route?.distance || 0) / 1000,
            summary:  route?.steps?.[0]?.road || '已规划路线',
            steps:    (route?.steps || []).slice(0, 5).map((s: any) => ({
                instruction: s.instruction,
                distance:    s.distance / 1000,
                duration:    Math.round(s.duration / 60),
            })),
        };
    }

    private buildTransitSummary(segments: any[]): string {
        return segments
            .map((s: any) => s.bus?.buslines?.[0]?.name || s.walking?.steps?.[0]?.road || '')
            .filter(Boolean)
            .join(' → ');
    }

    private toTimestamp(iso: string): string {
        return Math.floor(new Date(iso).getTime() / 1000).toString();
    }
}

registry.register(new AMapRouteTool());
```

### 2.5 提醒推送工具

#### 2.5.1 极光推送（JPush）集成

极光推送是国内占有率最高的移动推送服务，支持 iOS/Android 统一推送：

```typescript
// tools/notification/jpush-tool.ts
import crypto from 'crypto';

export interface PushParams {
    userId:    string;
    title:     string;
    content:   string;
    extras?:   Record<string, string>;     // 附加数据，如事件 ID
    schedule?: string;                     // 定时推送时间 ISO 8601
    silent?:   boolean;                    // 静默推送（不弹通知）
}

class JPushTool implements Tool<PushParams, { messageId: string }> {
    name        = 'push_notification';
    description = '发送 App 推送通知，支持即时和定时推送，用于日程提醒';
    timeout     = 3000;
    retries     = 3;

    schema = {
        type: 'object' as const,
        properties: {
            userId:   { type: 'string', description: '用户 ID' },
            title:    { type: 'string', description: '通知标题' },
            content:  { type: 'string', description: '通知内容' },
            schedule: { type: 'string', description: '定时发送时间 ISO 8601，不填则即时发送' },
        },
        required: ['userId', 'title', 'content'],
    };

    private readonly APP_KEY    = process.env.JPUSH_APP_KEY!;
    private readonly MASTER_SECRET = process.env.JPUSH_MASTER_SECRET!;
    private readonly BASE_URL   = 'https://api.jpush.cn/v3';

    async execute(params: PushParams, ctx: ToolContext): Promise<ToolResult<{ messageId: string }>> {
        const start = Date.now();
        try {
            const endpoint = params.schedule
                ? `${this.BASE_URL}/schedules`      // 定时推送
                : `${this.BASE_URL}/push`;           // 即时推送

            const body = params.schedule
                ? this.buildScheduleBody(params)
                : this.buildPushBody(params);

            const response = await fetch(endpoint, {
                method:  'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization:  this.buildAuth(),
                },
                body: JSON.stringify(body),
                signal: AbortSignal.timeout(this.timeout),
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(`极光推送失败: ${data.error?.message}`);
            }

            return {
                toolName:  this.name,
                success:   true,
                data:      { messageId: data.sendno || data.schedule_id || '' },
                latencyMs: Date.now() - start,
            };
        } catch (err: any) {
            // 降级到本地队列（离线场景兜底）
            await this.enqueueLocal(params);
            return {
                toolName:  this.name,
                success:   true,     // 降级后视为成功（本地队列会处理）
                data:      { messageId: `local_${Date.now()}` },
                latencyMs: Date.now() - start,
            };
        }
    }

    /** 即时推送 Body */
    private buildPushBody(params: PushParams) {
        return {
            platform:  'all',
            audience:  { alias: [params.userId] },  // 用 alias 映射用户
            notification: {
                alert: params.content,
                ios:   { title: params.title, extras: params.extras },
                android: {
                    title:    params.title,
                    alert:    params.content,
                    extras:   params.extras,
                    priority: 2,        // 高优先级
                },
            },
            options: {
                time_to_live:  86400,  // 离线消息保留 24h
                apns_production: process.env.NODE_ENV === 'production',
            },
        };
    }

    /** 定时推送 Body */
    private buildScheduleBody(params: PushParams) {
        return {
            cid:    `voical_${Date.now()}`,
            name:   params.title,
            enabled: true,
            trigger: {
                single: {
                    time: params.schedule,    // ISO 8601 → 极光格式自动转换
                },
            },
            push:   this.buildPushBody(params),
        };
    }

    /** 降级：写入本地 Redis 队列，由定时任务消费 */
    private async enqueueLocal(params: PushParams): Promise<void> {
        const redis = getRedisClient();
        await redis.zAdd('voical:push_queue', {
            score:  params.schedule
                ? new Date(params.schedule).getTime()
                : Date.now(),
            value:  JSON.stringify(params),
        });
    }

    /** Basic Auth：Base64(appKey:masterSecret) */
    private buildAuth(): string {
        return `Basic ${Buffer.from(`${this.APP_KEY}:${this.MASTER_SECRET}`).toString('base64')}`;
    }
}

registry.register(new JPushTool());
```

### 2.6 并行调度实现

```typescript
// tools/scheduler.ts

export class ToolScheduler {
    private readonly DEFAULT_TIMEOUT = 8000;

    /**
     * 按 DAG 执行计划并行/串行执行工具调用
     * @param plan - L3 Agent 生成的执行计划
     * @param ctx  - 隔离的任务组上下文
     */
    async execute(plan: ExecutionPlan, ctx: ToolContext): Promise<ToolResult[]> {
        const allResults: ToolResult[] = [];

        for (const step of plan.steps) {
            if (step.parallel && step.toolCalls.length > 1) {
                // 并行执行：所有工具同时发起，等待全部完成
                const results = await Promise.allSettled(
                    step.toolCalls.map(tc => this.executeOne(tc, ctx))
                );

                for (const result of results) {
                    if (result.status === 'fulfilled') {
                        allResults.push(result.value);
                        this.mergeContext(ctx, result.value);
                    } else {
                        allResults.push({
                            toolName:  '(unknown)',
                            success:   false,
                            error:     result.reason?.message || '未知错误',
                            latencyMs: 0,
                        });
                    }
                }
            } else {
                // 串行执行（有数据依赖）
                for (const tc of step.toolCalls) {
                    const result = await this.executeOne(tc, ctx);
                    allResults.push(result);
                    this.mergeContext(ctx, result);

                    // 串行失败时中止后续步骤
                    if (!result.success && step.failFast) {
                        return allResults;
                    }
                }
            }
        }

        return allResults;
    }

    /** 执行单个工具（含超时与重试） */
    private async executeOne(
        toolCall: ToolCall,
        ctx:      ToolContext,
    ): Promise<ToolResult> {
        const tool = registry.get(toolCall.name);
        let lastError: Error | null = null;

        for (let attempt = 0; attempt <= tool.retries; attempt++) {
            try {
                const result = await Promise.race([
                    tool.execute(toolCall.params, ctx),
                    this.timeout(tool.timeout || this.DEFAULT_TIMEOUT, toolCall.name),
                ]);
                return result;
            } catch (err: any) {
                lastError = err;
                if (attempt < tool.retries) {
                    // 指数退避
                    await this.sleep(200 * Math.pow(2, attempt));
                }
            }
        }

        return {
            toolName:  toolCall.name,
            success:   false,
            error:     lastError?.message || '超时',
            latencyMs: tool.timeout || this.DEFAULT_TIMEOUT,
        };
    }

    /** 将工具结果写入共享上下文，供后续步骤读取 */
    private mergeContext(ctx: ToolContext, result: ToolResult): void {
        if (result.success && result.data) {
            ctx.store.set(`result:${result.toolName}`, result.data);
        }
    }

    private timeout(ms: number, toolName: string): Promise<never> {
        return new Promise((_, reject) =>
            setTimeout(() => reject(new Error(`工具 ${toolName} 超时（${ms}ms）`)), ms)
        );
    }

    private sleep(ms: number) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

export interface ExecutionPlan {
    groupId: string;
    steps:   ExecutionStep[];
}

export interface ExecutionStep {
    stepIndex: number;
    parallel:  boolean;
    failFast:  boolean;
    toolCalls: ToolCall[];
}

export interface ToolCall {
    name:   string;
    params: Record<string, unknown>;
}
```

### 2.7 L4 接口定义

```typescript
// types/l4.ts

export interface IL4ToolLayer {
    initialize(): Promise<void>;
    execute(plan: ExecutionPlan, ctx: ToolContext): Promise<ToolResult[]>;
    getRegisteredTools(): string[];
}

export interface L4Config {
    enabledTools:   string[];           // 启用的工具列表
    calendarPlatform: CalendarPlatform; // 用户绑定的日历平台
    searchEngine:   'tavily' | 'baidu'; // 主搜索引擎
    maxParallelism: number;             // 最大并发工具数（建议 4）
    globalTimeout:  number;             // 全局超时（ms）
}
```

### 2.8 L4 开发里程碑

| 里程碑 | 周期 | 交付内容 | 验收标准 |
|--------|------|---------|---------|
| M1 工具注册表 | 第 1 周 | 注册表、统一接口、并行调度器骨架 | 工具可注册查找，调度器可顺序执行 |
| M2 搜索工具 | 第 1-2 周 | Tavily + 百度双引擎、结果提取 | 搜索漫展信息准确率 > 85%，P95 < 3s |
| M3 日历工具 | 第 2-3 周 | 钉钉适配器、读写 CRUD、空闲计算 | CRUD 成功率 > 99%，P95 < 1s |
| M4 地图工具 | 第 3 周 | 高德路线规划、地理编码、交通换乘 | 路线规划 P95 < 2s，公交/高铁解析正确 |
| M5 推送工具 | 第 3 周 | JPush 即时/定时推送、本地队列降级 | 推送成功率 > 99.5%，离线消息不丢失 |
| M6 并行调度 | 第 4 周 | 完整 DAG 执行、超时熔断、重试退避 | 并行工具执行时间 ≤ 最慢单工具耗时 |
| M7 联调测试 | 第 4 周 | L3→L4→L5 全链路打通 | 漫展返程示例完整 E2E 成功 |

---

## 3. L5 输出层

### 3.1 结果聚合与响应生成

L5 层接收 L4 工具的执行结果，合并多个工具输出，生成自然语言响应文本，再交给 TTS 合成播报。

#### 3.1.1 结果聚合器

```typescript
// output/result-aggregator.ts

export interface AggregatedResponse {
    text:         string;           // 用于 TTS 播报的自然语言文本
    displayText?: string;           // 用于界面展示的富文本（可含 Markdown）
    actions:      ResponseAction[]; // 待执行的动作（写日历、发通知等）
    needsConfirm: boolean;          // 是否需要用户语音确认
    confirmText?: string;           // 确认话术
}

export interface ResponseAction {
    type:    'calendar_write' | 'push_notification' | 'navigate';
    payload: unknown;
}

export class ResultAggregator {
    /**
     * 合并多个工具结果，生成统一响应
     * 使用 LLM 将结构化数据转为自然语言（调用 Claude API）
     */
    async aggregate(
        results:   ToolResult[],
        intent:    IntentType,
        ctx:       ToolContext,
    ): Promise<AggregatedResponse> {
        // 提取成功结果
        const successResults = results.filter(r => r.success);
        const failedTools    = results.filter(r => !r.success).map(r => r.toolName);

        // 检查是否有需要确认的写操作
        const pendingConfirm = results.find(r => r.needsConfirm);

        // 构建响应文本
        const text = await this.generateText(successResults, intent, failedTools, ctx);

        // 提取待执行动作
        const actions = this.extractActions(successResults);

        return {
            text,
            displayText: this.buildDisplayText(successResults, intent),
            actions,
            needsConfirm: !!pendingConfirm,
            confirmText:  pendingConfirm?.confirmText,
        };
    }

    /**
     * 用 LLM 将工具结果转为自然语言播报文本
     * 核心原则：简洁、口语化、播报时长 < 15 秒（约 150 字）
     */
    private async generateText(
        results:     ToolResult[],
        intent:      IntentType,
        failedTools: string[],
        ctx:         ToolContext,
    ): Promise<string> {
        // 简单场景用模板（快速路径，< 1ms）
        const template = this.applyTemplate(results, intent);
        if (template) return template;

        // 复杂场景用 LLM 生成（< 500ms）
        const systemPrompt = `你是一个语音助手，将工具执行结果转化为简洁的中文播报文本。
要求：
1. 口语化，适合 TTS 播报，不用 Markdown
2. 长度控制在 60-120 字之间
3. 突出最关键信息（时间、地点、结果）
4. 若有错误，礼貌说明并给出替代方案`;

        const userContent = `
意图：${intent}
工具结果：${JSON.stringify(results.map(r => ({ name: r.toolName, data: r.data })), null, 2)}
${failedTools.length > 0 ? `失败工具：${failedTools.join(', ')}` : ''}
请生成播报文本：`;

        const response = await fetch('https://api.anthropic.com/v1/messages', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model:      'claude-haiku-4-5',
                max_tokens: 300,
                messages: [{ role: 'user', content: userContent }],
                system:   systemPrompt,
            }),
        });

        const data = await response.json();
        return data.content?.[0]?.text || '处理完成，请查看日历。';
    }

    /** 模板快速路径（无需调用 LLM） */
    private applyTemplate(results: ToolResult[], intent: IntentType): string | null {
        const templates: Partial<Record<IntentType, (results: ToolResult[]) => string>> = {
            [IntentType.QUERY_DAY]: (results) => {
                const events = results.find(r => r.toolName === 'calendar_read')?.data as CalendarEvent[];
                if (!events?.length) return '今天暂无日程安排，时间完全空闲。';
                const count = events.length;
                const first = events[0];
                return `今天共有${count}个日程。${count === 1 ? `${this.formatTime(first.startTime)}的${first.title}。` : `第一个是${this.formatTime(first.startTime)}的${first.title}。`}`;
            },
            [IntentType.QUERY_FREE_SLOT]: (results) => {
                const slots = results.find(r => r.toolName === 'calendar_read')?.data as string[];
                if (!slots?.length) return '您今天的日程已排满，暂无空闲时段。';
                return `找到${slots.length}个空闲时段，推荐${this.formatTime(slots[0])}开始，您是否需要安排？`;
            },
        };

        const handler = templates[intent];
        return handler ? handler(results) : null;
    }

    private formatTime(iso: string): string {
        const d = new Date(iso);
        return `${d.getHours()}点${d.getMinutes() > 0 ? d.getMinutes() + '分' : ''}`;
    }

    private buildDisplayText(results: ToolResult[], intent: IntentType): string {
        return results.map(r => `**${r.toolName}**: ${JSON.stringify(r.data)}`).join('\n');
    }

    private extractActions(results: ToolResult[]): ResponseAction[] {
        return results
            .filter(r => r.toolName === 'calendar_write' && r.success)
            .map(r => ({ type: 'calendar_write' as const, payload: r.data }));
    }
}
```

### 3.2 TTS 语音合成

#### 3.2.1 国内 TTS 服务选型

| 服务 | 自然度（MOS） | 支持语音 | 免费额度 | 单价 | 特点 |
|------|------------|---------|---------|------|------|
| **讯飞语音合成** | 4.3 | 60+ | 50万字/天 | ¥0.02/千字 | 最自然，商务音色丰富 |
| **阿里云 TTS** | 4.1 | 40+ | 100万字/月 | ¥0.035/千字 | 稳定性高 |
| **百度语音合成** | 4.0 | 20+ | 50万字/天 | ¥0.02/千字 | 免费额度大 |
| **腾讯云 TTS** | 4.0 | 60+ | 10万字/月 | ¥0.06/千字 | 情感音色丰富 |

**策略**：讯飞为主引擎（自然度最高、商务音色专业），阿里云为备用（稳定性好），支持流式首包优化。

#### 3.2.2 讯飞 TTS 流式合成

```typescript
// output/tts/xunfei-tts.ts
import WebSocket from 'ws';
import crypto from 'crypto';
import { EventEmitter } from 'events';

export interface TTSParams {
    text:       string;
    voiceType?: string;   // 音色，见 §3.4 场景适配
    speed?:     number;   // 语速 0~100，默认 50
    volume?:    number;   // 音量 0~100，默认 80
    pitch?:     number;   // 音调 0~100，默认 50
    encoding?:  'raw' | 'lame' | 'speex-wb'; // 编码格式
}

export class XunfeiTTSClient extends EventEmitter {
    private readonly APPID      = process.env.XUNFEI_APPID!;
    private readonly API_KEY    = process.env.XUNFEI_API_KEY!;
    private readonly API_SECRET = process.env.XUNFEI_API_SECRET!;
    private readonly HOST       = 'tts-api.xfyun.cn';
    private readonly PATH       = '/v2/tts';

    /**
     * 流式合成：边合成边返回 PCM 数据
     * 发出 'data' 事件传递音频块，'end' 事件表示合成完成
     */
    synthesizeStream(params: TTSParams): void {
        const url = this.buildAuthUrl();
        const ws  = new WebSocket(url);
        const audioChunks: Buffer[] = [];

        ws.on('open', () => {
            const body = {
                common: { app_id: this.APPID },
                business: {
                    aue:   params.encoding || 'raw',    // raw = PCM 16bit
                    auf:   'audio/L16;rate=16000',
                    vcn:   params.voiceType || 'xiaoyan', // 音色
                    speed: params.speed  ?? 50,
                    volume: params.volume ?? 80,
                    pitch:  params.pitch  ?? 50,
                    tte:   'UTF8',
                    // SSML 支持：可插入停顿 <break time="500ms"/>
                },
                data: {
                    status: 2,                          // 2=最后一帧（TTS 不流式输入，一次发完）
                    text:   Buffer.from(params.text).toString('base64'),
                },
            };
            ws.send(JSON.stringify(body));
        });

        ws.on('message', (raw: Buffer) => {
            const msg = JSON.parse(raw.toString());
            if (msg.code !== 0) {
                this.emit('error', new Error(`讯飞 TTS 错误 ${msg.code}: ${msg.message}`));
                ws.close();
                return;
            }

            const audio = msg.data?.audio;
            if (audio) {
                const chunk = Buffer.from(audio, 'base64');
                audioChunks.push(chunk);
                this.emit('data', chunk);     // 流式推送，可在合成完成前开始播放
            }

            if (msg.data?.status === 2) {
                // 合成完毕
                const full = Buffer.concat(audioChunks);
                this.emit('end', full);
                ws.close();
            }
        });

        ws.on('error', (err) => {
            this.emit('error', err);
        });
    }

    /**
     * 非流式合成：等待完整音频返回
     * 适用于短文本（< 30 字）
     */
    async synthesize(params: TTSParams): Promise<Buffer> {
        return new Promise((resolve, reject) => {
            this.synthesizeStream(params);
            const chunks: Buffer[] = [];
            this.on('data',  (chunk: Buffer) => chunks.push(chunk));
            this.on('end',   () => resolve(Buffer.concat(chunks)));
            this.on('error', reject);
        });
    }

    /** 生成讯飞 TTS WebSocket 鉴权 URL */
    private buildAuthUrl(): string {
        const date = new Date().toUTCString();
        const signOrigin = `host: ${this.HOST}\ndate: ${date}\nGET ${this.PATH} HTTP/1.1`;
        const hmac = crypto.createHmac('sha256', this.API_SECRET);
        hmac.update(signOrigin);
        const signature   = hmac.digest('base64');
        const authOrigin  = `api_key="${this.API_KEY}", algorithm="hmac-sha256", headers="host date request-line", signature="${signature}"`;
        const authorization = Buffer.from(authOrigin).toString('base64');
        const params = new URLSearchParams({ authorization, date, host: this.HOST });
        return `wss://${this.HOST}${this.PATH}?${params}`;
    }
}
```

#### 3.2.3 阿里云 TTS 备用实现

```typescript
// output/tts/aliyun-tts.ts
import NLS from '@alicloud/nls-sdk';

export class AliyunTTSClient {
    async synthesize(text: string, voiceType = 'zhixiaobai'): Promise<Buffer> {
        const token    = await this.getToken();
        const synthesizer = new NLS.SpeechSynthesizer({
            url:     'wss://nls-gateway-cn-shanghai.aliyuncs.com/ws/v1',
            appkey:  process.env.ALIYUN_NLS_APP_KEY!,
            token,
            format:  'pcm',
            sampleRate: 16000,
            voice:   voiceType,
            speechRate:  0,          // 0=正常速度
            pitchRate:   0,
            volume:  100,
            enableSubtitle: false,
        });

        return new Promise((resolve, reject) => {
            const chunks: Buffer[] = [];
            synthesizer.on('data',     (d: Buffer) => chunks.push(d));
            synthesizer.on('completed', () => resolve(Buffer.concat(chunks)));
            synthesizer.on('failed',    (e: Error) => reject(e));
            synthesizer.start(text, true, 6000);
        });
    }

    private async getToken(): Promise<string> {
        // 复用 L1 的 Token 缓存机制
        return process.env.ALIYUN_NLS_TOKEN || '';
    }
}
```

#### 3.2.4 TTS 双引擎容灾路由

```typescript
// output/tts/tts-router.ts

export class TTSRouter {
    private xunfei = new XunfeiTTSClient();
    private aliyun = new AliyunTTSClient();
    private failCount = 0;
    private readonly FAIL_THRESHOLD   = 3;
    private readonly RECOVERY_INTERVAL = 60_000;
    private lastFailTime = 0;

    async synthesize(params: TTSParams): Promise<Buffer> {
        const useAliyun = (
            this.failCount >= this.FAIL_THRESHOLD &&
            Date.now() - this.lastFailTime < this.RECOVERY_INTERVAL
        );

        try {
            if (useAliyun) {
                return await this.aliyun.synthesize(params.text, params.voiceType);
            }
            return await this.xunfei.synthesize(params);
        } catch (err) {
            this.failCount++;
            this.lastFailTime = Date.now();
            if (!useAliyun) {
                return await this.aliyun.synthesize(params.text, params.voiceType);
            }
            throw err;
        }
    }

    /** 流式合成（优先讯飞） */
    synthesizeStream(params: TTSParams): EventEmitter {
        if (this.failCount < this.FAIL_THRESHOLD) {
            return this.xunfei.synthesizeStream(params), this.xunfei;
        }
        // 降级时用非流式打包返回
        const emitter = new EventEmitter();
        this.aliyun.synthesize(params.text)
            .then(buf => { emitter.emit('data', buf); emitter.emit('end', buf); })
            .catch(e  => emitter.emit('error', e));
        return emitter;
    }
}
```

### 3.3 Barge-in 打断机制

Barge-in 允许用户在 TTS 播报途中直接说话打断，无需等待播报结束，是高品质语音交互的关键体验。

```typescript
// output/barge-in/barge-in-detector.ts

export class BargeinDetector {
    private isPlaying   = false;
    private onBargein:  (() => void) | null = null;
    private audioPlayer: AudioPlayer | null = null;

    // 打断检测参数
    private readonly ENERGY_THRESHOLD   = 0.08;    // 能量阈值，超过则视为用户说话
    private readonly CONFIRM_FRAMES     = 3;        // 连续 N 帧超阈值才触发
    private consecutiveVoiceFrames      = 0;

    /**
     * TTS 开始播放时调用，启动打断检测
     */
    onPlayStart(player: AudioPlayer, onBargein: () => void): void {
        this.isPlaying  = true;
        this.audioPlayer = player;
        this.onBargein  = onBargein;
        this.consecutiveVoiceFrames = 0;
    }

    /**
     * 接收 L0 层实时传来的音频帧能量，判断是否触发打断
     * 由 L0 VAD 处理后每帧（20ms）调用一次
     */
    onAudioFrame(energyLevel: number): void {
        if (!this.isPlaying) return;

        if (energyLevel > this.ENERGY_THRESHOLD) {
            this.consecutiveVoiceFrames++;
            if (this.consecutiveVoiceFrames >= this.CONFIRM_FRAMES) {
                // 连续 3 帧（60ms）能量超阈 → 确认为用户说话 → 触发打断
                this.triggerBargein();
            }
        } else {
            this.consecutiveVoiceFrames = 0;
        }
    }

    private triggerBargein(): void {
        if (!this.isPlaying) return;

        // 1. 立即停止 TTS 播放
        this.audioPlayer?.stop();
        this.isPlaying = false;
        this.consecutiveVoiceFrames = 0;

        // 2. 触发打断回调（L0 开始重新录音）
        this.onBargein?.();

        console.log('[L5] Barge-in 触发，TTS 已中断');
    }

    onPlayEnd(): void {
        this.isPlaying  = false;
        this.audioPlayer = null;
        this.consecutiveVoiceFrames = 0;
    }
}

/** 音频播放器接口（Web/Native 平台各自实现） */
export interface AudioPlayer {
    play(pcm: Buffer): void;
    stop(): void;
    on(event: 'ended', listener: () => void): void;
}
```

### 3.4 场景模式适配

不同使用场景下，TTS 音色、语速、音量和播报详略需要差异化处理：

```typescript
// output/scene-adapter.ts

export type SceneMode = 'office' | 'driving' | 'meeting' | 'silent' | 'earphone';

export interface SceneConfig {
    voiceType:    string;     // 讯飞音色标识
    speed:        number;     // 0-100
    volume:       number;     // 0-100
    maxTextLen:   number;     // 播报文本最大字数
    useSummary:   boolean;    // 是否使用摘要模式（省略细节）
    enableBargein: boolean;   // 是否启用打断
}

const SCENE_CONFIGS: Record<SceneMode, SceneConfig> = {
    office: {
        voiceType:    'xiaoyan',     // 标准普通话女声
        speed:        55,
        volume:       75,
        maxTextLen:   120,
        useSummary:   false,
        enableBargein: true,
    },
    driving: {
        voiceType:    'aisjiuxu',    // 导航专用男声
        speed:        65,            // 略快，减少驾车分心时间
        volume:       90,            // 音量调高
        maxTextLen:   60,            // 极简播报
        useSummary:   true,
        enableBargein: true,
    },
    meeting: {
        voiceType:    'xiaoyan',
        speed:        50,
        volume:       40,            // 音量调低
        maxTextLen:   80,
        useSummary:   true,
        enableBargein: false,        // 会议中不用打断（以免误触发）
    },
    silent: {
        voiceType:    'xiaoyan',
        speed:        50,
        volume:       0,             // 静音，只走振动通知
        maxTextLen:   0,
        useSummary:   true,
        enableBargein: false,
    },
    earphone: {
        voiceType:    'aisxping',    // 耳机专属音色（更自然）
        speed:        58,
        volume:       85,
        maxTextLen:   150,
        useSummary:   false,
        enableBargein: true,
    },
};

export class SceneAdapter {
    private currentScene: SceneMode = 'office';

    /** 根据传感器/用户设置自动检测场景 */
    detectScene(context: {
        isConnectedToBluetooth?: boolean;
        isInMeeting?:            boolean;
        isPhoneSilent?:          boolean;
        isCarMode?:              boolean;
    }): SceneMode {
        if (context.isCarMode)              return 'driving';
        if (context.isInMeeting)            return 'meeting';
        if (context.isPhoneSilent)          return 'silent';
        if (context.isConnectedToBluetooth) return 'earphone';
        return 'office';
    }

    setScene(scene: SceneMode): void { this.currentScene = scene; }

    getConfig(): SceneConfig { return SCENE_CONFIGS[this.currentScene]; }

    /** 根据场景截断/精简播报文本 */
    adaptText(text: string): string {
        const config = this.getConfig();
        if (config.maxTextLen === 0) return '';    // 静音模式
        if (text.length <= config.maxTextLen) return text;

        // 超出字数：截取前 N 字 + 关键信息
        return text.slice(0, config.maxTextLen - 3) + '……';
    }

    getTTSParams(text: string): TTSParams {
        const config = this.getConfig();
        return {
            text:      this.adaptText(text),
            voiceType: config.voiceType,
            speed:     config.speed,
            volume:    config.volume,
        };
    }
}

/** 讯飞主要商务音色参考 */
export const XUNFEI_VOICES = {
    xiaoyan:    '小燕（标准女声，通用）',
    aisjiuxu:   '爱司旭（导航男声）',
    aisxping:   '爱司平（舒缓女声，耳机适用）',
    xiaofeng:   '小峰（标准男声）',
    aisjinger:  '爱司晶（情感女声）',
    xiaoqian:   '小倩（甜美女声）',
    aisbabyxu:  '爱司宝旭（儿童声）',
};
```

### 3.5 日历写入确认流程

写操作必须经过用户语音确认，避免误操作：

```typescript
// output/confirm-flow.ts

export type ConfirmState = 'pending' | 'confirmed' | 'cancelled' | 'timeout';

export class ConfirmationFlow {
    private pendingActions: ResponseAction[] = [];
    private state: ConfirmState = 'pending';
    private onConfirm: (() => void) | null = null;
    private onCancel:  (() => void) | null = null;

    private readonly TIMEOUT_MS = 10_000;  // 10 秒无响应自动取消
    private timeoutHandle: ReturnType<typeof setTimeout> | null = null;

    /**
     * 发起确认流程
     * @param actions     - 待确认的写操作
     * @param confirmText - TTS 播报的确认询问
     * @param ttsRouter   - TTS 引擎
     */
    async start(
        actions:     ResponseAction[],
        confirmText: string,
        ttsRouter:   TTSRouter,
    ): Promise<ConfirmState> {
        this.pendingActions = actions;
        this.state = 'pending';

        // 播报确认话术
        await ttsRouter.synthesize({ text: confirmText });

        return new Promise((resolve) => {
            this.onConfirm = () => resolve('confirmed');
            this.onCancel  = () => resolve('cancelled');

            // 超时自动取消
            this.timeoutHandle = setTimeout(() => {
                this.state = 'timeout';
                resolve('timeout');
            }, this.TIMEOUT_MS);
        });
    }

    /**
     * 接收用户语音意图回调（由 L2 NLU 分析后调用）
     */
    receiveUserIntent(intent: IntentType): void {
        if (this.state !== 'pending') return;
        if (this.timeoutHandle) clearTimeout(this.timeoutHandle);

        if (intent === IntentType.CONFIRM) {
            this.state = 'confirmed';
            this.onConfirm?.();
        } else if (intent === IntentType.CANCEL) {
            this.state = 'cancelled';
            this.onCancel?.();
        }
    }

    getPendingActions(): ResponseAction[] { return this.pendingActions; }
}
```

### 3.6 L5 接口定义

```typescript
// types/l5.ts

export interface IL5OutputLayer {
    initialize(config: L5Config): Promise<void>;
    process(
        toolResults: ToolResult[],
        intent:      IntentType,
        ctx:         ToolContext,
    ): Promise<OutputResult>;
    setScene(scene: SceneMode): void;
    stopPlayback(): void;         // 外部触发停止（Barge-in）
}

export interface OutputResult {
    text:         string;         // 播报文本
    audioBuffer?: Buffer;         // PCM 音频（非流式场景使用）
    actions:      ResponseAction[];
    confirmState?: ConfirmState;  // 若需要确认，此字段有值
    latencyMs:    number;
}

export interface L5Config {
    defaultScene:     SceneMode;
    enableBargein:    boolean;
    confirmTimeout:   number;     // 确认超时（ms）
    ttsEngine:        'xunfei' | 'aliyun';
    streamingEnabled: boolean;    // 流式合成边合成边播放
}
```

### 3.7 L5 开发里程碑

| 里程碑 | 周期 | 交付内容 | 验收标准 |
|--------|------|---------|---------|
| M1 结果聚合 | 第 1 周 | ResultAggregator、模板快速路径 | 主要意图模板覆盖率 100%，P95 < 5ms |
| M2 讯飞 TTS | 第 1-2 周 | WebSocket 流式合成、鉴权、双引擎路由 | MOS 评分 ≥ 4.0，首包延迟 < 300ms |
| M3 场景适配 | 第 2 周 | 5 种场景音色/语速配置、自动检测逻辑 | 驾车/办公室场景切换验证通过 |
| M4 Barge-in | 第 2-3 周 | 能量检测、TTS 立即停止、回调触发 | Barge-in 响应延迟 < 100ms，误触率 < 1% |
| M5 确认流程 | 第 3 周 | 写操作确认、超时取消、意图回调 | 确认/取消逻辑 100% 覆盖，超时兜底正确 |
| M6 LLM 响应生成 | 第 3 周 | Claude API 接入、复杂场景文本生成 | 生成文本自然度评分 ≥ 4/5，P95 < 600ms |
| M7 联调测试 | 第 4 周 | L4→L5 完整链路 | 漫展返程场景完整播报，E2E 延迟 < 4s |

---

## 4. L4 → L5 联调规范

### 4.1 完整调用链示例（漫展返程场景）

```typescript
// pipeline/tool-output-pipeline.ts

export class ToolOutputPipeline {
    private scheduler  = new ToolScheduler();
    private aggregator = new ResultAggregator();
    private ttsRouter  = new TTSRouter();
    private sceneAdapter = new SceneAdapter();
    private bargein    = new BargeinDetector();
    private confirm    = new ConfirmationFlow();

    async run(plan: ExecutionPlan, intent: IntentType, ctx: ToolContext): Promise<void> {
        // Step 1: L4 并行执行工具
        const toolResults = await this.scheduler.execute(plan, ctx);
        console.log(`[L4] 工具执行完成，成功 ${toolResults.filter(r => r.success).length}/${toolResults.length}`);

        // Step 2: L5 聚合结果，生成响应
        const response = await this.aggregator.aggregate(toolResults, intent, ctx);

        // Step 3: 场景适配 → TTS 参数
        const ttsParams = this.sceneAdapter.getTTSParams(response.text);

        if (ttsParams.text) {
            // Step 4: 流式 TTS 播报
            const player = this.createAudioPlayer();
            this.bargein.onPlayStart(player, () => {
                // 用户打断 → 重新进入 L0 录音流程
                this.onBargeinTriggered();
            });

            const tts = this.ttsRouter.synthesizeStream(ttsParams);
            tts.on('data', (chunk: Buffer) => player.play(chunk));
            tts.on('end', async () => {
                this.bargein.onPlayEnd();

                // Step 5: 若有待确认写操作，发起确认流程
                if (response.needsConfirm && response.confirmText) {
                    const state = await this.confirm.start(
                        response.actions, response.confirmText, this.ttsRouter,
                    );

                    if (state === 'confirmed') {
                        // 执行写操作（create/update/delete）
                        await this.executeActions(response.actions);
                        await this.ttsRouter.synthesize({ text: '好的，已为您写入日历。' });
                    } else {
                        await this.ttsRouter.synthesize({ text: '已取消，日历未做更改。' });
                    }
                }
            });
        }
    }

    private async executeActions(actions: ResponseAction[]): Promise<void> {
        for (const action of actions) {
            if (action.type === 'push_notification') {
                const pushTool = registry.get('push_notification');
                await pushTool.execute(action.payload as any, this.createCtx());
            }
        }
    }

    private onBargeinTriggered(): void {
        // 通知 L0 层重新开始录音
        process.nextTick(() => {
            EventBus.emit('voical:barge_in');
        });
    }

    private createAudioPlayer(): AudioPlayer { return new WebAudioPlayer(); }
    private createCtx(): ToolContext {
        return { groupId: 'system', userId: '', sessionId: '', store: new Map() };
    }
}
```

### 4.2 错误处理矩阵

| 场景 | 触发条件 | L4 处理 | L5 播报 |
|------|---------|---------|---------|
| 搜索工具超时 | Tavily/百度均超时 | 返回 success=false | "抱歉，网络查询超时，已记录请求稍后重试" |
| 日历 API 鉴权失败 | Token 过期 | 刷新 Token 重试 | 静默处理，无需播报 |
| 创建日程冲突 | 时间段已有日程 | 返回冲突信息 | "该时段已有「XX」日程，是否选择其他时间？" |
| TTS 讯飞故障 | WebSocket 断开 | 切换阿里云 | 静默切换，播报继续 |
| 全部工具失败 | 网络中断 | 写入离线队列 | "当前网络不稳定，操作已缓存，网络恢复后自动执行" |
| 用户确认超时 | 10s 无响应 | — | "未收到确认，操作已取消" |

---

## 5. 性能指标与监控

### 5.1 端到端延迟目标（P95）

| 阶段 | 目标 | 说明 |
|------|------|------|
| L4 单工具（本地日历） | < 500ms | CRUD 操作 |
| L4 单工具（联网搜索） | < 3000ms | Tavily advanced |
| L4 并行工具（搜索+日历） | < 3000ms | 取最慢工具耗时 |
| L5 结果聚合（模板路径） | < 10ms | 快速路径 |
| L5 结果聚合（LLM 路径） | < 600ms | Claude Haiku |
| L5 TTS 首包延迟 | < 300ms | 讯飞流式合成 |
| L5 Barge-in 响应 | < 100ms | 能量检测 → 停止播放 |
| L4+L5 完整端到端 | < 4500ms | 联网搜索场景 |
| L4+L5 完整端到端 | < 1500ms | 纯日历操作 |

### 5.2 监控指标埋点

```typescript
// monitoring/l4l5-metrics.ts
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('voical-l4-l5');

export const l4l5Metrics = {
    toolLatency:   meter.createHistogram('l4.tool_latency_ms'),
    toolSuccess:   meter.createCounter('l4.tool_success_total'),
    toolFailure:   meter.createCounter('l4.tool_failure_total'),
    ttsLatency:    meter.createHistogram('l5.tts_latency_ms'),
    bargeinCount:  meter.createCounter('l5.barge_in_total'),
    confirmRate:   meter.createCounter('l5.confirm_result_total'),
};
```

---

## 6. 成本估算

### 6.1 月度成本模型（100 DAU）

| 服务 | 用量 | 单价 | 月费用 |
|------|------|------|-------|
| Tavily 联网搜索 | 100人 × 2次/天 × 30天 = 6,000 次 | $0.005/次 | **¥220** |
| 百度搜索（备用，5%） | 300 次 | ¥0.03/次 | **¥9** |
| 钉钉日历 API | 免费 | — | **¥0** |
| 高德地图（路线规划） | 6,000 次 | 免费额度内 | **¥0** |
| 极光推送 | 100人 × 5次/天 × 30天 = 15,000 次 | 免费额度内 | **¥0** |
| 讯飞 TTS | 100人 × 5次/天 × 80字 × 30天 = 1,200,000 字 | 免费 50万/天，超出 ¥0.02/千字 | **¥0（免费额度内）** |
| Claude Haiku（响应生成） | 6,000 次 × 500 tokens | $0.00025/1K tokens | **¥55** |
| **合计** | | | **≈ ¥284/月** |

> L4/L5 层主要依赖免费额度，初期 100 DAU 月费极低，商业化后可与讯飞谈企业合同价格（通常较官网 6 折）。

---

## 7. 附录：完整代码示例

### 7.1 环境变量配置

```bash
# .env（新增 L4/L5 配置）
# L4 搜索
TAVILY_API_KEY=tvly-your_key
BAIDU_SEARCH_API_KEY=your_key
BAIDU_SEARCH_CUSTOM_ID=your_custom_id

# L4 日历
DINGTALK_APP_KEY=your_app_key
DINGTALK_APP_SECRET=your_app_secret

# L4 地图
AMAP_API_KEY=your_amap_key

# L4 推送
JPUSH_APP_KEY=your_jpush_key
JPUSH_MASTER_SECRET=your_master_secret

# L5 TTS（复用 L0/L1 讯飞配置）
# XUNFEI_APPID / XUNFEI_API_KEY / XUNFEI_API_SECRET

# L5 LLM 响应生成
ANTHROPIC_API_KEY=sk-ant-your_key
```

### 7.2 依赖清单

```json
{
  "dependencies": {
    "@alicloud/nls-sdk":     "^2.0.0",
    "ws":                    "^8.16.0",
    "@opentelemetry/api":    "^1.7.0"
  }
}
```

### 7.3 快速集成验证

```typescript
// scripts/test-l4-l5.ts

async function testL4L5() {
    // 初始化工具
    const ctx: ToolContext = {
        groupId:   'test_group',
        userId:    'test_user',
        sessionId: 'test_session',
        store:     new Map([['calendar_platform', 'dingtalk']]),
    };

    const scheduler = new ToolScheduler();

    // 测试 1：并行搜索 + 日历查询
    const parallelPlan: ExecutionPlan = {
        groupId: 'test_group',
        steps: [{
            stepIndex: 1, parallel: true, failFast: false,
            toolCalls: [
                { name: 'web_search',    params: { query: '2026杭州漫展时间', maxResults: 3 } },
                { name: 'calendar_read', params: { operation: 'get_free_slots',
                    startTime: '2026-10-01T00:00:00+08:00',
                    endTime:   '2026-10-10T00:00:00+08:00',
                    duration:  120 } },
            ],
        }],
    };

    console.log('[L4] 执行并行工具...');
    const results = await scheduler.execute(parallelPlan, ctx);
    console.log('[L4] 结果：', results.map(r => `${r.toolName}: ${r.success ? '成功' : '失败'} (${r.latencyMs}ms)`));

    // 测试 2：TTS 合成
    const ttsRouter = new TTSRouter();
    const sceneAdapter = new SceneAdapter();
    sceneAdapter.setScene('office');
    const ttsParams = sceneAdapter.getTTSParams(
        '2026年杭州漫展于10月3日至5日在杭州国际博览中心举办，已在您10月5日18点安排返程。'
    );
    console.log('[L5] TTS 参数：', ttsParams);
    const audio = await ttsRouter.synthesize(ttsParams);
    console.log(`[L5] TTS 合成完成，音频大小：${audio.length} bytes`);
}

testL4L5().catch(console.error);
```

---

*文档由 VoiCal 技术团队维护 · 高德地图 / 极光推送 / 讯飞 TTS 如有 API 更新，请同步修改对应章节*
