# HydraContext

**Intelligent context chunking for LLM memory systems**

HydraContext is a robust Python library for text segmentation, classification, and deduplication designed specifically for building LLM memory layers. It intelligently segments text into meaningful chunks while distinguishing between code, prose, and structured data.

## Features

- **🔪 Smart Segmentation**
  - Sentence and paragraph boundary detection
  - Code block preservation (fenced and indented)
  - Markdown-aware parsing (headings, lists)
  - Abbreviation handling to prevent false breaks

- **🎯 Content Classification**
  - Heuristic-based code vs prose detection
  - Structured data recognition (JSON, XML, YAML)
  - Confidence scoring for classification
  - Mixed content detection

- **🔄 Intelligent Deduplication**
  - Hash-based duplicate detection (MD5, SHA256, BLAKE2b)
  - Persistent caching with JSONL format
  - Fuzzy matching with text normalization
  - Statistics tracking and reporting

- **📊 Statistics & Output**
  - Comprehensive processing statistics
  - JSONL output for structured data
  - CSV export for hash information
  - Human-readable summary reports

- **⚡ Zero Dependencies**
  - Uses only Python standard library
  - No external dependencies required
  - Python 3.8+ compatible

- **🚀 Streaming Mode**
  - Memory-efficient processing for large files (>50MB)
  - Automatic detection or manual control
  - Progress callbacks for long operations
  - Configurable chunk sizes

- **🔍 Input Validation**
  - File existence and readability checks
  - Encoding validation
  - Parameter validation
  - Helpful error messages

- **📝 Logging Support**
  - Configurable log levels (DEBUG, INFO, WARNING, ERROR)
  - File and console logging
  - Detailed operation tracking
  - Debug mode for troubleshooting

## Installation

### From Source

```bash
git clone https://github.com/yourusername/hydracontext.git
cd hydracontext
pip install -e .
```

### Using pip (when published)

```bash
pip install hydracontext
```

## Quick Start

### Command Line Usage

```bash
# Basic sentence segmentation
hydracontext process input.txt -o output.jsonl

# Paragraph segmentation with statistics
hydracontext process input.txt -o output.jsonl -g paragraph --stats stats.json

# With deduplication cache
hydracontext process input.txt -o output.jsonl --cache cache.jsonl

# Disable classification
hydracontext process input.txt -o output.jsonl --no-classify

# Enable debug logging
hydracontext process input.txt -o output.jsonl --log-level DEBUG

# Force streaming mode for large files
hydracontext process large_file.txt -o output.jsonl --streaming

# Save logs to file
hydracontext process input.txt -o output.jsonl --log-file processing.log

# Custom streaming threshold (100MB)
hydracontext process input.txt -o output.jsonl --streaming-threshold 100
```

### Python API

```python
from hydracontext import ContextSegmenter, ContentDeduplicator, ContentClassifier

# Initialize components
segmenter = ContextSegmenter()
classifier = ContentClassifier()
deduplicator = ContentDeduplicator()

# Segment text
text = "Your text here. It can contain code and prose."
segments = segmenter.segment_text(text, granularity='sentence')

# Classify content
for segment in segments:
    classification = classifier.classify(segment.text)
    is_duplicate = deduplicator.is_duplicate(segment.text)

    print(f"Text: {segment.text}")
    print(f"Type: {classification.content_type.value}")
    print(f"Duplicate: {is_duplicate}")
```

## Core Components

### 1. ContextSegmenter

Intelligent text segmentation with support for multiple granularities.

```python
from hydracontext.core.segmenter import ContextSegmenter, SegmentType

segmenter = ContextSegmenter(
    min_sentence_length=3,    # Minimum characters for valid sentence
    preserve_code=True         # Keep code blocks intact
)

# Segment into sentences
segments = segmenter.segment_sentences(text)

# Segment into paragraphs
paragraphs = segmenter.segment_paragraphs(text)

# Each segment has:
# - text: The actual content
# - type: SegmentType enum (SENTENCE, PARAGRAPH, CODE_BLOCK, etc.)
# - start_pos, end_pos: Position in original text
# - metadata: Optional metadata dict
```

