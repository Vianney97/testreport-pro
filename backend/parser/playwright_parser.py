import json
from dataclasses import dataclass, field
from typing import List


@dataclass
class TestResult:
    name: str
    status: str
    duration_ms: float
    error_message: str = ""
    file_path: str = ""


@dataclass
class ReportSummary:
    total: int
    passed: int
    failed: int
    skipped: int
    duration_ms: float
    success_rate: float
    tests: List[TestResult] = field(default_factory=list)


def extract_tests_from_suite(suite: dict, tests: list, file_path: str = ""):
    current_file = suite.get("file", file_path) or file_path

    for spec in suite.get("tests", []):
        spec_title = spec.get("title", "Unknown")
        spec_file = spec.get("file", current_file) or current_file

        for result in spec.get("tests", []):
            status = result.get("status", "unknown")
            duration = result.get("duration", 0)
            error = ""
            if result.get("errors"):
                error = result["errors"][0].get("message", "")

            tests.append(TestResult(
                name=spec_title,
                status=status,
                duration_ms=duration,
                error_message=error,
                file_path=spec_file
            ))

    for sub_suite in suite.get("suites", []):
        extract_tests_from_suite(sub_suite, tests, current_file)


def parse_playwright(file_path: str) -> ReportSummary:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tests = []

    for suite in data.get("suites", []):
        extract_tests_from_suite(suite, tests)

    total = len(tests)
    passed = sum(1 for t in tests if t.status == "passed")
    failed = sum(1 for t in tests if t.status == "failed")
    skipped = sum(1 for t in tests if t.status not in ["passed", "failed"])
    total_duration = sum(t.duration_ms for t in tests)
    success_rate = round((passed / total * 100), 1) if total > 0 else 0

    return ReportSummary(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration_ms=total_duration,
        success_rate=success_rate,
        tests=tests
    )