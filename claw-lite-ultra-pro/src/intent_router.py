"""
Intent Router for CLAW Lite Ultra Pro - Production-Ready

This module interprets user input and routes it to the appropriate handler
based on a configurable intent registry.
"""

import json
import logging
from typing import Dict, Any, Optional
from tools.tool_registry import ToolRegistry

class IntentRouter:
    """
    Routes user intentions to handlers based on a JSON registry.
    """

    def __init__(self, config: Dict[str, Any], tool_registry: ToolRegistry):
        """
        Initializes the IntentRouter with application configuration and tool registry.
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.tool_registry = tool_registry
        self.intents = self._load_intent_registry()
        self.logger.info("IntentRouter initialized with %d intents.", len(self.intents))

    def _load_intent_registry(self) -> Dict[str, Any]:
        """
        Loads the intent registry from the path specified in the config.
        """
        registry_path = self.config["intents"]["registry_path"]
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                return {intent['name']: intent for intent in json.load(f)["intents"]}
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.critical(f"Failed to load intent registry from '{registry_path}': {e}", exc_info=True)
            raise

    async def route(self, message: str) -> str:
        """
        Routes the user's message by finding a matching intent.
        """
        self.logger.debug(f"Routing message: '{message}'")
        normalized_message = message.lower().strip()

        matched_intent = self._find_intent(normalized_message)

        if not matched_intent:
            self.logger.warning(f"No intent found for message: '{message}'")
            return "I'm sorry, I don't understand that request. Please try rephrasing."

        return await self._handle_intent(matched_intent)

    def _find_intent(self, message: str) -> Optional[Dict[str, Any]]:
        """
        Finds the first intent that matches the message based on keywords.
        """
        for intent in self.intents.values():
            for keyword in intent["triggers"]["keywords"]:
                if keyword in message:
                    return intent
        return None

    async def _handle_intent(self, intent: Dict[str, Any]) -> str:
        """
        Handles the matched intent based on its handler type.
        """
        handler_type = intent["handler"]["type"]
        self.logger.info(f"Handling intent '{intent['name']}' with handler: '{handler_type}'")

        if handler_type == "inline":
            return intent["handler"]["details"]["response"]
        
        if handler_type == "tool":
            tool_name = intent["handler"]["details"]["name"]
            function_name = intent["handler"]["details"]["function"]
            
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                self.logger.error(f"Tool '{tool_name}' is not registered.")
                return "An internal error occurred. The requested tool is not available."

            try:
                method_to_call = getattr(tool, function_name)
                return await method_to_call()
            except AttributeError:
                self.logger.error(f"Tool '{tool_name}' does not have a method '{function_name}'.")
                return "An internal error occurred. The requested tool function is not available."
            except Exception as e:
                self.logger.error(f"An error occurred while executing tool '{tool_name}': {e}", exc_info=True)
                return "An error occurred while processing your request."

        return f"Unknown handler type: {handler_type}"
