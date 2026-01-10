"""convert html to png
node -e "const { chromium } = require('playwright'); (async() => {
  const browser = await chromium.launch({ headless: true });
 PNG -> ZPL -> send to Zebra printer.

  Usage examples:
  python src/scripts/print_png_to_zpl.py --png ../output/location_label.png --image-type location_label --printer-ip 10.10.200.138
  python src/scripts/print_png_to_zpl.py --image-type label --output-dir ../output

  Notes:
  - If --png is omitted, the script looks in --output-dir for <image-type>.png
  - ZPL is written alongside the PNG in the output dir
  - Printer IP defaults to env PRINTER_IP or 10.10.200.138
"""

import argparse
import os
import socket
from zebrafy import ZebrafyImage


def to_zpl(png_path: str) -> bytes:
  with open(png_path, "rb") as image_file:
    return ZebrafyImage(image_file.read(), invert=True).to_zpl().encode()


def save_zpl(zpl_bytes: bytes, zpl_path: str):
  with open(zpl_path, "wb") as f:
    f.write(zpl_bytes)


def print_zpl_file(ip_address: str, file_path: str, port: int = 9100):
  with open(file_path, "rb") as f:
    zpl_data = f.read()

  with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.settimeout(10)
    s.connect((ip_address, port))
    s.sendall(zpl_data)
    print(f"Sent {file_path} to {ip_address}:{port}")


def main():
  parser = argparse.ArgumentParser(description="Convert PNG to ZPL and send to Zebra printer.")
  parser.add_argument("--png", help="Path to PNG file. If omitted, uses <output-dir>/<image-type>.png")
  parser.add_argument("--image-type", default="location_label", help="label or location_label or custom basename")
  parser.add_argument("--output-dir", default=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "output")), help="Folder containing PNG/ZPL")
  parser.add_argument("--printer-ip", default=os.getenv("PRINTER_IP", "10.10.200.138"), help="Zebra printer IP")
  parser.add_argument("--no-print", action="store_true", help="Only write ZPL, do not send to printer")
  args = parser.parse_args()

  output_dir = os.path.abspath(args.output_dir)
  if not os.path.isdir(output_dir):
    raise SystemExit(f"Output dir not found: {output_dir}")

  png_path = os.path.abspath(args.png) if args.png else os.path.join(output_dir, f"{args.image_type}.png")
  if not os.path.isfile(png_path):
    raise SystemExit(f"PNG not found: {png_path}")

  zpl_path = os.path.join(output_dir, f"{args.image_type}.zpl")

  zpl_bytes = to_zpl(png_path)
  save_zpl(zpl_bytes, zpl_path)
  print(f"Wrote ZPL -> {zpl_path}")

  if not args.no_print:
    print_zpl_file(args.printer_ip, zpl_path)


if __name__ == "__main__":
  main()
