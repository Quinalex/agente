"""
Tool registry and management system.
"""

import logging
from typing import Any, Dict, Optional

from app.tools.base import BaseTool
from app.tools.builtin import (
    CodeExecutorTool,
    EmailTool,
    FileTool,
    APICallerTool,
    SearchTool,
)

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register built-in tools."""
        builtin_tools = [
            SearchTool(),
            CodeExecutorTool(),
            FileTool(),
            EmailTool(),
            APICallerTool(),
        ]

        for tool in builtin_tools:
            self.register(tool.name, tool)
            logger.info(f"Registered tool: {tool.name}")

    def register(self, name: str, tool: BaseTool) -> None:
        """Register a new tool."""
        self.tools[name] = tool
        logger.info(f"Tool registered: {name}")

    def get(self, name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self.tools.get(name)

    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools with metadata."""
        return {
            name: {"description": tool.description, "schema": tool.get_schema()}
            for name, tool in self.tools.items()
        }

    async def execute(self, name: str, **kwargs) -> Any:
        """Execute a tool."""
        tool = self.get(name)
        if not tool:
            raise ValueError(f"Tool not found: {name}")

        logger.debug(f"Executing tool: {name} with args: {kwargs}")
        return await tool.execute(**kwargs)


# Global tool registry instance
tool_registry = ToolRegistry()
