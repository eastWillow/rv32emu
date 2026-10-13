#!/usr/bin/env python3
"""Require real ThreadX scheduling, a successful finisher, and bounded runtime."""

import subprocess
import sys

try:
    result = subprocess.run(
        [sys.argv[1], "-M", sys.argv[2]],
        capture_output=True,
        text=True,
        timeout=20,
    )
except subprocess.TimeoutExpired:
    sys.exit("ThreadX smoke test timed out")
print(result.stdout, end="")
print(result.stderr, end="", file=sys.stderr)
if result.returncode or "ThreadX smoke test PASS" not in result.stdout.splitlines():
    sys.exit("ThreadX smoke test failed")
