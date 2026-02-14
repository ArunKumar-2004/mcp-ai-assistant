class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register_tool(self, tool_name: str, handler):
        self._tools[tool_name] = handler

    def get_tool(self, tool_name: str):
        return self._tools.get(tool_name)

    def list_tools(self) -> list:
        return list(self._tools.keys())
