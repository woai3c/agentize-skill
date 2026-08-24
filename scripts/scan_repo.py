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


SCHEMA_VERSION = 4
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
    "AGENTS.local.md": "shared",
    "AGENTS.override.md": "shared",
    "CLAUDE.md": "claude",
    "CLAUDE.local.md": "claude",
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
TASKFILE_NAMES = {"taskfile.yaml", "taskfile.yml"}

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
    "openai.yaml",
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
VERIFICATION_COMMAND = re.compile(
    r"(?:\b(?:ava|ctest|e2e|eslint|jest|mocha|mypy|prettier|pytest|ruff|"
    r"shellcheck|tsc|unittest|vitest)\b|\bnode\s+--(?:check|test)\b|"
    r"\bgit\s+diff\s+--check\b|(?:^|[^A-Za-z0-9-])"
    r"(?:build|check|compile|fmt|format|lint|smoke|test|tests|typecheck|"
    r"type-check|validate|verify)"
    r"(?:$|[^A-Za-z0-9]))",
    re.IGNORECASE,
)
COMMAND_START = re.compile(
    r"^(?:(?:[A-Za-z_][A-Za-z0-9_]*=(?:\"[^\"]*\"|'[^']*'|\S+))\s+)*"
    r"(?:env\s+)?(?:\.{0,2}[/\\][^\s]+|bash|bazel|buck2?|bun|bundle|cargo|"
    r"cmake|cmd|composer|deno|docker|dotnet|eslint|git|go|gradle|java|just|"
    r"make|maven|mise|mix|mvnw?|node|nox|npm|npx|nx|php|pnpm|poetry|"
    r"powershell|prettier|pwsh|py|pytest|python(?:3(?:\.\d+)?)?|rake|ruby|"
    r"ruff|shellcheck|sh|swift|task|tox|tsc|turbo|uv|vitest|xcodebuild|yarn|"
    r"zsh)(?:\s|$)",
    re.IGNORECASE,
)
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_-]*)\s*$")
COMMAND_FENCE_LANGUAGES = {
    "",
    "bash",
    "batch",
    "cmd",
    "console",
    "powershell",
    "pwsh",
    "sh",
    "shell",
    "text",
    "txt",
    "zsh",
}
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
MAKE_TARGET = re.compile(r"^([A-Za-z0-9_.-]+)\s*:(?![=])")
JUST_TARGET = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*)(?:\s+[^:=]+)?\s*:(?![=])")
SENSITIVE_NAME = (
    r"(?:[A-Za-z0-9]+[_-])*(?:api[_-]?key|access[_-]?key|access[_-]?token|"
    r"auth[_-]?token|authorization|client[_-]?secret|private[_-]?key|"
    r"refresh[_-]?token|session[_-]?token|pat|token|password|passwd|secret|"
    r"credential)s?(?:[_-][A-Za-z0-9]+)*"
)
SENSITIVE_ASSIGNMENT = re.compile(
    rf"(?i)\b({SENSITIVE_NAME})\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s]+)"
)
SENSITIVE_OPTION = re.compile(
    rf"(?i)(--{SENSITIVE_NAME})(?:\s+)(?:\"[^\"]*\"|'[^']*'|[^\s]+)"
)
BASIC_AUTH_URL = re.compile(
    r"(?i)([A-Za-z][A-Za-z0-9+.-]*://)[^/\s:@]+:[^@\s/]+@"
)
BEARER_CREDENTIAL = re.compile(
    r"(?i)\b(Bearer)\s+(?:\"[^\"]*\"|'[^']*'|[^\s\"']+)"
)


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def portable_name_key(value: str) -> tuple[bytes, bytes]:
    """Sort names identically in the Python and Node.js implementations."""
    folded = value.translate(
        str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    )
    return folded.encode("utf-8"), value.encode("utf-8")


