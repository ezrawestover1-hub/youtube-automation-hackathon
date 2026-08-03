from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
from typing import Any

from .errors import DropFixBaseError
from .models import (
    ALLOWED_TRANSITIONS,
    AnalysisRun,
    DropFixErrorData,
    ErrorKind,
    EvidenceItem,
    ExportPackage,
    Finding,
    Project,
    RetentionEvent,
    RunStatus,
    RunQualityReport,
    UploadAsset,
    deterministic_id,
)


@dataclass
class InMemoryStore:
    projects: dict[str, Project] = field(default_factory=dict)
    runs: dict[str, AnalysisRun] = field(default_factory=dict)
    project_runs: dict[str, list[str]] = field(default_factory=dict)
    assets: dict[str, list[UploadAsset]] = field(default_factory=dict)
    status_audit: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    events: dict[str, list[RetentionEvent]] = field(default_factory=dict)
    evidence: dict[str, list[EvidenceItem]] = field(default_factory=dict)
    findings: dict[str, list[Finding]] = field(default_factory=dict)
    exports: dict[str, list[ExportPackage]] = field(default_factory=dict)
    quality_reports: dict[str, RunQualityReport] = field(default_factory=dict)
    retention_points_by_run: dict[str, list[dict[str, float]]] = field(default_factory=dict)
    transcript_segments_by_run: dict[str, list[dict[str, str | float]]] = field(default_factory=dict)

    def create_project(self, title: str, owner_email: str | None = None) -> Project:
        project_id = deterministic_id("prj", f"{title}:{owner_email or \"\"}:{datetime.utcnow().isoformat()}")
        project = Project(id=project_id, title=title, owner_email=owner_email)
        self.projects[project_id] = project
        self.project_runs[project_id] = []
        self.assets[project_id] = []
        self.status_audit[project_id] = []
        return project

    def create_run(self, project_id: str, settings: dict[str, Any] | None = None, deterministic_seed: str | None = None) -> AnalysisRun:
        if project_id not in self.projects:
            raise DropFixBaseError(ErrorKind.VALIDATION, "Project does not exist.", {"project_id": project_id})
        seed_settings = json.dumps(settings or {}, sort_keys=True, ensure_ascii=False)
        seed_value = deterministic_seed or f"{project_id}:{seed_settings}:{len(self.project_runs[project_id])}"
        run_seed = f"{project_id}:{seed_value}"
        run_id = deterministic_id("run", run_seed)
        run = AnalysisRun(id=run_id, project_id=project_id, status=RunStatus.PENDING, settings=settings or {})
        self.runs[run_id] = run
        self.project_runs[project_id].append(run_id)
        self.assets[run_id] = []
        self.events[run_id] = []
        self.evidence[run_id] = []
        self.findings[run_id] = []
        self.exports[run_id] = []
        self.quality_reports[run_id] = RunQualityReport(run_id=run_id, overall_score=0.0)
        self.retention_points_by_run[run_id] = []
        self.transcript_segments_by_run[run_id] = []
        self.status_audit[run_id] = []
        return run

    def get_project(self, project_id: str) -> Project:
        if project_id not in self.projects:
            raise DropFixBaseError(ErrorKind.VALIDATION, "Project not found.", {"project_id": project_id})
        return self.projects[project_id]

    def get_run(self, run_id: str) -> AnalysisRun:
        if run_id not in self.runs:
            raise DropFixBaseError(ErrorKind.VALIDATION, "Run not found.", {"run_id": run_id})
        return self.runs[run_id]

    def add_asset(self, run_id: str, asset_data: UploadAsset) -> UploadAsset:
        run = self.get_run(run_id)
        if run.status not in {RunStatus.PENDING, RunStatus.PARSE_OK, RunStatus.EVENTS_DETECTED, RunStatus.EVIDENCE_READY}:
            raise DropFixBaseError(
                ErrorKind.VALIDATION,
                "Cannot add assets in current status.",
                {"run_id": run_id, "status": run.status},
            )
        if run_id not in self.assets:
            self.assets[run_id] = []
        self.assets[run_id].append(asset_data)
        return asset_data

    def list_assets(self, run_id: str) -> list[UploadAsset]:
        if run_id not in self.assets:
            return []
        return self.assets[run_id]

    def set_run_status(self, run_id: str, next_status: RunStatus, message: str = "") -> AnalysisRun:
        run = self.get_run(run_id)
        if next_status not in ALLOWED_TRANSITIONS[run.status] and next_status != run.status:
            raise DropFixBaseError(
                ErrorKind.VALIDATION,
                f"Invalid run transition from {run.status} to {next_status}.",
                {"run_id": run_id, "from": run.status, "to": next_status},
            )
        run.transition(next_status, message)
        if next_status in {RunStatus.DONE, RunStatus.FAILED}:
            run.completed_at = datetime.utcnow()
        self.status_audit.setdefault(run_id, []).append(
            {
                "status": next_status.value,
                "message": message,
                "at": run.updated_at.isoformat(),
            }
        )
        return run

    def fail_run(self, run_id: str, code: ErrorKind, message: str, details: dict[str, Any]) -> AnalysisRun:
        run = self.get_run(run_id)
        run.error = DropFixErrorData(code=code, message=message, details=details)
        return self.set_run_status(run_id, RunStatus.FAILED, message)

    def delete_project(self, project_id: str) -> bool:
        if project_id not in self.projects:
            return False

        run_ids = self.project_runs.pop(project_id, [])
        for run_id in run_ids:
            self.runs.pop(run_id, None)
            self.assets.pop(run_id, None)
            self.events.pop(run_id, None)
            self.evidence.pop(run_id, None)
            self.findings.pop(run_id, None)
            self.exports.pop(run_id, None)
            self.quality_reports.pop(run_id, None)
            self.status_audit.pop(run_id, None)
            self.retention_points_by_run.pop(run_id, None)
            self.transcript_segments_by_run.pop(run_id, None)
        self.projects.pop(project_id, None)
        self.status_audit.pop(project_id, None)
        self.assets.pop(project_id, None)
        return True

    def list_run_audit(self, run_id: str) -> list[dict[str, Any]]:
        return self.status_audit.get(run_id, [])

    def make_event_id(self, run_id: str, seed: int) -> str:
        return deterministic_id("event", f"{run_id}:{seed}")

    def make_evidence_id(self, run_id: str, seed: int) -> str:
        return deterministic_id("evidence", f"{run_id}:{seed}")

    def make_finding_id(self, run_id: str, seed: int) -> str:
        return deterministic_id("finding", f"{run_id}:{seed}")

    def make_export_id(self, run_id: str, seed: int) -> str:
        return deterministic_id("export", f"{run_id}:{seed}")

    def set_transcript_segments(self, run_id: str, transcript_segments: list[dict[str, Any]]) -> None:
        self.get_run(run_id)
        normalized = [
            {
                "start_seconds": float(item["start_seconds"]),
                "end_seconds": float(item["end_seconds"]),
                "text": str(item.get("text", "")),
                "raw": item,
            }
            for item in transcript_segments
        ]
        normalized.sort(key=lambda item: float(item["start_seconds"]))
        self.transcript_segments_by_run[run_id] = normalized

    def get_transcript_segments(self, run_id: str) -> list[dict[str, Any]]:
        self.get_run(run_id)
        return list(self.transcript_segments_by_run.get(run_id, []))

    def set_retention_points(self, run_id: str, points: list[dict[str, float]]) -> None:
        self.get_run(run_id)
        existing = self.retention_points_by_run.get(run_id, [])
        all_points = existing + points
        all_points.sort(key=lambda item: float(item["time_seconds"]))
        deduped: list[dict[str, float]] = []
        last_time = None
        for point in all_points:
            current_time = float(point["time_seconds"])
            if last_time is None or current_time != last_time:
                deduped.append(point)
                last_time = current_time
        self.retention_points_by_run[run_id] = deduped

    def replace_retention_points(self, run_id: str, points: list[dict[str, float]]) -> None:
        self.get_run(run_id)
        normalized = [
            {
                "time_seconds": float(point["time_seconds"]),
                "retention_ratio": float(point["retention_ratio"]),
                "metadata": point.get("metadata", {}),
            }
            for point in points
        ]
        normalized.sort(key=lambda item: float(item["time_seconds"]))
        self.retention_points_by_run[run_id] = normalized

    def upsert_events(self, run_id: str, events: list[RetentionEvent]) -> list[RetentionEvent]:
        self.get_run(run_id)
        self.events[run_id] = list(events)
        return self.events[run_id]

    def list_events(self, run_id: str) -> list[RetentionEvent]:
        self.get_run(run_id)
        return list(self.events.get(run_id, []))

    def upsert_evidence(self, run_id: str, evidence_items: list[EvidenceItem]) -> list[EvidenceItem]:
        self.get_run(run_id)
        self.evidence[run_id] = list(evidence_items)
        return self.evidence[run_id]

    def list_evidence(self, run_id: str) -> list[EvidenceItem]:
        self.get_run(run_id)
        return list(self.evidence.get(run_id, []))

    def upsert_findings(self, run_id: str, findings: list[Finding]) -> list[Finding]:
        self.get_run(run_id)
        self.findings[run_id] = list(findings)
        return self.findings[run_id]

    def list_findings(self, run_id: str) -> list[Finding]:
        self.get_run(run_id)
        return list(self.findings.get(run_id, []))

    def upsert_export(self, run_id: str, export_package: ExportPackage) -> ExportPackage:
        self.get_run(run_id)
        self.exports[run_id].append(export_package)
        return export_package

    def list_exports(self, run_id: str) -> list[ExportPackage]:
        self.get_run(run_id)
        return list(self.exports.get(run_id, []))

    def upsert_quality_report(self, run_id: str, quality_report: RunQualityReport) -> RunQualityReport:
        self.get_run(run_id)
        self.quality_reports[run_id] = quality_report
        return quality_report

    def get_quality_report(self, run_id: str) -> RunQualityReport:
        self.get_run(run_id)
        return self.quality_reports.get(run_id, RunQualityReport(run_id=run_id, overall_score=0.0))


GLOBAL_STORE = InMemoryStore()
