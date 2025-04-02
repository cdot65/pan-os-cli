"""Configuration management for panos-cli."""

import os
import pathlib
import yaml
from typing import Optional

from pydantic import BaseModel, Field


class PanosConfig(BaseModel):
    """Configuration model for PAN-OS connections and client behavior."""

    username: str = Field(
        default_factory=lambda: os.environ.get("panos_username", ""),
        description="Username for PAN-OS authentication",
    )
    password: str = Field(
        default_factory=lambda: os.environ.get("panos_password", ""),
        description="Password for PAN-OS authentication",
    )
    hostname: str = Field(
        default_factory=lambda: os.environ.get("panos_host", ""),
        description="Hostname/IP of the PAN-OS device",
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for PAN-OS authentication (auto-generated if not provided)",
    )
    mock_mode: bool = Field(
        default=False,
        description="Run in mock mode without making actual API calls",
    )
    thread_pool_size: int = Field(
        default=10,
        description="Number of threads to use for concurrent operations",
    )


def load_config(config_path: Optional[str] = None) -> PanosConfig:
    """
    Load configuration from environment variables and configuration file.

    Args:
        config_path: Path to the configuration file (default: ~/.panos-cli/config.yaml)

    Returns:
        PanosConfig: Configuration object
    """
    if config_path is None:
        config_path = os.path.expanduser("~/.panos-cli/config.yaml")

    # Create config directory if it doesn't exist
    config_dir = os.path.dirname(config_path)
    pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)

    # Define settings files in order of precedence
    setting_files = [
        "settings.yaml",                         # Current directory settings
        ".secrets.yaml",                         # Current directory secrets
        config_path                              # User home directory config
    ]

    # Initialize default values from environment variables
    username = os.environ.get("panos_username", "")
    password = os.environ.get("panos_password", "")
    hostname = os.environ.get("panos_host", "")
    api_key = None
    mock_mode = False
    thread_pool_size = 10

    # Try to load configuration from YAML files
    for file_path in setting_files:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as file:
                    yaml_config = yaml.safe_load(file)
                    
                    if yaml_config and isinstance(yaml_config, dict):
                        # Extract credential values
                        if 'credentials' in yaml_config and isinstance(yaml_config['credentials'], dict):
                            creds = yaml_config['credentials']
                            if 'username' in creds:
                                username = creds['username']
                            if 'password' in creds:
                                password = creds['password']
                            if 'hostname' in creds:
                                hostname = creds['hostname']
                            if 'api_key' in creds:
                                api_key = creds['api_key']

                        # Extract settings values
                        if 'settings' in yaml_config and isinstance(yaml_config['settings'], dict):
                            settings = yaml_config['settings']
                            if 'mock_mode' in settings:
                                mock_mode = settings['mock_mode']
                            if 'thread_pool_size' in settings:
                                thread_pool_size = settings['thread_pool_size']
            except Exception:
                # Silently continue if there's an error reading the file
                pass

    # Create config with environment variables as fallback
    config = PanosConfig(
        username=username,
        password=password,
        hostname=hostname,
        api_key=api_key,
        mock_mode=mock_mode,
        thread_pool_size=thread_pool_size,
    )

    return config


def generate_api_key(config: PanosConfig) -> str:
    """
    Generate API key using username and password.

    Args:
        config: PanosConfig instance with username and password

    Returns:
        str: Generated API key
    """
    raise NotImplementedError("API key generation not yet implemented")
