# DropFix — YouTube Automation Hackathon Project

## What this is

DropFix is a **local-first** backend project built for the Devpost YouTube Automation Hackathon.  
It automates a creator workflow pain point: turning retention insights into concrete, actionable recommendations with reproducible quality checks.

This is the competition version we want judges to evaluate quickly:

- source is fully available in GitHub,
- setup is local-only (no new domain required),
- outputs are deterministic and inspectable in versioned files.

## Submission architecture (polished and judge-ready)

- **Repository-first**: all logic, scripts, docs, and evidence live in GitHub.
- **No required hosting domain**: the tool runs from local code and produces files locally.
- **Transparent execution**: every key step is documented and reproducible.
- **No secret leakage**: only `.env.example` is committed, never real credentials.

## One-click showcase for judges

- Open the local, recordable highlight deck:
  - [highlights/dropfix-highlight-showcase.html](C:\\Users\\3ewes\\Documents\\Codex\\2026-08-03\\ok\\highlights\\dropfix-highlight-showcase.html)
- Run the helper launcher:
  - [highlights/run-highlight-showcase.ps1](C:\\Users\\3ewes\\Documents\\Codex\\2026-08-03\\ok\\highlights\\run-highlight-showcase.ps1)
- Use the scene-by-scene talking track:
  - [highlights/highlight-rundown.md](C:\\Users\\3ewes\\Documents\\Codex\\2026-08-03\\ok\\highlights/highlight-rundown.md)

## Repository layout

- `backend/` — FastAPI service and core pipeline code
- `backend/app/` — API endpoints, models, services, quality scoring, and repository layer
- `backend/requirements.txt` — Python runtime dependencies
- `backend/.env.example` — environment variable template
- `outputs/` — generated run outputs (gitignored)
- `work/` — scratch notes and experiments (ignored by README references)
- `local-dev.md` — copy-paste local run + verification commands
- `highlights/` — polished visual demo and recording helpers

## Quick start (5-command path)

1. Clone and enter project

```powershell
git clone https://github.com/ezrawestover1-hub/youtube-automation-hackathon.git
cd youtube-automation-hackathon
```

2. Create local environment

```powershell
cd backend
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
```

3. Install dependencies

```powershell
pip install -r requirements.txt
```

4. Configure secrets (optional for demo run)

```powershell
Copy-Item .env.example .env
```

5. Run the service

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open `http://127.0.0.1:8000/docs` for live API docs.

## Why no external domain?

For this hackathon, a domain is optional overhead.  
The strongest path for consistency is to prove:

- reproducible commands,
- deterministic output,
- clean fallback behavior,
- and judge-usable evidence files in `outputs/`.

If we add a hosted UI later, it will be an enhancement, not the primary submission dependency.

## Security and safety defaults

- `.env` and other sensitive artifacts are gitignored.
- API keys are never hardcoded.
- Pipeline failures return structured errors and actionable guidance.

## Current quality posture

- profile-tunable analysis thresholds (`/runs/{run_id}/profile`)
- quality gating and score reporting (`/runs/{run_id}/quality`)
- deterministic evidence and recommendation outputs
- structured run statuses and audit trail

For full API details, open the backend API docs and the backend README.

## Useful next commands

- API documentation: `http://127.0.0.1:8000/docs`
- Health check: `GET /runs/{run_id}/status`
- Review outputs: `GET /runs/{run_id}/quality`, `GET /runs/{run_id}/export`

## Note

This repository is intentionally designed to be judged in a local environment first, then optionally exposed with a frontend later.
