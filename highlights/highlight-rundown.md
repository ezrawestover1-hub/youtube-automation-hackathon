# DropFix Highlight Reel — 90 Second Show-off Script

Use this with `highlights/run-highlight-showcase.ps1` and record your screen (OBS, Clipchamp, or native recorder).

## Scene order

1. **Intro (0:00–0:10)**
   - "DropFix automates creator review from retention data + transcript evidence to ranked recommendations."
2. **Setup & intake (0:10–0:20)**
   - Mention local-first workflow and single-command local run.
3. **Detection (0:20–0:33)**
   - Show retention event extraction and explain these are reproducible signals.
4. **Evidence (0:33–0:45)**
   - Show evidence endpoint and transcript overlap.
5. **Recommendations (0:45–1:00)**
   - Show top finding and why it is directly editable.
6. **Quality score (1:00–1:14)**
   - Show quality score and gate status as trust signal.
7. **Export (1:14–1:30)**
   - Show markdown export and handoff-ready results.

## On-screen lines (what to speak)

- "Every suggestion is tied to evidence, not vibes."
- "Profile-based tuning gives creators control."
- "Quality score and gate status help teams trust what to ship."
- "Everything is local-first, so judges can verify it from clone → run → export."

## Zero-effort auto-render mode

- From repo root run:
  - `npm.cmd install --prefix highlights puppeteer-core ffmpeg-static`
  - `.\highlights\run-highlight-showcase.ps1`
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
