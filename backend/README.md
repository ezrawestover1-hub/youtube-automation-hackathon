# DropFix Backend

This backend is the local-first, judged-as-code core of our YouTube creator automation project.

## Why this backend is polished for judging

- It ships as versioned code only (no domain dependency required).
- Every command is reproducible from a fresh clone.
- Outputs are written locally and can be inspected in a deterministic way.
- It includes quality gates and profile-tunable behavior for reliable, tunable automation.

## API contracts

- `POST /projects`
  - Create a project and an initial analysis run.
- `POST /runs/{run_id}/assets`
  - Add validated assets (`VIDEO`, `TRANSCRIPT`, `RETENTION`, `OTHER`).
- `POST /runs/{run_id}/analyze`
  - Execute the analysis pipeline and transition the run through lifecycle states.
- `GET /runs/{run_id}/events`
  - Return detected retention events.
- `GET /runs/{run_id}/evidence`
  - Return transcript-aligned evidence for each event.
- `GET /runs/{run_id}/findings`
  - Return recommendation findings with confidence and action items.
- `POST /runs/{run_id}/export`
  - Export run outputs as `json`, `markdown`, or `compact_json`.
- `GET /runs/{run_id}/quality`
  - Return quality checks and quality score.
- `GET /runs/{run_id}/profile`
  - Return current scoring profile.
- `PUT /runs/{run_id}/profile`
  - Set a custom scoring profile (JSON object or YAML-like text payload).
- `GET /runs/{run_id}/status`
  - Return run status and structured error context.
- `GET /runs/{run_id}/audit`
  - Return run state transition audit log.
- `DELETE /projects/{project_id}`
  - Idempotent cleanup.

## Run states

`PENDING -> PARSE_OK -> EVENTS_DETECTED -> EVIDENCE_READY -> RECOMMENDATION_READY -> DONE`  
and `FAILED` for rejected/invalid runs.

## Run locally

```powershell
cd backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open: `http://127.0.0.1:8000/docs`

## Setup checks (quick)

- Confirm structured responses:
  - `POST /projects`
  - `GET /runs/{run_id}/quality`
- Confirm fallback safety:
  - malformed input should return a structured error with `code`, `message`, and `details`.

## Notes

- This module intentionally avoids any hardcoded secrets.
- The architecture favors local execution for reliability during judging.
- Sprint progression has been preserved for development traceability.
