"""Commands for managing PAN-OS address objects and groups."""

import logging
import time
from typing import List, Optional

import typer
from panos.objects import AddressObject as PanosAddress
from panos.objects import AddressGroup as PanosAddressGroup
from rich.console import Console
from rich.table import Table
import rich.box

from pan_os_cli.client import PanosClient
from pan_os_cli.config import load_config
from pan_os_cli.models.objects import Address, AddressGroup
from pan_os_cli.utils import create_progress_tracker, load_yaml, process_futures, validate_data

# Configure logger and console
logger = logging.getLogger(__name__)
console = Console()

# Create Typer app for address objects
app = typer.Typer(help="Manage address objects and groups")
set_app = typer.Typer(help="Create or update PAN-OS objects")
delete_app = typer.Typer(help="Delete PAN-OS objects")
load_app = typer.Typer(help="Bulk load PAN-OS objects from YAML files")
get_app = typer.Typer(help="Get PAN-OS objects")
commit_app = typer.Typer(help="Commit configuration changes")
test_app = typer.Typer(help="Test PAN-OS connectivity")
show_app = typer.Typer(help="Show PAN-OS objects in detail")

# Register sub-apps
app.add_typer(set_app, name="set")
app.add_typer(delete_app, name="delete")
app.add_typer(load_app, name="load")
app.add_typer(get_app, name="get")
app.add_typer(commit_app, name="commit")
app.add_typer(test_app, name="test")
app.add_typer(show_app, name="show")


