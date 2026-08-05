# DropFix Devpost Submission Kit

## Project name

DropFix

## Tagline

Find where viewers leave, why they leave, and what to edit.

## One-sentence pitch

DropFix turns a YouTube retention signal and a transcript into a timestamped, confidence-calibrated edit decision an editor can act on immediately.

## Short description

YouTube Studio shows creators where viewers leave. DropFix explains the evidence, connects it to the exact transcript moment, and turns it into a prioritized editor brief.

## Full project description

Creators can already see retention graphs, CTR, and watch time in YouTube Studio. The hard part is deciding what to change in the video. A sharp retention drop might signal a slow setup, a missing payoff, a confusing transition, or something unrelated. Existing analytics surfaces leave the creator to translate that graph into an editing plan.

I built DropFix to close that gap. A creator imports a transcript and, when available, a YouTube Studio CSV export. DropFix detects meaningful retention changes, aligns each signal with the corresponding transcript moment, and produces an evidence-first recommendation. Each finding separates what was observed from the likely interpretation, gives an exact timestamped action, states confidence honestly, and includes a validation path for the next comparable upload or edit test.

Instead of generic advice like "improve the hook," DropFix gives editors a structured decision: what happened, where it happened, what to cut, move, rewrite, preserve, or test, and why that recommendation is trustworthy enough to use. Editors can accept, mark for rewrite, or dismiss a finding, then export the decisions as an editor brief.

The live demo includes clearly labeled synthetic data so anyone can test the workflow without an account. The same workflow accepts creator-provided YouTube Studio CSV exports for creator-specific retention evidence. DropFix does not scrape YouTube or claim direct account integration.

## Judging criteria mapping

### Functionality

- Imports transcript text, subtitle files, transcript CSV, and Studio-style analytics CSV.
- Parses retention points and relevant performance metrics locally in the browser.
- Detects retention events, aligns them with transcript time, and generates timestamped recommendations.
- Saves accept/rewrite/dismiss editor decisions locally.
- Exports editor briefs, summaries, JSON, and a judge evidence packet.

### Creativity

DropFix's central idea is the chain from **metric -> moment -> explanation -> edit**. Instead of building another dashboard or generic AI title generator, it converts viewer behavior into a decision an editor can use.

### Technical execution

- Uses deterministic detection for retention events rather than treating every recommendation as an AI guess.
- Keeps a structured recommendation schema: observed, compared, interpretation, recommended action, expected impact, confidence, confidence rationale, and validation.
- Scores recommendation quality on a visible 40-point internal assessment. Scores are calibrated from available evidence; they are not a performance prediction.
- Discloses baseline limitations and labels the synthetic demo data.

### Real-world usefulness

- Saves the manual work of comparing a retention graph with a transcript and turning the result into an editor brief.
- Gives exact timestamps and instructions rather than a wall of analytics.
- Preserves positive moments and provides validation guidance, so a creator can learn what to repeat as well as what to fix.

## Tech stack

- HTML, CSS, and vanilla JavaScript
- GitHub Pages for deployment
- Browser local storage for guest project persistence
- Client-side CSV and transcript parsing

## Demo script: 60 to 75 seconds

1. **Problem, 0-10 seconds**: "YouTube Studio can show a retention drop, but it rarely tells an editor what to change."
2. **Input, 10-22 seconds**: Open the workspace, show the labeled demo or a Studio CSV plus matching transcript, then click **Run analysis ->**.
3. **Evidence, 22-42 seconds**: Open a primary finding. Point out the measured retention change, linked transcript text, confidence, and exact edit instruction.
4. **Decision, 42-55 seconds**: Click **Accept edit** or **Mark for rewrite**. Explain that this becomes part of the editor handoff.
5. **Output, 55-70 seconds**: Open Export and download the editor brief. Close with: "Less time decoding analytics, more time making better videos."

## Suggested Devpost links

- Live project: https://ezrawestover1-hub.github.io/youtube-automation-hackathon/
- Repository: https://github.com/ezrawestover1-hub/youtube-automation-hackathon
- Demo video: upload the completed DropFix demo video directly to Devpost or YouTube, then add its public link here.

## Submission checklist

- Add the live project link.
- Add the repository link.
- Upload the demo video.
- Use the one-sentence pitch and full project description above.
- Include the CSV import limitation honestly: creator-provided exports are supported; direct account linking is not.
- Submit the project before the event deadline.