def redact_sensitive_text(value: str) -> str:
    redacted = SENSITIVE_ASSIGNMENT.sub(r"\1=<redacted>", value)
    redacted = SENSITIVE_OPTION.sub(r"\1 <redacted>", redacted)
    redacted = BASIC_AUTH_URL.sub(r"\1<redacted>@", redacted)
    return BEARER_CREDENTIAL.sub(r"\1 <redacted>", redacted)


def documented_verification_commands(text: str) -> list[dict[str, Any]]:
    """Collect conservative command candidates from fenced instruction examples."""
    commands: list[dict[str, Any]] = []
    fence_character: str | None = None
    fence_length = 0
    inspect_fence = False

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if fence_character is None:
            match = FENCE.match(line)
            if not match:
                continue
            marker, language = match.groups()
            fence_character = marker[0]
            fence_length = len(marker)
            inspect_fence = language.casefold() in COMMAND_FENCE_LANGUAGES
            continue

        if stripped.startswith(fence_character * fence_length) and not stripped.lstrip(
            fence_character
        ).strip():
            fence_character = None
            fence_length = 0
            inspect_fence = False
            continue
        if not inspect_fence or len(commands) >= 50:
            continue

        candidate = stripped
        if candidate.startswith(("$ ", "> ")):
            candidate = candidate[2:].lstrip()
        if (
            not candidate
            or candidate.startswith(("#", "//", "- ", "* "))
            or len(candidate) > 1_000
            or not COMMAND_START.search(candidate)
            or not VERIFICATION_COMMAND.search(candidate)
        ):
            continue
        commands.append(
            {
                "line": line_number,
                "definition": redact_sensitive_text(candidate),
            }
        )
    return commands


def capped(values: Iterable[str], limit: int = MAX_REPORTED_PATHS) -> list[str]:
    return sorted(set(values))[:limit]


def walk_repository(
    root: Path, max_files: int, include_vendored: bool
) -> tuple[list[Path], list[str], list[str], list[str], bool]:
    files: list[Path] = []
    skipped: set[str] = set()
    skipped_symlinks: set[str] = set()
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
        for directory_name in sorted(directory_names, key=portable_name_key):
            directory_path = current_path / directory_name
            if directory_path.is_symlink():
                skipped_symlinks.add(relative_path(directory_path, root))
                continue
            folded = directory_name.casefold()
            is_vendored = folded in VENDORED_DIRECTORIES
            if folded in IGNORED_DIRECTORIES or (is_vendored and not include_vendored):
                skipped.add(relative_path(directory_path, root))
                continue
            kept_directories.append(directory_name)
        directory_names[:] = kept_directories

        for file_name in sorted(file_names, key=portable_name_key):
            file_path = current_path / file_name
            if file_path.is_symlink():
                try:
                    file_path.resolve(strict=True).relative_to(root)
                except (OSError, RuntimeError, ValueError):
                    skipped_symlinks.add(relative_path(file_path, root))
                    continue
            if len(files) >= max_files:
                truncated = True
                break
            files.append(file_path)
        if truncated:
            break

    return files, sorted(skipped), sorted(skipped_symlinks), errors, truncated


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
    return path.name == "SKILL.md" and (
        len(path.parts) == 1
        or "skills" in {part.casefold() for part in path.parts[:-1]}
    )


def is_agent_config(relative: str) -> bool:
    path = Path(relative)
    if not path.parts:
        return False
    first = path.parts[0].casefold()
    return first in {
        ".agents",
        ".claude",
        ".codex",
        ".cursor",
        ".gemini",
        ".kimi",
        "agents",
    } and (
        path.name in AGENT_CONFIG_NAMES
        or path.suffix.casefold() in {".rules", ".toml"}
    )


def read_text(
    path: Path, root: Path, max_bytes: int = 1_000_000
) -> tuple[str | None, str | None]:
    try:
        resolved = path.resolve(strict=True)
        try:
            resolved.relative_to(root)
        except ValueError:
            return None, f"Skipped {path.name}: path resolves outside repository"
        size = resolved.stat().st_size
        if size > max_bytes:
            return None, f"Skipped {path.name}: file is larger than {max_bytes} bytes"
        return resolved.read_text(encoding="utf-8-sig", errors="replace"), None
    except OSError as error:
        return None, f"Unable to read {path}: {error}"


