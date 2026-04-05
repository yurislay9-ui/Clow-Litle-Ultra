"""
Main entry point for the CLAW Lite Ultra Pro application.

This script initializes the necessary components, loads the configuration,
and starts the main application loop.
"""

import asyncio
import logging
from config.config_loader import load_config
from intent_router import IntentRouter
from channels.terminal_cli import TerminalCLI
from tools.tool_registry import ToolRegistry

async def main():
    """
    The main asynchronous function that orchestrates the application startup.
    """
    
    # Load configuration
    try:
        config = load_config()
    except FileNotFoundError as e:
        logging.critical(f"Configuration file not found: {e}", exc_info=True)
        return

    # Configure logging
    log_level = config.get("logging", {}).get("level", "INFO").upper()
    log_format = config.get("logging", {}).get("format", "%(asctime)s - %(levelname)s - %(message)s")
    logging.basicConfig(level=log_level, format=log_format)

    logging.info("Initializing CLAW Lite Ultra Pro...")

    try:
        # Initialize the tool registry
        tool_registry = ToolRegistry(config)

        # Initialize the intent router
        router = IntentRouter(config, tool_registry)

        # Initialize the communication channel
        channel = TerminalCLI(router, config.get('channels', {}).get('terminal', {}))

        # Start the channel's interaction loop
        await channel.start_listening()

    except Exception as e:
        logging.critical(f"A critical error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application shut down by user.")
    finally:
        logging.info("CLAW Lite Ultra Pro has shut down.")

