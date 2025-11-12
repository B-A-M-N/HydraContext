"""
HydraContext - Universal JSON I/O Layer for LLM Pipelines

Enforces lossless, deterministic JSON format for all LLM interactions —
eliminating format drift, validation failures, and fidelity loss in
multi-model systems.

Core Features:
- Universal normalize() function (stdlib only, zero dependencies)
- Bidirectional normalization (input prompts + output responses)
- Multi-provider support (OpenAI, Anthropic, Ollama)
- Automatic JSON repair and validation
- Cross-model communication guarantees
"""

__version__ = "0.1.0"
__author__ = "HydraContext Contributors"

# ⭐ UNIVERSAL NORMALIZATION - The main entry point
from hydracontext.normalize import (
    normalize,
    normalize_input,
    normalize_output,
    normalize_auto,
)

# Core segmentation and deduplication
from hydracontext.core.segmenter import ContextSegmenter
from hydracontext.core.deduplicator import ContentDeduplicator
from hydracontext.core.classifier import ContentClassifier

# Prompt processing and normalization
from hydracontext.core.prompt_processor import normalize_prompt, split_prompt
from hydracontext.core.bidirectional import ContextNormalizer
from hydracontext.core.response_processor import ResponseNormalizer
from hydracontext.core.structured_parser import StructuredParser
from hydracontext.core.provider_parsers import UnifiedResponseParser

# API access
from hydracontext.api import HydraContextAPI

__all__ = [
    # ⭐ Universal normalization (primary interface)
    "normalize",
    "normalize_input",
    "normalize_output",
    "normalize_auto",
    # Core functionality
    "ContextSegmenter",
    "ContentDeduplicator",
    "ContentClassifier",
    # Prompt processing
    "normalize_prompt",
    "split_prompt",
    "ContextNormalizer",
    "ResponseNormalizer",
    "StructuredParser",
    "UnifiedResponseParser",
    # API
    "HydraContextAPI",
]
