"""Tests for validation utilities."""

import pytest
import tempfile
from pathlib import Path
from hydracontext.utils.validation import (
    ValidationError,
    validate_file_readable,
    validate_file_writable,
    validate_text_encoding,
    validate_text_content,
    validate_granularity,
    validate_hash_algorithm,
    validate_confidence_threshold,
    validate_file_size,
)


def test_validate_file_readable_exists():
    """Test validating a readable file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test content")
        temp_path = Path(f.name)

    try:
        validate_file_readable(temp_path)  # Should not raise
    finally:
        temp_path.unlink()


def test_validate_file_readable_not_exists():
    """Test validating a non-existent file."""
    fake_path = Path("/this/does/not/exist.txt")

    with pytest.raises(ValidationError, match="File not found"):
        validate_file_readable(fake_path)


def test_validate_file_writable():
    """Test validating writable file path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.txt"
        validate_file_writable(output_path)  # Should not raise


def test_validate_file_writable_creates_dir():
    """Test that validation creates parent directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "subdir" / "output.txt"
        validate_file_writable(output_path)

        assert output_path.parent.exists()


def test_validate_text_encoding_valid():
    """Test validating file with correct encoding."""
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as f:
        f.write("Hello, World! 你好")
        temp_path = Path(f.name)

    try:
        validate_text_encoding(temp_path, encoding='utf-8')  # Should not raise
    finally:
        temp_path.unlink()


def test_validate_text_content_valid():
    """Test validating valid text content."""
    text = "This is valid text"
    validate_text_content(text, min_length=1)  # Should not raise


def test_validate_text_content_too_short():
    """Test validating text that's too short."""
    text = "Hi"

    with pytest.raises(ValidationError, match="Text too short"):
        validate_text_content(text, min_length=10)


def test_validate_text_content_too_long():
    """Test validating text that's too long."""
    text = "A" * 1000

    with pytest.raises(ValidationError, match="Text too long"):
        validate_text_content(text, min_length=1, max_length=100)


def test_validate_text_content_not_string():
    """Test validating non-string input."""
    with pytest.raises(ValidationError, match="Expected string"):
        validate_text_content(123)  # Not a string


def test_validate_granularity_valid():
    """Test validating valid granularity values."""
    validate_granularity('sentence')  # Should not raise
    validate_granularity('paragraph')  # Should not raise


def test_validate_granularity_invalid():
    """Test validating invalid granularity."""
    with pytest.raises(ValidationError, match="Invalid granularity"):
        validate_granularity('word')


def test_validate_hash_algorithm_valid():
    """Test validating valid hash algorithms."""
    validate_hash_algorithm('md5')  # Should not raise
    validate_hash_algorithm('sha256')  # Should not raise
    validate_hash_algorithm('blake2b')  # Should not raise


def test_validate_hash_algorithm_invalid():
    """Test validating invalid hash algorithm."""
    with pytest.raises(ValidationError, match="Invalid algorithm"):
        validate_hash_algorithm('sha512')


def test_validate_confidence_threshold_valid():
    """Test validating valid confidence thresholds."""
    validate_confidence_threshold(0.0)  # Should not raise
    validate_confidence_threshold(0.5)  # Should not raise
    validate_confidence_threshold(1.0)  # Should not raise


def test_validate_confidence_threshold_out_of_range():
    """Test validating out-of-range threshold."""
    with pytest.raises(ValidationError, match="must be between 0.0 and 1.0"):
        validate_confidence_threshold(1.5)

    with pytest.raises(ValidationError, match="must be between 0.0 and 1.0"):
        validate_confidence_threshold(-0.1)


def test_validate_confidence_threshold_not_number():
    """Test validating non-numeric threshold."""
    with pytest.raises(ValidationError, match="must be a number"):
        validate_confidence_threshold("0.5")


def test_validate_file_size():
    """Test validating file size."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("A" * 1000)  # 1KB file
        temp_path = Path(f.name)

    try:
        size = validate_file_size(temp_path, max_size_mb=1)
        assert size == 1000
    finally:
        temp_path.unlink()


def test_validate_file_size_too_large():
    """Test validating oversized file."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("A" * (2 * 1024 * 1024))  # 2MB file
        temp_path = Path(f.name)

    try:
        with pytest.raises(ValidationError, match="File too large"):
            validate_file_size(temp_path, max_size_mb=1)
    finally:
        temp_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
