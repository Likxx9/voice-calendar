import json
import os
import ssl
import urllib.request
import urllib.parse
import time
import asyncio
import uuid
import concurrent.futures
from datetime import datetime, timedelta

def ensure_naive(dt: datetime) -> datetime:
    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)
    return dt

def get_now() -> datetime:
    return datetime.now()
from app.database import AsyncSessionLocal
from app.services.biz_dispatcher import BizDispatcher
from dotenv import load_dotenv

_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

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
        super().__init__("query_traffic_route", "单一交通方式的路线规划（驾车/公交/步行/骑行）。仅在用户明确指定了交通方式时使用此工具。", schema, timeout=8, retries=2)
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

    def _query_single_mode(self, start_loc, end_loc, origin, dest, mode):
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

            return {
                "mode": mode,
                "estimated_duration": f"{duration_min}分钟",
                "distance": f"{distance_km}公里",
                "duration_minutes": duration_min
            }

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")
        origin = params["origin"]
        dest = params["destination"]
        mode = params.get("mode", "driving")

        for attempt in range(self.retries + 1):
            try:
                start_loc = self._geocode(origin)
                end_loc = self._geocode(dest)
                result = self._query_single_mode(start_loc, end_loc, origin, dest, mode)
                result["status"] = "success"
                result["route"] = f"{origin} 到 {dest}"
                return json.dumps(result, ensure_ascii=False)
            except Exception as e:
                if attempt == self.retries:
                    return json.dumps({"error": str(e)}, ensure_ascii=False)
                time.sleep(1)


class MultiModeRouteTool(Tool):
    """用户未指定交通方式时，并发查询多种出行方式并返回对比结果。"""

    def __init__(self, api_key):
        schema = {
            "type": "object",
            "properties": {
                "origin": {"type": "string", "description": "出发地名称"},
                "destination": {"type": "string", "description": "目的地名称"},
                "date": {"type": "string", "description": "出发日期，YYYY-MM-DD"},
                "target_time": {"type": "string", "description": "期望出发时间，如 15:00"}
            },
            "required": ["origin", "destination"]
        }
        super().__init__(
            "query_multi_mode_route",
            "当用户想要在不同城市之间出行/跨城出行（如'杭州到上海'、'去上海'），或者去某地但未明确指定具体交通方式时，必须首选调用此工具。同时查询驾车、公交、步行、骑行多种方式，返回对比结果。对于跨城出行还会提示可选高铁。重要：绝对不能直接调用 schedule_management(CREATE_SCHEDULE)！",
            schema, timeout=10, retries=1
        )
        self.api_key = api_key
        self._route_tool = AMapRouteTool(api_key)

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")
        origin = params["origin"]
        dest = params["destination"]
        date_str = params.get("date", "")
        target_time = params.get("target_time", "")

        try:
            start_loc = self._route_tool._geocode(origin)
            end_loc = self._route_tool._geocode(dest)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

        modes = ["driving", "transit", "walking", "riding"]
        results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            futures = {
                pool.submit(self._safe_query, start_loc, end_loc, origin, dest, m): m
                for m in modes
            }
            for f in concurrent.futures.as_completed(futures):
                r = f.result()
                if r:
                    results.append(r)

        results.sort(key=lambda x: x.get("duration_minutes", 9999))

        start_coords = [float(c) for c in start_loc.split(",")]
        end_coords = [float(c) for c in end_loc.split(",")]
        straight_km = self._haversine(start_coords[1], start_coords[0], end_coords[1], end_coords[0])
        is_intercity = straight_km > 80

        mode_labels = {
            "driving": "🚗 驾车", "transit": "🚌 公交", "walking": "🚶 步行", "riding": "🚲 骑行"
        }
        for r in results:
            r["label"] = mode_labels.get(r["mode"], r["mode"])

        output = {
            "status": "success",
            "route": f"{origin} 到 {dest}",
            "straight_line_distance_km": round(straight_km, 1),
            "is_intercity": is_intercity,
            "options": results
        }

        if is_intercity:
            output["hint"] = f"{origin}到{dest}属于跨城出行（直线{round(straight_km)}公里），建议考虑高铁。可以调用 query_train_schedule 查询车次。"

        output["await_user_choice"] = True
        output["broadcasts"] = [{
            "type": "transport_options",
            "data": {
                "origin": origin,
                "destination": dest,
                "date": date_str,
                "target_time": target_time,
                "is_intercity": is_intercity,
                "options": results,
            }
        }]

        return json.dumps(output, ensure_ascii=False)

    def _safe_query(self, start_loc, end_loc, origin, dest, mode):
        try:
            return self._route_tool._query_single_mode(start_loc, end_loc, origin, dest, mode)
        except Exception as e:
            print(f"[MultiMode] {mode} 查询失败: {e}")
            return None

    @staticmethod
    def _haversine(lat1, lon1, lat2, lon2):
        import math
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class _12306Session:
    """管理 12306 的 cookie 会话，避免被反爬拦截。"""

    _UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

    def __init__(self):
        self._cookie = ""
        self._lock = __import__('threading').Lock()

    def ensure(self):
        with self._lock:
            if self._cookie:
                return
            try:
                req = urllib.request.Request(
                    "https://kyfw.12306.cn/otn/leftTicket/init",
                    headers={"User-Agent": self._UA},
                )
                with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
                    cookies = resp.headers.get_all("Set-Cookie")
                    if cookies:
                        self._cookie = "; ".join(c.split(";")[0] for c in cookies)
                        print(f"[12306] Cookie 获取成功")
            except Exception as e:
                print(f"[12306] Cookie 获取失败: {e}")

    def get_cookie(self):
        self.ensure()
        return self._cookie

    def invalidate(self):
        with self._lock:
            self._cookie = ""


