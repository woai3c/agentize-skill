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

        self.assertEqual(report["schema_version"], 4)
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
                "user.name=Agentize Test",
                "-c",
                "user.email=agentize@example.invalid",
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
                self.assertEqual(report["schema_version"], 4)
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
                self.assertEqual(report["schema_version"], 4)
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
