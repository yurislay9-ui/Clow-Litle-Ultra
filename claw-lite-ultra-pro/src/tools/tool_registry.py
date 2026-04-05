"""
Tool Registry for CLAW Lite Ultra Pro.

This module is responsible for discovering, loading, and providing access
to the available tools in the system.
"""

import logging
from typing import Dict, Any, Type

# Import tool classes here
from monitoring.health_checker import HealthChecker

class ToolRegistry:
    """
    Manages the lifecycle of tools in the application.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the ToolRegistry and loads all available tools.
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self._tools: Dict[str, Any] = {}
        self._load_tools()

    def _load_tools(self):
        """
        Loads and instantiates all tools that the system can use.
        """
        self.logger.info("Loading tools...")
        # A mapping of tool names (as used in intent registry) to their classes
        tool_classes = {
            "health_checker": HealthChecker,
        }

        for name, tool_class in tool_classes.items():
            try:
                self._tools[name] = tool_class(self.config)
                self.logger.info(f"Successfully loaded tool: '{name}'")
            except Exception as e:
                self.logger.error(f"Failed to load tool '{name}': {e}", exc_info=True)

    def get_tool(self, name: str) -> Optional[Any]:
        """
        Retrieves an instantiated tool by its name.
        """
        tool = self._tools.get(name)
        if not tool:
            self.logger.warning(f"Attempted to access non-existent tool: '{name}'")
        return tool
