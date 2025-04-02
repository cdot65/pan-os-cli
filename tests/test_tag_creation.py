import unittest
from unittest.mock import MagicMock, patch

from src.pan_os_cli.client import PanosClient
from src.pan_os_cli.config import PanosConfig
from src.pan_os_cli.models.objects import Address, AddressGroup


class TestTagCreation(unittest.TestCase):
    def setUp(self):
        self.config = PanosConfig(mock_mode=False)

        # Mock the Panorama client
        self.panorama_mock = MagicMock()
        self.panorama_mock.children = []

        # Setup the client with the mocked panorama instance
        with patch("src.pan_os_cli.client.Panorama", return_value=self.panorama_mock):
            with patch("src.pan_os_cli.client.PanosClient._connect"):
                self.client = PanosClient(self.config)
                self.client.device = self.panorama_mock

    def test_create_tags_in_shared(self):
        """Test that tags are created in Shared location when device_group is Shared"""
        # Setup test data
        address = Address(
            name="test-shared",
            ip_netmask="10.0.0.1/32",
            description="Test address",
            tags=["SHARED-TAG"],
        )

        # Mock the to_panos_object method
        address.to_panos_object = MagicMock()
        address.to_panos_object.return_value = MagicMock()
        address.to_panos_object.return_value.create = MagicMock()

        # Create a tag with a mock
        tag_mock = MagicMock()
        tag_mock.name = "SHARED-TAG"

        # Override ensure_tags_exist to track what was called
        address.ensure_tags_exist = MagicMock()

        with patch("panos.objects.Tag", return_value=tag_mock):
            # Call the method
            self.client.create_address_object(address, device_group="Shared")

            # Verify ensure_tags_exist was called with the panorama object
            address.ensure_tags_exist.assert_called_with(self.panorama_mock)

    def test_create_tags_in_device_group(self):
        """Test that tags are created in the device group when a device group is specified"""
        # Setup test data
        address = Address(
            name="test-dg",
            ip_netmask="10.0.0.2/32",
            description="Test device group address",
            tags=["DG-TAG"],
        )

        # Setup mocks for device group
        device_group_mock = MagicMock()
        device_group_mock.children = []

        # Mock the to_panos_object method
        address.to_panos_object = MagicMock()
        address.to_panos_object.return_value = MagicMock()
        address.to_panos_object.return_value.create = MagicMock()

        # Setup the _get_device_group_or_shared mock to return our device group
        self.client._get_device_group_or_shared = MagicMock(return_value=device_group_mock)

        # Override ensure_tags_exist to track what was called
        address.ensure_tags_exist = MagicMock()

        # Call the method
        self.client.create_address_object(address, device_group="Test-DG")

        # Verify ensure_tags_exist was called with the device group object
        address.ensure_tags_exist.assert_called_with(device_group_mock)

    def test_address_group_tags_in_device_group(self):
        """Test that tags for address groups are created in the device group"""
        # Setup test data
        address_group = AddressGroup(
            name="test-group",
            description="Test address group",
            static_members=["addr1", "addr2"],  # Changed from static_addresses
            tags=["GROUP-TAG"],
        )

        # Setup mocks for device group
        device_group_mock = MagicMock()
        device_group_mock.children = []

        # Mock the to_panos_object method
        address_group.to_panos_object = MagicMock()
        address_group.to_panos_object.return_value = MagicMock()
        address_group.to_panos_object.return_value.create = MagicMock()

        # Setup the _get_device_group_or_shared mock to return our device group
        self.client._get_device_group_or_shared = MagicMock(return_value=device_group_mock)

        # Override ensure_tags_exist to track what was called
        address_group.ensure_tags_exist = MagicMock()

        # Call the method
        self.client.create_address_group(address_group, device_group="Test-DG")

        # Verify ensure_tags_exist was called with the device group object
        address_group.ensure_tags_exist.assert_called_with(device_group_mock)


if __name__ == "__main__":
    unittest.main()
