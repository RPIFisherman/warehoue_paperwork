const http = require('http');
const path = require('path');
const fs = require('fs');
const { chromium } = require('playwright');
const { spawn } = require('child_process');

const PORT = process.env.PORT || 3000;
const ROOT = path.join(__dirname, '..', '..');
const OUTPUT = path.join(ROOT, 'output');
const PRINTER_IP = process.env.PRINTER_IP || '10.10.200.138';

const pageConfigs = {
  label: {
    name: 'Hold OSD Quarantine 4x6',
    file: path.join(ROOT, 'src', 'pages', 'hold_OSD_quarantine_card.html'),
    viewport: { width: 812, height: 1218 },
  },
  location_label: {
    name: 'Location Label 4x3',
    file: path.join(ROOT, 'src', 'pages', 'location_label.html'),
    viewport: { width: 812, height: 609 },
  },
  audit: {
    name: 'Master Logistics Tally & 3PL Audit',
    file: path.join(ROOT, 'src', 'pages', 'master_logistics_tally_and_3PL_revenue_audit_card.html'),
    viewport: { width: 1024, height: 1400 },
  },
  transaction_log: {
    name: 'Transaction Log',
    file: path.join(ROOT, 'src', 'pages', 'transaction_log.html'),
    viewport: { width: 1024, height: 1400 },
  },
};

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.pdf': 'application/pdf',
    '.ico': 'image/x-icon',
  }[ext] || 'application/octet-stream';
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  let filePath;

  if (url.pathname === '/' || url.pathname === '/index.html') {
    return serveIndex(res);
  }

  const candidates = [
    path.join(ROOT, url.pathname),
    path.join(ROOT, 'src', 'pages', path.basename(url.pathname)),
    path.join(ROOT, 'src', 'styles', path.basename(url.pathname)),
    path.join(ROOT, 'assets', url.pathname.replace('/assets/', '')), // handles /assets/images/...
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      const data = fs.readFileSync(candidate);
      return send(res, 200, data, { 'Content-Type': contentType(candidate) });
    }
  }

  send(res, 404, 'Not found');
}

function serveIndex(res) {
  const tabs = [
    { id: 'label', title: 'Hold OSD 4x6', url: '/src/pages/hold_OSD_quarantine_card.html' },
    { id: 'location_label', title: 'Location 4x3', url: '/src/pages/location_label.html' },
    { id: 'audit', title: 'Audit Card', url: '/src/pages/master_logistics_tally_and_3PL_revenue_audit_card.html' },
    { id: 'transaction_log', title: 'Transaction Log', url: '/src/pages/transaction_log.html' },
  ];

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Label Viewer</title>
  <style>
    body { margin: 0; font-family: Arial, sans-serif; display: flex; flex-direction: column; height: 100vh; }
    .tabs { display: flex; background: #222; color: white; }
    .tab { padding: 10px 16px; cursor: pointer; user-select: none; }
    .tab.active { background: #444; }
    iframe { flex: 1; border: none; width: 100%; }
  </style>
</head>
<body>
  <div class="tabs">
    ${tabs.map((t, idx) => `<div class="tab${idx === 0 ? ' active' : ''}" data-url="${t.url}">${t.title}</div>`).join('')}
  </div>
  <iframe id="frame" src="${tabs[0].url}"></iframe>
  <script>
    const tabs = Array.from(document.querySelectorAll('.tab'));
    const frame = document.getElementById('frame');
    tabs.forEach(tab => tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      frame.src = tab.dataset.url;
    }));
  </script>
</body>
</html>`;

  send(res, 200, html, { 'Content-Type': 'text/html' });
}

async function renderToPng(typeKey) {
  const cfg = pageConfigs[typeKey];
  if (!cfg) throw new Error(`Unknown page type: ${typeKey}`);
  if (!fs.existsSync(OUTPUT)) fs.mkdirSync(OUTPUT, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { ...cfg.viewport, deviceScaleFactor: 1 } });
  await page.emulateMedia({ media: 'print' });
  const url = `file://${cfg.file.replace(/\\/g, '/')}`;
  await page.goto(url);
  const pngPath = path.join(OUTPUT, `${typeKey}.png`);
  await page.screenshot({ path: pngPath, fullPage: true });
  await browser.close();
  return pngPath;
}

function runPythonPrint(pngPath, typeKey) {
  return new Promise((resolve, reject) => {
    const script = path.join(ROOT, 'src', 'scripts', 'print_png_to_zpl.py');
    const args = ['--png', pngPath, '--image-type', typeKey, '--printer-ip', PRINTER_IP];
    const proc = spawn('python', [script, ...args], { cwd: ROOT });
    let stdout = '';
    let stderr = '';
    proc.stdout.on('data', d => stdout += d.toString());
    proc.stderr.on('data', d => stderr += d.toString());
    proc.on('close', code => {
      if (code === 0) return resolve({ stdout, stderr });
      reject(new Error(`python exited ${code}: ${stderr || stdout}`));
    });
  });
}

async function handlePrint(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const typeKey = url.searchParams.get('type') || 'location_label';
  
  try {
    // Audit card uses regular printer (browser print), not ZPL
    if (typeKey === 'audit' || typeKey === 'transaction_log') {
      send(res, 200, JSON.stringify({ 
        ok: true, 
        message: 'Use browser print dialog',
        useWindowPrint: true 
      }), { 'Content-Type': 'application/json' });
      return;
    }
    
    // For label types, render to PNG and send to ZPL printer
    const pngPath = await renderToPng(typeKey);
    const result = await runPythonPrint(pngPath, typeKey);
    send(res, 200, JSON.stringify({ ok: true, message: 'Printed', stdout: result.stdout }), { 'Content-Type': 'application/json' });
  } catch (err) {
    send(res, 500, JSON.stringify({ ok: false, error: err.message }), { 'Content-Type': 'application/json' });
  }
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith('/api/print')) return handlePrint(req, res);
  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
