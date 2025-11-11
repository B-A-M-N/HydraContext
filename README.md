# HydraContext

**Intelligent LLM context processing and normalization**

> 💰 **Cost Optimization Framework** - Save 30-60% on LLM token costs through intelligent deduplication. Not a storage compression tool (adds 60-90% overhead). Designed for token cost reduction at scale.

HydraContext is a comprehensive Python library for LLM integration, providing bidirectional normalization, prompt/response processing, and intelligent text segmentation. It offers a unified interface for working with multiple LLM providers (OpenAI, Anthropic, Ollama) while handling context chunking, classification, and deduplication for memory layers and RAG pipelines.

## 💰 Value Proposition: Save Token Costs, Not Storage

> **"Pay $1 in storage to save $100 in LLM API costs"**

HydraContext is designed to **optimize token costs**, not storage space:

| Metric | Impact | Example (100K prompts, 40% duplication) |
|--------|--------|----------------------------------------|
| **LLM Token Costs** | ✅ **-30-60% savings** | Save **$72** ($180 → $108) |
| **Embedding Costs** | ✅ **-25-40% savings** | Save **$0.50** per million docs |
| **Storage Space** | ❌ **+60-90% overhead** | Cost **$0.10** (negligible) |
| **Processing Speed** | ✅ **Skip duplicates** | Process only unique content |
| **Context Quality** | ✅ **Better retrieval** | Classification improves search |

### When to Use HydraContext:

✅ **Working with LLM APIs** - Every duplicate prompt costs money
✅ **Building vector databases** - Don't embed the same content twice
✅ **Processing at scale** (>10K items) - ROI increases with volume
✅ **Content has 25%+ duplication** - Chat logs, FAQs, multi-doc corpora
✅ **Need metadata for retrieval** - Classification improves search quality

❌ **Pure storage optimization** - Use gzip/zstd compression instead
❌ **Small projects** (<1K items) - Token savings too small to matter
❌ **Unique content** (<20% duplication) - Just adds metadata overhead

**See [SPACE_EFFICIENCY.md](SPACE_EFFICIENCY.md) for detailed cost analysis.**

## Features

### LLM Integration & Normalization

- **🔄 Bidirectional Normalization**
  - Normalize prompts for different LLM providers
  - Parse and unify responses from OpenAI, Anthropic, Ollama
  - Provider-specific optimizations (streaming, formatting)
  - Consistent interface across all providers

- **💬 Prompt Processing**
  - Intelligent prompt classification (code, conversation, instruction, example, system)
  - Smart prompt segmentation with context overlap
  - Token estimation and length management
  - Automatic deduplication with hash-based tracking

- **📤 Response Processing**
  - Multi-provider response parsing and normalization
  - Streaming response handling
  - Artifact removal and cleanup
  - Response comparison and analysis

- **🏗️ Structured Parsing**
  - Lossless text ↔ JSON conversion with 17 content types
  - 5 fidelity levels for precision control
  - Code block, thinking block, and inline formatting detection
  - Complete reconstruction capability

- **🌐 Multi-Provider Support**
  - Unified response parser for OpenAI, Anthropic, Ollama
  - Auto-detection of provider response formats
  - Token count normalization across providers
  - Provider metadata preservation

### Text Processing & Analysis

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
git clone https://github.com/BenevolentJoker-JohnL/HydraContext.git
cd HydraContext
pip install -e .
```

### Using pip (when published)

```bash
pip install hydracontext
```

## Quick Start

### Bidirectional Normalization (LLM Integration)

```python
from hydracontext import ContextNormalizer

# Initialize normalizer
normalizer = ContextNormalizer()

# Normalize input prompt for any LLM provider
prompt = "Explain quantum computing"
normalized_input = normalizer.normalize_input(prompt)

# Parse and normalize LLM response (auto-detects provider format)
openai_response = {"choices": [{"message": {"content": "Quantum computing..."}}]}
normalized_output = normalizer.normalize_output(openai_response)

# Works with OpenAI, Anthropic, Ollama - unified interface!
print(normalized_output['content'])  # Clean, normalized text
```

### Prompt Processing

```python
from hydracontext.core.prompt_processor import (
    normalize_prompt,
    detect_prompt_type,
    split_prompt,
    PromptProcessor
)

# Normalize messy prompts
clean = normalize_prompt("   What  is   AI?   \n\n\n")  # "What is AI?"

# Classify prompt type
prompt_type = detect_prompt_type("```python\ndef foo(): pass```")  # "code"

