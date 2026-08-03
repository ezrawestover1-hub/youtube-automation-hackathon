# DropFix Sprint 1 Scaffold

This is a minimal backend foundation for the hackathon Sprint 1 goals:

- Canonical data contracts for project/run/assets/events/evidence/findings/exports.
- Deterministic IDs for replayability.
- Run lifecycle with explicit states and transitions.
- Standardized structured errors.
- Minimal ingestion validation for retention CSV and transcript payloads.
- Starter API routes for project/run orchestration.

## API contracts

- `POST /projects`
  - Creates a project and an initial analysis run.
- `POST /runs/{run_id}/assets`
  - Adds a validated asset (`VIDEO`, `TRANSCRIPT`, `RETENTION`, or `OTHER`) to a run.
  - MVP currently supports transcript/retention validation when payload is supplied.
- `POST /runs/{run_id}/analyze`
  - Runs the current Sprint 1 pipeline stub and advances run state through deterministic transitions.
- `GET /runs/{run_id}/events`
  - Returns currently detected retention events produced by the deterministic detector.
- `GET /runs/{run_id}/evidence`
  - Returns transcript-aligned evidence entries for each detected event.
- `GET /runs/{run_id}/findings`
  - Returns deterministic recommendation findings with confidence, rationale, estimated impact, and action items.
- `POST /runs/{run_id}/export`
  - Exports run outputs as `json`, `markdown`, or `compact_json`.
- `GET /runs/{run_id}/quality`
  - Returns quality checks (data coverage, overlap ratios, confidence health) and overall quality score.
- `GET /runs/{run_id}/profile`
  - Returns the scoring profile currently used by this run.
- `PUT /runs/{run_id}/profile`
  - Sets a custom scoring profile (JSON object or YAML-like plain text in request payload) for reproducible tuning.
- `GET /runs/{run_id}/status`
  - Returns run status, state message, and optional structured error.
- `GET /runs/{run_id}/audit`
  - Returns state transition audit log.
- `DELETE /projects/{project_id}`
  - Idempotent project deletion.

## Run states

`PENDING -> PARSE_OK -> EVENTS_DETECTED -> EVIDENCE_READY -> RECOMMENDATION_READY -> DONE`

and `FAILED` for any rejection.

## Notes

- Idempotent delete behavior is implemented for project cleanup.
- Errors are returned as structured JSON with a `code`, `message`, and `details`.
- This scaffold intentionally avoids real video storage and AI generation to keep Sprint 1 bounded.
- Sprint 2 adds deterministic retention-event extraction with type-labeled, threshold-driven candidates.
- Sprint 3 adds transcript upload + deterministic alignment that links each event to supporting transcript evidence.
- Sprint 5 adds quality gates, profile-tunable scoring config, and a quality report endpoint.

## Run locally

```bash
cd backend
python -m venv .venv
. ./.venv/Scripts/Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
