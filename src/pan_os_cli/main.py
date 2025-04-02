"""Main CLI entry point for pan-os-cli."""

import logging
import sys
from typing import Optional

import typer
from rich.console import Console

from pan_os_cli import commands
from pan_os_cli.config import load_config
from pan_os_cli.utils import configure_logging

# Configure console and logger
console = Console()
logger = logging.getLogger(__name__)

# Create main Typer app
app = typer.Typer(
    name="pan-os-cli",
    help="CLI tool for managing PAN-OS configurations with multi-threading support",
    add_completion=True,
)

# Create action apps
show_app = typer.Typer(help="Show PAN-OS configuration objects")
set_app = typer.Typer(help="Create or update PAN-OS configuration objects")
delete_app = typer.Typer(help="Delete PAN-OS configuration objects")
load_app = typer.Typer(help="Bulk load PAN-OS configuration objects from file")
test_app = typer.Typer(help="Test various PAN-OS operations")

# Create object type apps for each action
show_objects_app = typer.Typer(help="Show PAN-OS objects like addresses and address groups")
set_objects_app = typer.Typer(
    help="Create or update PAN-OS objects like addresses and address groups"
)
delete_objects_app = typer.Typer(help="Delete PAN-OS objects like addresses and address groups")
load_objects_app = typer.Typer(help="Bulk load PAN-OS objects like addresses and address groups")
test_objects_app = typer.Typer(help="Test PAN-OS objects operations with load testing")

# Register action apps to main app
app.add_typer(show_app, name="show")
app.add_typer(set_app, name="set")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")
app.add_typer(test_app, name="test")

# Register object type apps to action apps
show_app.add_typer(show_objects_app, name="objects")
set_app.add_typer(set_objects_app, name="objects")
delete_app.add_typer(delete_objects_app, name="objects")
load_app.add_typer(load_objects_app, name="objects")
test_app.add_typer(test_objects_app, name="objects")


