"""
QR Code Generator - Generates a QR code with the local server URL
Automatically detects the local IP address and creates a QR code pointing to http://[IP]:3000
Saves the QR code to assets/images/qr.png
"""

import socket
import qrcode
import os


def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket to determine the local IP
        # This doesn't actually connect, just determines routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        # Fallback to localhost if unable to determine
        return "127.0.0.1"


def generate_qr_code(url, output_path):
    """Generate a QR code for the given URL and save it to output_path"""
    qr = qrcode.QRCode(
        version=1,  # Controls size (1-40)
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=0,  # No white margin
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    print(f"QR code generated: {output_path}")
    print(f"URL: {url}")


def main():
    # Get local IP
    local_ip = get_local_ip()
    port = 3000
    url = f"http://{local_ip}:{port}"
    
    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
    output_path = os.path.join(project_root, "assets", "images", "qr.png")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate QR code
    generate_qr_code(url, output_path)


if __name__ == "__main__":
    main()
