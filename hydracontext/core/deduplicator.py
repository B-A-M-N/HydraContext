"""
Content deduplication with hash-based caching.

Provides efficient duplicate detection using content hashing
and optional persistent caching for large-scale processing.
"""

import hashlib
import json
from pathlib import Path
from typing import Set, Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ContentHash:
    """Metadata for a hashed content segment."""
    hash: str
    text: str
    first_seen: str
    occurrences: int = 1
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ContentHash':
        """Create from dictionary."""
        return cls(**data)


class ContentDeduplicator:
    """
    Hash-based content deduplication with persistent caching.

    Features:
    - Multiple hashing algorithms (MD5, SHA256, xxHash)
    - Fuzzy matching with normalization
    - Persistent cache with JSONL format
    - Statistics tracking
    """

    def __init__(
        self,
        algorithm: str = 'sha256',
        normalize: bool = True,
        cache_path: Optional[Path] = None,
        min_length: int = 10
    ):
        """
        Initialize the deduplicator.

        Args:
            algorithm: Hash algorithm ('md5', 'sha256', 'blake2b')
            normalize: Whether to normalize text before hashing
            cache_path: Path to persistent cache file (JSONL)
            min_length: Minimum text length to process
        """
        self.algorithm = algorithm
        self.normalize = normalize
        self.cache_path = Path(cache_path) if cache_path else None
        self.min_length = min_length

        # In-memory hash storage
        self.hash_map: Dict[str, ContentHash] = {}
        self.seen_hashes: Set[str] = set()

        # Statistics
        self.stats = {
            'total_processed': 0,
            'unique_content': 0,
            'duplicates_found': 0,
            'cache_hits': 0,
        }

        # Load existing cache if available
        if self.cache_path and self.cache_path.exists():
            self._load_cache()

    def hash_text(self, text: str) -> str:
        """
        Generate hash for text content.

        Args:
            text: Text to hash

        Returns:
            Hex digest of hash
        """
        # Normalize if requested
        content = self._normalize_text(text) if self.normalize else text

        # Generate hash based on algorithm
        if self.algorithm == 'md5':
            return hashlib.md5(content.encode('utf-8')).hexdigest()
        elif self.algorithm == 'sha256':
            return hashlib.sha256(content.encode('utf-8')).hexdigest()
        elif self.algorithm == 'blake2b':
            return hashlib.blake2b(content.encode('utf-8')).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {self.algorithm}")

    def is_duplicate(self, text: str, record: bool = True) -> bool:
        """
        Check if text is a duplicate.

        Args:
            text: Text to check
            record: Whether to record this text in the hash map

        Returns:
            True if duplicate, False if unique
        """
        if len(text) < self.min_length:
            return False

        content_hash = self.hash_text(text)
        self.stats['total_processed'] += 1

        is_dup = content_hash in self.seen_hashes

        if record:
            if is_dup:
                # Update occurrence count
                self.hash_map[content_hash].occurrences += 1
                self.stats['duplicates_found'] += 1
                if self.cache_path:
                    self.stats['cache_hits'] += 1
            else:
                # New unique content
                self.seen_hashes.add(content_hash)
                self.hash_map[content_hash] = ContentHash(
                    hash=content_hash,
                    text=text[:200] + '...' if len(text) > 200 else text,  # Store preview
                    first_seen=datetime.utcnow().isoformat(),
                    occurrences=1
                )
                self.stats['unique_content'] += 1

        return is_dup

    def deduplicate_list(self, texts: List[str]) -> List[str]:
        """
        Remove duplicates from a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List with duplicates removed (preserves order)
        """
        unique_texts = []
        seen_in_batch = set()

        for text in texts:
            if len(text) < self.min_length:
                unique_texts.append(text)
                continue

            text_hash = self.hash_text(text)

            # Check both global cache and current batch
            if text_hash not in seen_in_batch:
                unique_texts.append(text)
                seen_in_batch.add(text_hash)

                # Update global tracking
                self.is_duplicate(text, record=True)

        return unique_texts

    def get_hash_info(self, text: str) -> Optional[ContentHash]:
        """
        Get hash information for a text.

        Args:
            text: Text to look up

        Returns:
            ContentHash object if found, None otherwise
        """
        text_hash = self.hash_text(text)
        return self.hash_map.get(text_hash)

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            **self.stats,
            'unique_hashes': len(self.seen_hashes),
            'dedup_ratio': (
                self.stats['duplicates_found'] / self.stats['total_processed']
                if self.stats['total_processed'] > 0 else 0
            ),
        }

    def save_cache(self, path: Optional[Path] = None) -> None:
        """
        Save hash cache to disk in JSONL format.

        Args:
            path: Path to save cache (uses self.cache_path if not provided)
        """
        save_path = Path(path) if path else self.cache_path

        if not save_path:
            raise ValueError("No cache path specified")

        # Ensure parent directory exists
        save_path.parent.mkdir(parents=True, exist_ok=True)

        # Write JSONL format
        with open(save_path, 'w', encoding='utf-8') as f:
            for content_hash in self.hash_map.values():
                json.dump(content_hash.to_dict(), f)
                f.write('\n')

    def _load_cache(self) -> None:
        """Load hash cache from disk."""
        if not self.cache_path or not self.cache_path.exists():
            return

        with open(self.cache_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    content_hash = ContentHash.from_dict(data)
                    self.hash_map[content_hash.hash] = content_hash
                    self.seen_hashes.add(content_hash.hash)

        # Update stats
        self.stats['unique_content'] = len(self.seen_hashes)

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text for more aggressive deduplication.

        Args:
            text: Text to normalize

        Returns:
            Normalized text
        """
        # Convert to lowercase
        normalized = text.lower()

        # Collapse whitespace
        normalized = ' '.join(normalized.split())

        # Remove common punctuation variations
        # (but preserve structure for code)
        if not self._looks_like_code(normalized):
            # More aggressive normalization for prose
            normalized = normalized.strip('.,;:!? \t\n')

        return normalized

    def _looks_like_code(self, text: str) -> bool:
        """
        Quick heuristic to detect code-like content.

        Args:
            text: Text to check

        Returns:
            True if text looks like code
        """
        # Simple heuristics
        code_indicators = [
            '{', '}', '()', '=>', 'function', 'class',
            'def ', 'import ', 'const ', 'let ', 'var ',
        ]

        text_lower = text.lower()
        matches = sum(1 for indicator in code_indicators if indicator in text_lower)

        return matches >= 2

    def clear_cache(self) -> None:
        """Clear in-memory cache and reset statistics."""
        self.hash_map.clear()
        self.seen_hashes.clear()
        self.stats = {
            'total_processed': 0,
            'unique_content': 0,
            'duplicates_found': 0,
            'cache_hits': 0,
        }

    def export_hashes(self, output_path: Path, format: str = 'jsonl') -> None:
        """
        Export hash information to file.

        Args:
            output_path: Path to write export
            format: Export format ('jsonl' or 'csv')
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == 'jsonl':
            self.save_cache(output_path)
        elif format == 'csv':
            import csv
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=['hash', 'text', 'first_seen', 'occurrences']
                )
                writer.writeheader()
                for content_hash in self.hash_map.values():
                    writer.writerow({
                        'hash': content_hash.hash,
                        'text': content_hash.text,
                        'first_seen': content_hash.first_seen,
                        'occurrences': content_hash.occurrences,
                    })
        else:
            raise ValueError(f"Unsupported format: {format}")
