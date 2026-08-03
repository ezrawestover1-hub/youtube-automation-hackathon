# Local development and judge verification checklist

## Goal

Prove local execution in under 5 minutes from a clean environment.

## Prerequisites

- Python 3.11+
- Git

## Steps

1. Clone repository and enter backend

```powershell
git clone https://github.com/ezrawestover1-hub/youtube-automation-hackathon.git
cd youtube-automation-hackathon\backend
```

2. Create and activate a virtual environment

```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

3. Install dependencies

```powershell
pip install -r requirements.txt
```

4. Optional environment setup

```powershell
Copy-Item .env.example .env
```

5. Start server

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

6. Open interactive API docs

`http://127.0.0.1:8000/docs`

## Validation checklist (judges)

- Service starts without errors.
- `GET /runs/{run_id}/quality` returns a structured quality object once a run exists.
- `GET /runs/{run_id}/profile` reflects profile changes after `PUT /runs/{run_id}/profile`.
- No secrets or API keys are required to run baseline deterministic flows.
- Failure cases return JSON `{code, message, details}` responses.

## Output expectations

- If you run sample inputs, results should be written to `outputs/` (local path, gitignored).
- Generated exports should include quality score and profile metadata.

