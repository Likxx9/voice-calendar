import json
import os
import urllib.request
import notifier
from zhipuai import ZhipuAI
from tools import TOOLS_SCHEMA
from tool_registry import ToolScheduler
from output_aggregator import OutputAggregator
from tts import tts_client
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["ZHIPUAI_API_KEY"]
client = ZhipuAI(api_key=API_KEY)

# L4 工具调度器 & L5 聚合器
scheduler = ToolScheduler()
aggregator = OutputAggregator(api_key=API_KEY)

def get_current_location():
    try:
        amap_key = os.environ.get("AMAP_API_KEY", "")
        url = f'https://restapi.amap.com/v3/ip?key={amap_key}'
        with urllib.request.urlopen(url, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == '1':
                prov = data.get('province', '')
                city = data.get('city', '')
                if isinstance(city, list): city = ''
                if isinstance(prov, list): prov = ''
                return f"{prov}{city}"
    except Exception:
        pass
    return "未知"

def get_system_prompt():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_location = get_current_location()

    return f"""你是一个智能语音日历助理 Agent。你的任务是理解用户的自然语言指令，规划并执行多步任务。
当前系统时间是：{current_time}。
当前所在城市/位置：{current_location}。

请遵循以下原则：
1. 复杂意图拆解：如果用户请求包含多个意图，请返回需要并行调用的工具列表，系统将同时执行它们（L4 并发调度）。
2. 数据依赖：如果有数据依赖，例如必须先查漫展时间才能设置日程，请先调用查询工具，在拿到结果后再调用写入工具。
3. 缺失信息处理：如果用户查询路线但未提供出发地，请默认使用当前所在位置（{current_location}）作为出发地。
4. 时间缺失处理：如果用户要创建日程或待办但没有明确说具体时间（例如"帮我安排一个团队会议"、"提醒我写周报"），不要自己编造时间，直接调用 schedule_management 工具，将 intent 设为 CREATE_SCHEDULE 或 CREATE_MEETING，slots 中不传 start_time。系统会自动查询空闲时段并推荐合适的时间。
5. 工具调用完成后必须立即停止：每个工具只需要调用一次。当工具返回 status=success 时，任务已完成，不要再次调用同一个工具。直接结束，不需要回复任何文字，系统会自动生成播报。"""

def process_voice_intent(user_input: str):
    print(f"\n========== Agent (L4/L5架构) 启动 ==========")
    print(f"收到语音识别结果: {user_input}")

    messages = [
        {"role": "system", "content": get_system_prompt()},
        {"role": "user", "content": user_input}
    ]

    notifier.broadcast("agent_thinking", {"message": "Agent 正在分析您的请求..."})

    all_tool_messages = []

    # 单轮 LLM 推理 + 工具执行，不循环
    print(f"\n--- LLM 推理 ---")
    try:
        response = client.chat.completions.create(
            model="glm-4",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message.model_dump())

        if message.tool_calls:
            notifier.broadcast("agent_thinking", {"message": f"规划并行调用 {len(message.tool_calls)} 个工具..."})
            print(f"Agent 决定并行调用 {len(message.tool_calls)} 个工具...")

            for tc in message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                notifier.broadcast("tool_call", {
                    "tool": tc.function.name,
                    "args": args,
                    "status": "running"
                })

            tool_results = scheduler.execute_parallel(message.tool_calls)

            for res in tool_results:
                print(f" -> 工具执行完成，结果: {res['content']}")
                all_tool_messages.append(res)

                tc_name = None
                for tc in message.tool_calls:
                    if tc.id == res.get('tool_call_id'):
                        tc_name = tc.function.name
                        break

                notifier.broadcast("tool_result", {
                    "tool": tc_name or "unknown",
                    "result": res['content'],
                    "status": "done"
                })

    except Exception as e:
        print(f"Agent 运行异常: {e}")
        notifier.broadcast("session_end", {"message": f"发生错误: {e}", "error": True})
        return "处理中断"

    # L5 输出层
    print("\n========== 进入 L5 输出层 ==========")
    notifier.broadcast("agent_thinking", {"message": "正在生成回复..."})

    tts_text = aggregator.aggregate(user_input, all_tool_messages)
    print(f"\n[L5 聚合播报文本]:\n{tts_text}\n")

    notifier.broadcast("tts_text", {"text": tts_text})
    tts_client.synthesize_and_play(tts_text)

    notifier.broadcast("session_end", {"message": "本轮对话结束"})
    print(f"========== Agent 执行完毕 ==========\n")
    return tts_text

if __name__ == "__main__":
    test_text = "查一下从天安门去故宫怎么走，然后安排到我的日程里"
    process_voice_intent(test_text)
