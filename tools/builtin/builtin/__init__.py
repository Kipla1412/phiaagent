
from tools.builtin.memory import MemoryTool
from tools.builtin.web_fetch import WebFetchTool
from tools.builtin.web_search import WebSearchTool


__all__ = [
    "WebSearchTool",
    "WebFetchTool",
    "MemoryTool",
]


def get_all_builtin_tools() -> list[type]:
    return [
        WebSearchTool,
        WebFetchTool,
        MemoryTool,
    ]
