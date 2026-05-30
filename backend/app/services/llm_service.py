"""
LLM Service
大语言模型服务 - 语义理解、意图识别、实体提取

支持双模型路由（技术文档 §3.1.3）：
- 简单意图 → 规则路由（< 50ms）
- 复杂/多意图 → LLM 路由（Claude Haiku < 500ms / Sonnet < 1500ms）
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx

from app.core.config import settings


class LLMService:
    """LLM服务类"""

    def __init__(self):
        self.model = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL

    async def process_voice_input(
        self,
        text: str,
        context: Dict[str, Any],
        reference_time: datetime
    ) -> Dict[str, Any]:
        """
        处理语音输入 — NLU 语义解析层（L2）

        流程：语义清洗 → 意图识别 → 实体提取 → 完整性检查 → 置信度计算
        """
        cleaned_text = await self.semantic_correction(text, context)
        intents = await self.extract_intents(cleaned_text, reference_time)
        primary_intent = intents[0] if intents else {"type": "unknown", "confidence": 0.5}

        entities = await self.extract_entities(cleaned_text, reference_time)
        missing_fields = self.check_completeness(primary_intent["type"], entities)
        confidence = self.calculate_confidence(primary_intent["type"], entities, missing_fields)

        return {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "intent": primary_intent["type"],
            "intents": intents,
            "entities": entities,
            "missing_fields": missing_fields,
            "confidence": confidence,
            "reference_time": reference_time.isoformat(),
            "needs_agent": len(intents) > 1 or primary_intent["type"] == "SEARCH",
        }

    async def semantic_correction(self, text: str, context: Dict[str, Any]) -> str:
        """语义清洗与纠错"""
        address_book = context.get("address_book", {})

        cleaned = text
        for canonical, variants in address_book.items():
            for variant in variants:
                if variant in cleaned:
                    cleaned = cleaned.replace(variant, canonical)

        fillers = ["呃", "那个", "嗯", "啊", "就是说", "然后呢"]
        for filler in fillers:
            cleaned = cleaned.replace(filler, "")

        return cleaned.strip()

    async def extract_intents(self, text: str, reference_time: datetime) -> List[Dict[str, Any]]:
        """
        多意图识别（技术文档 §3.1）

        返回所有识别到的意图列表，支持多意图场景。
        """
        keywords = {
            "CREATE": ["添加", "创建", "记录", "提醒", "加个", "安排"],
            "MODIFY": ["修改", "更改", "调整", "更新", "推迟", "推"],
            "DELETE": ["删除", "取消", "去掉", "移除"],
            "QUERY": ["查看", "查询", "显示", "看看", "什么时候", "几点"],
            "SEARCH": ["搜索", "搜一下", "查一下", "检索", "联网", "搜", "查找"],
            "PLAN": ["规划", "安排行程", "计划"],
        }

        # 尝试调用 LLM 进行多意图识别
        llm_result = await self._llm_extract_intents(text, reference_time)
        if llm_result:
            return llm_result

        # 规则兜底
        found = []
        for itype, words in keywords.items():
            for word in words:
                if word in text:
                    found.append({
                        "type": itype,
                        "confidence": 0.75,
                        "matched_keyword": word,
                    })
                    break

        if not found:
            found.append({"type": "CREATE", "confidence": 0.6})

        return found

    async def _llm_extract_intents(self, text: str, reference_time: datetime) -> Optional[List[Dict[str, Any]]]:
        """通过 LLM 提取多意图（支持国产模型）"""
        prompt = f"""请分析以下用户输入，识别其中包含的所有意图。

当前时间：{reference_time.isoformat()}
用户输入：{text}

