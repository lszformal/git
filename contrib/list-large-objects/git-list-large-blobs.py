#!/usr/bin/env python3
"""List large blob objects in the current Git repository.

This helper uses ``git rev-list`` and ``git cat-file --batch-check`` to find
blob objects and report those whose size exceeds a configurable threshold.
It is intended for quick audits of repositories that have unexpectedly large
objects (for example when diagnosing pushes that were rejected by size
restrictions).
"""

from __future__ import annotations

import argparse
import subprocess
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class BlobInfo:
    oid: str
    size: int
    path: Optional[str]


def parse_rev_list() -> List[BlobInfo]:
    """Return blob candidates from ``git rev-list --objects --all`` output."""
    rev_output = subprocess.run(
        ["git", "rev-list", "--objects", "--all"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout

    blobs: List[BlobInfo] = []
    for line in rev_output.splitlines():
        if not line:
            continue
        parts = line.split(maxsplit=1)
        oid = parts[0]
        path = parts[1] if len(parts) > 1 else None
        blobs.append(BlobInfo(oid=oid, size=0, path=path))
    return blobs


def fill_sizes(blobs: List[BlobInfo]) -> None:
    """Populate ``size`` for each blob candidate using a batch request."""
    if not blobs:
        return

    proc = subprocess.Popen(
        ["git", "cat-file", "--batch-check"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )

    assert proc.stdin is not None
    assert proc.stdout is not None

    for blob in blobs:
        proc.stdin.write(f"{blob.oid}\n")
    proc.stdin.close()

    for blob in blobs:
        info = proc.stdout.readline()
        if not info:
            break
        parts = info.strip().split()
        if len(parts) < 3:
            continue
        _oid, obj_type, obj_size = parts[:3]
        if obj_type != "blob":
            blob.size = 0
            continue
        blob.size = int(obj_size)

    proc.wait()


def human_size(size: int) -> str:
    """Return a human-friendly size with binary prefixes."""
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(size)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} {units[-1]}"


def filter_large_blobs(blobs: Iterable[BlobInfo], min_size: int) -> List[BlobInfo]:
    return [blob for blob in blobs if blob.size >= min_size]


def print_report(blobs: List[BlobInfo]) -> None:
    if not blobs:
        print("No blobs meet the configured minimum size.")
        return

    blobs.sort(key=lambda b: b.size, reverse=True)
    width = max(len(blob.oid) for blob in blobs)

    print(f"Found {len(blobs)} blob(s) exceeding the threshold:\n")
    for blob in blobs:
        path_display = blob.path or "(no path available)"
        print(f"{blob.oid.ljust(width)}  {human_size(blob.size):>10}  {path_display}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List blobs larger than a given size in the current Git repository.",
    )
    parser.add_argument(
        "--min-size",
        type=str,
        default="5MiB",
        help=(
            "Minimum blob size to report. Supports suffixes like KiB, MiB, GiB. "
            "Defaults to 5MiB."
        ),
    )
    return parser.parse_args()


def parse_min_size(raw: str) -> int:
    suffixes = {
        "K": 1024,
        "KB": 1024,
        "KIB": 1024,
        "M": 1024 ** 2,
        "MB": 1024 ** 2,
        "MIB": 1024 ** 2,
        "G": 1024 ** 3,
        "GB": 1024 ** 3,
        "GIB": 1024 ** 3,
    }

    upper = raw.strip().upper()
    for suffix, factor in suffixes.items():
        if upper.endswith(suffix):
            return int(float(upper[: -len(suffix)]) * factor)
    return int(float(upper))


def main() -> None:
    args = parse_args()
    min_size = parse_min_size(args.min_size)

    blobs = parse_rev_list()
    fill_sizes(blobs)
    large_blobs = filter_large_blobs(blobs, min_size)
    print_report(large_blobs)


if __name__ == "__main__":
    main()
