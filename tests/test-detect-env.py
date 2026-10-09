#!/usr/bin/env python3
"""Exercise Kconfig's LLVM probe with isolated toolchain installations."""

import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import unittest


DETECTOR = Path(__file__).resolve().parents[1] / "tools/detect-env.py"


class LLVMDetectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.bin = self.directory / "bin"
        self.bin.mkdir()
        self.environment = dict(os.environ, PATH=str(self.bin))
        self.environment.pop("LLVM_CONFIG", None)

    def tool(
        self, name="llvm-config", version="20.1.8", status=0, library_status=0
    ):
        path = self.bin / name
        path.write_text(
            "#!/bin/sh\n"
            f"[ {status} -eq 0 ] || exit {status}\n"
            'case "$1" in\n'
            f"  --version) printf '%s\\n' {shlex.quote(version)} ;;\n"
            f"  --libs) [ {library_status} -eq 0 ] || exit {library_status}; "
            "printf '%s\\n' '-lLLVM' ;;\n"
            "  *) exit 1 ;;\n"
            "esac\n"
        )
        path.chmod(0o755)
        return path

    def probe(self, expected, option="--have-llvm"):
        result = subprocess.run(
            [sys.executable, str(DETECTOR), option],
            env=self.environment,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0 if expected else 1, result.stderr)

    def test_generic_supported_versions(self):
        for major in (18, 19, 20, 21):
            with self.subTest(major=major):
                self.tool(version=f"{major}.1.0")
                self.probe(True)

    def test_versioned_llvm20_without_llvm18(self):
        self.tool(name="llvm-config-20")
        self.probe(True)

    def test_legacy_cli_alias(self):
        self.tool(version="20.1.8")
        self.probe(True, option="--have-llvm18")

    def test_unsupported_versions(self):
        for version in ("17.0.0", "22.0.0", "invalid"):
            with self.subTest(version=version):
                self.tool(version=version)
                self.probe(False)

    def test_broken_versioned_tool(self):
        self.tool(name="llvm-config-18", status=1)
        self.probe(False)

    def test_missing_development_libraries(self):
        self.tool(library_status=1)
        self.probe(False)

    def test_explicit_configuration(self):
        self.tool(version="22.0.0")
        self.environment["LLVM_CONFIG"] = str(self.tool(name="chosen-llvm"))
        self.probe(True)

    def test_invalid_override_does_not_fall_back(self):
        self.tool(name="llvm-config-20")
        self.environment["LLVM_CONFIG"] = str(
            self.tool(name="chosen-llvm", version="22.0.0")
        )
        self.probe(False)

    def test_homebrew_llvm20(self):
        prefix = self.directory / "llvm20"
        (prefix / "bin").mkdir(parents=True)
        self.tool().rename(prefix / "bin/llvm-config")
        brew = self.bin / "brew"
        brew.write_text(
            "#!/bin/sh\n"
            '[ "$1" = --prefix ] && [ "$2" = llvm@20 ] || exit 1\n'
            f"printf '%s\\n' {shlex.quote(str(prefix))}\n"
        )
        brew.chmod(0o755)
        self.probe(True)

    def test_missing_llvm(self):
        self.probe(False)


if __name__ == "__main__":
    unittest.main()
