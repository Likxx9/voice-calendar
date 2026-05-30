"""
Agent Service — Agent 编排层（技术文档 §3）

核心模块，包含：
- LLM 任务规划模块（§3.1）：接收 NLU 输出，进行深度语义推理，输出结构化任务计划
- 任务图构建模块（§3.2）：以 DAG 形式表达任务间的关联与依赖
- 并行调度器（§3.3）：按 DAG 并发发起工具调用，汇总结果
"""
import asyncio
import json
import time
import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

import httpx

from app.core.config import settings
from app.services.tool_registry import (
    ContextStore, ToolResult, ToolRegistry, tool_registry,
)
from app.services.search_service import WebSearchTool, search_service

logger = logging.getLogger("agent")


# ──────────────────────────────────────────────────────────────
# 数据结构（技术文档 §5.1 / §5.2）
# ──────────────────────────────────────────────────────────────

@dataclass
class Intent:
    id: str
    type: str  # CREATE / QUERY / MODIFY / DELETE / SEARCH / PLAN
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    raw_span: Optional[List[int]] = None


@dataclass
class ExecutionStep:
    step_index: int
    tool_calls: List[str]
    parallel: bool = False
    depends_on: List[int] = field(default_factory=list)


@dataclass
class TaskGroup:
    id: str
    intents: List[str]
    related: bool = True
    tools_needed: List[str] = field(default_factory=list)
    execution_plan: List[ExecutionStep] = field(default_factory=list)


@dataclass
class AgentInput:
    session_id: str
    utterance_text: str
    intents: List[Intent]
    dialog_history: List[Dict[str, Any]] = field(default_factory=list)
    user_profile: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentOutput:
    session_id: str
    task_groups: List[TaskGroup] = field(default_factory=list)
    results: Dict[str, Any] = field(default_factory=dict)
    fallback_response: Optional[str] = None
    planning_latency_ms: float = 0.0


# ──────────────────────────────────────────────────────────────
# System Prompt（技术文档 §3.1.2）
# ──────────────────────────────────────────────────────────────

AGENT_SYSTEM_PROMPT = """You are a calendar scheduling agent. Given user intents and entities,
output a structured task plan in JSON. Rules:
1. Group intents that share a semantic goal (same event/trip/person)
2. Mark unrelated intents as isolated (different task_group_id)
3. Identify which tools are needed for each group
4. Specify execution order within groups (parallel where possible)
5. Flag intents requiring web search with needs_search: true

Available tools: web_search, calendar_api, maps_api, reminder_service

Output format:
{
  "task_groups": [
    {
      "id": "group_1",
      "intents": ["intent_id_1", "intent_id_2"],
      "related": true,
      "tools": ["web_search", "calendar_api"],
      "execution_plan": [
        { "step": 1, "tools": ["web_search"], "parallel": false },
        { "step": 2, "tools": ["calendar_api"], "parallel": true }
      ]
    }
  ]
}"""

INTENT_EXTRACTION_PROMPT = """你是语音日历的语义理解模块。请从用户输入中提取所有意图和实体。

用户输入：{text}
当前时间：{reference_time}
用户时区：{timezone}

请以JSON格式输出：
{{
  "intents": [
    {{
      "id": "intent_1",
      "type": "CREATE|QUERY|MODIFY|DELETE|SEARCH|PLAN",
      "entities": {{
        "title": "事件标题",
        "start_time": "ISO 8601格式",
        "end_time": "ISO 8601格式",
        "location": "地点",
        "participants": ["参与者"],
        "search_query": "搜索关键词（仅SEARCH类型）"
      }},
      "confidence": 0.95
    }}
  ],
  "needs_llm_planning": true/false,
  "complexity": "simple|complex"
}}

规则：
- 如果用户说"明天"，基于当前时间计算具体日期
- 如果用户说"下午三点"，转换为15:00
- 如果没有明确结束时间，默认事件持续1小时
- 涉及搜索外部信息（活动时间、天气等）标记为SEARCH类型
- 多个意图时判断是否语义关联"""

SEARCH_QUERY_PROMPT = """Given user intent: "{intent_text}"
Generate an optimized search query for event information.
Rules:
- Include year explicitly
- Use official Chinese name if known
- Add authoritative source hint
- Never include personal user information

Output JSON: {{ "query": "优化后的搜索关键词" }}"""


# ──────────────────────────────────────────────────────────────
# Agent 服务
# ──────────────────────────────────────────────────────────────

