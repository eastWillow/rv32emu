#!/usr/bin/env python3
"""Repeat one fixed Zephyr ztest workload and compare host completion time."""
import argparse
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for engine in ("qemu", "rv32emu"):
        parser.add_argument(f"--{engine}-elf", type=Path, required=True)
        parser.add_argument(f"--{engine}-bin", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeat", type=int, default=7)
    args = parser.parse_args()
    if args.repeat < 1:
        parser.error("--repeat must be positive")
    results = {"qemu": [], "rv32emu": []}
    case_signature = None
    suite_signature = None
    runner = Path(__file__).with_name("compare-run.py")
    for repeat in range(args.repeat):
        # Alternate order to reduce a consistent first-run advantage.
        order = ("qemu", "rv32emu") if repeat % 2 == 0 else ("rv32emu", "qemu")
        for engine in order:
            output = args.out.resolve() / str(repeat)
            env = dict(os.environ, ZEPHYR_COMPARE_OUT=str(output))
            command = [
                sys.executable,
                str(runner),
                "--engine",
                engine,
                "--elf",
                str(getattr(args, f"{engine}_elf").resolve()),
                "--bin",
                str(getattr(args, f"{engine}_bin").resolve()),
                "--timeout",
                "60",
            ]
            subprocess.run(
                command, env=env, stdout=subprocess.DEVNULL, check=True
            )
            paths = list((output / engine).glob("*.json"))
            if len(paths) != 1:
                raise RuntimeError(f"Expected one result in {output / engine}")
            result = json.loads(paths[0].read_text())
            if result["verdict"] != "passed":
                raise RuntimeError(
                    f"{engine} did not complete the ztest workload"
                )
            console = paths[0].with_suffix(".log").read_text()
            suites = re.findall(r"Running TESTSUITE (\S+)", console)
            cases = re.findall(r"\b(PASS|SKIP|FAIL) - (test_\w+)", console)
            if (
                not suites
                or not cases
                or any(status == "FAIL" for status, _ in cases)
            ):
                raise RuntimeError(
                    "The demo requires successful ztest case outcomes"
                )
            if case_signature is None:
                case_signature = cases
                suite_signature = suites
            elif cases != case_signature or suites != suite_signature:
                raise RuntimeError(
                    "The engines did not complete the same test cases"
                )
            results[engine].append(result["host_launch_to_verdict_seconds"])
            print(
                f"Run {repeat + 1}/{args.repeat}: {engine} "
                f"{results[engine][-1] * 1000:.3f} ms",
                flush=True,
            )
    medians = {
        engine: statistics.median(times) for engine, times in results.items()
    }
    summary = {
        "measurement": "Host launch-to-ztest-verdict; includes firmware and boot",
        "seconds": results,
        "median_seconds": medians,
        "case_outcomes": case_signature,
        "suite_names": suite_signature,
        "qemu_over_rv32emu_median": medians["qemu"] / medians["rv32emu"],
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
