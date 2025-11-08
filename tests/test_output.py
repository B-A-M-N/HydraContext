"""Tests for output utilities."""

import pytest
import tempfile
import json
from pathlib import Path
from hydracontext.utils.output import OutputWriter, StatsCollector


def test_write_jsonl():
    """Test writing JSONL format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.jsonl"

        data = [
            {'id': 1, 'text': 'First entry'},
            {'id': 2, 'text': 'Second entry'},
        ]

        OutputWriter.write_jsonl(data, output_path)

        assert output_path.exists()

        # Read back and verify
        lines = output_path.read_text().strip().split('\n')
        assert len(lines) == 2

        parsed = [json.loads(line) for line in lines]
        assert parsed == data


def test_write_jsonl_append():
    """Test appending to JSONL file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "output.jsonl"

        data1 = [{'id': 1}]
        data2 = [{'id': 2}]

        OutputWriter.write_jsonl(data1, output_path, append=False)
        OutputWriter.write_jsonl(data2, output_path, append=True)

        lines = output_path.read_text().strip().split('\n')
        assert len(lines) == 2


def test_read_jsonl():
    """Test reading JSONL format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = Path(tmpdir) / "input.jsonl"

        data = [
            {'id': 1, 'text': 'First'},
            {'id': 2, 'text': 'Second'},
        ]

        # Write data
        with open(input_path, 'w') as f:
            for item in data:
                json.dump(item, f)
                f.write('\n')

        # Read back
        read_data = OutputWriter.read_jsonl(input_path)

        assert read_data == data


def test_write_stats_json():
    """Test writing statistics in JSON format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stats.json"

        stats = {
            'total': 100,
            'unique': 80,
            'duplicates': 20,
        }

        OutputWriter.write_stats(stats, output_path, format='json')

        assert output_path.exists()

        # Read and verify
        with open(output_path) as f:
            loaded = json.load(f)

        assert loaded == stats


def test_write_stats_txt():
    """Test writing statistics in text format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "stats.txt"

        stats = {
            'total': 100,
            'unique': 80,
        }

        OutputWriter.write_stats(stats, output_path, format='txt')

        assert output_path.exists()

        content = output_path.read_text()
        assert 'total' in content
        assert '100' in content


def test_stats_collector_initialization():
    """Test stats collector initialization."""
    collector = StatsCollector()

    stats = collector.get_stats()

    assert 'processing' in stats
    assert 'input' in stats
    assert 'segmentation' in stats


def test_stats_collector_start_end():
    """Test start and end processing tracking."""
    collector = StatsCollector()

    collector.start_processing()
    assert collector.stats['processing']['start_time'] is not None

    collector.end_processing()
    assert collector.stats['processing']['end_time'] is not None
    assert collector.stats['processing']['duration_seconds'] > 0


def test_stats_collector_input_stats():
    """Test updating input statistics."""
    collector = StatsCollector()

    text = "Sample text with 100 characters" * 10

    collector.update_input_stats(text)

    assert collector.stats['input']['total_characters'] > 0
    assert collector.stats['input']['files_processed'] == 1


def test_stats_collector_segment_stats():
    """Test updating segment statistics."""
    collector = StatsCollector()

    collector.update_segment_stats('sentence')
    collector.update_segment_stats('sentence')
    collector.update_segment_stats('code_block')

    assert collector.stats['segmentation']['total_segments'] == 3
    assert collector.stats['segmentation']['sentences'] == 2
    assert collector.stats['segmentation']['code_blocks'] == 1


def test_stats_collector_classification_stats():
    """Test updating classification statistics."""
    collector = StatsCollector()

    collector.update_classification_stats('prose')
    collector.update_classification_stats('code')
    collector.update_classification_stats('prose')

    assert collector.stats['classification']['prose'] == 2
    assert collector.stats['classification']['code'] == 1


def test_stats_collector_dedup_stats():
    """Test updating deduplication statistics."""
    collector = StatsCollector()

    dedup_stats = {
        'total_processed': 100,
        'unique_content': 80,
        'duplicates_found': 20,
        'dedup_ratio': 0.2,
    }

    collector.update_dedup_stats(dedup_stats)

    assert collector.stats['deduplication']['total_processed'] == 100
    assert collector.stats['deduplication']['unique_content'] == 80


def test_stats_collector_output_stats():
    """Test updating output statistics."""
    collector = StatsCollector()

    collector.update_output_stats(50)

    assert collector.stats['output']['segments_written'] == 50
    assert collector.stats['output']['output_files'] == 1


def test_stats_collector_print_summary():
    """Test printing summary (should not raise errors)."""
    collector = StatsCollector()

    collector.start_processing()
    collector.update_input_stats("Sample text")
    collector.update_segment_stats('sentence')
    collector.end_processing()

    # Should not raise any errors
    collector.print_summary()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
