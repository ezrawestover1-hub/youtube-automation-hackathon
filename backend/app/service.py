from __future__ import annotations

from typing import Any

from .alignment import TranscriptAlignmentConfig, align_events_to_transcript
from .errors import ValidationError
from .event_detection import RetentionEventConfig, detect_events
from .models import (
    AssetKind,
    AnalysisRun,
    EvidenceItem,
    ErrorKind,
    ExportPackage,
    Finding,
    RetentionEvent,
    RunQualityReport,
    RunStatus,
    ScoringProfile,
    UploadAsset,
    deterministic_id,
)
from .recommendations import RecommendationConfig, build_findings
from .quality import build_quality_report
from .repository import GLOBAL_STORE
from .validation import parse_retention_csv, parse_transcript
import json


class DropFixService:
    def __init__(self, store=GLOBAL_STORE):
        self.store = store

    def create_project(self, title: str, owner_email: str | None = None) -> tuple:
        project = self.store.create_project(title=title, owner_email=owner_email)
        run = self.store.create_run(project.id)
        return project, run

    def get_project(self, project_id: str):
        return self.store.get_project(project_id)

    def create_asset(
        self,
        run_id: str,
        kind: str,
        filename: str,
        mime_type: str,
        metadata: dict[str, Any] | None = None,
        payload: str | None = None,
    ) -> UploadAsset:
        asset_kind = AssetKind(kind)
        if asset_kind == AssetKind.RETENTION:
            if payload is None:
                raise ValidationError("Retention asset requires a text payload in MVP mode.", {"kind": kind})
            points = parse_retention_csv(payload)
            preview = points[:3]
            checksum_source = "|".join(f"{row['time_seconds']}:{row['retention_ratio']}" for row in preview)
            self.store.set_retention_points(run_id, points)
        elif asset_kind == AssetKind.TRANSCRIPT:
            if payload is None:
                raise ValidationError("Transcript asset requires a text payload in MVP mode.", {"kind": kind})
            transcript = parse_transcript(payload)
            self.store.set_transcript_segments(run_id, transcript)
            preview = f"{len(transcript)} cue rows"
            checksum_source = f"transcript:{len(transcript)}"
        else:
            checksum_source = f"{len(payload or '')}"
            preview = payload[:200] if payload else ""

        metadata = metadata or {}
        metadata.setdefault("preview", str(preview)[:500])
        checksum = deterministic_id(
            "ck",
            f"{asset_kind.value}:{filename}:{checksum_source}",
            length=18,
        )
        asset = UploadAsset(
            id=deterministic_id(
                "asset",
                f"{run_id}:{asset_kind.value}:{filename}:{checksum}",
                length=18,
            ),
            project_id=self.store.get_run(run_id).project_id,
            run_id=run_id,
            kind=asset_kind,
            filename=filename,
            mime_type=mime_type,
            checksum=checksum,
            size_bytes=len(payload or ""),
            metadata=metadata,
        )
        return self.store.add_asset(run_id, asset)

    def get_run_status(self, run_id: str) -> AnalysisRun:
        return self.store.get_run(run_id)

    def get_run_events(self, run_id: str) -> list[RetentionEvent]:
        return self.store.list_events(run_id)

    def get_run_evidence(self, run_id: str) -> list[EvidenceItem]:
        return self.store.list_evidence(run_id)

    def get_run_findings(self, run_id: str) -> list[Finding]:
        return self.store.list_findings(run_id)

    def set_run_profile(self, run_id: str, payload: dict[str, Any] | str) -> ScoringProfile:
        self.store.get_run(run_id)
        parsed = self._normalize_profile_payload(payload)
        profile = ScoringProfile(**parsed)
        self.store.get_run(run_id).settings["scoring_profile"] = profile.dict()
        return profile

    def get_run_profile(self, run_id: str) -> ScoringProfile:
        run = self.store.get_run(run_id)
        raw_profile = run.settings.get("scoring_profile") or {}
        if isinstance(raw_profile, ScoringProfile):
            return raw_profile
        if not isinstance(raw_profile, dict):
            raise ValidationError("Run scoring profile is corrupted.", {"run_id": run_id})
        return ScoringProfile(**raw_profile)

    def get_run_quality(self, run_id: str) -> RunQualityReport:
        self.store.get_run(run_id)
        return self.store.get_quality_report(run_id)

    @staticmethod
    def _parse_yaml_profile(text: str) -> dict[str, Any]:
        output: dict[str, Any] = {}
        for line in text.splitlines():
            clean = line.strip()
            if not clean or clean.startswith("#"):
                continue
            if ":" not in clean:
                continue
            key, value = clean.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'\"")
            if not key:
                continue
            if value.lower() in {"true", "false"}:
                output[key] = value.lower() == "true"
            else:
                try:
                    if "." in value:
                        output[key] = float(value)
                    else:
                        output[key] = int(value)
                except ValueError:
                    output[key] = value
        return output

    @staticmethod
    def _normalize_profile_payload(payload: dict[str, Any] | str) -> dict[str, Any]:
        if isinstance(payload, str):
            text = payload.strip()
            if not text:
                return {}
            if text.lstrip().startswith("{"):
                try:
                    return dict(json.loads(text))
                except json.JSONDecodeError as err:
                    raise ValidationError("Profile payload is invalid JSON.", {"error": str(err), "payload": text[:200]})
            return DropFixService._parse_yaml_profile(text)
        if isinstance(payload, dict):
            return payload
        raise ValidationError("Profile payload must be JSON/YAML string or object.", {})

    @staticmethod
    def _build_detection_cfg(profile: ScoringProfile) -> RetentionEventConfig:
        return RetentionEventConfig(
            drop_delta_threshold=profile.detection_drop_delta_threshold,
            spike_delta_threshold=profile.detection_spike_delta_threshold,
            rewatch_delta_threshold=profile.detection_rewatch_delta_threshold,
            exit_ratio_threshold=profile.detection_exit_ratio_threshold,
            min_sample_gap_seconds=profile.detection_min_sample_gap_seconds,
            min_event_window_seconds=profile.detection_min_event_window_seconds,
            merge_gap_seconds=profile.detection_merge_gap_seconds,
        )

    @staticmethod
    def _build_alignment_cfg(profile: ScoringProfile) -> TranscriptAlignmentConfig:
        return TranscriptAlignmentConfig(min_overlap_ratio=profile.quality_min_overlap_ratio)

    @staticmethod
    def _build_recommendation_cfg(profile: ScoringProfile) -> RecommendationConfig:
        return RecommendationConfig(
            min_confidence=profile.recommendation_min_confidence,
            baseline_impact_seconds=profile.recommendation_baseline_impact_seconds,
            action_item_cap=profile.recommendation_action_item_cap,
            min_overlap_ratio=profile.quality_min_overlap_ratio,
        )

    def export_run(self, run_id: str, format: str = "json", include_audit: bool = True) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        fmt = (format or "json").lower()
        if fmt not in {"json", "markdown", "compact_json"}:
            raise ValidationError(
                "Unsupported export format. Use json, markdown, or compact_json.",
                {"requested_format": fmt, "supported": ["json", "markdown", "compact_json"]},
            )

        events = self.store.list_events(run_id)
        evidence = self.store.list_evidence(run_id)
        findings = self.store.list_findings(run_id)
        quality = self.store.get_quality_report(run_id)
        audit = self.store.list_run_audit(run_id) if include_audit else []
        package_id = self.store.make_export_id(run_id, len(self.store.list_exports(run_id)))

        base_payload = {
            "run": {
                "run_id": run.id,
                "project_id": run.project_id,
                "status": run.status.value,
                "status_message": run.status_message,
                "model_version": run.model_version,
                "settings": run.settings,
            },
            "counts": {"events": len(events), "evidence": len(evidence), "findings": len(findings)},
            "events": [event.model_dump() for event in events],
            "evidence": [item.model_dump() for item in evidence],
            "findings": [item.model_dump() for item in findings],
            "quality": quality.model_dump(),
            "audit": audit if include_audit else [],
            "metadata": {"export_format": fmt, "generated_by": "DropFix-MVP"},
        }

        if fmt == "markdown":
            payload = {
                "markdown": self._render_markdown_export(run_id, events, evidence, findings),
                "counts": base_payload["counts"],
                "quality": quality.model_dump(),
            }
        elif fmt == "compact_json":
            payload = {
                "run_id": run.id,
                "status": run.status.value,
                "events": len(events),
                "evidence": len(evidence),
                "findings": len(findings),
                "quality_score": quality.overall_score,
            }
        else:
            payload = base_payload

        storage_url = f"in-memory://export/{run_id}/{package_id}"
        package = ExportPackage(
            id=package_id,
            run_id=run_id,
            format=fmt,
            storage_url=storage_url,
        )
        self.store.upsert_export(run_id, package)

        return {
            "package_id": package.id,
            "run_id": run_id,
            "format": fmt,
            "storage_url": storage_url,
            "payload": payload,
        }

    @staticmethod
    def _render_markdown_export(
        run_id: str,
        events: list[RetentionEvent],
        evidence: list[EvidenceItem],
        findings: list[Finding],
    ) -> str:
        lines = [
            f"# DropFix Export: {run_id}",
            "",
            f"- events: {len(events)}",
            f"- evidence: {len(evidence)}",
            f"- findings: {len(findings)}",
            "",
            "## Findings",
        ]
        for idx, finding in enumerate(findings, start=1):
            lines.extend(
                [
                    f"{idx}. **{finding.category}** ({finding.confidence:.2f} confidence)",
                    f"   - window: {finding.start_seconds:.2f}-{finding.end_seconds:.2f}s",
                    f"   - observation: {finding.observation}",
                    f"   - recommendation: {finding.recommendation}",
                    f"   - rationale: {finding.rationale}",
                    f"   - limitation: {finding.limitation}",
                    f"   - impact estimate: {finding.estimated_impact_seconds:.2f}s",
                    "",
                ]
            )
        return "\n".join(lines)

    def queue_analysis(
        self,
        run_id: str,
        detection_cfg: RetentionEventConfig | None = None,
        alignment_cfg: TranscriptAlignmentConfig | None = None,
    ) -> AnalysisRun:
        run = self.store.get_run(run_id)
        profile = self.get_run_profile(run_id)
        assets = self.store.list_assets(run_id)
        if not assets:
            return self.store.fail_run(
                run_id,
                ErrorKind.INSUFFICIENT_DATA,
                "No assets uploaded for this run.",
                {"run_id": run_id},
            )

        has_retention = any(a.kind == AssetKind.RETENTION for a in assets)
        if not has_retention:
            return self.store.fail_run(
                run_id,
                ErrorKind.INSUFFICIENT_DATA,
                "At least one RETENTION asset is required for deterministic MVP.",
                {"run_id": run_id},
            )

        if run.status != RunStatus.PENDING:
            return run

        run = self.store.set_run_status(run_id, RunStatus.PARSE_OK, "Parsed and validated all provided assets.")

        retention_points = self.store.get_retention_points(run_id)
        if len(retention_points) < 2:
            return self.store.fail_run(
                run_id,
                ErrorKind.INSUFFICIENT_DATA,
                "Retention CSV does not contain enough points for analysis.",
                {"run_id": run_id, "point_count": len(retention_points)},
            )
        if len(retention_points) < profile.quality_min_points:
            return self.store.fail_run(
                run_id,
                ErrorKind.INSUFFICIENT_DATA,
                "Retention CSV quality threshold failed. Add more points to reduce sparse-sampling false positives.",
                {
                    "run_id": run_id,
                    "point_count": len(retention_points),
                    "required_point_count": profile.quality_min_points,
                },
            )
        if profile.quality_max_point_gap_seconds > 0 and len(retention_points) >= 2:
            times = sorted(float(item["time_seconds"]) for item in retention_points)
            max_gap = max(times[i] - times[i - 1] for i in range(1, len(times)))
            if max_gap > profile.quality_max_point_gap_seconds:
                return self.store.fail_run(
                    run_id,
                    ErrorKind.INSUFFICIENT_DATA,
                    "Retention CSV sampling gap too wide for reliable spike/drop detection.",
                    {
                        "run_id": run_id,
                        "max_gap_seconds": max_gap,
                        "max_gap_threshold_seconds": profile.quality_max_point_gap_seconds,
                    },
                )

        effective_detection_cfg = detection_cfg or self._build_detection_cfg(profile)
        effective_alignment_cfg = alignment_cfg or self._build_alignment_cfg(profile)
        effective_recommendation_cfg = self._build_recommendation_cfg(profile)

        detected = detect_events(retention_points, effective_detection_cfg)
        if not detected:
            self.store.upsert_evidence(run_id, [])
            self.store.upsert_findings(run_id, [])
            run = self.store.set_run_status(run_id, RunStatus.EVENTS_DETECTED, "No statistically-significant events detected.")
            run = self.store.set_run_status(run_id, RunStatus.EVIDENCE_READY, "No event evidence was produced.")
            run = self.store.set_run_status(run_id, RunStatus.RECOMMENDATION_READY, "MVP recommendation stub completed.")
            quality = build_quality_report(run_id, profile, retention_points, [], [], [])
            self.store.upsert_quality_report(run_id, quality)
            return self.store.set_run_status(run_id, RunStatus.DONE, "No-op analysis complete with zero findings.")

        retention_events: list[RetentionEvent] = []
        event_bundles: list[dict[str, Any]] = []
        for idx, item in enumerate(detected):
            event = RetentionEvent(
                id=self.store.make_event_id(run_id, idx),
                run_id=run_id,
                type=item["type"],
                start_seconds=item["start_seconds"],
                end_seconds=item["end_seconds"],
                severity=item["severity"],
                score=item["score"],
                metadata=item["metadata"],
            )
            retention_events.append(event)
            event_bundles.append(
                {
                    "id": event.id,
                    "run_id": event.run_id,
                    "start_seconds": event.start_seconds,
                    "end_seconds": event.end_seconds,
                    "evidence_id": self.store.make_evidence_id(run_id, idx),
                }
            )

        self.store.upsert_events(run_id, retention_events)

        transcript_segments = self.store.get_transcript_segments(run_id)
        evidence_items, alignments = align_events_to_transcript(
            event_bundles,
            transcript_segments,
            effective_alignment_cfg,
        )
        self.store.upsert_evidence(run_id, evidence_items)
        findings = build_findings(retention_events, evidence_items, effective_recommendation_cfg)
        self.store.upsert_findings(run_id, findings)
        quality = build_quality_report(run_id, profile, retention_points, retention_events, evidence_items, findings)
        self.store.upsert_quality_report(run_id, quality)

        run = self.store.set_run_status(run_id, RunStatus.EVENTS_DETECTED, f"Detected {len(retention_events)} event(s).")
        run = self.store.set_run_status(
            run_id,
            RunStatus.EVIDENCE_READY,
            f"Aligned {len(alignments)} evidence item(s) from transcript.",
        )
        run = self.store.set_run_status(
            run_id,
            RunStatus.RECOMMENDATION_READY,
            f"Generated {len(findings)} recommendation finding(s).",
        )
        return self.store.set_run_status(run_id, RunStatus.DONE, "Event-to-transcript alignment completed.")

    def delete_project(self, project_id: str) -> bool:
        return self.store.delete_project(project_id)

    def get_run_audit(self, run_id: str) -> list[dict[str, Any]]:
        return self.store.list_run_audit(run_id)
