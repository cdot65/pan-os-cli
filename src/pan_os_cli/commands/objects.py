"""Commands for managing PAN-OS address objects and groups."""

import logging
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

import typer
from panos.errors import PanDeviceError, PanXapiError
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from pan_os_cli.client import PanosClient
from pan_os_cli.config import get_or_create_config
from pan_os_cli.models.objects import Address, AddressGroup
from pan_os_cli.utils import create_progress_tracker, load_yaml, validate_objects_from_yaml

# Console setup
console = Console()
logger = logging.getLogger(__name__)

# Create Typer app for this command module
app = typer.Typer()

# Define Typer option defaults as module-level singletons
EMPTY_LIST = []
NONE_DEFAULT = None
SHARED_DEFAULT = "Shared"
MOCK_DEFAULT = False
THREADS_DEFAULT = 10
COMMIT_DEFAULT = False
WAIT_DEFAULT = True
TIMEOUT_DEFAULT = 600

# Define module-level singletons for typer.Option calls
TAGS_OPTION = typer.Option(EMPTY_LIST, help="Tags to apply to the address object")
STATIC_MEMBERS_OPTION = typer.Option(EMPTY_LIST, help="Static members for static groups")
GROUP_TAGS_OPTION = typer.Option(EMPTY_LIST, help="Tags to apply to the address group")

# Define a Typer app
app = typer.Typer()


def create_client(mock=False, threads=10):
    """Create a PAN-OS client."""
    config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
    return PanosClient(config)


@app.command("set-address")
def set_address(
    name: str = typer.Option(..., help="Name of the address object"),
    ip_netmask: Optional[str] = typer.Option(
        NONE_DEFAULT, "--ip-netmask", help="IP address or network in CIDR notation"
    ),
    fqdn: Optional[str] = typer.Option(NONE_DEFAULT, "--fqdn", help="Fully qualified domain name"),
    ip_range: Optional[str] = typer.Option(
        NONE_DEFAULT, "--ip-range", help="IP range (e.g., 192.168.1.1-192.168.1.10)"
    ),
    description: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Description of the address object"
    ),
    tags: List[str] = TAGS_OPTION,
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to add the address to"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Create or update an address object."""
    try:
        console.print(f"Creating address: [bold blue]{name}[/]")

        # Create address object
        address = Address(
            name=name,
            ip_netmask=ip_netmask,
            fqdn=fqdn,
            ip_range=ip_range,
            description=description,
            tags=tags,
        )

        # Connect to PAN-OS and create the object
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)
        result = client.create_address_object(address, devicegroup)

        if result:
            console.print(f"[bold green]Success:[/] Created address '{name}'")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error creating address object")
        raise typer.Exit(1) from e


@app.command("set-address-group")
def set_address_group(
    name: str = typer.Option(..., help="Name of the address group"),
    description: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Description of the address group"
    ),
    static_members: List[str] = STATIC_MEMBERS_OPTION,
    dynamic_filter: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Filter expression (for dynamic groups)"
    ),
    tags: List[str] = GROUP_TAGS_OPTION,
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to add the address group to"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Create or update an address group."""
    try:
        console.print(f"Creating address group: [bold blue]{name}[/]")

        # Create address group object
        address_group = AddressGroup(
            name=name,
            description=description,
            static_members=static_members,
            dynamic_filter=dynamic_filter,
            tags=tags,
        )

        # Connect to PAN-OS and create the object
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)
        result = client.create_address_group(address_group, devicegroup)

        if result:
            console.print(f"[bold green]Success:[/] Created address group '{name}'")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error creating address group")
        raise typer.Exit(1) from e


@app.command("delete-address")
def delete_address(
    name: str = typer.Option(..., help="Name of the address object to delete"),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group containing the address"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Delete an address object."""
    try:
        console.print(f"Deleting address: [bold blue]{name}[/]")

        # Connect to PAN-OS and delete the object
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)
        result = client.delete_address_object(name, devicegroup)

        if result:
            console.print(f"[bold green]Success:[/] Deleted address '{name}'")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error deleting address object")
        raise typer.Exit(1) from e


@app.command("delete-address-group")
def delete_address_group(
    name: str = typer.Option(..., help="Name of the address group to delete"),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group containing the address group"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Delete an address group."""
    try:
        console.print(f"Deleting address group: [bold blue]{name}[/]")

        # Connect to PAN-OS and delete the object
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)
        result = client.delete_address_group(name, devicegroup)

        if result:
            console.print(f"[bold green]Success:[/] Deleted address group '{name}'")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error deleting address group")
        raise typer.Exit(1) from e


