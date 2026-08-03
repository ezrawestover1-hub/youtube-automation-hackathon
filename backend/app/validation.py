from __future__ import annotations

import csv
from io import StringIO
from typing import Any

from .errors import InsufficientDataError, UnsupportedFormatError, ValidationError


RETENTION_REQUIRED_COLUMNS = {
    "time_seconds": {"time_seconds", "seconds", "time", "elapsed_sec", "elapsed_seconds"},
    "retention_ratio": {
        "relative_retention",
        "retention_ratio",
        "watch_ratio",
        "audience_retention",
    },
}

TRANSCRIPT_REQUIRED_COLUMNS = {
    "start": {"start", "start_time", "start_seconds", "start_sec"},
    "end": {"end", "end_time", "end_seconds", "end_sec"},
    "text": {"text", "transcript", "caption", "line", "sentence"},
}


def _resolve_column(columns: set[str], aliases: set[str]) -> str | None:
    lower = {c.strip().lower() for c in columns}
    for candidate in aliases:
        if candidate.lower() in lower:
            return candidate.lower()
    return None


def _canonical_lookup(row: dict[str, str], column_name: str) -> str | None:
    for key in row:
        if key.strip().lower() == column_name:
            return row.get(key, "")
    return None


def parse_retention_csv(text: str) -> list[dict[str, float]]:
    try:
        reader = csv.DictReader(StringIO(text))
    except Exception as err:
        raise UnsupportedFormatError("Retention payload is not CSV parseable.", {"error": str(err)})

    columns = set(reader.fieldnames or [])
    resolved_time = _resolve_column(columns, RETENTION_REQUIRED_COLUMNS["time_seconds"])
    resolved_ratio = _resolve_column(columns, RETENTION_REQUIRED_COLUMNS["retention_ratio"])
    if not resolved_time or not resolved_ratio:
        raise ValidationError(
            "Retention CSV is missing required numeric columns.",
            {
                "required": sorted(
                    [*RETENTION_REQUIRED_COLUMNS["time_seconds"], *RETENTION_REQUIRED_COLUMNS["retention_ratio"]]
                ),
                "received": sorted(columns),
            },
        )

    points: list[dict[str, float]] = []
    for idx, row in enumerate(reader, start=1):
        raw_time = _canonical_lookup(row, resolved_time)
        raw_ratio = _canonical_lookup(row, resolved_ratio)
        if raw_time is None or raw_ratio is None:
            continue
        try:
            time_seconds = float(raw_time)
            ratio = float(raw_ratio)
        except ValueError:
            raise ValidationError(
                "Retention CSV contains non-numeric values.",
                {"row": idx, "time": raw_time, "ratio": raw_ratio},
            )

        if time_seconds < 0:
            raise ValidationError("Retention time must be non-negative.", {"row": idx, "time": time_seconds})
        points.append(
            {
                "time_seconds": time_seconds,
                "retention_ratio": ratio,
                "metadata": dict(row),
            }
        )

    if not points:
        raise InsufficientDataError("Retention CSV contained no usable rows.", {"rows": 0})

    return points


def parse_transcript(payload: dict | list[dict] | str) -> list[dict[str, Any]]:
    if isinstance(payload, str):
        try:
            import json

            decoded = json.loads(payload)
        except Exception as err:
            raise UnsupportedFormatError("Transcript payload is not valid JSON.", {"error": str(err)})
        return parse_transcript(decoded)

    if isinstance(payload, list):
        if not payload:
            raise ValidationError("Transcript list is empty.")

        columns = set()
        for row in payload:
            if not isinstance(row, dict):
                raise ValidationError("Transcript rows must be JSON objects.", {"value_type": type(row).__name__})
            columns.update(row.keys())

        resolved_start = _resolve_column(columns, TRANSCRIPT_REQUIRED_COLUMNS["start"])
        resolved_end = _resolve_column(columns, TRANSCRIPT_REQUIRED_COLUMNS["end"])
        resolved_text = _resolve_column(columns, TRANSCRIPT_REQUIRED_COLUMNS["text"])
        if not resolved_start or not resolved_end or not resolved_text:
            raise ValidationError(
                "Transcript rows are missing required timing/text fields.",
                {
                    "required": sorted([*TRANSCRIPT_REQUIRED_COLUMNS["start"], *TRANSCRIPT_REQUIRED_COLUMNS["end"], *TRANSCRIPT_REQUIRED_COLUMNS["text"]]),
                    "received": sorted(columns),
                },
            )

        canonicalized: list[dict[str, Any]] = []
        for idx, row in enumerate(payload, start=1):
            row_start = _canonical_lookup(row, resolved_start)
            row_end = _canonical_lookup(row, resolved_end)
            row_text = _canonical_lookup(row, resolved_text)
            if row_start is None or row_end is None or row_text is None:
                raise ValidationError("Transcript row missing required fields.", {"row": idx, "row_keys": sorted(row.keys())})
            try:
                start = float(row_start)
                end = float(row_end)
            except (TypeError, ValueError):
                raise ValidationError("Transcript timing columns must be numeric.", {"row": idx})
            if end < start:
                raise ValidationError("Transcript end time must be >= start time.", {"row": idx, "start": start, "end": end})
            canonicalized.append({"start_seconds": start, "end_seconds": end, "text": str(row_text)})

        return canonicalized

    raise UnsupportedFormatError(
        "Transcript payload must be a JSON array (array of cue objects) or JSON string.",
        {"type": type(payload).__name__},
    )
