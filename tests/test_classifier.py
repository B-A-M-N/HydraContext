"""Tests for the ContentClassifier."""

import pytest
from hydracontext.core.classifier import ContentClassifier, ContentType


def test_basic_code_detection():
    """Test detection of obvious code."""
    classifier = ContentClassifier()

    code = """
    def hello_world():
        print("Hello, World!")
        return 0
    """

    result = classifier.classify(code)
    assert result.content_type == ContentType.CODE
    assert result.confidence > 0.6


def test_basic_prose_detection():
    """Test detection of obvious prose."""
    classifier = ContentClassifier()

    prose = """
    The quick brown fox jumps over the lazy dog.
    This is a simple sentence in the English language.
    It demonstrates natural language processing.
    """

    result = classifier.classify(prose)
    assert result.content_type == ContentType.PROSE
    assert result.confidence > 0.6


def test_json_detection():
    """Test detection of JSON structured data."""
    classifier = ContentClassifier()

    json_data = '{"name": "John", "age": 30, "city": "New York"}'

    result = classifier.classify(json_data)
    assert result.content_type == ContentType.STRUCTURED_DATA
    assert result.confidence > 0.7


def test_xml_detection():
    """Test detection of XML structured data."""
    classifier = ContentClassifier()

    xml_data = "<person><name>John</name><age>30</age></person>"

    result = classifier.classify(xml_data)
    assert result.content_type == ContentType.STRUCTURED_DATA


def test_mixed_content():
    """Test detection of mixed code and prose."""
    classifier = ContentClassifier()

    mixed = """
    This is a comment about the code.

    function test() {
        return true;
    }
    """

    result = classifier.classify(mixed)
    # Should detect as either mixed or code
    assert result.content_type in [ContentType.MIXED, ContentType.CODE, ContentType.PROSE]


def test_empty_text():
    """Test classification of empty text."""
    classifier = ContentClassifier()

    result = classifier.classify("")
    assert result.content_type == ContentType.UNKNOWN
    assert result.confidence == 0.0


def test_code_keywords():
    """Test that code keywords increase code score."""
    classifier = ContentClassifier()

    code = "function test() { return class instance; }"
    result = classifier.classify(code)

    assert result.content_type == ContentType.CODE
    assert result.indicators['code_keywords'] > 0.1


def test_prose_patterns():
    """Test that prose patterns increase prose score."""
    classifier = ContentClassifier()

    prose = "The cat is on the mat. It is a very nice cat."
    result = classifier.classify(prose)

    assert result.content_type == ContentType.PROSE
    assert result.indicators['prose_patterns'] > 0.3


def test_confidence_threshold():
    """Test custom confidence threshold."""
    classifier = ContentClassifier(threshold=0.8)

    ambiguous = "test data sample"
    result = classifier.classify(ambiguous)

    # With high threshold, should be unknown or have low confidence
    assert result.confidence <= 0.8 or result.content_type == ContentType.UNKNOWN


def test_metadata_includes_scores():
    """Test that metadata includes score breakdown."""
    classifier = ContentClassifier()

    text = "Sample text for testing"
    result = classifier.classify(text)

    assert 'code_score' in result.metadata
    assert 'prose_score' in result.metadata
    assert 'structured_score' in result.metadata


def test_python_code():
    """Test classification of Python code."""
    classifier = ContentClassifier()

    python_code = """
    import os

    class MyClass:
        def __init__(self):
            self.value = 0

        def increment(self):
            self.value += 1
    """

    result = classifier.classify(python_code)
    assert result.content_type == ContentType.CODE


def test_javascript_code():
    """Test classification of JavaScript code."""
    classifier = ContentClassifier()

    js_code = """
    const add = (a, b) => {
        return a + b;
    };

    let result = add(5, 3);
    console.log(result);
    """

    result = classifier.classify(js_code)
    assert result.content_type == ContentType.CODE


def test_markdown_prose():
    """Test classification of markdown text."""
    classifier = ContentClassifier()

    markdown = """
    # Introduction

    This is a paragraph of text in markdown format.
    It contains normal prose with some formatting.

    ## Section Two

    More text here with natural language.
    """

    result = classifier.classify(markdown)
    # Should lean towards prose despite some structural elements
    assert result.content_type in [ContentType.PROSE, ContentType.MIXED]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
