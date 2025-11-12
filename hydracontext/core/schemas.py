"""
Pydantic Schemas for HydraContext Normalization

Validates all normalized data structures using Pydantic models.
This ensures type safety, automatic validation, and clear error messages.
"""

from typing import Optional, Dict, Any, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum


class ProviderType(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    GENERIC = "generic"


class PromptType(str, Enum):
    """Types of prompts."""
    CODE = "code"
    CONVERSATION = "conversation"
    INSTRUCTION = "instruction"
    EXAMPLE = "example"
    SYSTEM = "system"


class UsageStats(BaseModel):
    """Token usage statistics (normalized across providers)."""
    prompt_tokens: int = Field(ge=0, description="Number of tokens in prompt")
    completion_tokens: int = Field(ge=0, description="Number of tokens in completion")
    total_tokens: int = Field(ge=0, description="Total tokens used")

    @field_validator('total_tokens')
    @classmethod
    def validate_total(cls, v, info):
        """Ensure total equals prompt + completion."""
        data = info.data
        if 'prompt_tokens' in data and 'completion_tokens' in data:
            expected = data['prompt_tokens'] + data['completion_tokens']
            if v != expected and v != 0:  # Allow 0 for missing data
                # Auto-correct if values exist
                return expected
        return v

    class Config:
        frozen = False  # Allow modification for auto-correction


class ContentMetadata(BaseModel):
    """Metadata about content structure."""
    has_code: bool = Field(default=False, description="Contains code blocks")
    code_blocks: int = Field(default=0, ge=0, description="Number of code blocks")
    has_lists: bool = Field(default=False, description="Contains markdown lists")
    has_headings: bool = Field(default=False, description="Contains markdown headings")
    line_count: int = Field(default=0, ge=0, description="Number of lines")
    paragraph_count: int = Field(default=0, ge=0, description="Number of paragraphs")

    class Config:
        frozen = True


class PromptSegment(BaseModel):
    """A segment of a prompt (for long prompts)."""
    id: str = Field(description="Unique segment identifier")
    prompt_id: str = Field(description="Parent prompt identifier")
    segment_index: int = Field(ge=0, description="Segment index")
    type: PromptType = Field(description="Prompt type")
    normalized: bool = Field(default=True, description="Whether content is normalized")
    content: str = Field(min_length=0, description="Segment content")
    length: int = Field(ge=0, description="Content length in characters")
    hash: str = Field(min_length=32, description="Content hash for deduplication")
    duplicate: bool = Field(default=False, description="Whether this is a duplicate")
    token_estimate: int = Field(ge=0, description="Estimated token count")
    timestamp: str = Field(description="ISO format timestamp")
    code_blocks: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detected code blocks")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")

    @field_validator('length')
    @classmethod
    def validate_length_matches_content(cls, v, info):
        """Ensure length matches actual content length."""
        if 'content' in info.data:
            actual_length = len(info.data['content'])
            if v != actual_length:
                # Auto-correct to actual length
                return actual_length
        return v

    class Config:
        frozen = False  # Allow modification


class NormalizedInput(BaseModel):
    """
    Normalized input (prompt) format.

    This is the standardized format for all prompts going TO the LLM.
    """
    content: str = Field(description="Normalized prompt text")
    type: PromptType = Field(description="Prompt type classification")
    token_estimate: int = Field(ge=0, description="Estimated token count")
    direction: Literal["input"] = Field(default="input", description="Direction indicator")
    segments: List[PromptSegment] = Field(default_factory=list, description="Prompt segments")

    @field_validator('segments')
    @classmethod
    def validate_segments_not_empty(cls, v):
        """Ensure segments list is not empty."""
        if not v:
            raise ValueError("Segments list cannot be empty")
        return v

    class Config:
        frozen = False


class NormalizedOutput(BaseModel):
    """
    Normalized output (response) format.

    This is the standardized format for all responses FROM the LLM.
    """
    content: str = Field(description="Normalized response text")
    provider: ProviderType = Field(description="LLM provider name")
    model: str = Field(min_length=1, description="Model name")
    usage: UsageStats = Field(description="Token usage statistics")
    finish_reason: str = Field(description="Why generation stopped")
    timestamp: str = Field(description="ISO format timestamp")
    direction: Literal["output"] = Field(default="output", description="Direction indicator")

    # Optional fields
    content_metadata: Optional[ContentMetadata] = Field(default=None, description="Content structure metadata")
    hash: Optional[str] = Field(default=None, description="Content hash for deduplication")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Provider-specific metadata")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")

    @field_validator('content')
    @classmethod
    def validate_content_not_none(cls, v):
        """Ensure content is not None."""
        if v is None:
            raise ValueError("Content cannot be None")
        return v

    class Config:
        frozen = False


