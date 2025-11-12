"""
HydraContext - Universal JSON Normalization & Validation Layer
--------------------------------------------------------------

This module provides the core `normalize()` function used to enforce
lossless, deterministic JSON I/O between LLMs and agents.

It ensures that *any* string emitted by a model is returned as valid JSON —
automatically repaired, recursively validated, and type-normalized.

Features:
- Automatic JSON validation and repair with up to N retries.
- Detects and extracts embedded JSON from mixed text.
- Strict or permissive modes for coercing malformed values.
- Deterministic ordering for cross-model fidelity.
- Two-tier system: lightweight (stdlib only) or full validation (with existing components)
"""

import json
import re
from typing import Any, Union, Optional, Dict, Literal
from datetime import datetime


def normalize(
    raw_output: Union[str, dict, list],
    retries: int = 3,
    strict: bool = True,
    sort_keys: bool = True,
    direction: Literal["input", "output", "auto"] = "auto",
    provider: Optional[str] = None,
    full_validation: bool = False,
) -> dict:
    """
    Normalize and validate model output into deterministic JSON.

    This is the universal entry point for HydraContext normalization.
    Works in two modes:

    1. **Lightweight** (default): Pure stdlib, zero dependencies, fast
       - JSON extraction and repair
       - Deterministic ordering
       - Type normalization

    2. **Full validation** (full_validation=True): Uses existing components
       - Provider-specific parsing (OpenAI/Anthropic/Ollama)
       - Pydantic schema validation
       - Fidelity checking
       - Rich metadata extraction

    Args:
        raw_output: The raw model output (string, dict, or list).
        retries: Number of repair attempts before raising error.
        strict: Whether to raise if repair fails (vs. return best effort).
        sort_keys: If True, ensures deterministic key ordering.
        direction: "input", "output", or "auto" (detect automatically).
        provider: Provider hint ("openai", "anthropic", "ollama", auto-detected if None).
        full_validation: Use full validation with Pydantic schemas and provider parsers.

    Returns:
        dict: Validated JSON object representing the model output.

    Examples:
        >>> # Lightweight mode (stdlib only)
        >>> normalize('{"result": "success"}')
        {'result': 'success'}

        >>> # Extract JSON from mixed text
        >>> normalize('The result is: {"status": "ok", "code": 200}')
        {'code': 200, 'status': 'ok'}

        >>> # Full validation with provider detection
        >>> ollama_response = {"response": "Hello", "model": "llama2", "done": True}
        >>> normalize(ollama_response, full_validation=True)
        {'content': 'Hello', 'provider': 'ollama', 'model': 'llama2', ...}
    """

    # Full validation mode: use existing components
    if full_validation:
        return _normalize_full(
            raw_output,
            direction=direction,
            provider=provider,
            retries=retries,
            strict=strict
        )

    # Lightweight mode: pure stdlib
    if isinstance(raw_output, (dict, list)):
        # Already parsed, just ensure determinism
        return _ensure_determinism(raw_output, sort_keys=sort_keys)

    text = str(raw_output).strip()

    # Try direct parsing first
    for attempt in range(retries + 1):
        try:
            parsed = json.loads(text)
            return _ensure_determinism(parsed, sort_keys=sort_keys)
        except json.JSONDecodeError as e:
            if attempt < retries:
                # Try to extract/repair JSON
                text = _attempt_repair(text, attempt=attempt)
            else:
                # Final attempt failed
                if strict:
                    raise ValueError(
                        f"Failed to normalize text into valid JSON after {retries} attempts. "
                        f"Last error: {e}"
                    )
                # Best-effort fallback
                return {
                    "_raw": raw_output,
                    "_error": str(e),
                    "_note": "best-effort normalization failed",
                    "_timestamp": datetime.utcnow().isoformat()
                }

    # Should never reach here, but fallback just in case
    if strict:
        raise ValueError("Unexpected error in normalization.")
    return {"_raw": raw_output, "_note": "unexpected normalization error"}


def _attempt_repair(text: str, attempt: int = 0) -> str:
    """
    Attempt to extract and repair JSON-like content.

    Progressive repair strategy - try gentler fixes first, more aggressive later.
    """
    # Attempt 0: Extract JSON block from mixed text
    if attempt == 0:
        # Look for JSON object or array
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]', text, re.DOTALL)
        if match:
            text = match.group(0)

    # Attempt 1: Fix common quote issues
    if attempt >= 1:
        # Replace single quotes with double quotes (but not in strings)
        text = re.sub(r"(?<=[{\[,:\s])'([^']*)'(?=[}\],\s])", r'"\1"', text)

    # Attempt 2: Fix unquoted keys
    if attempt >= 2:
        # Match word characters followed by colon (unquoted keys)
        text = re.sub(r'\b(\w+)(?=\s*:)', r'"\1"', text)

    # All attempts: Common fixes
    # Remove trailing commas
    text = re.sub(r',\s*([\]}])', r'\1', text)

    # Fix boolean values (ensure lowercase)
    text = re.sub(r'\bTrue\b', 'true', text)
    text = re.sub(r'\bFalse\b', 'false', text)
    text = re.sub(r'\bNone\b', 'null', text)

    # Remove any leading/trailing whitespace
    text = text.strip()

    return text


def _ensure_determinism(obj: Any, sort_keys: bool = True) -> Any:
    """
    Ensure deterministic ordering and types for fidelity.

    This enables consistent hashing and comparison across model outputs.
    """
    if isinstance(obj, dict):
        items = sorted(obj.items()) if sort_keys else obj.items()
        ordered = {k: _ensure_determinism(v, sort_keys=sort_keys) for k, v in items}
        return ordered
    elif isinstance(obj, list):
        return [_ensure_determinism(v, sort_keys=sort_keys) for v in obj]
    else:
        # Primitive types remain unchanged
        return obj