class AgentService:
    """Agent 编排层核心服务"""

    def __init__(self):
        self._registry = tool_registry
        self._init_tools()

    def _init_tools(self):
        self._registry.register(WebSearchTool(search_service))

    # ──────────────────────────────────────────────────────────
    # 3.1.1 触发条件判断
    # ──────────────────────────────────────────────────────────

    def _needs_llm_planning(self, intents: List[Intent]) -> bool:
        """判断是否需要 LLM 规划（技术文档 §3.1.1）"""
        if len(intents) >= 2:
            return True
        if any(i.type == "SEARCH" for i in intents):
            return True
        for intent in intents:
            entities = intent.entities
            time_expr = entities.get("time_expression", "")
            if any(kw in str(time_expr) for kw in ["最近", "方便", "赶在", "之前", "之后"]):
                return True
        return False

    # ──────────────────────────────────────────────────────────
    # 3.1 LLM 任务规划
    # ──────────────────────────────────────────────────────────

    async def _call_llm(self, system_prompt: str, user_prompt: str, use_strong: bool = False) -> str:
        """调用 LLM（技术文档 §3.1.3 双模型路由）"""
        if settings.AGENT_LLM_PROVIDER == "anthropic" and settings.ANTHROPIC_API_KEY:
            return await self._call_anthropic(system_prompt, user_prompt, use_strong)
        return await self._call_local_llm(system_prompt, user_prompt)

    async def _call_anthropic(self, system_prompt: str, user_prompt: str, use_strong: bool) -> str:
        model = settings.AGENT_LLM_STRONG_MODEL if use_strong else settings.AGENT_LLM_FAST_MODEL
        async with httpx.AsyncClient(timeout=settings.TOOL_TIMEOUT_LLM_MS / 1000.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": 2048,
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": user_prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def _call_local_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用本地 LLM（Ollama / vLLM）"""
        try:
            async with httpx.AsyncClient(timeout=settings.TOOL_TIMEOUT_LLM_MS / 1000.0) as client:
                resp = await client.post(
                    f"{settings.LLM_BASE_URL}/v1/chat/completions",
                    json={
                        "model": settings.LLM_MODEL,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.1,
                        "max_tokens": 2048,
                    },
                    headers={"Authorization": f"Bearer {settings.LLM_API_KEY}"} if settings.LLM_API_KEY else {},
                )
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"Local LLM call failed: {e}")
            return ""

    # ──────────────────────────────────────────────────────────
    # 多意图提取
    # ──────────────────────────────────────────────────────────

    async def extract_intents(
        self,
        text: str,
        reference_time: datetime,
        timezone: str = "Asia/Shanghai",
    ) -> List[Intent]:
        """从用户输入中提取多个意图（技术文档 §3.1）"""
        user_prompt = INTENT_EXTRACTION_PROMPT.format(
            text=text,
            reference_time=reference_time.isoformat(),
            timezone=timezone,
        )

        raw = await self._call_llm(AGENT_SYSTEM_PROMPT, user_prompt)

        try:
            parsed = json.loads(self._extract_json(raw))
            intents = []
            for item in parsed.get("intents", []):
                intents.append(Intent(
                    id=item.get("id", f"intent_{len(intents)}"),
                    type=item.get("type", "CREATE"),
                    entities=item.get("entities", {}),
                    confidence=item.get("confidence", 0.8),
                ))
            return intents if intents else self._fallback_intent_extraction(text, reference_time)
        except (json.JSONDecodeError, KeyError):
            return self._fallback_intent_extraction(text, reference_time)

    def _fallback_intent_extraction(self, text: str, reference_time: datetime) -> List[Intent]:
        """规则兜底：单意图提取（技术文档 §3.1.1 规则路由）"""
        intent_type = "CREATE"
        keywords = {
            "CREATE": ["添加", "创建", "记录", "提醒", "加个", "安排"],
            "QUERY": ["查看", "查询", "显示", "看看", "什么时候"],
            "MODIFY": ["修改", "更改", "调整", "更新", "推迟", "推"],
            "DELETE": ["删除", "取消", "去掉", "移除"],
            "SEARCH": ["搜索", "搜一下", "查一下", "检索", "联网", "搜", "查"],
        }
        for itype, words in keywords.items():
            if any(w in text for w in words):
                intent_type = itype
                break

        return [Intent(
            id="intent_0",
            type=intent_type,
            entities={"raw_text": text},
            confidence=0.7,
        )]

    # ──────────────────────────────────────────────────────────
    # 3.2 任务图构建
    # ──────────────────────────────────────────────────────────

    async def build_task_groups(self, intents: List[Intent]) -> List[TaskGroup]:
        """构建任务组（技术文档 §3.2）"""
        if len(intents) <= 1:
            return [self._single_intent_group(intents[0])]

        if self._needs_llm_planning(intents):
            return await self._llm_plan_groups(intents)

        return self._rule_based_grouping(intents)

    def _single_intent_group(self, intent: Intent) -> TaskGroup:
        tools = self._resolve_tools(intent)
        steps = []
        search_tools = [t for t in tools if t == "web_search"]
        other_tools = [t for t in tools if t != "web_search"]

        step_idx = 0
        if search_tools:
            steps.append(ExecutionStep(step_index=step_idx, tool_calls=search_tools, parallel=False))
            step_idx += 1
        if other_tools:
            steps.append(ExecutionStep(
                step_index=step_idx,
                tool_calls=other_tools,
                parallel=len(other_tools) > 1,
                depends_on=[0] if search_tools else [],
            ))

        return TaskGroup(
            id="group_0",
            intents=[intent.id],
            related=True,
            tools_needed=tools,
            execution_plan=steps,
        )

    def _resolve_tools(self, intent: Intent) -> List[str]:
        mapping = {
            "CREATE": ["calendar_api"],
            "QUERY": ["calendar_api"],
            "MODIFY": ["calendar_api"],
            "DELETE": ["calendar_api"],
            "SEARCH": ["web_search", "calendar_api"],
            "PLAN": ["web_search", "calendar_api", "maps_api"],
        }
        return mapping.get(intent.type, ["calendar_api"])

    def _rule_based_grouping(self, intents: List[Intent]) -> List[TaskGroup]:
        """规则级意图关联判断（技术文档 §3.2.1）：实体重叠检测"""
        groups: List[TaskGroup] = []
        used = set()

        for i, a in enumerate(intents):
            if i in used:
                continue
            group_intents = [a.id]
            group_tools = set(self._resolve_tools(a))
            used.add(i)

            for j, b in enumerate(intents):
                if j in used:
                    continue
                if self._entities_overlap(a.entities, b.entities):
                    group_intents.append(b.id)
                    group_tools.update(self._resolve_tools(b))
                    used.add(j)

            tools = list(group_tools)
            search_tools = [t for t in tools if t == "web_search"]
            other_tools = [t for t in tools if t != "web_search"]
            steps = []
            idx = 0
            if search_tools:
                steps.append(ExecutionStep(step_index=idx, tool_calls=search_tools))
                idx += 1
            if other_tools:
                steps.append(ExecutionStep(
                    step_index=idx,
                    tool_calls=other_tools,
                    parallel=len(other_tools) > 1,
                    depends_on=[0] if search_tools else [],
                ))

            groups.append(TaskGroup(
                id=f"group_{len(groups)}",
                intents=group_intents,
                related=len(group_intents) > 1,
                tools_needed=tools,
                execution_plan=steps,
            ))

        return groups

    def _entities_overlap(self, a: Dict, b: Dict) -> bool:
        shared_keys = {"start_time", "end_time", "location", "participants"}
        for key in shared_keys:
            va, vb = a.get(key), b.get(key)
            if va and vb and va == vb:
                return True
        return False

    async def _llm_plan_groups(self, intents: List[Intent]) -> List[TaskGroup]:
        """LLM 级任务组规划（技术文档 §3.1.2）"""
        intents_desc = json.dumps(
            [{"id": i.id, "type": i.type, "entities": i.entities} for i in intents],
            ensure_ascii=False,
        )
        user_prompt = f"User intents:\n{intents_desc}\n\nPlan the task groups."
        use_strong = len(intents) > 3

        raw = await self._call_llm(AGENT_SYSTEM_PROMPT, user_prompt, use_strong=use_strong)

        try:
            parsed = json.loads(self._extract_json(raw))
            groups = []
            for g in parsed.get("task_groups", []):
                steps = []
                for s in g.get("execution_plan", []):
                    steps.append(ExecutionStep(
                        step_index=s.get("step", len(steps)),
                        tool_calls=s.get("tools", []),
                        parallel=s.get("parallel", False),
                    ))
                groups.append(TaskGroup(
                    id=g.get("id", f"group_{len(groups)}"),
                    intents=g.get("intents", []),
                    related=g.get("related", True),
                    tools_needed=g.get("tools", []),
                    execution_plan=steps,
                ))
            return groups if groups else self._rule_based_grouping(intents)
        except (json.JSONDecodeError, KeyError):
            return self._rule_based_grouping(intents)

    # ──────────────────────────────────────────────────────────
    # 3.3 并行调度器
    # ──────────────────────────────────────────────────────────

    async def execute_task_group(self, group: TaskGroup, intents_map: Dict[str, Intent]) -> Dict[str, Any]:
        """执行单个任务组（技术文档 §3.3.1）"""
        ctx = ContextStore(group.id)

        for intent_id in group.intents:
            intent = intents_map.get(intent_id)
            if intent:
                ctx.set(f"intent:{intent_id}", {
                    "type": intent.type,
                    "entities": intent.entities,
                })

        for step in group.execution_plan:
            if step.parallel and len(step.tool_calls) > 1:
                results = await asyncio.gather(*[
                    self._execute_tool_with_retry(tool_name, ctx)
                    for tool_name in step.tool_calls
                ], return_exceptions=True)
                for r in results:
                    if isinstance(r, ToolResult):
                        ctx.merge_result(r)
            else:
                for tool_name in step.tool_calls:
                    result = await self._execute_tool_with_retry(tool_name, ctx)
                    ctx.merge_result(result)

        final = ctx.get_results()
        ctx.clear()
        return final

    async def _execute_tool_with_retry(self, tool_name: str, ctx: ContextStore) -> ToolResult:
        """带超时与重试的工具执行（技术文档 §3.3.2）"""
        timeout_ms, max_retries, backoff_ms = self._get_retry_config(tool_name)
        params = self._build_tool_params(tool_name, ctx)

        last_result = None
        for attempt in range(max_retries + 1):
            result = await self._registry.execute_with_timeout(tool_name, params, ctx, timeout_ms)
            if result.success:
                return result
            last_result = result
            if attempt < max_retries:
                await asyncio.sleep(backoff_ms * (2 ** attempt) / 1000.0)

        return last_result or ToolResult(tool_name=tool_name, success=False, error="All retries exhausted")

    def _get_retry_config(self, tool_name: str):
        configs = {
            "web_search": (settings.TOOL_TIMEOUT_SEARCH_MS, settings.TOOL_RETRY_SEARCH, 500),
            "calendar_api": (settings.TOOL_TIMEOUT_CALENDAR_MS, settings.TOOL_RETRY_CALENDAR, 200),
            "maps_api": (settings.TOOL_TIMEOUT_MAP_MS, 1, 500),
            "reminder_service": (settings.TOOL_TIMEOUT_REMINDER_MS, settings.TOOL_RETRY_REMINDER, 100),
        }
        return configs.get(tool_name, (3000, 1, 500))

    def _build_tool_params(self, tool_name: str, ctx: ContextStore) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        results = ctx.get_results()

        if tool_name == "web_search":
            for key, val in results.items():
                if key.startswith("intent:") and isinstance(val, dict):
                    entities = val.get("entities", {})
                    query = entities.get("search_query") or entities.get("raw_text", "")
                    if query:
                        params["query"] = query
                        break

        return params

    # ──────────────────────────────────────────────────────────
    # 搜索 Query 构建（技术文档 §4.2）
    # ──────────────────────────────────────────────────────────

    async def build_search_query(self, intent_text: str) -> str:
        prompt = SEARCH_QUERY_PROMPT.format(intent_text=intent_text)
        raw = await self._call_llm("", prompt)
        try:
            parsed = json.loads(self._extract_json(raw))
            return parsed.get("query", intent_text)
        except (json.JSONDecodeError, KeyError):
            return intent_text

    # ──────────────────────────────────────────────────────────
    # 主入口
    # ──────────────────────────────────────────────────────────

    async def process(
        self,
        session_id: str,
        text: str,
        dialog_history: List[Dict[str, Any]] = None,
        user_profile: Dict[str, Any] = None,
        reference_time: Optional[datetime] = None,
    ) -> AgentOutput:
        """Agent 编排层主入口"""
        start = time.monotonic()
        ref_time = reference_time or datetime.utcnow()
        timezone = (user_profile or {}).get("timezone", settings.DEFAULT_TIMEZONE)

        # Step 1: 多意图提取
        intents = await self.extract_intents(text, ref_time, timezone)
        intents_map = {i.id: i for i in intents}

        # Step 2: 任务图构建
        task_groups = await self.build_task_groups(intents)

        # Step 3: 并行调度执行
        all_results: Dict[str, Any] = {}
        if len(task_groups) == 1:
            all_results = await self.execute_task_group(task_groups[0], intents_map)
        else:
            group_results = await asyncio.gather(*[
                self.execute_task_group(g, intents_map) for g in task_groups
            ], return_exceptions=True)
            for i, gr in enumerate(group_results):
                if isinstance(gr, dict):
                    all_results[f"group_{i}"] = gr
                elif isinstance(gr, Exception):
                    all_results[f"group_{i}"] = {"error": str(gr)}

        planning_ms = (time.monotonic() - start) * 1000

        return AgentOutput(
            session_id=session_id,
            task_groups=task_groups,
            results={"intents": [self._intent_to_dict(i) for i in intents], **all_results},
            planning_latency_ms=planning_ms,
        )

    def _intent_to_dict(self, intent: Intent) -> Dict[str, Any]:
        return {
            "id": intent.id,
            "type": intent.type,
            "entities": intent.entities,
            "confidence": intent.confidence,
        }

    @staticmethod
    def _extract_json(text: str) -> str:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.strip().startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.strip().startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            if json_lines:
                return "\n".join(json_lines)
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return text[start:end]
        return text


agent_service = AgentService()
