"""Data models for PAN-OS address objects and address groups."""

import ipaddress
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class Address(BaseModel):
    """Model for PAN-OS Address objects."""

    name: str = Field(..., description="Name of the address object")
    ip_netmask: Optional[str] = Field(
        None, description="IP address or network in CIDR notation (e.g., 192.168.1.1/32)"
    )
    fqdn: Optional[str] = Field(None, description="Fully qualified domain name")
    ip_range: Optional[str] = Field(None, description="IP range (e.g., 192.168.1.1-192.168.1.10)")
    description: Optional[str] = Field(None, description="Description of the address object")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the address object"
    )

    class Config:
        """Pydantic model configuration."""

        extra = "allow"

    @field_validator("ip_netmask")
    @classmethod
    def validate_ip_netmask(cls, v):
        """Validate IP netmask format."""
        if v is None:
            return v
        try:
            ipaddress.ip_network(v)
            return v
        except ValueError as err:
            raise ValueError(
                f"Invalid IP address or network: {v}. "
                f"Please use CIDR notation (e.g., 192.168.1.0/24)."
            ) from err
        except Exception as e:
            raise ValueError(
                f"Invalid IP address format: {v}. "
                f"Please provide a valid IP address or network. "
                f"Error: {str(e)}"
            ) from e

    @field_validator("ip_range")
    @classmethod
    def validate_ip_range(cls, v):
        """Validate IP range format."""
        if v is None:
            return v
        try:
            start_ip, end_ip = v.split("-")
            ipaddress.ip_address(start_ip.strip())
            ipaddress.ip_address(end_ip.strip())
            return v
        except (ValueError, AttributeError) as err:
            raise ValueError(
                f"Invalid IP range: {v}. Must be in format: 192.168.1.1-192.168.1.10"
            ) from err

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate address object name."""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        if len(v) > 63:
            raise ValueError("Name must be 63 characters or less")
        return v

    def to_panos_object(self):
        """Convert to pan-os-python Address object."""
        from panos.objects import AddressObject as PanosAddress

        # Determine which address type to use based on provided fields
        if self.ip_netmask:
            addr_type = "ip-netmask"
            value = self.ip_netmask
        elif self.fqdn:
            addr_type = "fqdn"
            value = self.fqdn
        elif self.ip_range:
            addr_type = "ip-range"
            value = self.ip_range
        else:
            raise ValueError("One of ip_netmask, fqdn, or ip_range must be provided")

        return PanosAddress(
            name=self.name,
            type=addr_type,
            value=value,
            description=self.description,
            tag=self.tags,
        )

    def ensure_tags_exist(self, parent):
        """
        Create any tags that don't exist in PAN-OS before using them.

        Args:
            parent: The parent object to add the tags to (device group or firewall)
        """
        if not self.tags:
            return

        # Get existing tags
        from panos.objects import Tag
        from panos.panorama import DeviceGroup, Panorama

        # Need to refresh the tags directly from the device group
        if isinstance(parent, DeviceGroup) or isinstance(parent, Panorama):
            Tag.refreshall(parent)

        # Get the existing tags after refreshing
        existing_tags = [child.name for child in parent.children if isinstance(child, Tag)]

        # Create any tags that don't exist
        for tag_name in self.tags:
            if tag_name not in existing_tags:
                tag_obj = Tag(name=tag_name, color="color1")
                parent.add(tag_obj)
                tag_obj.create()
                # Update existing_tags to include the one we just created
                existing_tags.append(tag_name)


class AddressGroup(BaseModel):
    """Model for PAN-OS Address Group objects."""

    name: str = Field(..., description="Name of the address group")
    description: Optional[str] = Field(None, description="Description of the address group")
    static_members: Optional[List[str]] = Field(
        None, description="List of address object names for static group"
    )
    dynamic_filter: Optional[str] = Field(None, description="Filter expression for dynamic group")
    tags: List[str] = Field(
        default_factory=list, description="Tags associated with the address group"
    )

    class Config:
        """Pydantic model configuration."""

        extra = "allow"

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate address group name."""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        if len(v) > 63:
            raise ValueError("Name must be 63 characters or less")
        return v

    @field_validator("static_members", "dynamic_filter")
    @classmethod
    def validate_group_type(cls, v, info):
        """Ensure either static_members or dynamic_filter is provided, but not both."""
        field_name = info.field_name
        other_field = "dynamic_filter" if field_name == "static_members" else "static_members"

        # If this is the first field being validated, allow it
        if other_field not in info.data:
            return v

        # If both fields have values, raise an error
        if v is not None and info.data.get(other_field) is not None:
            raise ValueError("An address group cannot be both static and dynamic")

        # If neither field has a value, raise an error
        if v is None and info.data.get(other_field) is None:
            raise ValueError("Either static_members or dynamic_filter must be provided")

        return v

    def to_panos_object(self):
        """Convert to pan-os-python AddressGroup object."""
        from panos.objects import AddressGroup as PanosAddressGroup

        if self.static_members is not None:
            return PanosAddressGroup(
                name=self.name,
                static_value=self.static_members,
                description=self.description,
                tag=self.tags,
            )
        elif self.dynamic_filter is not None:
            return PanosAddressGroup(
                name=self.name,
                dynamic_value=self.dynamic_filter,
                description=self.description,
                tag=self.tags,
            )
        else:
            raise ValueError("Either static_members or dynamic_filter must be provided")

    def ensure_tags_exist(self, parent):
        """
        Create any tags that don't exist in PAN-OS before using them.

        Args:
            parent: The parent object to add the tags to (device group or firewall)
        """
        if not self.tags:
            return

        # Get existing tags
        from panos.objects import Tag
        from panos.panorama import DeviceGroup, Panorama

        # Need to refresh the tags directly from the device group
        if isinstance(parent, DeviceGroup) or isinstance(parent, Panorama):
            Tag.refreshall(parent)

        # Get the existing tags after refreshing
        existing_tags = [child.name for child in parent.children if isinstance(child, Tag)]

        # Create any tags that don't exist
        for tag_name in self.tags:
            if tag_name not in existing_tags:
                tag_obj = Tag(name=tag_name, color="color1")
                parent.add(tag_obj)
                tag_obj.create()
                # Update existing_tags to include the one we just created
                existing_tags.append(tag_name)
