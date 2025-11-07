"""
Text segmentation for HydraContext.

Handles sentence and paragraph boundary detection with support for
code blocks, markdown, and various text formats.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SegmentType(Enum):
    """Types of text segments."""
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    CODE_BLOCK = "code_block"
    LIST_ITEM = "list_item"
    HEADING = "heading"


@dataclass
class Segment:
    """A single text segment with metadata."""
    text: str
    type: SegmentType
    start_pos: int
    end_pos: int
    metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContextSegmenter:
    """
    Intelligent text segmentation with support for prose and code.

    Features:
    - Sentence boundary detection with abbreviation handling
    - Paragraph splitting with markdown awareness
    - Code block preservation
    - List and heading detection
    """

    # Common abbreviations that don't end sentences
    ABBREVIATIONS = {
        'dr', 'mr', 'mrs', 'ms', 'prof', 'sr', 'jr',
        'vs', 'etc', 'e.g', 'i.e', 'cf', 'al',
        'vol', 'fig', 'approx', 'appt', 'dept',
    }

    # Sentence-ending punctuation
    SENTENCE_ENDERS = r'[.!?]'

    # Code block patterns
    CODE_BLOCK_PATTERNS = [
        (r'```[\s\S]*?```', 'fenced'),  # Fenced code blocks
        (r'~~~[\s\S]*?~~~', 'fenced'),  # Alternative fenced blocks
        (r'(?:^|\n)(?: {4}|\t).+(?:\n(?: {4}|\t).+)*', 'indented'),  # Indented code
    ]

    def __init__(self, min_sentence_length: int = 3, preserve_code: bool = True):
        """
        Initialize the segmenter.

        Args:
            min_sentence_length: Minimum characters for a valid sentence
            preserve_code: Whether to preserve code blocks intact
        """
        self.min_sentence_length = min_sentence_length
        self.preserve_code = preserve_code

    def segment_text(self, text: str, granularity: str = 'sentence') -> List[Segment]:
        """
        Segment text into sentences or paragraphs.

        Args:
            text: Input text to segment
            granularity: 'sentence' or 'paragraph'

        Returns:
            List of Segment objects
        """
        if granularity == 'sentence':
            return self.segment_sentences(text)
        elif granularity == 'paragraph':
            return self.segment_paragraphs(text)
        else:
            raise ValueError(f"Invalid granularity: {granularity}")

    def segment_sentences(self, text: str) -> List[Segment]:
        """
        Split text into sentences while preserving code blocks.

        Args:
            text: Input text

        Returns:
            List of sentence segments
        """
        segments = []

        # Extract and preserve code blocks
        protected_regions = []
        if self.preserve_code:
            protected_regions = self._extract_code_blocks(text)

        # Track position in original text
        current_pos = 0

        for region_start, region_end, region_type in protected_regions:
            # Process text before code block
            if current_pos < region_start:
                prose_text = text[current_pos:region_start]
                prose_segments = self._split_sentences(prose_text, current_pos)
                segments.extend(prose_segments)

            # Add code block as single segment
            code_text = text[region_start:region_end]
            segments.append(Segment(
                text=code_text,
                type=SegmentType.CODE_BLOCK,
                start_pos=region_start,
                end_pos=region_end,
                metadata={'code_type': region_type}
            ))

            current_pos = region_end

        # Process remaining text
        if current_pos < len(text):
            remaining_text = text[current_pos:]
            remaining_segments = self._split_sentences(remaining_text, current_pos)
            segments.extend(remaining_segments)

        return segments

    def segment_paragraphs(self, text: str) -> List[Segment]:
        """
        Split text into paragraphs.

        Args:
            text: Input text

        Returns:
            List of paragraph segments
        """
        segments = []

        # Split on double newlines (paragraph breaks)
        paragraphs = re.split(r'\n\s*\n', text)

        current_pos = 0
        for para in paragraphs:
            if not para.strip():
                current_pos += len(para) + 2  # Account for newlines
                continue

            # Determine paragraph type
            para_type = self._classify_paragraph(para)

            # Find actual position in original text
            start_pos = text.find(para, current_pos)
            end_pos = start_pos + len(para)

            segments.append(Segment(
                text=para,
                type=para_type,
                start_pos=start_pos,
                end_pos=end_pos
            ))

            current_pos = end_pos

        return segments

    def _extract_code_blocks(self, text: str) -> List[Tuple[int, int, str]]:
        """
        Extract positions of code blocks in text.

        Returns:
            List of (start_pos, end_pos, code_type) tuples
        """
        code_blocks = []

        for pattern, code_type in self.CODE_BLOCK_PATTERNS:
            for match in re.finditer(pattern, text, re.MULTILINE):
                code_blocks.append((match.start(), match.end(), code_type))

        # Sort by position and merge overlapping blocks
        code_blocks.sort()
        merged = []
        for start, end, ctype in code_blocks:
            if merged and start < merged[-1][1]:
                # Overlapping - extend previous block
                merged[-1] = (merged[-1][0], max(end, merged[-1][1]), merged[-1][2])
            else:
                merged.append((start, end, ctype))

        return merged

    def _split_sentences(self, text: str, offset: int = 0) -> List[Segment]:
        """
        Split prose text into sentences.

        Args:
            text: Text to split
            offset: Position offset in original document

        Returns:
            List of sentence segments
        """
        sentences = []

        # Simple sentence splitting with abbreviation awareness
        potential_breaks = list(re.finditer(self.SENTENCE_ENDERS, text))

        sentence_start = 0
        for i, match in enumerate(potential_breaks):
            end_pos = match.end()

            # Check if this is a real sentence boundary
            if self._is_sentence_boundary(text, match.start(), end_pos):
                sentence_text = text[sentence_start:end_pos].strip()

                if len(sentence_text) >= self.min_sentence_length:
                    sentences.append(Segment(
                        text=sentence_text,
                        type=SegmentType.SENTENCE,
                        start_pos=offset + sentence_start,
                        end_pos=offset + end_pos
                    ))

                sentence_start = end_pos

        # Add final sentence if exists
        if sentence_start < len(text):
            final_text = text[sentence_start:].strip()
            if len(final_text) >= self.min_sentence_length:
                sentences.append(Segment(
                    text=final_text,
                    type=SegmentType.SENTENCE,
                    start_pos=offset + sentence_start,
                    end_pos=offset + len(text)
                ))

        return sentences

    def _is_sentence_boundary(self, text: str, punct_pos: int, end_pos: int) -> bool:
        """
        Determine if punctuation marks a sentence boundary.

        Args:
            text: Full text
            punct_pos: Position of punctuation
            end_pos: Position after punctuation

        Returns:
            True if this is a sentence boundary
        """
        # Check for abbreviations
        if punct_pos > 0:
            # Look back for potential abbreviation
            before = text[max(0, punct_pos - 10):punct_pos].lower()
            for abbrev in self.ABBREVIATIONS:
                if before.endswith(abbrev):
                    return False

        # Check what comes after
        if end_pos < len(text):
            after = text[end_pos:end_pos + 1]
            # Sentence should be followed by whitespace or end of text
            if after and not after.isspace():
                return False

            # Next character should be uppercase or digit (for numbered lists)
            if end_pos + 1 < len(text):
                next_char = text[end_pos:].lstrip()[:1]
                if next_char and not (next_char[0].isupper() or next_char[0].isdigit()):
                    # Exception for quotes
                    if next_char[0] not in '"\'':
                        return False

        return True

    def _classify_paragraph(self, para: str) -> SegmentType:
        """
        Classify the type of a paragraph.

        Args:
            para: Paragraph text

        Returns:
            SegmentType for the paragraph
        """
        stripped = para.strip()

        # Check for heading (markdown style)
        if re.match(r'^#{1,6}\s+', stripped):
            return SegmentType.HEADING

        # Check for list item
        if re.match(r'^[\-\*\+]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
            return SegmentType.LIST_ITEM

        # Check for code block
        if stripped.startswith('```') or stripped.startswith('~~~'):
            return SegmentType.CODE_BLOCK

        return SegmentType.PARAGRAPH
