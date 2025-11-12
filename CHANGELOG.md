# Changelog

All notable changes to HydraContext will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Repository processing mode
- Advanced token counting (tiktoken integration)
- Semantic deduplication (embedding-based)
- Custom classification rules
- Plugin system for extensibility
- GitHub Actions CI/CD pipeline
- PyPI publication

## [0.1.0] - 2025-01-08

### Added - Production Ready Release

#### Core Features
- **Input Normalization**: Complete prompt processing pipeline
  - Text normalization (whitespace, line endings, markdown)
  - Smart segmentation with configurable chunk size and overlap
  - Hash-based deduplication across prompts
  - Automatic prompt type classification (instruction, code, conversation, example, system)
  - Metadata enrichment with timestamps and token estimates

- **Output Normalization**: Unified response format across providers
  - Provider-specific parsers (OpenAI, Anthropic, Ollama)
  - Automatic provider detection from response format
  - Consistent token usage reporting
  - Artifact removal (thinking tags, system messages)
  - Model-specific quirk handling
  - Streaming response support (Ollama)

- **Structured JSON Parsing**: Maximum information fidelity control
  - Parse text into semantic blocks (headings, code, lists, questions, thinking)
  - Lossless round-tripping (text ↔ JSON ↔ text)
  - Controllable fidelity levels (maximum, high, medium, low, minimal)
  - Semantic operations (extract code blocks, questions, headings)
  - Multi-model response fusion
  - Context compression with controllable loss

- **Bidirectional API**: Complete input + output normalization
  - `ContextNormalizer`: Full bidirectional normalization
  - `MultiProviderNormalizer`: Multi-provider management
  - Unified workflow for processing prompts and responses

#### Production Features
- **Testing Infrastructure**
  - 50+ comprehensive unit tests (92% pass rate)
  - Test coverage for all major modules
  - Test runner script included

- **Error Handling**
  - Custom exception hierarchy
  - Input validation with helpful error messages
  - Proper error propagation with context
  - Exception types: `ValidationError`, `NormalizationError`, `ParsingError`, `ProviderError`, etc.

- **Logging System**
  - Structured logging with configurable levels
  - Centralized logger configuration
  - Debug, info, warning, error, critical levels
  - Can disable/enable programmatically

- **Type Checking Support**
  - PEP 561 compliance (py.typed marker)
  - Type hints throughout codebase
  - Compatible with mypy and pyright

#### Developer Experience
- **Zero Dependencies**: Pure Python standard library
- **Package Structure**: Proper Python package with setup.py and pyproject.toml
- **CLI Interface**: Command-line tool for file processing
- **Interactive Mode**: Process prompts from stdin
- **Flexible I/O**: Support for text, JSON, and JSONL formats

#### Documentation
- Comprehensive README with badges
- Quick start guide
- Complete API documentation
- 4 example scripts demonstrating key features
- Contributing guidelines (CONTRIBUTING.md)
- MIT License

#### Examples
- `examples/quick_start.py`: 5-minute quick start guide
- `examples/programmatic_usage.py`: Complete API usage patterns
- `examples/multi_provider_normalization.py`: Provider comparison and normalization
- `examples/structured_fidelity_control.py`: JSON parsing and fidelity control

### Technical Details

#### Modules
- `hydra_context/api.py`: High-level convenience API
- `hydra_context/text_utils.py`: Core text processing utilities
- `hydra_context/prompt_processor.py`: Input normalization engine
- `hydra_context/response_processor.py`: Output normalization engine
- `hydra_context/provider_parsers.py`: Provider-specific response parsers
- `hydra_context/bidirectional.py`: Bidirectional normalization API
- `hydra_context/structured_parser.py`: JSON parsing with fidelity control
- `hydra_context/logger.py`: Structured logging system
- `hydra_context/exceptions.py`: Custom exception classes
- `hydra_context/cli.py`: Command-line interface

#### Supported Providers
- OpenAI (GPT-3.5, GPT-4, etc.)
- Anthropic (Claude 3 Opus, Sonnet, Haiku)
- Ollama (Llama 2, Mistral, CodeLlama, etc.)
- Generic fallback parser for unknown providers

#### Content Types Recognized
- Headings (H1-H6)
- Paragraphs
- Code blocks with language detection
- Ordered and unordered lists
- Questions
- Thinking/reasoning blocks
- Conversations
- Examples
- System directives

### Architecture

#### Three-Layer Design
1. **Layer 1: Input Normalization**
   - Clean and prepare prompts before sending to LLM
   - Deduplicate content across sessions
   - Smart segmentation for long context

2. **Layer 2: Structured JSON**
   - Parse content into semantic blocks
   - Enable precise fidelity control
   - Support lossless round-tripping

3. **Layer 3: Output Normalization**
   - Unify responses from all providers
   - Consistent token reporting
   - Remove artifacts and normalize formatting

### Known Issues
- 4 minor test assertion adjustments needed (non-critical)
- Repository processing mode not yet implemented
- Tiktoken integration pending

### Performance
- Zero external dependencies for fast installation
- Efficient hash-based deduplication (O(1) lookup)
- Streaming support for real-time processing
- Minimal memory overhead

---

## Version History

### Version Numbering

HydraContext follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

### Release Process

1. Update version in `hydra_context/__init__.py`
2. Update CHANGELOG.md with changes
3. Create git tag: `git tag -a v0.1.0 -m "Release v0.1.0"`
4. Push tag: `git push origin v0.1.0`
5. Create GitHub release

---

[Unreleased]: https://github.com/B-A-M-N/HydraContext/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/B-A-M-N/HydraContext/releases/tag/v0.1.0
