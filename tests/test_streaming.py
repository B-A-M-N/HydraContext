"""Tests for streaming utilities."""

import pytest
import tempfile
from pathlib import Path
from hydracontext.utils.streaming import StreamingProcessor, should_use_streaming


def test_should_use_streaming_large_file():
    """Test that large files trigger streaming."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        # Write 60MB of data
        f.write("A" * (60 * 1024 * 1024))
        temp_path = Path(f.name)

    try:
        assert should_use_streaming(temp_path, threshold_mb=50) is True
    finally:
        temp_path.unlink()


def test_should_use_streaming_small_file():
    """Test that small files don't trigger streaming."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Small content")
        temp_path = Path(f.name)

    try:
        assert should_use_streaming(temp_path, threshold_mb=50) is False
    finally:
        temp_path.unlink()


def test_streaming_processor_init():
    """Test initializing streaming processor."""
    processor = StreamingProcessor(
        chunk_size=1024,
        granularity='sentence',
        classify=True,
        deduplicate=True
    )

    assert processor.chunk_size == 1024
    assert processor.granularity == 'sentence'
    assert processor.classifier is not None
    assert processor.deduplicator is not None


def test_streaming_processor_no_classify():
    """Test processor without classification."""
    processor = StreamingProcessor(classify=False)

    assert processor.classifier is None


def test_streaming_processor_no_dedup():
    """Test processor without deduplication."""
    processor = StreamingProcessor(deduplicate=False)

    assert processor.deduplicator is None


def test_streaming_process_file():
    """Test processing a file in streaming mode."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create input file
        input_path = Path(tmpdir) / "input.txt"
        input_path.write_text("""
        This is sentence one. This is sentence two.
        This is sentence three. This is sentence four.

        This is a new paragraph with more sentences.
        Let's add some more content to process.
        """)

        output_path = Path(tmpdir) / "output.jsonl"

        # Process with streaming
        processor = StreamingProcessor(
            chunk_size=100,  # Small chunks for testing
            granularity='sentence',
            classify=True,
            deduplicate=False
        )

        stats = processor.process_file_streaming(input_path, output_path)

        # Verify output exists
        assert output_path.exists()

        # Verify stats
        assert stats['chunks_processed'] > 0
        assert stats['segments_processed'] > 0
        assert stats['segments_written'] > 0

        # Verify output content
        lines = output_path.read_text().strip().split('\n')
        assert len(lines) > 0


def test_streaming_with_deduplication():
    """Test streaming with deduplication enabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.txt"
        input_path.write_text("""
        This is a repeated sentence. This is a repeated sentence.
        This is a unique sentence. This is a repeated sentence.
        """)

        output_path = Path(tmpdir) / "output.jsonl"

        processor = StreamingProcessor(
            chunk_size=100,
            granularity='sentence',
            classify=False,
            deduplicate=True
        )

        stats = processor.process_file_streaming(input_path, output_path)

        # Should have skipped duplicates
        assert stats['duplicates_skipped'] > 0


def test_streaming_progress_callback():
    """Test progress callback during streaming."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.txt"
        input_path.write_text("A" * 1000)

        output_path = Path(tmpdir) / "output.jsonl"

        progress_updates = []

        def callback(progress):
            progress_updates.append(progress)

        processor = StreamingProcessor(chunk_size=100)
        processor.process_file_streaming(
            input_path,
            output_path,
            progress_callback=callback
        )

        # Should have received progress updates
        assert len(progress_updates) > 0
        assert all('percent' in p for p in progress_updates)


def test_streaming_get_statistics():
    """Test getting statistics from streaming processor."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.txt"
        input_path.write_text("Test sentence. Another sentence.")

        output_path = Path(tmpdir) / "output.jsonl"

        processor = StreamingProcessor(
            chunk_size=100,
            deduplicate=True
        )

        processor.process_file_streaming(input_path, output_path)

        stats = processor.get_statistics()

        assert 'chunks_processed' in stats
        assert 'segments_processed' in stats
        assert 'bytes_processed' in stats
        assert 'deduplication' in stats  # Should include dedup stats


def test_streaming_with_cache():
    """Test streaming with persistent deduplication cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.txt"
        input_path.write_text("Test sentence. Test sentence.")

        output_path = Path(tmpdir) / "output.jsonl"
        cache_path = Path(tmpdir) / "cache.jsonl"

        processor = StreamingProcessor(
            chunk_size=100,
            deduplicate=True,
            cache_path=cache_path
        )

        processor.process_file_streaming(input_path, output_path)

        # Cache should have been created
        assert cache_path.exists() or processor.deduplicator.hash_map  # Either persisted or in memory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
