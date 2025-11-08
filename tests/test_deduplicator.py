"""Tests for the ContentDeduplicator."""

import pytest
import tempfile
from pathlib import Path
from hydracontext.core.deduplicator import ContentDeduplicator, ContentHash


def test_basic_deduplication():
    """Test basic duplicate detection."""
    dedup = ContentDeduplicator()

    text1 = "The quick brown fox"
    text2 = "Something different"
    text3 = "The quick brown fox"  # Duplicate of text1

    assert dedup.is_duplicate(text1) is False
    assert dedup.is_duplicate(text2) is False
    assert dedup.is_duplicate(text3) is True


def test_different_hash_algorithms():
    """Test different hashing algorithms."""
    for algo in ['md5', 'sha256', 'blake2b']:
        dedup = ContentDeduplicator(algorithm=algo)

        text = "Test text"
        assert dedup.is_duplicate(text) is False
        assert dedup.is_duplicate(text) is True


def test_normalization():
    """Test that normalization finds similar text."""
    dedup = ContentDeduplicator(normalize=True)

    text1 = "The Quick Brown Fox"
    text2 = "the quick brown fox"  # Different case
    text3 = "The   Quick   Brown   Fox"  # Different whitespace

    assert dedup.is_duplicate(text1) is False
    assert dedup.is_duplicate(text2) is True  # Should match due to normalization
    assert dedup.is_duplicate(text3) is True


def test_no_normalization():
    """Test that without normalization, exact matches are required."""
    dedup = ContentDeduplicator(normalize=False)

    text1 = "The Quick Brown Fox"
    text2 = "the quick brown fox"  # Different case

    assert dedup.is_duplicate(text1) is False
    assert dedup.is_duplicate(text2) is False  # Should NOT match


def test_min_length():
    """Test minimum length threshold."""
    dedup = ContentDeduplicator(min_length=10)

    short = "Hi"
    long = "This is a longer text string"

    assert dedup.is_duplicate(short) is False  # Too short, always False
    assert dedup.is_duplicate(short) is False  # Still too short
    assert dedup.is_duplicate(long) is False
    assert dedup.is_duplicate(long) is True  # Long enough, now duplicate


def test_deduplicate_list():
    """Test deduplicating a list of texts."""
    dedup = ContentDeduplicator()

    texts = [
        "First text",
        "Second text",
        "First text",  # Duplicate
        "Third text",
        "Second text",  # Duplicate
        "Fourth text",
    ]

    unique = dedup.deduplicate_list(texts)

    assert len(unique) == 4
    assert "First text" in unique
    assert "Second text" in unique
    assert "Third text" in unique
    assert "Fourth text" in unique


def test_statistics():
    """Test statistics tracking."""
    dedup = ContentDeduplicator()

    dedup.is_duplicate("Text 1")
    dedup.is_duplicate("Text 2")
    dedup.is_duplicate("Text 1")  # Duplicate

    stats = dedup.get_statistics()

    assert stats['total_processed'] == 3
    assert stats['unique_content'] == 2
    assert stats['duplicates_found'] == 1
    assert stats['dedup_ratio'] == pytest.approx(1/3)


def test_hash_info():
    """Test retrieving hash information."""
    dedup = ContentDeduplicator()

    text = "Test text for hashing"
    dedup.is_duplicate(text)

    info = dedup.get_hash_info(text)

    assert info is not None
    assert info.text[:200] in text  # Preview stored
    assert info.occurrences == 1
    assert info.first_seen is not None


def test_cache_persistence():
    """Test saving and loading cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_path = Path(tmpdir) / "cache.jsonl"

        # Create deduplicator and add some data
        dedup1 = ContentDeduplicator(cache_path=cache_path)
        dedup1.is_duplicate("Text 1")
        dedup1.is_duplicate("Text 2")
        dedup1.save_cache()

        # Load cache in new deduplicator
        dedup2 = ContentDeduplicator(cache_path=cache_path)

        # Should recognize as duplicate
        assert dedup2.is_duplicate("Text 1") is True
        assert dedup2.is_duplicate("Text 2") is True
        assert dedup2.is_duplicate("Text 3") is False


def test_clear_cache():
    """Test clearing the cache."""
    dedup = ContentDeduplicator()

    dedup.is_duplicate("Text 1")
    assert dedup.get_statistics()['unique_content'] == 1

    dedup.clear_cache()

    stats = dedup.get_statistics()
    assert stats['unique_content'] == 0
    assert stats['total_processed'] == 0


def test_export_hashes_jsonl():
    """Test exporting hashes to JSONL."""
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "hashes.jsonl"

        dedup = ContentDeduplicator()
        dedup.is_duplicate("Text 1")
        dedup.is_duplicate("Text 2")

        dedup.export_hashes(export_path, format='jsonl')

        assert export_path.exists()
        lines = export_path.read_text().strip().split('\n')
        assert len(lines) == 2  # Two unique texts


def test_export_hashes_csv():
    """Test exporting hashes to CSV."""
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "hashes.csv"

        dedup = ContentDeduplicator()
        dedup.is_duplicate("Text 1")
        dedup.is_duplicate("Text 2")

        dedup.export_hashes(export_path, format='csv')

        assert export_path.exists()
        content = export_path.read_text()
        assert 'hash' in content
        assert 'text' in content


def test_occurrence_counting():
    """Test that occurrences are counted correctly."""
    dedup = ContentDeduplicator()

    text = "Repeated text"

    for _ in range(5):
        dedup.is_duplicate(text)

    info = dedup.get_hash_info(text)
    assert info.occurrences == 5


def test_record_parameter():
    """Test the record parameter in is_duplicate."""
    dedup = ContentDeduplicator()

    text = "Test text"

    # Don't record
    assert dedup.is_duplicate(text, record=False) is False
    assert dedup.get_statistics()['total_processed'] == 1
    assert dedup.get_statistics()['unique_content'] == 0

    # Now record
    assert dedup.is_duplicate(text, record=True) is False
    assert dedup.get_statistics()['unique_content'] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