@set_app.command("address")
def set_address(
    name: str = typer.Option(..., help="Name of the address object"),
    ip_netmask: Optional[str] = typer.Option(
        None, "--ip-netmask", help="IP address or network in CIDR notation"
    ),
    fqdn: Optional[str] = typer.Option(None, "--fqdn", help="Fully qualified domain name"),
    ip_range: Optional[str] = typer.Option(
        None, "--ip-range", help="IP range (e.g., 192.168.1.1-192.168.1.10)"
    ),
    description: Optional[str] = typer.Option(None, help="Description of the address object"),
    tags: List[str] = typer.Option([], help="Tags to apply to the address object"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to add the address to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Create or update an address object."""
    # Validate input - one of ip_netmask, fqdn, or ip_range must be provided
    if not any([ip_netmask, fqdn, ip_range]):
        console.print(
            "[bold red]Error:[/] One of --ip-netmask, --fqdn, or --ip-range must be provided"
        )
        raise typer.Exit(1)

    try:
        # Create Address model
        address = Address(
            name=name,
            ip_netmask=ip_netmask,
            fqdn=fqdn,
            ip_range=ip_range,
            description=description,
            tags=tags,
        )

        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Convert to PAN-OS object
        panos_obj = address.to_panos_object()

        console.print(f"Creating address object [bold blue]{name}[/]...")
        futures = client.add_objects([panos_obj], devicegroup)

        # Process results
        if futures:
            process_futures(futures)
            console.print(f"[bold green]Success:[/] Address object {name} created/updated")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error creating address object")
        raise typer.Exit(1)


@delete_app.command("address")
def delete_address(
    name: str = typer.Option(..., help="Name of the address object to delete"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group containing the address"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Delete an address object."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Create PAN-OS object
        panos_obj = PanosAddress(name=name)

        console.print(f"Deleting address object [bold blue]{name}[/]...")
        futures = client.delete_objects([panos_obj], devicegroup)

        # Process results
        if futures:
            process_futures(futures)
            console.print(f"[bold green]Success:[/] Address object {name} deleted")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error deleting address object")
        raise typer.Exit(1)


@load_app.command("address")
def load_address(
    file: str = typer.Option(..., help="Path to YAML file with address objects"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to add addresses to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
    commit: bool = typer.Option(False, help="Commit changes after loading"),
):
    """Bulk load address objects from YAML file using multi-threading."""
    try:
        # Load YAML file
        data = load_yaml(file)

        if "addresses" not in data:
            console.print("[bold red]Error:[/] YAML file must contain an 'addresses' key")
            raise typer.Exit(1)

        # Validate addresses
        addresses = validate_data(data["addresses"], Address)

        if not addresses:
            console.print("[bold yellow]Warning:[/] No address objects found in YAML file")
            return

        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Convert to PAN-OS objects
        panos_objects = [addr.to_panos_object() for addr in addresses]

        # Create progress tracker
        with create_progress_tracker(len(panos_objects), "Loading address objects") as progress:
            console.print(
                f"Loading [bold blue]{len(panos_objects)}[/] address objects with [bold green]{threads}[/] threads..."
            )

            # Add objects using multi-threading
            futures = client.add_objects(panos_objects, devicegroup)

            # Process results
            if futures:
                results = process_futures(futures, progress)
                successful = len([r for r in results if r is not None])
                console.print(
                    f"[bold green]Success:[/] {successful}/{len(panos_objects)} address objects loaded"
                )

        # Commit changes if requested
        if commit and not mock:
            console.print("Committing changes...")
            job_id = client.commit()
            console.print(f"Commit job ID: [bold blue]{job_id}[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error loading address objects")
        raise typer.Exit(1)


@set_app.command("address-group")
def set_address_group(
    name: str = typer.Option(..., help="Name of the address group"),
    description: Optional[str] = typer.Option(None, help="Description of the address group"),
    static_members: List[str] = typer.Option(
        [], help="Static members for the group (for static groups)"
    ),
    dynamic_filter: Optional[str] = typer.Option(
        None, help="Filter expression (for dynamic groups)"
    ),
    tags: List[str] = typer.Option([], help="Tags to apply to the address group"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to add the address group to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Create or update an address group."""
    # Validate input
    if not static_members and not dynamic_filter:
        console.print(
            "[bold red]Error:[/] Either --static-members or --dynamic-filter must be provided"
        )
        raise typer.Exit(1)

    if static_members and dynamic_filter:
        console.print(
            "[bold red]Error:[/] Cannot provide both --static-members and --dynamic-filter"
        )
        raise typer.Exit(1)

    try:
        # Create AddressGroup model
        address_group = AddressGroup(
            name=name,
            description=description,
            static_members=static_members if static_members else None,
            dynamic_filter=dynamic_filter,
            tags=tags,
        )

        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Convert to PAN-OS object
        panos_obj = address_group.to_panos_object()

        console.print(f"Creating address group [bold blue]{name}[/]...")
        futures = client.add_objects([panos_obj], devicegroup)

        # Process results
        if futures:
            process_futures(futures)
            console.print(f"[bold green]Success:[/] Address group {name} created/updated")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error creating address group")
        raise typer.Exit(1)


@delete_app.command("address-group")
def delete_address_group(
    name: str = typer.Option(..., help="Name of the address group to delete"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group containing the address group"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Delete an address group."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Create PAN-OS object
        panos_obj = PanosAddressGroup(name=name)

        console.print(f"Deleting address group [bold blue]{name}[/]...")
        futures = client.delete_objects([panos_obj], devicegroup)

        # Process results
        if futures:
            process_futures(futures)
            console.print(f"[bold green]Success:[/] Address group {name} deleted")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error deleting address group")
        raise typer.Exit(1)


@load_app.command("address-group")
def load_address_group(
    file: str = typer.Option(..., help="Path to YAML file with address groups"),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to add address groups to"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
    commit: bool = typer.Option(False, help="Commit changes after loading"),
):
    """Bulk load address groups from YAML file using multi-threading."""
    try:
        # Load YAML file
        data = load_yaml(file)

        if "address_groups" not in data:
            console.print("[bold red]Error:[/] YAML file must contain an 'address_groups' key")
            raise typer.Exit(1)

        # Validate address groups
        address_groups = validate_data(data["address_groups"], AddressGroup)

        if not address_groups:
            console.print("[bold yellow]Warning:[/] No address groups found in YAML file")
            return

        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Convert to PAN-OS objects
        panos_objects = [grp.to_panos_object() for grp in address_groups]

        # Create progress tracker
        with create_progress_tracker(len(panos_objects), "Loading address groups") as progress:
            console.print(
                f"Loading [bold blue]{len(panos_objects)}[/] address groups with [bold green]{threads}[/] threads..."
            )

            # Add objects using multi-threading
            futures = client.add_objects(panos_objects, devicegroup)

            # Process results
            if futures:
                results = process_futures(futures, progress)
                successful = len([r for r in results if r is not None])
                console.print(
                    f"[bold green]Success:[/] {successful}/{len(panos_objects)} address groups loaded"
                )

        # Commit changes if requested
        if commit and not mock:
            console.print("Committing changes...")
            job_id = client.commit()
            console.print(f"Commit job ID: [bold blue]{job_id}[/]")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error loading address groups")
        raise typer.Exit(1)


@get_app.command("address")
def get_address(
    name: Optional[str] = typer.Option(
        None, help="Name of the address object to get (omit for all)"
    ),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to get addresses from"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Get address objects."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        if name:
            console.print(f"Getting address object [bold blue]{name}[/]...")
            # TODO: Implement get for single object
            console.print("[bold yellow]Warning:[/] Getting single objects not yet implemented")
        else:
            console.print(f"Getting all address objects from [bold blue]{devicegroup}[/]...")
            addresses = client.get_objects(PanosAddress, devicegroup)

            if not addresses:
                console.print("[bold yellow]Warning:[/] No address objects found")
                return

            console.print(f"Found [bold green]{len(addresses)}[/] address objects:")
            for addr in addresses:
                console.print(f"  - [bold blue]{addr.name}[/] ({addr.type}: {addr.value})")

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error getting address objects")
        raise typer.Exit(1)


@get_app.command("address-group")
def get_address_group(
    name: Optional[str] = typer.Option(
        None, help="Name of the address group to get (omit for all)"
    ),
    devicegroup: str = typer.Option(
        "Shared", "--devicegroup", "-dg", help="Device group to get address groups from"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Get address groups."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        if name:
            console.print(f"Getting address group [bold blue]{name}[/]...")
            # TODO: Implement get for single object
            console.print("[bold yellow]Warning:[/] Getting single objects not yet implemented")
        else:
            console.print(f"Getting all address groups from [bold blue]{devicegroup}[/]...")
            groups = client.get_objects(PanosAddressGroup, devicegroup)

            if not groups:
                console.print("[bold yellow]Warning:[/] No address groups found")
                return

            console.print(f"Found [bold green]{len(groups)}[/] address groups:")
            for group in groups:
                if group.static:
                    members = ", ".join(group.static_value) if group.static_value else ""
                    console.print(f"  - [bold blue]{group.name}[/] (static: {members})")
                else:
                    console.print(
                        f"  - [bold blue]{group.name}[/] (dynamic: {group.dynamic_value})"
                    )

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error getting address groups")
        raise typer.Exit(1)


@commit_app.command("changes")
def commit_changes(
    description: Optional[str] = typer.Option(None, help="Description for the commit"),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
    wait: bool = typer.Option(False, help="Wait for commit to complete"),
    timeout: int = typer.Option(600, help="Maximum time to wait for commit completion (seconds)"),
):
    """Commit configuration changes to PAN-OS."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Commit changes
        console.print("Committing changes to PAN-OS device...")
        job_id = client.commit()
        console.print(f"Commit job ID: [bold blue]{job_id}[/]")

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
                console.print(f"[bold yellow]Warning:[/] Commit timeout after {timeout} seconds")
                raise typer.Exit(1)

    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error during commit")
        raise typer.Exit(1)


@commit_app.command("status")
def check_commit(
    job_id: str = typer.Option(..., help="Commit job ID to check"),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Check the status of a commit job."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
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
        raise typer.Exit(1)


@test_app.command("auth")
def test_auth(
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Test PAN-OS authentication and connectivity."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # In mock mode, we don't actually test connectivity
        if mock:
            console.print("[bold green]MOCK:[/] Authentication would be tested")
            console.print("[bold green]MOCK:[/] Connection to PAN-OS device successful")
            return

        # Test connectivity using system info refresh
        console.print(f"Testing connection to [bold blue]{config.hostname}[/]...")
        client.device.refresh_system_info()
        
        # Display connection information
        console.print("[bold green]Connection successful![/]")
        console.print(f"Connected to: [bold blue]{config.hostname}[/]")
        console.print(f"Model: [bold]{client.device.model}[/]")
        console.print(f"Serial: [bold]{client.device.serial}[/]")
        console.print(f"SW Version: [bold]{client.device.version}[/]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error testing authentication")
        raise typer.Exit(1)


@show_app.command("addresses")
def show_addresses(
    name: Optional[str] = typer.Option(
        None, help="Name of the address object to show (omit for all)"
    ),
    device_group: str = typer.Option(
        "Shared", "--device-group", "-dg", help="Device group containing the addresses"
    ),
    mock: bool = typer.Option(False, help="Run in mock mode without making API calls"),
    threads: int = typer.Option(10, help="Number of threads to use for concurrent operations"),
):
    """Show address objects with detailed information."""
    try:
        # Load configuration
        config = load_config()
        config.mock_mode = mock
        config.thread_pool_size = threads

        # Create PAN-OS client
        client = PanosClient(config)

        # Get specific address or all addresses
        if name:
            console.print(f"Showing address object [bold blue]{name}[/] from [bold blue]{device_group}[/]...")
            
            if mock:
                console.print(f"[bold green]MOCK:[/] Would show address {name}")
                console.print("Name: [bold blue]{}[/]".format(name))
                console.print("Type: [bold]ip-netmask[/]")
                console.print("Value: [bold]192.0.2.1[/]")
                console.print("Description: [bold]Mock address object[/]")
                return
                
            # Create a dummy address object and refresh it
            dg = client._get_device_group(device_group)
            parent = dg if dg else client.device
            
            addr = PanosAddress(name=name)
            parent.add(addr)
            
            try:
                addr.refresh()
                
                # Display address details in a formatted way
                console.print(f"Name: [bold blue]{addr.name}[/]")
                console.print(f"Type: [bold]{addr.type}[/]")
                console.print(f"Value: [bold]{addr.value}[/]")
                
                if addr.description:
                    console.print(f"Description: [bold]{addr.description}[/]")
                
                if addr.tag:
                    console.print(f"Tags: [bold]{', '.join(addr.tag)}[/]")
                    
            except Exception:
                console.print(f"[bold red]Error:[/] Address object '{name}' not found in {device_group}")
                raise typer.Exit(1)
        else:
            console.print(f"Showing all address objects from [bold blue]{device_group}[/]...")
            
            if mock:
                console.print("[bold green]MOCK:[/] Would show all addresses")
                console.print("\n[bold blue]Address Objects[/]:")
                console.print("┌───────────┬─────────────┬────────────┬─────────────────────┐")
                console.print("│ [bold]Name[/]      │ [bold]Type[/]        │ [bold]Value[/]     │ [bold]Description[/]        │")
                console.print("├───────────┼─────────────┼────────────┼─────────────────────┤")
                console.print("│ web-srv1  │ ip-netmask  │ 192.0.2.1  │ Web Server 1        │")
                console.print("│ app-srv1  │ ip-netmask  │ 192.0.2.2  │ App Server 1        │")
                console.print("│ db-srv1   │ ip-netmask  │ 192.0.2.3  │ Database Server 1   │")
                console.print("└───────────┴─────────────┴────────────┴─────────────────────┘")
                return
                
            # Get all addresses
            addresses = client.get_objects(PanosAddress, device_group)
            
            if not addresses:
                console.print(f"[bold yellow]Warning:[/] No address objects found in {device_group}")
                return
                
            # Display addresses in a table format
            console.print(f"\n[bold blue]Address Objects in {device_group}[/]:")
            
            # Create a Rich table with rounded corners
            table = Table(show_header=True, header_style="bold", box=rich.box.ROUNDED)
            
            # Add columns
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Value", style="yellow")
            table.add_column("Description")
            table.add_column("Device Group", style="magenta")
            
            # Add rows
            for addr in addresses:
                name_col = addr.name[:13] + (addr.name[13:] and "...")
                type_col = addr.type[:11] + (addr.type[11:] and "...")
                value_col = str(addr.value)[:18] + (str(addr.value)[18:] and "...")
                desc_col = (addr.description or "")[:19] + ((addr.description or "")[19:] and "...")
                
                table.add_row(name_col, type_col, value_col, desc_col, device_group)
            
            # Print the table
            console.print(table)
            console.print(f"Total: [bold green]{len(addresses)}[/] address objects")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/] {str(e)}")
        logger.exception("Error showing address objects")
        raise typer.Exit(1)
