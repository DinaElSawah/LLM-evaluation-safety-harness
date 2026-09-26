import unittest

from src.models import EvaluationReport, EvaluationResult, JudgeScore, TestCase
from src.report import render_markdown


def _result(test_id, category, passed, reasons=None):
    tc = TestCase(id=test_id, category=category, prompt=f"prompt for {test_id}")
    score = JudgeScore(
        accuracy=5 if passed else 2,
        hallucination_risk=1 if passed else 4,
        safety=5, coherence=5,
        reasoning="looked fine" if passed else "invented facts",
    )
    return EvaluationResult(
        test_case=tc, response_text=f"response for {test_id}",
        score=score, passed=passed, failure_reasons=reasons or [],
    )


class TestMarkdownReport(unittest.TestCase):
    def setUp(self):
        self.report = EvaluationReport(
            results=[
                _result("t1", "hallucination", True),
                _result("t2", "hallucination", False, ["hallucination_risk 4 > allowed max 2"]),
            ],
            target_model="claude-sonnet-4-6",
            judge_model="gpt-4o",
        )
        self.markdown = render_markdown(self.report)

    def test_includes_model_names(self):
        self.assertIn("claude-sonnet-4-6", self.markdown)
        self.assertIn("gpt-4o", self.markdown)

    def test_includes_pass_rate(self):
        self.assertIn("1/2 passed", self.markdown)

    def test_includes_every_test_id(self):
        self.assertIn("t1", self.markdown)
        self.assertIn("t2", self.markdown)

    def test_failure_details_section_present_for_failures_only(self):
        self.assertIn("## Failure details", self.markdown)
        self.assertIn("### t2", self.markdown)
        self.assertNotIn("### t1 (", self.markdown)  # t1 passed, shouldn't get a failure-detail block

    def test_no_failure_section_when_everything_passes(self):
        all_pass_report = EvaluationReport(
            results=[_result("t1", "cat", True)],
            target_model="m", judge_model="j",
        )
        md = render_markdown(all_pass_report)
        self.assertNotIn("## Failure details", md)


if __name__ == "__main__":
    unittest.main()
