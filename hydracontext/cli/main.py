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
    """
    if stats_collector is None:
        stats_collector = StatsCollector()

    # Initialize components
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
    stats_path: Optional[Path] = None
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
    """
    stats_collector = StatsCollector()
    stats_collector.start_processing()

    # Read input
    print(f"Reading: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        input_text = f.read()

    # Process
    print(f"Processing with granularity: {granularity}")
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
        stats = stats_collector.get_stats()
        OutputWriter.write_stats(stats, stats_path, format='json')
        print(f"Statistics written to: {stats_path}")

    print(f"Output written to: {output_path}")
    print(f"Processed {result['total_segments']} segments, {result['unique_segments']} unique")


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
        """
    )

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

    # Version command
    version_parser = subparsers.add_parser('version', help='Show version')

    args = parser.parse_args()

    if args.command == 'process':
        # Validate input
        if not args.input.exists():
            print(f"Error: Input file not found: {args.input}", file=sys.stderr)
            sys.exit(1)

        # Process file
        try:
            process_file(
                input_path=args.input,
                output_path=args.output,
                granularity=args.granularity,
                classify=not args.no_classify,
                deduplicate=not args.no_dedup,
                cache_path=args.cache,
                stats_path=args.stats
            )
        except Exception as e:
            print(f"Error processing file: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == 'version':
        from hydracontext import __version__
        print(f"HydraContext version {__version__}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
