from typing import Any, Callable, Awaitable

ToolHandler = Callable[[dict[str, Any]], Awaitable[Any]]

TOOL_REGISTRY: dict[str, ToolHandler] = {}
_TOOL_DECLARATIONS: list[dict] = []


def register(declaration: dict):
    """Decorator. declaration debe ser un tool dict en formato OpenAI/Groq."""
    def decorator(fn: ToolHandler) -> ToolHandler:
        TOOL_REGISTRY[declaration["function"]["name"]] = fn
        _TOOL_DECLARATIONS.append(declaration)
        return fn
    return decorator


def get_tool_declarations() -> list[dict]:
    return list(_TOOL_DECLARATIONS)
