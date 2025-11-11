#!/usr/bin/env python3
"""
Test HydraContext on REAL codebases to verify actual deduplication rates.
This provides data-backed claims for the README.
"""

import sys
import os
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))

from hydracontext import ContentDeduplicator, ContextSegmenter


def analyze_codebase(repo_path: Path, file_extensions=None):
    """Analyze a real codebase for duplication."""
    if file_extensions is None:
        file_extensions = ['.py', '.js', '.ts', '.md', '.txt', '.json']

    print(f"\n{'=' * 70}")
    print(f"Analyzing: {repo_path.name}")
    print(f"{'=' * 70}")

    # Collect all files
    all_files = []
    for ext in file_extensions:
        all_files.extend(repo_path.rglob(f'*{ext}'))

    # Filter out common ignore patterns
    ignore_patterns = [
        'node_modules', '__pycache__', '.git', 'venv', 'env',
        '.pytest_cache', 'dist', 'build', '.egg-info'
    ]

    files = [
        f for f in all_files
        if not any(pattern in str(f) for pattern in ignore_patterns)
    ]

    if not files:
        print(f"  ⚠ No files found")
        return None

    print(f"\n📁 Files found: {len(files)}")

    # Read all content
    all_content = []
    total_size = 0
    read_errors = 0

    for file in files:
        try:
            content = file.read_text(encoding='utf-8', errors='ignore')
            all_content.append(content)
            total_size += len(content)
        except Exception as e:
            read_errors += 1

    if read_errors > 0:
        print(f"  ⚠ Could not read {read_errors} files")

    if not all_content:
        print(f"  ⚠ No content to analyze")
        return None

    print(f"📊 Total content: {total_size:,} bytes ({total_size / 1024 / 1024:.2f} MB)")

    # Test 1: Line-level deduplication (like for prompts)
    print(f"\n🔍 TEST 1: Line-Level Deduplication (Prompt Scenario)")
    print(f"  Simulates: Chat logs, prompts, code comments")

    dedup_lines = ContentDeduplicator()
    all_lines = []
    for content in all_content:
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        all_lines.extend(lines)

    total_lines = len(all_lines)
    unique_lines = []

    for line in all_lines:
        if not dedup_lines.is_duplicate(line, record=True):
            unique_lines.append(line)

    stats_lines = dedup_lines.get_statistics()
    line_dedup_ratio = stats_lines['dedup_ratio']

    print(f"  Total lines: {total_lines:,}")
    print(f"  Unique lines: {len(unique_lines):,}")
    print(f"  Duplicates: {total_lines - len(unique_lines):,}")
    print(f"  ✅ Deduplication rate: {line_dedup_ratio:.1%}")

    # Test 2: Segment-level deduplication (like for documents)
    print(f"\n🔍 TEST 2: Segment-Level Deduplication (Document Scenario)")
    print(f"  Simulates: Document chunks, paragraphs, code blocks")

    segmenter = ContextSegmenter()
    dedup_segments = ContentDeduplicator()

    all_segments = []
    for content in all_content[:50]:  # Limit to first 50 files for speed
        try:
            segments = segmenter.segment_text(content, granularity='sentence')
            all_segments.extend(segments)
        except:
            pass

    total_segments = len(all_segments)
    unique_segments = []

    for seg in all_segments:
        if not dedup_segments.is_duplicate(seg.text, record=True):
            unique_segments.append(seg)

    stats_segments = dedup_segments.get_statistics()
    segment_dedup_ratio = stats_segments['dedup_ratio']

    print(f"  Total segments: {total_segments:,}")
    print(f"  Unique segments: {len(unique_segments):,}")
    print(f"  Duplicates: {total_segments - len(unique_segments):,}")
    print(f"  ✅ Deduplication rate: {segment_dedup_ratio:.1%}")

    # Test 3: Function/Block level deduplication
    print(f"\n🔍 TEST 3: Block-Level Deduplication (Code Scenario)")
    print(f"  Simulates: Function definitions, import statements, common patterns")

    dedup_blocks = ContentDeduplicator()
    all_blocks = []

    for content in all_content[:50]:  # First 50 files
        # Split by double newlines (rough block detection)
        blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
        all_blocks.extend(blocks)

    total_blocks = len(all_blocks)
    unique_blocks = []

    for block in all_blocks:
        if not dedup_blocks.is_duplicate(block, record=True):
            unique_blocks.append(block)

    stats_blocks = dedup_blocks.get_statistics()
    block_dedup_ratio = stats_blocks['dedup_ratio']

    print(f"  Total blocks: {total_blocks:,}")
    print(f"  Unique blocks: {len(unique_blocks):,}")
    print(f"  Duplicates: {total_blocks - len(unique_blocks):,}")
    print(f"  ✅ Deduplication rate: {block_dedup_ratio:.1%}")

    return {
        'repo': repo_path.name,
        'files': len(files),
        'size_bytes': total_size,
        'size_mb': total_size / 1024 / 1024,
        'line_dedup': line_dedup_ratio,
        'segment_dedup': segment_dedup_ratio,
        'block_dedup': block_dedup_ratio,
    }


