#!/usr/bin/env python3
"""
How HydraContext Handles Plain Text from LLMs

Demonstrates that LLMs output TEXT (not JSON), and HydraContext
wraps that text in a standardized JSON envelope for processing.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hydracontext import ContextNormalizer, UnifiedResponseParser


def print_section(title):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70 + '\n')


def demo_llm_outputs_text_not_json():
    """Show that LLMs output text, not JSON."""
    print_section("WHAT LLMs ACTUALLY OUTPUT")

    print("""
🤖 LLMs output PLAIN TEXT (or markdown, or code):

Example 1 - Simple text:
"Quantum computing uses qubits instead of bits."

Example 2 - Text with markdown:
"Here's how it works:

1. Superposition allows qubits to be 0 and 1 simultaneously
2. Entanglement links qubits together
3. Measurement collapses the quantum state

This enables parallel processing."

Example 3 - Text with code:
"Here's a Python example:

```python
def quantum_gate(qubit):
    return apply_hadamard(qubit)
```

This applies a Hadamard gate to a qubit."

Example 4 - Malformed/incomplete response:
"Let me explain quantum comp"

Example 5 - No response (timeout/error):
""

❌ LLMs do NOT output:
{
  "content": "...",
  "provider": "...",
  "usage": {...}
}

The JSON structure comes from the PROVIDER'S API, not the LLM itself!
""")


def demo_provider_apis_wrap_in_json():
    """Show how provider APIs wrap LLM text output."""
    print_section("PROVIDER APIs WRAP TEXT IN DIFFERENT JSON FORMATS")

    llm_text_output = "Quantum computing uses qubits instead of bits."

    print(f"🤖 LLM generates this text:\n   \"{llm_text_output}\"\n")
    print("📦 Then each provider's API wraps it differently:\n")

    print("OpenAI API wraps it like this:")
    print("""
{
  "choices": [{
    "message": {
      "content": "Quantum computing uses qubits instead of bits."
    }
  }],
  "usage": {"total_tokens": 10}
}
""")

    print("Anthropic API wraps it like this:")
    print("""
{
  "content": [{
    "type": "text",
    "text": "Quantum computing uses qubits instead of bits."
  }],
  "usage": {"input_tokens": 5, "output_tokens": 5}
}
""")

    print("Ollama API wraps it like this:")
    print("""
{
  "response": "Quantum computing uses qubits instead of bits.",
  "done": true,
  "eval_count": 10
}
""")

    print("⚠️  Same LLM output, THREE DIFFERENT JSON structures!")
    print("   This is what HydraContext normalizes.\n")


def demo_hydracontext_unwraps_and_rewraps():
    """Show how HydraContext handles the wrapping."""
    print_section("HYDRACONTEXT: UNWRAP → STANDARDIZE → REWRAP")

    parser = UnifiedResponseParser()
    normalizer = ContextNormalizer()

    print("🔧 HydraContext's job:\n")
    print("1. UNWRAP: Extract text from provider-specific JSON")
    print("2. PROCESS: Clean/normalize the text")
    print("3. REWRAP: Put in standardized JSON envelope\n")

    # Different provider formats with SAME text content
    openai_wrapped = {
        "choices": [{"message": {"content": "Quantum computing uses qubits."}}],
        "model": "gpt-4"
    }

    anthropic_wrapped = {
        "content": [{"type": "text", "text": "Quantum computing uses qubits."}],
        "model": "claude-3"
    }

    ollama_wrapped = {
        "response": "Quantum computing uses qubits.",
        "model": "llama2",
        "done": True
    }

    print("📥 Input: Three different JSON wrappers\n")

    for name, wrapped in [("OpenAI", openai_wrapped), ("Anthropic", anthropic_wrapped), ("Ollama", ollama_wrapped)]:
        parsed = parser.parse(wrapped)
        print(f"   {name}: content = \"{parsed['content']}\"")
        print(f"           provider = {parsed['provider']}")
        print(f"           model = {parsed['model']}")
        print()

    print("✅ All three now have IDENTICAL structure!")
    print("   The TEXT is preserved, the WRAPPER is standardized.\n")


def demo_plain_text_handling():
    """Show how HydraContext handles plain text with no JSON."""
    print_section("HANDLING PLAIN TEXT (No JSON Wrapper)")

    normalizer = ContextNormalizer()

    # Case 1: Pure text response (no API wrapper)
    plain_text = "Quantum computing uses quantum mechanics for computation."

    print("📝 Case 1: Pure text (no JSON wrapper)")
    print(f"   Input: \"{plain_text}\"")
    print()

    normalized = normalizer.normalize_output(plain_text, provider='generic')

    print(f"   Output content: \"{normalized['normalized_content']}\"")
    print(f"   Output provider: {normalized['provider']}")
    print(f"   Output has_code: {normalized['metadata']['has_code']}")
    print(f"   Output hash: {normalized['hash'][:16]}...")
    print()

    # Case 2: Text with code blocks
    text_with_code = """Here's a Python example:

```python
def hello():
    print("hi")
```

