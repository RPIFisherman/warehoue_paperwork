"""
Simple HTTP server to share a PDF with embedded QR code on your local network.
Run: python serve_demo.py --port 8000
Then visit: http://<your-LAN-IP>:8000/ from another machine.
"""

from __future__ import annotations

import argparse
import http.server
import socket
from pathlib import Path
from typing import Optional

try:
    import qrcode
    from PIL import Image
    from PyPDF2 import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from io import BytesIO
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing deps. Install with: pip install 'qrcode[pil]' pillow PyPDF2 reportlab pdf2image") from exc

ROOT = Path(__file__).resolve().parent
PDF_FILE = ROOT / "Master Logistics Tally & 3PL Revenue Audit Card-1225.pdf"
PDF_WITH_QR = ROOT / "Master Logistics Tally & 3PL Revenue Audit Card-1225_with_QR.pdf"


class DemoHandler(http.server.SimpleHTTPRequestHandler):
    """Serve PDF with embedded QR code at / with HTML viewer."""

    def __init__(self, *args, directory: Optional[str] = None, **kwargs):
        # Force the directory so the handler can find files reliably.
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802 (http.server naming)
        if self.path in {"/", ""}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            pdf_filename = PDF_WITH_QR.name
            self.wfile.write(
                f"""
                <html>
                <head>
                    <title>Master Logistics Tally & 3PL Revenue Audit Card</title>
                    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
                    <style>
                        body {{ margin: 0; padding: 20px; background: #f5f5f5; font-family: Arial, sans-serif; }}
                        h1 {{ color: #333; }}
                        .controls {{ margin: 10px 0; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
                        .controls button {{ padding: 8px 16px; cursor: pointer; }}
                        .zoom-controls {{ display: flex; gap: 5px; }}
                        .zoom-controls button {{ padding: 6px 12px; }}
                        #zoom-level {{ padding: 8px 12px; background: #e0e0e0; border-radius: 4px; min-width: 60px; text-align: center; }}
                        #pdf-container {{ width: 100%; height: 80vh; border: 1px solid #ccc; overflow: auto; background: #fff; touch-action: manipulation; }}
                        canvas {{ display: block; margin: 0 auto; }}
                    </style>
                </head>
                <body>
                    <h1>Master Logistics Tally & 3PL Revenue Audit Card</h1>
                    <div class="controls">
                        <a href="/{pdf_filename}" download>
                            <button>Download PDF with QR Code</button>
                        </a>
                        <button onclick="previousPage()">← Previous</button>
                        <span id="page-info"></span>
                        <button onclick="nextPage()">Next →</button>
                        <div class="zoom-controls">
                            <button onclick="zoomOut()">−</button>
                            <span id="zoom-level">100%</span>
                            <button onclick="zoomIn()">+</button>
                        </div>
                    </div>
                    <div id="pdf-container"></div>
                    <script>
                        let pdfDoc = null;
                        let currentPage = 1;
                        let currentZoom = 1.5;
                        let touchStartDistance = 0;
                        const pdfjsLib = window['pdfjs-dist/build/pdf'];
                        pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
                        
                        async function loadPdf() {{
                            pdfDoc = await pdfjsLib.getDocument('/{pdf_filename}').promise;
                            document.getElementById('page-info').textContent = `Page 1 / ${{pdfDoc.numPages}}`;
                            renderPage(currentPage);
                        }}
                        
                        async function renderPage(pageNum) {{
                            const page = await pdfDoc.getPage(pageNum);
                            const viewport = page.getViewport({{ scale: currentZoom }});
                            const canvas = document.createElement('canvas');
                            const context = canvas.getContext('2d');
                            canvas.width = viewport.width;
                            canvas.height = viewport.height;
                            
                            const container = document.getElementById('pdf-container');
                            container.innerHTML = '';
                            container.appendChild(canvas);
                            
                            await page.render({{
                                canvasContext: context,
                                viewport: viewport
                            }}).promise;
                            
                            document.getElementById('page-info').textContent = `Page ${{pageNum}} / ${{pdfDoc.numPages}}`;
                            updateZoomDisplay();
                        }}
                        
                        function zoomIn() {{
                            currentZoom = Math.min(currentZoom + 0.2, 5);
                            renderPage(currentPage);
                        }}
                        
                        function zoomOut() {{
                            currentZoom = Math.max(currentZoom - 0.2, 0.5);
                            renderPage(currentPage);
                        }}
                        
                        function updateZoomDisplay() {{
                            const zoomPercent = Math.round(currentZoom / 1.5 * 100);
                            document.getElementById('zoom-level').textContent = zoomPercent + '%';
                        }}
                        
                        function getTouchDistance(touch1, touch2) {{
                            const dx = touch1.clientX - touch2.clientX;
                            const dy = touch1.clientY - touch2.clientY;
                            return Math.sqrt(dx * dx + dy * dy);
                        }}
                        
                        const container = document.getElementById('pdf-container');
                        
                        container.addEventListener('touchstart', (e) => {{
                            if (e.touches.length === 2) {{
                                touchStartDistance = getTouchDistance(e.touches[0], e.touches[1]);
                                e.preventDefault();
                            }}
                        }}, false);
                        
                        container.addEventListener('touchmove', (e) => {{
                            if (e.touches.length === 2) {{
                                const currentDistance = getTouchDistance(e.touches[0], e.touches[1]);
                                const zoomDelta = (currentDistance - touchStartDistance) * 0.005;
                                
                                currentZoom = Math.min(Math.max(currentZoom + zoomDelta, 0.5), 5);
                                touchStartDistance = currentDistance;
                                
                                renderPage(currentPage);
                                e.preventDefault();
                            }}
                        }}, false);
                        
                        document.addEventListener('wheel', (e) => {{
                            if (e.ctrlKey || e.metaKey) {{
                                e.preventDefault();
                                const zoomDelta = -e.deltaY * 0.001;
                                currentZoom = Math.min(Math.max(currentZoom + zoomDelta, 0.5), 5);
                                renderPage(currentPage);
                            }}
                        }}, false);
                        
                        loadPdf();
                    </script>
                </body>
                </html>
                """.encode("utf-8")
            )
            return
        return super().do_GET()

    def log_message(self, format: str, *args) -> None:  # noqa: A003 (shadow builtins)
        # Reduce noise; still logs to stdout.
        return super().log_message(format, *args)


