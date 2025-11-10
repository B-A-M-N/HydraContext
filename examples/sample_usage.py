"""
Example usage of HydraContext.

Demonstrates core functionality: segmentation, classification, and deduplication.
"""

from pathlib import Path
from hydracontext import ContextSegmenter, ContentDeduplicator, ContentClassifier


def example_basic_segmentation():
    """Basic text segmentation example."""
    print("=" * 60)
    print("Example 1: Basic Segmentation")
    print("=" * 60 + "\n")

    text = """
    HydraContext is a powerful library for text processing.
    It segments text intelligently, handling both code and prose.

    ```python
    def hello():
        print("Hello, World!")
    ```

    The library also supports deduplication and classification.
    """

    segmenter = ContextSegmenter()
    segments = segmenter.segment_text(text, granularity='sentence')

    print(f"Found {len(segments)} segments:\n")
    for i, seg in enumerate(segments, 1):
        print(f"{i}. [{seg.type.value}] {seg.text[:60]}...")


def example_classification():
    """Content classification example."""
    print("\n" + "=" * 60)
    print("Example 2: Content Classification")
    print("=" * 60 + "\n")

    samples = [
        "This is a simple sentence in prose format.",
        "def calculate_sum(a, b):\n    return a + b",
        '{"name": "John", "age": 30}',
    ]

    classifier = ContentClassifier()

    for sample in samples:
        result = classifier.classify(sample)
        print(f"Text: {sample[:50]}")
        print(f"Type: {result.content_type.value}")
        print(f"Confidence: {result.confidence:.2%}\n")


def example_deduplication():
    """Deduplication example."""
    print("=" * 60)
    print("Example 3: Deduplication")
    print("=" * 60 + "\n")

    texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Python is a great programming language.",
        "The quick brown fox jumps over the lazy dog.",  # Duplicate
        "Machine learning is fascinating.",
        "Python is a great programming language.",  # Duplicate
    ]

    deduplicator = ContentDeduplicator()

    print("Processing texts:")
    for i, text in enumerate(texts, 1):
        is_dup = deduplicator.is_duplicate(text)
        status = "DUPLICATE" if is_dup else "UNIQUE"
        print(f"{i}. [{status}] {text}")

    print(f"\nStatistics:")
    stats = deduplicator.get_statistics()
    print(f"  Total processed: {stats['total_processed']}")
    print(f"  Unique content: {stats['unique_content']}")
    print(f"  Duplicates: {stats['duplicates_found']}")
    print(f"  Dedup ratio: {stats['dedup_ratio']:.1%}")


def example_full_pipeline():
    """Full processing pipeline example."""
    print("\n" + "=" * 60)
    print("Example 4: Full Pipeline")
    print("=" * 60 + "\n")

    text = """
    Natural language processing is a fascinating field.
    It combines linguistics and computer science.

    ```python
    def tokenize(text):
        return text.split()
    ```

    Natural language processing is a fascinating field.
    Machine learning powers modern NLP systems.
    """

    # Initialize components
    segmenter = ContextSegmenter()
    classifier = ContentClassifier()
    deduplicator = ContentDeduplicator()

    # Segment
    segments = segmenter.segment_text(text, granularity='sentence')
    print(f"Segmented into {len(segments)} segments\n")

    # Process each segment
    unique_count = 0
    for seg in segments:
        # Check for duplicate
        is_dup = deduplicator.is_duplicate(seg.text)

        if not is_dup:
            unique_count += 1

            # Classify
            classification = classifier.classify(seg.text)

            print(f"Segment #{unique_count}:")
            print(f"  Type: {seg.type.value}")
            print(f"  Classification: {classification.content_type.value} "
                  f"({classification.confidence:.1%})")
            print(f"  Text: {seg.text[:60]}...")
            print()

    print(f"Unique segments: {unique_count}/{len(segments)}")


if __name__ == "__main__":
    example_basic_segmentation()
    example_classification()
    example_deduplication()
    example_full_pipeline()
