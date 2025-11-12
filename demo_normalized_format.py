#!/usr/bin/env python3
"""
Demonstration of HydraContext's Normalized Format

Shows exactly what format all communications are standardized to.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hydracontext import ContextNormalizer, UnifiedResponseParser


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print('=' * 70 + '\n')


def pretty_print(obj, title=""):
    """Pretty print a dictionary."""
    if title:
        print(f"📦 {title}:")
    print(json.dumps(obj, indent=2, default=str))
    print()


def demo_input_normalization():
    """Show the standardized INPUT format."""
    print_section("INPUT NORMALIZATION FORMAT")

    normalizer = ContextNormalizer()

    # Example 1: Simple prompt
    prompt = "Explain quantum computing in simple terms"
    normalized = normalizer.normalize_input(prompt)

    print("🔹 Example 1: Simple Prompt")
    print(f"   Raw: \"{prompt}\"")
    print()
    pretty_print(normalized, "Normalized INPUT Format")

    # Example 2: Longer prompt with code
    code_prompt = """
    Here's my Python code:

    ```python
    def calculate(x, y):
        return x + y
    ```

    Please explain what this does and suggest improvements.
    """

    normalized_code = normalizer.normalize_input(code_prompt)

    print("🔹 Example 2: Prompt with Code")
    print(f"   Raw length: {len(code_prompt)} chars")
    print()
    pretty_print(normalized_code, "Normalized INPUT Format")


def demo_output_normalization():
    """Show the standardized OUTPUT format."""
    print_section("OUTPUT NORMALIZATION FORMAT")

    normalizer = ContextNormalizer()

    # Example 1: OpenAI response
    openai_response = {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-4",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Quantum computing uses quantum mechanics principles like superposition and entanglement."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 9,
            "completion_tokens": 12,
            "total_tokens": 21
        }
    }

    print("🔹 Example 1: OpenAI Response")
    print("   Raw OpenAI Format:")
    print(json.dumps(openai_response, indent=2)[:200] + "...")
    print()

    normalized_openai = normalizer.normalize_ollama_output(openai_response)
    pretty_print(normalized_openai, "Normalized OUTPUT Format")

    # Example 2: Anthropic response
    anthropic_response = {
        "id": "msg_013Zva2CMHLNnXjNJJKqJ2EF",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "Quantum computing leverages quantum mechanics for computation."
            }
        ],
        "model": "claude-3-opus-20240229",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 25
        }
    }

    print("🔹 Example 2: Anthropic Response")
    print("   Raw Anthropic Format:")
    print(json.dumps(anthropic_response, indent=2)[:200] + "...")
    print()

    normalized_anthropic = normalizer.normalize_ollama_output(anthropic_response)
    pretty_print(normalized_anthropic, "Normalized OUTPUT Format")

    # Example 3: Ollama response
    ollama_response = {
        "model": "llama2",
        "created_at": "2023-08-04T19:22:45.499127Z",
        "response": "Quantum computing uses qubits instead of classical bits.",
        "done": True,
        "total_duration": 4883583458,
        "prompt_eval_count": 26,
        "eval_count": 282
    }

    print("🔹 Example 3: Ollama Response")
    print("   Raw Ollama Format:")
    print(json.dumps(ollama_response, indent=2)[:200] + "...")
    print()

    normalized_ollama = normalizer.normalize_ollama_output(ollama_response)
    pretty_print(normalized_ollama, "Normalized OUTPUT Format")


def demo_unified_standard():
    """Show the unified standard that all responses conform to."""
    print_section("UNIFIED STANDARD FORMAT")

    print("""
All responses from different providers are normalized to this structure:

