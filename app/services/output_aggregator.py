from zhipuai import ZhipuAI
import json

class OutputAggregator:
    def __init__(self, api_key):
        self.client = ZhipuAI(api_key=api_key)

    def aggregate(self, intent: str, tool_messages: list) -> str:
        """
        使用 LLM 将结构化的工具返回结果，转化为 TTS 友好的简短口语化播报文本。
        """
        if not tool_messages:
            return "处理完成。"

        system_prompt = """你是一个智能语音助手，负责将工具执行结果转化为简洁的中文播报文本。
要求：
1. 口语化，适合 TTS（语音合成）播报，不要使用 Markdown（如加粗、列表）。
2. 长度控制在 60-120 字之间，务必简明扼要。
3. 突出最关键信息（如需要花多久，去哪，什么时候）。
4. 若遇到查询失败或错误，礼貌说明。"""

        tools_data = []
        for msg in tool_messages:
            if msg.get("role") == "tool":
                tools_data.append(msg.get("content", ""))

        user_content = f"用户的原始意图是：'{intent}'\n\n工具返回的数据：\n{json.dumps(tools_data, ensure_ascii=False)}\n\n请生成语音播报文本："

        try:
            response = self.client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content
        except Exception as e:
            print("Aggregator Exception:", e)
            return "我已经帮您处理完毕，请查看手机或屏幕确认详情。"
