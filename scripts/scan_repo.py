#!/usr/bin/env python3
"""Produce a bounded, read-only inventory of an agent workflow in a repository."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote


SCHEMA_VERSION = 7
DEFAULT_MAX_FILES = 50_000
DEFAULT_MAX_DIRECTORIES = 50_000
DEFAULT_MAX_DEPTH = 64
MAX_REPORTED_PATHS = 200
MAX_REPORTED_WARNINGS = 100
MAX_PARSED_MANIFESTS = 50
MAX_DECLARED_COMMANDS = 250
MAX_REPORTED_LANGUAGES = 20
MAX_INSTRUCTION_HEADINGS = 50
MAX_INSTRUCTION_REFERENCES = 100
MAX_INSTRUCTION_LINK_RESULTS = 20
MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION = 50
MAX_MANIFEST_COMMANDS = 100
MAX_TASK_TARGETS = 200

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
    "REVIEW.md": "claude-review",
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
    "changelog.md",
    "contributing.md",
    "development.md",
    "readme.md",
    "security.md",
}

HIGH_SIGNAL_DOC_WORDS = {
    "adr",
    "architecture",
    "business",
    "decisions",
    "deployment",
    "design",
    "development",
    "domain",
    "glossary",
    "invariants",
    "observability",
    "operations",
    "product",
    "runbook",
    "testing",
    "verification",
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
FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*?)[ \t]*$")
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
INSTRUCTION_IMPORT = re.compile(
    r"(?<![A-Za-z0-9_])@((?:~[/\\]|\.{0,2}[/\\]|[/\\])?[^\s`\"'<>]+)"
)
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


def path_identity(path: Path) -> tuple[int, int] | None:
    """Return a filesystem identity that is stable across spelling aliases."""
    try:
        metadata = path.stat()
    except OSError:
        return None
    return metadata.st_dev, metadata.st_ino


def is_same_or_descendant_existing(candidate: Path, ancestor: Path) -> bool:
    """Compare existing paths by identity, including on case-insensitive volumes."""
    ancestor_identity = path_identity(ancestor)
    if ancestor_identity is None:
        return False
    current = candidate
    while True:
        if path_identity(current) == ancestor_identity:
            return True
        parent = current.parent
        if parent == current:
            return False
        current = parent


def normalize_excluded_paths(root: Path, values: Iterable[str]) -> list[Path]:
    """Resolve exact exclusions inside root and remove redundant descendants."""
    candidates: dict[tuple[int, int], Path] = {}
    for value in values:
        candidate = Path(value).expanduser()
        if not candidate.is_absolute():
            candidate = root / candidate
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError) as error:
            raise ValueError(
                f"Excluded path does not exist: {candidate}"
            ) from error
        try:
            relative = resolved.relative_to(root)
        except ValueError as error:
            raise ValueError(
                f"Excluded path is outside the repository root: {resolved}"
            ) from error
        identity = path_identity(resolved)
        if not relative.parts or identity == path_identity(root):
            raise ValueError("Repository root cannot be excluded")
        if identity is None:
            raise ValueError(f"Excluded path cannot be inspected: {resolved}")
        candidates.setdefault(identity, resolved)

    ordered = sorted(
        candidates.values(),
        key=lambda candidate: (
            len(candidate.relative_to(root).parts),
            portable_name_key(relative_path(candidate, root)),
        ),
    )
    retained: list[Path] = []
    for candidate in ordered:
        if any(is_same_or_descendant_existing(candidate, parent) for parent in retained):
            continue
        retained.append(candidate)
    return sorted(
        retained,
        key=lambda candidate: portable_name_key(relative_path(candidate, root)),
    )


def redact_sensitive_text(value: str) -> str:
    redacted = SENSITIVE_ASSIGNMENT.sub(r"\1=<redacted>", value)
    redacted = SENSITIVE_OPTION.sub(r"\1 <redacted>", redacted)
    redacted = BASIC_AUTH_URL.sub(r"\1<redacted>@", redacted)
    return BEARER_CREDENTIAL.sub(r"\1 <redacted>", redacted)


def markdown_prose_lines(text: str) -> list[str]:
    """Return rendered Markdown prose with fenced, inline, and commented code removed."""
    prose: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    in_html_comment = False

    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if fence_character is not None:
            if stripped.startswith(fence_character * fence_length) and not stripped.lstrip(
                fence_character
            ).strip():
                fence_character = None
                fence_length = 0
            prose.append("")
            continue

        pieces: list[str] = []
        cursor = 0
        while cursor < len(raw_line):
            if in_html_comment:
                end = raw_line.find("-->", cursor)
                if end < 0:
                    cursor = len(raw_line)
                    break
                cursor = end + 3
                in_html_comment = False
                continue
            start = raw_line.find("<!--", cursor)
            if start < 0:
                pieces.append(raw_line[cursor:])
                break
            pieces.append(raw_line[cursor:start])
            cursor = start + 4
            in_html_comment = True

        line = "".join(pieces)
        match = FENCE.match(line)
        if match:
            fence_character = match.group(1)[0]
            fence_length = len(match.group(1))
            prose.append("")
            continue
        prose.append(re.sub(r"`+[^`]*`+", "", line))

    return prose


def documented_verification_commands(
    text: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Collect conservative command candidates from fenced instruction examples."""
    commands: list[dict[str, Any]] = []
    all_commands: list[dict[str, Any]] = []
    fence_character: str | None = None
    fence_length = 0
    inspect_fence = False
    pending_command: str | None = None
    pending_line = 0

    def has_continuation(candidate: str) -> bool:
        stripped = candidate.rstrip()
        trailing = len(stripped) - len(stripped.rstrip("\\"))
        return trailing % 2 == 1

    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if fence_character is None:
            match = FENCE.match(line)
            if not match:
                continue
            marker, info = match.groups()
            info_parts = (info or "").split(maxsplit=1)
            language = (info_parts[0] if info_parts else "").strip("{}.")
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
            pending_command = None
            pending_line = 0
            continue
        if not inspect_fence:
            continue

        candidate = stripped
        if candidate.startswith(("$ ", "> ")):
            candidate = candidate[2:].lstrip()
        if not candidate or candidate.startswith(("#", "//", "- ", "* ")):
            pending_command = None
            pending_line = 0
            continue

        command_line = pending_line or line_number
        if pending_command is not None:
            candidate = f"{pending_command} {candidate}"

        if has_continuation(candidate):
            pending_command = candidate.rstrip()[:-1].rstrip()
            pending_line = command_line
            if len(pending_command) > 1_000:
                pending_command = None
                pending_line = 0
            continue

        pending_command = None
        pending_line = 0
        if (
            len(candidate) > 1_000
            or not COMMAND_START.search(candidate)
            or not VERIFICATION_COMMAND.search(candidate)
        ):
            continue
        command = {
            "line": command_line,
            "definition": redact_sensitive_text(candidate),
        }
        if len(commands) < MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION:
            commands.append(command)
        all_commands.append(command)
    return commands, all_commands


