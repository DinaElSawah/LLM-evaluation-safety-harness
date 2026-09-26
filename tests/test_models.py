import unittest

from src.models import EvaluationReport, EvaluationResult, JudgeScore, TestCase, Thresholds


class TestJudgeScoreValidation(unittest.TestCase):
    def test_valid_scores_construct_fine(self):
        score = JudgeScore(accuracy=4, hallucination_risk=1, safety=5, coherence=4, reasoning="ok")
        self.assertEqual(score.accuracy, 4)

    def test_rejects_score_above_range(self):
        with self.assertRaises(ValueError):
            JudgeScore(accuracy=6, hallucination_risk=1, safety=5, coherence=4, reasoning="bad")

    def test_rejects_score_below_range(self):
        with self.assertRaises(ValueError):
            JudgeScore(accuracy=0, hallucination_risk=1, safety=5, coherence=4, reasoning="bad")

    def test_rejects_non_integer_score(self):
        with self.assertRaises(ValueError):
            JudgeScore(accuracy=3.5, hallucination_risk=1, safety=5, coherence=4, reasoning="bad")


def _make_result(test_id: str, category: str, passed: bool) -> EvaluationResult:
    tc = TestCase(id=test_id, category=category, prompt="p")
    score = JudgeScore(accuracy=5, hallucination_risk=1, safety=5, coherence=5, reasoning="r")
    return EvaluationResult(test_case=tc, response_text="resp", score=score, passed=passed)


class TestEvaluationReportAggregates(unittest.TestCase):
    def setUp(self):
        self.report = EvaluationReport(
            results=[
                _make_result("t1", "hallucination", True),
                _make_result("t2", "hallucination", False),
                _make_result("t3", "safety", True),
            ],
            target_model="fake-target",
            judge_model="fake-judge",
        )

    def test_totals(self):
        self.assertEqual(self.report.total, 3)
        self.assertEqual(self.report.passed_count, 2)
        self.assertEqual(self.report.failed_count, 1)

    def test_pass_rate(self):
        self.assertAlmostEqual(self.report.pass_rate, 2 / 3)

    def test_pass_rate_empty_report_does_not_divide_by_zero(self):
        empty = EvaluationReport(results=[], target_model="x", judge_model="y")
        self.assertEqual(empty.pass_rate, 0.0)

    def test_results_by_category(self):
        by_cat = self.report.results_by_category()
        self.assertEqual(set(by_cat.keys()), {"hallucination", "safety"})
        self.assertEqual(len(by_cat["hallucination"]), 2)
        self.assertEqual(len(by_cat["safety"]), 1)


if __name__ == "__main__":
    unittest.main()
