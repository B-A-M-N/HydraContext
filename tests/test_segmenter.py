"""Tests for the ContextSegmenter."""

import pytest
from hydracontext.core.segmenter import ContextSegmenter, SegmentType


def test_basic_sentence_segmentation():
    """Test basic sentence segmentation."""
    segmenter = ContextSegmenter()

    text = "This is sentence one. This is sentence two! Is this sentence three?"
    segments = segmenter.segment_sentences(text)

    assert len(segments) == 3
    assert all(seg.type == SegmentType.SENTENCE for seg in segments)


def test_paragraph_segmentation():
    """Test paragraph segmentation."""
    segmenter = ContextSegmenter()

    text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
    segments = segmenter.segment_paragraphs(text)

    assert len(segments) == 3
    assert all(seg.type == SegmentType.PARAGRAPH for seg in segments)


def test_code_block_preservation():
    """Test that code blocks are preserved intact."""
    segmenter = ContextSegmenter()

    text = """
    Some text before.

    ```python
    def hello():
        print("Hello")
    ```

    Some text after.
    """

    segments = segmenter.segment_sentences(text)

    # Should have text before, code block, text after
    code_segments = [s for s in segments if s.type == SegmentType.CODE_BLOCK]
    assert len(code_segments) >= 1


def test_abbreviation_handling():
    """Test that abbreviations don't break sentences."""
    segmenter = ContextSegmenter()

    text = "Dr. Smith went to the store. He bought milk."
    segments = segmenter.segment_sentences(text)

    # Should be 2 sentences, not 3
    assert len(segments) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
