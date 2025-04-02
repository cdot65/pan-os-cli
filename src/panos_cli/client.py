"""PAN-OS client with multi-threading support."""

import concurrent.futures
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, List, Optional, TypeVar

from panos.errors import PanDeviceError, PanXapiError
from panos.panorama import DeviceGroup, Panorama
from rich.console import Console

from panos_cli.config import PanosConfig

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
            raise ValueError(error_msg)

    def _get_device_group(self, device_group: str) -> Optional[DeviceGroup]:
        """
        Get device group object.

        Args:
            device_group: Name of the device group

        Returns:
            DeviceGroup object or None for "Shared"
        """
        if device_group.lower() in ["shared", "-shared"]:
            return None

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
                    f"API call failed ({retry_count}/{max_retries}), retrying in {wait_time}s: {str(e)}"
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
            device_group: Device group to add objects to

        Returns:
            List of futures for the operations
        """
        if self.config.mock_mode:
            logger.info(f"MOCK: Would add {len(objects_to_add)} objects to {device_group}")
            console.print(
                f"[bold green]MOCK:[/] Adding {len(objects_to_add)} objects to {device_group}"
            )
            return []

        dg = self._get_device_group(device_group)
        parent = dg if dg else self.device

        futures = []
        for obj in objects_to_add:
            # Add object to the parent
            parent.add(obj)
            # Submit create operation to thread pool
            future = self.executor.submit(
                self._execute_with_retry, obj.create, retry_on_exception=True
            )
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

        dg = self._get_device_group(device_group)
        parent = dg if dg else self.device

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
                f"[bold green]MOCK:[/] Deleting {len(objects_to_delete)} objects from {device_group}"
            )
            return []

        dg = self._get_device_group(device_group)
        parent = dg if dg else self.device

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

        dg = self._get_device_group(device_group)
        parent = dg if dg else self.device

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