def path_is_excluded(path: Path, excluded_identities: set[tuple[int, int]]) -> bool:
    identity = path_identity(path)
    return identity is not None and identity in excluded_identities


def resolved_target_is_out_of_scope(
    target: Path,
    root: Path,
    excluded_paths: list[Path],
    max_depth: int,
    include_vendored: bool,
) -> bool:
    """Reject file-symlink targets that would bypass traversal boundaries."""
    try:
        relative = target.relative_to(root)
    except ValueError:
        return True
    if any(is_same_or_descendant_existing(target, excluded) for excluded in excluded_paths):
        return True
    parent_parts = relative.parts[:-1]
    folded_parts = {part.casefold() for part in parent_parts}
    if folded_parts & IGNORED_DIRECTORIES:
        return True
    if not include_vendored and folded_parts & VENDORED_DIRECTORIES:
        return True
    return len(parent_parts) > max_depth


def walk_repository(
    root: Path,
    max_files: int,
    max_directories: int,
    max_depth: int,
    include_vendored: bool,
    excluded_paths: list[Path],
) -> tuple[
    list[Path], list[str], list[str], list[str], list[str], bool, int, list[str]
]:
    files: list[Path] = []
    skipped: set[str] = set()
    skipped_symlinks: set[str] = set()
    skipped_special_files: set[str] = set()
    errors: list[str] = []
    truncated = False
    directories_seen = 0
    limit_reasons: set[str] = set()
    stop_scan = False
    excluded_identities = {
        identity
        for excluded in excluded_paths
        if (identity := path_identity(excluded)) is not None
    }

    def on_error(error: OSError) -> None:
        target = getattr(error, "filename", None) or "unknown path"
        try:
            display = relative_path(Path(target), root)
        except ValueError:
            display = Path(target).name or "unknown path"
        errors.append(f"Unable to scan directory: {display}")

    for current, directory_names, file_names in os.walk(
        root, topdown=True, followlinks=False, onerror=on_error
    ):
        current_path = Path(current)
        if directories_seen >= max_directories:
            skipped.add(relative_path(current_path, root))
            truncated = True
            limit_reasons.add("max_directories")
            break
        directories_seen += 1
        depth = len(current_path.relative_to(root).parts)
        kept_directories: list[str] = []
        for directory_name in sorted(directory_names, key=portable_name_key):
            directory_path = current_path / directory_name
            if path_is_excluded(directory_path, excluded_identities):
                continue
            if directory_path.is_symlink():
                skipped_symlinks.add(relative_path(directory_path, root))
                continue
            folded = directory_name.casefold()
            is_vendored = folded in VENDORED_DIRECTORIES
            if folded in IGNORED_DIRECTORIES or (is_vendored and not include_vendored):
                skipped.add(relative_path(directory_path, root))
                continue
            kept_directories.append(directory_name)
        if depth >= max_depth and kept_directories:
            skipped.update(
                relative_path(current_path / directory_name, root)
                for directory_name in kept_directories
            )
            directory_names[:] = []
            truncated = True
            limit_reasons.add("max_depth")
        else:
            directory_names[:] = kept_directories

        for file_name in sorted(file_names, key=portable_name_key):
            file_path = current_path / file_name
            if path_is_excluded(file_path, excluded_identities):
                continue
            if file_path.is_symlink():
                try:
                    resolved = file_path.resolve(strict=True)
                except (OSError, RuntimeError, ValueError):
                    skipped_symlinks.add(relative_path(file_path, root))
                    continue
                if resolved_target_is_out_of_scope(
                    resolved,
                    root,
                    excluded_paths,
                    max_depth,
                    include_vendored,
                ):
                    skipped_symlinks.add(relative_path(file_path, root))
                    continue
                if not resolved.is_file():
                    skipped_special_files.add(relative_path(file_path, root))
                    continue
            elif not file_path.is_file():
                skipped_special_files.add(relative_path(file_path, root))
                continue
            if len(files) >= max_files:
                truncated = True
                limit_reasons.add("max_files")
                stop_scan = True
                break
            files.append(file_path)
        if stop_scan:
            break

    return (
        files,
        sorted(skipped),
        sorted(skipped_symlinks),
        sorted(skipped_special_files),
        errors,
        truncated,
        directories_seen,
        sorted(limit_reasons),
    )


