import json
from dataclasses import dataclass, field
from typing import List
from .playwright_parser import TestResult, ReportSummary


def parse_cucumber(file_path: str) -> ReportSummary:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    tests = []
    total = passed = failed = skipped = 0
    total_duration = 0.0

    for feature in data:
        feature_name = feature.get("name", "Unknown Feature")
        elements = feature.get("elements", [])

        for scenario in elements:
            scenario_name = scenario.get("name", "Unknown Scenario")
            steps = scenario.get("steps", [])

            # Statut global du scenario = pire statut de ses steps
            scenario_status = "passed"
            scenario_duration = 0.0
            error_message = ""

            for step in steps:
                result = step.get("result", {})
                step_status = result.get("status", "skipped")
                step_duration = result.get("duration", 0) / 1_000_000  # ns → ms

                scenario_duration += step_duration

                if step_status == "failed":
                    scenario_status = "failed"
                    error_message = result.get("error_message", "")
                elif step_status == "skipped" and scenario_status != "failed":
                    scenario_status = "skipped"

            # Scenario sans steps = skipped
            if not steps:
                scenario_status = "skipped"

            tests.append(TestResult(
                name=f"{feature_name} — {scenario_name}",
                status=scenario_status,
                duration_ms=round(scenario_duration, 2),
                error_message=error_message,
                file_path=feature.get("uri", "")
            ))

            total += 1
            total_duration += scenario_duration
            if scenario_status == "passed":
                passed += 1
            elif scenario_status == "failed":
                failed += 1
            else:
                skipped += 1

    success_rate = round((passed / total * 100), 1) if total > 0 else 0

    return ReportSummary(
        total=total,
        passed=passed,
        failed=failed,
        skipped=skipped,
        duration_ms=round(total_duration, 2),
        success_rate=success_rate,
        tests=tests
    )