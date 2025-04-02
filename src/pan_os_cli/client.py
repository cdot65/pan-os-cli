"""PAN-OS client with multi-threading support."""

import concurrent.futures
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional, TypeVar

from panos.errors import PanDeviceError, PanXapiError
from panos.objects import AddressGroup, AddressObject
from panos.panorama import DeviceGroup, Panorama
from rich.console import Console

from pan_os_cli.config import PanosConfig

# Type variable for generic functions
T = TypeVar("T")

# Configure logger
logger = logging.getLogger(__name__)
console = Console()


class PanosClient:
    """
    Client for PAN-OS API operations with multi-threading support.

    All API operations are executed with ThreadPoolExecutor to ensure
    efficient concurrent processing.
    """

    def __init__(self, config: PanosConfig):
        """
        Initialize PAN-OS client with given configuration.

        Args:
            config: PanosConfig with authentication and operational parameters
        """
        self.config = config
        self.device = None

        # Configure thread pool executor with size from config
        self.executor = ThreadPoolExecutor(max_workers=config.thread_pool_size)

        if not config.mock_mode:
            self._connect()

    def _connect(self) -> None:
        """
        Connect to PAN-OS device and initialize client.

        Raises:
            ValueError: If connection fails
        """
        try:
            if self.config.api_key:
                self.device = Panorama(hostname=self.config.hostname, api_key=self.config.api_key)
            else:
                self.device = Panorama(
                    hostname=self.config.hostname,
                    api_username=self.config.username,
                    api_password=self.config.password,
                )

            # Test connection
            self.device.refresh_system_info()
            logger.info(f"Connected to {self.config.hostname} successfully")

        except (PanDeviceError, PanXapiError) as e:
            error_msg = f"Failed to connect to {self.config.hostname}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

    def _get_device_group_or_shared(self, device_group: str) -> DeviceGroup:
        """
        Get device group object or shared.

        Args:
            device_group: Name of the device group

        Returns:
            DeviceGroup object or shared
        """
        if device_group.lower() in ["shared", "-shared"]:
            return self.device

        dg = DeviceGroup(name=device_group)
        self.device.add(dg)
        return dg

    def _execute_with_retry(
        self, func: Callable[..., T], *args: Any, max_retries: int = 3, **kwargs: Any
    ) -> T:
        """
        Execute function with retry logic and exponential backoff.

        Args:
            func: Function to execute
            *args: Arguments to pass to function
            max_retries: Maximum number of retry attempts
            **kwargs: Keyword arguments to pass to function

        Returns:
            Return value of the function

        Raises:
            Exception: If all retries fail
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would execute {func.__name__} with args {args} {kwargs}")
            return None

        retry_count = 0
        last_exception = None

        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except (PanDeviceError, PanXapiError) as e:
                retry_count += 1
                last_exception = e

                if retry_count >= max_retries:
                    break

                # Exponential backoff
                wait_time = 2**retry_count
                logger.warning(
                    f"API call failed ({retry_count}/{max_retries}), retrying in {wait_time}s: "
                    f"{str(e)}"
                )
                time.sleep(wait_time)

        # If we get here, all retries failed
        error_msg = f"Operation failed after {max_retries} attempts: {str(last_exception)}"
        logger.error(error_msg)
        raise last_exception

    def add_objects(
        self, objects_to_add: List[Any], device_group: str = "Shared"
    ) -> List[concurrent.futures.Future]:
        """
        Add multiple objects to PAN-OS in parallel.

        Args:
            objects_to_add: List of PAN-OS objects to add
            device_group: Device group to add the objects to

        Returns:
            List of Future objects representing the pending create operations
        """
        # Get the parent object
        parent = self._get_device_group_or_shared(device_group)

        futures = []
        for obj in objects_to_add:
            # Convert Pydantic model to pan-os-python object if it has to_panos_object method
            if hasattr(obj, "to_panos_object"):
                obj = obj.to_panos_object()

            # Add object to the parent
            parent.add(obj)
            # Submit create operation to thread pool
            future = self.executor.submit(self._execute_with_retry, obj.create)
            futures.append(future)

        return futures

    def update_objects(
        self, objects_to_update: List[Any], device_group: str = "Shared"
    ) -> List[concurrent.futures.Future]:
        """
        Update multiple objects in PAN-OS in parallel.

        Args:
            objects_to_update: List of PAN-OS objects to update
            device_group: Device group containing the objects

        Returns:
            List of futures for the operations
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would update {len(objects_to_update)} objects in {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Updating {len(objects_to_update)} objects in {device_group}"
            )
            return []

        dg = self._get_device_group_or_shared(device_group)
        parent = dg

        futures = []
        for obj in objects_to_update:
            # Add object to the parent
            parent.add(obj)
            # Submit update operation to thread pool
            future = self.executor.submit(
                self._execute_with_retry, obj.apply, retry_on_exception=True
            )
            futures.append(future)

        return futures

    def delete_objects(
        self, objects_to_delete: List[Any], device_group: str = "Shared"
    ) -> List[concurrent.futures.Future]:
        """
        Delete multiple objects from PAN-OS in parallel.

        Args:
            objects_to_delete: List of PAN-OS objects to delete
            device_group: Device group containing the objects

        Returns:
            List of futures for the operations
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would delete {len(objects_to_delete)} objects from {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Deleting {len(objects_to_delete)} objects from "
                f"{device_group}"
            )
            return []

        dg = self._get_device_group_or_shared(device_group)
        parent = dg

        futures = []
        for obj in objects_to_delete:
            # Add object to the parent
            parent.add(obj)
            # Submit delete operation to thread pool
            future = self.executor.submit(
                self._execute_with_retry, obj.delete, retry_on_exception=True
            )
            futures.append(future)

        return futures

    def get_objects(self, obj_class: type, device_group: str = "Shared") -> List[Any]:
        """
        Get all objects of a specific class from PAN-OS.

        Args:
            obj_class: Class of objects to retrieve
            device_group: Device group to get objects from

        Returns:
            List of objects
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would get all {obj_class.__name__} objects from {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Getting all {obj_class.__name__} objects from {device_group}"
            )
            return []

        dg = self._get_device_group_or_shared(device_group)
        parent = dg

        # Create a dummy object to use for the API call
        dummy_obj = obj_class()
        parent.add(dummy_obj)

        try:
            dummy_obj.refreshall()
            return parent.findall(obj_class)
        except (PanDeviceError, PanXapiError) as e:
            logger.error(f"Failed to get objects: {str(e)}")
            raise

    def commit(self) -> str:
        """
        Commit configuration changes to PAN-OS.

        Returns:
            Commit job ID or mock message
        """
        if self.config.mock_mode:
            logger.info("MOCK: Would commit changes")
            console.print("[bold green]MOCK:[/] Committing changes")
            return "mock-job-12345"

        try:
            result = self._execute_with_retry(self.device.commit, sync=False)
            job_id = result.get("id")
            logger.info(f"Commit initiated with job ID: {job_id}")
            return job_id
        except (PanDeviceError, PanXapiError) as e:
            logger.error(f"Commit failed: {str(e)}")
            raise

    def check_commit_status(self, job_id: str) -> dict:
        """
        Check status of a commit job.

        Args:
            job_id: Job ID to check

        Returns:
            Dictionary with commit status
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would check status of commit job {job_id}")
            console.print(f"[bold green]MOCK:[/] Checking status of commit job {job_id}")
            return {"status": "success", "progress": 100}

        try:
            result = self._execute_with_retry(self.device.commit_status, job_id)
            return result
        except (PanDeviceError, PanXapiError) as e:
            logger.error(f"Failed to check commit status: {str(e)}")
            raise

    def wait_for_job(self, job_id: str, interval: int = 5, timeout: int = 600) -> dict:
        """
        Wait for a job to complete.

        Args:
            job_id: Job ID to wait for
            interval: Polling interval in seconds
            timeout: Maximum time to wait in seconds

        Returns:
            Final job status
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would wait for job {job_id}")
            console.print(f"[bold green]MOCK:[/] Waiting for job {job_id}")
            return {"status": "success", "progress": 100}

        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.check_commit_status(job_id)
            if status.get("status") in ["success", "failure", "error"]:
                return status

            logger.info(f"Job {job_id} in progress: {status.get('progress', 0)}%")
            time.sleep(interval)

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    # Methods for specific object types required by the commands module

    def create_address_object(self, address: AddressObject, device_group: str = "Shared") -> bool:
        """
        Create or update an address object.

        Args:
            address: Address object to create
            device_group: Device group to add the address to

        Returns:
            True if successful, False otherwise
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would create address object {address.name} in {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Creating address object '{address.name}' in {device_group}"
            )
            return True

        try:
            # Add and create the object
            futures = self.add_objects([address], device_group)
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Raise any exceptions
            return True
        except Exception as e:
            logger.error(f"Failed to create address object: {str(e)}")
            raise

    def create_address_group(self, group: AddressGroup, device_group: str = "Shared") -> bool:
        """
        Create or update an address group.

        Args:
            group: AddressGroup object to create
            device_group: Device group to add the group to

        Returns:
            True if successful, False otherwise
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would create address group {group.name} in {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Creating address group '{group.name}' in {device_group}"
            )
            return True

        try:
            # Add and create the object
            futures = self.add_objects([group], device_group)
            for future in concurrent.futures.as_completed(futures):
                future.result()  # Raise any exceptions
            return True
        except Exception as e:
            logger.error(f"Failed to create address group: {str(e)}")
            raise

    def delete_address_object(self, name: str, device_group: str = "Shared") -> bool:
        """
        Delete an address object.

        Args:
            name: Name of the address object to delete
            device_group: Device group containing the address

        Returns:
            True if successful, False otherwise
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would delete address object {name} from {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Deleting address object '{name}' from {device_group}"
            )
            return True

        try:
            dg = self._get_device_group_or_shared(device_group)

            # Create a temporary object for deletion
            obj = AddressObject(name=name)
            dg.add(obj)

            # Delete the object
            self._execute_with_retry(obj.delete)
            return True
        except Exception as e:
            logger.error(f"Failed to delete address object: {str(e)}")
            raise

    def delete_address_group(self, name: str, device_group: str = "Shared") -> bool:
        """
        Delete an address group.

        Args:
            name: Name of the address group to delete
            device_group: Device group containing the group

        Returns:
            True if successful, False otherwise
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would delete address group {name} from {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Deleting address group '{name}' from {device_group}"
            )
            return True

        try:
            dg = self._get_device_group_or_shared(device_group)

            # Create a temporary object for deletion
            obj = AddressGroup(name=name)
            dg.add(obj)

            # Delete the object
            self._execute_with_retry(obj.delete)
            return True
        except Exception as e:
            logger.error(f"Failed to delete address group: {str(e)}")
            raise

    def list_addresses(self, device_group: str = "Shared") -> List[Dict[str, Any]]:
        """
        List all address objects in a device group.

        Args:
            device_group: Device group to list addresses from

        Returns:
            List of address objects as dictionaries
        """
        if self.config.mock_mode:
            return self._mock_list_addresses(device_group)

        try:
            from panos.objects import AddressObject

            dg = self._get_device_group_or_shared(device_group)
            # Use the proper refreshall pattern with parent object
            address_objects = AddressObject.refreshall(dg)

            # Debug log to inspect objects
            self._debug_log_objects(address_objects)

            # Convert to list of dictionaries
            addresses = [self._convert_address_to_dict(obj) for obj in address_objects]
            return addresses

        except Exception as e:
            logger.error(f"Failed to list address objects: {str(e)}")
            raise

    def _mock_list_addresses(self, device_group: str) -> List[Dict[str, Any]]:
        """Return mock address data for testing without API calls."""
        logger.info(f"MOCK: Would list address objects from {device_group}")
        console.print(f"[bold green]MOCK:[/] Listing address objects from {device_group}")
        return [
            {
                "name": "mock-server1",
                "type": "ip-netmask",
                "value": "10.0.0.1/32",
                "description": "Mock server 1",
                "tag": ["mock"],
            },
            {
                "name": "mock-server2",
                "type": "ip-netmask",
                "value": "10.0.0.2/32",
                "description": "Mock server 2",
                "tag": ["mock"],
            },
        ]

    def _debug_log_objects(self, objects: List[Any]) -> None:
        """Log debug information about PAN-OS objects."""
        for obj in objects:
            logger.debug(f"Object name: {obj.name}")
            logger.debug(f"Object attributes: {dir(obj)}")
            logger.debug(f"Object vars: {vars(obj)}")

    def _convert_address_to_dict(self, obj: Any) -> Dict[str, Any]:
        """Convert a PAN-OS address object to a dictionary."""
        # Base address dict with common properties
        addr_dict = {
            "name": obj.name,
            "description": obj.description or "",
            "tag": obj.tag or [],
        }

        # Extract address value based on type
        self._extract_address_value(obj, addr_dict)

        return addr_dict

    def _extract_address_value(self, obj: Any, addr_dict: Dict[str, Any]) -> None:
        """Extract the address value based on its type."""
        # Determine address type
        addr_type = getattr(obj, "type", "Unknown") if hasattr(obj, "type") else "Unknown"

        # Try getting values based on type attributes
        if addr_type == "ip-netmask" or (hasattr(obj, "value") and obj.value):
            addr_dict["ip-netmask"] = obj.value
        elif addr_type == "fqdn" or (hasattr(obj, "fqdn") and obj.fqdn):
            addr_dict["fqdn"] = obj.fqdn
        elif addr_type == "ip-range" or (hasattr(obj, "ip_range") and obj.ip_range):
            addr_dict["ip-range"] = obj.ip_range
        else:
            # Try to extract from XML element if available
            self._extract_from_element(obj, addr_dict)

    def _extract_from_element(self, obj: Any, addr_dict: Dict[str, Any]) -> None:
        """Extract address information from the XML element if available."""
        if not hasattr(obj, "element") or obj.element is None:
            return

        try:
            # Check for ip-netmask
            ip_netmask = obj.element.find("./ip-netmask")
            if ip_netmask is not None and ip_netmask.text:
                addr_dict["ip-netmask"] = ip_netmask.text
                return

            # Check for fqdn
            fqdn = obj.element.find("./fqdn")
            if fqdn is not None and fqdn.text:
                addr_dict["fqdn"] = fqdn.text
                return

            # Check for ip-range
            ip_range = obj.element.find("./ip-range")
            if ip_range is not None and ip_range.text:
                addr_dict["ip-range"] = ip_range.text
        except Exception as e:
            logger.debug(f"Error accessing element data: {str(e)}")

    def get_address_group(self, name: str, device_group: str = "Shared") -> Optional[AddressGroup]:
        """
        Get a specific address group from a device group.

        Args:
            name: Name of the address group to get
            device_group: Device group to get the address group from

        Returns:
            The address group object or None if not found
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would get address group {name} from {device_group}")
            console.print(f"[bold green]MOCK:[/] Getting address group {name} from {device_group}")
            # Create a mock address group
            mock_group = AddressGroup(
                name=name,
                static_value=["mock-server1", "mock-server2"],
                description="Mock address group",
            )
            mock_group.tag = ["mock"]
            return mock_group

        try:
            dg = self._get_device_group_or_shared(device_group)
            group = AddressGroup(name=name)
            dg.add(group)

            try:
                group.refresh()
                return group
            except PanDeviceError:
                # Group not found
                return None

        except Exception as e:
            logger.error(f"Failed to get address group: {str(e)}")
            raise

    def get_address_groups(self, device_group: str) -> List[AddressGroup]:
        """
        Get all address groups from a device group.

        Args:
            device_group: Device group to get address groups from

        Returns:
            List of address group objects
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would get address groups from {device_group}")
            console.print(f"[bold green]MOCK:[/] Getting address groups from {device_group}")
            # Create mock address groups
            mock_groups = [
                AddressGroup(
                    name="mock-group1",
                    static_value=["mock-server1", "mock-server2"],
                    description="Mock group 1",
                ),
                AddressGroup(
                    name="mock-group2", static_value=["mock-server2"], description="Mock group 2"
                ),
            ]
            # Add tags to mock groups
            for group in mock_groups:
                group.tag = ["mock"]
            return mock_groups

        try:
            dg = self._get_device_group_or_shared(device_group)
            # Use the proper refreshall pattern with parent object
            return AddressGroup.refreshall(dg)

        except Exception as e:
            logger.error(f"Failed to get address groups: {str(e)}")
            raise

    def list_address_groups(self, device_group: str = "Shared") -> List[Dict[str, Any]]:
        """
        List all address groups in a device group.

        Args:
            device_group: Device group to list address groups from

        Returns:
            List of address groups as dictionaries
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would list address groups from {device_group}")
            console.print(f"[bold green]MOCK:[/] Listing address groups from {device_group}")
            return [
                {
                    "name": "mock-group1",
                    "static_value": ["mock-server1", "mock-server2"],
                    "description": "Mock group 1",
                    "tag": ["mock"],
                },
                {
                    "name": "mock-group2",
                    "static_value": ["mock-server2"],
                    "description": "Mock group 2",
                    "tag": ["mock"],
                },
            ]

        try:
            from panos.objects import AddressGroup

            dg = self._get_device_group_or_shared(device_group)
            # Use the proper refreshall pattern with parent object
            address_groups = AddressGroup.refreshall(dg)

            # Debug log to inspect objects
            for obj in address_groups:
                logger.debug(f"Group name: {obj.name}")
                logger.debug(f"Group attributes: {dir(obj)}")
                logger.debug(f"Group vars: {vars(obj)}")

            # Convert to list of dictionaries
            groups = []
            for obj in address_groups:
                groups.append(
                    {
                        "name": obj.name,
                        "static_value": obj.static_value or [],
                        "dynamic_value": obj.dynamic_value,
                        "description": obj.description or "",
                        "tag": obj.tag or [],
                    }
                )

            return groups

        except Exception as e:
            logger.error(f"Failed to list address groups: {str(e)}")
            raise

    def get_address(self, name: str, device_group: str = "Shared") -> Optional[AddressObject]:
        """
        Get a specific address object from a device group.

        Args:
            name: Name of the address object to get
            device_group: Device group to get the address from

        Returns:
            The address object or None if not found
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would get address {name} from {device_group}")
            console.print(f"[bold green]MOCK:[/] Getting address {name} from {device_group}")
            # Create a mock address
            mock_address = AddressObject(
                name=name, value="10.0.0.1/32", type="ip-netmask", description="Mock address object"
            )
            mock_address.tag = ["mock"]
            return mock_address

        try:
            dg = self._get_device_group_or_shared(device_group)
            address = AddressObject(name=name)
            dg.add(address)

            try:
                address.refresh()
                return address
            except PanDeviceError:
                # Address not found
                return None
        except Exception as e:
            logger.error(f"Failed to get address: {str(e)}")
            raise
