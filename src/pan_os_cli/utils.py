"""Utility functions for pan-os-cli."""

import logging
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar

from pydantic import ValidationError
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

# Type variable for generic functions
T = TypeVar("T")

# Console setup
console = Console()


def configure_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.

    Args:
        verbose: Enable debug logging if True
    """
    log_level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file content.

    Args:
        file_path: Path to YAML file

    Returns:
        Dict containing parsed YAML content

    Raises:
        FileNotFoundError: If file does not exist
        yaml.YAMLError: If file cannot be parsed
    """
    path = Path(file_path).expanduser().resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Error parsing YAML file {path}: {str(e)}")


def save_yaml(file_path: str, data: Dict[str, Any]) -> None:
    """
    Save data to YAML file.

    Args:
        file_path: Path to save YAML file
        data: Data to save

    Raises:
        IOError: If file cannot be written
    """
    path = Path(file_path).expanduser().resolve()

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(path), exist_ok=True)

    try:
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
    except (IOError, yaml.YAMLError) as e:
        raise IOError(f"Error writing YAML file {path}: {str(e)}")


def validate_data(data: Dict[str, Any], model_class: Type[T]) -> List[T]:
    """
    Validate data against a Pydantic model.

    Args:
        data: Data to validate
        model_class: Pydantic model class to validate against

    Returns:
        List of validated model instances

    Raises:
        ValidationError: If validation fails
    """
    validated_objects = []

    for idx, item in enumerate(data):
        try:
            validated_objects.append(model_class(**item))
        except ValidationError as e:
            # Add item index to error message
            error_msg = f"Validation error in item {idx + 1}: {str(e)}"
            console.print(f"[bold red]Error:[/] {error_msg}")
            raise ValidationError(e.raw_errors, model_class)

    return validated_objects


def create_progress_tracker(total: int, description: str = "Processing") -> Progress:
    """
    Create a Rich progress tracker.

    Args:
        total: Total number of items to process
        description: Description for the progress bar

    Returns:
        Progress object
    """
    progress = Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        TextColumn("[bold yellow]{task.completed}/{task.total}"),
        transient=False,
    )
    progress.add_task(description, total=total)
    return progress


def process_futures(futures: List[Any], progress: Progress = None) -> List[Any]:
    """
    Process futures from concurrent operations, optionally with progress tracking.

    Args:
        futures: List of futures to process
        progress: Optional progress tracker

    Returns:
        List of results from futures
    """
    results = []

    for future in futures:
        try:
            result = future.result()
            results.append(result)
            if progress:
                progress.advance(progress.tasks[0].id)
        except Exception as e:
            console.print(f"[bold red]Error:[/] {str(e)}")
            if progress:
                progress.advance(progress.tasks[0].id)

    return results
