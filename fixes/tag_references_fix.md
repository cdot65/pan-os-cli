# PAN-OS Tag References Fix

## Problem

When creating address objects or address groups with tags, the PAN-OS API requires that the tags exist in the system before they can be referenced. If a tag doesn't exist, the API call fails with an error like:

```
PanDeviceXapiError: test1234 -> tag 'LAB' is not a valid reference
test1234 -> tag is invalid
```

This creates a poor user experience, as users must manually create tags before they can assign them to objects.

## Solution

We implemented a solution that automatically creates missing tags before adding them to address objects or address groups. The implementation involves the following changes:

1. Added an `ensure_tags_exist` method to both the `Address` and `AddressGroup` classes in `models/objects.py`.
   - The method checks if the specified tags exist in the PAN-OS system
   - If a tag doesn't exist, it creates the tag with a default color

2. Updated the `create_address_object` and `create_address_group` methods in `client.py` to call the new `ensure_tags_exist` method before creating the objects.

3. Added a new `address-groups` command to the CLI to enable creating address groups with tags.

## Implementation Details

### In `models/objects.py`:

```python
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
    existing_tags = []
    for child in parent.children:
        if isinstance(child, Tag):
            existing_tags.append(child.name)

    # Create any tags that don't exist
    for tag_name in self.tags:
        if tag_name not in existing_tags:
            print(f"Creating missing tag: {tag_name}")
            tag_obj = Tag(name=tag_name, color="color1")
            parent.add(tag_obj)
            tag_obj.create()
```

### In `client.py`:

```python
def create_address_object(self, address: AddressObject, device_group: str = "Shared") -> bool:
    """Create an address object."""
    # Get the parent device group
    dg = self._get_device_group_or_shared(device_group)

    # Have the address ensure its tags exist first
    if hasattr(address, "ensure_tags_exist"):
        address.ensure_tags_exist(dg)

    # Convert the address object to a PAN-OS object and add it to the device group
    try:
        panw_obj = address.to_pandevice()
        dg.add(panw_obj)
        panw_obj.create()
        logger.info(f"Successfully created address {address.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create address {address.name}: {str(e)}")
        raise
```

Similar changes were made to the `create_address_group` method.

## Testing

The solution was tested with the following commands:

```bash
# Create an address object with a non-existent tag
poetry run pan-os-cli set objects addresses --name test1234 --type ip-netmask --value 1.1.1.1/32 --tags "LAB"

# Create an address group with multiple non-existent tags
poetry run pan-os-cli set objects address-groups --name testgroup --static-members test1234 --tags "LAB,TEST"
```

Both commands executed successfully, automatically creating the necessary tags.

## Benefits

1. Improved user experience - users can now specify tags without having to create them first
2. Reduced errors - fewer API errors due to non-existent tag references
3. Streamlined workflow - one-step process to create objects with tags
