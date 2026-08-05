# DropFix

**Find where viewers leave, why they leave, and what to edit.**

DropFix is a browser-native YouTube creator workflow for the YouTube Automation Hackathon. It turns a transcript plus YouTube Studio retention data into a ranked, timestamped editing handoff.

> Retention signal -> exact moment -> edit decision.

## Live project

- [Open DropFix](https://ezrawestover1-hub.github.io/youtube-automation-hackathon/)
- [Devpost submission kit](DEVPOST_SUBMISSION.md)

## The problem

Creators can already see a retention graph in YouTube Studio, but a graph does not tell an editor what to change. Analytics and editing decisions live in separate tools, leaving creators to guess whether a drop came from a slow setup, weak payoff, confusing section, or something else.

## What DropFix does

1. Import a transcript and paste it directly, upload subtitles, or use a transcript CSV.
2. Optionally import a YouTube Studio CSV containing retention points and performance metrics.
3. Detect timestamped retention changes and align them with the matching transcript passage.
4. Produce evidence-first recommendations: observed signal, comparison, interpretation, exact edit, confidence, and validation path.
5. Accept, rewrite, or dismiss each recommendation.
6. Export an editor brief, summary, JSON, or judge evidence packet.

The included labeled demo is synthetic and clearly marked. It demonstrates the workflow without presenting demo numbers as a creator's real channel performance.

## Why it is different

Most analytics surfaces explain *what* happened. DropFix bridges the operational gap between analytics and editing:

| Analytics alone | DropFix |
| --- | --- |
| Retention fell around a point | Retention fell from one measured point to the next, linked to the corresponding transcript moment |
| "Improve the hook" | A timestamped instruction to cut, move, rewrite, preserve, or test a specific moment |
| A graph to interpret | An editor decision queue and handoff brief |

## Evidence and scoring

Recommendations use a fixed 40-point internal quality check. It evaluates evidence quality, specificity, actionability, goal alignment, confidence calibration, expected usefulness, novelty, and validation quality. The number is a recommendation-quality check, not a prediction of video performance or hackathon placement.

DropFix intentionally distinguishes observation from inference. When there is not enough evidence, it discloses the limitation instead of claiming a channel-level conclusion.

## Quick demo path

1. Open the [live project](https://ezrawestover1-hub.github.io/youtube-automation-hackathon/#workspace).
2. Select **Load labelled demo data** or choose **YouTube Studio CSV (real analytics)** and upload an export alongside its transcript.
3. Click **Run analysis ->**.
4. Review a primary finding and choose **Accept edit**, **Mark for rewrite**, or **Dismiss**.
5. Open **Export** and download the editor brief or judge packet.

## Technical approach

- A static, client-side application built around a deterministic workflow state.
- Local parsing for transcript formats and Studio-style CSV exports.
- Deterministic retention-event detection plus transcript-to-timestamp alignment.
- Structured recommendation schema with source labels, confidence language, and validation guidance.
- Local workspace persistence for projects and editor decisions.
- No account, server, scraping, or YouTube credential is required to test the core workflow.

## Run locally

Open `index.html` in a modern browser, or serve the repository with any static HTTP server. The deployed GitHub Pages version is the recommended judge path.

## Repository layout

- `index.html` - DropFix interface, analysis logic, import handling, and exports.
- `index.js` - minimal local static server.
- `DEVPOST_SUBMISSION.md` - paste-ready submission copy and demo plan.

## Data boundary

DropFix can ingest creator-provided YouTube Studio CSV exports. It does **not** connect directly to a YouTube account, scrape YouTube, or claim API integration. That makes the live demo account-free while keeping the creator-data path honest and reproducible.
