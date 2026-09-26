"""
Turns an EvaluationReport into a readable Markdown report.
"""
from __future__ import annotations

from .models import EvaluationReport, EvaluationResult


def _result_row(r: EvaluationResult) -> str:
    status = "PASS" if r.passed else "FAIL"
    s = r.score
    return (
        f"| {r.test_case.id} | {r.test_case.category} | {status} | "
        f"{s.accuracy} | {s.hallucination_risk} | {s.safety} | {s.coherence} |"
    )


def render_markdown(report: EvaluationReport) -> str:
    lines = []
    lines.append("# LLM Evaluation & Safety Report")
    lines.append("")
    lines.append(f"**Target model:** `{report.target_model}`  ")
    lines.append(f"**Judge model:** `{report.judge_model}`")
    lines.append("")
    lines.append(
        f"**Result: {report.passed_count}/{report.total} passed "
        f"({report.pass_rate:.0%})**"
    )
    lines.append("")

    lines.append("## Summary by category")
    lines.append("")
    lines.append("| Category | Passed | Total |")
    lines.append("|---|---|---|")
    for cat, results in sorted(report.results_by_category().items()):
        passed = sum(1 for r in results if r.passed)
        lines.append(f"| {cat} | {passed} | {len(results)} |")
    lines.append("")

    lines.append("## All results")
    lines.append("")
    lines.append("| Test ID | Category | Verdict | Accuracy | Hallucination Risk | Safety | Coherence |")
    lines.append("|---|---|---|---|---|---|---|")
    for r in report.results:
        lines.append(_result_row(r))
    lines.append("")

    failed = [r for r in report.results if not r.passed]
    if failed:
        lines.append("## Failure details")
        lines.append("")
        for r in failed:
            lines.append(f"### {r.test_case.id} ({r.test_case.category})")
            lines.append("")
            lines.append(f"**Prompt:** {r.test_case.prompt}")
            lines.append("")
            lines.append(f"**Response:** {r.response_text}")
            lines.append("")
            lines.append(f"**Why it failed:** {'; '.join(r.failure_reasons)}")
            lines.append("")
            lines.append(f"**Judge reasoning:** {r.score.reasoning}")
            lines.append("")

    return "\n".join(lines)
