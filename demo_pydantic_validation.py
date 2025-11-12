#!/usr/bin/env python3
"""
Demonstration of Pydantic Validation for HydraContext

Shows how Pydantic automatically validates normalized data structures,
ensuring type safety and information fidelity.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    from hydracontext.core.schemas import (
        NormalizedInput,
        NormalizedOutput,
        ExtendedNormalizedOutput,
        validate_normalized_input,
        validate_normalized_output,
        safe_validate,
        UsageStats
    )
except ImportError:
    print("⚠️  Pydantic not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pydantic"])
    from hydracontext.core.schemas import (
        NormalizedInput,
        NormalizedOutput,
        ExtendedNormalizedOutput,
        validate_normalized_input,
        validate_normalized_output,
        safe_validate,
        UsageStats
    )


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70 + '\n')


def demo_valid_output():
    """Show validation of valid normalized output."""
    print_section("✅ VALID OUTPUT VALIDATION")

    valid_output = {
        "content": "Quantum computing uses qubits instead of bits.",
        "provider": "ollama",
        "model": "llama2",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 25
        },
        "finish_reason": "stop",
        "timestamp": "2025-11-11T17:00:00",
        "direction": "output"
    }

    print("📥 Input data:")
    print(f"   {valid_output}\n")

    try:
        validated = validate_normalized_output(valid_output)
        print("✅ Validation PASSED!")
        print(f"   Content: {validated.content[:50]}...")
        print(f"   Provider: {validated.provider}")
        print(f"   Model: {validated.model}")
        print(f"   Total tokens: {validated.usage.total_tokens}")
        print(f"   Type: {type(validated).__name__}")

        # Pydantic gives us type-safe access
        print(f"\n   🔒 Type-safe access:")
        print(f"      validated.usage.total_tokens = {validated.usage.total_tokens} (guaranteed int)")
        print(f"      validated.provider.value = {validated.provider.value} (guaranteed enum)")

    except Exception as e:
        print(f"❌ Validation FAILED: {e}")


def demo_invalid_output():
    """Show validation catching errors."""
    print_section("❌ INVALID OUTPUT VALIDATION")

    invalid_outputs = [
        {
            "name": "Missing required field",
            "data": {
                "content": "Test",
                "provider": "ollama",
                # Missing 'model', 'usage', 'finish_reason', 'timestamp'
            }
        },
        {
            "name": "Wrong type (provider)",
            "data": {
                "content": "Test",
                "provider": "invalid_provider",  # Not in enum
                "model": "test",
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
                "finish_reason": "stop",
                "timestamp": "2025-11-11T17:00:00",
                "direction": "output"
            }
        },
        {
            "name": "Negative token count",
            "data": {
                "content": "Test",
                "provider": "ollama",
                "model": "test",
                "usage": {"prompt_tokens": -5, "completion_tokens": 10, "total_tokens": 5},
                "finish_reason": "stop",
                "timestamp": "2025-11-11T17:00:00",
                "direction": "output"
            }
        },
        {
            "name": "None content (data loss!)",
            "data": {
                "content": None,  # Data loss!
                "provider": "ollama",
                "model": "test",
                "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
                "finish_reason": "stop",
                "timestamp": "2025-11-11T17:00:00",
                "direction": "output"
            }
        }
    ]

    for test in invalid_outputs:
        print(f"🔍 Test: {test['name']}")

        validated, errors = safe_validate(test['data'], NormalizedOutput)

        if errors:
            print(f"   ❌ Caught errors:")
            for err in errors:
                print(f"      Field '{err.field}': {err.error}")
        else:
            print(f"   ⚠️  Unexpectedly passed")
        print()


def demo_auto_correction():
    """Show Pydantic auto-correcting inconsistencies."""
    print_section("🔧 AUTO-CORRECTION")

    # Total tokens doesn't match sum
    inconsistent_data = {
        "content": "Test",
        "provider": "ollama",
        "model": "test",
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 15,
            "total_tokens": 100  # Wrong! Should be 25
        },
        "finish_reason": "stop",
        "timestamp": "2025-11-11T17:00:00",
        "direction": "output"
    }

    print("📥 Input data with inconsistent token count:")
    print(f"   prompt_tokens: 10")
    print(f"   completion_tokens: 15")
    print(f"   total_tokens: 100 (incorrect!)\n")

    validated = validate_normalized_output(inconsistent_data)

    print("✅ Pydantic auto-corrected:")
    print(f"   prompt_tokens: {validated.usage.prompt_tokens}")
    print(f"   completion_tokens: {validated.usage.completion_tokens}")
    print(f"   total_tokens: {validated.usage.total_tokens} (corrected to 25!)")


def demo_type_safety():
    """Show type safety benefits."""
    print_section("🔒 TYPE SAFETY BENEFITS")

    data = {
        "content": "Quantum computing test",
        "provider": "ollama",
        "model": "llama2",
        "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        "finish_reason": "stop",
        "timestamp": "2025-11-11T17:00:00",
        "direction": "output"
    }

    validated = validate_normalized_output(data)

    print("🔍 Without Pydantic (dict access):")
    print("   data['usage']['total_tokens']  # Could be string, None, missing")
    print("   data['provider']  # Could be any string")
    print("   data.get('content', '')  # Manual default handling\n")

    print("✅ With Pydantic (type-safe):")
    print(f"   validated.usage.total_tokens = {validated.usage.total_tokens}")
    print(f"      Type: {type(validated.usage.total_tokens).__name__} (guaranteed)")
    print(f"      Range: >= 0 (enforced)")
    print(f"\n   validated.provider = {validated.provider}")
    print(f"      Type: ProviderType enum (guaranteed)")
    print(f"      Values: {list(validated.provider.__class__)}")
    print(f"\n   validated.content = \"{validated.content[:30]}...\"")
    print(f"      Type: str (guaranteed, never None)")

    print("\n💡 IDE autocomplete works perfectly!")
    print("   validated.usage.  ← Shows: prompt_tokens, completion_tokens, total_tokens")


def demo_fidelity_check():
    """Show how validation ensures fidelity."""
    print_section("🎯 FIDELITY ASSURANCE")

    print("Pydantic validation ensures information fidelity by:\n")

    checks = [
        ("✅ Content exists", "Validates content is not None or empty"),
        ("✅ Required fields present", "All critical fields must exist"),
        ("✅ Correct types", "Provider is enum, tokens are int >= 0"),
        ("✅ Consistent data", "total_tokens = prompt + completion"),
        ("✅ Valid timestamps", "ISO format timestamps"),
        ("✅ No unexpected fields", "Extra fields can be caught (strict mode)"),
        ("✅ Nested validation", "Usage, metadata validated recursively")
    ]

    for check, description in checks:
        print(f"   {check}")
        print(f"      {description}\n")

    print("🔐 Benefits:")
    print("   • Catch data corruption immediately")
    print("   • Prevent silent failures")
    print("   • Guarantee type safety throughout codebase")
    print("   • Auto-generate JSON schemas for docs")
    print("   • Clear error messages when validation fails")


def demo_real_world_scenario():
    """Show real-world validation scenario."""
    print_section("🌍 REAL-WORLD SCENARIO")

    print("Scenario: Ollama returns malformed response\n")

    # Simulate Ollama returning unexpected format
    ollama_response = {
        "response": "Quantum computing explanation",
        "model": "llama2",
        "done": True,
        "eval_count": 50
        # Missing: prompt_eval_count, total_duration, etc.
    }

    print("📥 Raw Ollama response:")
    print(f"   {ollama_response}\n")

    # Try to normalize it
    try:
        # This would need to be wrapped to match our schema
        normalized = {
            "content": ollama_response.get("response", ""),
            "provider": "ollama",
            "model": ollama_response.get("model", "unknown"),
            "usage": {
                "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                "completion_tokens": ollama_response.get("eval_count", 0),
                "total_tokens": ollama_response.get("prompt_eval_count", 0) + ollama_response.get("eval_count", 0)
            },
            "finish_reason": "stop" if ollama_response.get("done") else "length",
            "timestamp": "2025-11-11T17:00:00",
            "direction": "output"
        }

        validated = validate_normalized_output(normalized)

        print("✅ Successfully normalized and validated!")
        print(f"   Content: {validated.content[:40]}...")
        print(f"   Provider: {validated.provider}")
        print(f"   Tokens: {validated.usage.total_tokens}")
        print("\n💡 Even with missing fields, Pydantic ensures type safety!")

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        print("   This prevents corrupted data from entering the system!")


def main():
    print("\n" + "█" * 70)
    print("  PYDANTIC VALIDATION FOR HYDRACONTEXT")
    print("  Ensuring type safety and information fidelity")
    print("█" * 70)

    demo_valid_output()
    demo_invalid_output()
    demo_auto_correction()
    demo_type_safety()
    demo_fidelity_check()
    demo_real_world_scenario()

    print("\n" + "=" * 70)
    print("  WHY PYDANTIC?")
    print("=" * 70)
    print("""
