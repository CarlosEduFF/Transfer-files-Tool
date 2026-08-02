import argparse
import sys
from pathlib import Path

from PIL import Image
from rembg import new_session, remove

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

MODELS = [
    "u2net", "u2netp", "u2net_human_seg", "u2net_cloth_seg",
    "silueta", "isnet-general-use", "isnet-anime",
]


def process_image(input_path: Path, output_path: Path, session, args) -> None:
    input_image = Image.open(input_path)
    output_image = remove(
        input_image,
        session=session,
        alpha_matting=args.alpha_matting,
        alpha_matting_foreground_threshold=args.af_threshold,
        alpha_matting_background_threshold=args.ab_threshold,
        alpha_matting_erode_size=args.matting_erode_size,
        bgcolor=args.bgcolor,
    )
    output_image.save(output_path)


def process_path(input_path: Path, output_path: Path, session, args) -> None:
    if input_path.is_dir():
        output_path.mkdir(parents=True, exist_ok=True)
        files = sorted(
            p for p in input_path.iterdir()
            if p.suffix.lower() in SUPPORTED_EXTENSIONS
        )
        if not files:
            print(f"No supported images found in '{input_path}'.", file=sys.stderr)
            sys.exit(1)

        for file in files:
            dest = output_path / f"{file.stem}.png"
            print(f"Processing {file.name} -> {dest.name}")
            process_image(file, dest, session, args)
    else:
        if input_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            print(
                f"Unsupported file extension '{input_path.suffix}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
                file=sys.stderr,
            )
            sys.exit(1)
        process_image(input_path, output_path, session, args)


def parse_bgcolor(value: str) -> tuple[int, int, int, int]:
    parts = value.split(",")
    if len(parts) not in (3, 4):
        raise argparse.ArgumentTypeError("bgcolor must be 'R,G,B' or 'R,G,B,A'")
    try:
        channels = [int(p) for p in parts]
    except ValueError:
        raise argparse.ArgumentTypeError("bgcolor channels must be integers 0-255")
    if len(channels) == 3:
        channels.append(255)
    if any(c < 0 or c > 255 for c in channels):
        raise argparse.ArgumentTypeError("bgcolor channels must be in range 0-255")
    return tuple(channels)


def main() -> None:
    parser = argparse.ArgumentParser(description="Remove the background from image(s).")
    parser.add_argument(
        "input", nargs="?", default="input.jpg",
        help="Path to an image file or a directory of images (default: input.jpg)",
    )
    parser.add_argument(
        "output", nargs="?", default="output.png",
        help="Path to the output file, or output directory when input is a directory (default: output.png)",
    )
    parser.add_argument(
        "--model", choices=MODELS, default="u2net",
        help="Segmentation model to use (default: u2net)",
    )
    parser.add_argument(
        "--alpha-matting", action="store_true",
        help="Enable alpha matting for smoother edges (hair, fur, etc.)",
    )
    parser.add_argument(
        "--af-threshold", type=int, default=240,
        help="Alpha matting foreground threshold (default: 240)",
    )
    parser.add_argument(
        "--ab-threshold", type=int, default=10,
        help="Alpha matting background threshold (default: 10)",
    )
    parser.add_argument(
        "--matting-erode-size", type=int, default=10,
        help="Alpha matting erode size (default: 10)",
    )
    parser.add_argument(
        "--bgcolor", type=parse_bgcolor, default=None,
        help="Replace transparent background with an 'R,G,B' or 'R,G,B,A' color instead of leaving it transparent",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input path '{input_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    session = new_session(args.model)
    process_path(input_path, output_path, session, args)


if __name__ == "__main__":
    main()
