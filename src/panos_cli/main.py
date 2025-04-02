"""Main CLI entry point for panos-cli."""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from panos_cli import commands
from panos_cli.config import load_config
from panos_cli.utils import configure_logging

# Configure console and logger
console = Console()
logger = logging.getLogger(__name__)

# Create main Typer app
app = typer.Typer(
    name="panos-cli",
    help="CLI tool for managing PAN-OS configurations with multi-threading support",
    add_completion=True,
)

# Register command groups
app.add_typer(commands.objects.app, name="objects", help="Manage address objects and groups")
app.add_typer(commands.objects.test_app, name="test", help="Test PAN-OS connectivity")
app.add_typer(commands.objects.show_app, name="show", help="Show detailed information")


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """
    PAN-OS CLI - Efficiently manage PAN-OS configurations with multi-threading support.

    Command pattern: panos-cli <action> <object-type> <object> [options]

    Examples:
    - panos-cli set objects address --name web-server --ip-netmask 192.168.1.100/32
    - panos-cli load objects address --file addresses.yaml
    - panos-cli delete objects address --name web-server
    """
    # Configure logging
    configure_logging(verbose)

    # Load configuration (even if we don't use it here, this validates it's available)
    try:
        load_config(config_file)
    except Exception as e:
        logger.error(f"Configuration error: {str(e)}")
        if verbose:
            console.print_exception(show_locals=True)
        sys.exit(1)


if __name__ == "__main__":
    app()
