#!/usr/bin/env python3
"""
Batch background-removal for images using `rembg`.

This script is meant to be run with the repo's Python venv, e.g.:
  game-server/venv/bin/python game-server/scripts/rembg_batch.py path/to/images

It creates a timestamped backup folder, then writes PNGs with an alpha channel
either in-place or into an output directory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shutil
import sys
from pathlib import Path


def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _iter_inputs(root: Path, pattern: str, recursive: bool) -> list[Path]:
    if recursive:
        return sorted([p for p in root.rglob(pattern) if p.is_file()])
    return sorted([p for p in root.glob(pattern) if p.is_file()])


def _is_inside_dir(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def run_rembg_single(src: Path, dst: Path) -> None:
    # Import lazily so a --dry-run doesn't require rembg installed.
    from rembg import remove  # type: ignore

    dst.parent.mkdir(parents=True, exist_ok=True)
    data = src.read_bytes()
    out = remove(data)
    dst.write_bytes(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch remove backgrounds with rembg (adds alpha).")
    parser.add_argument("input_dir", type=Path, help="Directory containing images to process.")
    parser.add_argument(
        "--pattern",
        default="*.png",
        help="Glob pattern to match files (default: *.png). Example: *.jpg",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Recurse into subdirectories (default: false).",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Write processed images to this directory (keeps originals unchanged).",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a backup folder (not recommended).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Backup directory to use (default: <input_dir>/_backup_pre_rembg_<timestamp>/).",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print actions but do not run rembg.")
    args = parser.parse_args()

    input_dir = args.input_dir
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"[rembg_batch] input_dir not found or not a dir: {input_dir}", file=sys.stderr)
        return 2

    inputs = _iter_inputs(input_dir, args.pattern, args.recursive)
    if not inputs:
        print(f"[rembg_batch] No inputs matched {args.pattern} in {input_dir}")
        return 0

    backup_dir: Path | None
    if args.no_backup or args.out_dir is not None:
        backup_dir = None
    else:
        backup_dir = args.backup_dir or (input_dir / f"_backup_pre_rembg_{_timestamp()}")

    if backup_dir is not None:
        backup_dir.mkdir(parents=True, exist_ok=True)

    out_dir = args.out_dir
    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"[rembg_batch] Inputs: {len(inputs)}")
    if backup_dir is not None:
        print(f"[rembg_batch] Backup: {backup_dir}")
    if out_dir is not None:
        print(f"[rembg_batch] Output: {out_dir}")
    print(f"[rembg_batch] Pattern: {args.pattern}  Recursive: {args.recursive}")

    for src in inputs:
        if backup_dir is not None:
            if not _is_inside_dir(src, input_dir):
                raise RuntimeError(f"Refusing to backup outside input_dir: {src}")
            rel = src.resolve().relative_to(input_dir.resolve())
            backup_path = backup_dir / rel
            if args.dry_run:
                print(f"[dry-run] backup {src} -> {backup_path}")
            else:
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, backup_path)

        if out_dir is not None:
            rel = src.resolve().relative_to(input_dir.resolve())
            dst = out_dir / rel
            # Ensure PNG output for alpha, even if input is jpg.
            if dst.suffix.lower() != ".png":
                dst = dst.with_suffix(".png")
            if args.dry_run:
                print(f"[dry-run] rembg {src} -> {dst}")
            else:
                run_rembg_single(src, dst)
            continue

        # In-place: write to temp then replace.
        tmp = src.with_name(f".__rembg_tmp__{src.stem}.png")
        if args.dry_run:
            print(f"[dry-run] rembg {src} -> {tmp} (then replace {src})")
            continue

        run_rembg_single(src, tmp)
        shutil.move(tmp, src)

    print("[rembg_batch] Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
