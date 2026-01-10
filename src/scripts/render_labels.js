const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');

const ROOT = path.join(__dirname, '..', '..');
const OUTPUT = path.join(ROOT, 'output');

const pages = [
  {
    name: 'label',
    html: path.join(ROOT, 'src', 'pages', 'hold_OSD_quarantine_card.html'),
    viewport: { width: 812, height: 1218 }, // 4x6 @ 203dpi
  },
  {
    name: 'location_label',
    html: path.join(ROOT, 'src', 'pages', 'location_label.html'),
    viewport: { width: 812, height: 609 }, // 4x3 @ 203dpi
  },
];

async function renderPage(browser, pageDef) {
  const page = await browser.newPage({ viewport: { ...pageDef.viewport, deviceScaleFactor: 1 } });
  await page.emulateMedia({ media: 'print' });
  const url = `file://${pageDef.html.replace(/\\/g, '/')}`;
  await page.goto(url);
  const outPath = path.join(OUTPUT, `${pageDef.name}.png`);
  await page.screenshot({ path: outPath, fullPage: true });
  await page.close();
  console.log(`Rendered ${pageDef.name} -> ${outPath}`);
}

(async () => {
  if (!fs.existsSync(OUTPUT)) fs.mkdirSync(OUTPUT, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  try {
    for (const p of pages) {
      await renderPage(browser, p);
    }
  } finally {
    await browser.close();
  }
})();
