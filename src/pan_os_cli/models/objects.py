"""Data models for PAN-OS address objects and address groups."""

from typing import List, Optional
from pydantic import BaseModel, Field, validator
import ipaddress


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

        extra = "forbid"

    @validator("ip_netmask", pre=True)
    def validate_ip_netmask(cls, v):
        """Validate IP netmask format."""
        if v is None:
            return v
        try:
            ipaddress.ip_network(v)
            return v
        except ValueError:
            raise ValueError(f"Invalid IP address or network: {v}")

    @validator("ip_range", pre=True)
    def validate_ip_range(cls, v):
        """Validate IP range format."""
        if v is None:
            return v
        try:
            start, end = v.split("-")
            ipaddress.ip_address(start.strip())
            ipaddress.ip_address(end.strip())
            return v
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid IP range: {v}. Must be in format: 192.168.1.1-192.168.1.10")

    @validator("name", pre=True)
    def validate_name(cls, v):
        """Validate address object name."""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        if len(v) > 63:
            raise ValueError("Name must be 63 characters or less")
        return v

    def to_panos_object(self):
        """Convert to pan-os-python Address object."""
        from panos.objects import Address as PanosAddress

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

        extra = "forbid"

    @validator("name", pre=True)
    def validate_name(cls, v):
        """Validate address group name."""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        if len(v) > 63:
            raise ValueError("Name must be 63 characters or less")
        return v

    @validator("static_members", "dynamic_filter")
    def validate_group_type(cls, v, values, **kwargs):
        """Ensure either static_members or dynamic_filter is provided, but not both."""
        field = kwargs["field"].name
        other_field = "dynamic_filter" if field == "static_members" else "static_members"

        # If this is the first field being validated, allow it
        if other_field not in values:
            return v

        # If both fields have values, raise an error
        if v is not None and values.get(other_field) is not None:
            raise ValueError("An address group cannot be both static and dynamic")

        # If neither field has a value, raise an error
        if v is None and values.get(other_field) is None:
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
