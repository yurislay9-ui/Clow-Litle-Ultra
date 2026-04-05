"""
Unit tests for the ToolRegistry.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

# Mock the tool class before it's even imported by the module we're testing
from tools.tool_registry import ToolRegistry


@patch('tools.tool_registry.HealthChecker', new_callable=MagicMock)
class TestToolRegistry(unittest.TestCase):
    """
    Tests the functionality of the ToolRegistry.
    """

    def setUp(self):
        self.mock_config = {"some_config": "value"}

    def test_initialization_and_tool_loading(self, MockHealthChecker):
        """Test that the registry initializes and loads tools correctly."""
        # Configure the mock class to have a name
        MockHealthChecker.__name__ = "HealthChecker"
        
        registry = ToolRegistry(self.mock_config)
        
        self.assertIn("health_checker", registry._tools)
        # The tool instance in the registry should be an instance of our mock
        self.assertIsInstance(registry._tools["health_checker"], MockHealthChecker)
        # Ensure the tool was instantiated with the config
        MockHealthChecker.assert_called_once_with(self.mock_config)

    def test_get_tool_success(self, MockHealthChecker):
        """Test retrieving a successfully loaded tool."""
        registry = ToolRegistry(self.mock_config)
        tool = registry.get_tool("health_checker")
        self.assertIsNotNone(tool)
        self.assertIsInstance(tool, MockHealthChecker)

    def test_get_tool_not_found(self, MockHealthChecker):
        """Test retrieving a non-existent tool."""
        registry = ToolRegistry(self.mock_config)
        tool = registry.get_tool("non_existent_tool")
        self.assertIsNone(tool)

    def test_tool_loading_failure(self, MockHealthChecker):
        """Test that the registry handles an error during tool instantiation."""
        # Configure the mock to raise an exception when instantiated
        MockHealthChecker.side_effect = Exception("Failed to initialize")

        # Even with the error, the registry should initialize without crashing
        registry = ToolRegistry(self.mock_config)
        
        # The faulty tool should not be in the loaded tools registry
        self.assertNotIn("health_checker", registry._tools)
        # And attempting to get it should return None
        self.assertIsNone(registry.get_tool("health_checker"))


if __name__ == '__main__':
    unittest.main()
