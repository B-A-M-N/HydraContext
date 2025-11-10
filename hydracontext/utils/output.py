"""
Output utilities for HydraContext.

Handles JSONL export, statistics generation, and reporting.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class OutputWriter:
    """
    Handle output generation in various formats.

    Supports JSONL for structured data and human-readable stats.
    """

    @staticmethod
    def write_jsonl(
        data: List[Dict[str, Any]],
        output_path: Path,
        append: bool = False
    ) -> None:
        """
        Write data to JSONL file.

        Args:
            data: List of dictionaries to write
            output_path: Path to output file
            append: Whether to append or overwrite
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        mode = 'a' if append else 'w'

        with open(output_path, mode, encoding='utf-8') as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write('\n')

    @staticmethod
    def read_jsonl(input_path: Path) -> List[Dict[str, Any]]:
        """
        Read data from JSONL file.

        Args:
            input_path: Path to input file

        Returns:
            List of dictionaries
        """
        data = []

        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        return data

    @staticmethod
    def write_stats(
        stats: Dict[str, Any],
        output_path: Path,
        format: str = 'json'
    ) -> None:
        """
        Write statistics to file.

        Args:
            stats: Statistics dictionary
            output_path: Path to output file
            format: Output format ('json' or 'txt')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

        elif format == 'txt':
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("HydraContext Processing Statistics\n")
                f.write("=" * 50 + "\n\n")

                for key, value in stats.items():
                    if isinstance(value, dict):
                        f.write(f"{key}:\n")
                        for sub_key, sub_value in value.items():
                            f.write(f"  {sub_key}: {sub_value}\n")
                    else:
                        f.write(f"{key}: {value}\n")

                f.write("\n" + "=" * 50 + "\n")
                f.write(f"Generated: {datetime.utcnow().isoformat()}\n")

        else:
            raise ValueError(f"Unsupported format: {format}")


class StatsCollector:
    """
    Collect and aggregate processing statistics.
    """

    def __init__(self):
        """Initialize statistics collector."""
        self.stats = {
            'processing': {
                'start_time': None,
                'end_time': None,
                'duration_seconds': 0,
            },
            'input': {
                'total_characters': 0,
                'total_lines': 0,
                'files_processed': 0,
            },
            'segmentation': {
                'total_segments': 0,
                'sentences': 0,
                'paragraphs': 0,
                'code_blocks': 0,
                'list_items': 0,
                'headings': 0,
            },
            'classification': {
                'prose': 0,
                'code': 0,
                'structured_data': 0,
                'mixed': 0,
                'unknown': 0,
            },
            'deduplication': {
                'total_processed': 0,
                'unique_content': 0,
                'duplicates_removed': 0,
                'dedup_ratio': 0.0,
            },
            'output': {
                'segments_written': 0,
                'output_files': 0,
            }
        }

    def start_processing(self) -> None:
        """Mark start of processing."""
        self.stats['processing']['start_time'] = datetime.utcnow().isoformat()

    def end_processing(self) -> None:
        """Mark end of processing and calculate duration."""
        end_time = datetime.utcnow()
        self.stats['processing']['end_time'] = end_time.isoformat()

        if self.stats['processing']['start_time']:
            start_time = datetime.fromisoformat(self.stats['processing']['start_time'])
            duration = (end_time - start_time).total_seconds()
            self.stats['processing']['duration_seconds'] = round(duration, 2)

    def update_input_stats(self, text: str) -> None:
        """
        Update input statistics.

        Args:
            text: Input text
        """
        self.stats['input']['total_characters'] += len(text)
        self.stats['input']['total_lines'] += len(text.splitlines())
        self.stats['input']['files_processed'] += 1

    def update_segment_stats(self, segment_type: str) -> None:
        """
        Update segmentation statistics.

        Args:
            segment_type: Type of segment
        """
        self.stats['segmentation']['total_segments'] += 1

        type_lower = segment_type.lower()
        if type_lower in self.stats['segmentation']:
            self.stats['segmentation'][type_lower] += 1

    def update_classification_stats(self, content_type: str) -> None:
        """
        Update classification statistics.

        Args:
            content_type: Type of content
        """
        type_lower = content_type.lower()
        if type_lower in self.stats['classification']:
            self.stats['classification'][type_lower] += 1

    def update_dedup_stats(self, dedup_stats: Dict[str, Any]) -> None:
        """
        Update deduplication statistics.

        Args:
            dedup_stats: Stats from deduplicator
        """
        self.stats['deduplication'].update(dedup_stats)

    def update_output_stats(self, segments_count: int) -> None:
        """
        Update output statistics.

        Args:
            segments_count: Number of segments written
        """
        self.stats['output']['segments_written'] += segments_count
        self.stats['output']['output_files'] += 1

    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()

    def print_summary(self) -> None:
        """Print a human-readable summary."""
        print("\n" + "=" * 60)
        print("HydraContext Processing Summary")
        print("=" * 60 + "\n")

        print(f"Duration: {self.stats['processing']['duration_seconds']}s")
        print(f"Files processed: {self.stats['input']['files_processed']}")
        print(f"Total characters: {self.stats['input']['total_characters']:,}")
        print(f"Total lines: {self.stats['input']['total_lines']:,}")

        print("\nSegmentation:")
        print(f"  Total segments: {self.stats['segmentation']['total_segments']}")
        print(f"  - Sentences: {self.stats['segmentation']['sentences']}")
        print(f"  - Paragraphs: {self.stats['segmentation']['paragraphs']}")
        print(f"  - Code blocks: {self.stats['segmentation']['code_blocks']}")
        print(f"  - List items: {self.stats['segmentation']['list_items']}")
        print(f"  - Headings: {self.stats['segmentation']['headings']}")

        print("\nClassification:")
        print(f"  - Prose: {self.stats['classification']['prose']}")
        print(f"  - Code: {self.stats['classification']['code']}")
        print(f"  - Structured: {self.stats['classification']['structured_data']}")
        print(f"  - Mixed: {self.stats['classification']['mixed']}")

        print("\nDeduplication:")
        print(f"  Unique content: {self.stats['deduplication']['unique_content']}")
        print(f"  Duplicates removed: {self.stats['deduplication']['duplicates_removed']}")
        dedup_ratio = self.stats['deduplication'].get('dedup_ratio', 0)
        print(f"  Dedup ratio: {dedup_ratio:.1%}")

        print("\nOutput:")
        print(f"  Segments written: {self.stats['output']['segments_written']}")
        print(f"  Output files: {self.stats['output']['output_files']}")

        print("\n" + "=" * 60 + "\n")
