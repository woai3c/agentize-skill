#!/usr/bin/env python3
"""Produce a bounded, read-only inventory of an agent workflow in a repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    tomllib = None


SCHEMA_VERSION = 1
DEFAULT_MAX_FILES = 50_000
MAX_REPORTED_PATHS = 200

IGNORED_DIRECTORIES = {
    ".git",
    ".hg",
    ".svn",
    ".cache",
    ".mypy_cache",
    ".next",
    ".nuxt",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".turbo",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "out",
    "target",
    "venv",
}

VENDORED_DIRECTORIES = {"third_party", "vendor"}

INSTRUCTION_FILES = {
    "AGENTS.md": "shared",
    "CLAUDE.md": "claude",
    "GEMINI.md": "gemini",
    ".cursorrules": "cursor",
    ".windsurfrules": "windsurf",
    "copilot-instructions.md": "copilot",
}

MANIFEST_NAMES = {
    "Cargo.toml",
    "Gemfile",
    "Package.swift",
    "build.gradle",
    "build.gradle.kts",
    "composer.json",
    "deno.json",
    "deno.jsonc",
    "go.mod",
    "mix.exs",
    "package.json",
    "pom.xml",
    "pyproject.toml",
    "requirements.txt",
}

LOCKFILE_NAMES = {
    "Cargo.lock",
    "bun.lock",
    "bun.lockb",
    "composer.lock",
    "deno.lock",
    "Gemfile.lock",
    "go.sum",
    "package-lock.json",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}

TASK_RUNNER_NAMES = {
    "GNUmakefile",
    "Justfile",
    "Makefile",
    "Taskfile.yaml",
    "Taskfile.yml",
    "justfile",
}

QUALITY_CONFIG_NAMES = {
    ".editorconfig",
    ".markdownlint-cli2.yaml",
    ".pre-commit-config.yaml",
    ".prettierrc",
    ".prettierrc.json",
    ".prettierrc.yaml",
    ".prettierrc.yml",
    ".yamllint.yaml",
    ".yamllint.yml",
    "biome.json",
    "eslint.config.js",
    "eslint.config.mjs",
    "lefthook.yml",
    "mypy.ini",
    "pytest.ini",
    "ruff.toml",
    "tox.ini",
    "tsconfig.json",
}

AGENT_CONFIG_NAMES = {
    ".mcp.json",
    "config.toml",
    "config.yaml",
    "config.yml",
    "hooks.json",
    "requirements.toml",
    "settings.json",
    "settings.local.json",
}

DOC_BASENAMES = {
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "DEVELOPMENT.md",
    "README.md",
    "SECURITY.md",
}

HIGH_SIGNAL_DOC_WORDS = {
    "adr",
    "architecture",
    "decisions",
    "design",
    "development",
    "domain",
    "glossary",
    "invariants",
    "operations",
    "runbook",
    "testing",
}

TEST_DIRECTORY_NAMES = {
    "e2e",
    "integration-tests",
    "integration_tests",
    "spec",
    "specs",
    "test",
    "tests",
}

LANGUAGE_EXTENSIONS = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".go": "Go",
    ".h": "C/C++ Header",
    ".hpp": "C++ Header",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".lua": "Lua",
    ".md": "Markdown",
    ".php": "PHP",
    ".ps1": "PowerShell",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
}

VERIFICATION_NAME = re.compile(
    r"(?:^|[-_:])(test|check|lint|format|fmt|typecheck|type-check|build|verify|ci|e2e|smoke)(?:$|[-_:])",
    re.IGNORECASE,
)
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MAKE_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?![=])")
JUST_TARGET = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)(?:\s+[^:=]+)?\s*:(?![=])")


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def capped(values: Iterable[str], limit: int = MAX_REPORTED_PATHS) -> list[str]:
    return sorted(set(values))[:limit]


def walk_repository(
    root: Path, max_files: int, include_vendored: bool
) -> tuple[list[Path], list[str], list[str], bool]:
    files: list[Path] = []
    skipped: set[str] = set()
    errors: list[str] = []
    truncated = False

    def on_error(error: OSError) -> None:
        target = getattr(error, "filename", None) or "unknown path"
        errors.append(f"Unable to scan {target}: {error.strerror or error}")

    for current, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False, onerror=on_error
    ):
        current_path = Path(current)
        kept_directories: list[str] = []
        for directory_name in sorted(directory_names, key=str.casefold):
            folded = directory_name.casefold()
            is_vendored = folded in VENDORED_DIRECTORIES
            if folded in IGNORED_DIRECTORIES or (is_vendored and not include_vendored):
                skipped.add(relative_path(current_path / directory_name, root))
                continue
            kept_directories.append(directory_name)
        directory_names[:] = kept_directories

        for file_name in sorted(file_names, key=str.casefold):
            files.append(current_path / file_name)
            if len(files) >= max_files:
                truncated = True
                break
        if truncated:
            break

    return files, sorted(skipped), errors, truncated


def is_ci_path(relative: str) -> bool:
    lowered = relative.casefold()
    name = Path(relative).name.casefold()
    return (
        lowered.startswith(".github/workflows/")
        or lowered.startswith(".circleci/")
        or lowered.startswith(".buildkite/")
        or name
        in {
            ".gitlab-ci.yml",
            "azure-pipelines.yml",
            "bitbucket-pipelines.yml",
            "jenkinsfile",
        }
    )


def is_test_path(relative: str) -> bool:
    path = Path(relative)
    parts = {part.casefold() for part in path.parts[:-1]}
    name = path.name.casefold()
    return bool(parts & TEST_DIRECTORY_NAMES) or bool(
        re.search(r"(?:^|[._-])(test|spec)(?:[._-]|$)", name)
    )


def is_high_signal_doc(relative: str) -> bool:
    path = Path(relative)
    if path.suffix.casefold() not in {".md", ".mdx", ".rst"}:
        return False
    if path.name in DOC_BASENAMES:
        return True
    parts = {part.casefold() for part in path.parts}
    stem_words = set(re.split(r"[-_.]", path.stem.casefold()))
    return "docs" in parts and bool((parts | stem_words) & HIGH_SIGNAL_DOC_WORDS)


def instruction_kind(relative: str) -> str | None:
    path = Path(relative)
    if path.name in INSTRUCTION_FILES:
        if path.name == "copilot-instructions.md" and ".github" not in path.parts:
            return None
        return INSTRUCTION_FILES[path.name]
    if path.suffix.casefold() == ".mdc" and tuple(part.casefold() for part in path.parts[:2]) == (
        ".cursor",
        "rules",
    ):
        return "cursor"
    return None


def is_skill_path(relative: str) -> bool:
    path = Path(relative)
    return path.name == "SKILL.md" and "skills" in {
        part.casefold() for part in path.parts[:-1]
    }


def is_agent_config(relative: str) -> bool:
    path = Path(relative)
    if not path.parts:
        return False
    first = path.parts[0].casefold()
    return first in {".agents", ".claude", ".codex", ".cursor", ".gemini", ".kimi"} and (
        path.name in AGENT_CONFIG_NAMES or path.suffix.casefold() in {".rules", ".toml"}
    )


def read_text(path: Path, max_bytes: int = 1_000_000) -> tuple[str | None, str | None]:
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return None, f"Skipped {path.name}: file is larger than {max_bytes} bytes"
        return path.read_text(encoding="utf-8-sig", errors="replace"), None
    except OSError as error:
        return None, f"Unable to read {path}: {error}"


def extract_markdown_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    target = unquote(target).strip()
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target) or target.startswith("//"):
        return None
    return target.split("#", 1)[0].split("?", 1)[0]


def summarize_instruction(path: Path, root: Path, kind: str) -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    try:
        size = path.lstat().st_size
    except OSError:
        size = -1
    text, warning = read_text(path, max_bytes=512_000)
    if warning:
        warnings.append(warning)
    headings: list[str] = []
    broken_links: list[str] = []
    outside_links: list[str] = []
    line_count = 0

    if text is not None:
        line_count = len(text.splitlines())
        for line in text.splitlines():
            match = HEADING.match(line)
            if match and len(headings) < 50:
                headings.append(match.group(2).strip())
        for match in list(MARKDOWN_LINK.finditer(text))[:100]:
            target = extract_markdown_target(match.group(1))
            if not target:
                continue
            candidate = (path.parent / target).resolve(strict=False)
            try:
                candidate.relative_to(root)
            except ValueError:
                outside_links.append(target)
                continue
            if not candidate.exists():
                broken_links.append(target)

    return (
        {
            "path": relative_path(path, root),
            "kind": kind,
            "bytes": size,
            "lines": line_count,
            "symlink": path.is_symlink(),
            "headings": headings,
            "broken_relative_links": sorted(set(broken_links))[:20],
            "relative_links_outside_repository": sorted(set(outside_links))[:20],
        },
        warnings,
    )


def parse_package_scripts(path: Path, root: Path) -> tuple[dict[str, Any] | None, str | None]:
    text, warning = read_text(path, max_bytes=2_000_000)
    if warning:
        return None, warning
    try:
        data = json.loads(text or "{}")
    except json.JSONDecodeError as error:
        return None, f"Unable to parse {relative_path(path, root)}: {error}"
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return None, None
    clean_scripts = {
        str(name): str(command)
        for name, command in scripts.items()
        if isinstance(name, str) and isinstance(command, str)
    }
    return {
        "source": relative_path(path, root),
        "package_manager": detect_package_manager(path.parent),
        "scripts": dict(sorted(clean_scripts.items()))[:100],
    }, None


def detect_package_manager(directory: Path) -> str | None:
    for name, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lock", "bun"),
        ("bun.lockb", "bun"),
        ("package-lock.json", "npm"),
    ):
        if (directory / name).exists():
            return manager
    return None


def parse_task_targets(path: Path, root: Path) -> tuple[dict[str, Any] | None, str | None]:
    text, warning = read_text(path)
    if warning:
        return None, warning
    pattern = JUST_TARGET if path.name.casefold() == "justfile" else MAKE_TARGET
    targets: set[str] = set()
    for line in (text or "").splitlines():
        if line.startswith((" ", "\t", "#")):
            continue
        match = pattern.match(line)
        if match and not match.group(1).startswith("."):
            targets.add(match.group(1))
    if not targets:
        return None, None
    return {
        "source": relative_path(path, root),
        "runner": "just" if path.name.casefold() == "justfile" else "make",
        "targets": sorted(targets)[:200],
    }, None


def parse_python_scripts(path: Path, root: Path) -> tuple[dict[str, Any] | None, str | None]:
    if tomllib is None:
        return None, "Python is too old to parse pyproject.toml without a dependency"
    try:
        with path.open("rb") as stream:
            data = tomllib.load(stream)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return None, f"Unable to parse {relative_path(path, root)}: {error}"
    scripts = data.get("project", {}).get("scripts", {})
    if not isinstance(scripts, dict) or not scripts:
        return None, None
    return {
        "source": relative_path(path, root),
        "scripts": {
            str(name): str(command)
            for name, command in sorted(scripts.items())
            if isinstance(name, str) and isinstance(command, str)
        },
    }, None


def git_metadata(root: Path) -> dict[str, Any]:
    def run(*arguments: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                ["git", "-C", str(root), *arguments],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as error:
            return subprocess.CompletedProcess([], 1, "", str(error))

    top_level = run("rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        return {"is_repository": False}

    git_root = Path(top_level.stdout.strip()).resolve()
    branch_result = run("symbolic-ref", "--quiet", "--short", "HEAD")
    if branch_result.returncode != 0:
        branch_result = run("rev-parse", "--short", "HEAD")
    status_result = run("status", "--porcelain=v1", "--untracked-files=normal")
    status_lines = status_result.stdout.splitlines() if status_result.returncode == 0 else []
    dirty_paths: list[str] = []
    for line in status_lines[:100]:
        path_text = line[3:] if len(line) > 3 else line
        if " -> " in path_text:
            path_text = path_text.split(" -> ", 1)[1]
        dirty_paths.append(path_text.strip('"'))

    return {
        "is_repository": True,
        "root": str(git_root),
        "target_matches_git_root": git_root == root,
        "branch_or_commit": branch_result.stdout.strip() or None,
        "dirty_path_count": len(status_lines),
        "dirty_paths": dirty_paths,
        "dirty_paths_truncated": len(status_lines) > len(dirty_paths),
    }


def ecosystems_for(paths: list[str]) -> list[str]:
    names = {Path(path).name for path in paths}
    ecosystems: set[str] = set()
    rules = {
        "Node.js": {"package.json"},
        "Python": {"pyproject.toml", "requirements.txt"},
        "Rust": {"Cargo.toml"},
        "Go": {"go.mod"},
        "Java/JVM": {"pom.xml", "build.gradle", "build.gradle.kts"},
        "Ruby": {"Gemfile"},
        "PHP": {"composer.json"},
        "Elixir": {"mix.exs"},
        "Swift": {"Package.swift"},
        "Deno": {"deno.json", "deno.jsonc"},
    }
    for ecosystem, markers in rules.items():
        if names & markers:
            ecosystems.add(ecosystem)
    return sorted(ecosystems)


def build_report(root: Path, max_files: int, include_vendored: bool) -> dict[str, Any]:
    files, skipped, warnings, truncated = walk_repository(root, max_files, include_vendored)
    relatives = [relative_path(path, root) for path in files]
    language_counts = Counter(
        language
        for path in files
        if (language := LANGUAGE_EXTENSIONS.get(path.suffix.casefold())) is not None
    )

    manifests = capped(
        relative for relative in relatives if Path(relative).name in MANIFEST_NAMES
    )
    lockfiles = capped(
        relative for relative in relatives if Path(relative).name in LOCKFILE_NAMES
    )
    task_runners = capped(
        relative for relative in relatives if Path(relative).name in TASK_RUNNER_NAMES
    )
    ci_files = capped(relative for relative in relatives if is_ci_path(relative))
    quality_configs = capped(
        relative
        for relative in relatives
        if Path(relative).name in QUALITY_CONFIG_NAMES
    )
    docs = capped(relative for relative in relatives if is_high_signal_doc(relative))
    test_paths = capped(relative for relative in relatives if is_test_path(relative))
    skills = capped(relative for relative in relatives if is_skill_path(relative))
    agent_configs = capped(relative for relative in relatives if is_agent_config(relative))

    instruction_summaries: list[dict[str, Any]] = []
    for path, relative in zip(files, relatives):
        kind = instruction_kind(relative)
        if kind is None:
            continue
        summary, summary_warnings = summarize_instruction(path, root, kind)
        instruction_summaries.append(summary)
        warnings.extend(summary_warnings)
    instruction_summaries.sort(key=lambda item: item["path"])

    package_scripts: list[dict[str, Any]] = []
    python_scripts: list[dict[str, Any]] = []
    task_targets: list[dict[str, Any]] = []
    path_by_relative = dict(zip(relatives, files))
    for relative in manifests:
        path = path_by_relative[relative]
        if path.name == "package.json" and len(package_scripts) < 50:
            parsed, warning = parse_package_scripts(path, root)
            if parsed:
                package_scripts.append(parsed)
            if warning:
                warnings.append(warning)
        elif path.name == "pyproject.toml" and len(python_scripts) < 50:
            parsed, warning = parse_python_scripts(path, root)
            if parsed:
                python_scripts.append(parsed)
            if warning:
                warnings.append(warning)
    for relative in task_runners[:50]:
        parsed, warning = parse_task_targets(path_by_relative[relative], root)
        if parsed:
            task_targets.append(parsed)
        if warning:
            warnings.append(warning)

    verification_commands: list[dict[str, str]] = []
    for package in package_scripts:
        for name, command in package["scripts"].items():
            if VERIFICATION_NAME.search(name):
                verification_commands.append(
                    {"source": package["source"], "name": name, "definition": command}
                )
    for runner in task_targets:
        for target in runner["targets"]:
            if VERIFICATION_NAME.search(target):
                verification_commands.append(
                    {"source": runner["source"], "name": target, "definition": runner["runner"]}
                )
    verification_commands = verification_commands[:250]

    root_instructions = [
        item for item in instruction_summaries if "/" not in item["path"]
    ]
    broken_link_count = sum(
        len(item["broken_relative_links"]) for item in instruction_summaries
    )
    diagnostics: list[str] = []
    if not files:
        diagnostics.append("empty_repository")
    if not instruction_summaries:
        diagnostics.append("no_agent_instruction_surface_detected")
    elif not any(item["kind"] == "shared" for item in root_instructions):
        diagnostics.append("provider_specific_root_instructions_only")
    if len(root_instructions) > 1:
        diagnostics.append("multiple_root_instruction_surfaces_require_reconciliation")
    if any(item["bytes"] > 32_000 for item in root_instructions):
        diagnostics.append("large_root_instruction_file_may_need_routing")
    if broken_link_count:
        diagnostics.append("broken_relative_links_in_agent_instructions")
    if not verification_commands:
        diagnostics.append("no_declared_verification_command_detected")
    if not ci_files:
        diagnostics.append("no_ci_configuration_detected")
    if len(files) >= 100 and not any(
        HIGH_SIGNAL_DOC_WORDS & set(re.split(r"[-_.]", Path(path).stem.casefold()))
        for path in docs
    ):
        diagnostics.append("no_high_signal_architecture_or_testing_doc_detected")
    if truncated:
        diagnostics.append("scan_truncated_at_file_limit")

    top_level = []
    try:
        top_level = sorted((entry.name for entry in root.iterdir()), key=str.casefold)[:200]
    except OSError as error:
        warnings.append(f"Unable to list repository root: {error}")

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "scan": {
            "files_seen": len(files),
            "max_files": max_files,
            "truncated": truncated,
            "include_vendored": include_vendored,
            "skipped_directories": skipped[:MAX_REPORTED_PATHS],
            "warnings": sorted(set(warnings))[:100],
        },
        "version_control": git_metadata(root),
        "project": {
            "top_level_entries": top_level,
            "ecosystems": ecosystems_for(manifests),
            "languages": [
                {"name": name, "files": count}
                for name, count in language_counts.most_common(20)
            ],
            "manifests": manifests,
            "lockfiles": lockfiles,
            "task_runners": task_runners,
        },
        "agent_surface": {
            "instructions": instruction_summaries,
            "skills": skills,
            "config": agent_configs,
        },
        "documentation": {"high_signal_files": docs},
        "automation": {
            "ci_files": ci_files,
            "quality_configs": quality_configs,
        },
        "verification": {
            "test_paths": test_paths,
            "package_scripts": package_scripts,
            "python_entrypoints": python_scripts,
            "task_targets": task_targets,
            "declared_commands": verification_commands,
        },
        "diagnostic_hints": diagnostics,
    }


def render_markdown(report: dict[str, Any]) -> str:
    project = report["project"]
    agent_surface = report["agent_surface"]
    verification = report["verification"]
    lines = [
        "# Agentize repository inventory",
        "",
        f"- Root: `{report['root']}`",
        f"- Files scanned: {report['scan']['files_seen']}",
        f"- Ecosystems: {', '.join(project['ecosystems']) or 'none detected'}",
        f"- Git repository: {report['version_control'].get('is_repository', False)}",
        "",
        "## Agent surfaces",
        "",
    ]
    if agent_surface["instructions"]:
        for instruction in agent_surface["instructions"]:
            details = f"{instruction['lines']} lines, {instruction['kind']}"
            if instruction["broken_relative_links"]:
                details += f", {len(instruction['broken_relative_links'])} broken link(s)"
            lines.append(f"- `{instruction['path']}` ({details})")
    else:
        lines.append("- No recognized instruction file detected.")

    lines.extend(["", "## Verification signals", ""])
    if verification["declared_commands"]:
        for command in verification["declared_commands"][:40]:
            lines.append(
                f"- `{command['name']}` from `{command['source']}`: "
                f"`{command['definition']}`"
            )
    else:
        lines.append("- No declared verification command detected.")

    lines.extend(["", "## Other evidence", ""])
    lines.append(
        f"- Skills: {len(agent_surface['skills'])}; CI files: "
        f"{len(report['automation']['ci_files'])}; test paths: "
        f"{len(verification['test_paths'])}"
    )
    lines.append(
        f"- High-signal docs: {', '.join(report['documentation']['high_signal_files'][:20]) or 'none'}"
    )

    lines.extend(["", "## Diagnostic hints", ""])
    if report["diagnostic_hints"]:
        lines.extend(f"- `{hint}`" for hint in report["diagnostic_hints"])
    else:
        lines.append("- No automatic hints. Human assessment is still required.")

    if report["scan"]["warnings"]:
        lines.extend(["", "## Scanner warnings", ""])
        lines.extend(f"- {warning}" for warning in report["scan"]["warnings"])
    return "\n".join(lines) + "\n"


def parse_arguments(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a repository and report coding-agent workflow signals."
    )
    parser.add_argument("--root", default=".", help="Repository root to inspect.")
    parser.add_argument(
        "--format", choices=("json", "markdown"), default="json", help="Output format."
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=DEFAULT_MAX_FILES,
        help=f"Stop after this many files (default: {DEFAULT_MAX_FILES}).",
    )
    parser.add_argument(
        "--include-vendored",
        action="store_true",
        help="Include vendor and third_party directories in the bounded scan.",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    options = parse_arguments(arguments if arguments is not None else sys.argv[1:])
    if options.max_files < 1:
        print("--max-files must be positive", file=sys.stderr)
        return 2
    root = Path(options.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Repository root is not a directory: {root}", file=sys.stderr)
        return 2
    report = build_report(root, options.max_files, options.include_vendored)
    if options.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
