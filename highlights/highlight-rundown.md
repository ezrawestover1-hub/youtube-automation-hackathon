# DropFix Highlight Reel — User-Ready Demo Script

Use this with `highlights/run-highlight-showcase.ps1` in auto-record mode.

## Scene order

1. **Intro (0:00—0:08)**
   - "DropFix automates creator review from retention data + transcript evidence to ranked recommendations."
2. **Setup & intake (0:08—0:16)**
   - Mention local-first workflow and single-command local run.
3. **Detection (0:16—0:30)**
   - Show retention event extraction and explain these are reproducible signals.
4. **Evidence (0:30—0:42)**
   - Show evidence endpoint and transcript overlap.
5. **Recommendations (0:42—0:54)**
   - Show top finding and why it is directly editable.
6. **Quality score (0:54—1:06)**
   - Show quality score and gate status as trust signal.
7. **Export (1:06—1:30)**
   - Show markdown export and handoff-ready results.

## On-screen lines (what to speak)

- "Every suggestion is tied to evidence, not vibes."
- "Profile-based tuning gives creators control."
- "Quality score and gate status help teams trust what to ship."
- "Everything is local-first, so judges can verify it from clone → run → export."

## Zero-effort auto-render mode

- From repo root run:
  - `.\highlights\run-highlight-showcase.ps1 -Install -OpenOutput`
- Output file:
  - `outputs\\dropfix-highlight-showcase.mp4`

Run this once and send the generated MP4 directly.

## Recorded demo command (optional live callouts)

- `cd backend`
- `python -m venv .venv`
- `. ./.venv/Scripts/Activate.ps1`
- `pip install -r requirements.txt`
- `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

You can keep it visual by just showing the local-open HTML deck while referencing the checklist.
