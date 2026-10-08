#!/usr/bin/env python3
"""Run raw system-mode regression images through a pseudo-terminal."""

import argparse
import os
import pty
import select
import subprocess
import time
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument("--emulator", type=Path, required=True)
parser.add_argument("--timeout", type=float, default=5.0)
parser.add_argument("images", nargs="+", type=Path)
args = parser.parse_args()


def run(image: Path) -> None:
    disk = image.parent / "empty-rootfs.img"
    if not disk.exists():
        with disk.open("wb") as stream:
            stream.truncate(1024 * 1024)
    master, slave = pty.openpty()
    process = subprocess.Popen(
        [
            str(args.emulator.resolve()),
            "-k",
            str(image.resolve()),
            "-x",
            f"vblk:{disk.resolve()},rootfs",
        ],
        stdin=slave,
        stdout=slave,
        stderr=slave,
        close_fds=True,
    )
    os.close(slave)
    output = bytearray()
    input_sent = False
    deadline = time.monotonic() + args.timeout
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.1)
            if ready:
                try:
                    output.extend(os.read(master, 4096))
                except OSError:
                    break
            if image.stem == "uart-iir" and b"UART-READY" in output and not input_sent:
                os.write(master, b"U")
                input_sent = True
            complete_lines = output.split(b"\n")[:-1]
            if any(
                b"PASS " in line or b"FAIL " in line for line in complete_lines
            ):
                break
            if process.poll() is not None:
                break
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        os.close(master)

    transcript = output.decode("utf-8", errors="replace").replace("\r", "")
    print(transcript, end="" if transcript.endswith("\n") else "\n")
    expected = f"PASS {image.stem}"
    if expected not in transcript:
        raise RuntimeError(f"{image.name}: expected {expected!r}")


for image in args.images:
    print(f"Running {image.stem} ...", flush=True)
    run(image)