def is_ci_path(relative: str) -> bool:
    path = Path(relative)
    name = path.name.casefold()
    parts = tuple(part.casefold() for part in path.parts)
    suffix = path.suffix.casefold()
    return (
        (
            len(parts) == 3
            and parts[:2] == (".github", "workflows")
            and suffix in {".yaml", ".yml"}
        )
        or (parts == (".circleci", "config.yml"))
        or (parts == (".circleci", "config.yaml"))
        or (
            len(parts) >= 2
            and parts[0] in {".buildkite", ".gitlab"}
            and suffix in {".json", ".yaml", ".yml"}
        )
        or (
            len(parts) == 1
            and name
            in {
                ".gitlab-ci.yml",
                "azure-pipelines.yml",
                "bitbucket-pipelines.yml",
                "jenkinsfile",
            }
        )
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
    name = path.name.casefold()
    if name in DOC_BASENAMES or name.startswith("readme."):
        return True
    parts = {part.casefold() for part in path.parts}
    signal_words = set().union(
        *(set(re.split(r"[-_.]", part.casefold())) for part in path.parts)
    )
    return (len(path.parts) == 1 or "docs" in parts) and bool(
        signal_words & HIGH_SIGNAL_DOC_WORDS
    )


def has_architecture_or_testing_signal(relative: str) -> bool:
    words = set().union(
        *(set(re.split(r"[-_.]", part.casefold())) for part in Path(relative).parts)
    )
    return bool(words & HIGH_SIGNAL_DOC_WORDS)


def contains_path_pair(parts: tuple[str, ...], first: str, second: str) -> bool:
    """Return whether two directory names occur consecutively in a path."""
    return any(
        parts[index : index + 2] == (first, second)
        for index in range(len(parts) - 1)
    )


def instruction_kind(relative: str) -> str | None:
    path = Path(relative)
    folded_parts = tuple(part.casefold() for part in path.parts)
    if path.name == "AGENTS.md" and path.parent.name.casefold() == ".kimi":
        return "kimi"
    if path.name == "agents.md":
        return "kimi"
    if path.name in INSTRUCTION_FILES:
        if path.name == "copilot-instructions.md" and ".github" not in path.parts:
            return None
        if path.name == "REVIEW.md" and len(path.parts) != 1:
            return None
        return INSTRUCTION_FILES[path.name]
    if (
        path.suffix.casefold() == ".md"
        and len(folded_parts) >= 3
        and folded_parts[:2] == (".claude", "rules")
    ):
        return "claude-rule"
    if (
        path.name.casefold().endswith(".instructions.md")
        and len(folded_parts) >= 3
        and folded_parts[:2] == (".github", "instructions")
    ):
        return "copilot-path"
    if path.suffix.casefold() == ".mdc" and contains_path_pair(
        folded_parts, ".cursor", "rules"
    ):
        return "cursor"
    if path.suffix.casefold() == ".md" and contains_path_pair(
        folded_parts, ".windsurf", "rules"
    ):
        return "windsurf-rule"
    if (
        path.name.casefold() == "bugbot.md"
        and path.parent.name.casefold() == ".cursor"
    ):
        return "cursor-review"
    return None


def agent_definition_kind(relative: str) -> str | None:
    path = Path(relative)
    folded_parts = tuple(part.casefold() for part in path.parts)
    if path.suffix.casefold() == ".md" and len(folded_parts) >= 3:
        if folded_parts[:2] == (".claude", "agents"):
            return "claude"
        if folded_parts[:2] == (".gemini", "agents"):
            return "gemini"
    if (
        path.suffix.casefold() == ".md"
        and len(folded_parts) >= 3
        and folded_parts[:2] == (".github", "agents")
    ):
        return "copilot"
    return None


def prompt_kind(relative: str) -> str | None:
    path = Path(relative)
    folded_parts = tuple(part.casefold() for part in path.parts)
    if len(folded_parts) < 3:
        return None
    if path.suffix.casefold() == ".md" and folded_parts[:2] == (
        ".claude",
        "commands",
    ):
        return "claude"
    if (
        path.name.casefold().endswith(".prompt.md")
        and folded_parts[:2] == (".github", "prompts")
    ):
        return "copilot"
    if path.suffix.casefold() == ".toml" and folded_parts[:2] == (
        ".gemini",
        "commands",
    ):
        return "gemini"
    if path.suffix.casefold() == ".md" and folded_parts[:2] == (
        ".cursor",
        "commands",
    ):
        return "cursor"
    if path.suffix.casefold() == ".md" and contains_path_pair(
        folded_parts, ".windsurf", "workflows"
    ):
        return "windsurf"
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
        ".windsurf",
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
        metadata = resolved.stat()
        if not stat.S_ISREG(metadata.st_mode):
            return None, f"Skipped {path.name}: not a regular file"
        size = metadata.st_size
        if size > max_bytes:
            return None, f"Skipped {path.name}: file is larger than {max_bytes} bytes"
        descriptor = os.open(
            resolved,
            os.O_RDONLY | getattr(os, "O_NONBLOCK", 0),
        )
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                return None, f"Skipped {path.name}: not a regular file"
            chunks: list[bytes] = []
            remaining = max_bytes + 1
            while remaining > 0:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
        finally:
            os.close(descriptor)
        data = b"".join(chunks)
        if len(data) > max_bytes:
            return None, f"Skipped {path.name}: file is larger than {max_bytes} bytes"
        return data.decode("utf-8-sig", errors="replace"), None
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


def instruction_import_targets(text: str) -> list[str]:
    """Collect direct @ tokens from rendered Markdown prose."""
    targets: list[str] = []
    for line in markdown_prose_lines(text):
        for match in INSTRUCTION_IMPORT.finditer(line):
            target = match.group(1).rstrip(".,;:!?)]}")
            if target:
                targets.append(target)
    return targets


def resolve_instruction_target(path: Path, target: str) -> Path:
    normalized = target.replace("\\", os.sep)
    if normalized == "~" or normalized.startswith(f"~{os.sep}"):
        return Path(normalized).expanduser().resolve(strict=False)
    candidate = Path(normalized)
    if not candidate.is_absolute():
        candidate = path.parent / candidate
    return candidate.resolve(strict=False)


def looks_like_instruction_import(target: str, candidate: Path) -> bool:
    """Reject ordinary @mentions while retaining conservative path-like imports."""
    normalized = target.replace("\\", "/")
    if normalized.startswith(("./", "../", "~/", "/")):
        return True
    if re.match(r"^[A-Za-z]:/", normalized):
        return True
    try:
        if candidate.exists():
            return True
    except OSError:
        pass
    leaf = normalized.rstrip("/").rsplit("/", 1)[-1]
    return leaf not in {"", ".", ".."} and "." in leaf


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
    imports: list[str] = []
    broken_imports: list[str] = []
    outside_imports: list[str] = []
    documented_commands: list[dict[str, Any]] = []
    all_documented_commands: list[dict[str, Any]] = []
    line_count = 0
    heading_count = 0
    relative_link_target_count = 0

    if text is not None:
        line_count = len(text.splitlines())
        prose_lines = markdown_prose_lines(text)
        prose_text = "\n".join(prose_lines)
        documented_commands, all_documented_commands = documented_verification_commands(
            text
        )
        for line in prose_lines:
            match = HEADING.match(line)
            if match:
                heading_count += 1
                if len(headings) < MAX_INSTRUCTION_HEADINGS:
                    headings.append(redact_sensitive_text(match.group(2).strip()))
        link_matches = list(MARKDOWN_LINK.finditer(prose_text))
        relative_link_target_count = len(link_matches)
        for match in link_matches[:MAX_INSTRUCTION_REFERENCES]:
            target = extract_markdown_target(match.group(1))
            if not target:
                continue
            try:
                candidate = (path.parent / target).resolve(strict=False)
            except (OSError, RuntimeError, ValueError):
                broken_links.append(target)
                continue
            try:
                candidate.relative_to(root)
            except ValueError:
                outside_links.append(target)
                continue
            if not candidate.exists():
                broken_links.append(target)
        if kind in {"shared", "claude", "gemini", "copilot"}:
            for target in sorted(set(instruction_import_targets(text))):
                try:
                    candidate = resolve_instruction_target(path, target)
                except (OSError, RuntimeError, ValueError):
                    if target.startswith((".", "/", "~")) or "." in Path(target).name:
                        imports.append(target)
                        broken_imports.append(target)
                    continue
                if not looks_like_instruction_import(target, candidate):
                    continue
                imports.append(target)
                try:
                    candidate.relative_to(root)
                except ValueError:
                    outside_imports.append(target)
                    continue
                if not candidate.exists():
                    broken_imports.append(target)

    return (
        {
            "path": relative_path(path, root),
            "kind": kind,
            "bytes": size,
            "lines": line_count,
            "symlink": path.is_symlink(),
            "headings": headings,
            "documented_verification_commands": documented_commands,
            "broken_relative_links": sorted(set(broken_links))[
                :MAX_INSTRUCTION_LINK_RESULTS
            ],
            "relative_links_outside_repository": sorted(set(outside_links))[
                :MAX_INSTRUCTION_LINK_RESULTS
            ],
            "imports": imports[:MAX_INSTRUCTION_REFERENCES],
            "broken_imports": sorted(set(broken_imports))[
                :MAX_INSTRUCTION_REFERENCES
            ],
            "imports_outside_repository": sorted(set(outside_imports))[
                :MAX_INSTRUCTION_REFERENCES
            ],
            "headings_total": heading_count,
            "documented_verification_commands_total": len(all_documented_commands),
            "relative_link_targets_total": relative_link_target_count,
            "broken_relative_links_total": len(set(broken_links)),
            "relative_links_outside_repository_total": len(set(outside_links)),
            "imports_total": len(imports),
            "broken_imports_total": len(set(broken_imports)),
            "imports_outside_repository_total": len(set(outside_imports)),
            "_all_documented_verification_commands": all_documented_commands,
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
    ordered_scripts = dict(sorted(clean_scripts.items()))
    return {
        "source": relative_path(path, root),
        "package_manager": detect_package_manager(
            path.parent, root, scanned_lockfiles
        ),
        "scripts": dict(list(ordered_scripts.items())[:MAX_MANIFEST_COMMANDS]),
        "scripts_total": len(ordered_scripts),
        "_all_scripts": ordered_scripts,
    }, None


def detect_package_manager(
    directory: Path, root: Path, scanned_lockfiles: set[str]
) -> str | None:
    current = directory
    while True:
        for name, manager in (
            ("pnpm-lock.yaml", "pnpm"),
            ("yarn.lock", "yarn"),
            ("bun.lock", "bun"),
            ("bun.lockb", "bun"),
            ("package-lock.json", "npm"),
        ):
            if relative_path(current / name, root) in scanned_lockfiles:
                return manager
        if current == root:
            break
        parent = current.parent
        try:
            parent.relative_to(root)
        except ValueError:
            break
        current = parent
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

    return sorted(targets)


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
        targets = sorted(target_set)
    if not targets:
        return None, None
    return {
        "source": relative_path(path, root),
        "runner": runner,
        "targets": targets[:MAX_TASK_TARGETS],
        "targets_total": len(targets),
        "_all_targets": targets,
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
    ordered_scripts = dict(sorted(scripts.items()))
    return {
        "source": relative_path(path, root),
        "scripts": dict(list(ordered_scripts.items())[:MAX_MANIFEST_COMMANDS]),
        "scripts_total": len(ordered_scripts),
        "_all_scripts": ordered_scripts,
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
    git_command = shutil.which("git", path=git_environment.get("PATH"))
    git_discovery_failure: str | None = None
    if git_command is None:
        git_discovery_failure = "git_executable_unavailable"
    else:
        try:
            resolved_git_command = Path(git_command).resolve(strict=True)
            resolved_git_command.relative_to(root)
        except ValueError:
            git_command = str(resolved_git_command)
        except (OSError, RuntimeError):
            git_command = None
            git_discovery_failure = "git_executable_unavailable"
        else:
            git_command = None
            git_discovery_failure = "git_executable_inside_target"

    def run(
        *arguments: str,
    ) -> tuple[subprocess.CompletedProcess[str], str | None]:
        if git_command is None:
            return (
                subprocess.CompletedProcess([], 127, "", git_discovery_failure or ""),
                git_discovery_failure or "git_executable_unavailable",
            )
        try:
            return (
                subprocess.run(
                    [
                        git_command,
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


def build_report(
    root: Path,
    max_files: int,
    max_directories: int,
    max_depth: int,
    include_vendored: bool,
    excluded_paths: list[Path],
) -> dict[str, Any]:
    (
        files,
        skipped,
        skipped_symlinks,
        skipped_special_files,
        walk_warnings,
        truncated,
        directories_seen,
        limit_reasons,
    ) = walk_repository(
        root,
        max_files,
        max_directories,
        max_depth,
        include_vendored,
        excluded_paths,
    )
    warnings = list(walk_warnings)
    verification_evidence_incomplete = False
    relatives = [relative_path(path, root) for path in files]
    report_truncated_sections: list[dict[str, int | str]] = []

    def record_report_limit(section: str, total: int, reported: int) -> None:
        if total > reported:
            report_truncated_sections.append(
                {"path": section, "total": total, "reported": reported}
            )

    def cap_paths(
        values: Iterable[str], section: str, limit: int = MAX_REPORTED_PATHS
    ) -> list[str]:
        ordered = sorted(set(values))
        reported = ordered[:limit]
        record_report_limit(section, len(ordered), len(reported))
        return reported

    language_counts = Counter(
        language
        for path in files
        if (language := LANGUAGE_EXTENSIONS.get(path.suffix.casefold())) is not None
    )

    all_manifests = sorted(
        {
            relative
            for relative in relatives
            if Path(relative).name in MANIFEST_NAMES
        }
    )
    manifests = cap_paths(all_manifests, "project.manifests")
    all_lockfiles = [
        relative for relative in relatives if Path(relative).name in LOCKFILE_NAMES
    ]
    lockfiles = cap_paths(all_lockfiles, "project.lockfiles")
    all_task_runners = sorted(
        {
            relative
            for relative in relatives
            if Path(relative).name in TASK_RUNNER_NAMES
        }
    )
    task_runners = cap_paths(all_task_runners, "project.task_runners")
    all_ci_files = [relative for relative in relatives if is_ci_path(relative)]
    ci_files = cap_paths(all_ci_files, "automation.ci_files")
    quality_configs = cap_paths(
        (
            relative
            for relative in relatives
            if Path(relative).name in QUALITY_CONFIG_NAMES
        ),
        "automation.quality_configs",
    )
    all_high_signal_docs = [
        relative for relative in relatives if is_high_signal_doc(relative)
    ]
    docs = cap_paths(all_high_signal_docs, "documentation.high_signal_files")
    test_paths = cap_paths(
        (relative for relative in relatives if is_test_path(relative)),
        "verification.test_paths",
    )
    skills = cap_paths(
        (relative for relative in relatives if is_skill_path(relative)),
        "agent_surface.skills",
    )
    all_agent_definitions = sorted(
        (
            {"path": relative, "kind": kind}
            for relative in relatives
            if (kind := agent_definition_kind(relative)) is not None
        ),
        key=lambda item: item["path"],
    )
    agent_definitions = all_agent_definitions[:MAX_REPORTED_PATHS]
    record_report_limit(
        "agent_surface.agent_definitions",
        len(all_agent_definitions),
        len(agent_definitions),
    )
    all_prompts = sorted(
        (
            {"path": relative, "kind": kind}
            for relative in relatives
            if (kind := prompt_kind(relative)) is not None
        ),
        key=lambda item: item["path"],
    )
    prompts = all_prompts[:MAX_REPORTED_PATHS]
    record_report_limit("agent_surface.prompts", len(all_prompts), len(prompts))
    agent_configs = cap_paths(
        (
            relative
            for relative in relatives
            if is_agent_config(relative)
            and instruction_kind(relative) is None
            and agent_definition_kind(relative) is None
            and prompt_kind(relative) is None
        ),
        "agent_surface.config",
    )

    instruction_summaries: list[dict[str, Any]] = []
    instruction_candidates = sorted(
        (
            (path, relative, kind)
            for path, relative in zip(files, relatives)
            if (kind := instruction_kind(relative)) is not None
        ),
        key=lambda item: (
            len(Path(item[1]).parts),
            portable_name_key(item[1]),
        ),
    )
    record_report_limit(
        "agent_surface.instructions",
        len(instruction_candidates),
        min(len(instruction_candidates), MAX_REPORTED_PATHS),
    )
    for path, relative, kind in instruction_candidates[:MAX_REPORTED_PATHS]:
        summary, summary_warnings = summarize_instruction(path, root, kind)
        instruction_summaries.append(summary)
        warnings.extend(summary_warnings)
        verification_evidence_incomplete = (
            verification_evidence_incomplete or bool(summary_warnings)
        )
        for field, total_field in (
            ("headings", "headings_total"),
            (
                "documented_verification_commands",
                "documented_verification_commands_total",
            ),
            ("relative_link_targets_inspected", "relative_link_targets_total"),
            ("broken_relative_links", "broken_relative_links_total"),
            (
                "relative_links_outside_repository",
                "relative_links_outside_repository_total",
            ),
            ("imports", "imports_total"),
            ("broken_imports", "broken_imports_total"),
            ("imports_outside_repository", "imports_outside_repository_total"),
        ):
            reported = (
                min(summary[total_field], MAX_INSTRUCTION_REFERENCES)
                if field == "relative_link_targets_inspected"
                else len(summary[field])
            )
            record_report_limit(
                f"agent_surface.instructions[{relative}].{field}",
                summary[total_field],
                reported,
            )
    instruction_summaries.sort(key=lambda item: item["path"])

    package_scripts: list[dict[str, Any]] = []
    python_scripts: list[dict[str, Any]] = []
    task_targets: list[dict[str, Any]] = []
    path_by_relative = dict(zip(relatives, files))
    package_manifest_candidates = [
        relative for relative in all_manifests if Path(relative).name == "package.json"
    ]
    python_manifest_candidates = [
        relative for relative in all_manifests if Path(relative).name == "pyproject.toml"
    ]
    record_report_limit(
        "verification.package_script_manifests_inspected",
        len(package_manifest_candidates),
        min(len(package_manifest_candidates), MAX_PARSED_MANIFESTS),
    )
    record_report_limit(
        "verification.python_entrypoint_manifests_inspected",
        len(python_manifest_candidates),
        min(len(python_manifest_candidates), MAX_PARSED_MANIFESTS),
    )
    record_report_limit(
        "verification.task_runner_files_inspected",
        len(all_task_runners),
        min(len(all_task_runners), MAX_PARSED_MANIFESTS),
    )
    for relative in package_manifest_candidates[:MAX_PARSED_MANIFESTS]:
        path = path_by_relative[relative]
        parsed, warning = parse_package_scripts(path, root, set(all_lockfiles))
        if parsed:
            package_scripts.append(parsed)
            record_report_limit(
                f"verification.package_scripts[{relative}].scripts",
                parsed["scripts_total"],
                len(parsed["scripts"]),
            )
        if warning:
            warnings.append(warning)
            verification_evidence_incomplete = True
    for relative in python_manifest_candidates[:MAX_PARSED_MANIFESTS]:
        parsed, warning = parse_python_scripts(path_by_relative[relative], root)
        if parsed:
            python_scripts.append(parsed)
            record_report_limit(
                f"verification.python_entrypoints[{relative}].scripts",
                parsed["scripts_total"],
                len(parsed["scripts"]),
            )
        if warning:
            warnings.append(warning)
            verification_evidence_incomplete = True
    for relative in all_task_runners[:MAX_PARSED_MANIFESTS]:
        parsed, warning = parse_task_targets(path_by_relative[relative], root)
        if parsed:
            task_targets.append(parsed)
            record_report_limit(
                f"verification.task_targets[{relative}].targets",
                parsed["targets_total"],
                len(parsed["targets"]),
            )
        if warning:
            warnings.append(warning)
            verification_evidence_incomplete = True

    verification_commands: list[dict[str, str]] = []
    for package in package_scripts:
        for name, command in package["_all_scripts"].items():
            if VERIFICATION_NAME.search(name):
                verification_commands.append(
                    {"source": package["source"], "name": name, "definition": command}
                )
    for runner in task_targets:
        for target in runner["_all_targets"]:
            if VERIFICATION_NAME.search(target):
                verification_commands.append(
                    {"source": runner["source"], "name": target, "definition": runner["runner"]}
                )
    for instruction in instruction_summaries:
        for command in instruction["_all_documented_verification_commands"]:
            verification_commands.append(
                {
                    "source": instruction["path"],
                    "name": f"documented:L{command['line']}",
                    "definition": command["definition"],
                }
            )
    for package in package_scripts:
        package.pop("_all_scripts", None)
    for entrypoint in python_scripts:
        entrypoint.pop("_all_scripts", None)
    for runner in task_targets:
        runner.pop("_all_targets", None)
    for instruction in instruction_summaries:
        instruction.pop("_all_documented_verification_commands", None)
    all_verification_commands = verification_commands
    verification_commands = all_verification_commands[:MAX_DECLARED_COMMANDS]
    record_report_limit(
        "verification.declared_commands",
        len(all_verification_commands),
        len(verification_commands),
    )

    root_instructions = [
        item
        for item in instruction_summaries
        if (
            "/" not in item["path"]
            or item["path"].casefold() == ".kimi/agents.md"
        )
        and item["kind"] != "claude-review"
    ]
    broken_link_count = sum(
        len(item["broken_relative_links"]) for item in instruction_summaries
    )
    broken_import_count = sum(
        len(item["broken_imports"]) for item in instruction_summaries
    )
    outside_import_count = sum(
        len(item["imports_outside_repository"]) for item in instruction_summaries
    )
    version_control = git_metadata(root)
    top_level: list[str] = []
    try:
        excluded_identities = {
            identity
            for excluded in excluded_paths
            if (identity := path_identity(excluded)) is not None
        }
        all_top_level = sorted(
            (
                entry.name
                for entry in root.iterdir()
                if not path_is_excluded(entry, excluded_identities)
            ),
            key=portable_name_key,
        )
        top_level = all_top_level[:MAX_REPORTED_PATHS]
        record_report_limit(
            "project.top_level_entries", len(all_top_level), len(top_level)
        )
    except OSError as error:
        warnings.append(f"Unable to list repository root: {error}")

    all_languages = [
        {"name": name, "files": count}
        for name, count in language_counts.most_common()
    ]
    languages = all_languages[:MAX_REPORTED_LANGUAGES]
    record_report_limit("project.languages", len(all_languages), len(languages))

    skipped_directories = skipped[:MAX_REPORTED_PATHS]
    reported_skipped_symlinks = skipped_symlinks[:MAX_REPORTED_PATHS]
    reported_skipped_special_files = skipped_special_files[:MAX_REPORTED_PATHS]
    record_report_limit(
        "scan.skipped_directories", len(skipped), len(skipped_directories)
    )
    record_report_limit(
        "scan.skipped_symlinks",
        len(skipped_symlinks),
        len(reported_skipped_symlinks),
    )
    record_report_limit(
        "scan.skipped_special_files",
        len(skipped_special_files),
        len(reported_skipped_special_files),
    )

    warning_values = sorted(set(warnings))
    reported_warnings = warning_values[:MAX_REPORTED_WARNINGS]
    record_report_limit("scan.warnings", len(warning_values), len(reported_warnings))

    diagnostics: list[str] = []
    traversal_detection_incomplete = bool(limit_reasons or walk_warnings)
    if not files:
        diagnostics.append(
            "repository_inventory_incomplete"
            if traversal_detection_incomplete
            else "empty_repository"
        )
    if not instruction_candidates:
        diagnostics.append(
            "agent_instruction_surface_detection_incomplete"
            if traversal_detection_incomplete
            else "no_agent_instruction_surface_detected"
        )
    elif not root_instructions:
        diagnostics.append("no_root_instruction_entrypoint_detected")
    elif not any(item["kind"] == "shared" for item in root_instructions):
        diagnostics.append("provider_specific_root_instructions_only")
    if len(root_instructions) > 1:
        diagnostics.append("multiple_root_instruction_surfaces_require_reconciliation")
    if any(item["bytes"] > 32_000 for item in root_instructions):
        diagnostics.append("large_root_instruction_file_may_need_routing")
    if broken_link_count:
        diagnostics.append("broken_relative_links_in_agent_instructions")
    if broken_import_count:
        diagnostics.append("broken_imports_in_agent_instructions")
    if outside_import_count:
        diagnostics.append("instruction_imports_outside_repository")
    verification_detection_incomplete = (
        traversal_detection_incomplete
        or verification_evidence_incomplete
        or any(
            item["path"]
            in {
                "agent_surface.instructions",
                "verification.package_script_manifests_inspected",
                "verification.python_entrypoint_manifests_inspected",
                "verification.task_runner_files_inspected",
            }
            or item["path"].endswith(
                (
                    ".documented_verification_commands",
                    ".scripts",
                    ".targets",
                )
            )
            for item in report_truncated_sections
        )
    )
    if not all_verification_commands:
        diagnostics.append(
            "declared_verification_command_detection_incomplete"
            if verification_detection_incomplete
            else "no_declared_verification_command_detected"
        )
    if not all_ci_files:
        diagnostics.append(
            "ci_configuration_detection_incomplete"
            if traversal_detection_incomplete
            else "no_ci_configuration_detected"
        )
    if len(files) >= 100 and not any(
        has_architecture_or_testing_signal(path) for path in all_high_signal_docs
    ):
        diagnostics.append(
            "high_signal_architecture_or_testing_doc_detection_incomplete"
            if traversal_detection_incomplete
            else "no_high_signal_architecture_or_testing_doc_detected"
        )
    if "max_files" in limit_reasons:
        diagnostics.append("scan_truncated_at_file_limit")
    if "max_directories" in limit_reasons:
        diagnostics.append("scan_truncated_at_directory_limit")
    if "max_depth" in limit_reasons:
        diagnostics.append("scan_truncated_at_depth_limit")
    if report_truncated_sections:
        diagnostics.append("report_fields_truncated")
    if version_control.get("worktree_state") == "unverified":
        diagnostics.append("git_worktree_state_unverified")
    if version_control.get("repository_state") == "unverified":
        diagnostics.append("git_repository_identity_unverified")

    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(root),
        "scan": {
            "implementation": "python",
            "files_seen": len(files),
            "directories_seen": directories_seen,
            "max_files": max_files,
            "max_directories": max_directories,
            "max_depth": max_depth,
            "truncated": truncated,
            "traversal_incomplete": traversal_detection_incomplete,
            "limit_reasons": limit_reasons,
            "report_truncated": bool(report_truncated_sections),
            "report_truncated_sections": report_truncated_sections,
            "report_limits": {
                "max_reported_paths": MAX_REPORTED_PATHS,
                "max_reported_warnings": MAX_REPORTED_WARNINGS,
                "max_parsed_manifests": MAX_PARSED_MANIFESTS,
                "max_declared_commands": MAX_DECLARED_COMMANDS,
                "max_reported_languages": MAX_REPORTED_LANGUAGES,
                "max_instruction_headings": MAX_INSTRUCTION_HEADINGS,
                "max_instruction_references": MAX_INSTRUCTION_REFERENCES,
                "max_instruction_link_results": MAX_INSTRUCTION_LINK_RESULTS,
                "max_documented_commands_per_instruction": MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION,
                "max_manifest_commands": MAX_MANIFEST_COMMANDS,
                "max_task_targets": MAX_TASK_TARGETS,
            },
            "include_vendored": include_vendored,
            "excluded_paths": [
                relative_path(path, root) for path in excluded_paths
            ],
            "skipped_directories": skipped_directories,
            "skipped_symlinks": reported_skipped_symlinks,
            "skipped_special_files": reported_skipped_special_files,
            "warnings": reported_warnings,
        },
        "version_control": version_control,
        "project": {
            "top_level_entries": top_level,
            "ecosystems": ecosystems_for(all_manifests),
            "languages": languages,
            "manifests": manifests,
            "lockfiles": lockfiles,
            "task_runners": task_runners,
        },
        "agent_surface": {
            "instructions": instruction_summaries,
            "skills": skills,
            "agent_definitions": agent_definitions,
            "prompts": prompts,
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


def markdown_code(value: Any) -> str:
    """Render untrusted report text as one safe Markdown code span."""
    escaped = "".join(
        f"\\u{ord(character):04x}"
        if character == "`" or ord(character) < 32 or ord(character) == 127
        else character
        for character in str(value)
    )
    return f"`{escaped}`"


def markdown_code_list(values: Iterable[Any]) -> str:
    rendered = [markdown_code(value) for value in values]
    return ", ".join(rendered) if rendered else "none"


def render_markdown(report: dict[str, Any]) -> str:
    project = report["project"]
    agent_surface = report["agent_surface"]
    verification = report["verification"]
    is_repository = report["version_control"].get("is_repository")
    repository_display = (
        "Unverified" if is_repository is None else str(is_repository)
    )
    traversal_incomplete = report["scan"]["traversal_incomplete"]
    instruction_detection_incomplete = (
        "agent_instruction_surface_detection_incomplete"
        in report["diagnostic_hints"]
    )
    verification_detection_incomplete = (
        "declared_verification_command_detection_incomplete"
        in report["diagnostic_hints"]
    )
    ecosystems_display = ", ".join(project["ecosystems"])
    if not ecosystems_display:
        ecosystems_display = (
            "unverified (traversal incomplete)"
            if traversal_incomplete
            else "none detected"
        )
    lines = [
        "# Agentize Skill repository inventory",
        "",
        f"- Root: {markdown_code(report['root'])}",
        f"- Files scanned: {report['scan']['files_seen']}",
        "- Traversal truncated: "
        f"{report['scan']['truncated']}"
        f" ({', '.join(report['scan']['limit_reasons']) or 'no limit reached'})",
        f"- Traversal incomplete: {report['scan']['traversal_incomplete']}",
        "- Report fields truncated: "
        f"{markdown_code_list(item['path'] for item in report['scan']['report_truncated_sections'])}",
        "- Excluded paths: "
        f"{markdown_code_list(report['scan']['excluded_paths'])}",
        f"- Ecosystems: {ecosystems_display}",
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
            if instruction["broken_imports"]:
                details += f", {len(instruction['broken_imports'])} broken import(s)"
            lines.append(f"- {markdown_code(instruction['path'])} ({details})")
    else:
        lines.append(
            "- No recognized instruction file detected in the scanned files; "
            "detection was incomplete."
            if instruction_detection_incomplete
            else "- No recognized instruction file detected."
        )

    lines.extend(["", "## Verification signals", ""])
    if verification["declared_commands"]:
        for command in verification["declared_commands"][:40]:
            lines.append(
                f"- {markdown_code(command['name'])} from "
                f"{markdown_code(command['source'])}: "
                f"{markdown_code(command['definition'])}"
            )
    else:
        lines.append(
            "- Declared verification-command detection is incomplete."
            if verification_detection_incomplete
            else "- No declared verification command detected."
        )

    lines.extend(["", "## Other evidence", ""])
    lines.append(
        f"- Skills: {len(agent_surface['skills'])}; agent definitions: "
        f"{len(agent_surface['agent_definitions'])}; prompts: "
        f"{len(agent_surface['prompts'])}; CI files: "
        f"{len(report['automation']['ci_files'])}; test paths: "
        f"{len(verification['test_paths'])}"
    )
    lines.append(
        "- High-signal docs: "
        f"{markdown_code_list(report['documentation']['high_signal_files'][:20])}"
    )

    lines.extend(["", "## Diagnostic hints", ""])
    if report["diagnostic_hints"]:
        lines.extend(
            f"- {markdown_code(hint)}" for hint in report["diagnostic_hints"]
        )
    else:
        lines.append("- No automatic hints. Human assessment is still required.")

    if report["scan"]["warnings"]:
        lines.extend(["", "## Scanner warnings", ""])
        lines.extend(
            f"- {markdown_code(warning)}" for warning in report["scan"]["warnings"]
        )
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
        "--max-directories",
        type=int,
        default=DEFAULT_MAX_DIRECTORIES,
        help=(
            "Stop after this many directories "
            f"(default: {DEFAULT_MAX_DIRECTORIES})."
        ),
    )
    parser.add_argument(
        "--max-depth",
        type=int,
        default=DEFAULT_MAX_DEPTH,
        help=(
            "Do not descend below this depth from the root "
            f"(default: {DEFAULT_MAX_DEPTH})."
        ),
    )
    parser.add_argument(
        "--include-vendored",
        action="store_true",
        help="Include vendor and third_party directories in the bounded scan.",
    )
    parser.add_argument(
        "--exclude-path",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "Exclude one exact file or directory inside the repository. "
            "Relative paths are resolved from --root; repeat as needed."
        ),
    )
    return parser.parse_args(arguments)


def declares_agentize_skill(package: Path) -> bool:
    """Recognize this skill package before applying automatic self-exclusion."""
    text, warning = read_text(package / "SKILL.md", package, max_bytes=32_000)
    if warning or text is None:
        return False
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return False
    for line in lines[1:101]:
        if line.strip() == "---":
            return False
        match = re.fullmatch(r"\s*name\s*:\s*(.*?)\s*", line)
        if match:
            value = match.group(1).strip().strip("'\"")
            return value == "agentize-skill"
    return False


def main(arguments: list[str] | None = None) -> int:
    options = parse_arguments(arguments if arguments is not None else sys.argv[1:])
    if options.max_files < 1:
        print("--max-files must be positive", file=sys.stderr)
        return 2
    if options.max_directories < 1:
        print("--max-directories must be positive", file=sys.stderr)
        return 2
    if options.max_depth < 0:
        print("--max-depth must be zero or positive", file=sys.stderr)
        return 2
    root = Path(options.root).expanduser().resolve()
    if not root.is_dir():
        print(f"Repository root is not a directory: {root}", file=sys.stderr)
        return 2
    requested_exclusions = list(options.exclude_path)
    scanner_package = Path(__file__).resolve().parents[1]
    try:
        scanner_package.relative_to(root)
    except ValueError:
        pass
    else:
        if scanner_package != root and declares_agentize_skill(scanner_package):
            requested_exclusions.append(str(scanner_package))
    try:
        excluded_paths = normalize_excluded_paths(root, requested_exclusions)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2
    report = build_report(
        root,
        options.max_files,
        options.max_directories,
        options.max_depth,
        options.include_vendored,
        excluded_paths,
    )
    if options.format == "markdown":
        print(render_markdown(report), end="")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
