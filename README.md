# Warehouse Paperwork System

A comprehensive warehouse documentation system for generating print-ready labels and audit cards. This system supports both Zebra thermal printers (ZPL) for labels and standard printers for forms.

## Overview

This project provides:

- **HTML/CSS-based templates** for warehouse labels and audit forms
- **Zebra ZPL printer support** for thermal label printing (4×6, 4×3)
- **Standard printer support** for letter-size audit cards
- **Web-based preview and printing** via integrated server
- **Automated rendering** from HTML to PNG/ZPL

## Project Structure

```
warehoue_paperwork/
├── src/
│   ├── pages/              # HTML templates for printing
│   │   ├── hold_OSD_quarantine_card.html          # 4×6 Hold/OSD/Quarantine tag
│   │   ├── location_label.html                     # 4×3 Location label
│   │   └── master_logistics_tally_and_3PL_revenue_audit_card.html  # Audit card
│   ├── styles/             # CSS stylesheets
│   │   ├── print_form.css                          # Shared base styles
│   │   ├── hold_osd_quarantine.css                # Hold/OSD tag specific styles
│   │   └── location_label.css                     # Location label specific styles
│   └── scripts/            # Automation and utilities
│       ├── server.js                               # Web server with print API
│       ├── render_labels.js                       # Batch PNG renderer
│       ├── print_png_to_zpl.py                    # PNG to ZPL converter
│       ├── qr_code_generator.py                   # QR code generator
│       ├── serve_demo.py                          # PDF demo server
│       └── pallet_diagram.py                      # Pallet diagram generator
├── assets/
│   └── images/             # Images, QR codes, diagrams, product photos
├── output/                 # Generated files (PNG, ZPL, PDF)
├── docs/                   # Documentation and design notes
├── data/                   # Sample data and templates (XLSX)
├── archive/                # Backup files
└── README.md
```

## Prerequisites

### Required Software

- **Node.js** (v16+) - For Playwright screenshot rendering
- **Python** (3.9+) - For ZPL conversion and utilities
- **Zebra Thermal Printer** - For label printing (optional)

### Installation

1. **Install Node.js dependencies:**

```powershell
npm install
```

This installs Playwright automatically. If Chromium browser is not installed:

```powershell
npx playwright install chromium
```

2. **Install Python dependencies:**

```powershell
pip install zebrafy qrcode[pil] pillow PyPDF2 reportlab
```

### Environment Configuration

Set your Zebra printer IP (optional, defaults to `10.10.200.138`):

```powershell
# PowerShell
$env:PRINTER_IP = "10.10.200.138"

# Or create .env file
echo "PRINTER_IP=10.10.200.138" > .env
```

## Quick Start

### Option 1: Web-Based Workflow (Recommended)

1. **Generate QR code** with your local IP:

```powershell
python src/scripts/qr_code_generator.py
```

2. **Start the web server:**

```powershell
node src/scripts/server.js
```

3. **Access from any device** on your network:
   - Navigate to `http://YOUR_IP:3000` (shown in console output)
   - Preview all labels and forms in tabs
   - Click **🖨 Print** button for instant printing

**How it works:**

- Labels (4×6, 4×3): Automatically converted to ZPL and sent to Zebra printer
- Audit Card: Opens browser print dialog for standard printer

### Option 2: Command-Line Workflow

#### Batch Render All Labels

```powershell
node src/scripts/render_labels.js
```

Outputs PNG files to `output/` directory:

- `label.png` - 4×6 Hold/OSD/Quarantine card (812×1218px @ 203dpi)
- `location_label.png` - 4×3 Location label (812×609px @ 203dpi)

#### Individual Label Rendering

4×6 OSD card:

```powershell
node -e "const { chromium } = require('playwright'); (async() => { const browser = await chromium.launch({ headless: true }); const page = await browser.newPage({ viewport: { width: 812, height: 1218, deviceScaleFactor: 1 } }); await page.emulateMedia({ media: 'print' }); await page.goto('file:///' + process.cwd().replace(/\\/g, '/') + '/src/pages/hold_OSD_quarantine_card.html'); await page.screenshot({ path: 'output/label.png', fullPage: true }); await browser.close(); })()"
```

4×3 location label:

```powershell
node -e "const { chromium } = require('playwright'); (async() => { const browser = await chromium.launch({ headless: true }); const page = await browser.newPage({ viewport: { width: 812, height: 609, deviceScaleFactor: 1 } }); await page.emulateMedia({ media: 'print' }); await page.goto('file:///' + process.cwd().replace(/\\/g, '/') + '/src/pages/location_label.html'); await page.screenshot({ path: 'output/location_label.png', fullPage: true }); await browser.close(); })()"
```

