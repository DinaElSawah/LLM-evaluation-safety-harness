import unittest

from src.judge import JudgeParseError, judge_response
from src.models import TestCase
from tests.fake_provider import FakeProvider


def _tc() -> TestCase:
    return TestCase(id="t1", category="test", prompt="hi")


class TestJudgeJSONExtraction(unittest.TestCase):
    """The judge model won't always return clean JSON. These tests pin down
    exactly which messy formats we tolerate and which we correctly reject."""

    def test_clean_json(self):
        raw = '{"accuracy": 4, "hallucination_risk": 1, "safety": 5, "coherence": 4, "reasoning": "fine"}'
        provider = FakeProvider(fixed_response=raw)
        score = judge_response(provider, _tc(), "some response")
        self.assertEqual(score.accuracy, 4)
        self.assertEqual(score.hallucination_risk, 1)

    def test_json_wrapped_in_markdown_fence(self):
        raw = (
            "Here is my evaluation:\n\n"
            "```json\n"
            '{"accuracy": 3, "hallucination_risk": 2, "safety": 4, "coherence": 3, "reasoning": "ok"}\n'
            "```\n"
            "Let me know if you need more detail."
        )
        provider = FakeProvider(fixed_response=raw)
        score = judge_response(provider, _tc(), "some response")
        self.assertEqual(score.accuracy, 3)
        self.assertEqual(score.safety, 4)

    def test_json_fence_without_language_tag(self):
        raw = '```\n{"accuracy": 5, "hallucination_risk": 1, "safety": 5, "coherence": 5, "reasoning": "great"}\n```'
        provider = FakeProvider(fixed_response=raw)
        score = judge_response(provider, _tc(), "resp")
        self.assertEqual(score.accuracy, 5)

    def test_stray_leading_and_trailing_text_without_fence(self):
        raw = (
            'Sure, here is the JSON you asked for: '
            '{"accuracy": 2, "hallucination_risk": 4, "safety": 3, "coherence": 2, "reasoning": "weak"} '
            "Hope that helps!"
        )
        provider = FakeProvider(fixed_response=raw)
        score = judge_response(provider, _tc(), "resp")
        self.assertEqual(score.hallucination_risk, 4)

    def test_missing_required_key_raises_parse_error(self):
        raw = '{"accuracy": 4, "hallucination_risk": 1, "safety": 5}'  # missing coherence, reasoning
        provider = FakeProvider(fixed_response=raw)
        with self.assertRaises(JudgeParseError):
            judge_response(provider, _tc(), "resp")

    def test_completely_unparseable_output_raises_parse_error(self):
        provider = FakeProvider(fixed_response="I refuse to evaluate this, sorry!")
        with self.assertRaises(JudgeParseError):
            judge_response(provider, _tc(), "resp")

    def test_out_of_range_score_raises_value_error(self):
        raw = '{"accuracy": 9, "hallucination_risk": 1, "safety": 5, "coherence": 4, "reasoning": "bad score"}'
        provider = FakeProvider(fixed_response=raw)
        with self.assertRaises(ValueError):
            judge_response(provider, _tc(), "resp")

    def test_judge_prompt_includes_context_and_notes_when_present(self):
        """The judge should actually receive the reference context and probing
        notes when the test case defines them -- otherwise it can't judge accuracy."""
        provider = FakeProvider(
            fixed_response='{"accuracy": 5, "hallucination_risk": 1, "safety": 5, "coherence": 5, "reasoning": "ok"}'
        )
        tc = TestCase(
            id="t2", category="factual", prompt="What year?",
            context="Ground truth: 2017.", notes="Checks factual recall.",
        )
        judge_response(provider, tc, "It was 2017.")
        sent_prompt, sent_system = provider.calls[0]
        self.assertIn("Ground truth: 2017.", sent_prompt)
        self.assertIn("Checks factual recall.", sent_prompt)
        self.assertIn("It was 2017.", sent_prompt)


if __name__ == "__main__":
    unittest.main()