_12306_session = _12306Session()


class _StationCodeCache:
    """12306 站点编码缓存，首次使用时从 12306 拉取全量站点数据。"""

    def __init__(self):
        self._codes = None
        self._lock = __import__('threading').Lock()

    def _load(self):
        url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        with urllib.request.urlopen(req, timeout=10, context=_ssl_ctx) as resp:
            text = resp.read().decode("utf-8-sig")

        mapping = {}
        # 格式: @bjb|北京北|VAP|beijingbei|bjb|0@...
        for entry in text.split("@"):
            parts = entry.split("|")
            if len(parts) >= 4:
                chinese_name = parts[1]
                code = parts[2]
                mapping[chinese_name] = code
        return mapping

    def get(self, city_name: str):
        with self._lock:
            if self._codes is None:
                try:
                    self._codes = self._load()
                    print(f"[12306] 站点数据加载完成，共 {len(self._codes)} 个站点")
                except Exception as e:
                    print(f"[12306] 站点数据加载失败: {e}")
                    self._codes = {}

        clean = city_name
        for suffix in ["市", "站"]:
            if clean.endswith(suffix):
                clean = clean[:-1]

        if clean in self._codes:
            return self._codes[clean]

        # 尝试加"站"后缀 / 主要火车站名
        for variant in [clean, clean + "南", clean + "北", clean + "东", clean + "西"]:
            if variant in self._codes:
                return self._codes[variant]

        # 模糊匹配：城市名包含在站名中
        for name, code in self._codes.items():
            if clean in name:
                return code

        return None


_station_cache = _StationCodeCache()


