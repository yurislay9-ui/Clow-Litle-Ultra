"""
Terminal Command-Line Interface (CLI) Channel.

This module provides a simple command-line interface for interacting with the agent.
It listens for user input, passes it to the IntentRouter, and prints the response.
"""

import asyncio
import logging
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    from intent_router import IntentRouter

class TerminalCLI:
    """
    A communication channel that uses the terminal for input and output.
    """

    def __init__(self, router: 'IntentRouter', config: Dict[str, Any]):
        """
        Initializes the TerminalCLI channel.

        Args:
            router (IntentRouter): The intent router that will process messages.
            config (Dict[str, Any]): The configuration for this channel.
        """
        self.router = router
        self.config = config
        self.is_running = False
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("TerminalCLI initialized.")

    async def start_listening(self):
        """
        Starts the main loop to listen for and process user input.
        """
        self.is_running = True
        welcome_message = self.config.get("welcome_message", "CLAW Lite Ultra Pro is ready.")
        print(welcome_message)

        while self.is_running:
            try:
                message = await asyncio.to_thread(self._read_input)

                if message.lower() == 'exit':
                    self.is_running = False
                    self.logger.info("Exit command received. Shutting down CLI channel.")
                    continue

                if message:
                    response = await self.router.route(message)
                    assistant_prompt = self.config.get("assistant_prompt", "[ASSISTANT]: ")
                    print(f"{assistant_prompt}{response}")

            except (EOFError, KeyboardInterrupt):
                self.is_running = False
                self.logger.info("CLI channel interrupted. Shutting down.")
            except Exception as e:
                self.logger.error(f"An error in the CLI channel: {e}", exc_info=True)
                print("An unexpected error occurred. Please check the logs.")

    def _read_input(self) -> str:
        """
        Reads a line of input from the user.
        """
        user_prompt = self.config.get("user_prompt", "[USER]: ")
        return input(user_prompt)

    def stop(self):
        """
        Stops the listening loop.
        """
        self.is_running = False