**Features:**
- Preserves code blocks (fenced with ``` or indented)
- Handles common abbreviations (Dr., Mr., etc.)
- Detects markdown headings and lists
- Maintains original text positions

### 2. ContentClassifier

Heuristic-based classification for distinguishing code from prose.

```python
from hydracontext.core.classifier import ContentClassifier, ContentType

classifier = ContentClassifier(threshold=0.6)

result = classifier.classify(text)

print(f"Type: {result.content_type.value}")        # prose, code, structured_data, mixed
print(f"Confidence: {result.confidence:.2%}")       # 0.0 to 1.0
print(f"Indicators: {result.indicators}")           # Individual feature scores
print(f"Metadata: {result.metadata}")               # Additional info
```

**Classification Features:**
- Code syntax patterns (brackets, operators, keywords)
- Indentation analysis
- Prose patterns (articles, verbs, sentence structure)
- Punctuation analysis
- Line length patterns
- Structured data detection (JSON, XML, YAML)

### 3. ContentDeduplicator

Hash-based deduplication with optional persistent caching.

```python
from hydracontext.core.deduplicator import ContentDeduplicator
from pathlib import Path

deduplicator = ContentDeduplicator(
    algorithm='sha256',              # Hash algorithm: md5, sha256, blake2b
    normalize=True,                  # Normalize text before hashing
    cache_path=Path('cache.jsonl'),  # Optional persistent cache
    min_length=10                    # Minimum text length to process
)

# Check for duplicates
is_dup = deduplicator.is_duplicate(text, record=True)

# Deduplicate a list
unique_texts = deduplicator.deduplicate_list(texts)

# Get statistics
stats = deduplicator.get_statistics()
print(f"Unique: {stats['unique_content']}")
print(f"Duplicates: {stats['duplicates_found']}")
print(f"Dedup ratio: {stats['dedup_ratio']:.1%}")

# Save cache for reuse
deduplicator.save_cache(Path('cache.jsonl'))
```

**Deduplication Features:**
- Multiple hash algorithms
- Text normalization for fuzzy matching
- Persistent JSONL cache
- Statistics tracking
- Export to CSV or JSONL

### 4. Streaming Mode for Large Files

Process large files efficiently without loading them entirely into memory.

```python
from pathlib import Path
from hydracontext.utils.streaming import StreamingProcessor

# Create streaming processor
processor = StreamingProcessor(
    chunk_size=1024 * 1024,  # 1MB chunks
    granularity='sentence',
    classify=True,
    deduplicate=True,
    cache_path=Path('cache.jsonl')
)

# Process large file
def progress_callback(progress):
    print(f"Progress: {progress['percent']:.1f}%")

stats = processor.process_file_streaming(
    input_path=Path('large_file.txt'),
    output_path=Path('output.jsonl'),
    progress_callback=progress_callback
)

print(f"Processed {stats['segments_processed']} segments")
print(f"Written {stats['segments_written']} unique segments")
```

**Streaming Features:**
- Automatic mode selection based on file size
- Configurable chunk sizes
- Progress tracking callbacks
- Memory-efficient processing
- Same deduplication and classification features

### 5. Input Validation

Validate files and parameters before processing.

```python
from pathlib import Path
from hydracontext.utils.validation import (
    validate_file_readable,
    validate_file_writable,
    validate_text_encoding,
    validate_granularity,
    ValidationError,
)

try:
    # Validate input file
    validate_file_readable(Path('input.txt'))
    validate_text_encoding(Path('input.txt'), encoding='utf-8')

    # Validate output path
    validate_file_writable(Path('output.jsonl'))

    # Validate parameters
    validate_granularity('sentence')

    # Process file...

except ValidationError as e:
    print(f"Validation failed: {e}")
```

**Validation Features:**
- File existence and readability checks
- Encoding validation
- Parameter validation (granularity, hash algorithms, thresholds)
- File size limits
- Clear error messages

### 6. Logging

Configure logging for detailed operation tracking.

```python
from pathlib import Path
from hydracontext.utils.logging import setup_logging, get_logger

# Setup logging
setup_logging(
    level='DEBUG',  # DEBUG, INFO, WARNING, ERROR
    log_file=Path('hydracontext.log')
)

# Get logger for your module
logger = get_logger(__name__)

logger.info("Starting processing")
logger.debug("Detailed debug information")
logger.warning("Warning message")
logger.error("Error occurred")
```

**Logging Features:**
- Multiple log levels
- Console and file logging
- Structured log messages
- Per-module loggers
- Integration with CLI

## Integration with Hydra Memory Layer

HydraContext is designed to integrate seamlessly with Hydra's memory system.

### Processing Pipeline

```python
from pathlib import Path
from hydracontext.cli.main import process_text
from hydracontext.utils.output import StatsCollector

# Initialize stats collector
stats = StatsCollector()
stats.start_processing()

# Process document
result = process_text(
    input_text=document_text,
    granularity='sentence',
    classify=True,
    deduplicate=True,
    cache_path=Path('hydra_cache.jsonl'),
    output_path=Path('hydra_chunks.jsonl'),
    stats_collector=stats
)

stats.end_processing()

# Get processing statistics
processing_stats = stats.get_stats()
```

### Output Format

HydraContext outputs JSONL (JSON Lines) format, perfect for streaming and database ingestion:

```json
{"text": "This is a sentence.", "type": "sentence", "start_pos": 0, "end_pos": 19, "length": 19, "classification": {"content_type": "prose", "confidence": 0.95}}
{"text": "def hello():\n    print('Hi')", "type": "code_block", "start_pos": 20, "end_pos": 48, "length": 28, "classification": {"content_type": "code", "confidence": 0.92}}
```

### Plugging into Hydra

```python
# Example integration with Hydra's memory system
import json
from pathlib import Path

def ingest_into_hydra(jsonl_path: Path):
    """Ingest HydraContext chunks into Hydra memory."""
    with open(jsonl_path) as f:
        for line in f:
            chunk = json.loads(line)

            # Create memory entry
            memory_entry = {
                'content': chunk['text'],
                'content_type': chunk['classification']['content_type'],
                'confidence': chunk['classification']['confidence'],
                'chunk_type': chunk['type'],
                'position': chunk['start_pos'],
                'length': chunk['length'],
            }

            # Store in Hydra's memory layer
            hydra.memory.store(memory_entry)

# Process and ingest
process_file(
    input_path=Path('document.txt'),
    output_path=Path('chunks.jsonl'),
    classify=True,
    deduplicate=True,
    cache_path=Path('hydra.cache')
)

ingest_into_hydra(Path('chunks.jsonl'))
```

## Advanced Usage

### Custom Segmentation

```python
from hydracontext.core.segmenter import ContextSegmenter

segmenter = ContextSegmenter(
    min_sentence_length=5,
    preserve_code=True
)

# Get detailed segment information
segments = segmenter.segment_text(text, granularity='sentence')

for seg in segments:
    print(f"Type: {seg.type.value}")
    print(f"Position: {seg.start_pos}-{seg.end_pos}")
    print(f"Text: {seg.text}")
    print(f"Metadata: {seg.metadata}")
    print()
```

### Fine-Tuned Classification

```python
from hydracontext.core.classifier import ContentClassifier

# Lower threshold for more permissive classification
classifier = ContentClassifier(threshold=0.5)

result = classifier.classify(text)

# Access detailed indicators
print("Feature scores:")
for feature, score in result.indicators.items():
    print(f"  {feature}: {score:.2f}")

# Get metadata
print(f"Code score: {result.metadata['code_score']}")
print(f"Prose score: {result.metadata['prose_score']}")
```

### Cache Management

```python
from hydracontext.core.deduplicator import ContentDeduplicator
from pathlib import Path

dedup = ContentDeduplicator(cache_path=Path('cache.jsonl'))

# Process documents
for doc in documents:
    dedup.is_duplicate(doc, record=True)

# Save cache for next run
dedup.save_cache()

# Export hash information
dedup.export_hashes(Path('hashes.csv'), format='csv')

# Clear cache when needed
dedup.clear_cache()
```

## Examples

See the `examples/` directory for complete examples:

```bash
# Run the example script
python examples/sample_usage.py
```

This demonstrates:
- Basic segmentation
- Content classification
- Deduplication
- Full processing pipeline

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=hydracontext --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_classifier.py -v

# Run with debugging
pytest tests/ -v -s --log-cli-level=DEBUG
```

### Pre-commit Hooks

The project uses pre-commit hooks for code quality:

```bash
# Install pre-commit
pip install pre-commit

# Set up git hooks
pre-commit install

# Run hooks manually on all files
pre-commit run --all-files

# Run specific hook
pre-commit run black --all-files
```

**Hooks included:**
- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **bandit**: Security scanning
- **File checks**: Trailing whitespace, file size, etc.

### Continuous Integration

GitHub Actions automatically runs tests on:
- Python 3.8, 3.9, 3.10, 3.11, 3.12
- All pull requests
- Pushes to main/develop branches

**CI Pipeline includes:**
- Unit tests with coverage
- Linting and formatting checks
- Type checking
- Security scanning
- Package building
- Integration tests

View the workflow: `.github/workflows/ci.yml`

## Configuration

HydraContext can be configured through:

1. **Command-line arguments** (see `hydracontext --help`)
2. **Python API parameters** (see component docstrings)
3. **Environment variables** (future feature)

## Performance

HydraContext is designed for efficiency:

- **Zero Dependencies**: No external libraries to install
- **Streaming**: Process large files without loading everything into memory
- **Caching**: Persistent hash cache for deduplication across runs
- **Fast Hashing**: Multiple algorithm options (MD5 for speed, SHA256 for security)

Typical performance on a modern laptop:
- **Segmentation**: ~100K words/second
- **Classification**: ~50K words/second
- **Deduplication**: ~200K words/second (with cache)

## Use Cases

- **LLM Memory Systems**: Chunk documents for vector databases
- **Data Preprocessing**: Clean and deduplicate text datasets
- **Content Analysis**: Classify and categorize mixed content
- **Document Processing**: Extract structured information from documents
- **Code Documentation**: Separate code from prose in technical docs

## Roadmap

Future enhancements:
- [ ] Neural classification option (using transformers)
- [ ] Language detection
- [ ] Multi-file batch processing
- [ ] Streaming API for large files
- [ ] Plugin system for custom segmenters
- [ ] Web API server mode
- [ ] Integration with popular vector databases

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Built for the **Hydra** memory system, designed to provide intelligent context chunking for LLM-based applications.

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/hydracontext/issues)
- **Documentation**: [Full Documentation](https://hydracontext.readthedocs.io)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/hydracontext/discussions)

---

Made with ❤️ for the LLM community