@app.command("load-address")
def load_address(
    file: str = typer.Option(..., help="Path to YAML file with address objects"),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to add addresses to"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
    commit: bool = typer.Option(COMMIT_DEFAULT, help="Commit changes after loading"),
):
    """Bulk load address objects from YAML file using multi-threading."""
    try:
        # Validate input file exists
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[bold red]Error:[/] File not found: {file}")
            raise typer.Exit(1)

        # Load and validate address objects from YAML
        yaml_data = load_yaml(file)
        panos_objects = validate_objects_from_yaml(yaml_data, "addresses", Address)

        if not panos_objects:
            console.print("[yellow]Warning:[/] No valid address objects found in the file")
            return

        # Connect to PAN-OS
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Create the objects with multithreading
        with create_progress_tracker(len(panos_objects), "Loading address objects") as progress:
            console.print(
                f"Loading [bold blue]{len(panos_objects)}[/] address objects with "
                f"[bold green]{threads}[/] threads..."
            )

            with ThreadPoolExecutor(max_workers=threads) as executor:
                # Submit all tasks
                future_to_obj = {
                    executor.submit(client.create_address_object, obj, devicegroup): obj
                    for obj in panos_objects
                }

                # Process results as they complete
                results = []
                for future in as_completed(future_to_obj):
                    obj = future_to_obj[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error creating address object {obj.name}: {str(e)}")
                    progress.advance(0)

                successful = len([r for r in results if r is not None])
                console.print(
                    f"[bold green]Success:[/] {successful}/{len(panos_objects)} "
                    f"address objects loaded"
                )

        # Commit changes if requested
        if commit and successful > 0:
            console.print("Committing changes...")
            commit_result = client.commit(admins="Test address objects bulk load")
            console.print(f"Commit job ID: {commit_result}")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error loading address objects")
        raise typer.Exit(1) from e


@app.command("load-address-group")
def load_address_group(
    file: str = typer.Option(..., help="Path to YAML file with address groups"),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to add address groups to"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
    commit: bool = typer.Option(COMMIT_DEFAULT, help="Commit changes after loading"),
):
    """Bulk load address groups from YAML file using multi-threading."""
    try:
        # Validate input file exists
        file_path = Path(file)
        if not file_path.exists():
            console.print(f"[bold red]Error:[/] File not found: {file}")
            raise typer.Exit(1)

        # Load and validate address group objects from YAML
        yaml_data = load_yaml(file)
        panos_objects = validate_objects_from_yaml(yaml_data, AddressGroup)

        if not panos_objects:
            console.print("[yellow]Warning:[/] No valid address group objects found in the file")
            return

        # Connect to PAN-OS
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Create the objects with multithreading
        with create_progress_tracker(len(panos_objects), "Loading address groups") as progress:
            console.print(
                f"Loading [bold blue]{len(panos_objects)}[/] address groups with "
                f"[bold green]{threads}[/] threads..."
            )

            with ThreadPoolExecutor(max_workers=threads) as executor:
                # Submit all tasks
                future_to_obj = {
                    executor.submit(client.create_address_group, obj, devicegroup): obj
                    for obj in panos_objects
                }

                # Process results as they complete
                results = []
                for future in as_completed(future_to_obj):
                    obj = future_to_obj[future]
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        logger.error(f"Error creating address group {obj.name}: {str(e)}")
                    progress.advance(0)

                successful = len([r for r in results if r is not None])
                console.print(
                    f"[bold green]Success:[/] {successful}/{len(panos_objects)} "
                    f"address groups loaded"
                )

        # Commit changes if requested
        if commit and successful > 0:
            console.print("Committing changes...")
            commit_result = client.commit("Address groups bulk load")
            console.print(f"Commit job ID: {commit_result}")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error loading address groups")
        raise typer.Exit(1) from e


@app.command("get-address")
def get_address(
    name: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Name of the address object to get (omit for all)"
    ),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to get addresses from"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Get address objects."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Get addresses from PAN-OS
        try:
            _get_address_impl(client, name, devicegroup)
        except (PanDeviceError, PanXapiError) as e:
            console.print(f"[bold red]Error:[/] Failed to retrieve addresses: {str(e)}")
            raise typer.Exit(1) from e

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error getting address objects")
        raise typer.Exit(1) from e


def _get_address_impl(client, name, devicegroup):
    """Implementation for getting address object(s)."""
    # Get addresses based on whether a specific name was provided
    addresses = _fetch_addresses(client, name, devicegroup)

    # Create a table for display
    table = Table(title=f"Address Objects in '{devicegroup}'")
    _setup_address_table_columns(table)

    # Process each address and add to table
    for addr in addresses:
        addr_info = _extract_address_info(addr, devicegroup)
        table.add_row(
            addr_info["name"],
            addr_info["type"],
            addr_info["value"],
            addr_info["description"],
            addr_info["tags"],
        )

    # Display results
    console.print(table)
    console.print(f"[bold green]Total:[/] {len(addresses)} address objects")


def _fetch_addresses(client, name, devicegroup):
    """Fetch addresses from PAN-OS based on input parameters."""
    if name:
        # Get specific address by name
        address = client.get_address(name, devicegroup)
        if not address:
            console.print(f"[bold red]Error:[/] Address '{name}' not found.")
            raise typer.Exit(1)
        return [address]
    else:
        # Get all addresses
        addresses = client.list_addresses(devicegroup)
        if not addresses:
            console.print(
                f"[bold yellow]Warning:[/] No addresses found in device group '{devicegroup}'."
            )
            raise typer.Exit(0)
        return addresses


def _setup_address_table_columns(table):
    """Set up columns for address display table."""
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Value", style="yellow")
    table.add_column("Description")
    table.add_column("Tags")


def _extract_address_info(addr, devicegroup):
    """Extract relevant information from an address object or dictionary."""
    # Return structure for consistent data format
    result = {"name": "", "type": "Unknown", "value": "", "description": "", "tags": ""}

    # Handle different input formats (object vs dictionary)
    if hasattr(addr, "name"):
        # Process AddressObject instance
        _process_address_object(addr, result)
    else:
        # Process dictionary format (from list_addresses)
        _process_address_dict(addr, result)

    return result


def _process_address_object(addr, result):
    """Process an AddressObject instance to extract information."""
    # Extract basic info
    result["name"] = addr.name
    result["description"] = getattr(addr, "description", "")

    # Process tags
    if hasattr(addr, "tag") and addr.tag:
        result["tags"] = ", ".join(addr.tag)

    # Determine address type and value
    if hasattr(addr, "type"):
        if addr.type == "ip-netmask":
            result["type"] = "IP/Netmask"
            result["value"] = getattr(addr, "value", "")
        elif addr.type == "ip-range":
            result["type"] = "IP Range"
            result["value"] = getattr(addr, "value", "")
        elif addr.type == "fqdn":
            result["type"] = "FQDN"
            result["value"] = getattr(addr, "value", "")


def _process_address_dict(addr, result):
    """Process an address dictionary to extract information."""
    # Extract basic info
    result["name"] = addr.get("name", "")
    result["description"] = addr.get("description", "")

    # Process tags
    if "tag" in addr and addr["tag"]:
        result["tags"] = ", ".join(addr["tag"])

    # Determine address type and value
    if "ip-netmask" in addr and addr["ip-netmask"]:
        result["type"] = "IP/Netmask"
        result["value"] = addr["ip-netmask"]
    elif "ip-range" in addr and addr["ip-range"]:
        result["type"] = "IP Range"
        result["value"] = addr["ip-range"]
    elif "fqdn" in addr and addr["fqdn"]:
        result["type"] = "FQDN"
        result["value"] = addr["fqdn"]


@app.command("get-address-group")
def get_address_group(
    name: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Name of the address group to get (omit for all)"
    ),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--devicegroup", "-dg", help="Device group to get address groups from"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Get address groups."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # If name is provided, get specific address group, otherwise get all
        groups = []
        if name:
            group = client.get_address_group(name, devicegroup)
            if group:
                groups = [group]
        else:
            groups = client.get_address_groups(devicegroup)

        if not groups:
            if name:
                console.print(
                    f"[yellow]No address group found:[/] '{name}' in device group '{devicegroup}'"
                )
            else:
                console.print(f"[yellow]No address groups found[/] in device group '{devicegroup}'")
            return

        # Display results in a table
        table = Table(title=f"Address Groups in {devicegroup}")
        table.add_column("Name", style="cyan", width=20)
        table.add_column("Type", style="green", width=15)
        table.add_column("Value", style="yellow", width=30)
        table.add_column("Description", width=30)
        table.add_column("Device Group", style="magenta", width=20)

        # Add rows to the table
        for group in groups:
            group_type = ""
            group_value = ""

            # Determine address group type and value
            try:
                if hasattr(group, "static_value") and group.static_value:
                    group_type = "Static"
                    group_value = ", ".join(group.static_value)
                elif hasattr(group, "dynamic_value") and group.dynamic_value:
                    group_type = "Dynamic"
                    group_value = group.dynamic_value
            except Exception:
                pass

            # Add row to the table
            table.add_row(
                group.name,
                group_type,
                group_value,
                group.description or "",
                devicegroup,
            )

        console.print(table)
        console.print(f"[bold green]Total:[/] {len(groups)} address groups")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error getting address groups")
        raise typer.Exit(1) from e


@app.command("commit-changes")
def commit_changes(
    description: Optional[str] = typer.Option(NONE_DEFAULT, help="Description for the commit"),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
    wait: bool = typer.Option(WAIT_DEFAULT, help="Wait for commit to complete"),
    timeout: int = typer.Option(
        TIMEOUT_DEFAULT, help="Maximum time to wait for commit completion (seconds)"
    ),
):
    """Commit configuration changes to PAN-OS."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Commit changes
        console.print("Committing changes to PAN-OS device...")
        job_id = client.commit(description)
        console.print(f"Commit job ID: {job_id}")

        # Wait for commit to complete if requested
        if wait and not mock:
            console.print("Waiting for commit to complete...")
            start_time = time.time()

            while time.time() - start_time < timeout:
                status = client.check_commit_status(job_id)
                progress = status.get("progress", 0)
                console.print(f"Commit progress: [bold blue]{progress}%[/]")

                if status.get("status") == "success":
                    console.print("[bold green]Commit completed successfully[/]")
                    break
                elif status.get("status") in ["failed", "error"]:
                    console.print(
                        f"[bold red]Commit failed:[/] {status.get('result', 'Unknown error')}"
                    )
                    raise typer.Exit(1)

                time.sleep(5)

            if time.time() - start_time >= timeout:
                console.print(f"[yellow]Warning:[/] Commit timeout after {timeout} seconds")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error during commit")
        raise typer.Exit(1) from e


@app.command("check-commit")
def check_commit(
    job_id: str = typer.Option(..., help="Commit job ID to check"),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Check the status of a commit job."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Check commit status
        console.print(f"Checking status of commit job [bold blue]{job_id}[/]...")
        status = client.check_commit_status(job_id)

        if status.get("status") == "success":
            console.print("[bold green]Commit completed successfully[/]")
        elif status.get("status") in ["failed", "error"]:
            console.print(f"[bold red]Commit failed:[/] {status.get('result', 'Unknown error')}")
        else:
            progress = status.get("progress", 0)
            console.print(f"Commit in progress: [bold blue]{progress}%[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error checking commit status")
        raise typer.Exit(1) from e


@app.command("test-auth")
def test_auth(
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Test PAN-OS authentication and connectivity."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        # Handle differently for mock mode
        if mock:
            console.print("[bold green]Running in mock mode - no actual connection will be made[/]")
            console.print("Configuration appears to be valid")
            console.print("[bold blue]Mock connection successful![/]")
            return

        # Test connectivity using system info refresh
        console.print(f"Testing connection to [bold blue]{client.config.hostname}[/]...")
        client.device.refresh_system_info()

        # Display connection information
        console.print("[bold green]Connection successful![/]")
        console.print(f"Connected to: [bold blue]{client.config.hostname}[/]")

        # Get device info based on device type
        from panos.panorama import Panorama

        if isinstance(client.device, Panorama):
            console.print("Device Type: [bold]Panorama[/]")
            console.print(f"Hostname: [bold]{client.device.hostname}[/]")
            console.print(f"Serial: [bold]{client.device.serial}[/]")
            console.print(f"SW Version: [bold]{client.device.version}[/]")
        else:
            console.print("Device Type: [bold]Firewall[/]")
            console.print(f"Model: [bold]{client.device.model}[/]")
            console.print(f"Serial: [bold]{client.device.serial}[/]")
            console.print(f"SW Version: [bold]{client.device.version}[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error testing authentication")
        raise typer.Exit(1) from e


@app.command("addresses")
def test_addresses(  # noqa: C901
    count: int = typer.Option(100, help="Number of address objects to create"),
    devicegroup: str = typer.Option(
        SHARED_DEFAULT, "--device-group", "-dg", help="Device group to add addresses to"
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
    commit: bool = typer.Option(COMMIT_DEFAULT, help="Commit changes after loading"),
    monitor_threads: bool = typer.Option(
        False, "--monitor-threads", help="Monitor and display thread activity"
    ),
):
    """
    Test creating multiple address objects using multithreading.

    This command generates and creates multiple address objects on a PAN-OS device.
    Use the --monitor-threads flag to visualize thread activity during execution.
    Thread monitoring is automatically enabled when using more than 5 threads.

    The thread monitoring display shows:
    - Active Threads: Currently running threads with their IDs and object being processed
    - Thread Utilization: Current and maximum thread usage as a percentage
    - Task Progress: Number of completed tasks out of the total

    This helps optimize the thread count for your specific environment and
    verify that all threads are being utilized effectively.
    """
    # Early debug
    try:
        # Print out available flags for debugging
        console.print("[bold cyan]DEBUG: Command arguments:[/bold cyan]")
        console.print(f"count={count}, devicegroup={devicegroup}, mock={mock}")
        console.print(f"threads={threads}, commit={commit}, monitor_threads={monitor_threads}")

        # Work with existing flags if --monitor-threads isn't recognized
        # If thread count is > 5, enable thread monitoring as a temporary measure
        enable_thread_monitoring = monitor_threads or threads > 5

        # Create client
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)

        console.print(f"Generating {count} address objects with random words and timestamps...")

        # Generate test address objects
        address_objects = []
        start_time = time.time()

        # Define address types to rotate through
        addr_types = ["ip-netmask", "fqdn", "ip-range"]

        # Lists for random name generation
        adjectives = [
            "red",
            "blue",
            "green",
            "yellow",
            "purple",
            "orange",
            "black",
            "white",
            "big",
            "small",
            "fast",
            "slow",
            "loud",
            "quiet",
            "happy",
            "sad",
            "brave",
            "shy",
            "wild",
            "calm",
            "fancy",
            "plain",
            "soft",
            "hard",
            "hot",
            "cold",
            "young",
            "old",
            "fresh",
            "stale",
            "clean",
            "dirty",
            "smooth",
            "rough",
        ]

        nouns = [
            "apple",
            "banana",
            "car",
            "dog",
            "elephant",
            "fish",
            "guitar",
            "house",
            "igloo",
            "jacket",
            "kite",
            "lamp",
            "mountain",
            "notebook",
            "ocean",
            "pencil",
            "rabbit",
            "sun",
            "table",
            "umbrella",
            "vase",
            "window",
            "xylophone",
            "zebra",
            "airport",
            "book",
            "cloud",
            "door",
            "egg",
            "flower",
            "garden",
            "hat",
        ]

        for i in range(count):
            # Get timestamp with milliseconds
            timestamp = int(time.time() * 1000)

            # Choose random adjective and noun
            adj = random.choice(adjectives)
            noun = random.choice(nouns)

            # Choose address type based on index
            addr_type = addr_types[i % len(addr_types)]

            # Create address object based on type
            if addr_type == "ip-netmask":
                # Generate IP in 10.0.0.0/8 range
                third_octet = (i // 255) % 255
                fourth_octet = i % 255
                ip = f"10.0.{third_octet}.{fourth_octet}/32"

                address = Address(
                    name=f"{adj}-{noun}-{timestamp}", ip_netmask=ip, description=None, tags=[]
                )
            elif addr_type == "fqdn":
                # Generate unique domain name
                address = Address(
                    name=f"{adj}-{noun}-{timestamp}",
                    fqdn=f"{adj}-{noun}-{timestamp}.example.com",
                    description=None,
                    tags=[],
                )
            else:  # ip-range
                # Generate IP range
                third_octet = (i // 255) % 255
                start_ip = f"192.168.{third_octet}.1"
                end_ip = f"192.168.{third_octet}.10"

                address = Address(
                    name=f"{adj}-{noun}-{timestamp}",
                    ip_range=f"{start_ip}-{end_ip}",
                    description=None,
                    tags=[],
                )

            address_objects.append(address)

        generation_time = time.time() - start_time
        console.print(f"Generated {count} address objects in {generation_time:.2f} seconds")

        # Create address objects using multithreading
        console.print(f"Creating {count} address objects with {threads} threads...")

        # Dictionary to track active threads
        active_threads = {}
        active_threads_lock = threading.Lock()

        # Thread stats
        thread_stats = {
            "max_concurrent": 0,
            "total_tasks": count,
            "completed_tasks": 0,
            "active_threads_history": [],
        }

        # Create a wrapper function that executes in the thread and tracks its ID
        def create_address_with_monitoring(obj, devicegroup):
            # Get the actual thread ID from within the worker thread
            thread_id = threading.get_ident()

            # Register this thread as active
            with active_threads_lock:
                active_threads[thread_id] = {
                    "object_name": obj.name,
                    "start_time": time.time(),
                }
                # Update max concurrent threads right after adding
                thread_stats["max_concurrent"] = max(
                    thread_stats["max_concurrent"], len(active_threads)
                )

            # If in mock mode, add a small delay to ensure threads overlap
            if mock:
                time.sleep(random.uniform(0.05, 0.1))

            # Execute the actual work
            try:
                result = client.create_address_object(obj, devicegroup)
                return result
            finally:
                # Ensure thread is marked as completed even if an exception occurs
                with active_threads_lock:
                    if thread_id in active_threads:
                        del active_threads[thread_id]
                    thread_stats["completed_tasks"] += 1

        # Temporarily increase logging level to suppress excessive messages
        original_log_level = logger.level
        logger.setLevel(logging.WARNING)

        # Track successful and failed operations
        successful = 0
        failed = 0

        # Setup for thread monitoring if enabled
        if enable_thread_monitoring:
            # Create a table for displaying thread statistics
            def get_thread_table():
                table = Table(title=f"Thread Utilization ({len(active_threads)}/{threads} active)")
                table.add_column("Thread ID", justify="right", style="cyan")
                table.add_column("Object Name", style="green")
                table.add_column("Status", style="yellow")

                with active_threads_lock:
                    # Add currently active threads to the table
                    for thread_id, details in active_threads.items():
                        table.add_row(
                            str(thread_id),
                            details["object_name"],
                            "Active",
                        )

                # Add thread stats to the table
                max_usage_percentage = (
                    (thread_stats["max_concurrent"] / threads) * 100 if threads > 0 else 0
                )
                current_usage_percentage = (
                    (len(active_threads) / threads) * 100 if threads > 0 else 0
                )

                table.add_row(
                    "SUMMARY",
                    "",
                    f"Max Concurrent: {thread_stats['max_concurrent']} "
                    f"({max_usage_percentage:.1f}%)",
                )
                table.add_row(
                    "",
                    "",
                    f"Current: {len(active_threads)}/{threads} ({current_usage_percentage:.1f}%)",
                )
                table.add_row(
                    "",
                    "",
                    f"Completed: {thread_stats['completed_tasks']}/{thread_stats['total_tasks']}",
                )

                return Panel(table)

            # Create progress bar for monitoring
            progress = Progress(
                SpinnerColumn(),
                TextColumn("Creating address objects"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
            )
            task = progress.add_task("Creating", total=len(address_objects))

            # Start live display that will update with thread information
            with Live(get_thread_table(), refresh_per_second=4, console=console) as live:
                with ThreadPoolExecutor(max_workers=threads) as executor:
                    # Submit all tasks and track the threads
                    future_to_obj = {}
                    for obj in address_objects:
                        future = executor.submit(create_address_with_monitoring, obj, devicegroup)

                        future_to_obj[future] = obj

                        # Add done callback to update stats when the task completes
                        future.add_done_callback(
                            lambda f, obj_name=obj.name: progress.update(task, advance=1)
                        )

                    # Process results as they complete
                    for future in as_completed(future_to_obj):
                        try:
                            result = future.result()
                            if result:
                                successful += 1
                            else:
                                failed += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to create address {future_to_obj[future].name}: {str(e)}"
                            )
                            failed += 1

                        # Update the live display
                        live.update(get_thread_table())
        else:
            # Standard progress bar without thread monitoring
            with Progress(
                SpinnerColumn(),
                TextColumn("Creating address objects"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                # Set up progress tracking
                task = progress.add_task("Creating", total=len(address_objects))

                with ThreadPoolExecutor(max_workers=threads) as executor:
                    # Submit all tasks
                    future_to_obj = {
                        executor.submit(client.create_address_object, obj, devicegroup): obj
                        for obj in address_objects
                    }

                    for future in as_completed(future_to_obj):
                        try:
                            result = future.result()
                            if result:
                                successful += 1
                            else:
                                failed += 1
                        except Exception as e:
                            logger.error(
                                f"Failed to create address {future_to_obj[future].name}: {str(e)}"
                            )
                            failed += 1

                        # Update progress
                        progress.update(task, advance=1)

        # Restore original logging level
        logger.setLevel(original_log_level)

        # Display results
        total_time = time.time() - start_time
        console.print("Address creation results:")
        console.print(f"Total objects: {count}")
        console.print(f"Successfully created: {successful}")
        console.print(f"Failed: {failed}")
        console.print(f"Total time: {total_time:.2f} seconds")
        console.print(f"Objects per second: {count / total_time:.2f}")

        if enable_thread_monitoring:
            # Display thread utilization summary
            console.print("\nThread utilization summary:")
            console.print(
                f"Maximum concurrent threads: {thread_stats['max_concurrent']} of {threads} "
                f"({(thread_stats['max_concurrent'] / threads) * 100:.1f}%)"
            )

            # Calculate the average thread utilization
            if thread_stats["active_threads_history"]:
                avg_utilization = sum(thread_stats["active_threads_history"]) / len(
                    thread_stats["active_threads_history"]
                )
                console.print(
                    f"Average thread utilization: {avg_utilization:.1f} "
                    f"({(avg_utilization / threads) * 100:.1f}%)"
                )

        # Commit changes if requested
        if commit and successful > 0:
            console.print("Committing changes...")
            commit_result = client.commit(admins="Test address objects bulk load")
            console.print(f"Commit job ID: {commit_result}")

        console.print(f"[bold cyan]Debug: monitor_threads={monitor_threads}[/bold cyan]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error in test_addresses")
        raise typer.Exit(1) from e


@app.command("show")
def show_addresses(
    name: Optional[str] = typer.Option(
        NONE_DEFAULT, help="Name of the address object to show (omit for all)"
    ),
    device_group: str = typer.Option(
        SHARED_DEFAULT,
        "--device-group",
        "-dg",
        help="Device group containing the addresses",
    ),
    mock: bool = typer.Option(MOCK_DEFAULT, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(
        THREADS_DEFAULT, help="Number of threads to use for concurrent operations"
    ),
):
    """Show address objects with detailed information."""
    try:
        config = get_or_create_config(mock_mode=mock, thread_pool_size=threads)
        client = PanosClient(config)
        _show_addresses_impl(client, name, device_group)
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error showing addresses")
        raise typer.Exit(1) from e


def _show_addresses_impl(client, name, device_group):
    """Implementation for showing address objects with detailed information."""
    # Get all addresses or specific address
    try:
        if name:
            addresses = [client.get_address(name, device_group)]
            if not addresses[0]:
                console.print(f"[bold red]Error:[/] Address '{name}' not found.")
                raise typer.Exit(1)
        else:
            addresses = client.list_addresses(device_group)
            if not addresses:
                console.print(
                    f"[bold yellow]Warning:[/] No addresses found in device group '{device_group}'."
                )
                raise typer.Exit(0)
    except (PanDeviceError, PanXapiError) as e:
        console.print(f"[bold red]Error:[/] Failed to retrieve addresses: {str(e)}")
        raise typer.Exit(1) from e

    # Create a table
    table = Table(title=f"Address Objects in '{device_group}'")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Value", style="yellow")
    table.add_column("Description")
    table.add_column("Tags")

    # Add rows to the table
    for addr in addresses:
        if isinstance(addr, dict):
            name = addr.get("name", "")
            description = addr.get("description", "")
            tags = ", ".join(addr.get("tag", []))

            # Determine address type and value
            addr_type = "Unknown"
            value = ""

            if "ip-netmask" in addr and addr["ip-netmask"]:
                addr_type = "IP/Netmask"
                value = addr["ip-netmask"]
            elif "ip-range" in addr and addr["ip-range"]:
                addr_type = "IP Range"
                value = addr["ip-range"]
            elif "fqdn" in addr and addr["fqdn"]:
                addr_type = "FQDN"
                value = addr["fqdn"]

            table.add_row(name, addr_type, value, description, tags)

    console.print(table)