class TrainScheduleTool(Tool):
    """通过 12306 API 实时查询高铁/动车车次信息。"""

    def __init__(self):
        schema = {
            "type": "object",
            "properties": {
                "origin_city": {"type": "string", "description": "出发城市，如'北京'"},
                "destination_city": {"type": "string", "description": "到达城市，如'上海'"},
                "date": {"type": "string", "description": "出发日期，ISO8601格式 YYYY-MM-DD。不传则默认今天。"},
                "target_time": {"type": "string", "description": "用户期望的出发时间，格式 HH:MM。如果用户提到了上下午或具体时间，必须提取为 24 小时制传入。如果没提，则不传。"}
            },
            "required": ["origin_city", "destination_city"]
        }
        super().__init__(
            "query_train_schedule",
            "查询两个城市之间的高铁/动车车次（实时 12306 数据）。返回车次号、发车到站时间、耗时和座位信息。注意：如果用户已经明确指明了要选择哪趟车次（例如'我选G744'），绝对不能再次调用此工具查询，而必须直接从对话历史中提取车次信息，调用 schedule_management(intent=CREATE_SCHEDULE) 进行日程创建！另外，若用户未指定具体交通方式（如只说'从杭州到上海'而没提到'坐高铁'），禁止直接调用此工具，必须先调用 query_multi_mode_route 规划多种出行方式！",
            schema, timeout=15
        )

    def _query_12306(self, from_code, to_code, date_str):
        _12306_session.ensure()
        base_headers = {
            "User-Agent": _12306Session._UA,
            "Accept": "application/json, text/javascript, */*",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://kyfw.12306.cn/otn/leftTicket/init",
            "Cookie": _12306_session.get_cookie(),
        }

        data = None
        for endpoint in ["queryG", "queryZ", "query", "queryA"]:
            url = (
                f"https://kyfw.12306.cn/otn/leftTicket/{endpoint}"
                f"?leftTicketDTO.train_date={date_str}"
                f"&leftTicketDTO.from_station={from_code}"
                f"&leftTicketDTO.to_station={to_code}"
                f"&purpose_codes=ADULT"
            )
            req = urllib.request.Request(url, headers=base_headers)
            try:
                with urllib.request.urlopen(req, timeout=self.timeout, context=_ssl_ctx) as resp:
                    text = resp.read().decode("utf-8-sig")
                    if text.startswith("<!DOCTYPE") or text.startswith("<html"):
                        _12306_session.invalidate()
                        _12306_session.ensure()
                        base_headers["Cookie"] = _12306_session.get_cookie()
                        continue
                    data = json.loads(text)
                    if data.get("data") and data["data"].get("result"):
                        break
            except Exception:
                continue

        if not data or not data.get("data") or not data["data"].get("result"):
            return []

        station_map = data["data"].get("map", {})
        trains = []

        for raw in data["data"]["result"]:
            fields = raw.split("|")
            if len(fields) < 35:
                continue

            train_no = fields[3]
            # 只保留高铁(G)、动车(D)、城际(C)
            if not train_no or train_no[0] not in ("G", "D", "C"):
                continue

            from_station = station_map.get(fields[6], fields[6])
            to_station = station_map.get(fields[7], fields[7])
            depart_time = fields[8]  # HH:MM
            arrive_time = fields[9]  # HH:MM
            duration_str = fields[10]  # HH:MM

            # 解析耗时为分钟
            try:
                dur_parts = duration_str.split(":")
                duration_min = int(dur_parts[0]) * 60 + int(dur_parts[1])
            except (ValueError, IndexError):
                duration_min = 0

            # 座位余票: 二等座=fields[30], 一等座=fields[31], 商务座=fields[32]
            second_class = fields[30] if len(fields) > 30 else "--"
            first_class = fields[31] if len(fields) > 31 else "--"
            business_class = fields[32] if len(fields) > 32 else "--"

            trains.append({
                "train_no": train_no,
                "from_station": from_station,
                "to_station": to_station,
                "depart_time": depart_time,
                "arrive_time": arrive_time,
                "duration_str": duration_str,
                "duration_minutes": duration_min,
                "second_class_seats": second_class,
                "first_class_seats": first_class,
                "business_class_seats": business_class,
            })

        return trains

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")
        origin = params["origin_city"]
        dest = params["destination_city"]
        date_str = params.get("date", get_now().strftime("%Y-%m-%d"))
        target_time = params.get("target_time")

        from_code = _station_cache.get(origin)
        to_code = _station_cache.get(dest)

        if not from_code:
            return json.dumps({
                "status": "error",
                "message": f"未找到出发城市'{origin}'对应的火车站编码，请检查城市名称。"
            }, ensure_ascii=False)
        if not to_code:
            return json.dumps({
                "status": "error",
                "message": f"未找到目的城市'{dest}'对应的火车站编码，请检查城市名称。"
            }, ensure_ascii=False)

        try:
            trains = self._query_12306(from_code, to_code, date_str)
        except Exception as e:
            print(f"[12306] 查询异常: {e}")
            return json.dumps({
                "status": "error",
                "message": f"12306 查询失败: {str(e)}"
            }, ensure_ascii=False)

        if not trains:
            return json.dumps({
                "status": "no_available",
                "message": f"{date_str} {origin}到{dest}暂无高铁/动车班次，建议换个日期或使用 query_traffic_route 查询其他交通方式。"
            }, ensure_ascii=False)

        now = get_now()
        is_today = (date_str == now.strftime("%Y-%m-%d"))

        no_seat_values = {"", "--", "无", "0"}

        available = []
        for t in trains:
            if is_today:
                try:
                    depart_dt = ensure_naive(datetime.strptime(f"{date_str} {t['depart_time']}", "%Y-%m-%d %H:%M"))
                    if depart_dt <= now:
                        continue
                except ValueError:
                    pass

            seats_2 = t.get("second_class_seats", "--")
            seats_1 = t.get("first_class_seats", "--")
            seats_b = t.get("business_class_seats", "--")
            if seats_2 in no_seat_values and seats_1 in no_seat_values and seats_b in no_seat_values:
                continue

            hours = t["duration_minutes"] // 60
            mins = t["duration_minutes"] % 60
            duration_display = f"{hours}小时{mins}分钟" if hours else f"{mins}分钟"

            available.append({
                "train_no": t["train_no"],
                "from_station": t["from_station"],
                "to_station": t["to_station"],
                "depart_time": f"{date_str} {t['depart_time']}",
                "arrive_time": f"{date_str} {t['arrive_time']}",
                "duration": duration_display,
                "duration_minutes": t["duration_minutes"],
                "second_class_seats": seats_2,
                "first_class_seats": seats_1,
                "business_class_seats": seats_b,
            })

        if target_time:
            try:
                import re
                nums = re.findall(r'\d+', target_time)
                if nums:
                    h = int(nums[0])
                    m = int(nums[1]) if len(nums) > 1 else 0
                    if "下午" in target_time or "pm" in target_time.lower():
                        if h < 12: h += 12
                    target_min = h * 60 + m
                    def get_diff(t):
                        time_str = t['depart_time'].split(" ")[1]
                        parts = time_str.split(":")
                        t_min = int(parts[0]) * 60 + int(parts[1])
                        return abs(t_min - target_min)
                    available.sort(key=get_diff)
                    # 严格过滤：仅保留发车时间在期望出发时间前后 120 分钟（2小时）内的车次，确保不展示整天的无关车次
                    filtered = [t for t in available if get_diff(t) <= 120]
                    if not filtered:
                        # 如果没有在 2 小时内的车次，则作为兜底保留最近的 5 趟车次
                        filtered = available[:5]
                    available = filtered
            except Exception as e:
                print(f"[TrainScheduleTool] parse target_time error: {e}")


        if not available:
            return json.dumps({
                "status": "no_available",
                "message": f"{date_str} {origin}到{dest}已无可乘坐的班次，建议改日期。"
            }, ensure_ascii=False)

        output = {
            "status": "success",
            "origin": origin,
            "destination": dest,
            "date": date_str,
            "total_trains": len(available),
            "trains": available[:15],
            "note": "以上为 12306 实时车次数据。请等待用户选择车次后再安排日程。"
        }
        output["await_user_choice"] = True
        output["broadcasts"] = [{
            "type": "train_options",
            "data": {
                "origin": origin,
                "destination": dest,
                "date": date_str,
                "trains": available[:8],
            }
        }]
        return json.dumps(output, ensure_ascii=False)


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
                    "enum": ["CREATE_MEETING", "QUERY_FREE_SLOT", "QUERY_SCHEDULE", "CREATE_SCHEDULE", "UPDATE_SCHEDULE", "CANCEL_SCHEDULE"],
                    "description": "要执行的业务意图。注意：对于未指定具体交通工具（如坐高铁、飞机、驾车等）的跨城/异地行程规划（如'从杭州到上海'），严禁使用 CREATE_SCHEDULE，必须调用 query_multi_mode_route！"
                },
                "slots": {
                    "type": "object",
                    "description": "业务槽位。title(标题); start_time(ISO8601,可选); end_time(ISO8601,可选); duration_minutes(时长,默认60); time_range_start(ISO8601,用于多天活动的搜索起点); time_range_end(ISO8601,多天活动的搜索终点); platform(dingtalk/tencent); attendees(参会人数组); is_fixed_time(布尔值, 高铁/航班等不可随意更改时间的客观行程请设为True); date(YYYY-MM-DD, 用户提到日期但没说具体时间时传此字段，如'6月2号添加会议'则传date='2026-06-02'；删除/修改日程时也用于区分同名日程)",
                    "additionalProperties": True
                }
            },
            "required": ["intent", "slots"]
        }
        super().__init__("schedule_management", "调用后端业务系统管理日程。支持：创建日程(CREATE_SCHEDULE)、创建会议(CREATE_MEETING)、查询空闲时间(QUERY_FREE_SLOT)、查询某天已有日程(QUERY_SCHEDULE)、修改日程(UPDATE_SCHEDULE)、删除/取消日程(CANCEL_SCHEDULE)。用户询问某天有什么安排或日程时使用QUERY_SCHEDULE；要求删除或去掉日程时必须使用CANCEL_SCHEDULE。特别注意：如果是跨城出行且未明确指定交通工具，严禁直接调用本工具的 CREATE_SCHEDULE 意图创建日程，而必须先调用 query_multi_mode_route 进行规划出行方式并等待用户确认！", schema)

    def execute(self, params):
        print(f"\n[Tool Execution] {self.name} called with: {params}")

        user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        try:
            dispatcher_ref = [None]
            async def _run_with_ref():
                async with AsyncSessionLocal() as db:
                    dispatcher = BizDispatcher(db)
                    dispatcher_ref[0] = dispatcher
                    return await dispatcher.dispatch(user_id, params['intent'], params['slots'])

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import nest_asyncio
                    nest_asyncio.apply()
                    result = loop.run_until_complete(_run_with_ref())
                else:
                    result = asyncio.run(_run_with_ref())
            except (RuntimeError, ImportError):
                try:
                    result = asyncio.run(_run_with_ref())
                except RuntimeError:
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        result = executor.submit(lambda: asyncio.run(_run_with_ref())).result()

            print(f"[Tool Result] {self.name}: {result}")
            tool_result = {"status": "success", "message": result}
            d = dispatcher_ref[0]
            if d:
                if d.last_event_action:
                    tool_result["event_action"] = d.last_event_action
                if d.pending_broadcasts:
                    tool_result["broadcasts"] = [
                        {"type": t, "data": data} for t, data in d.pending_broadcasts
                    ]
            return json.dumps(tool_result, ensure_ascii=False)
        except Exception as e:
            print(f"[Tool Error] {self.name}: {e}")
            return json.dumps({
                "status": "error",
                "message": f"执行失败: {str(e)}"
            }, ensure_ascii=False)


amap_key = os.environ.get("AMAP_API_KEY", "")

registered_tools = [
    AMapRouteTool(amap_key),
    MultiModeRouteTool(amap_key),
    TrainScheduleTool(),
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