class OllamaMetadata(BaseModel):
    """Ollama-specific metadata."""
    model: str = Field(description="Model name")
    done: bool = Field(default=True, description="Generation complete")
    total_duration: Optional[int] = Field(default=None, ge=0, description="Total duration in nanoseconds")
    load_duration: Optional[int] = Field(default=None, ge=0, description="Load duration in nanoseconds")
    prompt_eval_count: Optional[int] = Field(default=None, ge=0, description="Prompt tokens evaluated")
    eval_count: Optional[int] = Field(default=None, ge=0, description="Response tokens generated")
    context: Optional[List[int]] = Field(default=None, description="Context window state")

    class Config:
        frozen = True


class ExtendedNormalizedOutput(NormalizedOutput):
    """Extended output format with provider-specific fields."""
    ollama_metadata: Optional[OllamaMetadata] = Field(default=None, description="Ollama-specific metadata")
    original_content: Optional[str] = Field(default=None, description="Original response before normalization")
    original_length: Optional[int] = Field(default=None, ge=0, description="Original content length")
    normalized_length: Optional[int] = Field(default=None, ge=0, description="Normalized content length")
    reduction_ratio: Optional[float] = Field(default=None, ge=0, le=1, description="Reduction ratio from normalization")

    class Config:
        frozen = False


class FidelityCheck(BaseModel):
    """Result of a fidelity check."""
    original_length: int = Field(ge=0, description="Original text length")
    normalized_length: int = Field(ge=0, description="Normalized text length")
    content_preserved: bool = Field(description="Whether content exists")
    semantic_preserved: bool = Field(description="Whether meaning is preserved")
    structure_preserved: bool = Field(description="Whether structure is preserved")
    fidelity_score: float = Field(ge=0.0, le=1.0, description="Overall fidelity score (0-1)")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Ensure timestamp is valid ISO format."""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")

    class Config:
        frozen = True


class ValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(description="Field that failed validation")
    error: str = Field(description="Error message")
    value: Optional[Any] = Field(default=None, description="Invalid value")
    expected: Optional[str] = Field(default=None, description="Expected format")

    class Config:
        frozen = True


# Helper functions

def validate_normalized_input(data: Dict[str, Any]) -> NormalizedInput:
    """
    Validate and parse normalized input data.

    Args:
        data: Dictionary to validate

    Returns:
        Validated NormalizedInput model

    Raises:
        ValidationError: If data is invalid
    """
    return NormalizedInput.model_validate(data)


def validate_normalized_output(data: Dict[str, Any]) -> NormalizedOutput:
    """
    Validate and parse normalized output data.

    Args:
        data: Dictionary to validate

    Returns:
        Validated NormalizedOutput model

    Raises:
        ValidationError: If data is invalid
    """
    return NormalizedOutput.model_validate(data)


def validate_extended_output(data: Dict[str, Any]) -> ExtendedNormalizedOutput:
    """
    Validate and parse extended normalized output data.

    Args:
        data: Dictionary to validate

    Returns:
        Validated ExtendedNormalizedOutput model

    Raises:
        ValidationError: If data is invalid
    """
    return ExtendedNormalizedOutput.model_validate(data)


def safe_validate(
    data: Dict[str, Any],
    model_class: type[BaseModel]
) -> tuple[Optional[BaseModel], List[ValidationError]]:
    """
    Safely validate data without raising exceptions.

    Args:
        data: Dictionary to validate
        model_class: Pydantic model class to validate against

    Returns:
        Tuple of (validated_model or None, list of validation errors)
    """
    try:
        validated = model_class.model_validate(data)
        return validated, []
    except Exception as e:
        errors = []
        if hasattr(e, 'errors'):
            for err in e.errors():
                errors.append(ValidationError(
                    field='.'.join(str(x) for x in err['loc']),
                    error=err['msg'],
                    value=err.get('input'),
                    expected=err.get('type')
                ))
        else:
            errors.append(ValidationError(
                field='unknown',
                error=str(e),
                value=None,
                expected=None
            ))
        return None, errors


# Export all schemas
__all__ = [
    'ProviderType',
    'PromptType',
    'UsageStats',
    'ContentMetadata',
    'PromptSegment',
    'NormalizedInput',
    'NormalizedOutput',
    'ExtendedNormalizedOutput',
    'OllamaMetadata',
    'FidelityCheck',
    'ValidationError',
    'validate_normalized_input',
    'validate_normalized_output',
    'validate_extended_output',
    'safe_validate',
]
