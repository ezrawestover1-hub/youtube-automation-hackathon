from __future__ import annotations

from typing import Any

from .models import QualityCheck, RunQualityReport, ScoringProfile


def _check(name: str, value: float | int | bool | str | None, threshold: float | int | None, passed: bool, message: str):
    return QualityCheck(
        name=name,
        passed=passed,
        value=value,
        threshold=threshold,
        message=message,
    )


def build_quality_report(
    run_id: str,
    profile: ScoringProfile,
    retention_points: list[dict[str, float]],
    events: list[Any],
    evidence: list[Any],
    findings: list[Any],
) -> RunQualityReport:
    checks: list[QualityCheck] = []
    event_count = len(events)
    evidence_count = len(evidence)
    finding_count = len(findings)

    has_retention = len(retention_points) >= profile.quality_min_points
    checks.append(
        _check(
            "Minimum retention points",
            len(retention_points),
            profile.quality_min_points,
            has_retention,
            "Increase retention sampling density for more reliable event detection.",
        )
    )

    point_gaps_ok = True
    max_gap = 0.0
    if len(retention_points) > 1:
        times = sorted(float(item["time_seconds"]) for item in retention_points)
        max_gap = max(times[i] - times[i - 1] for i in range(1, len(times)))
        point_gaps_ok = max_gap <= profile.quality_max_point_gap_seconds
    checks.append(
        _check(
            "Retention sampling gap",
            max_gap,
            profile.quality_max_point_gap_seconds,
            point_gaps_ok,
            "Capture retention at least every few seconds to reduce spike/drop false positives.",
        )
    )

    overlap_events = 0
    overlap_events_strong = 0
    for item in evidence:
        if item.kind != "transcript_missing":
            overlap_events += 1
            if float(item.metadata.get("transcript_match_ratio", 0.0)) >= profile.quality_min_overlap_ratio:
                overlap_events_strong += 1
    overlap_ratio = overlap_events / event_count if event_count else 0.0
    strong_overlap_ratio = overlap_events_strong / event_count if event_count else 0.0

    checks.append(
        _check(
            "Minimum evidence overlap ratio",
            overlap_ratio,
            profile.quality_min_overlap_events_ratio,
            overlap_ratio >= profile.quality_min_overlap_events_ratio,
            "Upload transcript to improve overlap and avoid weak timing recommendations.",
        )
    )

    checks.append(
        _check(
            "Minimum strong overlap ratio",
            strong_overlap_ratio,
            profile.quality_min_overlap_ratio,
            strong_overlap_ratio >= profile.quality_min_overlap_ratio,
            "Prefer direct transcript overlap over nearest-neighbor fallback.",
        )
    )

    confidence_ratio = 0.0
    if findings:
        confidence_ratio = min(1.0, sum(item.confidence for item in findings) / len(findings) / 1.0)
    checks.append(
        _check(
            "Average finding confidence",
            confidence_ratio,
            profile.recommendation_min_confidence,
            confidence_ratio >= profile.recommendation_min_confidence,
            "Increase data quality or confidence floor before publish.",
        )
    )

    finding_density = finding_count / event_count if event_count else 0.0
    checks.append(
        _check(
            "Finding density",
            finding_density,
            profile.quality_min_transcript_presence_ratio,
            finding_density >= profile.quality_min_transcript_presence_ratio,
            "Too many events without actionable recommendations.",
        )
    )

    passed = [1 if item.passed else 0 for item in checks]
    weighted = [
        0.2,
        0.2,
        0.2,
        0.15,
        0.15,
        0.1,
    ]
    overall_score = float(sum(p * w for p, w in zip(passed, weighted)))
    if has_retention and not evidence:
        overall_score *= 0.8

    return RunQualityReport(
        run_id=run_id,
        overall_score=overall_score,
        checks=checks,
        finding_count=finding_count,
        event_count=event_count,
        evidence_count=evidence_count,
        overlap_ratio=overlap_ratio,
        quality_profile=profile,
    )
