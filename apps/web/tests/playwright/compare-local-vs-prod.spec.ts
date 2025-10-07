import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import pixelmatch from 'pixelmatch';
import { PNG } from 'pngjs';

const OUT_DIR = path.resolve(__dirname, '../../test-artifacts');
const LOCAL_URL = process.env.BASE_URL || 'http://localhost:5173';
const PROD_URL = 'https://www.concordbroker.com';

function ensureDir(p: string) {
  if (!fs.existsSync(p)) fs.mkdirSync(p, { recursive: true });
}

async function takeShot(page, url: string, file: string) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.setViewportSize({ width: 1366, height: 900 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: file, fullPage: true });
}

test('visual parity: local /properties vs production', async ({ page, browser }) => {
  ensureDir(OUT_DIR);
  const localPng = path.join(OUT_DIR, 'local-properties.png');
  const prodPng = path.join(OUT_DIR, 'prod-properties.png');
  const diffPng = path.join(OUT_DIR, 'diff-properties.png');

  // Local
  await takeShot(page, `${LOCAL_URL}/properties`, localPng);

  // Production (separate context to avoid shared state)
  const ctx = await browser.newContext();
  const prodPage = await ctx.newPage();
  await takeShot(prodPage, `${PROD_URL}/properties`, prodPng);
  await ctx.close();

  // Compare
  const img1 = PNG.sync.read(fs.readFileSync(localPng));
  const img2 = PNG.sync.read(fs.readFileSync(prodPng));
  const width = Math.min(img1.width, img2.width);
  const height = Math.min(img1.height, img2.height);
  const crop = (img: PNG) => new PNG({ width, height, data: img.data });
  const diff = new PNG({ width, height });
  const pixels = pixelmatch(
    img1.data,
    img2.data,
    diff.data,
    width,
    height,
    { threshold: 0.1 }
  );
  fs.writeFileSync(diffPng, PNG.sync.write(diff));

  // Allow minimal variance
  expect(pixels).toBeLessThan(500);
});
