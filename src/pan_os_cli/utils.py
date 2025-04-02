"""Utility functions for pan-os-cli."""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Type, TypeVar

import yaml
from pydantic import BaseModel, ValidationError
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
        raise yaml.YAMLError(f"Error parsing YAML file {path}: {str(e)}") from e


def load_yaml_file(file_path: str) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents.

    This is an alias for load_yaml to maintain backward compatibility.

    Args:
        file_path: Path to the YAML file

    Returns:
        Dict containing parsed YAML content
    """
    return load_yaml(file_path)


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
        raise IOError(f"Error writing YAML file {path}: {str(e)}") from e


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
    result = []
    errors = []

    for i, item in enumerate(data):
        try:
            validated = model_class(**item)
            result.append(validated)
        except ValidationError as e:
            errors.append(f"Item {i}: {str(e)}")

    if errors:
        raise ValidationError(
            f"Validation failed for {len(errors)} items:\n" + "\n".join(errors),
            model=model_class,
        )

    return result


def validate_objects_from_yaml(
    yaml_data: Dict[str, Any], object_key: str, model_class: Type[BaseModel]
) -> List[BaseModel]:
    """
    Validate objects from YAML data against a specified model.

    Args:
        yaml_data: Parsed YAML data
        object_key: Key in the YAML data containing the objects list
        model_class: Pydantic model class to validate against

    Returns:
        List of validated model instances

    Raises:
        ValueError: If the object_key is not found in yaml_data
        ValidationError: If validation fails
    """
    if object_key not in yaml_data:
        raise ValueError(f"Key '{object_key}' not found in YAML data")

    objects_data = yaml_data[object_key]
    if not isinstance(objects_data, list):
        raise ValueError(f"Expected a list for '{object_key}', got {type(objects_data).__name__}")

    return validate_data(objects_data, model_class)


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
        TextColumn("[bold green]{task.completed}/{task.total}"),
        console=console,
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
    import concurrent.futures

    results = []
    errors = []

    for future in concurrent.futures.as_completed(futures):
        try:
            result = future.result()
            results.append(result)
            if progress:
                progress.update(progress.tasks[0].id, advance=1)
        except Exception as e:
            errors.append(str(e))
            if progress:
                progress.update(progress.tasks[0].id, advance=1)

    if errors:
        console.print("[bold red]Errors occurred during processing[/bold red]")
        for i, error in enumerate(errors, start=1):
            console.print(f"  {i}. {error}")

    return results