✅ BENEFITS OF PYDANTIC VALIDATION:

1. AUTOMATIC VALIDATION:
   - No manual checking of fields
   - Validates types, ranges, formats automatically
   - Clear error messages when validation fails

2. TYPE SAFETY:
   - IDE autocomplete works perfectly
   - Static type checkers (mypy) can verify correctness
   - No runtime AttributeErrors from missing fields

3. DATA INTEGRITY:
   - Guarantees no None values where they shouldn't be
   - Ensures required fields are present
   - Validates nested structures recursively

4. FIDELITY ASSURANCE:
   - Catch data corruption immediately
   - Prevent information loss (e.g., None content)
   - Auto-correct inconsistencies (e.g., token counts)

5. DEVELOPER EXPERIENCE:
   - Clean, declarative schema definitions
   - Auto-generate JSON schemas for documentation
   - Easy serialization to/from JSON
   - Standard Python type hints

6. PERFORMANCE:
   - Written in Rust (pydantic v2)
   - Faster than manual validation
   - Lazy validation possible

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COMPARISON:

❌ Manual validation:
   if 'content' not in data or data['content'] is None:
       raise ValueError("Missing content")
   if 'usage' not in data or not isinstance(data['usage'], dict):
       raise ValueError("Invalid usage")
   # ... 50 more lines of checks ...

✅ Pydantic validation:
   validated = NormalizedOutput.model_validate(data)
   # Done! All checks automatic.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 RECOMMENDATION:
   Use Pydantic schemas for ALL normalized data structures.
   This ensures maximum fidelity with minimal code.
""")


if __name__ == "__main__":
    main()
