from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import EvidenceItem
from .repository import InMemoryStore


@dataclass(frozen=True)
class TranscriptAlignmentConfig:
    fallback_window_seconds: float = 2.5
    min_overlap_ratio: float = 0.05


def _prepare_segment(item: dict[str, Any]) -> dict[str, Any]:
    start = float(item["start_seconds"])
    end = float(item["end_seconds"])
    if end < start:
        raise ValueError("Transcript segment end must be >= start.")
    return {
        "start_seconds": start,
        "end_seconds": end,
        "text": str(item.get("text", "")),
        "raw": item,
    }


def _find_best_overlap(segment: dict[str, Any], event_start: float, event_end: float) -> dict[str, Any] | None:
    overlap_start = max(segment["start_seconds"], event_start)
    overlap_end = min(segment["end_seconds"], event_end)
    overlap = max(0.0, overlap_end - overlap_start)
    event_length = max(0.001, event_end - event_start)
    return {"segment": segment, "ratio": overlap / event_length}


def _fallback_nearest_segment(segments: list[dict[str, Any]], event_start: float, event_end: float) -> dict[str, Any]:
    center = (event_start + event_end) / 2
    best = segments[0]
    best_distance = abs(((best["start_seconds"] + best["end_seconds"]) / 2) - center)
    for segment in segments[1:]:
        center_candidate = (segment["start_seconds"] + segment["end_seconds"]) / 2
        distance = abs(center_candidate - center)
        if distance < best_distance:
            best = segment
            best_distance = distance
    return {
        "segment": best,
        "distance": best_distance,
    }


def align_events_to_transcript(
    events: list[dict[str, Any]] | Any,
    transcript_segments: list[dict[str, Any]],
    cfg: TranscriptAlignmentConfig | None = None,
) -> tuple[list[EvidenceItem], list[dict[str, Any]]]:
    cfg = cfg or TranscriptAlignmentConfig()
    store_evidence: list[EvidenceItem] = []
    if not transcript_segments:
        for event in events:
            store_evidence.append(
                EvidenceItem(
                    id=event["evidence_id"],
                    run_id=event["run_id"],
                    kind="transcript_missing",
                    source="transcript",
                    timestamp_seconds=float(event["start_seconds"]),
                    event_ids=[event["id"]],
                    value="No transcript provided for this run.",
                    metadata={"reason": "missing_transcript"},
                )
            )
        return store_evidence, []

    prepared_segments = [_prepare_segment(s) for s in transcript_segments]
    aligned: list[dict[str, Any]] = []
    for event in events:
        event_start = float(event["start_seconds"])
        event_end = max(float(event["start_seconds"]), float(event["end_seconds"]))
        center = (event_start + event_end) / 2
        event_window = event_end - event_start
        best_overlap = None
        for segment in prepared_segments:
            candidate = _find_best_overlap(segment, event_start, event_end)
            if best_overlap is None or candidate["ratio"] > best_overlap["ratio"]:
                best_overlap = candidate

        matched_source = prepared_segments[0]
        if best_overlap and best_overlap["ratio"] >= cfg.min_overlap_ratio:
            matched_source = best_overlap["segment"]
            source_type = "transcript_overlap"
            details = {"overlap_ratio": best_overlap["ratio"]}
        else:
            nearest = _fallback_nearest_segment(prepared_segments, event_start, event_end)
            matched_source = nearest["segment"]
            source_type = "transcript_nearest"
            details = {"distance_seconds": nearest["distance"], "fallback_window_seconds": cfg.fallback_window_seconds}
            if details["distance_seconds"] > cfg.fallback_window_seconds:
                source_type = "transcript_outside_window"
                details["fallback_disqualified"] = True

        evidence_text = str(matched_source.get("text", ""))[:500]
        evid = EvidenceItem(
            id=event["evidence_id"],
            run_id=event["run_id"],
            kind=source_type,
            source="transcript_segment",
            timestamp_seconds=center,
            event_ids=[event["id"]],
            value=evidence_text,
            metadata={
                "event_seconds": {"start": event_start, "end": event_end},
                "event_window_seconds": event_window,
                "transcript_segment": {
                    "start": matched_source["start_seconds"],
                    "end": matched_source["end_seconds"],
                },
                "transcript_match_ratio": best_overlap["ratio"] if best_overlap else 0.0,
                **details,
            },
        )
        store_evidence.append(evid)
        aligned.append(
            {
                "event_id": event["id"],
                "evidence_id": evid.id,
                "transcript_match_type": source_type,
                "timestamp_seconds": evid.timestamp_seconds,
            }
        )

    return store_evidence, aligned
