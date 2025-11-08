"""
Streaming utilities for processing large files.

Provides memory-efficient file processing by reading and processing in chunks.
"""

from pathlib import Path
from typing import Iterator, Optional, Callable, Dict, Any
import json

from hydracontext.core.segmenter import ContextSegmenter, Segment
from hydracontext.core.deduplicator import ContentDeduplicator
from hydracontext.core.classifier import ContentClassifier
from hydracontext.utils.logging import get_logger

logger = get_logger(__name__)


class StreamingProcessor:
    """
    Process large files in chunks to reduce memory usage.

    Reads file in configurable chunk sizes and processes segments
    incrementally, writing results as they're generated.
    """

    def __init__(
        self,
        chunk_size: int = 1024 * 1024,  # 1MB default
        overlap_size: int = 1000,  # Character overlap between chunks
        granularity: str = 'sentence',
        classify: bool = True,
        deduplicate: bool = True,
        cache_path: Optional[Path] = None
    ):
        """
        Initialize streaming processor.

        Args:
            chunk_size: Size of chunks to read (bytes)
            overlap_size: Overlap between chunks to avoid breaking sentences
            granularity: Segmentation granularity
            classify: Whether to classify content
            deduplicate: Whether to deduplicate
            cache_path: Path to deduplication cache
        """
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.granularity = granularity

        # Initialize components
        self.segmenter = ContextSegmenter()
        self.classifier = ContentClassifier() if classify else None
        self.deduplicator = ContentDeduplicator(cache_path=cache_path) if deduplicate else None

        # Statistics
        self.stats = {
            'chunks_processed': 0,
            'segments_processed': 0,
            'segments_written': 0,
            'duplicates_skipped': 0,
            'bytes_processed': 0,
        }

    def process_file_streaming(
        self,
        input_path: Path,
        output_path: Path,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Process a file in streaming mode.

        Args:
            input_path: Path to input file
            output_path: Path to output JSONL file
            progress_callback: Optional callback for progress updates

        Returns:
            Processing statistics
        """
        logger.info(f"Starting streaming processing: {input_path}")
        file_size = input_path.stat().st_size
        logger.info(f"File size: {file_size:,} bytes")

        # Create output file
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(input_path, 'r', encoding='utf-8') as infile:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                overlap_buffer = ""
                position = 0

                for chunk in self._read_chunks(infile, self.chunk_size):
                    # Combine with overlap from previous chunk
                    text = overlap_buffer + chunk

                    # Process chunk
                    segments = self.segmenter.segment_text(text, granularity=self.granularity)

                    # Determine which segments to keep for next iteration
                    # Keep last few segments as overlap to avoid breaking boundaries
                    keep_count = min(3, len(segments))
                    process_segments = segments[:-keep_count] if len(segments) > keep_count else segments

                    # Save overlap for next iteration
                    if len(segments) > keep_count:
                        overlap_buffer = ''.join(seg.text for seg in segments[-keep_count:])
                    else:
                        overlap_buffer = ""

                    # Process and write segments
                    for segment in process_segments:
                        result = self._process_segment(segment)

                        if result:
                            # Write JSONL
                            json.dump(result, outfile, ensure_ascii=False)
                            outfile.write('\n')
                            self.stats['segments_written'] += 1

                        self.stats['segments_processed'] += 1

                    self.stats['chunks_processed'] += 1
                    self.stats['bytes_processed'] += len(chunk)

                    # Progress callback
                    if progress_callback:
                        progress = {
                            'bytes_processed': self.stats['bytes_processed'],
                            'file_size': file_size,
                            'percent': (self.stats['bytes_processed'] / file_size * 100) if file_size > 0 else 0,
                            'chunks': self.stats['chunks_processed'],
                            'segments': self.stats['segments_processed'],
                        }
                        progress_callback(progress)

                # Process remaining overlap
                if overlap_buffer:
                    logger.debug("Processing final overlap buffer")
                    segments = self.segmenter.segment_text(overlap_buffer, granularity=self.granularity)

                    for segment in segments:
                        result = self._process_segment(segment)
                        if result:
                            json.dump(result, outfile, ensure_ascii=False)
                            outfile.write('\n')
                            self.stats['segments_written'] += 1
                        self.stats['segments_processed'] += 1

        logger.info(f"Streaming processing complete. Processed {self.stats['segments_processed']} segments")
        logger.info(f"Written {self.stats['segments_written']} unique segments")

        return self.stats.copy()

    def _read_chunks(self, file_handle, chunk_size: int) -> Iterator[str]:
        """
        Read file in chunks.

        Args:
            file_handle: Open file handle
            chunk_size: Size of chunks to read

        Yields:
            Text chunks
        """
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break

            logger.debug(f"Read chunk of {len(chunk)} characters")
            yield chunk

    def _process_segment(self, segment: Segment) -> Optional[Dict[str, Any]]:
        """
        Process a single segment.

        Args:
            segment: Segment to process

        Returns:
            Result dictionary or None if duplicate
        """
        # Check for duplicates
        if self.deduplicator:
            is_duplicate = self.deduplicator.is_duplicate(segment.text)
            if is_duplicate:
                self.stats['duplicates_skipped'] += 1
                logger.debug(f"Skipping duplicate segment: {segment.text[:50]}...")
                return None

        # Classify if enabled
        classification = None
        if self.classifier:
            classification = self.classifier.classify(segment.text)

        # Build result
        result = {
            'text': segment.text,
            'type': segment.type.value,
            'start_pos': segment.start_pos,
            'end_pos': segment.end_pos,
            'length': len(segment.text),
        }

        if classification:
            result['classification'] = {
                'content_type': classification.content_type.value,
                'confidence': round(classification.confidence, 3),
            }

        if segment.metadata:
            result['metadata'] = segment.metadata

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.

        Returns:
            Statistics dictionary
        """
        stats = self.stats.copy()

        if self.deduplicator:
            dedup_stats = self.deduplicator.get_statistics()
            stats['deduplication'] = dedup_stats

        return stats


def should_use_streaming(file_path: Path, threshold_mb: int = 50) -> bool:
    """
    Determine if streaming mode should be used for a file.

    Args:
        file_path: Path to file
        threshold_mb: Size threshold in MB

    Returns:
        True if streaming is recommended
    """
    size_mb = file_path.stat().st_size / (1024 * 1024)
    should_stream = size_mb > threshold_mb

    if should_stream:
        logger.info(f"File size {size_mb:.1f}MB > {threshold_mb}MB, using streaming mode")
    else:
        logger.debug(f"File size {size_mb:.1f}MB <= {threshold_mb}MB, using standard mode")

    return should_stream
