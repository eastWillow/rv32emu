#!/usr/bin/env python3
"""Format enabled ranges without laying out large clang-format-off macros."""

import argparse
from pathlib import Path
import re
import subprocess


def enabled_ranges(source):
    lines = source.splitlines()
    start = 1
    enabled = True
    ranges = []
    marker = re.compile(r"^\s*(?://|/\*)\s*clang-format (off|on)\b")
    for number, line in enumerate(lines, 1):
        match = marker.match(line)
        if not match:
            continue
        if match[1] == "off" and enabled:
            if start < number:
                ranges.append((start, number - 1))
            enabled = False
        elif match[1] == "on" and not enabled:
            start = number + 1
            enabled = True
    if enabled and start <= len(lines):
        ranges.append((start, len(lines)))
    return ranges


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--formatter", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--in-place", action="store_true")
    parser.add_argument("files", nargs="*")
    args = parser.parse_args()
    failed = False
    for filename in args.files:
        ranges = enabled_ranges(Path(filename).read_text())
        if not ranges:
            continue
        command = [args.formatter, "--style=file"]
        command += [f"--lines={start}:{end}" for start, end in ranges]
        command += ["--dry-run", "--Werror"] if args.check else ["-i"]
        command.append(filename)
        failed |= subprocess.run(command).returncode != 0
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
