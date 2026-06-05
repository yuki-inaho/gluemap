#!/usr/bin/env python3
"""Create a deterministic image subset for GLUEMAP smoke runs."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=os.environ.get(
            "TOMATO_IMAGES_PATH",
            "/home/kasm-user/Desktop/NYX660_2025_12_01_17_33_27_0135/Color",
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=os.environ.get(
            "TOMATO_SMOKE_OUTPUT",
            "data/tomato_nyx660_color_smoke",
        ),
    )
    parser.add_argument(
        "--max-images",
        type=int,
        default=int(os.environ.get("TOMATO_MAX_IMAGES", "12")),
    )
    parser.add_argument(
        "--stride",
        type=int,
        default=int(os.environ.get("TOMATO_STRIDE", "30")),
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=int(os.environ.get("TOMATO_OFFSET", "0")),
    )
    parser.add_argument(
        "--mode",
        choices=["symlink", "copy"],
        default="symlink",
        help="symlink saves disk; copy is useful for moving the subset.",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="remove an existing output directory before writing.",
    )
    return parser.parse_args()


def iter_images(source: Path) -> list[Path]:
    return sorted(
        p
        for p in source.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )


def main() -> None:
    args = parse_args()
    source = args.source.expanduser().resolve()
    output = args.output.expanduser()

    if not source.is_dir():
        raise FileNotFoundError(f"source directory not found: {source}")
    if args.max_images <= 0:
        raise ValueError("--max-images must be positive")
    if args.stride <= 0:
        raise ValueError("--stride must be positive")
    if args.offset < 0:
        raise ValueError("--offset must be non-negative")

    images = iter_images(source)
    if not images:
        raise FileNotFoundError(f"no images found under: {source}")

    selected = images[args.offset :: args.stride][: args.max_images]
    if len(selected) < 2:
        raise ValueError(
            "subset must contain at least two images; adjust --stride or "
            "--max-images"
        )

    if args.clear and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    for i, src in enumerate(selected):
        dst = output / f"{i:05d}{src.suffix.lower()}"
        if dst.exists() or dst.is_symlink():
            dst.unlink()
        if args.mode == "symlink":
            os.symlink(src, dst)
        else:
            shutil.copy2(src, dst)

    manifest = output / "manifest.txt"
    manifest.write_text(
        "\n".join(f"{i:05d}\t{src}" for i, src in enumerate(selected)) + "\n"
    )
    print(
        f"wrote {len(selected)} images to {output} "
        f"(source={source}, stride={args.stride}, offset={args.offset})"
    )


if __name__ == "__main__":
    main()
