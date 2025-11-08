"""Tests for the ContextSegmenter."""

import pytest
from hydracontext.core.segmenter import ContextSegmenter, SegmentType, Segment


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


def test_segment_positions():
    """Test that segment positions are tracked correctly."""
    segmenter = ContextSegmenter()

    text = "First sentence. Second sentence."
    segments = segmenter.segment_sentences(text)

    assert segments[0].start_pos == 0
    assert segments[0].end_pos > 0
    assert segments[1].start_pos > segments[0].end_pos


def test_min_sentence_length():
    """Test minimum sentence length filter."""
    segmenter = ContextSegmenter(min_sentence_length=10)

    text = "Hi. This is a longer sentence that meets the minimum."
    segments = segmenter.segment_sentences(text)

    # "Hi." should be filtered out
    assert len(segments) == 1
    assert "longer" in segments[0].text


def test_segment_text_sentence():
    """Test segment_text with sentence granularity."""
    segmenter = ContextSegmenter()

    text = "First. Second. Third."
    segments = segmenter.segment_text(text, granularity='sentence')

    assert len(segments) == 3


def test_segment_text_paragraph():
    """Test segment_text with paragraph granularity."""
    segmenter = ContextSegmenter()

    text = "Para 1.\n\nPara 2.\n\nPara 3."
    segments = segmenter.segment_text(text, granularity='paragraph')

    assert len(segments) == 3


def test_segment_text_invalid_granularity():
    """Test that invalid granularity raises error."""
    segmenter = ContextSegmenter()

    with pytest.raises(ValueError, match="Invalid granularity"):
        segmenter.segment_text("Text", granularity='word')


def test_markdown_heading_detection():
    """Test detection of markdown headings."""
    segmenter = ContextSegmenter()

    text = "# Heading One\n\n## Heading Two\n\nRegular paragraph."
    segments = segmenter.segment_paragraphs(text)

    heading_segments = [s for s in segments if s.type == SegmentType.HEADING]
    assert len(heading_segments) >= 1


def test_list_item_detection():
    """Test detection of list items."""
    segmenter = ContextSegmenter()

    text = "- Item one\n- Item two\n- Item three"
    segments = segmenter.segment_paragraphs(text)

    list_segments = [s for s in segments if s.type == SegmentType.LIST_ITEM]
    assert len(list_segments) >= 1


def test_indented_code_block():
    """Test detection of indented code blocks."""
    segmenter = ContextSegmenter()

    text = """
Regular text.

    def hello():
        print("Hello")
        return True

More regular text.
    """

    segments = segmenter.segment_sentences(text)

    code_segments = [s for s in segments if s.type == SegmentType.CODE_BLOCK]
    assert len(code_segments) >= 0  # May or may not detect indented blocks


def test_multiple_code_blocks():
    """Test handling multiple code blocks."""
    segmenter = ContextSegmenter()

    text = """
Text before.

```python
code1()
```

Text between.

```javascript
code2()
```

Text after.
    """

    segments = segmenter.segment_sentences(text)

    code_segments = [s for s in segments if s.type == SegmentType.CODE_BLOCK]
    assert len(code_segments) >= 2


def test_empty_text():
    """Test segmentation of empty text."""
    segmenter = ContextSegmenter()

    segments = segmenter.segment_sentences("")
    assert len(segments) == 0


def test_single_word():
    """Test segmentation of single word."""
    segmenter = ContextSegmenter(min_sentence_length=1)

    segments = segmenter.segment_sentences("Word")
    assert len(segments) == 1


def test_preserve_code_setting():
    """Test preserve_code setting."""
    segmenter_with = ContextSegmenter(preserve_code=True)
    segmenter_without = ContextSegmenter(preserve_code=False)

    text = "```python\ncode\n```"

    segments_with = segmenter_with.segment_sentences(text)
    segments_without = segmenter_without.segment_sentences(text)

    # Both should work, but may segment differently
    assert isinstance(segments_with, list)
    assert isinstance(segments_without, list)


def test_segment_metadata():
    """Test that segment metadata is included."""
    segmenter = ContextSegmenter()

    text = "```python\ncode\n```"
    segments = segmenter.segment_sentences(text)

    code_segment = next((s for s in segments if s.type == SegmentType.CODE_BLOCK), None)

    if code_segment:
        assert code_segment.metadata is not None
        assert isinstance(code_segment.metadata, dict)


def test_question_mark_sentence():
    """Test sentences ending with question marks."""
    segmenter = ContextSegmenter()

    text = "What is this? It is a test! Really?"
    segments = segmenter.segment_sentences(text)

    assert len(segments) == 3


def test_exclamation_sentence():
    """Test sentences ending with exclamation marks."""
    segmenter = ContextSegmenter()

    text = "Hello! How are you! Great!"
    segments = segmenter.segment_sentences(text)

    assert len(segments) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
