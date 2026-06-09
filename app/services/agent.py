import json
import os
import urllib.request
from zhipuai import ZhipuAI
from app.services.tools import TOOLS_SCHEMA
from app.services.tool_registry import ToolScheduler
from app.services.output_aggregator import OutputAggregator
from app.speech.tts import tts_client
from app.core import notifier
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ["ZHIPUAI_API_KEY"]
client = ZhipuAI(api_key=API_KEY)

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

## 核心规则（必须严格遵守）

**规则零：你必须通过工具来完成用户请求，绝不能只回复文字。**
- 用户的每一个请求（创建、删除、修改日程、查路线、查高铁等）都必须调用对应的工具。
- 如果你不确定该调什么工具，也要尝试调用最相关的工具，而不是直接回复"处理完成"或"好的"等文字。
- 只有在工具返回结果后，系统才会自动生成语音播报，你不需要自己生成回复文字。

请遵循以下原则：
1. 复杂意图拆解：如果用户请求包含多个意图，请返回需要并行调用的工具列表，系统将同时执行它们（L4 并发调度）。
2. 数据依赖：如果有数据依赖，例如必须先查漫展时间才能设置日程，请先调用查询工具，在拿到结果后再调用写入工具。
3. 缺失信息处理：如果用户查询路线但未提供出发地，请默认使用当前所在位置（{current_location}）作为出发地。
4. 时间计算：遇到如"今晚7点"、"明天下午3点"等带有具体时间指代的词语，必须结合当前系统时间准确计算为 ISO8601 格式（如 YYYY-MM-DDTHH:MM:SS）并填入 start_time 槽位中，绝对不能省略。
5. 时间必须在未来：**绝对禁止安排过去的时间**。计算出的 start_time 必须晚于当前系统时间（{current_time}）。如果用户说"今天上午10点"但现在已经是下午，则应理解为"明天上午10点"。
6. 时间缺失处理：只有当用户完全没有提及具体时间时，不传 start_time，系统会自动推荐时间。
7. 工具调用完成后立即停止：工具返回 status=success 后，不要再次调用同一个工具，也不需要回复任何文字。
8. 多天跨度活动：当用户提到去参加一个跨度为多天的活动（如漫展、连续几天的会议等）时，如果用户没有说明是哪一天去，你必须先通过文字/语音询问用户计划哪一天去。在得到用户关于明确日期的答复之前，绝对禁止自行决定日期或直接去查询路线和车次。
9. 确认日期后规划：当用户明确了日期后，再依次开展路线规划与交通工具的选择。

## 日程管理（查询/删除/修改）

10. 查询已有日程：当用户问"我明天有什么安排"、"帮我查一下6月3号的行程/日程"时，必须调用 schedule_management 工具，intent 设为 QUERY_SCHEDULE。slots 中传入：
   - date: 用户提到的具体日期，格式为 YYYY-MM-DD。如果不指明日期则默认为今天。
   示例：用户说"帮我查一下6月3号我都有什么行程安排" → intent=QUERY_SCHEDULE, slots={{"date":"2026-06-03"}}

10. 删除日程：当用户说"删除XX"、"取消XX"、"去掉XX日程"等，必须调用 schedule_management 工具，intent 设为 CANCEL_SCHEDULE。slots 中传入：
   - title: 日程名称关键词（如"晚会"、"周会"）
   - date: 如果用户提到了具体日期（如"6月1号的"），务必传入 YYYY-MM-DD 格式的 date 字段，用于精确定位同名日程。
   示例：用户说"删除6月1号的晚会" → intent=CANCEL_SCHEDULE, slots={{"title":"晚会", "date":"2026-06-01"}}

11. 修改日程：当用户说"把XX改到XX"、"修改XX的时间"等，必须调用 schedule_management 工具，intent 设为 UPDATE_SCHEDULE。slots 中传入 title 和新的 start_time。

## 出行规划（重要）

12. 交通方式未指定时的处理流程：
   当用户要求**创建异地/跨城的行程**（如"帮我创建从杭州到上海的行程"）或说"我要去XX"、"帮我规划去XX的路线"等，且**没有明确指定"坐高铁"、"驾车"等具体交通方式**时：
   - 必须调用 query_multi_mode_route 查询多种出行方式。如果用户提到了具体的日期和时间，也请通过 date 和 target_time 传递过去。
   - **绝对不可以提前擅自决定调用 query_train_schedule，必须等待用户从 query_multi_mode_route 的推荐中做出选择。**
   - 工具会将选项推送给用户，**你必须停止后续推理**，等待用户选择。
   - 不要自己替用户选择交通方式。

