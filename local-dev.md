# Local development and judge verification checklist

## Goal

Prove local execution in under 5 minutes from a clean environment.

## Prerequisites

- Node.js 18+ (or current LTS)
- Git

## Steps

1. Clone repository

```powershell
git clone https://github.com/ezrawestover1-hub/youtube-automation-hackathon.git
cd youtube-automation-hackathon
```

2. Install dependencies

```powershell
npm install
```

3. Start local server

```powershell
npm start
```

4. Open local app

```powershell
http://localhost:3000
```

5. Verify judge flow

From the workspace:
- Load sample transcript
- Run analysis
- Review clips + metadata + quality summary
- Export summary JSON / text
- Repeat with at least one profile preset

## Validation checklist (judges)

- App starts on `http://localhost:3000` without errors.
- File upload + pasted transcript both parse successfully.
- Workflow tabs unlock in order as expected.
- Output cards include clip scores, reasons, and timestamp ranges.
- Metadata generation returns titles, descriptions, tags, hashtags, and rationale.
- Edge cases fail safely with user-visible status messages.

## Output expectations

- If you run sample inputs, exports should include quality score, rationale, and project summary.
