from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import RetentionEventType


@dataclass(frozen=True)
class RetentionEventConfig:
    drop_delta_threshold: float = 0.045
    spike_delta_threshold: float = 0.05
    rewatch_delta_threshold: float = 0.06
    exit_ratio_threshold: float = 0.18
    min_sample_gap_seconds: float = 0.75
    min_event_window_seconds: float = 0.5
    merge_gap_seconds: float = 3.5


def _clamp01(value: float) -> float:
    if value < 0:
        return 0.0
    if value > 1:
        return 1.0
    return float(value)


def _normalize_retention_points(points: list[dict[str, float]]) -> list[dict[str, float]]:
    normalized = sorted(points, key=lambda p: float(p["time_seconds"]))
    cleaned = []
    for p in normalized:
        cleaned.append(
            {
                "time_seconds": float(p["time_seconds"]),
                "retention_ratio": float(p["retention_ratio"]),
                "metadata": p.get("metadata", {}),
            }
        )
    deduped = []
    last_time = None
    for row in cleaned:
        if last_time is None or row["time_seconds"] != last_time:
            deduped.append(row)
            last_time = row["time_seconds"]
    return deduped


def _detect_candidates(points: list[dict[str, float]], cfg: RetentionEventConfig) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for idx in range(1, len(points)):
        previous = points[idx - 1]
        current = points[idx]
        delta_time = current["time_seconds"] - previous["time_seconds"]
        if delta_time < cfg.min_sample_gap_seconds:
            continue

        delta_ratio = current["retention_ratio"] - previous["retention_ratio"]
        max_range = max(1.0, abs(previous["retention_ratio"] - current["retention_ratio"]))
        if delta_ratio <= -cfg.drop_delta_threshold:
            start_t = previous["time_seconds"]
            end_t = current["time_seconds"]
            if (end_t - start_t) >= cfg.min_event_window_seconds:
                candidates.append(
                    {
                        "type": RetentionEventType.DROP,
                        "start_seconds": start_t,
                        "end_seconds": end_t,
                        "severity": _clamp01(abs(delta_ratio) / max_range),
                        "score": _clamp01(abs(delta_ratio) / max_range),
                        "metadata": {"delta_ratio": delta_ratio, "delta_seconds": delta_time},
                    }
                )

        if delta_ratio >= cfg.spike_delta_threshold:
            start_t = previous["time_seconds"]
            end_t = current["time_seconds"]
            candidates.append(
                {
                    "type": RetentionEventType.SPIKE,
                    "start_seconds": start_t,
                    "end_seconds": end_t,
                    "severity": _clamp01(delta_ratio / max_range),
                    "score": _clamp01(delta_ratio / max_range),
                    "metadata": {"delta_ratio": delta_ratio, "delta_seconds": delta_time},
                }
            )

        if previous["retention_ratio"] >= cfg.exit_ratio_threshold and current["retention_ratio"] <= cfg.exit_ratio_threshold:
            candidates.append(
                {
                    "type": RetentionEventType.EXIT,
                    "start_seconds": previous["time_seconds"],
                    "end_seconds": current["time_seconds"],
                    "severity": _clamp01((cfg.exit_ratio_threshold - current["retention_ratio"]) / cfg.exit_ratio_threshold),
                    "score": _clamp01((cfg.exit_ratio_threshold - current["retention_ratio"]) / cfg.exit_ratio_threshold),
                    "metadata": {
                        "exit_ratio_threshold": cfg.exit_ratio_threshold,
                        "delta_ratio": delta_ratio,
                        "delta_seconds": delta_time,
                    },
                }
            )

        if idx >= 2:
            before = points[idx - 2]
            prior_delta = previous["retention_ratio"] - before["retention_ratio"]
            if prior_delta <= -cfg.drop_delta_threshold and delta_ratio >= cfg.rewatch_delta_threshold:
                candidates.append(
                    {
                        "type": RetentionEventType.REWATCH,
                        "start_seconds": previous["time_seconds"],
                        "end_seconds": current["time_seconds"],
                        "severity": _clamp01((delta_ratio - prior_delta) / max_range),
                        "score": _clamp01((delta_ratio - prior_delta) / max_range),
                        "metadata": {
                            "prior_delta": prior_delta,
                            "rewatch_delta": delta_ratio,
                            "delta_seconds": delta_time,
                        },
                    }
                )
    return candidates


def _merge_candidates(candidates: list[dict[str, Any]], cfg: RetentionEventConfig) -> list[dict[str, Any]]:
    if not candidates:
        return []
    sorted_candidates = sorted(candidates, key=lambda item: item["start_seconds"])
    merged: list[dict[str, Any]] = []
    for candidate in sorted_candidates:
        if not merged:
            merged.append(candidate)
            continue

        previous = merged[-1]
        if previous["type"] == candidate["type"] and candidate["start_seconds"] - previous["end_seconds"] <= cfg.merge_gap_seconds:
            previous["end_seconds"] = max(previous["end_seconds"], candidate["end_seconds"])
            previous["score"] = max(previous["score"], candidate["score"])
            previous["severity"] = max(previous["severity"], candidate["severity"])
            previous["metadata"] = {
                "merged_count": previous["metadata"].get("merged_count", 1) + 1,
            } | previous["metadata"]
            continue
        merged.append(candidate)
    return sorted(merged, key=lambda item: item["start_seconds"])


def detect_events(points: list[dict[str, float]], cfg: RetentionEventConfig | None = None) -> list[dict[str, Any]]:
    cfg = cfg or RetentionEventConfig()
    normalized = _normalize_retention_points(points)
    if len(normalized) < 2:
        return []

    candidates = _detect_candidates(normalized, cfg)
    merged = _merge_candidates(candidates, cfg)
    if not merged:
        return []

    for event in merged:
        event["metadata"]["source_point_count"] = len(normalized)
    return merged