def get_lan_ip() -> str:
    """Best-effort LAN IP discovery for quick copy/paste."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def add_qr_to_pdf(pdf_path: Path, output_path: Path, target_url: str) -> None:
    """Add a QR code to the bottom-right corner of the last page of a PDF."""
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    
    # Scale QR code (roughly 1 inch = 72 points in PDF)
    qr_size = 72  # 1 inch (half size)
    qr_img = qr_img.resize((qr_size, qr_size))
    
    # Save QR code as temporary image
    qr_temp = ROOT / "temp_qr.png"
    qr_img.save(qr_temp)
    
    # Read the original PDF
    reader = PdfReader(str(pdf_path))
    writer = PdfWriter()
    
    # Get last page
    last_page = reader.pages[-1]
    page_height = float(last_page.mediabox.height)
    page_width = float(last_page.mediabox.width)
    
    # Create an overlay PDF with the QR code
    qr_overlay = BytesIO()
    c = canvas.Canvas(qr_overlay, pagesize=(page_width, page_height))
    
    # Position QR in bottom-right corner with margin
    margin = 36  # 0.5 inch
    qr_x = page_width - qr_size - margin - 54  # Additional 0.75 inch left
    qr_y = margin
    
    c.drawImage(str(qr_temp), qr_x, qr_y, width=qr_size, height=qr_size)
    c.save()
    
    # Merge QR overlay with original PDF
    qr_overlay.seek(0)
    overlay_reader = PdfReader(qr_overlay)
    overlay_page = overlay_reader.pages[0]
    
    last_page.merge_page(overlay_page)
    
    # Add all pages except the last
    for i in range(len(reader.pages) - 1):
        writer.add_page(reader.pages[i])
    
    # Add the last page with QR code
    writer.add_page(last_page)
    
    # Write output PDF
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)
    
    # Clean up temp file
    qr_temp.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve PDF with QR code over HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    if not PDF_FILE.exists():
        raise FileNotFoundError(f"Missing PDF at {PDF_FILE}")

    lan_ip = get_lan_ip()
    lan_url = f"http://{lan_ip}:{args.port}/"
    add_qr_to_pdf(PDF_FILE, PDF_WITH_QR, lan_url)

    server = http.server.ThreadingHTTPServer(("0.0.0.0", args.port), DemoHandler)
    print(f"Serving PDF from {PDF_FILE}")
    print(f"QR overlay saved to {PDF_WITH_QR}")
    print(f"Local:      http://127.0.0.1:{args.port}/")
    print(f"LAN (try):  {lan_url}")
    print("Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