def extract_markdown_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        target = target[1 : target.index(">")]
    else:
        target = target.split(maxsplit=1)[0]
    try:
        target = unquote(target, errors="strict")
    except UnicodeDecodeError:
        pass
    target = target.strip()
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
    text, warning = read_text(path, root, max_bytes=512_000)
    if warning:
        warnings.append(warning)
    headings: list[str] = []
    broken_links: list[str] = []
    outside_links: list[str] = []
    documented_commands: list[dict[str, Any]] = []
    line_count = 0

    if text is not None:
        line_count = len(text.splitlines())
        documented_commands = documented_verification_commands(text)
        for line in text.splitlines():
            match = HEADING.match(line)
            if match and len(headings) < 50:
                headings.append(redact_sensitive_text(match.group(2).strip()))
        for match in list(MARKDOWN_LINK.finditer(text))[:100]:
            target = extract_markdown_target(match.group(1))
            if not target:
                continue
            try:
                candidate = (path.parent / target).resolve(strict=False)
            except (OSError, RuntimeError):
                broken_links.append(target)
                continue
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
            "documented_verification_commands": documented_commands,
            "broken_relative_links": sorted(set(broken_links))[:20],
            "relative_links_outside_repository": sorted(set(outside_links))[:20],
        },
        warnings,
    )


def parse_package_scripts(
    path: Path, root: Path, scanned_lockfiles: set[str]
) -> tuple[dict[str, Any] | None, str | None]:
    text, warning = read_text(path, root, max_bytes=2_000_000)
    if warning:
        return None, warning

    def reject_nonstandard_constant(value: str) -> None:
        raise ValueError(f"Non-standard JSON constant: {value}")

    try:
        data = json.loads(
            text or "{}", parse_constant=reject_nonstandard_constant
        )
    except (json.JSONDecodeError, ValueError):
        return None, f"Unable to parse {relative_path(path, root)}: invalid JSON"
    if not isinstance(data, dict):
        return None, None
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return None, None
    clean_scripts = {
        str(name): redact_sensitive_text(str(command))
        for name, command in scripts.items()
        if isinstance(name, str) and isinstance(command, str)
    }
    return {
        "source": relative_path(path, root),
        "package_manager": detect_package_manager(
            path.parent, root, scanned_lockfiles
        ),
        "scripts": dict(sorted(clean_scripts.items())[:100]),
    }, None


def detect_package_manager(
    directory: Path, root: Path, scanned_lockfiles: set[str]
) -> str | None:
    for name, manager in (
        ("pnpm-lock.yaml", "pnpm"),
        ("yarn.lock", "yarn"),
        ("bun.lock", "bun"),
        ("bun.lockb", "bun"),
        ("package-lock.json", "npm"),
    ):
        if relative_path(directory / name, root) in scanned_lockfiles:
            return manager
    return None


def parse_taskfile_targets(text: str) -> list[str]:
    targets: set[str] = set()
    in_tasks = False
    target_indent: int | None = None

    for line in text.splitlines():
        stripped = line.strip()
        if not in_tasks:
            if line == line.lstrip() and re.fullmatch(
                r"tasks\s*:\s*(?:#.*)?", line
            ):
                in_tasks = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("\t") or line == line.lstrip():
            break

        indent = len(line) - len(line.lstrip(" "))
        if target_indent is None:
            target_indent = indent
        match = re.match(r"^ +([A-Za-z0-9_.-]+)\s*:", line)
        if not match:
            continue
        if indent == target_indent:
            targets.add(match.group(1))

    return sorted(targets)[:200]