📋 STANDARD OUTPUT FORMAT:
{
  // Core content (what you actually need)
  "content": str,              // The actual response text (cleaned)
  "provider": str,             // Provider name (openai/anthropic/ollama)
  "model": str,                // Model name

  // Token usage (normalized across providers)
  "usage": {
    "prompt_tokens": int,
    "completion_tokens": int,
    "total_tokens": int
  },

  // Generation metadata
  "finish_reason": str,        // Why generation stopped
  "timestamp": str,            // ISO format timestamp

  // Content metadata
  "content_metadata": {
    "has_code": bool,          // Contains code blocks?
    "code_blocks": int,        // Number of code blocks
    "has_lists": bool,         // Contains markdown lists?
    "has_headings": bool,      // Contains markdown headings?
    "line_count": int,         // Number of lines
    "paragraph_count": int     // Number of paragraphs
  },

  // Deduplication
  "hash": str,                 // Content hash for dedup

  // Provider-specific extras (optional)
  "metadata": dict             // Original provider-specific fields
}

📋 STANDARD INPUT FORMAT:
{
  // Core content
  "content": str,              // Normalized prompt text
  "type": str,                 // Prompt type (code/conversation/instruction)
  "direction": "input",        // Direction indicator

  // Token estimation
  "token_estimate": int,       // Estimated tokens

  // Segmentation (if prompt is long)
  "segments": [
    {
      "content": str,
      "type": str,
      "token_estimate": int,
      "segment_id": int
    }
  ]
}
""")


def demo_cross_provider_consistency():
    """Show that all providers produce the same structure."""
    print_section("CROSS-PROVIDER CONSISTENCY")

    parser = UnifiedResponseParser()

    # Three different provider formats
    responses = {
        "OpenAI": {
            "choices": [{"message": {"content": "Hello from OpenAI"}}],
            "model": "gpt-4",
            "usage": {"total_tokens": 10}
        },
        "Anthropic": {
            "content": [{"type": "text", "text": "Hello from Anthropic"}],
            "model": "claude-3",
            "usage": {"input_tokens": 5, "output_tokens": 5}
        },
        "Ollama": {
            "response": "Hello from Ollama",
            "model": "llama2",
            "done": True,
            "eval_count": 10
        }
    }

    print("🔍 All three providers normalized to same structure:\n")

    for provider_name, raw_response in responses.items():
        normalized = parser.parse(raw_response)

        # Show only the key fields for comparison
        comparison = {
            "content": normalized["content"],
            "provider": normalized["provider"],
            "model": normalized["model"],
            "usage": normalized["usage"]
        }

        print(f"   {provider_name}:")
        print(f"   {json.dumps(comparison, indent=6)}")
        print()

    print("✅ Notice: All have the same keys (content, provider, model, usage)")
    print("   despite different raw formats!")


def main():
    """Run all demonstrations."""
    print("\n" + "█" * 70)
    print("  HYDRACONTEXT NORMALIZED FORMAT DEMONSTRATION")
    print("  Showing exactly what 'normalized' means")
    print("█" * 70)

    demo_input_normalization()
    demo_output_normalization()
    demo_unified_standard()
    demo_cross_provider_consistency()

    print("\n" + "=" * 70)
    print("  KEY TAKEAWAYS")
    print("=" * 70)
    print("""
1. INPUT NORMALIZATION:
   - Cleans whitespace and formatting
   - Classifies prompt type (code/conversation/instruction)
   - Estimates tokens
   - Segments long prompts
   - Returns: {content, type, token_estimate, segments, direction}

2. OUTPUT NORMALIZATION:
   - Extracts content from provider-specific formats
   - Normalizes token usage across providers
   - Adds content metadata (has_code, line_count, etc.)
   - Generates hash for deduplication
   - Returns: {content, provider, model, usage, metadata, hash}

3. UNIFIED STANDARD:
   - All providers → same keys and structure
   - OpenAI, Anthropic, Ollama all become identical format
   - Easy to chain models: output of Model A → input to Model B
   - No information loss during normalization

4. BENEFITS:
   - Write code once, works with any provider
   - Switch providers without changing code
   - Chain models from different providers seamlessly
   - Compare outputs across providers easily
   - Deduplicate responses regardless of source
""")

    print("\n✅ Normalization = Standardized JSON structure across all providers")
    print()


if __name__ == "__main__":
    main()
