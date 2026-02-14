class AgentContext:
    def __init__(self):
        self._results = {}

    def add_tool_result(self, tool_name: str, result: dict):
        self._results[tool_name] = result

    def get_context_snapshot(self) -> dict:
        return self._results.copy()

    def clear(self):
        self._results = {}
