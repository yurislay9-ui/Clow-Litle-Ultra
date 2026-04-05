"""
Unit tests for the TerminalCLI channel.
"""

import asyncio
import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../src')))

from channels.terminal_cli import TerminalCLI
from intent_router import IntentRouter


class TestTerminalCLI(unittest.TestCase):
    """
    Tests the functionality of the TerminalCLI communication channel.
    """

    def setUp(self):
        """Set up a mock router and config for each test."""
        self.mock_router = MagicMock(spec=IntentRouter)
        self.mock_config = {
            "welcome_message": "Ready",
            "user_prompt": "U: ",
            "assistant_prompt": "A: "
        }

    def test_initialization(self):
        """Test that the CLI initializes correctly."""
        cli = TerminalCLI(self.mock_router, self.mock_config)
        self.assertEqual(cli.router, self.mock_router)
        self.assertEqual(cli.config, self.mock_config)
        self.assertFalse(cli.is_running)

    @patch('builtins.print')
    @patch('asyncio.to_thread')
    async def test_start_listening_and_exit(self, mock_to_thread, mock_print):
        """Test that the listening loop starts and can be exited."""
        cli = TerminalCLI(self.mock_router, self.mock_config)
        
        # Mock the input to return 'exit' on the first call
        mock_input_future = asyncio.Future()
        mock_input_future.set_result('exit')
        mock_to_thread.return_value = mock_input_future
        
        # Run start_listening and expect it to complete quickly
        await asyncio.wait_for(cli.start_listening(), timeout=1.0)
        
        # Verify the welcome message was printed
        mock_print.assert_any_call("Ready")
        self.assertFalse(cli.is_running)

    @patch('builtins.print')
    @patch('asyncio.to_thread')
    async def test_message_routing(self, mock_to_thread, mock_print):
        """Test that a user message is correctly routed and the response is printed."""
        cli = TerminalCLI(self.mock_router, self.mock_config)
        
        # Configure the mock router to return a specific response
        self.mock_router.route = AsyncMock(return_value="Router says hello!")
        
        # Simulate the user typing a message, then 'exit'
        async def input_side_effect(*args, **kwargs):
            if mock_to_thread.call_count == 1:
                return "test message"
            else:
                return "exit"
        
        mock_to_thread.side_effect = input_side_effect

        await asyncio.wait_for(cli.start_listening(), timeout=1.0)

        # Verify that the router was called with the user's message
        self.mock_router.route.assert_awaited_once_with("test message")
        
        # Verify that the assistant's response was printed
        mock_print.assert_any_call("A: Router says hello!")


if __name__ == '__main__':
    # This allows running async tests directly
    unittest.main()

