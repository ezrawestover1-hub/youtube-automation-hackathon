# DropFix

## Quick Overview

DropFix is a **browser-only YouTube creator workflow app** built for the Devpost YouTube Automation Hackathon.

It helps creators and editors automate three pain points:

- Clip selection from transcript structure and timestamps
- Metadata generation for titles, descriptions, tags, and hashtags
- Workflow clarity with transparent scoring and actionable recommendations

## Live demo

- Public site: https://ezrawestover1-hub.github.io/youtube-automation-hackathon/
- Primary repo: https://github.com/ezrawestover1-hub/youtube-automation-hackathon

## Why judges care

### Functionality

- Full upload flow for transcript files and pasted transcript text
- Transcript parser, segment scoring, clip ranking, and metadata pack generation
- Persistent local workspace (no account needed)
- Export/copy actions for metadata JSON and summary text

### Creativity

- Evidence-first workflow: each recommendation is tied to parsed evidence (segment timecode, score, rationale)
- Profile presets + adjustable weighting for creator style control
- “Quality narrative” panel explains why clips were recommended

### Technical execution

- Single-page implementation with predictable state model (projects, tabs, workflow progression)
- Clear edge-case handling for empty/invalid transcripts and oversized files
- Deterministic transforms in a standalone client environment
- Minimal architecture with one primary surface (`index.html`) for faster judge review

### Real-world usefulness

- Useful for real creators in pre-edit planning: faster candidate clip discovery and description/title ideation
- Fast enough for hourly use while still remaining reviewable and understandable
- No external API account or service dependency required to test core features

## How to run (fastest path)

### Option A — one-command local launch (recommended)

```powershell
npm start
```

Then open:

```
http://localhost:3000
```

### Option B — direct file open (no install)

Open `index.html` directly in any modern browser.

### Option C — GitHub Pages

Open the public site link above.

## What to test in 60 seconds

1. Click **+ New project** and load sample data with **Load sample transcript**.
2. Click **Run analysis**.
3. Review:
   - Top clips list
   - Reason bullets and score bars
   - Metadata pack (title, description variants, tags, hashtags)
4. Export JSON or summary using the panel buttons.

## Repository layout

- `index.html` — app UI and all in-browser logic
- `index.js` — tiny static server for local serving
- `highlights/` — optional demo/video helpers (nonessential for core app logic)
- `backend/` — legacy workspace from earlier iterations (kept for continuity, not required for judging)
- `outputs/` — gitignored generated local outputs
- `work/` — working scratch space (not part of submission)
- `local-dev.md` — local run notes

## Deployment

- Static GitHub Pages workflow is enabled from `.github/workflows/gh-pages.yml`.
- Deployment source is the repository `main` branch; site content is built from `index.html`.

## Submission notes for Devpost

- Include the GitHub repo and demo link in your submission form.
- Mention that the app is browser-native and works without a dedicated backend.
- In judging video, show:
  - upload path,
  - analysis output,
  - one clip edit decision, and
  - generated metadata usage.


