# Installation

There are several ways to install PAN-OS CLI, depending on your requirements and environment.

## Prerequisites

Before installing PAN-OS CLI, ensure you have:

- Python 3.8 or newer
- Access to a PAN-OS device (firewall or Panorama)
- Network connectivity to the management interface of your PAN-OS device

## Using pip

The simplest way to install PAN-OS CLI is using pip:

```bash
pip install pan-os-cli
```

## Using Poetry

If you prefer using Poetry for dependency management:

```bash
# Clone the repository
git clone https://github.com/cdot65/pan-os-cli.git
cd pan-os-cli

# Install with Poetry
poetry install
```

## Development Installation

If you want to contribute to PAN-OS CLI or run the latest development version:

```bash
# Clone the repository
git clone https://github.com/cdot65/pan-os-cli.git
cd pan-os-cli

# Install in development mode
pip install -e .
```

## Verifying Installation

After installation, verify that PAN-OS CLI is correctly installed:

```bash
pan-os-cli --version
```

You should see the version number of PAN-OS CLI displayed.

## Docker Installation

You can also use PAN-OS CLI with Docker:

```bash
# Pull the Docker image
docker pull cdot65/pan-os-cli:latest

# Run PAN-OS CLI in Docker
docker run --rm cdot65/pan-os-cli:latest pan-os-cli --help
```

## Next Steps

After installing PAN-OS CLI, see the [Getting Started](getting-started.md) guide to configure and begin using the tool.