# Test auth command
@test_app.command("auth")
def test_auth_wrapper(
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Test PAN-OS authentication and connectivity."""
    commands.objects.test_auth(mock=mock, threads=threads)


# Test addresses command
@test_objects_app.command("addresses")
def test_addresses_wrapper(
    count: int = typer.Option(100, help="Number of address objects to create"),
    devicegroup: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group to add addresses to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
    commit: bool = typer.Option(False, help="Commit changes after loading"),
):
    """Test creating multiple address objects using multithreading."""
    commands.objects.test_addresses(
        count=count, devicegroup=devicegroup, mock=mock, threads=threads, commit=commit
    )


# Show addresses command
@show_objects_app.command("addresses")
def show_addresses_wrapper(
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group containing the addresses"
    ),
    name: Optional[str] = typer.Option(
        None, help="Name of the address object to show (omit for all)"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Show address objects with detailed information."""
    commands.objects.show_addresses(
        name=name, device_group=device_group, mock=mock, threads=threads
    )


# Show address groups command
@show_objects_app.command("address-groups")
def show_address_groups_wrapper(
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group containing the address groups"
    ),
    name: Optional[str] = typer.Option(
        None, help="Name of the address group to show (omit for all)"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Show address groups with detailed information."""
    commands.objects.get_address_group(
        name=name, devicegroup=device_group, mock=mock, threads=threads
    )


# Set addresses command
@set_objects_app.command("addresses")
def set_addresses_wrapper(
    name: str = typer.Option(..., help="Name of the address object"),
    type: str = typer.Option(..., help="Type of address (ip-netmask, fqdn, ip-range)"),
    value: str = typer.Option(..., help="Value of the address (depends on type)"),
    description: Optional[str] = typer.Option(None, help="Description of the address object"),
    tags: str = typer.Option(None, help="Comma-separated list of tags to apply"),
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group to add the address to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Create or update an address object."""
    # Process tags if provided
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]

    # Map type to the appropriate parameter
    if type == "ip-netmask":
        commands.objects.set_address(
            name=name,
            ip_netmask=value,
            fqdn=None,
            ip_range=None,
            description=description,
            tags=tag_list,
            devicegroup=device_group,
            mock=mock,
            threads=threads,
        )
    elif type == "fqdn":
        commands.objects.set_address(
            name=name,
            ip_netmask=None,
            fqdn=value,
            ip_range=None,
            description=description,
            tags=tag_list,
            devicegroup=device_group,
            mock=mock,
            threads=threads,
        )
    elif type == "ip-range":
        commands.objects.set_address(
            name=name,
            ip_netmask=None,
            fqdn=None,
            ip_range=value,
            description=description,
            tags=tag_list,
            devicegroup=device_group,
            mock=mock,
            threads=threads,
        )
    else:
        console.print(
            f"[bold red]Error:[/] Invalid address type '{type}'. "
            f"Must be one of: ip-netmask, fqdn, ip-range"
        )
        raise typer.Exit(1)


# Delete addresses command
@delete_objects_app.command("addresses")
def delete_addresses_wrapper(
    name: str = typer.Option(..., help="Name of the address object to delete"),
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group containing the address"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Delete an address object."""
    commands.objects.delete_address(name=name, devicegroup=device_group, mock=mock, threads=threads)


# Load addresses command
@load_objects_app.command("addresses")
def load_addresses_wrapper(
    file: str = typer.Option(..., help="Path to YAML file with address objects"),
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group to add addresses to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
    commit: bool = typer.Option(False, help="Commit changes after loading"),
):
    """Bulk load address objects from YAML file."""
    commands.objects.load_address(
        file=file, devicegroup=device_group, mock=mock, threads=threads, commit=commit
    )


# Set address groups command
@set_objects_app.command("address-groups")
def set_address_groups_wrapper(
    name: str = typer.Option(..., help="Name of the address group"),
    static_members: str = typer.Option(None, help="Comma-separated list of static members"),
    dynamic_filter: str = typer.Option(None, help="Filter expression for dynamic group"),
    description: Optional[str] = typer.Option(None, help="Description of the address group"),
    tags: str = typer.Option(None, help="Comma-separated list of tags to apply"),
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group to add the address group to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Create or update an address group."""
    # Process tags if provided
    tag_list = []
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]

    # Process static members if provided
    static_member_list = []
    if static_members:
        static_member_list = [member.strip() for member in static_members.split(",")]

    if static_members and dynamic_filter:
        console.print("[bold red]Error:[/] Cannot specify both static_members and dynamic_filter")
        raise typer.Exit(1)

    if not static_members and not dynamic_filter:
        console.print("[bold red]Error:[/] Must specify either static_members or dynamic_filter")
        raise typer.Exit(1)

    # Call the command in objects.py
    commands.objects.set_address_group(
        name=name,
        description=description,
        static_members=static_member_list,
        dynamic_filter=dynamic_filter,
        tags=tag_list,
        devicegroup=device_group,
        mock=mock,
        threads=threads,
    )


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Path to config file"),
):
    """
    PAN-OS CLI - Efficiently manage PAN-OS configurations with multi-threading support.

    Command pattern: pan-os-cli <action> <object-type> <object> [options]

    Examples:
    - pan-os-cli show objects addresses --device-group LAB_DG
    - pan-os-cli show objects address-groups -dg LAB_DG
    - pan-os-cli set objects addresses --name test123 --type ip-netmask
      --value 1.1.1.1/32 --tags "Automation,test"
    - pan-os-cli delete objects addresses --name test123
    - pan-os-cli load objects addresses --file example.yaml
    """
    # Configure logging
    configure_logging(verbose)

    # Load configuration (even if we don't use it here, this validates it's available)
    try:
        load_config(config_file)
    except Exception as e:
        console.print(f"[bold red]Error loading configuration:[/] {str(e)}")
        logger.error(f"Error loading configuration: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    app()
