#!/usr/bin/env python3
"""Exercise the NuttX image builder with synthetic Git trees and tools."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
BUILDER = REPO / "tools" / "build-nuttx-image.sh"


def run(command, *, cwd=None, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )


def git(directory, *args):
    return run(["git", "-C", str(directory), *args])


def add_submodule(repository, child, path):
    git(
        repository,
        "-c",
        "protocol.file.allow=always",
        "submodule",
        "add",
        "-q",
        str(child),
        path,
    )
    git(repository, "add", ".gitmodules", path)
    git(repository, "commit", "-qm", f"Add fixture submodule {path}")


def initialize_repository(directory):
    directory.mkdir(parents=True)
    git(directory, "init", "-q")
    git(directory, "config", "user.name", "NuttX builder test")
    git(directory, "config", "user.email", "builder-test@example.invalid")
    (directory / ".gitignore").write_text(
        ".config\nMake.defs\nnuttx\n", encoding="utf-8"
    )
    (directory / "source.txt").write_text(
        "clean pinned source\n", encoding="utf-8"
    )
    git(directory, "add", ".gitignore", "source.txt")
    git(directory, "commit", "-qm", "Create pinned fixture")


class NuttxBuilderFixture:
    def __init__(self, root):
        self.root = root
        self.nuttx = root / "nuttx"
        self.apps = root / "nuttx-apps"
        self.output = root / "output"
        self.bin = root / "bin"
        self.call_log = root / "calls.log"
        root.mkdir(parents=True, exist_ok=True)
        initialize_repository(self.nuttx)
        initialize_repository(self.apps)
        self._create_nuttx_layout()
        git(self.nuttx, "add", "boards", "tools")
        git(self.nuttx, "commit", "-qm", "Add fixture build tools")
        self._create_stub_tools()

    @staticmethod
    def head(directory):
        return git(directory, "rev-parse", "HEAD").stdout.strip()

    def _create_nuttx_layout(self):
        board = self.nuttx / "boards/risc-v/qemu-rv/rv-virt"
        (board / "configs").mkdir(parents=True)
        (board / "scripts").mkdir()
        (board / "scripts/Make.defs").write_text("fixture\n", encoding="utf-8")
        tools = self.nuttx / "tools"
        tools.mkdir()
        process_config = tools / "process_config.sh"
        process_config.write_text(
            "#!/bin/sh\n"
            "printf 'process_config\\n' >> \"$CALL_LOG\"\n"
            'while [ "$#" -gt 0 ]; do\n'
            '  if [ "$1" = -o ]; then shift; output=$1; fi\n'
            "  shift\n"
            "done\n"
            "printf 'CONFIG_FIXTURE=y\\n' > \"$output\"\n",
            encoding="utf-8",
        )
        process_config.chmod(0o755)
        configure = tools / "configure.sh"
        configure.write_text(
            "#!/bin/sh\n"
            "printf 'configure\\n' >> \"$CALL_LOG\"\n"
            'if [ -e "$NUTTX_APPS_DIR/ignored-source.c" ]; then\n'
            "  echo 'ignored apps source reached configure' >&2\n"
            "  exit 21\n"
            "fi\n"
            "printf 'CONFIG_FIXTURE=y\\n' > \"$NUTTX_DIR/.config\"\n",
            encoding="utf-8",
        )
        configure.chmod(0o755)

    def _create_stub_tools(self):
        self.bin.mkdir()
        make = self.bin / "make"
        make.write_text(
            "#!/bin/sh\n"
            'printf \'make %s\\n\' "$*" >> "$CALL_LOG"\n'
            "directory=.\n"
            'while [ "$#" -gt 0 ]; do\n'
            '  if [ "$1" = -C ]; then shift; directory=$1; fi\n'
            '  if [ "$1" = distclean ]; then exit 0; fi\n'
            "  shift\n"
            "done\n"
            'if [ -e "$directory/ignored-source.c" ]; then\n'
            "  echo 'ignored NuttX source reached build' >&2\n"
            "  exit 22\n"
            "fi\n"
            'cat "$directory/source.txt" > "$directory/nuttx"\n'
            'for source in "$directory/vendor/source.txt" \\\n'
            '    "$directory/vendor/nested/source.txt"; do\n'
            '  [ ! -f "$source" ] || cat "$source" >> "$directory/nuttx"\n'
            "done\n",
            encoding="utf-8",
        )
        make.chmod(0o755)
        gcc = self.bin / "riscv-none-elf-gcc"
        gcc.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        gcc.chmod(0o755)
        objcopy = self.bin / "riscv-none-elf-objcopy"
        objcopy.write_text(
            "#!/bin/sh\n"
            "printf 'objcopy\\n' >> \"$CALL_LOG\"\n"
            'cp "$3" "$4"\n',
            encoding="utf-8",
        )
        objcopy.chmod(0o755)
        mktemp = self.bin / "mktemp"
        mktemp.write_text(
            "#!/bin/sh\n"
            'if [ -n "${TEST_FIXED_MKTEMP_DIR:-}" ]; then\n'
            '  mkdir -p "$TEST_FIXED_MKTEMP_DIR"\n'
            "  printf '%s\\n' \"$TEST_FIXED_MKTEMP_DIR\"\n"
            "else\n"
            '  exec /usr/bin/mktemp "$@"\n'
            "fi\n",
            encoding="utf-8",
        )
        mktemp.chmod(0o755)

    def environment(self):
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{self.bin}:{env.get('PATH', '')}",
                "CALL_LOG": str(self.call_log),
                "NUTTX_DIR": str(self.nuttx),
                "NUTTX_APPS_DIR": str(self.apps),
                "NUTTX_REVISION": self.head(self.nuttx),
                "NUTTX_APPS_REVISION": self.head(self.apps),
                "OUTPUT_DIR": str(self.output),
                "CROSS_COMPILE": "riscv-none-elf-",
                "GIT_ALLOW_PROTOCOL": "file",
            }
        )
        return env

    def execute(self, output_dir=None, env_overrides=None):
        env = self.environment()
        if output_dir is not None:
            env["OUTPUT_DIR"] = str(output_dir)
        if env_overrides is not None:
            env.update(env_overrides)
        return subprocess.run(
            ["bash", str(BUILDER)],
            cwd=REPO,
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )


class BuildNuttxImageTests(unittest.TestCase):
    def new_fixture(self):
        temp_dir = tempfile.TemporaryDirectory(prefix="nuttx-builder-test-")
        self.addCleanup(temp_dir.cleanup)
        return NuttxBuilderFixture(Path(temp_dir.name))

    def make_dirty(self, repository, kind):
        source = repository / "source.txt"
        if kind == "tracked":
            source.write_text("changed tracked source\n", encoding="utf-8")
        elif kind == "staged":
            source.write_text("staged source change\n", encoding="utf-8")
            git(repository, "add", "source.txt")
        elif kind == "untracked":
            (repository / "new-source.c").write_text(
                "untracked source\n", encoding="utf-8"
            )
        else:
            raise AssertionError(f"Unknown dirty state: {kind}")

    def assert_rejected_before_side_effects(
        self, fixture, repository_label, dirty_path
    ):
        fixture.nuttx.joinpath(".config").write_text(
            "existing generated configuration\n", encoding="utf-8"
        )
        fixture.output.mkdir()
        output_marker = fixture.output / "keep-me"
        output_marker.write_text("existing output\n", encoding="utf-8")
        old_config = fixture.nuttx / ".config"
        result = fixture.execute()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(repository_label, result.stderr)
        self.assertIn(dirty_path, result.stderr)
        self.assertFalse(fixture.call_log.exists())
        self.assertEqual(
            output_marker.read_text(encoding="utf-8"), "existing output\n"
        )
        self.assertEqual(
            old_config.read_text(encoding="utf-8"),
            "existing generated configuration\n",
        )

    def test_rejects_tracked_staged_and_untracked_changes_in_both_repositories(
        self,
    ):
        for repo_name in ("nuttx", "nuttx-apps"):
            for kind in ("tracked", "staged", "untracked"):
                with self.subTest(repository=repo_name, state=kind):
                    fixture = self.new_fixture()
                    repository = getattr(
                        fixture,
                        "apps" if repo_name == "nuttx-apps" else repo_name,
                    )
                    self.make_dirty(repository, kind)
                    dirty_path = (
                        "source.txt" if kind != "untracked" else "new-source.c"
                    )
                    self.assert_rejected_before_side_effects(
                        fixture, repo_name, dirty_path
                    )

    def test_rejects_dirty_content_in_initialized_submodules(self):
        for root_name in ("nuttx", "nuttx-apps"):
            for kind in ("tracked", "untracked"):
                with self.subTest(repository=root_name, state=kind):
                    fixture = self.new_fixture()
                    repository = getattr(
                        fixture,
                        "apps" if root_name == "nuttx-apps" else root_name,
                    )
                    child = fixture.root / f"{root_name}-child"
                    initialize_repository(child)
                    add_submodule(repository, child, "vendor")
                    if kind == "tracked":
                        (repository / "vendor/source.txt").write_text(
                            "dirty submodule source\n", encoding="utf-8"
                        )
                    else:
                        (repository / "vendor/new-source.c").write_text(
                            "untracked submodule source\n", encoding="utf-8"
                        )
                    self.assert_rejected_before_side_effects(
                        fixture, root_name, "vendor"
                    )

    def test_builds_from_clean_pinned_nested_submodules(self):
        fixture = self.new_fixture()
        child = fixture.root / "nuttx-child"
        nested = fixture.root / "nested-child"
        initialize_repository(child)
        initialize_repository(nested)
        add_submodule(child, nested, "nested")
        add_submodule(fixture.nuttx, child, "vendor")

        result = fixture.execute()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (fixture.output / "nuttx.bin").read_text(encoding="utf-8"),
            "clean pinned source\nclean pinned source\nclean pinned source\n",
        )
        self.assertEqual(git(fixture.nuttx, "status", "--porcelain").stdout, "")

    def test_rejects_dirty_nested_submodule_contents(self):
        for kind in ("tracked", "untracked"):
            with self.subTest(state=kind):
                fixture = self.new_fixture()
                child = fixture.root / "nuttx-child"
                nested = fixture.root / "nested-child"
                initialize_repository(child)
                initialize_repository(nested)
                add_submodule(child, nested, "nested")
                add_submodule(fixture.nuttx, child, "vendor")
                git(
                    fixture.nuttx,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "update",
                    "--init",
                    "--recursive",
                )
                nested_source = fixture.nuttx / "vendor/nested/source.txt"
                if kind == "tracked":
                    nested_source.write_text(
                        "dirty nested source\n", encoding="utf-8"
                    )
                    dirty_path = "vendor"
                else:
                    (nested_source.parent / "new-source.c").write_text(
                        "untracked nested source\n", encoding="utf-8"
                    )
                    dirty_path = "vendor"
                self.assert_rejected_before_side_effects(
                    fixture, "nuttx", dirty_path
                )

    def test_submodule_failure_preserves_sources_and_existing_output(self):
        fixture = self.new_fixture()
        child = fixture.root / "nuttx-child"
        initialize_repository(child)
        add_submodule(fixture.nuttx, child, "vendor")
        expected_head = fixture.head(fixture.nuttx)
        (fixture.nuttx / ".config").write_text(
            "existing generated configuration\n", encoding="utf-8"
        )
        fixture.output.mkdir()
        output_marker = fixture.output / "keep-me"
        output_marker.write_text("existing output\n", encoding="utf-8")
        child.rename(fixture.root / "unavailable-child")

        result = fixture.execute()

        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Failed to initialize pinned submodules", result.stderr)
        self.assertFalse(fixture.call_log.exists())
        self.assertEqual(
            output_marker.read_text(encoding="utf-8"), "existing output\n"
        )
        self.assertEqual(
            (fixture.nuttx / ".config").read_text(encoding="utf-8"),
            "existing generated configuration\n",
        )
        self.assertEqual(fixture.head(fixture.nuttx), expected_head)
        self.assertEqual(git(fixture.nuttx, "status", "--porcelain").stdout, "")

    def test_output_path_must_not_overlap_source_checkouts(self):
        for source_name in ("nuttx", "nuttx-apps"):
            for direction in ("inside", "ancestor"):
                with self.subTest(source=source_name, direction=direction):
                    fixture = self.new_fixture()
                    source = getattr(
                        fixture,
                        "apps" if source_name == "nuttx-apps" else source_name,
                    )
                    output = (
                        source / "image"
                        if direction == "inside"
                        else fixture.root
                    )

                    result = fixture.execute(output_dir=output)

                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn(
                        "must not overlap source checkout", result.stderr
                    )
                    self.assertFalse(fixture.call_log.exists())
                    self.assertFalse((source / "image").exists())

    def test_output_path_must_not_resolve_inside_temporary_build_tree(self):
        fixture = self.new_fixture()
        build_root = fixture.root / "fixed-build-root"
        result = fixture.execute(
            output_dir=build_root / "image",
            env_overrides={"TEST_FIXED_MKTEMP_DIR": str(build_root)},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("outside the temporary build tree", result.stderr)
        self.assertFalse(build_root.exists())
        self.assertFalse(fixture.call_log.exists())

    def test_excludes_ignored_inputs_and_preserves_generated_outputs(self):
        fixture = self.new_fixture()
        source = fixture.nuttx / "source.txt"
        source.write_text("new clean pinned source\n", encoding="utf-8")
        git(fixture.nuttx, "add", "source.txt")
        git(fixture.nuttx, "commit", "-qm", "Advance fixture revision")
        nuttx_revision = fixture.head(fixture.nuttx)
        apps_revision = fixture.head(fixture.apps)
        branch = git(
            fixture.nuttx, "symbolic-ref", "--short", "HEAD"
        ).stdout.strip()
        git(fixture.nuttx, "checkout", "--detach", "-q")
        git(fixture.nuttx, "branch", "-f", branch, f"{nuttx_revision}^")
        (fixture.nuttx / ".config").write_text(
            "CONFIG_EXISTING=y\n", encoding="utf-8"
        )
        (fixture.nuttx / "Make.defs").write_text(
            "generated\n", encoding="utf-8"
        )
        (fixture.nuttx / ".git/info/exclude").write_text(
            "ignored-source.c\n", encoding="utf-8"
        )
        (fixture.apps / ".git/info/exclude").write_text(
            "ignored-source.c\n", encoding="utf-8"
        )
        (fixture.nuttx / "ignored-source.c").write_text(
            "must not enter the image\n", encoding="utf-8"
        )
        (fixture.apps / "ignored-source.c").write_text(
            "must not enter the apps checkout\n", encoding="utf-8"
        )

        result = fixture.execute()

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        calls = fixture.call_log.read_text(encoding="utf-8")
        self.assertNotIn("distclean", calls)
        metadata = json.loads((fixture.output / "metadata.json").read_text())
        self.assertEqual(
            metadata, {"nuttx": nuttx_revision, "nuttx_apps": apps_revision}
        )
        self.assertEqual(
            (fixture.output / "nuttx.bin").read_text(encoding="utf-8"),
            "new clean pinned source\n",
        )
        self.assertEqual(
            (fixture.nuttx / ".config").read_text(encoding="utf-8"),
            "CONFIG_EXISTING=y\n",
        )
        self.assertEqual(
            (fixture.nuttx / "Make.defs").read_text(encoding="utf-8"),
            "generated\n",
        )
        self.assertEqual(git(fixture.nuttx, "status", "--porcelain").stdout, "")


if __name__ == "__main__":
    unittest.main(verbosity=2)
