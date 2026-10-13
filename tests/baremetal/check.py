#!/usr/bin/env python3
"""Run bounded machine-mode regressions and reject incompatible boot options."""

from pathlib import Path
import subprocess
import sys
import tempfile

emulator = sys.argv[1]


def run(*args):
    return subprocess.run(
        [emulator, *args],
        capture_output=True,
        text=True,
        timeout=5,
    )


for image in sys.argv[2:]:
    result = run("-M", image)
    if result.returncode:
        sys.exit(f"{image}: failed ({result.returncode})\n{result.stderr}")

for options in [("-k", "unused"), ("-b", "unused"), ("-x", "vrng")]:
    result = run("-M", sys.argv[2], *options)
    if (
        not result.returncode
        or "cannot be combined" not in result.stdout + result.stderr
    ):
        sys.exit(f"Conflicting boot options were not rejected: {options}")

with tempfile.TemporaryDirectory() as directory:
    empty = Path(directory) / "empty.bin"
    empty.write_bytes(b"")
    if not run("-M", str(empty)).returncode:
        sys.exit("Empty image was accepted")
    # ECALL without mtvec must fail, rather than retrying forever.
    unhandled = Path(directory) / "unhandled.bin"
    unhandled.write_bytes(bytes.fromhex("73000000"))
    if not run("-M", str(unhandled)).returncode:
        sys.exit("Unhandled machine trap was accepted")

print("Bare-metal trap and boot-option tests passed")