def parse_task_targets(
    path: Path, root: Path
) -> tuple[dict[str, Any] | None, str | None]:
    text, warning = read_text(path, root)
    if warning:
        return None, warning
    name = path.name.casefold()
    if name in TASKFILE_NAMES:
        runner = "task"
        targets = parse_taskfile_targets(text or "")
    else:
        runner = "just" if name == "justfile" else "make"
        pattern = JUST_TARGET if runner == "just" else MAKE_TARGET
        target_set: set[str] = set()
        for line in (text or "").splitlines():
            if line.startswith((" ", "\t", "#")):
                continue
            match = pattern.match(line)
            if match and not match.group(1).startswith("."):
                target_set.add(match.group(1))
        targets = sorted(target_set)[:200]
    if not targets:
        return None, None
    return {
        "source": relative_path(path, root),
        "runner": runner,
        "targets": targets,
    }, None


def strip_toml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if quote == '"':
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quote = None
        elif quote == "'":
            if character == "'":
                quote = None
        elif character in {'"', "'"}:
            quote = character
        elif character == "#":
            return line[:index].strip()
    return line.strip()


def parse_toml_string(raw: str) -> str | None:
    value = raw.strip()
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return None
        return parsed if isinstance(parsed, str) else None
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return None


def parse_toml_key(raw: str) -> str | None:
    key = raw.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]+", key):
        return key
    return parse_toml_string(key)


def parse_python_scripts(path: Path, root: Path) -> tuple[dict[str, Any] | None, str | None]:
    text, warning = read_text(path, root, max_bytes=2_000_000)
    if warning:
        return None, warning

    scripts: dict[str, str] = {}
    in_scripts = False
    saw_scripts = False
    for original_line in (text or "").splitlines():
        line = strip_toml_comment(original_line)
        if not line:
            continue
        table = re.fullmatch(r"\[\s*([^\]]+?)\s*\]", line)
        if table:
            in_scripts = table.group(1).strip() == "project.scripts"
            saw_scripts = saw_scripts or in_scripts
            continue
        if not in_scripts:
            continue
        assignment = re.fullmatch(r"(.+?)\s*=\s*(.+)", line)
        if not assignment:
            return (
                None,
                f"Unable to parse {relative_path(path, root)}: "
                "unsupported project.scripts entry",
            )
        key = parse_toml_key(assignment.group(1))
        value = parse_toml_string(assignment.group(2))
        if key is None or value is None:
            return (
                None,
                f"Unable to parse {relative_path(path, root)}: "
                "unsupported project.scripts entry",
            )
        scripts[key] = redact_sensitive_text(value)

    if not saw_scripts or not scripts:
        return None, None
    return {
        "source": relative_path(path, root),
        "scripts": dict(sorted(scripts.items())),
    }, None


