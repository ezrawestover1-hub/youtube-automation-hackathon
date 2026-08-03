# DropFix Showcase — User Ready

This is the fastest path to produce the recorded demo video.

## One command (recommended)

- `.\highlights\run-highlight-showcase.ps1 -Install -OpenOutput`

This does:

- opens the HTML deck,
- installs highlight dependencies if needed,
- records the deck automatically,
- writes `outputs\dropfix-highlight-showcase.mp4`,
- opens the result when complete.

## Common options

- Shorter version: `.\highlights\run-highlight-showcase.ps1 -Install -OpenOutput -Seconds 45`
- Manual deck view only: `.\highlights\run-highlight-showcase.ps1 -AutoRecord:$false`
- Custom clip quality: adjust `-Width`, `-Height`, `-Fps`.

## If recording fails

- Make sure Chrome or Brave is installed.
- Run with `-Install` once.
- Re-run with the same command and check that `outputs\` contains the new mp4.

## What judges should see

- deterministic scenes,
- local-first workflow,
- clear recommendation + evidence framing,
- quality score output and export framing.
