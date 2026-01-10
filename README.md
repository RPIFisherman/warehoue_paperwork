# Photo Server Labels & Cards

This repo contains print-ready HTML/CSS labels and cards for warehouse operations, plus utilities to render PNGs and convert them to ZPL for Zebra printers.

## Structure
- `src/pages/` — HTML pages to print
  - `hold_OSD_quarantine_card.html` — 4×6 master hold/OSD/quarantine tag
  - `location_label.html` — 4×3 e‑commerce picking location label
  - `master_logistics_tally_and_3PL_revenue_audit_card.html` — audit/tally card
- `src/styles/` — Shared and page‑specific styles
  - `print_form.css` — shared base print styles
  - `hold_osd_quarantine.css` — OSD tag overrides
  - `location_label.css` — location label styles
- `src/scripts/` — Utilities and helpers
  - `print_png_to_zpl.py` — convert PNG to ZPL and send to Zebra
  - `render_labels.js` — render both labels to PNG (output/)
  - `server.js` — lightweight server with tabbed viewer + print API
  - `serve_demo.py` — simple server/demo
  - `pallet_diagram.py` — diagram helper
- `assets/images/` — images used in pages (item images, QR, diagrams, barcodes)
- `output/` — generated PNG/ZPL/PDF artifacts
- `docs/` — documentation (Markdown, notes)
- `archive/` — backups or legacy files
- `data/` — sample data inputs (e.g., XLSX)

## Prerequisites
- Node.js (for Playwright screenshot rendering)
- Python 3.9+ and `zebrafy` (for PNG→ZPL)
- Python `qrcode` library (for QR code generation)

Install Playwright (if not installed):
```powershell
npm install
npm install playwright
npx playwright install chromium
```

Install Python deps:
```powershell
pip install zebrafy qrcode[pil]
```

## Generate QR Code with Local IP
Run the QR code generator to create a QR code pointing to your local server:

```powershell
python src/scripts/qr_code_generator.py
```

This will:
- Automatically detect your local IP address
- Generate a QR code pointing to `http://[YOUR_IP]:3000`
- Save it to `assets/images/qr.png`

Run this whenever your IP changes or when setting up the project.

## Render HTML to PNG
Use Playwright to render pages to PNG at label resolution.

4×6 OSD card (203 dpi → 812×1218):
```powershell
node -e "const { chromium } = require('playwright'); (async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 812, height: 1218, deviceScaleFactor: 1 } });
  await page.emulateMedia({ media: 'print' });
  await page.goto('file:///C:/Users/Yuyang-RPI/Documents/GitHub/photo-server/src/pages/hold_OSD_quarantine_card.html');
  await page.screenshot({ path: 'output/label.png', fullPage: true });
  await browser.close();
})()"
```

4×3 location label (203 dpi → 812×609):
```powershell
node -e "const { chromium } = require('playwright'); (async() => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 812, height: 609, deviceScaleFactor: 1 } });
  await page.emulateMedia({ media: 'print' });
  await page.goto('file:///C:/Users/Yuyang-RPI/Documents/GitHub/photo-server/src/pages/location_label.html');
  await page.screenshot({ path: 'output/location_label.png', fullPage: true });
  await browser.close();
})()"
```

## Convert PNG to ZPL and Print
Run the Python script to convert the PNG and send ZPL to a Zebra printer.

```powershell
python src/scripts/print_png_to_zpl.py
```

Script settings:
Script options:
- `--png` path (optional) or `--image-type` to pick `<output>/<image-type>.png`
- `--printer-ip` (default env `PRINTER_IP` or `10.10.200.138`)
- `--no-print` to only write ZPL

## Render both labels (PNG)
```powershell
node src/scripts/render_labels.js
```
Outputs to `output/label.png` and `output/location_label.png`.

## Run the server (tabs + print API)
```powershell
node src/scripts/server.js
```
Then open http://localhost:3000. Tabs show the three pages. Each page has a print icon that calls `/api/print?type=<label|location_label|audit>`.

**Print Behavior:**
- **Label types** (label, location_label): Renders the page to PNG, converts to ZPL, and sends to Zebra printer (via `print_png_to_zpl.py`)
- **Audit card** (audit): Opens the browser's print dialog for printing to a regular letter-size printer

The server uses Playwright for rendering labels and calls `print_png_to_zpl.py` for ZPL conversion.

## Notes
- All pages use print-target sizes via `@page` in CSS for accurate layout.
- When generating barcodes for ZPL, prefer rendering the barcode in HTML/PNG or embed with ZPL directly for crisp results.
- Images referenced in pages live under `assets/images/`.
- Keep output artifacts in `output/` to avoid cluttering the root.
 - Set `PRINTER_IP` env var to override the default printer.
