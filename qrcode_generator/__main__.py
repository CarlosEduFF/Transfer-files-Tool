import argparse
from pathlib import Path

import qrcode
from qrcode.constants import (
    ERROR_CORRECT_H,
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
)

ERROR_CORRECTION_LEVELS = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a QR code.")
    parser.add_argument(
        "data", nargs="?", default="https://www.example.com",
        help="Data to encode (default: https://www.example.com)",
    )
    parser.add_argument(
        "output", nargs="?", default="qrcode.png",
        help="Output path; use a .svg extension for SVG output (default: qrcode.png)",
    )
    parser.add_argument("--fill-color", default="black", help="Foreground color (default: black)")
    parser.add_argument("--back-color", default="white", help="Background color (default: white)")
    parser.add_argument(
        "--error-correction", choices=ERROR_CORRECTION_LEVELS.keys(), default="M",
        help="Error correction level: L=7%%, M=15%%, Q=25%%, H=30%% (default: M)",
    )
    parser.add_argument("--box-size", type=int, default=10, help="Size of each box in pixels (default: 10)")
    parser.add_argument("--border", type=int, default=4, help="Border size in boxes (default: 4)")
    parser.add_argument(
        "--version", type=int, default=None,
        help="QR version 1-40 controlling size/capacity (default: auto)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)

    if output_path.suffix.lower() == ".svg":
        import qrcode.image.svg

        qr = qrcode.QRCode(
            version=args.version,
            error_correction=ERROR_CORRECTION_LEVELS[args.error_correction],
            box_size=args.box_size,
            border=args.border,
            image_factory=qrcode.image.svg.SvgPathImage,
        )
        qr.add_data(args.data)
        qr.make(fit=args.version is None)
        img = qr.make_image(fill_color=args.fill_color, back_color=args.back_color)
    else:
        qr = qrcode.QRCode(
            version=args.version,
            error_correction=ERROR_CORRECTION_LEVELS[args.error_correction],
            box_size=args.box_size,
            border=args.border,
        )
        qr.add_data(args.data)
        qr.make(fit=args.version is None)
        img = qr.make_image(fill_color=args.fill_color, back_color=args.back_color)

    img.save(output_path)
    print(f"Saved QR code to '{output_path}'")


if __name__ == "__main__":
    main()
