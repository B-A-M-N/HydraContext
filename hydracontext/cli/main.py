"""
HydraContext CLI - Main entry point.

Command-line interface for processing text with HydraContext.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from hydracontext.core.segmenter import ContextSegmenter, SegmentType
from hydracontext.core.deduplicator import ContentDeduplicator
from hydracontext.core.classifier import ContentClassifier, ContentType
from hydracontext.utils.output import OutputWriter, StatsCollector
from hydracontext.utils.logging import setup_logging, get_logger
from hydracontext.utils.validation import (
    ValidationError,
    validate_file_readable,
    validate_file_writable,
    validate_text_encoding,
    validate_text_content,
    validate_granularity,
    validate_file_size,
)
from hydracontext.utils.streaming import StreamingProcessor, should_use_streaming

logger = get_logger(__name__)


def process_text(
    input_text: str,
    granularity: str = 'sentence',
    classify: bool = True,
    deduplicate: bool = True,
    cache_path: Optional[Path] = None,
    output_path: Optional[Path] = None,
    stats_collector: Optional[StatsCollector] = None
) -> dict:
    """
    Process text through the HydraContext pipeline.

    Args:
        input_text: Text to process
        granularity: Segmentation granularity ('sentence' or 'paragraph')
        classify: Whether to classify content type
        deduplicate: Whether to deduplicate content
        cache_path: Path to deduplication cache
        output_path: Path to write output JSONL
        stats_collector: Optional stats collector

    Returns:
        Dictionary with processing results

    Raises:
        ValidationError: If input validation fails
    """
    # Validate inputs
    validate_text_content(input_text, min_length=1)
    validate_granularity(granularity)

    logger.debug(f"Processing {len(input_text)} characters with granularity: {granularity}")

    if stats_collector is None:
        stats_collector = StatsCollector()

    # Initialize components
    logger.debug("Initializing components")
    segmenter = ContextSegmenter()
    classifier = ContentClassifier() if classify else None
    deduplicator = ContentDeduplicator(cache_path=cache_path) if deduplicate else None

    # Update input stats
    stats_collector.update_input_stats(input_text)

    # Segment text
    segments = segmenter.segment_text(input_text, granularity=granularity)

    # Process segments
    results = []
    unique_segments = []

    for segment in segments:
        # Check for duplicates
        is_duplicate = False
        if deduplicator:
            is_duplicate = deduplicator.is_duplicate(segment.text)

        if not is_duplicate or not deduplicate:
            unique_segments.append(segment)

            # Classify content
            classification = None
            if classifier:
                classification = classifier.classify(segment.text)
                stats_collector.update_classification_stats(classification.content_type.value)

            # Update stats
            stats_collector.update_segment_stats(segment.type.value)

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

            results.append(result)

    # Update deduplication stats
    if deduplicator:
        dedup_stats = deduplicator.get_statistics()
        stats_collector.update_dedup_stats(dedup_stats)

    # Write output
    if output_path:
        OutputWriter.write_jsonl(results, output_path)
        stats_collector.update_output_stats(len(results))

    return {
        'segments': results,
        'total_segments': len(segments),
        'unique_segments': len(unique_segments),
        'duplicates': len(segments) - len(unique_segments),
    }


def process_file(
    input_path: Path,
    output_path: Path,
    granularity: str = 'sentence',
    classify: bool = True,
    deduplicate: bool = True,
    cache_path: Optional[Path] = None,
    stats_path: Optional[Path] = None,
    streaming: Optional[bool] = None,
    streaming_threshold_mb: int = 50
) -> None:
    """
    Process a single file.

    Args:
        input_path: Path to input file
        output_path: Path to output JSONL
        granularity: Segmentation granularity
        classify: Whether to classify content
        deduplicate: Whether to deduplicate
        cache_path: Path to deduplication cache
        stats_path: Path to write statistics
        streaming: Force streaming mode (None = auto-detect)
        streaming_threshold_mb: File size threshold for auto streaming

    Raises:
        ValidationError: If file validation fails
    """
    # Validate inputs
    logger.info(f"Validating input file: {input_path}")
    validate_file_readable(input_path)
    validate_text_encoding(input_path, encoding='utf-8')
    validate_file_writable(output_path)

    if stats_path:
        validate_file_writable(stats_path)

    # Determine if streaming should be used
    file_size_bytes = input_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)

    if streaming is None:
        use_streaming = should_use_streaming(input_path, streaming_threshold_mb)
    else:
        use_streaming = streaming

    logger.info(f"File size: {file_size_mb:.2f}MB, Streaming mode: {use_streaming}")

    if use_streaming:
        # Use streaming processor for large files
        logger.info("Using streaming processor")
        processor = StreamingProcessor(
            chunk_size=1024 * 1024,  # 1MB chunks
            granularity=granularity,
            classify=classify,
            deduplicate=deduplicate,
            cache_path=cache_path
        )

        def progress_callback(progress):
            logger.info(
                f"Progress: {progress['percent']:.1f}% "
                f"({progress['bytes_processed']:,} / {progress['file_size']:,} bytes)"
            )

        result = processor.process_file_streaming(
            input_path=input_path,
            output_path=output_path,
            progress_callback=progress_callback
        )

        # Write stats if requested
        if stats_path:
            logger.info(f"Writing statistics to: {stats_path}")
            OutputWriter.write_stats(result, stats_path, format='json')

        logger.info(f"Output written to: {output_path}")
        logger.info(f"Processed {result['segments_processed']} segments, "
                   f"{result['segments_written']} unique")

    else:
        # Use standard in-memory processing for small files
        logger.info("Using standard in-memory processing")
        stats_collector = StatsCollector()
        stats_collector.start_processing()

        # Read input
        logger.info(f"Reading file: {input_path}")
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                input_text = f.read()
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {input_path}: {e}")
            raise ValidationError(f"File encoding error: {e}")
        except Exception as e:
            logger.error(f"Error reading {input_path}: {e}")
            raise

        # Process
        logger.info(f"Processing with granularity: {granularity}")
        result = process_text(
            input_text=input_text,
            granularity=granularity,
            classify=classify,
            deduplicate=deduplicate,
            cache_path=cache_path,
            output_path=output_path,
            stats_collector=stats_collector
        )

        stats_collector.end_processing()

        # Print summary
        stats_collector.print_summary()

        # Write stats if requested
        if stats_path:
            logger.info(f"Writing statistics to: {stats_path}")
            stats = stats_collector.get_stats()
            OutputWriter.write_stats(stats, stats_path, format='json')
            logger.info(f"Statistics written to: {stats_path}")

        logger.info(f"Output written to: {output_path}")
        logger.info(f"Processed {result['total_segments']} segments, {result['unique_segments']} unique")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='HydraContext - Intelligent text segmentation and deduplication',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process file with sentence segmentation
  hydracontext process input.txt -o output.jsonl

  # Process with paragraph granularity
  hydracontext process input.txt -o output.jsonl -g paragraph

  # Process without classification
  hydracontext process input.txt -o output.jsonl --no-classify

  # Process with deduplication cache
  hydracontext process input.txt -o output.jsonl --cache cache.jsonl

  # Process and save statistics
  hydracontext process input.txt -o output.jsonl --stats stats.json

  # Enable debug logging
  hydracontext process input.txt -o output.jsonl --log-level DEBUG
        """
    )

    # Add global arguments
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='Logging level')
    parser.add_argument('--log-file', type=Path, help='Log to file')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process text file')
    process_parser.add_argument('input', type=Path, help='Input text file')
    process_parser.add_argument('-o', '--output', type=Path, required=True,
                                help='Output JSONL file')
    process_parser.add_argument('-g', '--granularity', choices=['sentence', 'paragraph'],
                                default='sentence', help='Segmentation granularity')
    process_parser.add_argument('--no-classify', action='store_true',
                                help='Disable content classification')
    process_parser.add_argument('--no-dedup', action='store_true',
                                help='Disable deduplication')
    process_parser.add_argument('--cache', type=Path,
                                help='Path to deduplication cache file')
    process_parser.add_argument('--stats', type=Path,
                                help='Path to write statistics JSON')
    process_parser.add_argument('--streaming', action='store_true',
                                help='Force streaming mode (for large files)')
    process_parser.add_argument('--no-streaming', action='store_true',
                                help='Disable streaming mode')
    process_parser.add_argument('--streaming-threshold', type=int, default=50,
                                help='File size threshold for auto-streaming (MB, default: 50)')

    # Version command
    version_parser = subparsers.add_parser('version', help='Show version')

    args = parser.parse_args()

    # Setup logging
    setup_logging(level=args.log_level, log_file=args.log_file)

    if args.command == 'process':
        # Determine streaming mode
        streaming_mode = None
        if args.streaming:
            streaming_mode = True
        elif args.no_streaming:
            streaming_mode = False

        # Process file
        try:
            process_file(
                input_path=args.input,
                output_path=args.output,
                granularity=args.granularity,
                classify=not args.no_classify,
                deduplicate=not args.no_dedup,
                cache_path=args.cache,
                stats_path=args.stats,
                streaming=streaming_mode,
                streaming_threshold_mb=args.streaming_threshold
            )
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            sys.exit(1)
        except KeyboardInterrupt:
            logger.warning("Processing interrupted by user")
            sys.exit(130)
        except Exception as e:
            logger.error(f"Error processing file: {e}", exc_info=True)
            sys.exit(1)

    elif args.command == 'version':
        from hydracontext import __version__
        print(f"HydraContext version {__version__}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