def main():
    """Analyze multiple real codebases."""
    print("\n" + "█" * 70)
    print("  REAL CODEBASE DEDUPLICATION ANALYSIS")
    print("  Verifying HydraContext claims with actual data")
    print("█" * 70)

    # Find repos
    home = Path('/home/joker')
    repo_candidates = [
        'HydraContext',
        'PromptForge',
        'SOLLOL',
        'SynapticLlamas',
        'product_qa_app',
    ]

    results = []

    for repo_name in repo_candidates:
        repo_path = home / repo_name
        if repo_path.exists() and repo_path.is_dir():
            try:
                result = analyze_codebase(repo_path)
                if result:
                    results.append(result)
            except Exception as e:
                print(f"  ❌ Error analyzing {repo_name}: {e}")

    # Summary
    print("\n" + "█" * 70)
    print("  SUMMARY: Actual Deduplication Rates Across Real Codebases")
    print("█" * 70)

    if not results:
        print("\n  ⚠ No results to summarize")
        return

    print(f"\n📊 Analyzed {len(results)} repositories:")
    print(f"\n{'Repository':<25} {'Files':>8} {'Size (MB)':>10} {'Line':>8} {'Segment':>10} {'Block':>8}")
    print("─" * 70)

    total_files = 0
    total_size = 0
    line_dedup_rates = []
    segment_dedup_rates = []
    block_dedup_rates = []

    for r in results:
        print(f"{r['repo']:<25} {r['files']:>8,} {r['size_mb']:>10.2f} "
              f"{r['line_dedup']:>7.1%} {r['segment_dedup']:>9.1%} {r['block_dedup']:>7.1%}")

        total_files += r['files']
        total_size += r['size_mb']
        line_dedup_rates.append(r['line_dedup'])
        segment_dedup_rates.append(r['segment_dedup'])
        block_dedup_rates.append(r['block_dedup'])

    print("─" * 70)
    print(f"{'TOTAL':<25} {total_files:>8,} {total_size:>10.2f}")

    # Calculate averages
    avg_line = sum(line_dedup_rates) / len(line_dedup_rates)
    avg_segment = sum(segment_dedup_rates) / len(segment_dedup_rates)
    avg_block = sum(block_dedup_rates) / len(block_dedup_rates)

    print(f"\n📈 AVERAGE DEDUPLICATION RATES:")
    print(f"  Line-level (prompts):     {avg_line:.1%}")
    print(f"  Segment-level (documents): {avg_segment:.1%}")
    print(f"  Block-level (code):        {avg_block:.1%}")

    # Calculate ranges
    min_line, max_line = min(line_dedup_rates), max(line_dedup_rates)
    min_seg, max_seg = min(segment_dedup_rates), max(segment_dedup_rates)
    min_block, max_block = min(block_dedup_rates), max(block_dedup_rates)

    print(f"\n📊 RANGES:")
    print(f"  Line-level:    {min_line:.1%} - {max_line:.1%}")
    print(f"  Segment-level: {min_seg:.1%} - {max_seg:.1%}")
    print(f"  Block-level:   {min_block:.1%} - {max_block:.1%}")

    # Calculate token savings
    print(f"\n💰 TOKEN COST IMPACT (based on actual deduplication rates):")

    # Use average segment dedup (most relevant for LLM use cases)
    dedup_rate = avg_segment

    example_prompts = 100_000
    unique_prompts = example_prompts * (1 - dedup_rate)
    avg_tokens_per_prompt = 25  # Conservative estimate

    total_tokens_original = example_prompts * avg_tokens_per_prompt
    total_tokens_dedup = unique_prompts * avg_tokens_per_prompt
    tokens_saved = total_tokens_original - total_tokens_dedup

    # GPT-4 pricing
    cost_per_1k_input = 0.03
    cost_per_1k_output = 0.06

    # Assume each prompt generates 100 token response
    output_tokens_original = example_prompts * 100
    output_tokens_dedup = unique_prompts * 100

    input_cost_orig = (total_tokens_original / 1000) * cost_per_1k_input
    output_cost_orig = (output_tokens_original / 1000) * cost_per_1k_output
    total_cost_orig = input_cost_orig + output_cost_orig

    input_cost_dedup = (total_tokens_dedup / 1000) * cost_per_1k_input
    output_cost_dedup = (output_tokens_dedup / 1000) * cost_per_1k_output
    total_cost_dedup = input_cost_dedup + output_cost_dedup

    savings = total_cost_orig - total_cost_dedup
    savings_pct = (savings / total_cost_orig) * 100

    print(f"\n  Example: 100K prompts with {dedup_rate:.1%} actual deduplication")
    print(f"  Original cost:  ${total_cost_orig:.2f}")
    print(f"  With dedup:     ${total_cost_dedup:.2f}")
    print(f"  💰 SAVINGS:     ${savings:.2f} ({savings_pct:.1f}%)")

    print(f"\n✅ VERIFIED CLAIMS FOR README:")
    print(f"  Based on {len(results)} real codebases analyzing {total_files:,} files")
    print(f"  Actual deduplication rates: {min_seg:.0%}-{max_seg:.0%}")
    print(f"  Average savings: {savings_pct:.0f}%")
    print(f"  Conservative claim: {savings_pct * 0.8:.0f}-{savings_pct * 1.2:.0f}% token cost reduction")


if __name__ == "__main__":
    main()