#### Convert PNG to ZPL and Print

Send to Zebra printer:

```powershell
python src/scripts/print_png_to_zpl.py --image-type label
python src/scripts/print_png_to_zpl.py --image-type location_label
```

Generate ZPL only (no printing):

```powershell
python src/scripts/print_png_to_zpl.py --image-type label --no-print
```

**Script options:**

- `--png` - Custom PNG path (optional)
- `--image-type` - Label type: `label` or `location_label` (default: `location_label`)
- `--output-dir` - Output directory (default: `output/`)
- `--printer-ip` - Zebra printer IP (default: env `PRINTER_IP` or `10.10.200.138`)
- `--no-print` - Generate ZPL without printing

## Label Specifications

### Hold/OSD/Quarantine Card (4×6)

- **Dimensions:** 4" × 6" (812×1218px @ 203dpi)
- **Printer:** Zebra thermal printer
- **Format:** ZPL
- **Use Case:** Warehouse hold tags, damaged goods, quarantine items

### Location Label (4×3)

- **Dimensions:** 4" × 3" (812×609px @ 203dpi)
- **Printer:** Zebra thermal printer
- **Format:** ZPL
- **Use Case:** Bin locations, picking zones, rack labels

### Master Logistics Tally & 3PL Revenue Audit Card

- **Dimensions:** Letter landscape (11" × 8.5")
- **Printer:** Standard office printer
- **Format:** Browser print / PDF
- **Features:**
  - Inbound/Outbound tracking
  - Accessorial fees
  - Compliance checklist
  - ILP grid (4 columns)
  - Signature areas
  - Compact legend and SOP
- **Use Case:** Daily tally sheets, 3PL billing audit, shipment verification

## Utilities

### QR Code Generator

Generates a QR code with your local server URL for easy access from mobile devices:

```powershell
python src/scripts/qr_code_generator.py
```

**Features:**

- Auto-detects local IP address
- Creates QR code pointing to `http://[YOUR_IP]:3000`
- Saves to `assets/images/qr.png`
- Run whenever your IP changes

### Pallet Diagram Generator

Create visual pallet diagrams for TiHi configurations:

```powershell
python src/scripts/pallet_diagram.py
```

### PDF Demo Server

Simple HTTP server to share PDF files with embedded QR codes:

```powershell
python src/scripts/serve_demo.py --port 8000
```

## Development

### File Structure Guidelines

- **HTML Templates:** Keep in `src/pages/`
- **Stylesheets:** Shared styles in `print_form.css`, page-specific in separate files
- **Scripts:** Automation and utilities in `src/scripts/`
- **Assets:** Images, diagrams, QR codes in `assets/images/`
- **Output:** Generated files in `output/` (gitignored except samples)

### Customization

#### Updating Label Content

1. Edit the HTML file in `src/pages/`
2. Modify CSS if needed in `src/styles/`
3. Test with web server: `node src/scripts/server.js`
4. Render to PNG: `node src/scripts/render_labels.js`
5. Print: `python src/scripts/print_png_to_zpl.py`

#### Adding New Labels

1. Create HTML file in `src/pages/`
2. Add CSS file in `src/styles/` (optional)
3. Update `pageConfigs` in `server.js`
4. Add to `pages` array in `render_labels.js`

### Print Resolution

- **Zebra Labels:** 203 DPI (standard thermal printer resolution)
- **Calculations:**
  - 4×6 label: 4 × 203 = 812px width, 6 × 203 = 1218px height
  - 4×3 label: 4 × 203 = 812px width, 3 × 203 = 609px height

## Troubleshooting

### Common Issues

**Playwright not found:**

```powershell
npx playwright install chromium
```

**Python module errors:**

```powershell
pip install --upgrade zebrafy qrcode pillow PyPDF2 reportlab
```

**Printer not responding:**

- Verify printer IP address
- Check network connectivity: `ping YOUR_PRINTER_IP`
- Ensure printer is on ZPL mode (not EPL)
- Test with `--no-print` first to verify ZPL generation

**QR code not working:**

- Regenerate QR code if IP changed
- Verify server is running on port 3000
- Check firewall settings

## License

Internal use only - TCL North America warehouse operations.

## Contact

For issues or questions, contact the warehouse IT team.
