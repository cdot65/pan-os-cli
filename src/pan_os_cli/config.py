"""Configuration management for panos-cli."""

import os
import pathlib
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class PanosConfig(BaseModel):
    """Configuration model for PAN-OS connections and client behavior."""

    username: str = Field(
        default="",
        description="Username for PAN-OS authentication",
    )
    password: str = Field(
        default="",
        description="Password for PAN-OS authentication",
    )
    hostname: str = Field(
        default="",
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
    is_ngfw: bool = Field(
        default=False,
        description="Flag to indicate if the device is a Next-Generation Firewall",
    )


def load_config(config_path: Optional[str] = None) -> PanosConfig:
    """
    Load configuration exclusively from config.yaml file.
    Environment variables are intentionally ignored.

    Args:
        config_path: Path to the configuration file
                     (default: looks in ~/.pan-os-cli/config.yaml and ~/.panos-cli/config.yaml)

    Returns:
        PanosConfig: Configuration object
    """
    if config_path is None:
        # Use os.path.join for cross-platform path compatibility
        home_dir = os.path.expanduser("~")

        # Try both configuration paths
        config_paths = [
            os.path.join(home_dir, ".pan-os-cli", "config.yaml"),  # Primary location as per PRD
            os.path.join(home_dir, ".panos-cli", "config.yaml"),  # Alternative location
        ]

        # Use the first config file that exists
        for path in config_paths:
            if os.path.exists(path):
                config_path = path
                break
        else:
            # If no config file exists, use the default path
            config_path = config_paths[0]

    # Create config directory if it doesn't exist
    config_dir = os.path.dirname(config_path)
    pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)

    # Load YAML file directly
    try:
        with open(config_path, "r") as f:
            yaml_content = yaml.safe_load(f)
    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to load config from {config_path}: {str(e)}")
        yaml_content = {}

    # Extract values directly from the YAML structure
    username = password = hostname = api_key = ""
    mock_mode = False
    thread_pool_size = 10

    # Handle "default" section as per PRD format
    if yaml_content and "default" in yaml_content:
        default_config = yaml_content["default"]
        username = default_config.get("username", "")
        password = default_config.get("password", "")
        hostname = default_config.get("hostname", "")
        api_key = default_config.get("api_key", None)
        mock_mode = default_config.get("mock_mode", False)
        thread_pool_size = default_config.get("thread_pool_size", 10)
    # Alternative format with credentials/settings sections
    elif yaml_content:
        if "credentials" in yaml_content:
            credentials = yaml_content["credentials"]
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            hostname = credentials.get("hostname", "")
            api_key = credentials.get("api_key", None)

        if "settings" in yaml_content:
            settings = yaml_content["settings"]
            mock_mode = settings.get("mock_mode", False)
            thread_pool_size = settings.get("thread_pool_size", 10)

    # Create config with settings from file only
    config = PanosConfig(
        username=username,
        password=password,
        hostname=hostname,
        api_key=api_key,
        mock_mode=mock_mode if not isinstance(mock_mode, str) else mock_mode.lower() == "true",
        thread_pool_size=thread_pool_size,
        is_ngfw=False,  # This will be set by the CLI flag if needed
    )

    # Add some debug logging to help diagnose configuration issues
    import logging

    logger = logging.getLogger(__name__)
    logger.debug(f"Loaded configuration from: {config_path}")
    logger.debug(f"YAML content: {yaml_content}")
    logger.debug(f"Hostname: {config.hostname}, Username: {'Set' if config.username else 'Not set'}")
    logger.debug(f"API Key: {'Set' if config.api_key else 'Not set'}")
    logger.debug(f"Thread Pool Size: {config.thread_pool_size}, Mock Mode: {config.mock_mode}")

    return config


def generate_api_key(config: PanosConfig) -> str:
    """
    Generate an API key using pan-os-python.

    Args:
        config: PAN-OS configuration with username, password, and hostname

    Returns:
        Generated API key as string

    Raises:
        ImportError: If pan-os-python is not installed
        ValueError: If API key generation fails
    """
    # If in mock mode, return dummy key
    if config.mock_mode:
        return "mock-api-key"

    try:
        import xml.etree.ElementTree as Et

        import requests

        # Use direct XML API request since Panorama class does not have generate_api_key method
        url = f"https://{config.hostname}/api/"
        params = {"type": "keygen", "user": config.username, "password": config.password}

        # Disable SSL warnings in case of self-signed certificates
        try:
            import urllib3

            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        except ImportError:
            pass

        # Make the API request
        response = requests.get(url, params=params, verify=False, timeout=10)
        response.raise_for_status()

        # Parse the XML response
        root = Et.fromstring(response.text)
        api_key = root.find(".//key")

        if api_key is not None:
            return api_key.text

        raise ValueError("API key not found in response")
    except ImportError as err:
        raise ImportError("Required libraries (requests) are needed to generate API key") from err
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to connect to {config.hostname}: {str(e)}") from e
    except Exception as e:
        raise ValueError(f"Failed to generate API key: {str(e)}") from e


def get_or_create_config(config_path: Optional[str] = None, mock_mode: bool = False, thread_pool_size: int = 10) -> PanosConfig:
    """
    Get or create a configuration object with optional overrides.

    Args:
        config_path: Path to the configuration file (default: ~/.pan-os-cli/config.yaml)
        mock_mode: Override mock_mode setting
        thread_pool_size: Override thread_pool_size setting

    Returns:
        PanosConfig: Configuration object
    """
    # Load base configuration
    config = load_config(config_path)

    # Apply overrides
    config.mock_mode = mock_mode
    config.thread_pool_size = thread_pool_size

    # Ensure we have an API key if not in mock mode
    if not config.mock_mode and not config.api_key and config.username and config.password:
        config.api_key = generate_api_key(config)

    return config
