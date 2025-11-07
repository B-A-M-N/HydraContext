"""
Content classification: Code vs Prose detection.

Heuristic-based classifier to distinguish between code,
prose, structured data, and mixed content.
"""

import re
from typing import Dict, Optional, Tuple
from enum import Enum
from dataclasses import dataclass


class ContentType(Enum):
    """Types of content."""
    PROSE = "prose"
    CODE = "code"
    STRUCTURED_DATA = "structured_data"
    MIXED = "mixed"
    UNKNOWN = "unknown"


@dataclass
class ClassificationResult:
    """Result of content classification."""
    content_type: ContentType
    confidence: float  # 0.0 to 1.0
    indicators: Dict[str, float]  # Individual feature scores
    metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ContentClassifier:
    """
    Heuristic-based classifier for distinguishing code from prose.

    Uses multiple features:
    - Syntax patterns (brackets, operators, keywords)
    - Indentation and structure
    - Character distribution
    - Line patterns
    """

    # Programming language keywords (common across languages)
    CODE_KEYWORDS = {
        'function', 'class', 'def', 'return', 'if', 'else', 'for', 'while',
        'import', 'from', 'const', 'let', 'var', 'int', 'float', 'string',
        'public', 'private', 'static', 'void', 'async', 'await', 'try',
        'catch', 'throw', 'new', 'this', 'self', 'lambda', 'yield',
    }

    # Prose indicators
    PROSE_PATTERNS = [
        r'\b(the|a|an|and|or|but|in|on|at|to|for|of|with)\b',  # Common articles/prepositions
        r'[.!?]\s+[A-Z]',  # Sentence boundaries
        r'\b(is|are|was|were|be|been|being)\b',  # Verb forms
    ]

    # Code syntax patterns
    CODE_PATTERNS = [
        r'[{}\[\]()]',  # Brackets
        r'[=<>!]+',  # Operators
        r';$',  # Statement terminators
        r'=>|->|\|\||&&',  # Arrow functions, logical operators
        r'^\s*#include|^import |^from .+ import',  # Imports
        r'^\s*(public|private|protected)\s+(class|interface|enum)',  # Access modifiers
    ]

    # Structured data patterns (JSON, XML, YAML, etc.)
    STRUCTURED_PATTERNS = [
        r'^\s*[\{].*[\}]\s*$',  # JSON-like
        r'^\s*<[^>]+>.*</[^>]+>\s*$',  # XML-like
        r'^\s*[\w-]+:\s+',  # YAML-like key:value
    ]

    def __init__(self, threshold: float = 0.6):
        """
        Initialize classifier.

        Args:
            threshold: Confidence threshold for classification (0.0 to 1.0)
        """
        self.threshold = threshold

    def classify(self, text: str) -> ClassificationResult:
        """
        Classify text as code, prose, structured data, or mixed.

        Args:
            text: Text to classify

        Returns:
            ClassificationResult with type and confidence
        """
        if not text.strip():
            return ClassificationResult(
                content_type=ContentType.UNKNOWN,
                confidence=0.0,
                indicators={}
            )

        # Calculate individual feature scores
        indicators = {
            'code_syntax': self._score_code_syntax(text),
            'code_keywords': self._score_code_keywords(text),
            'indentation': self._score_indentation(text),
            'prose_patterns': self._score_prose_patterns(text),
            'structured_data': self._score_structured_data(text),
            'punctuation': self._score_punctuation(text),
            'line_length': self._score_line_length(text),
            'whitespace': self._score_whitespace(text),
        }

        # Weighted combination
        code_score = (
            indicators['code_syntax'] * 0.3 +
            indicators['code_keywords'] * 0.25 +
            indicators['indentation'] * 0.2 +
            (1 - indicators['prose_patterns']) * 0.25
        )

        prose_score = (
            indicators['prose_patterns'] * 0.4 +
            indicators['punctuation'] * 0.3 +
            (1 - indicators['code_syntax']) * 0.3
        )

        structured_score = indicators['structured_data']

        # Determine classification
        max_score = max(code_score, prose_score, structured_score)

        if structured_score > 0.7:
            content_type = ContentType.STRUCTURED_DATA
            confidence = structured_score
        elif code_score > prose_score and code_score >= self.threshold:
            content_type = ContentType.CODE
            confidence = code_score
        elif prose_score >= self.threshold:
            content_type = ContentType.PROSE
            confidence = prose_score
        elif abs(code_score - prose_score) < 0.2:
            # Scores are close - likely mixed content
            content_type = ContentType.MIXED
            confidence = max(code_score, prose_score)
        else:
            content_type = ContentType.UNKNOWN
            confidence = max_score

        # Add metadata
        metadata = {
            'code_score': round(code_score, 3),
            'prose_score': round(prose_score, 3),
            'structured_score': round(structured_score, 3),
            'char_count': len(text),
            'line_count': len(text.splitlines()),
        }

        return ClassificationResult(
            content_type=content_type,
            confidence=confidence,
            indicators=indicators,
            metadata=metadata
        )

    def _score_code_syntax(self, text: str) -> float:
        """
        Score based on code syntax patterns.

        Returns:
            Score from 0.0 (no code syntax) to 1.0 (heavy code syntax)
        """
        total_patterns = len(self.CODE_PATTERNS)
        matches = 0

        for pattern in self.CODE_PATTERNS:
            if re.search(pattern, text, re.MULTILINE):
                matches += 1

        # Also check bracket density
        bracket_chars = sum(1 for c in text if c in '{}[]()<>')
        bracket_density = bracket_chars / len(text) if text else 0

        pattern_score = matches / total_patterns
        syntax_score = (pattern_score * 0.7) + (min(bracket_density * 10, 1.0) * 0.3)

        return min(syntax_score, 1.0)

    def _score_code_keywords(self, text: str) -> float:
        """
        Score based on programming keywords.

        Returns:
            Score from 0.0 to 1.0
        """
        words = re.findall(r'\b\w+\b', text.lower())

        if not words:
            return 0.0

        keyword_count = sum(1 for word in words if word in self.CODE_KEYWORDS)
        keyword_ratio = keyword_count / len(words)

        # Scale: 5% keywords = 0.5, 10%+ = 1.0
        return min(keyword_ratio * 10, 1.0)

    def _score_indentation(self, text: str) -> float:
        """
        Score based on consistent indentation (indicates code).

        Returns:
            Score from 0.0 to 1.0
        """
        lines = [line for line in text.splitlines() if line.strip()]

        if len(lines) < 3:
            return 0.0

        # Count lines with leading whitespace
        indented = sum(1 for line in lines if line[0] in ' \t')
        indentation_ratio = indented / len(lines)

        # Check for consistent indentation levels
        indents = [len(line) - len(line.lstrip()) for line in lines if line.strip()]

        if not indents:
            return 0.0

        # Look for multiples of 2 or 4 (common indent sizes)
        indent_set = set(indents)
        consistent = all(
            indent % 2 == 0 or indent % 4 == 0
            for indent in indent_set
        )

        consistency_bonus = 0.3 if consistent else 0.0

        return min(indentation_ratio + consistency_bonus, 1.0)

    def _score_prose_patterns(self, text: str) -> float:
        """
        Score based on natural language patterns.

        Returns:
            Score from 0.0 to 1.0
        """
        text_lower = text.lower()
        total_patterns = len(self.PROSE_PATTERNS)
        matches = 0

        for pattern in self.PROSE_PATTERNS:
            if re.search(pattern, text_lower):
                matches += 1

        pattern_score = matches / total_patterns

        # Check for sentence-like structure
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0

        # Prose typically has 10-25 words per sentence
        sentence_score = 0.0
        if 10 <= avg_sentence_length <= 30:
            sentence_score = 0.5
        elif 5 <= avg_sentence_length <= 40:
            sentence_score = 0.3

        return min((pattern_score * 0.6) + (sentence_score * 0.4), 1.0)

    def _score_structured_data(self, text: str) -> float:
        """
        Score based on structured data patterns (JSON, XML, YAML).

        Returns:
            Score from 0.0 to 1.0
        """
        stripped = text.strip()

        # JSON detection
        if (stripped.startswith('{') and stripped.endswith('}')) or \
           (stripped.startswith('[') and stripped.endswith(']')):
            try:
                import json
                json.loads(stripped)
                return 1.0
            except:
                pass

        # XML detection
        if stripped.startswith('<') and stripped.endswith('>'):
            tag_count = len(re.findall(r'<[^>]+>', stripped))
            if tag_count >= 2:
                return 0.9

        # YAML-like key:value patterns
        lines = stripped.splitlines()
        key_value_lines = sum(
            1 for line in lines
            if re.match(r'^\s*[\w-]+:\s+', line)
        )

        if lines and key_value_lines / len(lines) > 0.5:
            return 0.8

        return 0.0

    def _score_punctuation(self, text: str) -> float:
        """
        Score based on punctuation patterns (prose has more varied punctuation).

        Returns:
            Score from 0.0 to 1.0
        """
        if not text:
            return 0.0

        # Count different punctuation types
        punct_types = {
            'period': text.count('.'),
            'comma': text.count(','),
            'question': text.count('?'),
            'exclaim': text.count('!'),
            'colon': text.count(':'),
            'semicolon': text.count(';'),
        }

        # Prose typically has varied punctuation
        variety = sum(1 for count in punct_types.values() if count > 0)
        variety_score = variety / len(punct_types)

        # Sentence-ending punctuation is strong prose indicator
        sentence_enders = punct_types['period'] + punct_types['question'] + punct_types['exclaim']
        ender_density = sentence_enders / len(text)

        # Prose typically has 1-3% sentence enders
        ender_score = min(ender_density * 50, 1.0)

        return (variety_score * 0.4) + (ender_score * 0.6)

    def _score_line_length(self, text: str) -> float:
        """
        Score based on line length patterns.

        Returns:
            Score from 0.0 (code-like) to 1.0 (prose-like)
        """
        lines = [line for line in text.splitlines() if line.strip()]

        if not lines:
            return 0.5

        avg_length = sum(len(line) for line in lines) / len(lines)

        # Prose typically has longer lines (60-80 chars)
        # Code typically has shorter lines (30-50 chars)
        if 60 <= avg_length <= 100:
            return 0.8  # Prose-like
        elif 30 <= avg_length <= 60:
            return 0.3  # Code-like
        else:
            return 0.5  # Uncertain

    def _score_whitespace(self, text: str) -> float:
        """
        Score based on whitespace patterns.

        Returns:
            Score from 0.0 to 1.0 (higher = more code-like)
        """
        if not text:
            return 0.0

        # Code typically has more whitespace
        whitespace_ratio = sum(1 for c in text if c in ' \t\n') / len(text)

        # Code also has more blank lines
        lines = text.splitlines()
        blank_lines = sum(1 for line in lines if not line.strip())
        blank_ratio = blank_lines / len(lines) if lines else 0

        return (whitespace_ratio * 0.5) + (blank_ratio * 0.5)
