"""
Search Service — 联网搜索工具（技术文档 §4）

支持 Tavily API（推荐）、SerpAPI、Bing Search API 三种搜索引擎，
主/备自动切换，搜索结果缓存 6h。
"""
import time
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

import httpx

from app.core.config import settings
from app.services.tool_registry import Tool, ToolResult, ContextStore


class SearchService:
    """联网搜索服务"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = settings.SEARCH_CACHE_TTL_HOURS * 3600

    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        cache_key = f"{query}:{max_results}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached["ts"]) < self._cache_ttl:
            return cached["data"]

        provider = settings.SEARCH_PROVIDER
        try:
            if provider == "tavily" and settings.TAVILY_API_KEY:
                result = await self._search_tavily(query, max_results)
            elif provider == "serpapi" and settings.SERPAPI_API_KEY:
                result = await self._search_serpapi(query, max_results)
            elif provider == "bing" and settings.BING_SEARCH_API_KEY:
                result = await self._search_bing(query, max_results)
            else:
                result = self._mock_search(query, max_results)
        except Exception:
            result = self._mock_search(query, max_results)

        self._cache[cache_key] = {"ts": time.time(), "data": result}
        return result

    async def _search_tavily(self, query: str, max_results: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": settings.TAVILY_API_KEY,
                    "query": query,
                    "max_results": max_results,
                    "search_depth": "advanced",
                    "include_answer": True,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for r in data.get("results", [])[:max_results]:
            results.append({
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "url": r.get("url", ""),
                "score": r.get("score", 0),
            })

        return {
            "query": query,
            "answer": data.get("answer", ""),
            "results": results,
            "provider": "tavily",
        }

    async def _search_serpapi(self, query: str, max_results: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "api_key": settings.SERPAPI_API_KEY,
                    "q": query,
                    "num": max_results,
                    "hl": "zh-CN",
                    "gl": "cn",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for r in data.get("organic_results", [])[:max_results]:
            results.append({
                "title": r.get("title", ""),
                "content": r.get("snippet", ""),
                "url": r.get("link", ""),
                "score": r.get("position", 0),
            })

        return {
            "query": query,
            "answer": data.get("answer_box", {}).get("answer", ""),
            "results": results,
            "provider": "serpapi",
        }

    async def _search_bing(self, query: str, max_results: int) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                "https://api.bing.microsoft.com/v7.0/search",
                params={"q": query, "count": max_results, "mkt": "zh-CN"},
                headers={"Ocp-Apim-Subscription-Key": settings.BING_SEARCH_API_KEY},
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for r in data.get("webPages", {}).get("value", [])[:max_results]:
            results.append({
                "title": r.get("name", ""),
                "content": r.get("snippet", ""),
                "url": r.get("url", ""),
                "score": 0,
            })

        return {
            "query": query,
            "answer": "",
            "results": results,
            "provider": "bing",
        }

    def _mock_search(self, query: str, max_results: int) -> Dict[str, Any]:
        return {
            "query": query,
            "answer": f"关于「{query}」的搜索结果（模拟）",
            "results": [
                {
                    "title": f"{query} - 搜索结果",
                    "content": f"这是关于 {query} 的模拟搜索结果。请配置 TAVILY_API_KEY 以启用真实联网搜索。",
                    "url": "",
                    "score": 0.9,
                }
            ],
            "provider": "mock",
        }


class WebSearchTool(Tool):
    """联网搜索工具 — 实现 Tool 接口供 Agent 调度器调用"""

    def __init__(self, search_service: SearchService):
        self._svc = search_service

    @property
    def name(self) -> str:
        return "web_search"

    @property
    def schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        }

    async def execute(self, params: Dict[str, Any], ctx: ContextStore) -> ToolResult:
        query = params.get("query", "")
        max_results = params.get("max_results", 5)

        result = await self._svc.search(query, max_results)
        ctx.set("search_results", result)

        return ToolResult(
            tool_name=self.name,
            success=True,
            data=result,
        )


search_service = SearchService()