def _normalize_full(
    raw_output: Union[str, dict, list],
    direction: Literal["input", "output", "auto"],
    provider: Optional[str],
    retries: int,
    strict: bool
) -> Dict:
    """
    Full normalization using existing HydraContext components.

    This mode provides:
    - Provider-specific parsing (OpenAI, Anthropic, Ollama)
    - Pydantic schema validation
    - Fidelity checking
    - Rich metadata extraction
    """
    # Import here to keep lightweight mode dependency-free
    from .core.bidirectional import ContextNormalizer
    from .core.provider_parsers import UnifiedResponseParser
    from .core.normalization_validator import NormalizationValidator

    try:
        from .core.schemas import validate_normalized_output, validate_normalized_input
        use_pydantic = True
    except ImportError:
        use_pydantic = False

    normalizer = ContextNormalizer()
    parser = UnifiedResponseParser()
    validator = NormalizationValidator(strict=strict)

    # Auto-detect direction if needed
    if direction == "auto":
        direction = _detect_direction(raw_output, provider)

    # Handle based on direction
    for attempt in range(retries):
        try:
            if direction == "input":
                # Normalize prompt/input
                if isinstance(raw_output, str):
                    normalized = normalizer.normalize_input(raw_output)
                else:
                    # Already structured, just validate
                    normalized = raw_output

                # Validate
                if use_pydantic:
                    validated = validate_normalized_input(normalized)
                    return validated.model_dump()
                else:
                    results = validator.validate_normalized_input(normalized)
                    errors = [r for r in results if not r.passed and r.severity == 'error']
                    if errors and strict:
                        raise ValueError(f"Validation failed: {errors[0].message}")
                    return normalized

            else:  # output
                # Parse provider response
                if isinstance(raw_output, dict):
                    # Check if it's a provider-specific response or generic dict
                    detected_provider = parser._detect_provider(raw_output)
                    if detected_provider != 'generic':
                        # It's a provider response, parse it
                        parsed = parser.parse(raw_output, provider=provider)
                        normalized = normalizer.normalize_ollama_output(raw_output)
                    else:
                        # Generic dict - treat as content
                        normalized = {
                            "content": json.dumps(raw_output, sort_keys=True),
                            "provider": provider or "generic",
                            "model": "unknown",
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            "finish_reason": "stop",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                elif isinstance(raw_output, str):
                    # Check if it's JSON that we should parse
                    try:
                        parsed_json = json.loads(raw_output)
                        # It's valid JSON - wrap it
                        normalized = {
                            "content": raw_output,
                            "provider": provider or "generic",
                            "model": "unknown",
                            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                            "finish_reason": "stop",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                    except json.JSONDecodeError:
                        # Plain text response
                        normalized = normalizer.normalize_output(raw_output, provider=provider)
                else:
                    normalized = {
                        "content": str(raw_output),
                        "provider": provider or "generic",
                        "model": "unknown",
                        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                        "finish_reason": "stop",
                        "timestamp": datetime.utcnow().isoformat()
                    }

                # Validate
                if use_pydantic:
                    validated = validate_normalized_output(normalized)
                    return validated.model_dump()
                else:
                    results = validator.validate_normalized_output(normalized)
                    errors = [r for r in results if not r.passed and r.severity == 'error']
                    if errors and strict:
                        raise ValueError(f"Validation failed: {errors[0].message}")
                    return normalized

        except Exception as e:
            if attempt == retries - 1:
                if strict:
                    raise
                # Best effort fallback
                return {
                    "_raw": raw_output,
                    "_error": str(e),
                    "_note": "full validation failed, returning raw",
                    "_timestamp": datetime.utcnow().isoformat()
                }
            # Retry with next attempt
            continue

    # Should not reach here
    return {"_raw": raw_output}


def _detect_direction(data: Any, provider: Optional[str]) -> Literal["input", "output"]:
    """
    Auto-detect whether data is input (prompt) or output (response).

    Heuristics:
    - Has provider-specific response structure → output
    - Has 'direction' field → use that
    - Has 'response'/'choices'/'content' array → output
    - Otherwise → input
    """
    if isinstance(data, dict):
        # Check explicit direction field
        if 'direction' in data:
            return data['direction']

        # Check for provider response patterns
        if 'choices' in data:  # OpenAI
            return "output"
        if 'content' in data and isinstance(data['content'], list):  # Anthropic
            return "output"
        if 'response' in data and 'done' in data:  # Ollama
            return "output"
        if 'model' in data and ('usage' in data or 'finish_reason' in data):
            return "output"

    # Default to input for plain strings or unclear structure
    return "input"


# Convenience functions

def normalize_input(prompt: str, full_validation: bool = True, **kwargs) -> dict:
    """
    Normalize a prompt for sending to an LLM.

    Defaults to full_validation=True because prompts are typically plain text,
    not JSON.
    """
    return normalize(prompt, direction="input", full_validation=full_validation, **kwargs)


def normalize_output(response: Union[str, dict], provider: Optional[str] = None, full_validation: bool = True, **kwargs) -> dict:
    """
    Normalize a response from an LLM.

    Defaults to full_validation=True for provider-specific parsing.
    """
    return normalize(response, direction="output", provider=provider, full_validation=full_validation, **kwargs)


def normalize_auto(data: Union[str, dict], **kwargs) -> dict:
    """Normalize data with automatic direction detection."""
    return normalize(data, direction="auto", **kwargs)
