from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .errors import (
    DependencyFailureError,
    DropFixBaseError,
    ProcessingTimeoutError,
    UnsupportedFormatError,
)
from .models import (
    AnalysisRun,
    AssetKind,
    DropFixErrorData,
    EvidenceItem,
    Finding,
    RunQualityReport,
    ScoringProfile,
    Project,
    RetentionEvent,
    RunStatus,
)
from .service import DropFixService


router = APIRouter(prefix="")
service = DropFixService()


class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=1)
    owner_email: str | None = None


class ProjectCreateResponse(BaseModel):
    project: Project
    run_id: str
    status: RunStatus


class AssetCreateRequest(BaseModel):
    kind: str
    filename: str
    mime_type: str
    payload: str | None = None
    metadata: dict[str, Any] | None = None


class AssetCreateResponse(BaseModel):
    project_id: str
    run_id: str
    asset_id: str
    filename: str
    kind: AssetKind


class RunStatusResponse(BaseModel):
    run_id: str
    status: RunStatus
    status_message: str
    error: DropFixErrorData | None


class RunEventsResponse(BaseModel):
    run_id: str
    count: int
    events: list[RetentionEvent]


class RunEvidenceResponse(BaseModel):
    run_id: str
    count: int
    evidence: list[EvidenceItem]


class RunFindingsResponse(BaseModel):
    run_id: str
    count: int
    findings: list[Finding]


class RunExportResponse(BaseModel):
    package_id: str
    run_id: str
    format: str
    storage_url: str
    payload: dict[str, Any]


class ProfileUpdateRequest(BaseModel):
    payload: dict[str, Any] | str


class ProfileResponse(BaseModel):
    run_id: str
    profile: ScoringProfile


class DeleteProjectResponse(BaseModel):
    project_id: str
    deleted: bool
    detail: str


@router.post("/projects", response_model=ProjectCreateResponse, status_code=201)
def create_project(payload: ProjectCreateRequest) -> ProjectCreateResponse:
    project, run = service.create_project(payload.title, payload.owner_email)
    return ProjectCreateResponse(project=project, run_id=run.id, status=run.status)


@router.post("/runs/{run_id}/assets", response_model=AssetCreateResponse)
def upload_asset(run_id: str, payload: AssetCreateRequest) -> AssetCreateResponse:
    asset = service.create_asset(
        run_id=run_id,
        kind=payload.kind,
        filename=payload.filename,
        mime_type=payload.mime_type,
        metadata=payload.metadata,
        payload=payload.payload,
    )
    return AssetCreateResponse(
        project_id=asset.project_id,
        run_id=asset.run_id,
        asset_id=asset.id,
        filename=asset.filename,
        kind=asset.kind,
    )


@router.post("/runs/{run_id}/analyze", response_model=AnalysisRun)
def analyze_run(run_id: str) -> AnalysisRun:
    return service.queue_analysis(run_id)


@router.get("/runs/{run_id}/status", response_model=RunStatusResponse)
def run_status(run_id: str) -> RunStatusResponse:
    run = service.get_run_status(run_id)
    return RunStatusResponse(
        run_id=run.id,
        status=run.status,
        status_message=run.status_message,
        error=run.error,
    )


@router.get("/runs/{run_id}/events", response_model=RunEventsResponse)
def run_events(run_id: str) -> RunEventsResponse:
    events = service.get_run_events(run_id)
    return RunEventsResponse(run_id=run_id, count=len(events), events=events)


@router.get("/runs/{run_id}/evidence", response_model=RunEvidenceResponse)
def run_evidence(run_id: str) -> RunEvidenceResponse:
    evidence = service.get_run_evidence(run_id)
    return RunEvidenceResponse(run_id=run_id, count=len(evidence), evidence=evidence)


@router.get("/runs/{run_id}/findings", response_model=RunFindingsResponse)
def run_findings(run_id: str) -> RunFindingsResponse:
    findings = service.get_run_findings(run_id)
    return RunFindingsResponse(run_id=run_id, count=len(findings), findings=findings)


@router.get("/runs/{run_id}/quality", response_model=RunQualityReport)
def run_quality(run_id: str) -> RunQualityReport:
    return service.get_run_quality(run_id)


@router.post("/runs/{run_id}/export", response_model=RunExportResponse)
def run_export(run_id: str, format: str = "json", include_audit: bool = True) -> RunExportResponse:
    return RunExportResponse(**service.export_run(run_id, format=format, include_audit=include_audit))


@router.get("/runs/{run_id}/profile", response_model=ProfileResponse)
def get_profile(run_id: str) -> ProfileResponse:
    profile = service.get_run_profile(run_id)
    return ProfileResponse(run_id=run_id, profile=profile)


@router.put("/runs/{run_id}/profile", response_model=ProfileResponse)
def set_profile(run_id: str, payload: ProfileUpdateRequest) -> ProfileResponse:
    profile = service.set_run_profile(run_id, payload.payload)
    return ProfileResponse(run_id=run_id, profile=profile)


@router.get("/runs/{run_id}/audit")
def run_audit(run_id: str) -> dict[str, list[dict[str, Any]]]:
    return {"run_id": run_id, "audit": service.get_run_audit(run_id)}


@router.delete("/projects/{project_id}", response_model=DeleteProjectResponse)
def delete_project(project_id: str) -> DeleteProjectResponse:
    deleted = service.delete_project(project_id)
    detail = "project deleted" if deleted else "project already deleted"
    return DeleteProjectResponse(project_id=project_id, deleted=True, detail=detail)


@router.exception_handler(DropFixBaseError)
async def handle_application_error(_: Any, exc: DropFixBaseError):
    return JSONResponse(
        status_code=getattr(exc, "status_code", 400),
        content={"error": exc.to_payload()},
    )


@router.exception_handler(UnsupportedFormatError)
async def handle_unsupported_format(_: Any, exc: UnsupportedFormatError):
    return JSONResponse(
        status_code=415,
        content={"error": exc.to_payload()},
    )


@router.exception_handler(ProcessingTimeoutError)
async def handle_timeout(_: Any, exc: ProcessingTimeoutError):
    return JSONResponse(
        status_code=408,
        content={"error": exc.to_payload()},
    )


@router.exception_handler(DependencyFailureError)
async def handle_dependency(_: Any, exc: DependencyFailureError):
    return JSONResponse(
        status_code=503,
        content={"error": exc.to_payload()},
    )
