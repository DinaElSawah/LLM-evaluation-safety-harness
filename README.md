# LLM Evaluation & Safety Harness

A real, runnable framework for stress-testing an LLM's responses against a fixed rubric — accuracy, hallucination risk, safety, and coherence — using an LLM-as-judge pattern, with a full unit-test suite covering the orchestration logic itself.

This is the technical proof behind a claim made elsewhere in this portfolio: the [AI Enablement Playbook's case study](https://github.com/DinaElSawah/ai-enablement-playbook) references "structured evaluation criteria and prompt stress tests" used to quality-assure LLM outputs before deployment. This repo is that idea, built as actual working software instead of a described process.

## What it does

You give it a list of test cases (a prompt, optionally some reference context, and pass/fail thresholds). For each one, it:

1. Sends the prompt to a **target model** (the one being evaluated)
2. Sends the target's response — along with the original prompt and any reference context — to a **judge model**, which scores it 1–5 on four axes
3. Checks the scores against that test case's thresholds
4. Produces a Markdown report: overall pass rate, a breakdown by category, and full detail on every failure

See [`sample_report.md`](./sample_report.md) for a real example of the output (generated from hand-written illustrative responses — see "A note on testing without live API calls" below for why).

## Why an LLM judges another LLM

A model grading its own output is the obvious failure mode here — it has no independent perspective on its own mistakes. The harness is built so the **judge can be a different model family than the target** (e.g. evaluate Claude's answers using GPT-4o as judge, or vice versa). `run_evaluation.py` takes both as separate arguments for exactly this reason.

## Architecture

```
src/
├── models.py       # TestCase, JudgeScore, EvaluationResult, EvaluationReport (plain dataclasses)
├── providers/
│   ├── base.py            # LLMProvider abstract interface
│   ├── openai_provider.py
│   └── anthropic_provider.py
├── judge.py         # Builds the judge prompt, calls the judge model, parses its JSON verdict
├── harness.py        # Orchestrates: generate -> judge -> apply thresholds -> build report
├── loader.py         # Loads test cases from YAML
└── report.py         # Renders an EvaluationReport as Markdown

test_cases/education_prompts.yaml   # 10 real test cases: hallucination, prompt-injection,
                                     # content-appropriateness, bias, ambiguity, factual accuracy
tests/                              # Full unittest suite (33 tests) using a FakeProvider
run_evaluation.py                   # CLI entry point for a real run
generate_sample_report.py           # Produces sample_report.md from hand-written example data
```

The provider interface (`LLMProvider.generate(prompt, system_prompt)`) is deliberately the only thing the harness knows about — it never touches an SDK directly. That's what makes it possible to test the entire orchestration and scoring logic with a `FakeProvider` that returns pre-programmed responses, with zero API calls, zero API keys, and zero network access required.

## Design decisions worth knowing about

- **A judge parsing failure is a fail, not a silent pass.** If the judge model returns malformed output, that test case is automatically marked failed with the parse error recorded — an unscoreable response never gets counted as validated. (`test_harness.py::test_judge_parse_failure_is_a_fail_not_a_silent_pass`)
- **JSON extraction handles messy judge output.** Real judge models don't always return clean JSON — they wrap it in ` ```json ` fences, or add a sentence before/after it. `judge.py` handles both, and rejects genuinely unparseable output rather than guessing. (`test_judge.py` covers five different malformed-output shapes.)
- **Per-test-case threshold overrides.** Most test cases use sensible defaults, but a few demand a stricter bar — e.g. the two hallucination test cases set `max_hallucination_risk: 1` instead of the default `2`, because "mostly didn't make things up" isn't good enough when the prompt is explicitly designed to induce fabrication.
- **hallucination_risk is inverted on purpose.** Lower is better on that one axis, unlike the other three — this is modeled explicitly in `Thresholds` (a max, not a min) rather than silently flipping the scale, so the code reads the same way the rubric is described in the judge prompt.

## Test cases included

| Category | What it probes for |
|---|---|
| `factual-accuracy` | Does the model get verifiable facts right? |
| `hallucination` | Does it fabricate details about things that don't exist (a fake study, private data it can't know)? |
| `prompt-injection` | Does it follow instructions smuggled inside content it's supposed to just summarize? |
| `content-appropriateness` | Does it handle a sensitive request (a stressed student asking about medication) safely, and produce genuinely appropriate content for benign requests? |
| `ambiguity-handling` | Does it ask for clarification on an underspecified prompt, or confidently invent an answer? |
| `fairness-and-bias` | Does its suggested response challenge a stereotyping claim constructively? |
| `coherence` | Can it explain a real concept from this portfolio (enablement program tiers) clearly? |

## Running it for real

```bash
pip install -r requirements.txt
pip install anthropic openai   # whichever you're using as target/judge
cp .env.example .env           # fill in your key(s)

python run_evaluation.py \
  --target anthropic:claude-sonnet-4-6 \
  --judge openai:gpt-4o \
  --test-cases test_cases/education_prompts.yaml \
  --out report.md
```

Exits non-zero if anything fails — plug this into a CI pipeline and a regression in model behavior fails the build.

## Running the tests

```bash
python -m unittest discover -s tests -v
```

33 tests, all passing, no API keys or network required — they exercise the judge's JSON parsing, the harness's threshold logic, report rendering, and the YAML loader entirely against `FakeProvider`.

## A note on testing without live API calls

This was built and verified in a sandboxed environment with no network access, so I couldn't run it against real OpenAI/Anthropic endpoints from there. Rather than skip verification, I designed the whole thing around a provider interface specifically so the **logic** — threshold checking, JSON parsing, report generation, judge-failure handling — could be fully unit-tested against a fake provider instead. That's not a workaround; it's the same reason you'd mock an external API in any real test suite, whether or not the network happens to be reachable. `sample_report.md` was generated from realistic hand-written example data (see `generate_sample_report.py`) specifically to show the real output format without requiring a live key. The actual API integration in `providers/` follows each vendor's documented SDK interface and is ready to run the moment you add a key.

## Part of the portfolio series

- [AI Enablement Playbook](https://github.com/DinaElSawah/ai-enablement-playbook) — the strategy layer this harness's evaluation approach comes from
- [GenAI Onboarding Workshop Kit](https://github.com/DinaElSawah/Genai-onboarding-workshop-kit)
- [AI Adoption Scorecard](https://github.com/DinaElSawah/AI-adoption-scorecard)
- [AI Curriculum Framework](https://github.com/DinaElSawah/ai-curriculum-framework)
- **LLM Evaluation & Safety Harness** *(this repo)* — the technical implementation behind the evaluation claims made elsewhere in this portfolio

## About

Built by Dina El Sawah — AI Training & Enablement specialist. [LinkedIn](https://www.linkedin.com/in/dina-elsawah)
