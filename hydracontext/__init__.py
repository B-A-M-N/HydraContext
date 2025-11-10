"""
HydraContext - Intelligent context chunking for LLM memory systems.

A robust text segmentation and deduplication library designed for Hydra's memory layer.
"""

__version__ = "0.1.0"
__author__ = "HydraContext Contributors"

from hydracontext.core.segmenter import ContextSegmenter
from hydracontext.core.deduplicator import ContentDeduplicator
from hydracontext.core.classifier import ContentClassifier

__all__ = [
    "ContextSegmenter",
    "ContentDeduplicator",
    "ContentClassifier",
]
