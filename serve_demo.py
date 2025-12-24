"""
Simple HTTP server to share demo.jpg on your local network.
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
except ImportError as exc:  # pragma: no cover - import guard
    raise SystemExit("Missing deps. Install with: pip install 'qrcode[pil]' pillow") from exc

ROOT = Path(__file__).resolve().parent
PHOTO = ROOT / "demo.jpg"
PHOTO_WITH_QR = ROOT / "demo_with_qr.jpg"


class DemoHandler(http.server.SimpleHTTPRequestHandler):
    """Serve demo_with_qr.jpg at / and still expose the original file."""

    def __init__(self, *args, directory: Optional[str] = None, **kwargs):
        # Force the directory so the handler can find demo.jpg reliably.
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):  # noqa: N802 (http.server naming)
        if self.path in {"/", ""}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                f"""
                <html>
                <head><title>demo.jpg</title></head>
                <body style='margin:0;display:flex;align-items:center;justify-content:center;background:#111;'>
                                    <img src="/demo_with_qr.jpg" alt="demo.jpg with QR" style='max-width:100vw;max-height:100vh;object-fit:contain;'>
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


def add_qr_to_photo(photo_path: Path, output_path: Path, target_url: str) -> None:
    """Overlay a QR code that points to target_url in the bottom-right corner."""

    base = Image.open(photo_path).convert("RGB")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(target_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Scale QR to roughly 1/5 of the shorter edge, capped for readability.
    target_size = int(min(base.size) * 0.2)
    target_size = max(160, min(target_size, 360))
    qr_img = qr_img.resize((target_size, target_size))

    margin = int(target_size * 0.15)
    x = max(0, base.width - target_size - margin)
    y = max(0, base.height - target_size - margin)
    base.paste(qr_img, (x, y))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.save(output_path, "JPEG", quality=90)


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve demo.jpg over HTTP")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    if not PHOTO.exists():
        raise FileNotFoundError(f"Missing demo.jpg at {PHOTO}")

    lan_ip = get_lan_ip()
    lan_url = f"http://{lan_ip}:{args.port}/"
    add_qr_to_photo(PHOTO, PHOTO_WITH_QR, lan_url)

    server = http.server.ThreadingHTTPServer(("0.0.0.0", args.port), DemoHandler)
    print(f"Serving demo.jpg from {PHOTO}")
    print(f"QR overlay saved to {PHOTO_WITH_QR}")
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
