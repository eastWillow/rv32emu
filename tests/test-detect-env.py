"""Exercise LLVM discovery through the same CLI that Kconfig and make use."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


DETECT_ENV = Path(__file__).resolve().parents[1] / "tools" / "detect-env.py"


class LLVMDetectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.bin_dir = Path(self.tmp.name)
        self.env = {**os.environ, "PATH": str(self.bin_dir)}
        self.env.pop("LLVM_CONFIG", None)

    def tool(self, name, version, libs_status=0):
        path = self.bin_dir / name
        path.write_text(
            "#!/bin/sh\n"
            'case "$1" in\n'
            f"  --version) printf '%s\\n' '{version}' ;;\n"
            f"  --libs) printf '%s\\n' '-lLLVM'; exit {libs_status} ;;\n"
            "  *) exit 1 ;;\n"
            "esac\n"
        )
        path.chmod(0o755)
        return path

    def query(self, option):
        return subprocess.run(
            [sys.executable, str(DETECT_ENV), option],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_supported_versioned_tools(self):
        for major in range(18, 22):
            with self.subTest(major=major):
                tool = self.tool(f"llvm-config-{major}", f"{major}.1.0")
                self.assertEqual(self.query("--have-llvm").returncode, 0)
                self.assertEqual(
                    self.query("--llvm-config").stdout.strip(), str(tool)
                )
                tool.unlink()

    def test_supported_unversioned_tools(self):
        for major in range(18, 22):
            with self.subTest(major=major):
                self.tool("llvm-config", f"{major}.1.0")
                self.assertEqual(self.query("--have-llvm").returncode, 0)

    def test_missing_unsupported_and_invalid_tools(self):
        self.assertNotEqual(self.query("--have-llvm").returncode, 0)
        self.assertEqual(self.query("--llvm-config").stdout, "")
        for version in ("17.0.0", "22.0.0", "not a version"):
            with self.subTest(version=version):
                self.tool("llvm-config", version)
                self.assertNotEqual(self.query("--have-llvm").returncode, 0)
                self.assertEqual(self.query("--llvm-config").stdout, "")

    def test_falls_back_from_unusable_newer_tool(self):
        self.tool("llvm-config-21", "21.1.0", libs_status=1)
        expected = self.tool("llvm-config-20", "20.1.0")
        self.assertEqual(self.query("--have-llvm").returncode, 0)
        self.assertEqual(
            self.query("--llvm-config").stdout.strip(), str(expected)
        )

    def test_explicit_override_is_respected(self):
        self.tool("llvm-config-21", "21.1.0")
        expected = self.tool("custom-llvm-config", "20.1.0")
        self.env["LLVM_CONFIG"] = str(expected)
        self.assertEqual(
            self.query("--llvm-config").stdout.strip(), str(expected)
        )
        self.tool("custom-llvm-config", "20.1.0", libs_status=1)
        self.assertNotEqual(self.query("--have-llvm").returncode, 0)
        self.assertEqual(self.query("--llvm-config").stdout, "")

    def test_homebrew_versioned_install(self):
        prefix = self.bin_dir / "llvm@20"
        (prefix / "bin").mkdir(parents=True)
        expected = self.tool("llvm-config-brew", "20.1.0")
        expected = expected.rename(prefix / "bin" / "llvm-config")
        brew = self.bin_dir / "brew"
        brew.write_text(
            "#!/bin/sh\n"
            'if [ "$1" = --prefix ] && [ "$2" = llvm@20 ]; then\n'
            f"  printf '%s\\n' '{prefix}'\n"
            "else\n"
            "  exit 1\n"
            "fi\n"
        )
        brew.chmod(0o755)
        self.assertEqual(self.query("--have-llvm").returncode, 0)
        self.assertEqual(
            self.query("--llvm-config").stdout.strip(), str(expected)
        )

    def test_legacy_query_alias(self):
        self.tool("llvm-config-20", "20.1.0")
        self.assertEqual(self.query("--have-llvm18").returncode, 0)


if __name__ == "__main__":
    unittest.main()
