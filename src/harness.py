"""
The harness: orchestrates running a full test suite against a target model,
judging each response, and applying pass/fail thresholds.
"""
from __future__ import annotations

from .judge import JudgeParseError, judge_response
from .models import EvaluationReport, EvaluationResult, JudgeScore, TestCase
from .providers.base import LLMProvider


def _check_thresholds(test_case: TestCase, score: JudgeScore) -> list[str]:
    """Return a list of human-readable failure reasons; empty list means pass."""
    reasons = []
    t = test_case.thresholds
    if score.accuracy < t.min_accuracy:
        reasons.append(f"accuracy {score.accuracy} < required {t.min_accuracy}")
    if score.hallucination_risk > t.max_hallucination_risk:
        reasons.append(
            f"hallucination_risk {score.hallucination_risk} > allowed max {t.max_hallucination_risk}"
        )
    if score.safety < t.min_safety:
        reasons.append(f"safety {score.safety} < required {t.min_safety}")
    if score.coherence < t.min_coherence:
        reasons.append(f"coherence {score.coherence} < required {t.min_coherence}")
    return reasons


class EvaluationHarness:
    def __init__(self, target_provider: LLMProvider, judge_provider: LLMProvider):
        self.target_provider = target_provider
        self.judge_provider = judge_provider

    def run_single(self, test_case: TestCase) -> EvaluationResult:
        """Run one test case end-to-end: generate -> judge -> apply thresholds.

        A judge parsing failure is NOT swallowed into a silent pass — it is
        surfaced as an automatic fail with a clear reason, since an
        unscoreable response is not a validated response.
        """
        response_text = self.target_provider.generate(
            test_case.prompt, system_prompt=test_case.system_prompt
        )

        try:
            score = judge_response(self.judge_provider, test_case, response_text)
        except (JudgeParseError, ValueError) as e:
            placeholder_score = JudgeScore(
                accuracy=1, hallucination_risk=5, safety=1, coherence=1,
                reasoning=f"Judge failed to produce a valid score: {e}",
            )
            return EvaluationResult(
                test_case=test_case,
                response_text=response_text,
                score=placeholder_score,
                passed=False,
                failure_reasons=[f"judge_error: {e}"],
            )

        failure_reasons = _check_thresholds(test_case, score)
        return EvaluationResult(
            test_case=test_case,
            response_text=response_text,
            score=score,
            passed=len(failure_reasons) == 0,
            failure_reasons=failure_reasons,
        )

    def run_suite(self, test_cases: list[TestCase]) -> EvaluationReport:
        results = [self.run_single(tc) for tc in test_cases]
        return EvaluationReport(
            results=results,
            target_model=self.target_provider.model_name,
            judge_model=self.judge_provider.model_name,
        )
