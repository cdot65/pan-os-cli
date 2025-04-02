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
    Generate API key using username and password.

    Args:
        config: PanosConfig instance with username and password

    Returns:
        str: Generated API key
    """
    if config.mock_mode:
        return "mock-api-key"

    try:
        from panos.panorama import Panorama

        device = Panorama(
            hostname=config.hostname,
            api_username=config.username,
            api_password=config.password,
        )
        api_key = device.generate_api_key()
        return api_key
    except ImportError:
        raise ImportError("pan-os-python is required to generate API key")
    except Exception as e:
        raise ValueError(f"Failed to generate API key: {str(e)}")
