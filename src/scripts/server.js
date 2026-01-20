const http = require("http");
const path = require("path");
const fs = require("fs");
const net = require("net");
const { chromium } = require("playwright");
const { PNG } = require("pngjs");
const { rgbaToZ64 } = require("zpl-image");

const PORT = process.env.PORT || 3000;
const ROOT = path.join(__dirname, "..", "..");
const OUTPUT = path.join(ROOT, "output");
const PRINTER_IP = process.env.PRINTER_IP || "10.10.200.138";

const pageConfigs = {
  label: {
    name: "Hold OSD Quarantine 4x6",
    file: path.join(ROOT, "src", "pages", "hold_OSD_quarantine_card.html"),
    viewport: { width: 812, height: 1218 },
  },
  location_label: {
    name: "Location Label 4x3",
    file: path.join(ROOT, "src", "pages", "location_label.html"),
    viewport: { width: 812, height: 609 },
  },
  audit: {
    name: "Master Logistics Tally & 3PL Audit",
    file: path.join(
      ROOT,
      "src",
      "pages",
      "master_logistics_tally_and_3PL_revenue_audit_card.html"
    ),
    viewport: { width: 1024, height: 1400 },
  },
  audit_pallet_location: {
    name: "Master Logistics Tally & 3PL Audit + Pallet Location",
    file: path.join(
      ROOT,
      "src",
      "pages",
      "master_logistics_tally_and_3PL_revenue_audit_card_pallet_location.html"
    ),
    viewport: { width: 1024, height: 1400 },
  },
  outbound_audit: {
    name: "Outbound OSD Audit",
    file: path.join(ROOT, "src", "pages", "outbound_OSD_audit.html"),
    viewport: { width: 1024, height: 1400 },
  },
  transaction_log: {
    name: "Transaction Log",
    file: path.join(ROOT, "src", "pages", "transaction_log.html"),
    viewport: { width: 1024, height: 1400 },
  },
};

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return (
    {
      ".html": "text/html",
      ".css": "text/css",
      ".js": "application/javascript",
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".gif": "image/gif",
      ".webp": "image/webp",
      ".pdf": "application/pdf",
      ".ico": "image/x-icon",
    }[ext] || "application/octet-stream"
  );
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  let filePath;

  if (url.pathname === "/" || url.pathname === "/index.html") {
    return serveIndex(res);
  }

  const candidates = [
    path.join(ROOT, url.pathname),
    path.join(ROOT, "src", "pages", path.basename(url.pathname)),
    path.join(ROOT, "src", "styles", path.basename(url.pathname)),
    path.join(ROOT, "assets", url.pathname.replace("/assets/", "")), // handles /assets/images/...
  ];

  for (const candidate of candidates) {
    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      const data = fs.readFileSync(candidate);
      return send(res, 200, data, { "Content-Type": contentType(candidate) });
    }
  }

  send(res, 404, "Not found");
}

