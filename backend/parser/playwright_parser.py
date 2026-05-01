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


def parse_playwright(file_path: str) -> ReportSummary:
    with open(file_path, "r") as f:
        data = json.load(f)

    tests = []
    total = passed = failed = skipped = 0
    total_duration = 0

    for suite in data.get("suites", []):
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    status = result.get("status", "unknown")
                    duration = result.get("duration", 0)
                    error = ""

                    if result.get("errors"):
                        error = result["errors"][0].get("message", "")

                    tests.append(TestResult(
                        name=spec.get("title", "Unknown"),
                        status=status,
                        duration_ms=duration,
                        error_message=error,
                        file_path=spec.get("file", "")
                    ))

                    total += 1
                    total_duration += duration
                    if status == "passed":
                        passed += 1
                    elif status == "failed":
                        failed += 1
                    else:
                        skipped += 1

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