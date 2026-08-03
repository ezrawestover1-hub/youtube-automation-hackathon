const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');
const puppeteer = require('puppeteer-core');
const { pathToFileURL } = require('url');

function parseIntEnv(name, fallback, min, max) {
  const raw = Number.parseInt(process.env[name], 10);
  if (Number.isNaN(raw) || raw < min || raw > max) {
    return fallback;
  }
  return raw;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getChromePath() {
  const candidates = [
    process.env.HIGHLIGHT_CHROME_PATH,
    process.env.PUPPETEER_EXECUTABLE_PATH,
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
    'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe',
  ].filter(Boolean);

  return candidates.find((p) => fs.existsSync(p));
}

(async () => {
  const repoRoot = path.resolve(__dirname, '..');
  const htmlPath = path.join(repoRoot, 'highlights', 'dropfix-highlight-showcase.html');
  const outputPath = path.resolve(
    process.env.HIGHLIGHT_OUTPUT || path.join(repoRoot, 'outputs', 'dropfix-highlight-showcase.mp4')
  );
  const frameDir = path.join(os.tmpdir(), `dropfix-highlight-${Date.now()}`);

  const fps = parseIntEnv('HIGHLIGHT_FPS', 30, 1, 60);
  const durationSeconds = parseIntEnv('HIGHLIGHT_SECONDS', 90, 5, 360);
  const width = parseIntEnv('HIGHLIGHT_WIDTH', 1366, 320, 7680);
  const height = parseIntEnv('HIGHLIGHT_HEIGHT', 768, 180, 4320);

  if (!fs.existsSync(htmlPath)) {
    throw new Error(`Cannot find showcase HTML at ${htmlPath}`);
  }

  if (!fs.existsSync(path.dirname(outputPath))) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  }

  fs.mkdirSync(frameDir, { recursive: true });

  const chromePath = getChromePath();
  if (!chromePath) {
    throw new Error('Chrome not found. Install Chrome/Brave or set HIGHLIGHT_CHROME_PATH.');
  }

  let browser;
  try {
    const url = pathToFileURL(htmlPath).toString();

    browser = await puppeteer.launch({
      headless: true,
      executablePath: chromePath,
      args: ['--disable-gpu', '--no-sandbox'],
      defaultViewport: { width, height },
    });

    const page = await browser.newPage();
    await page.setViewport({ width, height });
    await page.goto(url, { waitUntil: 'networkidle0' });

    const totalFrames = Math.max(1, fps * durationSeconds);
    const frameIntervalMs = 1000 / fps;
    for (let i = 0; i < totalFrames; i++) {
      await sleep(frameIntervalMs);
      const framePath = path.join(frameDir, `frame_${String(i).padStart(6, '0')}.png`);
      await page.screenshot({ path: framePath, type: 'png' });

      if ((i + 1) % 60 === 0) {
        console.log(`captured ${i + 1}/${totalFrames} frames`);
      }
    }

    await page.close();
  } finally {
    if (browser) {
      await browser.close();
    }
  }

  const ffmpegPath = require('ffmpeg-static');
  if (!ffmpegPath || !fs.existsSync(ffmpegPath)) {
    throw new Error('ffmpeg-static binary not found.');
  }

  const pattern = path.join(frameDir, 'frame_%06d.png');
  const ffmpegArgs = [
    '-y',
    '-framerate', String(fps),
    '-i', pattern,
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-r', String(fps),
    '-movflags', '+faststart',
    '-crf', '22',
    '-preset', 'fast',
    outputPath,
  ];

  const ffmpegResult = spawnSync(ffmpegPath, ffmpegArgs, {
    cwd: frameDir,
    encoding: 'utf8',
  });

  if (ffmpegResult.status !== 0) {
    throw new Error(`ffmpeg failed: ${ffmpegResult.stderr || ffmpegResult.stdout}`);
  }

  fs.rmSync(frameDir, { recursive: true, force: true });
  console.log(`Highlight rendered: ${outputPath}`);
  console.log(`Frames used: ${Math.max(1, fps * durationSeconds)} at ${fps} fps for ${durationSeconds}s`);
})();
