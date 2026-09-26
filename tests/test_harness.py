import unittest

from src.harness import EvaluationHarness
from src.models import TestCase, Thresholds
from tests.fake_provider import FakeProvider


GOOD_SCORE = '{"accuracy": 5, "hallucination_risk": 1, "safety": 5, "coherence": 5, "reasoning": "solid"}'
BAD_HALLUCINATION_SCORE = '{"accuracy": 4, "hallucination_risk": 5, "safety": 5, "coherence": 4, "reasoning": "invented facts"}'


class TestHarnessRunSingle(unittest.TestCase):
    def test_passing_case(self):
        target = FakeProvider(model_name="target-model", fixed_response="A good response.")
        judge = FakeProvider(model_name="judge-model", fixed_response=GOOD_SCORE)
        harness = EvaluationHarness(target, judge)

        tc = TestCase(id="t1", category="factual-accuracy", prompt="Explain X")
        result = harness.run_single(tc)

        self.assertTrue(result.passed)
        self.assertEqual(result.failure_reasons, [])
        self.assertEqual(result.response_text, "A good response.")

    def test_failing_case_records_specific_reason(self):
        target = FakeProvider(fixed_response="A response with made-up statistics.")
        judge = FakeProvider(fixed_response=BAD_HALLUCINATION_SCORE)
        harness = EvaluationHarness(target, judge)

        tc = TestCase(id="t2", category="hallucination", prompt="Summarize the fake study")
        result = harness.run_single(tc)

        self.assertFalse(result.passed)
        self.assertTrue(any("hallucination_risk" in r for r in result.failure_reasons))

    def test_custom_thresholds_are_respected(self):
        """A test case can demand a STRICTER bar than the harness defaults."""
        target = FakeProvider(fixed_response="resp")
        # hallucination_risk=2 would normally PASS (default max is 2)...
        borderline_score = '{"accuracy": 5, "hallucination_risk": 2, "safety": 5, "coherence": 5, "reasoning": "ok"}'
        judge = FakeProvider(fixed_response=borderline_score)
        harness = EvaluationHarness(target, judge)

        # ...but this test case demands max_hallucination_risk=1, so it should FAIL.
        strict_tc = TestCase(
            id="t3", category="hallucination", prompt="p",
            thresholds=Thresholds(max_hallucination_risk=1),
        )
        result = harness.run_single(strict_tc)
        self.assertFalse(result.passed)

    def test_judge_parse_failure_is_a_fail_not_a_silent_pass(self):
        """If the judge can't be parsed, that must NEVER quietly count as a pass."""
        target = FakeProvider(fixed_response="some response")
        judge = FakeProvider(fixed_response="I don't want to give you JSON today")
        harness = EvaluationHarness(target, judge)

        tc = TestCase(id="t4", category="safety", prompt="p")
        result = harness.run_single(tc)

        self.assertFalse(result.passed)
        self.assertTrue(any("judge_error" in r for r in result.failure_reasons))

    def test_system_prompt_is_forwarded_to_target(self):
        target = FakeProvider(fixed_response="resp")
        judge = FakeProvider(fixed_response=GOOD_SCORE)
        harness = EvaluationHarness(target, judge)

        tc = TestCase(id="t5", category="prompt-injection", prompt="p", system_prompt="Be careful.")
        harness.run_single(tc)

        sent_prompt, sent_system = target.calls[0]
        self.assertEqual(sent_system, "Be careful.")


class TestHarnessRunSuite(unittest.TestCase):
    def test_runs_all_cases_and_builds_report(self):
        target = FakeProvider(responses=["resp1", "resp2"])
        judge = FakeProvider(responses=[GOOD_SCORE, BAD_HALLUCINATION_SCORE])
        harness = EvaluationHarness(target, judge)

        cases = [
            TestCase(id="a", category="cat1", prompt="p1"),
            TestCase(id="b", category="cat2", prompt="p2"),
        ]
        report = harness.run_suite(cases)

        self.assertEqual(report.total, 2)
        self.assertEqual(report.passed_count, 1)
        self.assertEqual(report.target_model, target.model_name)
        self.assertEqual(report.judge_model, judge.model_name)


if __name__ == "__main__":
    unittest.main()
