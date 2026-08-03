const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawnSync } = require('child_process');
const puppeteer = require('puppeteer-core');

const fps = Number.parseInt(process.env.HIGHLIGHT_FPS || '30', 10);
const durationSeconds = Number.parseInt(process.env.HIGHLIGHT_SECONDS || '90', 10);
const width = Number.parseInt(process.env.HIGHLIGHT_WIDTH || '1920', 10);
const height = Number.parseInt(process.env.HIGHLIGHT_HEIGHT || '1080', 10);

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

(async () => {
  const repoRoot = path.resolve(__dirname, '..');
  const htmlPath = path.join(repoRoot, 'highlights', 'dropfix-highlight-showcase.html');
  const url = new URL(`file://${path.resolve(htmlPath).replace(/\\/g, '/')}`);
  const outputPath = path.join(repoRoot, 'outputs', 'dropfix-highlight-showcase.mp4');
  const frameDir = path.join(os.tmpdir(), `dropfix-highlight-${Date.now()}`);

  if (!fs.existsSync(path.dirname(outputPath))) {
    fs.mkdirSync(path.dirname(outputPath), { recursive: true });
  }

  fs.mkdirSync(frameDir, { recursive: true });

  const chromePath = [
    'C:/Program Files/Google/Chrome/Application/chrome.exe',
    'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  ].find((p) => fs.existsSync(p));

  if (!chromePath) {
    throw new Error('Chrome not found. Install Chrome or update the script executablePath.');
  }

  const browser = await puppeteer.launch({
    headless: true,
    executablePath: chromePath,
    args: ['--disable-gpu', '--no-sandbox'],
    defaultViewport: { width, height },
  });

  const page = await browser.newPage();
  await page.setViewport({ width, height });
  await page.goto(url.toString(), { waitUntil: 'networkidle0' });

  const totalFrames = Math.max(1, fps * durationSeconds);
  const frameIntervalMs = 1000 / fps;
  for (let i = 0; i < totalFrames; i++) {
    await sleep(frameIntervalMs);
    const framePath = path.join(frameDir, `frame_${String(i).padStart(6, '0')}.png`);
    await page.screenshot({ path: framePath, type: 'png' });

    if ((i + 1) % 50 === 0) {
      console.log(`captured ${i + 1}/${totalFrames} frames`);
    }
  }

  await page.close();
  await browser.close();

  const ffmpegPath = require('ffmpeg-static');
  if (!ffmpegPath || !fs.existsSync(ffmpegPath)) {
    throw new Error('ffmpeg-static binary not found.');
  }

  const pattern = path.join(frameDir, 'frame_%06d.png');
  const ffmpegArgs = [
    '-y',
    '-framerate', String(fps),
    '-i', pattern,
    '-vcodec', 'libx264',
    '-pix_fmt', 'yuv420p',
    '-r', String(fps),
    '-movflags', '+faststart',
    '-crf', '24',
    '-preset', 'veryfast',
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
})();
