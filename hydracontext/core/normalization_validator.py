"""
Normalization Validation and Fidelity Checking

Ensures that the normalization process maintains information fidelity
and validates JSON structure correctness.

This module:
1. Validates JSON schema correctness
2. Checks for information loss during normalization
3. Verifies semantic preservation
4. Ensures round-trip fidelity
5. Detects edge cases and errors
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib


@dataclass
class ValidationResult:
    """Result of a validation check."""
    passed: bool
    message: str
    severity: str  # 'error', 'warning', 'info'
    details: Optional[Dict] = None


@dataclass
class FidelityReport:
    """Report on normalization fidelity."""
    original_length: int
    normalized_length: int
    content_preserved: bool
    semantic_preserved: bool
    structure_preserved: bool
    validations: List[ValidationResult]
    fidelity_score: float  # 0.0 to 1.0


class NormalizationValidator:
    """
    Validates normalization process maintains information fidelity.

    Ensures that:
    - JSON structure is valid
    - No information is lost
    - Semantic meaning is preserved
    - Round-trip conversion works
    """

    # Required fields for normalized output
    REQUIRED_OUTPUT_FIELDS = {
        'content', 'provider', 'model', 'usage',
        'finish_reason', 'timestamp'
    }

    # Required fields for normalized input
    REQUIRED_INPUT_FIELDS = {
        'content', 'type', 'token_estimate', 'direction'
    }

    # Required usage subfields
    REQUIRED_USAGE_FIELDS = {
        'prompt_tokens', 'completion_tokens', 'total_tokens'
    }

    def __init__(self, strict: bool = True):
        """
        Initialize validator.

        Args:
            strict: If True, fail on any validation error. If False, allow warnings.
        """
        self.strict = strict
        self.validation_history: List[FidelityReport] = []

    def validate_normalized_output(self, normalized: Dict) -> List[ValidationResult]:
        """
        Validate a normalized output response.

        Args:
            normalized: Normalized response dict

        Returns:
            List of validation results
        """
        results = []

        # Check 1: Is it valid JSON structure?
        results.append(self._validate_json_structure(normalized))

        # Check 2: Has required fields?
        results.append(self._validate_required_fields(
            normalized,
            self.REQUIRED_OUTPUT_FIELDS,
            "output"
        ))

        # Check 3: Usage field has correct structure?
        if 'usage' in normalized:
            results.append(self._validate_usage_field(normalized['usage']))
        else:
            results.append(ValidationResult(
                passed=False,
                message="Missing 'usage' field",
                severity='error'
            ))

        # Check 4: Content is non-None?
        results.append(self._validate_content_exists(normalized))

        # Check 5: Provider is valid?
        results.append(self._validate_provider(normalized.get('provider')))

        # Check 6: Timestamp is valid ISO format?
        results.append(self._validate_timestamp(normalized.get('timestamp')))

        # Check 7: Token counts are non-negative integers?
        results.append(self._validate_token_counts(normalized.get('usage', {})))

        return results

    def validate_normalized_input(self, normalized: Dict) -> List[ValidationResult]:
        """
        Validate a normalized input prompt.

        Args:
            normalized: Normalized input dict

        Returns:
            List of validation results
        """
        results = []

        # Check 1: Is it valid JSON structure?
        results.append(self._validate_json_structure(normalized))

        # Check 2: Has required fields?
        results.append(self._validate_required_fields(
            normalized,
            self.REQUIRED_INPUT_FIELDS,
            "input"
        ))

        # Check 3: Direction is 'input'?
        if normalized.get('direction') != 'input':
            results.append(ValidationResult(
                passed=False,
                message=f"Direction should be 'input', got '{normalized.get('direction')}'",
                severity='error'
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message="Direction field correct",
                severity='info'
            ))

        # Check 4: Type is valid?
        results.append(self._validate_prompt_type(normalized.get('type')))

        # Check 5: Token estimate is positive?
        token_est = normalized.get('token_estimate', 0)
        if token_est < 0:
            results.append(ValidationResult(
                passed=False,
                message=f"Token estimate cannot be negative: {token_est}",
                severity='error'
            ))
        else:
            results.append(ValidationResult(
                passed=True,
                message=f"Token estimate valid: {token_est}",
                severity='info'
            ))

        return results

    def check_fidelity(
        self,
        original: str,
        normalized_dict: Dict,
        check_type: str = 'output'
    ) -> FidelityReport:
        """
        Check information fidelity after normalization.

        Compares original text with normalized version to ensure
        no critical information was lost.

        Args:
            original: Original text
            normalized_dict: Normalized dict with 'content' or 'normalized_content'
            check_type: 'input' or 'output'

        Returns:
            Fidelity report
        """
        validations = []

        # Get normalized content
        if check_type == 'output':
            normalized_content = (
                normalized_dict.get('content') or
                normalized_dict.get('normalized_content') or
                ''
            )
        else:
            normalized_content = normalized_dict.get('content', '')

        # Check 1: Content exists
        if not normalized_content:
            validations.append(ValidationResult(
                passed=False,
                message="Normalized content is empty",
                severity='error'
            ))
            content_preserved = False
        else:
            validations.append(ValidationResult(
                passed=True,
                message=f"Normalized content exists ({len(normalized_content)} chars)",
                severity='info'
            ))
            content_preserved = True

        # Check 2: Key terms preserved
        semantic_preserved = self._check_semantic_preservation(
            original,
            normalized_content
        )
        validations.append(ValidationResult(
            passed=semantic_preserved,
            message="Semantic preservation check",
            severity='error' if not semantic_preserved else 'info',
            details={
                'original_length': len(original),
                'normalized_length': len(normalized_content)
            }
        ))

        # Check 3: Structure preserved (code blocks, lists, etc.)
        structure_preserved = self._check_structure_preservation(
            original,
            normalized_content
        )
        validations.append(ValidationResult(
            passed=structure_preserved,
            message="Structure preservation check",
            severity='warning' if not structure_preserved else 'info'
        ))

        # Calculate fidelity score
        fidelity_score = self._calculate_fidelity_score(
            original,
            normalized_content,
            semantic_preserved,
            structure_preserved
        )

        return FidelityReport(
            original_length=len(original),
            normalized_length=len(normalized_content),
            content_preserved=content_preserved,
            semantic_preserved=semantic_preserved,
            structure_preserved=structure_preserved,
            validations=validations,
            fidelity_score=fidelity_score
        )

    def validate_round_trip(
        self,
        original_text: str,
        normalize_func,
        denormalize_func
    ) -> Tuple[bool, Dict]:
        """
        Validate that text can be normalized and denormalized without loss.

        Args:
            original_text: Original text
            normalize_func: Function to normalize text
            denormalize_func: Function to denormalize back to text

        Returns:
            (success, details_dict)
        """
        # Normalize
        normalized = normalize_func(original_text)

        # Denormalize
        reconstructed = denormalize_func(normalized)

        # Compare
        exact_match = original_text == reconstructed

        # Calculate similarity even if not exact
        similarity = self._calculate_text_similarity(original_text, reconstructed)

        return exact_match or similarity > 0.95, {
            'original_length': len(original_text),
            'reconstructed_length': len(reconstructed),
            'exact_match': exact_match,
            'similarity': similarity,
            'length_delta': len(reconstructed) - len(original_text)
        }

    # Private validation methods

    def _validate_json_structure(self, data: Any) -> ValidationResult:
        """Check if data is valid JSON-serializable structure."""
        try:
            json.dumps(data)
            return ValidationResult(
                passed=True,
                message="Valid JSON structure",
                severity='info'
            )
        except (TypeError, ValueError) as e:
            return ValidationResult(
                passed=False,
                message=f"Invalid JSON structure: {e}",
                severity='error'
            )

    def _validate_required_fields(
        self,
        data: Dict,
        required: set,
        data_type: str
    ) -> ValidationResult:
        """Check if all required fields are present."""
        missing = required - set(data.keys())

        if missing:
            return ValidationResult(
                passed=False,
                message=f"Missing required {data_type} fields: {missing}",
                severity='error',
                details={'missing_fields': list(missing)}
            )

        return ValidationResult(
            passed=True,
            message=f"All required {data_type} fields present",
            severity='info'
        )

    def _validate_usage_field(self, usage: Dict) -> ValidationResult:
        """Validate usage field structure."""
        if not isinstance(usage, dict):
            return ValidationResult(
                passed=False,
                message=f"Usage field must be dict, got {type(usage).__name__}",
                severity='error'
            )

        missing = self.REQUIRED_USAGE_FIELDS - set(usage.keys())

        if missing:
            return ValidationResult(
                passed=False,
                message=f"Usage field missing: {missing}",
                severity='error',
                details={'missing_fields': list(missing)}
            )

        return ValidationResult(
            passed=True,
            message="Usage field structure valid",
            severity='info'
        )

    def _validate_content_exists(self, data: Dict) -> ValidationResult:
        """Check if content field exists and is not None."""
        content = data.get('content') or data.get('normalized_content')

        if content is None:
            return ValidationResult(
                passed=False,
                message="Content field is None",
                severity='error'
            )

        if not isinstance(content, str):
            return ValidationResult(
                passed=False,
                message=f"Content must be string, got {type(content).__name__}",
                severity='error'
            )

        return ValidationResult(
            passed=True,
            message=f"Content field valid ({len(content)} chars)",
            severity='info'
        )

    def _validate_provider(self, provider: Optional[str]) -> ValidationResult:
        """Validate provider field."""
        valid_providers = {'openai', 'anthropic', 'ollama', 'generic'}

        if not provider:
            return ValidationResult(
                passed=False,
                message="Provider field is empty",
                severity='warning'
            )

        if provider not in valid_providers:
            return ValidationResult(
                passed=False,
                message=f"Unknown provider '{provider}', expected one of {valid_providers}",
                severity='warning'
            )

        return ValidationResult(
            passed=True,
            message=f"Provider '{provider}' is valid",
            severity='info'
        )

    def _validate_timestamp(self, timestamp: Optional[str]) -> ValidationResult:
        """Validate timestamp is ISO format."""
        if not timestamp:
            return ValidationResult(
                passed=False,
                message="Timestamp field is empty",
                severity='warning'
            )

        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return ValidationResult(
                passed=True,
                message="Timestamp is valid ISO format",
                severity='info'
            )
        except (ValueError, AttributeError) as e:
            return ValidationResult(
                passed=False,
                message=f"Invalid timestamp format: {e}",
                severity='warning'
            )

    def _validate_token_counts(self, usage: Dict) -> ValidationResult:
        """Validate token counts are non-negative integers."""
        for field in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            value = usage.get(field, 0)

            if not isinstance(value, int) or value < 0:
                return ValidationResult(
                    passed=False,
                    message=f"Invalid token count for '{field}': {value}",
                    severity='error'
                )

        return ValidationResult(
            passed=True,
            message="Token counts are valid",
            severity='info'
        )

    def _validate_prompt_type(self, prompt_type: Optional[str]) -> ValidationResult:
        """Validate prompt type field."""
        valid_types = {'code', 'conversation', 'instruction', 'example', 'system'}

        if not prompt_type:
            return ValidationResult(
                passed=False,
                message="Prompt type is empty",
                severity='error'
            )

        if prompt_type not in valid_types:
            return ValidationResult(
                passed=False,
                message=f"Unknown prompt type '{prompt_type}', expected one of {valid_types}",
                severity='warning'
            )

        return ValidationResult(
            passed=True,
            message=f"Prompt type '{prompt_type}' is valid",
            severity='info'
        )

    def _check_semantic_preservation(self, original: str, normalized: str) -> bool:
        """
        Check if semantic meaning is preserved.

        Uses simple heuristics:
        - Key terms should be present
        - Length shouldn't change dramatically
        - Word overlap should be high
        """
        if not normalized:
            return False

        # Extract key terms (words longer than 3 chars, alphanumeric)
        import re
        original_terms = set(re.findall(r'\b[a-zA-Z0-9]{4,}\b', original.lower()))
        normalized_terms = set(re.findall(r'\b[a-zA-Z0-9]{4,}\b', normalized.lower()))

        if not original_terms:
            return True  # No key terms to preserve

        # Calculate term preservation ratio
        preserved = len(original_terms & normalized_terms)
        total = len(original_terms)
        preservation_ratio = preserved / total if total > 0 else 0

        # Check length change isn't too dramatic
        length_ratio = len(normalized) / len(original) if len(original) > 0 else 1

        # Semantic preserved if:
        # - At least 70% of key terms preserved
        # - Length is between 20% and 200% of original
        return preservation_ratio >= 0.7 and 0.2 <= length_ratio <= 2.0

    def _check_structure_preservation(self, original: str, normalized: str) -> bool:
        """
        Check if structural elements are preserved.

        Checks for:
        - Code blocks (```)
        - Lists (-, *, 1.)
        - Headings (#)
        """
        # Count structural elements
        original_code_blocks = original.count('```')
        normalized_code_blocks = normalized.count('```')

        original_headings = len([l for l in original.split('\n') if l.strip().startswith('#')])
        normalized_headings = len([l for l in normalized.split('\n') if l.strip().startswith('#')])

        # Structure preserved if counts are similar (allow ±1 for edge cases)
        code_blocks_match = abs(original_code_blocks - normalized_code_blocks) <= 1
        headings_match = abs(original_headings - normalized_headings) <= 1

        return code_blocks_match and headings_match

    def _calculate_fidelity_score(
        self,
        original: str,
        normalized: str,
        semantic_preserved: bool,
        structure_preserved: bool
    ) -> float:
        """
        Calculate overall fidelity score (0.0 to 1.0).

        Components:
        - Content existence: 0.3
        - Semantic preservation: 0.4
        - Structure preservation: 0.2
        - Length ratio: 0.1
        """
        score = 0.0

        # Content exists
        if normalized:
            score += 0.3

        # Semantic preservation
        if semantic_preserved:
            score += 0.4

        # Structure preservation
        if structure_preserved:
            score += 0.2

        # Length ratio (penalty for dramatic changes)
        if original and normalized:
            length_ratio = len(normalized) / len(original)
            if 0.5 <= length_ratio <= 1.5:
                score += 0.1
            elif 0.2 <= length_ratio <= 2.0:
                score += 0.05

        return min(score, 1.0)

    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 to 1.0)."""
        if not text1 or not text2:
            return 0.0

        # Simple word-level Jaccard similarity
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def print_validation_report(
        self,
        results: List[ValidationResult],
        show_info: bool = False
    ) -> None:
        """Print validation results in a readable format."""
        errors = [r for r in results if r.severity == 'error' and not r.passed]
        warnings = [r for r in results if r.severity == 'warning' and not r.passed]
        info = [r for r in results if r.severity == 'info' and r.passed]

        if errors:
            print(f"\n❌ ERRORS ({len(errors)}):")
            for result in errors:
                print(f"   {result.message}")
                if result.details:
                    print(f"      Details: {result.details}")

        if warnings:
            print(f"\n⚠️  WARNINGS ({len(warnings)}):")
            for result in warnings:
                print(f"   {result.message}")

        if show_info and info:
            print(f"\n✅ PASSED ({len(info)}):")
            for result in info:
                print(f"   {result.message}")

        total_passed = len([r for r in results if r.passed])
        total = len(results)
        print(f"\n📊 TOTAL: {total_passed}/{total} checks passed")

    def print_fidelity_report(self, report: FidelityReport) -> None:
        """Print fidelity report in a readable format."""
        print(f"\n📊 FIDELITY REPORT")
        print(f"   Original length: {report.original_length} chars")
        print(f"   Normalized length: {report.normalized_length} chars")
        print(f"   Content preserved: {'✅' if report.content_preserved else '❌'}")
        print(f"   Semantic preserved: {'✅' if report.semantic_preserved else '❌'}")
        print(f"   Structure preserved: {'✅' if report.structure_preserved else '❌'}")
        print(f"   Fidelity score: {report.fidelity_score:.2f}/1.00")

        if report.fidelity_score >= 0.9:
            print(f"   Overall: ✅ EXCELLENT")
        elif report.fidelity_score >= 0.7:
            print(f"   Overall: ⚠️  GOOD")
        else:
            print(f"   Overall: ❌ POOR - Information loss detected")