# Process with full pipeline
processor = PromptProcessor(max_chars=2048)
result = processor.process("Explain transformers in detail...")
print(result[0]['type'])           # "instruction"
print(result[0]['token_estimate']) # Estimated token count
```

### Response Parsing & Structured Parsing

```python
from hydracontext import UnifiedResponseParser, StructuredParser

# Parse responses from any provider
parser = UnifiedResponseParser()
response = parser.parse(raw_api_response)  # Auto-detects provider
print(response['content'])
print(response['tokens'])

# Convert text to structured JSON (lossless)
structured_parser = StructuredParser()
parsed = structured_parser.parse(
    "# Heading\n\nParagraph\n\n```python\ncode```",
    fidelity='high'
)
# Returns structured JSON with 17 content types
# Can reconstruct original text perfectly!
```

### Text Segmentation & Analysis

```python
from hydracontext import ContextSegmenter, ContentClassifier, ContentDeduplicator

# Initialize components
segmenter = ContextSegmenter()
classifier = ContentClassifier()
deduplicator = ContentDeduplicator()

# Segment text intelligently
text = "Your text here. It can contain code and prose."
segments = segmenter.segment_text(text, granularity='sentence')

# Classify and deduplicate
for segment in segments:
    classification = classifier.classify(segment.text)
    is_duplicate = deduplicator.is_duplicate(segment.text)

    print(f"Type: {classification.content_type.value}")
    print(f"Confidence: {classification.confidence:.1%}")
    print(f"Duplicate: {is_duplicate}")
```

### Command Line Usage

```bash
# Text segmentation and processing
hydracontext process input.txt -o output.jsonl

# With classification and deduplication
hydracontext process input.txt -o output.jsonl -g paragraph --cache cache.jsonl

# Streaming mode for large files
hydracontext process large_file.txt -o output.jsonl --streaming

# Enable debug logging
hydracontext process input.txt -o output.jsonl --log-level DEBUG
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

## Performance & Cost Efficiency

### Cost Savings (The Primary Value)

**Token Cost Reduction:**
- **30-60% savings** on LLM API costs through deduplication
- **25-40% savings** on embedding costs (don't embed duplicates)
- **Faster processing** - skip duplicate content entirely

**Real Example (100K prompts with 40% duplication):**
```
Without HydraContext: $180 in LLM costs
With HydraContext:    $108 in LLM costs
Savings:              $72 (40% reduction)

Storage overhead:     +$0.10
Net benefit:          $71.90
```

**Break-even point:** ~1,000 prompts with 25% duplication

### Processing Performance

Typical performance on a modern laptop:
- **Segmentation**: ~100K words/second
- **Classification**: ~50K words/second
- **Deduplication**: ~200K words/second (with cache)

**Design Efficiency:**
- **Zero Dependencies**: No external libraries to install
- **Streaming**: Process large files without loading everything into memory
- **Caching**: Persistent hash cache for deduplication across runs
- **Fast Hashing**: Multiple algorithm options (MD5 for speed, SHA256 for security)

### Important: Storage vs. Cost Trade-off

⚠️ **HydraContext increases storage by 60-90%** due to metadata, but saves 30-60% in token costs.

This trade-off makes sense because:
- **Storage costs:** ~$0.001 per GB (negligible)
- **Token costs:** ~$0.03-0.06 per 1K tokens (significant)
- **ROI:** Saving $100 in tokens costs $1 in storage

For detailed cost analysis, see [SPACE_EFFICIENCY.md](SPACE_EFFICIENCY.md)

## Use Cases

### LLM Integration
- **Multi-Provider Applications**: Build apps that work seamlessly with OpenAI, Anthropic, and Ollama
- **Response Normalization**: Parse and unify responses from different LLM APIs
- **Prompt Engineering**: Classify, normalize, and optimize prompts before sending to LLMs
- **Streaming LLM Applications**: Handle streaming responses with consistent formatting
- **LLM Comparison Tools**: Compare outputs from different providers with normalized data

### Text Processing & Memory
- **LLM Memory Systems**: Chunk documents for vector databases and RAG pipelines
- **Data Preprocessing**: Clean, deduplicate, and structure text datasets
- **Content Analysis**: Classify and categorize mixed content (code, prose, structured data)
- **Document Processing**: Extract and segment information from documents
- **Code Documentation**: Separate code from prose in technical documentation
- **Knowledge Base Building**: Structure unstructured text for searchable knowledge systems

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

- **Issues**: [GitHub Issues](https://github.com/BenevolentJoker-JohnL/HydraContext/issues)
- **Documentation**: [Full Documentation](https://hydracontext.readthedocs.io)
- **Discussions**: [GitHub Discussions](https://github.com/BenevolentJoker-JohnL/HydraContext/discussions)

---

Made with ❤️ for the LLM community
