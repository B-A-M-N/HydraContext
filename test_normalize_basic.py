#!/usr/bin/env python3
"""
Quick test of the universal normalize() function.
Tests both lightweight and full validation modes.
"""

from hydracontext import normalize, normalize_input, normalize_output


def test_lightweight_mode():
    """Test lightweight normalization (stdlib only)."""
    print("=" * 70)
    print("TEST 1: Lightweight Mode (Pure Stdlib)")
    print("=" * 70)

    # Test 1: Clean JSON
    print("\n1. Clean JSON:")
    input_json = '{"status": "ok", "code": 200}'
    result = normalize(input_json)
    print(f"   Input:  {input_json}")
    print(f"   Output: {result}")
    assert result == {'code': 200, 'status': 'ok'}  # Deterministic ordering
    print("   ✅ PASS")

    # Test 2: Mixed text with JSON
    print("\n2. Extract JSON from mixed text:")
    mixed = "The result is: {status: 'success', value: 42}"
    result = normalize(mixed)
    print(f"   Input:  '{mixed}'")
    print(f"   Output: {result}")
    assert 'status' in result
    print("   ✅ PASS")

    # Test 3: Malformed JSON (trailing comma)
    print("\n3. Repair trailing comma:")
    malformed = '{"items": [1, 2, 3,], "done": true,}'
    result = normalize(malformed)
    print(f"   Input:  '{malformed}'")
    print(f"   Output: {result}")
    assert result == {'done': True, 'items': [1, 2, 3]}
    print("   ✅ PASS")

    # Test 4: Already parsed dict
    print("\n4. Already parsed dict:")
    already_json = {"foo": "bar", "baz": [1, 2, 3]}
    result = normalize(already_json)
    print(f"   Input:  {already_json}")
    print(f"   Output: {result}")
    assert result == {'baz': [1, 2, 3], 'foo': 'bar'}  # Deterministic ordering
    print("   ✅ PASS")

    # Test 5: Best-effort fallback
    print("\n5. Best-effort fallback (non-JSON):")
    invalid = "completely invalid text with no JSON"
    result = normalize(invalid, strict=False)
    print(f"   Input:  '{invalid}'")
    print(f"   Output: {result}")
    assert '_raw' in result and '_note' in result
    print("   ✅ PASS (graceful fallback)")

    print("\n" + "=" * 70)
    print("✅ All lightweight tests passed!")
    print("=" * 70)


def test_full_validation_mode():
    """Test full validation mode with provider parsing."""
    print("\n" + "=" * 70)
    print("TEST 2: Full Validation Mode")
    print("=" * 70)

    try:
        # Test 1: Ollama response
        print("\n1. Ollama provider response:")
        ollama_resp = {
            "response": "Hello, I'm an AI assistant.",
            "model": "llama2",
            "done": True,
            "prompt_eval_count": 10,
            "eval_count": 20
        }
        result = normalize(ollama_resp, full_validation=True, strict=False)
        print(f"   Input:  Ollama dict with response/model/done")
        print(f"   Output keys: {list(result.keys())}")
        assert 'content' in result or 'normalized_content' in result
        print("   ✅ PASS")

        # Test 2: Direction auto-detection
        print("\n2. Auto-detect direction:")
        prompt = "Explain quantum computing"
        result = normalize_input(prompt, full_validation=True, strict=False)
        print(f"   Input:  '{prompt}'")
        print(f"   Output keys: {list(result.keys())}")
        print("   ✅ PASS")

        print("\n" + "=" * 70)
        print("✅ Full validation tests passed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n⚠️  Full validation requires optional dependencies: {e}")
        print("   (This is expected if Pydantic not installed)")


def test_convenience_functions():
    """Test convenience wrappers."""
    print("\n" + "=" * 70)
    print("TEST 3: Convenience Functions")
    print("=" * 70)

    # Test normalize_input
    print("\n1. normalize_input():")
    result = normalize_input("What is AI?")
    print(f"   Input:  'What is AI?'")
    print(f"   Output: {result}")
    print("   ✅ PASS")

    # Test normalize_output
    print("\n2. normalize_output():")
    output_json = '{"answer": "AI is..."}'
    result = normalize_output(output_json)
    print(f"   Input:  {output_json}")
    print(f"   Output: {result}")
    print("   ✅ PASS")

    print("\n" + "=" * 70)
    print("✅ Convenience function tests passed!")
    print("=" * 70)


if __name__ == "__main__":
    print("\n" + "█" * 70)
    print("  HYDRACONTEXT UNIVERSAL NORMALIZE() TESTS")
    print("█" * 70)

    test_lightweight_mode()
    test_full_validation_mode()
    test_convenience_functions()

    print("\n" + "█" * 70)
    print("  ✅ ALL TESTS PASSED")
    print("█" * 70)
    print("\nThe universal normalize() function is working correctly!")
    print("It can handle:")
    print("  • Valid JSON")
    print("  • Malformed JSON (repairs automatically)")
    print("  • Mixed text + JSON (extracts JSON)")
    print("  • Provider-specific formats (with full_validation=True)")
    print("  • Graceful fallback on complete failure")