def has_git_marker(root: Path) -> bool:
    current = root
    while True:
        try:
            (current / ".git").lstat()
            return True
        except FileNotFoundError:
            pass
        except OSError:
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def git_metadata(root: Path) -> dict[str, Any]:
    git_environment = {
        key: value
        for key, value in os.environ.items()
        if not key.upper().startswith("GIT_")
    }
    git_environment["GIT_OPTIONAL_LOCKS"] = "0"
    git_environment["GIT_TERMINAL_PROMPT"] = "0"
    git_environment["GIT_PAGER"] = "cat"

    def run(
        *arguments: str,
    ) -> tuple[subprocess.CompletedProcess[str], str | None]:
        try:
            return (
                subprocess.run(
                    [
                        "git",
                        "-c",
                        "core.fsmonitor=false",
                        "-c",
                        "core.untrackedCache=false",
                        "-C",
                        str(root),
                        *arguments,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    env=git_environment,
                    timeout=5,
                    check=False,
                ),
                None,
            )
        except FileNotFoundError as error:
            return (
                subprocess.CompletedProcess([], 127, "", str(error)),
                "git_executable_unavailable",
            )
        except subprocess.TimeoutExpired as error:
            return (
                subprocess.CompletedProcess([], 124, "", str(error)),
                "git_identity_query_timed_out",
            )
        except OSError as error:
            return (
                subprocess.CompletedProcess([], 1, "", str(error)),
                "git_identity_query_failed",
            )

    top_level, identity_failure = run("rev-parse", "--show-toplevel")
    if top_level.returncode != 0:
        if has_git_marker(root):
            return {
                "is_repository": None,
                "repository_state": "unverified",
                "repository_state_reason": (
                    identity_failure or "git_identity_query_failed"
                ),
                "worktree_state": "unverified",
                "worktree_state_reason": "repository_identity_unverified",
                "dirty_path_count": None,
                "dirty_paths": [],
                "dirty_paths_truncated": None,
            }
        return {
            "is_repository": False,
            "repository_state": "not_repository",
            "worktree_state": "not_applicable",
            "dirty_path_count": None,
            "dirty_paths": [],
            "dirty_paths_truncated": None,
        }

    git_root = Path(top_level.stdout.strip()).resolve()
    try:
        root.relative_to(git_root)
    except ValueError:
        return {
            "is_repository": None,
            "repository_state": "unverified",
            "repository_state_reason": "git_root_outside_target_scope",
            "worktree_state": "unverified",
            "worktree_state_reason": "git_root_outside_target_scope",
            "dirty_path_count": None,
            "dirty_paths": [],
            "dirty_paths_truncated": None,
        }

    branch_result, _ = run("symbolic-ref", "--quiet", "--short", "HEAD")
    if branch_result.returncode != 0:
        branch_result, _ = run("rev-parse", "--short", "HEAD")

    return {
        "is_repository": True,
        "repository_state": "verified",
        "root": str(git_root),
        "target_matches_git_root": git_root == root,
        "branch_or_commit": (
            branch_result.stdout.strip() if branch_result.returncode == 0 else None
        ),
        "worktree_state": "unverified",
        "worktree_state_reason": "content_comparison_skipped_to_avoid_git_filters",
        "dirty_path_count": None,
        "dirty_paths": [],
        "dirty_paths_truncated": None,
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
    files, skipped, skipped_symlinks, warnings, truncated = walk_repository(
        root, max_files, include_vendored
    )
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
            parsed, warning = parse_package_scripts(path, root, set(lockfiles))
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
    for instruction in instruction_summaries:
        for command in instruction["documented_verification_commands"]:
            verification_commands.append(
                {
                    "source": instruction["path"],
                    "name": f"documented:L{command['line']}",
                    "definition": command["definition"],
                }
            )
    verification_commands = verification_commands[:250]

    root_instructions = [
        item for item in instruction_summaries if "/" not in item["path"]
    ]
    broken_link_count = sum(
        len(item["broken_relative_links"]) for item in instruction_summaries
    )
    version_control = git_metadata(root)
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
    if version_control.get("worktree_state") == "unverified":
        diagnostics.append("git_worktree_state_unverified")
    if version_control.get("repository_state") == "unverified":
        diagnostics.append("git_repository_identity_unverified")

    top_level = []
    try:
        top_level = sorted(
            (entry.name for entry in root.iterdir()), key=portable_name_key
        )[:200]
    except OSError as error:
        warnings.append(f"Unable to list repository root: {error}")

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "scan": {
            "implementation": "python",
            "files_seen": len(files),
            "max_files": max_files,
            "truncated": truncated,
            "include_vendored": include_vendored,
            "skipped_directories": skipped[:MAX_REPORTED_PATHS],
            "skipped_symlinks": skipped_symlinks[:MAX_REPORTED_PATHS],
            "warnings": sorted(set(warnings))[:100],
        },
        "version_control": version_control,
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
    is_repository = report["version_control"].get("is_repository")
    repository_display = (
        "Unverified" if is_repository is None else str(is_repository)
    )
    lines = [
        "# Agentize repository inventory",
        "",
        f"- Root: `{report['root']}`",
        f"- Files scanned: {report['scan']['files_seen']}",
        f"- Ecosystems: {', '.join(project['ecosystems']) or 'none detected'}",
        f"- Git repository: {repository_display}",
        "- Git worktree state: "
        f"{report['version_control'].get('worktree_state', 'unverified')}",
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
