"""
LLM Service
大语言模型服务 - 语义理解、意图识别、实体提取
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

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
        处理语音输入
        
        Args:
            text: 原始语音识别文本
            context: 上下文信息（用户字典、历史对话等）
            reference_time: 参考时间（用于解析相对时间）
        
        Returns:
            结构化的语义理解结果
        """
        # Step 1: 语义清洗与纠错
        cleaned_text = await self.semantic_correction(text, context)
        
        # Step 2: 意图识别
        intent = await self.extract_intent(cleaned_text)
        
        # Step 3: 实体提取
        entities = await self.extract_entities(cleaned_text, reference_time)
        
        # Step 4: 检查完整性
        missing_fields = self.check_completeness(intent, entities)
        
        # Step 5: 生成置信度
        confidence = self.calculate_confidence(intent, entities, missing_fields)
        
        return {
            "original_text": text,
            "cleaned_text": cleaned_text,
            "intent": intent,
            "entities": entities,
            "missing_fields": missing_fields,
            "confidence": confidence,
            "reference_time": reference_time.isoformat()
        }
    
    async def semantic_correction(self, text: str, context: Dict[str, Any]) -> str:
        """
        语义清洗与纠错
        
        - 去除口语化填充词（呃、那个、嗯等）
        - 修正同音字错误
        - 结合用户字典进行实体修复
        """
        # 构建纠错提示词
        address_book = context.get("address_book", {})
        favorite_locations = context.get("favorite_locations", {})
        
        prompt = f"""
请对以下语音识别文本进行语义清洗：

1. 去除口语化填充词（呃、那个、嗯、啊等）
2. 修正明显的同音字错误
3. 结合以下字典进行实体修复：
   - 联系人字典: {json.dumps(address_book, ensure_ascii=False)}
   - 常用地点字典: {json.dumps(favorite_locations, ensure_ascii=False)}
4. 保持原意不变

输入文本：{text}

输出清洗后的文本：
"""
        
        # TODO: 调用真实LLM API
        # 这里模拟返回
        cleaned = text
        for canonical, variants in address_book.items():
            for variant in variants:
                if variant in cleaned:
                    cleaned = cleaned.replace(variant, canonical)
        
        return cleaned
    
    async def extract_intent(self, text: str) -> str:
        """
        意图识别
        
        支持的意图类型：
        - create_event: 创建日历事件
        - update_event: 更新日历事件
        - delete_event: 删除日历事件
        - query_event: 查询日历事件
        - create_task: 创建待办任务
        - query_task: 查询待办任务
        - check_conflict: 检查时间冲突
        - query_free_busy: 查询忙闲状态
        - general_chat: 通用对话
        """
        # 构建意图识别提示词
        prompt = f"""
请判断以下用户输入的意图类型：

用户输入：{text}

可用的意图类型：
1. create_event - 创建日历事件（包含"添加"、"创建"、"记录"、"提醒"等关键词）
2. update_event - 更新日历事件（包含"修改"、"更改"、"调整"等关键词）
3. delete_event - 删除日历事件（包含"删除"、"取消"、"去掉"等关键词）
4. query_event - 查询日历事件（包含"查看"、"查询"、"显示"等关键词）
5. create_task - 创建待办任务（包含"待办"、"任务"、"todo"等关键词）
6. query_task - 查询待办任务
7. check_conflict - 检查时间冲突
8. query_free_busy - 查询忙闲状态
9. general_chat - 通用对话

请只输出意图类型名称：
"""
        
        # TODO: 调用真实LLM API
        # 这里模拟意图识别
        intent = "create_event"
        keywords = {
            "create_event": ["添加", "创建", "记录", "提醒", "加个"],
            "update_event": ["修改", "更改", "调整", "更新"],
            "delete_event": ["删除", "取消", "去掉", "移除"],
            "query_event": ["查看", "查询", "显示", "看看"],
            "create_task": ["待办", "任务", "todo"],
            "query_task": ["查看待办", "查询任务"],
            "check_conflict": ["冲突", "重叠", "时间冲突"],
            "query_free_busy": ["忙闲", "空闲", "有空"]
        }
        
        for intent_type, words in keywords.items():
            if any(word in text for word in words):
                intent = intent_type
                break
        
        return intent
    
    async def extract_entities(self, text: str, reference_time: datetime) -> Dict[str, Any]:
        """
        实体提取
        
        提取：标题、时间、地点、参与者等
        """
        # 构建实体提取提示词
        prompt = f"""
请从以下文本中提取日历事件相关信息：

当前时间：{reference_time.isoformat()}
用户输入：{text}

请提取以下信息（JSON格式）：
{{
    "title": "事件标题",
    "start_time": "开始时间（ISO 8601格式）",
    "end_time": "结束时间（ISO 8601格式）",
    "location": "地点",
    "participants": ["参与者列表"],
    "is_all_day": false,
    "reminder_minutes": 30
}}

注意：
- 如果用户说"明天"，基于当前时间计算
- 如果用户说"下午三点"，转换为15:00
- 如果没有明确结束时间，默认事件持续1小时

输出JSON：
"""
        
        # TODO: 调用真实LLM API
        # 这里模拟实体提取
        entities = {
            "title": None,
            "start_time": None,
            "end_time": None,
            "location": None,
            "participants": [],
            "is_all_day": False,
            "reminder_minutes": 30
        }
        
        # 简单的时间解析模拟
        time_keywords = {
            "明天": 1,
            "后天": 2,
            "大后天": 3,
            "下周": 7,
            "下个月": 30
        }
        
        title_parts = []
        for keyword, days in time_keywords.items():
            if keyword in text:
                target_date = reference_time.replace(day=reference_time.day + days)
                entities["start_time"] = target_date.replace(hour=14, minute=0, second=0).isoformat()
                entities["end_time"] = target_date.replace(hour=15, minute=0, second=0).isoformat()
                text = text.replace(keyword, "")
        
        # 提取时间点
        time_patterns = {
            "上午": 9,
            "中午": 12,
            "下午": 14,
            "晚上": 19
        }
        
        for period, hour in time_patterns.items():
            if period in text:
                if entities["start_time"]:
                    # 更新小时
                    dt = datetime.fromisoformat(entities["start_time"])
                    entities["start_time"] = dt.replace(hour=hour).isoformat()
                    entities["end_time"] = dt.replace(hour=hour + 1).isoformat()
                text = text.replace(period, "")
        
        # 剩余文本作为标题
        title_parts = [t.strip() for t in text.split() if t.strip()]
        entities["title"] = " ".join(title_parts) if title_parts else "未命名事件"
        
        return entities
    
    def check_completeness(self, intent: str, entities: Dict[str, Any]) -> List[str]:
        """
        检查事件完整性
        
        必填字段：title, start_time
        """
        missing = []
        
        if not entities.get("title"):
            missing.append("事件标题")
        
        if not entities.get("start_time"):
            missing.append("开始时间")
        
        return missing
    
    def calculate_confidence(
        self,
        intent: str,
        entities: Dict[str, Any],
        missing_fields: List[str]
    ) -> float:
        """计算置信度"""
        base_confidence = 0.9
        
        # 根据缺失字段降低置信度
        if missing_fields:
            base_confidence -= len(missing_fields) * 0.1
        
        # 根据实体完整度调整
        if entities.get("location"):
            base_confidence += 0.05
        if entities.get("participants"):
            base_confidence += 0.05
        
        return max(0.5, min(1.0, base_confidence))


# 全局LLM服务实例
llm_service = LLMService()
