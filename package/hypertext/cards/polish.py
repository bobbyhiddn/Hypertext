#!/usr/bin/env python3
"""Deterministic finalization for generated cards.

Historically this command sent the complete, already-rendered card through a
second image-generation request to remove possible brackets.  That request
could resample clean text and introduce halos or small layout changes.  The
generator/reviewer contracts already reject brackets, so finalization must be
pixel preserving.
"""
import argparse
import os
import shutil
import sys


def finalize_card(in_path: str, out_path: str) -> None:
    """Publish *in_path* without decoding, resampling, or recompositing it."""
    if os.path.abspath(in_path) == os.path.abspath(out_path):
        return
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    shutil.copyfile(in_path, out_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove brackets from generated card image")
    parser.add_argument("in_path", help="Input image path")
    parser.add_argument("out_path", nargs="?", help="Output image path (defaults to overwrite input)")

    args = parser.parse_args()
    in_path = args.in_path
    out_path = args.out_path or in_path

    if not os.path.exists(in_path):
        print(f"Error: {in_path} not found.")
        return 1

    print(f"Finalizing card without pixel changes -> {out_path}...")
    try:
        finalize_card(in_path, out_path)
        print("Finalization complete.")
    except Exception as e:
        print(f"Error polishing card: {e}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
