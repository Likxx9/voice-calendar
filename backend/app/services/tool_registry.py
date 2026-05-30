"""
Tool Registry — 统一工具调用接口（技术文档 §5.3）

所有工具均实现 Tool 接口，保证调度器可统一调用。
"""
import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    """工具调用结果"""
    tool_name: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    latency_ms: float = 0.0
    needs_user_confirm: bool = False


class ContextStore:
    """
    任务组隔离上下文空间（技术文档 §3.2.3）

    每个任务组持有独立 context_store，键值空间以 group_id 为前缀，
    读写通过 ContextProxy 强制隔离。
    """

    def __init__(self, group_id: str):
        self.group_id = group_id
        self._store: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(f"{self.group_id}:{key}", default)

    def set(self, key: str, value: Any) -> None:
        self._store[f"{self.group_id}:{key}"] = value

    def get_results(self) -> Dict[str, Any]:
        return {
            k.removeprefix(f"{self.group_id}:"): v
            for k, v in self._store.items()
        }

    def merge_result(self, result: ToolResult) -> None:
        self.set(f"tool_result:{result.tool_name}", {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "latency_ms": result.latency_ms,
        })

    def clear(self) -> None:
        self._store.clear()


class Tool(ABC):
    """工具基类（技术文档 §5.3）"""

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @property
    def schema(self) -> Dict[str, Any]:
        return {}

    @abstractmethod
    async def execute(self, params: Dict[str, Any], ctx: ContextStore) -> ToolResult:
        ...


class ToolRegistry:
    """工具注册表，管理所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self._tools.keys())

    def get_schemas(self) -> List[Dict[str, Any]]:
        return [
            {"name": t.name, "schema": t.schema}
            for t in self._tools.values()
        ]

    async def execute_with_timeout(
        self,
        tool_name: str,
        params: Dict[str, Any],
        ctx: ContextStore,
        timeout_ms: int,
    ) -> ToolResult:
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' not found",
            )

        start = time.monotonic()
        try:
            result = await asyncio.wait_for(
                tool.execute(params, ctx),
                timeout=timeout_ms / 1000.0,
            )
            result.latency_ms = (time.monotonic() - start) * 1000
            return result
        except asyncio.TimeoutError:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=f"Tool '{tool_name}' timed out after {timeout_ms}ms",
                latency_ms=(time.monotonic() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                error=str(e),
                latency_ms=(time.monotonic() - start) * 1000,
            )


tool_registry = ToolRegistry()
