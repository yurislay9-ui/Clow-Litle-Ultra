"""
Unit tests for the IntentRouter.
"""

import unittest
import asyncio
from unittest.mock import MagicMock, AsyncMock
import os

# Add the src directory to the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from intent_router import IntentRouter
from tools.tool_registry import ToolRegistry

class TestIntentRouter(unittest.TestCase):
    """
    Tests the functionality of the IntentRouter.
    """

    def setUp(self):
        """Set up a mock config and tool registry for each test."""
        self.mock_config = {
            "intents": {
                "registry_path": "dummy/path.json"
            }
        }

        # Mock the ToolRegistry
        self.mock_tool_registry = MagicMock(spec=ToolRegistry)

        # Mock the intent registry file content
        self.intents_data = {
            "intents": [
                {
                    "name": "greet",
                    "triggers": {"keywords": ["hello"]},
                    "handler": {"type": "inline", "details": {"response": "Hi there!"}}
                },
                {
                    "name": "check_health",
                    "triggers": {"keywords": ["status"]},
                    "handler": {"type": "tool", "details": {"name": "health_checker", "function": "get_system_health"}}
                }
            ]
        }

    def test_initialization(self):
        """Test that the router initializes correctly and loads intents."""
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.intents_data))) as mock_file:
            with unittest.mock.patch('os.path.exists', return_value=True):
                router = IntentRouter(self.mock_config, self.mock_tool_registry)
                self.assertEqual(len(router.intents), 2)
                self.assertIn("greet", router.intents)

    async def test_route_to_inline_handler(self):
        """Test routing to a simple inline response."""
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.intents_data))) as mock_file:
            with unittest.mock.patch('os.path.exists', return_value=True):
                router = IntentRouter(self.mock_config, self.mock_tool_registry)
                response = await router.route("hello there")
                self.assertEqual(response, "Hi there!")

    async def test_route_to_tool_handler_success(self):
        """Test routing to a tool and successful execution."""
        # Mock the tool and its method
        mock_tool = MagicMock()
        mock_tool.get_system_health = AsyncMock(return_value="System is A-OK")
        self.mock_tool_registry.get_tool.return_value = mock_tool

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.intents_data))) as mock_file:
            with unittest.mock.patch('os.path.exists', return_value=True):
                router = IntentRouter(self.mock_config, self.mock_tool_registry)
                response = await router.route("what is the system status?")
                
                self.assertEqual(response, "System is A-OK")
                self.mock_tool_registry.get_tool.assert_called_once_with("health_checker")
                mock_tool.get_system_health.assert_awaited_once()

    async def test_route_to_tool_handler_tool_not_found(self):
        """Test routing to a tool when the tool is not in the registry."""
        self.mock_tool_registry.get_tool.return_value = None

        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.intents_data))) as mock_file:
            with unittest.mock.patch('os.path.exists', return_value=True):
                router = IntentRouter(self.mock_config, self.mock_tool_registry)
                response = await router.route("check status")
                
                self.assertIn("internal error", response.lower())
                self.assertIn("tool is not available", response.lower())

    async def test_no_intent_found(self):
        """Test the response when no intent matches the user's message."""
        with unittest.mock.patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(self.intents_data))) as mock_file:
            with unittest.mock.patch('os.path.exists', return_value=True):
                router = IntentRouter(self.mock_config, self.mock_tool_registry)
                response = await router.route("I would like to order a pizza.")
                
                self.assertIn("I don't understand", response)

# To run the async tests
if __name__ == '__main__':
    unittest.main()
