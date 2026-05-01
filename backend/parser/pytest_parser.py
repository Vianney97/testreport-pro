import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import List
from .playwright_parser import TestResult, ReportSummary


def parse_pytest(file_path: str) -> ReportSummary:
    tree = ET.parse(file_path)
    root = tree.getroot()

    tests = []
    total = passed = failed = skipped = 0
    total_duration = 0.0

    for testcase in root.iter("testcase"):
        name = testcase.get("name", "Unknown")
        duration = float(testcase.get("time", 0)) * 1000
        file_path_attr = testcase.get("classname", "").replace(".", "/")
        error = ""

        failure = testcase.find("failure")
        error_tag = testcase.find("error")
        skip_tag = testcase.find("skipped")

        if failure is not None:
            status = "failed"
            error = failure.get("message", "")
            failed += 1
        elif error_tag is not None:
            status = "failed"
            error = error_tag.get("message", "")
            failed += 1
        elif skip_tag is not None:
            status = "skipped"
            skipped += 1
        else:
            status = "passed"
            passed += 1

        total += 1
        total_duration += duration

        tests.append(TestResult(
            name=name,
            status=status,
            duration_ms=duration,
            error_message=error,
            file_path=file_path_attr
        ))

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