import json
import os
import urllib.request
import urllib.parse
import time
import asyncio
import uuid
from app.database import AsyncSessionLocal
from app.services.biz_dispatcher import BizDispatcher
from dotenv import load_dotenv

load_dotenv()

class Tool:
    def __init__(self, name, description, schema, timeout=5, retries=1):
        self.name = name
        self.description = description
        self.schema = schema
        self.timeout = timeout
        self.retries = retries

    def execute(self, params):
        raise NotImplementedError

class AMapRouteTool(Tool):
    def __init__(self, api_key):
        schema = {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "出发地名称"},
                "destination": {"type": "string", "description": "目的地名称"},
                "mode": {"type": "string", "description": "driving|transit|walking|riding", "default": "driving"}
            },
            "required": ["origin", "destination"]
        }
        super().__init__("query_traffic_route", "高德地图路线规划，支持驾车、公交、高铁、步行，返回时长和路线摘要", schema, timeout=8, retries=2)
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3"

    def _geocode(self, address):
        url = f"{self.base_url}/geocode/geo?address={urllib.parse.quote(address)}&key={self.api_key}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=self.timeout) as response:
            data = json.loads(response.read().decode())
            if data.get("status") == "1" and data.get("geocodes"):
                return data["geocodes"][0]["location"]
        raise Exception(f"无法获取地点 '{address}' 的经纬度")

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")
        origin = params["origin"]
        dest = params["destination"]
        mode = params.get("mode", "driving")

        for attempt in range(self.retries + 1):
            try:
                start_loc = self._geocode(origin)
                end_loc = self._geocode(dest)

                api_map = {
                    "driving": "/direction/driving",
                    "transit": "/direction/transit/integrated",
                    "walking": "/direction/walking",
                    "riding": "/direction/bicycling"
                }
                endpoint = api_map.get(mode, "/direction/driving")
                query = urllib.parse.urlencode({
                    "origin": start_loc,
                    "destination": end_loc,
                    "key": self.api_key,
                    "output": "json"
                })

                url = f"{self.base_url}{endpoint}?{query}"
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    data = json.loads(response.read().decode())
                    if data.get("status") != "1":
                        raise Exception(f"路线规划失败: {data.get('info')}")

                    if mode == "transit":
                        route = data.get("route", {}).get("transits", [{}])[0]
                    else:
                        route = data.get("route", {}).get("paths", [{}])[0]

                    duration_min = int(route.get("duration", 0)) // 60
                    distance_km = int(route.get("distance", 0)) / 1000

                    return json.dumps({
                        "status": "success",
                        "route": f"{origin} 到 {dest}",
                        "estimated_duration": f"{duration_min}分钟",
                        "distance": f"{distance_km}公里",
                        "mode": mode
                    }, ensure_ascii=False)
            except Exception as e:
                if attempt == self.retries:
                    return json.dumps({"error": str(e)}, ensure_ascii=False)
                time.sleep(1)


class MockEventTimeTool(Tool):
    def __init__(self):
        schema = {
            "type": "object",
            "properties": {
                "event_name": {"type": "string", "description": "活动或事件的名称"}
            },
            "required": ["event_name"]
        }
        super().__init__("get_event_time", "查询外部事件、展会等活动的时间和地点。", schema)

    def execute(self, params):
        event_name = params["event_name"]
        print(f"\n[Tool Execution] {self.name} called with: {event_name}")

        if "漫展" in event_name or "杭州" in event_name:
            return json.dumps({
                "event_name": "2026杭州国际动漫展",
                "time": "2026-06-15 09:00:00 - 2026-06-17 18:00:00",
                "location": "杭州白马湖国际会展中心"
            }, ensure_ascii=False)

        return json.dumps({
            "event_name": event_name,
            "time": "未知",
            "location": "未知"
        }, ensure_ascii=False)


class BizDispatcherTool(Tool):
    def __init__(self):
        schema = {
            "type": "object",
            "properties": {
                "intent": {
                    "type": "string",
                    "enum": ["CREATE_MEETING", "QUERY_FREE_SLOT", "CREATE_SCHEDULE", "UPDATE_SCHEDULE", "CANCEL_SCHEDULE"],
                    "description": "要执行的业务意图"
                },
                "slots": {
                    "type": "object",
                    "description": "业务槽位。title(标题/关键词,用于查找或创建); start_time(ISO8601,可选-不传则系统自动推荐空闲时间); end_time(ISO8601,可选); duration_minutes(时长,默认60); platform(dingtalk/tencent); attendees(参会人名单数组); UPDATE_SCHEDULE时用new_start_time表示新时间",
                    "additionalProperties": True
                }
            },
            "required": ["intent", "slots"]
        }
        super().__init__("schedule_management", "调用后端业务系统创建会议、创建日程、查询空闲时间、或取消日程。", schema)

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")

        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        async def _run():
            async with AsyncSessionLocal() as db:
                dispatcher = BizDispatcher(db)
                return await dispatcher.dispatch(user_id, params['intent'], params['slots'])

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    result = loop.run_until_complete(_run())
                else:
                    result = asyncio.run(_run())
            except RuntimeError:
                result = asyncio.run(_run())

            print(f"[Tool Result] {self.name}: {result}")
            return json.dumps({
                "status": "success",
                "message": result
            }, ensure_ascii=False)
        except Exception as e:
            print(f"[Tool Error] {self.name}: {e}")
            return json.dumps({
                "status": "error",
                "message": f"执行失败: {str(e)}"
            }, ensure_ascii=False)


amap_key = os.environ.get("AMAP_API_KEY", "")

registered_tools = [
    AMapRouteTool(amap_key),
    MockEventTimeTool(),
    BizDispatcherTool()
]

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.schema
        }
    } for tool in registered_tools
]

AVAILABLE_TOOLS = {tool.name: tool for tool in registered_tools}
