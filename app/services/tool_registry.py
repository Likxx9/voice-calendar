import json
import concurrent.futures
from app.services.tools import AVAILABLE_TOOLS

class ToolScheduler:
    def __init__(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

    def execute_parallel(self, tool_calls):
        """
        并行执行 Zhipu 返回的多个 tool_call。
        返回结果列表。
        """
        futures = {}
        for tool_call in tool_calls:
            func_name = tool_call.function.name
            try:
                func_args = json.loads(tool_call.function.arguments)
            except Exception:
                func_args = {}

            if func_name in AVAILABLE_TOOLS:
                tool_instance = AVAILABLE_TOOLS[func_name]
                future = self.executor.submit(tool_instance.execute, func_args)
                futures[future] = (tool_call.id, func_name)
            else:
                dummy_future = concurrent.futures.Future()
                dummy_future.set_result(json.dumps({"error": f"Tool {func_name} not found."}))
                futures[dummy_future] = (tool_call.id, func_name)

        results = []
        for future in concurrent.futures.as_completed(futures.keys()):
            tool_call_id, func_name = futures[future]
            try:
                result_data = future.result()
            except Exception as e:
                result_data = json.dumps({"error": f"Exception in {func_name}: {str(e)}"})

            results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "content": result_data
            })

        return results