以JSON数组格式输出每个意图：
[{{"type": "CREATE|QUERY|MODIFY|DELETE|SEARCH|PLAN", "confidence": 0.95, "description": "简短描述"}}]
"""
        try:
            provider = settings.AGENT_LLM_PROVIDER
            
            # 通义千问（阿里云）
            if provider == "alibaba" and settings.ALIBABA_API_KEY:
                model = settings.ALIBABA_FAST_MODEL
                base_url = settings.ALIBABA_BASE_URL
                api_key = settings.ALIBABA_API_KEY
            # 智谱GLM
            elif provider == "zhipu" and settings.ZHIPU_API_KEY:
                model = settings.ZHIPU_FAST_MODEL
                base_url = settings.ZHIPU_BASE_URL
                api_key = settings.ZHIPU_API_KEY
            # 本地Ollama
            elif settings.LLM_BASE_URL and settings.LLM_MODEL:
                model = settings.LLM_MODEL
                base_url = settings.LLM_BASE_URL
                api_key = settings.LLM_API_KEY
            else:
                return None
            
            async with httpx.AsyncClient(timeout=3.0) as client:
                headers = {"Content-Type": "application/json"}
                if api_key:
                    headers["Authorization"] = f"Bearer {api_key}"
                
                resp = await client.post(
                    f"{base_url}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1,
                        "max_tokens": 512,
                    },
                )
                resp.raise_for_status()
                raw = resp.json()["choices"][0]["message"]["content"]
                start = raw.find("[")
                end = raw.rfind("]") + 1
                if start >= 0 and end > start:
                    return json.loads(raw[start:end])
        except Exception:
            pass
        return None

    async def extract_entities(self, text: str, reference_time: datetime) -> Dict[str, Any]:
        """实体提取 — 时间、地点、参与者等"""
        entities = {
            "title": None,
            "start_time": None,
            "end_time": None,
            "location": None,
            "participants": [],
            "is_all_day": False,
            "reminder_minutes": 30,
            "search_query": None,
        }

        search_keywords = ["搜索", "搜一下", "查一下", "检索", "联网", "搜", "查找"]
        for kw in search_keywords:
            if kw in text:
                idx = text.index(kw) + len(kw)
                entities["search_query"] = text[idx:].strip()
                break

        time_keywords = {
            "明天": 1, "后天": 2, "大后天": 3, "下周": 7, "下个月": 30,
        }

        for keyword, days in time_keywords.items():
            if keyword in text:
                try:
                    target_date = reference_time.replace(day=reference_time.day + days)
                    entities["start_time"] = target_date.replace(hour=14, minute=0, second=0).isoformat()
                    entities["end_time"] = target_date.replace(hour=15, minute=0, second=0).isoformat()
                except ValueError:
                    pass
                text = text.replace(keyword, "")

        time_patterns = {"上午": 9, "中午": 12, "下午": 14, "晚上": 19}
        for period, hour in time_patterns.items():
            if period in text:
                if entities["start_time"]:
                    dt = datetime.fromisoformat(entities["start_time"])
                    entities["start_time"] = dt.replace(hour=hour).isoformat()
                    entities["end_time"] = dt.replace(hour=hour + 1).isoformat()
                text = text.replace(period, "")

        for w in ["添加", "创建", "记录", "提醒", "加个", "安排", "帮我", "查看", "搜索", "联网检索"]:
            text = text.replace(w, "")

        title_parts = [t.strip() for t in text.split() if t.strip()]
        remaining = "".join(title_parts) if title_parts else ""
        if remaining and not entities.get("search_query"):
            entities["title"] = remaining or "未命名事件"

        return entities

    def check_completeness(self, intent: str, entities: Dict[str, Any]) -> List[str]:
        missing = []
        if intent in ("CREATE", "create_event"):
            if not entities.get("title"):
                missing.append("事件标题")
            if not entities.get("start_time"):
                missing.append("开始时间")
        return missing

    def calculate_confidence(
        self, intent: str, entities: Dict[str, Any], missing_fields: List[str]
    ) -> float:
        base = 0.9
        if missing_fields:
            base -= len(missing_fields) * 0.1
        if entities.get("location"):
            base += 0.05
        if entities.get("participants"):
            base += 0.05
        return max(0.5, min(1.0, base))


llm_service = LLMService()
