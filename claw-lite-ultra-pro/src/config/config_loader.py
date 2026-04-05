"""
Configuration loader for CLAW Lite Ultra Pro.

This module handles loading configuration settings from TOML files,
allowing for environment-specific overrides.
"""

import os
import toml
from typing import Dict, Any

# The default environment if none is specified
DEFAULT_ENVIRONMENT = 'development'

# Path to the configuration directory
CONFIG_DIR = os.path.join(os.path.dirname(__file__))
BASE_CONFIG_PATH = os.path.join(CONFIG_DIR, 'defaults.toml')

def load_config(env: str = None) -> Dict[str, Any]:
    """
    Loads the base configuration and merges it with environment-specific settings.

    Args:
        env (str, optional): The environment to load. If not provided, it will
                             fall back to the `APP_ENV` environment variable or the
                             default environment.

    Returns:
        Dict[str, Any]: The fully loaded and merged configuration.

    Raises:
        FileNotFoundError: If the base configuration file is not found.
    """
    if not os.path.exists(BASE_CONFIG_PATH):
        raise FileNotFoundError(f"Base configuration file not found at: {BASE_CONFIG_PATH}")

    # Load base configuration
    with open(BASE_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = toml.load(f)

    # Determine the environment
    environment = env or os.getenv('APP_ENV', DEFAULT_ENVIRONMENT)
    env_config_path = os.path.join(CONFIG_DIR, 'environment_profiles', f'{environment}.toml')

    # Load and merge environment-specific configuration if it exists
    if os.path.exists(env_config_path):
        with open(env_config_path, 'r', encoding='utf-8') as f:
            env_config = toml.load(f)
            # Deep merge the environment config into the base config
            _deep_merge(config, env_config)

    return config

def _deep_merge(source: Dict, destination: Dict) -> Dict:
    """
    Recursively merges two dictionaries.

    Args:
        source (Dict): The source dictionary to merge from.
        destination (Dict): The destination dictionary to merge into.

    Returns:
        Dict: The merged dictionary.
    """
    for key, value in source.items():
        if isinstance(value, dict) and key in destination and isinstance(destination[key], dict):
            destination[key] = _deep_merge(value, destination[key])
        else:
            destination[key] = value
    return destination