13. 用户明确指定了交通方式时：
   - 直接调用 query_traffic_route 并传入对应的 mode（driving/transit/walking/riding）。

14. 高铁出行的完整规划流程：
   当用户选择高铁，或直接说"坐高铁去XX"、"查一下去XX的高铁"时：
   - 调用 query_train_schedule 查询车次列表。如果用户提到了具体的出发时间（如"下午3点"），必须在参数 target_time 中传入转换后的24小时制时间（如"15:00"）。
   - 工具会将车次列表推送给用户，**你必须停止后续推理**，等待用户选择具体车次。
   - 不要自己替用户选择车次。

15. 用户选择了具体车次后：
   当用户说"我选G21次列车"等明确选择了车次时：
   - **绝对不能再次调用 query_train_schedule**！你必须直接从先前的对话历史中提取该车次的发车时间、时长，并直接调用 schedule_management（intent=CREATE_SCHEDULE）创建出行日程。start_time 设为发车时间，duration_minutes 设为列车行程时长。title 格式："高铁G21出行：北京→上海"。系统在创建时会自动检测冲突。

16. 用户指定了出行时间时：
   当用户说"明天上午坐高铁去上海"：
   - date 传明天日期，查询车次后推送给用户选择。
17. 高铁/出行日程时间变更与改签：当用户要求修改、变更已定高铁/出行日程的时间，或选择改签另一趟高铁时：
   - 必须通过组合调用来替换日程：
     1) 调用 schedule_management 且将 intent 设为 CANCEL_SCHEDULE，在 slots 中传入原有日程的关键词（如“高铁”或“出行”）和它的日期，删除原有的失效高铁行程。
     2) 调用 schedule_management 且将 intent 设为 CREATE_SCHEDULE，创建新的高铁出行行程。
   - 这样可以避免在日历中留下旧行程导致冲突和数据重复。"""

chat_memory = []
MAX_HISTORY_ROUNDS = 6  # 只保留最近3轮对话


def process_voice_intent(user_input: str):
    global chat_memory
    print(f"\n========== Agent (L4/L5架构) 启动 ==========")
    print(f"收到语音识别结果: {user_input}")

    # 关键词过滤，无日程/出行相关关键词则不调用 LLM (Agent)
    KEYWORDS = [
        "日程", "会议", "安排", "行程", "时间", "日期", "忙", "空闲", "空", "空挡", "规划", "路线", 
        "路况", "怎么走", "去", "高铁", "火车", "动车", "车次", "列车", "票", "驾车", "开车", "自驾", 
        "公交", "地铁", "步行", "走路", "骑行", "单车", "漫展", "动漫展", "展会", "活动", "新建", "创建", 
        "添加", "加入", "删除", "取消", "去掉", "撤销", "修改", "改到", "更改", "查询", "查看", "显示", 
        "看看", "日程表"
    ]
    user_input_clean = user_input.strip()
    if not user_input_clean or not any(kw in user_input_clean for kw in KEYWORDS):
        print("[Agent] 未检测到日程或出行相关关键词，直接停止调用 Agent 并提示无法操作")
        tts_text = "未检测到日程或出行相关指令，无法操作。"
        notifier.broadcast("agent_thinking", {"message": "未检测到有效指令"})
        notifier.broadcast("tts_text", {"text": tts_text})
        tts_client.synthesize_and_play(tts_text)
        notifier.broadcast("session_end", {"message": "未识别到有效指令，本轮对话结束"})
        return tts_text

    messages = [{"role": "system", "content": get_system_prompt()}]

    if chat_memory:
        messages.extend(chat_memory)

    messages.append({"role": "user", "content": user_input})

    notifier.broadcast("agent_thinking", {"message": "Agent 正在分析您的请求..."})

    all_tool_messages = []
    awaiting_choice = False

    print(f"\n--- LLM 推理 ---")
    try:
        for iteration in range(5):
            response = client.chat.completions.create(
                model="glm-4",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto"
            )

            message = response.choices[0].message
            messages.append(message.model_dump())

            if not message.tool_calls:
                # 如果是第一轮且LLM没调工具，可能是误判，强制提醒一次
                if iteration == 0 and len(all_tool_messages) == 0:
                    reply_text = (message.content or "").strip()
                    # 检测是否为空洞回复（没有实质内容的短文本）
                    if len(reply_text) < 15 or reply_text in ["处理完成。", "处理完成", "好的。", "好的", "已完成。"]:
                        print(f"[Agent] LLM 未调用工具且回复空洞({reply_text})，强制重试")
                        nudge = (
                            f"你没有调用任何工具！请仔细分析用户的请求：{user_input}。"
                            f"然后调用合适的工具来执行。"
                            f"删除/取消日程请用 schedule_management(intent=CANCEL_SCHEDULE)，"
                            f"创建日程请用 schedule_management(intent=CREATE_SCHEDULE)。"
                        )
                        messages.append({"role": "user", "content": nudge})
                        continue
                break

            notifier.broadcast("agent_thinking", {"message": f"第 {iteration+1} 轮：规划并行调用 {len(message.tool_calls)} 个工具..."})
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
                messages.append({"role": "tool", "content": res['content'], "tool_call_id": res.get('tool_call_id')})

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

                try:
                    result_data = json.loads(res['content'])

                    for bc in result_data.get('broadcasts', []):
                        notifier.broadcast(bc['type'], bc['data'])

                    if result_data.get('await_user_choice'):
                        awaiting_choice = True

                    action = result_data.get('event_action')
                    if action:
                        action_type = action.get('type')
                        if action_type == 'created':
                            event_type = 'event_created'
                        elif action_type == 'deleted':
                            event_type = 'event_deleted'
                        else:
                            event_type = 'event_updated'
                        notifier.broadcast(event_type, {
                            k: v for k, v in action.items() if k != 'type'
                        })
                except (json.JSONDecodeError, KeyError, TypeError):
                    pass

            if awaiting_choice:
                print("[Agent] 工具请求等待用户选择，暂停推理循环")
                break

    except Exception as e:
        print(f"Agent 运行异常: {e}")
        notifier.broadcast("session_end", {"message": f"发生错误: {e}", "error": True})
        return "处理中断"

    if awaiting_choice:
        notifier.broadcast("await_user_choice", {"message": "请在下方选择您的偏好"})
        print("========== Agent 等待用户选择 ==========\n")

        chat_memory.append({"role": "user", "content": user_input})
        
        options_text = "我已经查询了相关信息。请在以下选项中做出选择：\n"
        for msg in all_tool_messages:
            try:
                data = json.loads(msg['content'])
                if data.get("trains"):
                    for t in data["trains"]:
                        options_text += f"- 高铁车次 {t['train_no']}: {t['from_station']} 到 {t['to_station']}, 发车时间 {t['depart_time']}, 时长 {t['duration_minutes']} 分钟\n"
                elif data.get("options"):
                    for o in data["options"]:
                        options_text += f"- 出行方式 {o.get('mode')}: 预计时长 {o.get('duration_minutes')} 分钟\n"
            except Exception:
                pass

        chat_memory.append({"role": "assistant", "content": options_text})
        if len(chat_memory) > MAX_HISTORY_ROUNDS:
            chat_memory = chat_memory[-MAX_HISTORY_ROUNDS:]

        return "[等待用户选择]"

    # L5 输出层
    print("\n========== 进入 L5 输出层 ==========")
    notifier.broadcast("agent_thinking", {"message": "正在生成回复..."})

    tts_text = aggregator.aggregate(user_input, all_tool_messages)
    print(f"\n[L5 聚合播报文本]:\n{tts_text}\n")

    notifier.broadcast("tts_text", {"text": tts_text})
    tts_client.synthesize_and_play(tts_text)

    notifier.broadcast("session_end", {"message": "本轮对话结束"})
    print(f"========== Agent 执行完毕 ==========\n")

    # 只记录用户输入和工具调用结果摘要，不记录"处理完成"等空洞文本
    memory_summary = tts_text if len(tts_text) > 10 else f"已完成用户请求：{user_input}"
    chat_memory.append({"role": "user", "content": user_input})
    chat_memory.append({"role": "assistant", "content": memory_summary})
    if len(chat_memory) > MAX_HISTORY_ROUNDS:
        chat_memory = chat_memory[-MAX_HISTORY_ROUNDS:]

    return tts_text

if __name__ == "__main__":
    test_text = "查一下从天安门去故宫怎么走，然后安排到我的日程里"
    process_voice_intent(test_text)
