"""
Input validation utilities for HydraContext.

Provides validation for file paths, text content, and parameters.
"""

import os
from pathlib import Path
from typing import Optional, List


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_file_readable(file_path: Path) -> None:
    """
    Validate that a file exists and is readable.

    Args:
        file_path: Path to file

    Raises:
        ValidationError: If file doesn't exist or isn't readable
    """
    if not file_path.exists():
        raise ValidationError(f"File not found: {file_path}")

    if not file_path.is_file():
        raise ValidationError(f"Not a file: {file_path}")

    if not os.access(file_path, os.R_OK):
        raise ValidationError(f"File not readable: {file_path}")


def validate_file_writable(file_path: Path) -> None:
    """
    Validate that a file path is writable.

    Args:
        file_path: Path to file

    Raises:
        ValidationError: If path isn't writable
    """
    # Check if parent directory exists
    parent = file_path.parent
    if not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            raise ValidationError(f"Cannot create directory {parent}: {e}")

    # Check if directory is writable
    if not os.access(parent, os.W_OK):
        raise ValidationError(f"Directory not writable: {parent}")

    # If file exists, check if it's writable
    if file_path.exists() and not os.access(file_path, os.W_OK):
        raise ValidationError(f"File not writable: {file_path}")


def validate_text_encoding(file_path: Path, encoding: str = 'utf-8') -> None:
    """
    Validate that a file can be read with specified encoding.

    Args:
        file_path: Path to file
        encoding: Text encoding to validate

    Raises:
        ValidationError: If file cannot be decoded
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            # Try to read first 1KB
            f.read(1024)
    except UnicodeDecodeError as e:
        raise ValidationError(f"File encoding error in {file_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Error reading file {file_path}: {e}")


def validate_text_content(text: str, min_length: int = 1, max_length: Optional[int] = None) -> None:
    """
    Validate text content.

    Args:
        text: Text to validate
        min_length: Minimum text length
        max_length: Optional maximum text length

    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(text, str):
        raise ValidationError(f"Expected string, got {type(text).__name__}")

    if len(text) < min_length:
        raise ValidationError(f"Text too short: {len(text)} < {min_length}")

    if max_length and len(text) > max_length:
        raise ValidationError(f"Text too long: {len(text)} > {max_length}")


def validate_granularity(granularity: str) -> None:
    """
    Validate segmentation granularity parameter.

    Args:
        granularity: Granularity value

    Raises:
        ValidationError: If granularity is invalid
    """
    valid_values = ['sentence', 'paragraph']
    if granularity not in valid_values:
        raise ValidationError(
            f"Invalid granularity '{granularity}'. Must be one of: {', '.join(valid_values)}"
        )


def validate_hash_algorithm(algorithm: str) -> None:
    """
    Validate hash algorithm parameter.

    Args:
        algorithm: Hash algorithm name

    Raises:
        ValidationError: If algorithm is invalid
    """
    valid_algorithms = ['md5', 'sha256', 'blake2b']
    if algorithm not in valid_algorithms:
        raise ValidationError(
            f"Invalid algorithm '{algorithm}'. Must be one of: {', '.join(valid_algorithms)}"
        )


def validate_confidence_threshold(threshold: float) -> None:
    """
    Validate confidence threshold parameter.

    Args:
        threshold: Threshold value

    Raises:
        ValidationError: If threshold is invalid
    """
    if not isinstance(threshold, (int, float)):
        raise ValidationError(f"Threshold must be a number, got {type(threshold).__name__}")

    if not 0.0 <= threshold <= 1.0:
        raise ValidationError(f"Threshold must be between 0.0 and 1.0, got {threshold}")


def validate_file_size(file_path: Path, max_size_mb: Optional[int] = None) -> int:
    """
    Validate file size and return size in bytes.

    Args:
        file_path: Path to file
        max_size_mb: Optional maximum file size in MB

    Returns:
        File size in bytes

    Raises:
        ValidationError: If file is too large
    """
    size_bytes = file_path.stat().st_size

    if max_size_mb:
        max_size_bytes = max_size_mb * 1024 * 1024
        if size_bytes > max_size_bytes:
            size_mb = size_bytes / (1024 * 1024)
            raise ValidationError(
                f"File too large: {size_mb:.1f}MB > {max_size_mb}MB. "
                "Consider using streaming mode."
            )

    return size_bytes
