import json
import xml.etree.ElementTree as ET
from .playwright_parser import parse_playwright, ReportSummary, TestResult
from .pytest_parser import parse_pytest
from .cucumber_parser import parse_cucumber
from dataclasses import field
from typing import List


def detect_format(file_path: str) -> str:
    # Fichier XML → JUnit/Pytest XML
    if file_path.endswith(".xml"):
        return "junit_xml"

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return "unknown"

    # Cucumber JSON : liste avec "elements"
    if isinstance(data, list) and len(data) > 0:
        if "elements" in data[0]:
            return "cucumber"

    if isinstance(data, dict):
        # Playwright officiel : contient "suites"
        if "suites" in data:
            return "playwright"

        # Pytest JSON (pytest-json-report) : contient "summary" + tests avec "nodeid"
        if "summary" in data and "tests" in data:
            tests = data.get("tests", [])
            if tests and "nodeid" in tests[0]:
                return "pytest_json"

        # Playwright custom : contient "summary" + tests avec "title"
        if "summary" in data and "tests" in data:
            tests = data.get("tests", [])
            if tests and "title" in tests[0]:
                return "playwright_custom"

        # Jest JSON : contient "testResults" 
        if "testResults" in data:
            return "jest"

        # Mocha JSON : contient "stats" + "tests"
        if "stats" in data and "tests" in data:
            return "mocha"

        # Allure JSON : contient "uid" + "status"
        if "uid" in data and "status" in data:
            return "allure"

    return "unknown"


def parse_pytest_json(data: dict) -> ReportSummary:
    tests = []
    total = passed = failed = skipped = 0
    total_duration = 0.0

    for test in data.get("tests", []):
        nodeid = test.get("nodeid", "Unknown")
        outcome = test.get("outcome", "unknown")

        duration = 0.0
        for phase in ["setup", "call", "teardown"]:
            duration += test.get(phase, {}).get("duration", 0) * 1000

        error = ""
        if outcome == "failed":
            call = test.get("call", {})
            error = str(call.get("longrepr", ""))[:200]

        name = nodeid.split("::")[-1] if "::" in nodeid else nodeid
        file_attr = nodeid.split("::")[0] if "::" in nodeid else ""
        status = "passed" if outcome == "passed" else "failed" if outcome == "failed" else "skipped"

        tests.append(TestResult(
            name=name, status=status, duration_ms=round(duration, 2),
            error_message=error, file_path=file_attr
        ))
        total += 1
        total_duration += duration
        if status == "passed": passed += 1
        elif status == "failed": failed += 1
        else: skipped += 1

    success_rate = round((passed / total * 100), 1) if total > 0 else 0
    return ReportSummary(total=total, passed=passed, failed=failed, skipped=skipped,
                         duration_ms=round(total_duration, 2), success_rate=success_rate, tests=tests)


def parse_playwright_custom(data: dict) -> ReportSummary:
    tests = []
    total = passed = failed = skipped = 0
    total_duration = 0.0

    for test in data.get("tests", []):
        name = test.get("title", "Unknown")
        status_raw = test.get("status", "unknown")
        duration = test.get("durationMs", 0)
        error = test.get("error", {}).get("message", "") if test.get("error") else ""
        status = "passed" if status_raw == "passed" else "failed" if status_raw == "failed" else "skipped"

        tests.append(TestResult(
            name=name, status=status, duration_ms=duration,
            error_message=error, file_path=test.get("file", "")
        ))
        total += 1
        total_duration += duration
        if status == "passed": passed += 1
        elif status == "failed": failed += 1
        else: skipped += 1

    success_rate = round((passed / total * 100), 1) if total > 0 else 0
    return ReportSummary(total=total, passed=passed, failed=failed, skipped=skipped,
                         duration_ms=round(total_duration, 2), success_rate=success_rate, tests=tests)


def parse_jest(data: dict) -> ReportSummary:
    tests = []
    total = passed = failed = skipped = 0
    total_duration = float(data.get("testResults", [{}])[0].get("perfStats", {}).get("runtime", 0))

    for suite in data.get("testResults", []):
        file_path = suite.get("testFilePath", "")
        for test in suite.get("testResults", []):
            name = test.get("fullName", "Unknown")
            status_raw = test.get("status", "unknown")
            duration = test.get("duration", 0) or 0
            error = " ".join(test.get("failureMessages", []))[:200]
            status = "passed" if status_raw == "passed" else "failed" if status_raw == "failed" else "skipped"

            tests.append(TestResult(
                name=name, status=status, duration_ms=duration,
                error_message=error, file_path=file_path
            ))
            total += 1
            if status == "passed": passed += 1
            elif status == "failed": failed += 1
            else: skipped += 1

    success_rate = round((passed / total * 100), 1) if total > 0 else 0
    return ReportSummary(total=total, passed=passed, failed=failed, skipped=skipped,
                         duration_ms=total_duration, success_rate=success_rate, tests=tests)


def parse_mocha(data: dict) -> ReportSummary:
    tests = []
    total = passed = failed = skipped = 0
    stats = data.get("stats", {})
    total_duration = stats.get("duration", 0)

    for test in data.get("tests", []):
        name = test.get("fullTitle", test.get("title", "Unknown"))
        duration = test.get("duration", 0)
        error = test.get("err", {}).get("message", "") if test.get("err") else ""
        status = "failed" if test.get("err") else "passed"

        tests.append(TestResult(
            name=name, status=status, duration_ms=duration,
            error_message=error, file_path=test.get("file", "")
        ))
        total += 1
        if status == "passed": passed += 1
        else: failed += 1

    for test in data.get("pending", []):
        tests.append(TestResult(
            name=test.get("fullTitle", "Unknown"), status="skipped",
            duration_ms=0, error_message="", file_path=""
        ))
        total += 1
        skipped += 1

    success_rate = round((passed / total * 100), 1) if total > 0 else 0
    return ReportSummary(total=total, passed=passed, failed=failed, skipped=skipped,
                         duration_ms=total_duration, success_rate=success_rate, tests=tests)


def universal_parse(file_path: str) -> tuple[ReportSummary, str]:
    fmt = detect_format(file_path)

    if fmt == "playwright":
        return parse_playwright(file_path), "Playwright"
    elif fmt == "junit_xml":
        return parse_pytest(file_path), "JUnit / Pytest XML"
    elif fmt == "cucumber":
        return parse_cucumber(file_path), "Cucumber"
    elif fmt == "pytest_json":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_pytest_json(data), "Pytest JSON"
    elif fmt == "playwright_custom":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_playwright_custom(data), "Playwright"
    elif fmt == "jest":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_jest(data), "Jest"
    elif fmt == "mocha":
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return parse_mocha(data), "Mocha"
    else:
        raise ValueError(f"Format non reconnu. Formats supportés : Playwright, Pytest, Cucumber, Jest, Mocha")