function serveIndex(res) {
  const tabs = [
    {
      id: "label",
      title: "Hold OSD 4x6",
      url: "/src/pages/hold_OSD_quarantine_card.html",
    },
    {
      id: "location_label",
      title: "Location 3x4",
      url: "/src/pages/location_label.html",
    },
    {
      id: "audit",
      title: "Audit Card",
      url: "/src/pages/master_logistics_tally_and_3PL_revenue_audit_card.html",
    },
    {
      id: "audit_pallet_location",
      title: "Audit Card + Pallet Location",
      url: "/src/pages/master_logistics_tally_and_3PL_revenue_audit_card_pallet_location.html",
    },
    {
      id: "transaction_log",
      title: "Transaction Log",
      url: "/src/pages/transaction_log.html",
    },
    {
      id: "outbound_audit",
      title: "Outbound OSD Audit",
      url: "/src/pages/outbound_OSD_audit.html",
    },
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
    ${tabs
      .map(
        (t, idx) =>
          `<div class="tab${idx === 0 ? " active" : ""}" data-url="${t.url}">${
            t.title
          }</div>`
      )
      .join("")}
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

  send(res, 200, html, { "Content-Type": "text/html" });
}

async function renderToPng(typeKey) {
  const cfg = pageConfigs[typeKey];
  if (!cfg) throw new Error(`Unknown page type: ${typeKey}`);
  if (!fs.existsSync(OUTPUT)) fs.mkdirSync(OUTPUT, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({
    viewport: { ...cfg.viewport, deviceScaleFactor: 1 },
  });
  await page.emulateMedia({ media: "print" });
  const url = `file://${cfg.file.replace(/\\/g, "/")}`;
  await page.goto(url);
  const pngPath = path.join(OUTPUT, `${typeKey}.png`);
  await page.screenshot({ path: pngPath, fullPage: true });
  await browser.close();
  return pngPath;
}

/**
 * Convert RGBA image to grayscale and apply Floyd-Steinberg dithering
 * @param {Buffer} rgba - RGBA pixel data
 * @param {number} width - Image width
 * @param {number} height - Image height
 * @returns {Buffer} - Dithered RGBA buffer
 */
function ditherImage(rgba, width, height) {
  // Create a copy to avoid mutating the original
  const dithered = Buffer.from(rgba);

  // First pass: convert to grayscale
  for (let i = 0; i < rgba.length; i += 4) {
    const r = rgba[i];
    const g = rgba[i + 1];
    const b = rgba[i + 2];
    // Standard grayscale conversion
    const gray = Math.round(0.299 * r + 0.587 * g + 0.114 * b);
    dithered[i] = gray;
    dithered[i + 1] = gray;
    dithered[i + 2] = gray;
    // Keep alpha unchanged
    dithered[i + 3] = rgba[i + 3];
  }

  // Second pass: Floyd-Steinberg dithering
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = (y * width + x) * 4;
      const oldPixel = dithered[idx];
      const newPixel = oldPixel < 128 ? 0 : 255;
      const quantError = oldPixel - newPixel;

      dithered[idx] = newPixel;
      dithered[idx + 1] = newPixel;
      dithered[idx + 2] = newPixel;

      // Distribute error to neighboring pixels
      // Right pixel (x+1, y)
      if (x + 1 < width) {
        const rightIdx = idx + 4;
        dithered[rightIdx] = Math.max(
          0,
          Math.min(255, dithered[rightIdx] + (quantError * 7) / 16)
        );
        dithered[rightIdx + 1] = dithered[rightIdx];
        dithered[rightIdx + 2] = dithered[rightIdx];
      }

      // Bottom-left pixel (x-1, y+1)
      if (y + 1 < height && x > 0) {
        const blIdx = ((y + 1) * width + (x - 1)) * 4;
        dithered[blIdx] = Math.max(
          0,
          Math.min(255, dithered[blIdx] + (quantError * 3) / 16)
        );
        dithered[blIdx + 1] = dithered[blIdx];
        dithered[blIdx + 2] = dithered[blIdx];
      }

      // Bottom pixel (x, y+1)
      if (y + 1 < height) {
        const bottomIdx = ((y + 1) * width + x) * 4;
        dithered[bottomIdx] = Math.max(
          0,
          Math.min(255, dithered[bottomIdx] + (quantError * 5) / 16)
        );
        dithered[bottomIdx + 1] = dithered[bottomIdx];
        dithered[bottomIdx + 2] = dithered[bottomIdx];
      }

      // Bottom-right pixel (x+1, y+1)
      if (y + 1 < height && x + 1 < width) {
        const brIdx = ((y + 1) * width + (x + 1)) * 4;
        dithered[brIdx] = Math.max(
          0,
          Math.min(255, dithered[brIdx] + (quantError * 1) / 16)
        );
        dithered[brIdx + 1] = dithered[brIdx];
        dithered[brIdx + 2] = dithered[brIdx];
      }
    }
  }

  return dithered;
}

function pngToZpl(pngPath) {
  const buf = fs.readFileSync(pngPath);
  const png = PNG.sync.read(buf);

  // Apply grayscale and dithering before ZPL conversion
  const ditheredData = ditherImage(png.data, png.width, png.height);

  const res = rgbaToZ64(ditheredData, png.width);
  const zpl = `^XA^FO0,0^GFA,${res.length},${res.length},${res.rowlen},${res.z64}^FS^XZ`;
  return {
    zpl,
    meta: {
      width: png.width,
      height: png.height,
      length: res.length,
      rowlen: res.rowlen,
    },
  };
}

function sendZplToPrinter(zpl, printerIp = PRINTER_IP, port = 9100) {
  return new Promise((resolve, reject) => {
    const client = new net.Socket();
    client.setTimeout(10000);
    client.connect(port, printerIp, () => {
      client.write(zpl, "utf8", () => client.end());
    });
    client.on("close", resolve);
    client.on("timeout", () => {
      client.destroy();
      reject(new Error(`Printer connection timed out (${printerIp}:${port})`));
    });
    client.on("error", reject);
  });
}

async function handlePrint(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  const typeKey = url.searchParams.get("type") || "location_label";

  try {
    // Audit card uses regular printer (browser print), not ZPL
    if (typeKey === "audit" || typeKey === "transaction_log") {
      send(
        res,
        200,
        JSON.stringify({
          ok: true,
          message: "Use browser print dialog",
          useWindowPrint: true,
        }),
        { "Content-Type": "application/json" }
      );
      return;
    }

    // For label types, render to PNG and send to ZPL printer
    const pngPath = await renderToPng(typeKey);
    const { zpl, meta } = pngToZpl(pngPath);
    const zplPath = path.join(OUTPUT, `${typeKey}.zpl`);
    fs.writeFileSync(zplPath, zpl, "utf8");
    await sendZplToPrinter(zpl);
    send(
      res,
      200,
      JSON.stringify({ ok: true, message: "Printed", zplPath, meta }),
      { "Content-Type": "application/json" }
    );
  } catch (err) {
    send(res, 500, JSON.stringify({ ok: false, error: err.message }), {
      "Content-Type": "application/json",
    });
  }
}

const server = http.createServer((req, res) => {
  if (req.url.startsWith("/api/print")) return handlePrint(req, res);
  return serveStatic(req, res);
});

server.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
