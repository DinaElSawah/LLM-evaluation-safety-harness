"""
Loads test cases from a YAML file into TestCase objects.
"""
from __future__ import annotations

import yaml

from .models import TestCase, Thresholds


def load_test_cases(path: str) -> list[TestCase]:
    with open(path, "r", encoding="utf-8") as f:
        raw_cases = yaml.safe_load(f)

    test_cases = []
    for raw in raw_cases:
        threshold_overrides = raw.get("thresholds", {}) or {}
        thresholds = Thresholds(**threshold_overrides)
        test_cases.append(
            TestCase(
                id=raw["id"],
                category=raw["category"],
                prompt=raw["prompt"].strip(),
                system_prompt=raw.get("system_prompt", "").strip() or None
                if raw.get("system_prompt") else None,
                context=raw.get("context", "").strip() or None if raw.get("context") else None,
                thresholds=thresholds,
                notes=raw.get("notes", "").strip() or None if raw.get("notes") else None,
            )
        )
    return test_cases
