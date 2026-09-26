#!/usr/bin/env python3
"""
CLI entry point: run the full evaluation suite against a real target model
and a real judge model, and write a Markdown report.

Usage:
    export ANTHROPIC_API_KEY=...        # or OPENAI_API_KEY
    python run_evaluation.py --target anthropic:claude-sonnet-4-6 \\
                              --judge openai:gpt-4o \\
                              --test-cases test_cases/education_prompts.yaml \\
                              --out sample_report.md

Using a DIFFERENT model family as judge than the one under test is
recommended — it reduces the risk of a model rating its own output leniently.
"""
from __future__ import annotations

import argparse
import sys

from src import EvaluationHarness, load_test_cases, report
from src.providers import AnthropicProvider, OpenAIProvider


def build_provider(spec: str):
    """spec is like 'anthropic:claude-sonnet-4-6' or 'openai:gpt-4o'."""
    try:
        vendor, model = spec.split(":", 1)
    except ValueError:
        raise SystemExit(f"Provider spec must be 'vendor:model', got: {spec!r}")

    if vendor == "anthropic":
        return AnthropicProvider(model_name=model)
    elif vendor == "openai":
        return OpenAIProvider(model_name=model)
    else:
        raise SystemExit(f"Unknown provider vendor: {vendor!r} (use 'anthropic' or 'openai')")


def main():
    parser = argparse.ArgumentParser(description="Run the LLM Evaluation & Safety Harness")
    parser.add_argument("--target", required=True, help="e.g. anthropic:claude-sonnet-4-6")
    parser.add_argument("--judge", required=True, help="e.g. openai:gpt-4o")
    parser.add_argument("--test-cases", default="test_cases/education_prompts.yaml")
    parser.add_argument("--out", default="report.md")
    args = parser.parse_args()

    target_provider = build_provider(args.target)
    judge_provider = build_provider(args.judge)

    test_cases = load_test_cases(args.test_cases)
    print(f"Loaded {len(test_cases)} test cases from {args.test_cases}")

    harness = EvaluationHarness(target_provider, judge_provider)

    print(f"Running against target={target_provider.model_name}, judge={judge_provider.model_name}...")
    eval_report = harness.run_suite(test_cases)

    markdown = report.render_markdown(eval_report)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(markdown)

    print(f"\n{eval_report.passed_count}/{eval_report.total} passed ({eval_report.pass_rate:.0%})")
    print(f"Full report written to {args.out}")

    # Exit non-zero on any failure so this can gate a CI pipeline
    sys.exit(0 if eval_report.failed_count == 0 else 1)


if __name__ == "__main__":
    main()
