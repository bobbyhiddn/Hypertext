#!/usr/bin/env python3
"""Convert JPEG images to PNG format.

Usage:
  python jpeg_to_png.py <path>           # Convert single file
  python jpeg_to_png.py <directory>      # Convert all JPEGs in directory
  python jpeg_to_png.py --help
"""

import argparse
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow required. Install with: pip install Pillow", file=sys.stderr)
    sys.exit(1)


def convert_file(jpeg_path: Path, keep_original: bool = False) -> Path | None:
    """Convert a single JPEG to PNG. Returns output path or None on failure."""
    if not jpeg_path.exists():
        print(f"File not found: {jpeg_path}", file=sys.stderr)
        return None

    out_path = jpeg_path.with_suffix(".png")

    try:
        img = Image.open(jpeg_path)
        img.save(out_path, "PNG")
        print(f"Converted: {jpeg_path.name} -> {out_path.name} ({img.size[0]}x{img.size[1]})")

        if not keep_original:
            jpeg_path.unlink()
            print(f"  Removed original: {jpeg_path.name}")

        return out_path
    except Exception as e:
        print(f"Error converting {jpeg_path}: {e}", file=sys.stderr)
        return None


def convert_directory(dir_path: Path, keep_original: bool = False) -> int:
    """Convert all JPEGs in a directory. Returns count of converted files."""
    if not dir_path.is_dir():
        print(f"Not a directory: {dir_path}", file=sys.stderr)
        return 0

    converted = 0
    for ext in ("*.jpeg", "*.jpg", "*.JPEG", "*.JPG"):
        for jpeg_path in dir_path.glob(ext):
            if convert_file(jpeg_path, keep_original):
                converted += 1

    return converted


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert JPEG images to PNG format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        type=Path,
        help="File or directory to convert",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep original JPEG files (default: delete after conversion)",
    )
    args = parser.parse_args()

    path = args.path

    if path.is_file():
        result = convert_file(path, args.keep)
        return 0 if result else 1
    elif path.is_dir():
        count = convert_directory(path, args.keep)
        if count == 0:
            print(f"No JPEG files found in {path}")
            return 1
        print(f"\nConverted {count} file(s)")
        return 0
    else:
        print(f"Path not found: {path}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