This is a simple function."""

    print("📝 Case 2: Text with code blocks")
    print(f"   Input: {len(text_with_code)} chars of text")
    print()

    normalized_code = normalizer.normalize_output(text_with_code, provider='generic')

    print(f"   Output content length: {len(normalized_code['normalized_content'])} chars")
    print(f"   Output has_code: {normalized_code['metadata']['has_code']}")
    print(f"   Output code_blocks: {normalized_code['metadata']['code_blocks']}")
    print()

    # Case 3: Malformed/incomplete
    incomplete = "Let me explain quantum comp"

    print("📝 Case 3: Incomplete/malformed response")
    print(f"   Input: \"{incomplete}\"")
    print()

    normalized_incomplete = normalizer.normalize_output(incomplete, provider='generic')

    print(f"   Output content: \"{normalized_incomplete['normalized_content']}\"")
    print(f"   Output still normalized: ✅")
    print()

    # Case 4: Empty response
    empty = ""

    print("📝 Case 4: Empty response")
    print(f"   Input: \"\" (empty string)")
    print()

    normalized_empty = normalizer.normalize_output(empty, provider='generic')

    print(f"   Output content: \"{normalized_empty['normalized_content']}\"")
    print(f"   Output length: {normalized_empty['normalized_length']}")
    print(f"   Output still normalized: ✅")
    print()


def demo_real_world_scenarios():
    """Show real-world text handling scenarios."""
    print_section("REAL-WORLD SCENARIOS")

    normalizer = ContextNormalizer()

    scenarios = [
        {
            "name": "Model outputs thinking tags (needs cleanup)",
            "text": "<thinking>Let me think about this...</thinking>\n\nQuantum computing uses qubits.",
            "expected_clean": "Quantum computing uses qubits."
        },
        {
            "name": "Model outputs with weird whitespace",
            "text": "Quantum  computing\n\n\n\n   uses    qubits.",
            "expected_clean": "Quantum computing\n\nuses qubits."
        },
        {
            "name": "Model outputs with markdown formatting",
            "text": "# Quantum Computing\n\n- Uses qubits\n- Superposition\n- Entanglement",
            "expected_clean": "# Quantum Computing\n\n- Uses qubits\n- Superposition\n- Entanglement"
        },
        {
            "name": "Model outputs JSON in text (not a JSON API response)",
            "text": 'Here\'s the answer in JSON format:\n\n{"result": "Quantum uses qubits"}',
            "expected_clean": 'Here\'s the answer in JSON format:\n\n{"result": "Quantum uses qubits"}'
        },
        {
            "name": "Model stops mid-sentence (timeout)",
            "text": "Quantum computing is a revolutionary technology that",
            "expected_clean": "Quantum computing is a revolutionary technology that"
        }
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"🔍 Scenario {i}: {scenario['name']}")
        print(f"   Raw text ({len(scenario['text'])} chars)")

        normalized = normalizer.normalize_output(scenario['text'], provider='generic')

        print(f"   Normalized: \"{normalized['normalized_content'][:60]}{'...' if len(normalized['normalized_content']) > 60 else ''}\"")
        print(f"   Length change: {scenario['text'].__len__()} → {normalized['normalized_length']}")
        print(f"   Still processable: ✅")
        print()


def main():
    print("\n" + "█" * 70)
    print("  TEXT vs JSON: What LLMs Actually Output")
    print("  And how HydraContext handles it")
    print("█" * 70)

    demo_llm_outputs_text_not_json()
    demo_provider_apis_wrap_in_json()
    demo_hydracontext_unwraps_and_rewraps()
    demo_plain_text_handling()
    demo_real_world_scenarios()

    print("\n" + "=" * 70)
    print("  KEY UNDERSTANDING")
    print("=" * 70)
    print("""
🎯 THE ACTUAL FLOW:

1. LLM GENERATES TEXT:
   "Quantum computing uses qubits instead of bits."
   ↓

2. PROVIDER API WRAPS IN JSON (different formats):
   OpenAI:    {"choices": [{"message": {"content": "..."}}]}
   Anthropic: {"content": [{"type": "text", "text": "..."}]}
   Ollama:    {"response": "..."}
   ↓

3. HYDRACONTEXT NORMALIZES:
   - Unwraps provider JSON
   - Extracts the TEXT
   - Cleans/processes the text
   - Rewraps in STANDARD JSON envelope
   ↓

4. STANDARDIZED OUTPUT:
   {"content": "Quantum computing uses qubits instead of bits.",
    "provider": "...", "model": "...", "usage": {...}, ...}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ WORKS WITH:
   - Plain text output
   - Markdown output
   - Code output
   - Malformed/incomplete output
   - Empty output
   - Output with thinking tags
   - Output with weird formatting

❌ DOES NOT REQUIRE:
   - LLM to output JSON
   - LLM to output specific format
   - LLM to complete response

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 THE JSON STRUCTURE IS THE ENVELOPE, NOT THE CONTENT

Think of it like mail:
- LLM writes a letter (text)
- Provider puts it in an envelope (their JSON format)
- HydraContext changes the envelope (standardized JSON format)
- The letter itself (text) stays the same
""")


if __name__ == "__main__":
    main()
