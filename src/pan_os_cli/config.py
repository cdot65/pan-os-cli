"""Configuration management for panos-cli."""

import os
import pathlib
from typing import Optional

from dynaconf import Dynaconf
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
        config_path: Path to the configuration file (default: ~/.pan-os-cli/config.yaml)

    Returns:
        PanosConfig: Configuration object
    """
    if config_path is None:
        # Use os.path.join for cross-platform path compatibility
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".pan-os-cli")
        config_path = os.path.join(config_dir, "config.yaml")

    # Create config directory if it doesn't exist
    config_dir = os.path.dirname(config_path)
    pathlib.Path(config_dir).mkdir(parents=True, exist_ok=True)

    # Load configuration with dynaconf
    settings = Dynaconf(
        envvar_prefix="PANOS",
        settings_files=[config_path],
        environments=True,
    )

    # Create config with environment variables as fallback
    config = PanosConfig(
        username=settings.get("username", ""),
        password=settings.get("password", ""),
        hostname=settings.get("hostname", ""),
        api_key=settings.get("api_key", None),
        mock_mode=settings.get("mock_mode", False),
        thread_pool_size=settings.get("thread_pool_size", 10),
    )

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


def get_or_create_config(
    config_path: Optional[str] = None, mock_mode: bool = False, thread_pool_size: int = 10
) -> PanosConfig:
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
