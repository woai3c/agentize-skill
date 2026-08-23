from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCANNER = REPOSITORY_ROOT / "scripts" / "scan_repo.py"


def write(root: Path, relative: str, content: str = "") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def scan(root: Path, *extra: str) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--format", "json", *extra],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"scanner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return json.loads(result.stdout)


class ScanRepositoryTests(unittest.TestCase):
    def test_empty_repository_reports_missing_spine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = scan(Path(temporary))

        self.assertEqual(report["scan"]["files_seen"], 0)
        self.assertIn("empty_repository", report["diagnostic_hints"])
        self.assertIn(
            "no_agent_instruction_surface_detected", report["diagnostic_hints"]
        )
        self.assertIn("no_declared_verification_command_detected", report["diagnostic_hints"])

    def test_partial_node_repository_keeps_provider_surface_and_commands_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root,
                "package.json",
                json.dumps(
                    {
                        "name": "partial-project",
                        "scripts": {
                            "test:unit": "vitest run",
                            "typecheck": "tsc --noEmit",
                            "start": "node src/index.js",
                        },
                    }
                ),
            )
            write(root, "package-lock.json", "{}")
            write(root, "CLAUDE.md", "# Project rules\n\nRun the focused tests.\n")
            write(root, "docs/architecture.md", "# Architecture\n")
            write(root, "src/index.ts", "export const value = 1;\n")
            write(root, "tests/index.test.ts", "// representative test\n")

            report = scan(root)

        self.assertEqual(report["project"]["ecosystems"], ["Node.js"])
        self.assertEqual(report["agent_surface"]["instructions"][0]["kind"], "claude")
        self.assertIn("provider_specific_root_instructions_only", report["diagnostic_hints"])
        command_names = {
            command["name"] for command in report["verification"]["declared_commands"]
        }
        self.assertEqual(command_names, {"test:unit", "typecheck"})
        self.assertNotIn(
            "no_declared_verification_command_detected", report["diagnostic_hints"]
        )

    def test_multiple_instruction_surfaces_and_broken_links_are_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "AGENTS.md", "# Shared rules\n\nSee [missing](docs/missing.md).\n")
            write(root, "GEMINI.md", "# Gemini rules\n")
            write(
                root,
                ".agents/skills/example/SKILL.md",
                "---\nname: example\ndescription: Example fixture.\n---\n",
            )
            write(root, "Makefile", "test:\n\t@echo ok\n")
            write(root, ".github/workflows/ci.yml", "name: CI\n")

            report = scan(root)

        self.assertIn(
            "multiple_root_instruction_surfaces_require_reconciliation",
            report["diagnostic_hints"],
        )
        self.assertIn(
            "broken_relative_links_in_agent_instructions", report["diagnostic_hints"]
        )
        self.assertEqual(report["agent_surface"]["skills"], [".agents/skills/example/SKILL.md"])
        self.assertEqual(report["automation"]["ci_files"], [".github/workflows/ci.yml"])
        self.assertEqual(
            report["agent_surface"]["instructions"][0]["broken_relative_links"],
            ["docs/missing.md"],
        )

    def test_file_limit_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(5):
                write(root, f"src/file-{index}.py", "pass\n")

            report = scan(root, "--max-files", "3")

        self.assertTrue(report["scan"]["truncated"])
        self.assertEqual(report["scan"]["files_seen"], 3)
        self.assertIn("scan_truncated_at_file_limit", report["diagnostic_hints"])

    def test_vendored_directories_are_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "src/main.py", "pass\n")
            write(root, "vendor/library.py", "pass\n")

            default_report = scan(root)
            included_report = scan(root, "--include-vendored")

        self.assertEqual(default_report["scan"]["files_seen"], 1)
        self.assertEqual(included_report["scan"]["files_seen"], 2)
        self.assertIn("vendor", default_report["scan"]["skipped_directories"])


if __name__ == "__main__":
    unittest.main()
