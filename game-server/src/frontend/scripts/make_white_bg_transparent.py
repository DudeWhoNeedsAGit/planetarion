#!/usr/bin/env python3
"""
Make near-white backgrounds transparent for icon-style PNGs.

Approach:
- Identify "near-white" pixels using an RGB threshold.
- Flood-fill from image borders to mark the background region only (prevents nuking interior whites).
- Set alpha=0 for the background region; keep other pixels.

Typical use (in-place with backups):
  python scripts/make_white_bg_transparent.py ../src/assets/icons/nav --backup-dir _orig --threshold 245
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


def _is_near_white(r: int, g: int, b: int, threshold: int) -> bool:
    return r >= threshold and g >= threshold and b >= threshold


def _background_mask_rgba(img: Image.Image, threshold: int) -> list[list[bool]]:
    w, h = img.size
    px = img.load()
    near = [[False] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            r, g, b, _a = px[x, y]
            near[y][x] = _is_near_white(r, g, b, threshold)

    bg = [[False] * w for _ in range(h)]
    q: deque[tuple[int, int]] = deque()

    def seed(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and near[y][x] and not bg[y][x]:
            bg[y][x] = True
            q.append((x, y))

    for x in range(w):
        seed(x, 0)
        seed(x, h - 1)
    for y in range(h):
        seed(0, y)
        seed(w - 1, y)

    while q:
        x, y = q.popleft()
        if x > 0:
            seed(x - 1, y)
        if x + 1 < w:
            seed(x + 1, y)
        if y > 0:
            seed(x, y - 1)
        if y + 1 < h:
            seed(x, y + 1)

    return bg


def process_png(src: Path, dst: Path, threshold: int) -> None:
    img = Image.open(src)
    img = img.convert("RGBA")
    bg = _background_mask_rgba(img, threshold=threshold)

    w, h = img.size
    px = img.load()
    for y in range(h):
        row = bg[y]
        for x in range(w):
            if row[x]:
                r, g, b, _a = px[x, y]
                px[x, y] = (r, g, b, 0)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, format="PNG", optimize=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="A PNG file or a directory of PNG files.")
    ap.add_argument("--threshold", type=int, default=245, help="Near-white threshold (0-255). Default: 245")
    ap.add_argument("--backup-dir", default=None, help="If set, move originals into this subdir before writing output.")
    ap.add_argument(
        "--glob",
        default="*.png",
        help="Glob to use when PATH is a directory. Default: *.png",
    )
    args = ap.parse_args()

    target = Path(args.path)
    if not target.exists():
        raise SystemExit(f"Not found: {target}")

    if target.is_file():
        if target.suffix.lower() != ".png":
            raise SystemExit("Only .png is supported for file input.")
        process_png(target, target, threshold=args.threshold)
        return 0

    files = sorted(target.glob(args.glob))
    if not files:
        print(f"No files matched {args.glob} in {target}")
        return 0

    backup_dir = Path(args.backup_dir) if args.backup_dir else None
    for fp in files:
        if fp.suffix.lower() != ".png":
            continue
        src = fp
        dst = fp
        if backup_dir:
            backup_path = target / backup_dir / fp.name
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            if not backup_path.exists():
                fp.replace(backup_path)
                src = backup_path
                dst = target / fp.name
        process_png(src, dst, threshold=args.threshold)
        print(f"Wrote {dst}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

