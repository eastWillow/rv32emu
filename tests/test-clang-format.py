#!/usr/bin/env python3
"""Exercise the real formatter on the instruction macro and enabled code."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FORMATTER = os.environ.get("CLANG_FORMAT", "clang-format-20")


@unittest.skipUnless(shutil.which(FORMATTER), f"{FORMATTER} is unavailable")
class FormatTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.header = Path(self.temp.name) / "decode.h"
        self.original = (ROOT / "src/decode.h").read_text()
        self.header.write_text(self.original)
        shutil.copy(ROOT / ".clang-format", self.header.parent)

    def run_formatter(self, mode):
        return subprocess.run(
            [
                sys.executable,
                str(ROOT / "tools/clang-format.py"),
                "--formatter",
                FORMATTER,
                mode,
                str(self.header),
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )

    def test_large_disabled_macro_finishes(self):
        result = self.run_formatter("--check")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_enabled_code_is_still_checked(self):
        self.header.write_text(
            self.original + "int format_probe(){return 1;}\n"
        )
        result = self.run_formatter("--check")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("code should be clang-formatted", result.stderr)

    def test_in_place_preserves_disabled_macro(self):
        self.header.write_text(
            self.original + "int format_probe(){return 1;}\n"
        )
        result = self.run_formatter("--in-place")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.header.read_text().startswith(self.original))
        self.assertEqual(self.run_formatter("--check").returncode, 0)


if __name__ == "__main__":
    unittest.main()
