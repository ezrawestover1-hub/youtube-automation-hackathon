from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


def deterministic_id(namespace: str, seed: str, length: int = 20) -> str:
    """Create a short deterministic identifier for reproducible records."""
    import hashlib

    digest = hashlib.sha256(f"{namespace}:{seed}".encode("utf-8")).hexdigest()
    return f"{namespace}_{digest[:length]}"


class CanonicalTime(BaseModel):
    seconds: float = Field(ge=0, description="Elapsed seconds from start of recording.")


class RunStatus(str, Enum):
    PENDING = "PENDING"
    PARSE_OK = "PARSE_OK"
    EVENTS_DETECTED = "EVENTS_DETECTED"
    EVIDENCE_READY = "EVIDENCE_READY"
    RECOMMENDATION_READY = "RECOMMENDATION_READY"
    FAILED = "FAILED"
    DONE = "DONE"


class AssetKind(str, Enum):
    VIDEO = "VIDEO"
    TRANSCRIPT = "TRANSCRIPT"
    RETENTION = "RETENTION"
    OTHER = "OTHER"


class RetentionEventType(str, Enum):
    DROP = "DROP"
    SPIKE = "SPIKE"
    EXIT = "EXIT"
    REWATCH = "REWATCH"


class ErrorKind(str, Enum):
    VALIDATION = "VALIDATION_ERROR"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    PROCESSING_TIMEOUT = "PROCESSING_TIMEOUT"
    DEPENDENCY_FAILURE = "DEPENDENCY_FAILURE"


class DropFixErrorData(BaseModel):
    code: ErrorKind
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class UploadAsset(BaseModel):
    id: str
    project_id: str
    run_id: str
    kind: AssetKind
    filename: str
    mime_type: str
    checksum: str | None = None
    size_bytes: int | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AnalysisRun(BaseModel):
    id: str
    project_id: str
    status: RunStatus
    model_version: str = "dropfix-core-v1"
    settings: dict[str, Any] = Field(default_factory=dict)
    error: DropFixErrorData | None = None
    status_message: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None

    def transition(self, next_status: RunStatus, message: str = "") -> None:
        self.status = next_status
        self.status_message = message
        self.updated_at = datetime.utcnow()


class Project(BaseModel):
    id: str
    title: str
    type: str = "DROPFIX"
    owner_email: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RetentionEvent(BaseModel):
    id: str
    run_id: str
    type: RetentionEventType
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    severity: float = Field(ge=0, le=1)
    score: float = Field(ge=0, description="Normalized event strength.")
    metadata: dict[str, Any] = Field(default_factory=dict)


class EvidenceItem(BaseModel):
    id: str
    run_id: str
    kind: str
    source: str
    timestamp_seconds: float = Field(ge=0)
    event_ids: list[str] = Field(default_factory=list)
    value: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScoringProfile(BaseModel):
    detection_drop_delta_threshold: float = 0.045
    detection_spike_delta_threshold: float = 0.05
    detection_rewatch_delta_threshold: float = 0.06
    detection_exit_ratio_threshold: float = 0.18
    detection_min_sample_gap_seconds: float = 0.75
    detection_min_event_window_seconds: float = 0.5
    detection_merge_gap_seconds: float = 3.5
    recommendation_min_confidence: float = 0.10
    recommendation_baseline_impact_seconds: float = 2.8
    recommendation_action_item_cap: int = 3
    quality_min_points: int = 4
    quality_max_point_gap_seconds: float = 12.0
    quality_min_overlap_ratio: float = 0.05
    quality_min_overlap_events_ratio: float = 0.4
    quality_min_transcript_presence_ratio: float = 0.5


class QualityCheck(BaseModel):
    name: str
    passed: bool
    value: float | int | str | bool | None = None
    threshold: float | int | str | None = None
    message: str


class RunQualityReport(BaseModel):
    run_id: str
    overall_score: float = Field(ge=0, le=1)
    checks: list[QualityCheck] = Field(default_factory=list)
    finding_count: int = 0
    event_count: int = 0
    evidence_count: int = 0
    overlap_ratio: float = Field(default=0, ge=0, le=1)
    quality_profile: ScoringProfile | None = None


class Finding(BaseModel):
    id: str
    run_id: str
    category: str
    start_seconds: float = Field(ge=0)
    end_seconds: float = Field(ge=0)
    severity: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    estimated_impact_seconds: float = Field(ge=0)
    rationale: str
    observation: str
    recommendation: str
    limitation: str
    action_items: list[str] = Field(default_factory=list)
    evidence_ids: list[str]


class ExportPackage(BaseModel):
    id: str
    run_id: str
    format: str
    storage_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


@dataclass
class RunTransition:
    from_status: RunStatus
    to_status: RunStatus


ALLOWED_TRANSITIONS: dict[RunStatus, set[RunStatus]] = {
    RunStatus.PENDING: {
        RunStatus.PARSE_OK,
        RunStatus.FAILED,
    },
    RunStatus.PARSE_OK: {
        RunStatus.EVENTS_DETECTED,
        RunStatus.FAILED,
    },
    RunStatus.EVENTS_DETECTED: {
        RunStatus.EVIDENCE_READY,
        RunStatus.FAILED,
    },
    RunStatus.EVIDENCE_READY: {
        RunStatus.RECOMMENDATION_READY,
        RunStatus.FAILED,
    },
    RunStatus.RECOMMENDATION_READY: {RunStatus.DONE, RunStatus.FAILED},
    RunStatus.DONE: {RunStatus.DONE},
    RunStatus.FAILED: {RunStatus.FAILED},
}
