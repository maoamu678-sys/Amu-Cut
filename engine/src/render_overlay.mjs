#!/usr/bin/env node
/**
 * Capture the transparent Three.js overlay at a fixed frame rate.
 * This is intentionally separate from FFmpeg so the generated PNG frames
 * remain inspectable and the project stays editable.
 */

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";
import { fileURLToPath } from "node:url";
import { pathToFileURL } from "node:url";
import { chromium } from "playwright";

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(process.argv[2] ?? "..");
const outputDir = path.resolve(process.argv[3] ?? path.join(projectDir, "output", "overlay"));
const timelinePath = path.join(projectDir, "timeline.json");
const timeline = JSON.parse(await fs.readFile(timelinePath, "utf8"));
const rendererPath = path.resolve(scriptDir, "../render/index.html");
const scenePath = path.join(projectDir, "scene.mjs");
const sceneModule = await import(pathToFileURL(scenePath).href);
const visualConfig = sceneModule.getVisualConfig?.() ?? {};

const browserExecutable = process.env.AMU_BROWSER_EXECUTABLE
  ?? "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

await fs.mkdir(outputDir, { recursive: true });
const browser = await chromium.launch({
  headless: true,
  executablePath: browserExecutable,
});
const page = await browser.newPage({
  viewport: { width: timeline.format.width, height: timeline.format.height },
  deviceScaleFactor: 1,
  colorScheme: "dark",
});
await page.goto(`file://${rendererPath}`);
await page.evaluate((value) => window.__AMU_PROJECT__ = value, timeline);
await page.evaluate((value) => window.__AMU_STYLE_CONFIG__ = value, visualConfig);
await page.evaluate(() => window.__AMU_READY__?.());

const duration = Math.max(...timeline.scenes.map((scene) => scene.start + scene.duration), 0);
const frameCount = Math.ceil(duration * timeline.format.fps);
for (let frame = 0; frame < frameCount; frame += 1) {
  await page.evaluate((time) => window.__AMU_RENDER_AT__?.(time), frame / timeline.format.fps);
  const filename = path.join(outputDir, `overlay-${String(frame + 1).padStart(6, "0")}.png`);
  await page.locator("#stage").screenshot({ path: filename, omitBackground: true });
}

await browser.close();
console.log(`已生成透明叠加帧：${outputDir}`);
