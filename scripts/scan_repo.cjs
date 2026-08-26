#!/usr/bin/env node
'use strict';

// Produce the same bounded, read-only repository inventory as scan_repo.py
// without requiring Python or third-party Node.js packages.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCHEMA_VERSION = 7;
const DEFAULT_MAX_FILES = 50000;
const DEFAULT_MAX_DIRECTORIES = 50000;
const DEFAULT_MAX_DEPTH = 64;
const MAX_REPORTED_PATHS = 200;
const MAX_REPORTED_WARNINGS = 100;
const MAX_PARSED_MANIFESTS = 50;
const MAX_DECLARED_COMMANDS = 250;
const MAX_REPORTED_LANGUAGES = 20;
const MAX_INSTRUCTION_HEADINGS = 50;
const MAX_INSTRUCTION_REFERENCES = 100;
const MAX_INSTRUCTION_LINK_RESULTS = 20;
const MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION = 50;
const MAX_MANIFEST_COMMANDS = 100;
const MAX_TASK_TARGETS = 200;

const IGNORED_DIRECTORIES = new Set([
  '.git',
  '.hg',
  '.svn',
  '.cache',
  '.mypy_cache',
  '.next',
  '.nuxt',
  '.pytest_cache',
  '.ruff_cache',
  '.tox',
  '.turbo',
  '.venv',
  '__pycache__',
  'build',
  'coverage',
  'dist',
  'node_modules',
  'out',
  'target',
  'venv',
]);

const VENDORED_DIRECTORIES = new Set(['third_party', 'vendor']);

const INSTRUCTION_FILES = new Map([
  ['AGENTS.md', 'shared'],
  ['AGENTS.local.md', 'shared'],
  ['AGENTS.override.md', 'shared'],
  ['CLAUDE.md', 'claude'],
  ['CLAUDE.local.md', 'claude'],
  ['GEMINI.md', 'gemini'],
  ['REVIEW.md', 'claude-review'],
  ['.cursorrules', 'cursor'],
  ['.windsurfrules', 'windsurf'],
  ['copilot-instructions.md', 'copilot'],
]);

const MANIFEST_NAMES = new Set([
  'Cargo.toml',
  'Gemfile',
  'Package.swift',
  'build.gradle',
  'build.gradle.kts',
  'composer.json',
  'deno.json',
  'deno.jsonc',
  'go.mod',
  'mix.exs',
  'package.json',
  'pom.xml',
  'pyproject.toml',
  'requirements.txt',
]);

const LOCKFILE_NAMES = new Set([
  'Cargo.lock',
  'bun.lock',
  'bun.lockb',
  'composer.lock',
  'deno.lock',
  'Gemfile.lock',
  'go.sum',
  'package-lock.json',
  'pnpm-lock.yaml',
  'poetry.lock',
  'uv.lock',
  'yarn.lock',
]);

const TASK_RUNNER_NAMES = new Set([
  'GNUmakefile',
  'Justfile',
  'Makefile',
  'Taskfile.yaml',
  'Taskfile.yml',
  'justfile',
]);
const TASKFILE_NAMES = new Set(['taskfile.yaml', 'taskfile.yml']);

const QUALITY_CONFIG_NAMES = new Set([
  '.editorconfig',
  '.markdownlint-cli2.yaml',
  '.pre-commit-config.yaml',
  '.prettierrc',
  '.prettierrc.json',
  '.prettierrc.yaml',
  '.prettierrc.yml',
  '.yamllint.yaml',
  '.yamllint.yml',
  'biome.json',
  'eslint.config.js',
  'eslint.config.mjs',
  'lefthook.yml',
  'mypy.ini',
  'pytest.ini',
  'ruff.toml',
  'tox.ini',
  'tsconfig.json',
]);

const AGENT_CONFIG_NAMES = new Set([
  '.mcp.json',
  'config.toml',
  'config.yaml',
  'config.yml',
  'hooks.json',
  'openai.yaml',
  'requirements.toml',
  'settings.json',
  'settings.local.json',
]);

const DOC_BASENAMES = new Set([
  'changelog.md',
  'contributing.md',
  'development.md',
  'readme.md',
  'security.md',
]);

const HIGH_SIGNAL_DOC_WORDS = new Set([
  'adr',
  'architecture',
  'business',
  'decisions',
  'deployment',
  'design',
  'development',
  'domain',
  'glossary',
  'invariants',
  'observability',
  'operations',
  'product',
  'runbook',
  'testing',
  'verification',
]);

const TEST_DIRECTORY_NAMES = new Set([
  'e2e',
  'integration-tests',
  'integration_tests',
  'spec',
  'specs',
  'test',
  'tests',
]);

const LANGUAGE_EXTENSIONS = new Map([
  ['.c', 'C'],
  ['.cc', 'C++'],
  ['.cpp', 'C++'],
  ['.cs', 'C#'],
  ['.css', 'CSS'],
  ['.dart', 'Dart'],
  ['.ex', 'Elixir'],
  ['.exs', 'Elixir'],
  ['.go', 'Go'],
  ['.h', 'C/C++ Header'],
  ['.hpp', 'C++ Header'],
  ['.html', 'HTML'],
  ['.java', 'Java'],
  ['.js', 'JavaScript'],
  ['.jsx', 'JavaScript'],
  ['.kt', 'Kotlin'],
  ['.kts', 'Kotlin'],
  ['.lua', 'Lua'],
  ['.md', 'Markdown'],
  ['.php', 'PHP'],
  ['.ps1', 'PowerShell'],
  ['.py', 'Python'],
  ['.rb', 'Ruby'],
  ['.rs', 'Rust'],
  ['.scala', 'Scala'],
  ['.sh', 'Shell'],
  ['.sql', 'SQL'],
  ['.swift', 'Swift'],
  ['.ts', 'TypeScript'],
  ['.tsx', 'TypeScript'],
  ['.vue', 'Vue'],
]);

const VERIFICATION_NAME =
  /(?:^|[-_:])(test|check|lint|format|fmt|typecheck|type-check|build|verify|ci|e2e|smoke)(?:$|[-_:])/i;
const VERIFICATION_COMMAND =
  /(?:\b(?:ava|ctest|e2e|eslint|jest|mocha|mypy|prettier|pytest|ruff|shellcheck|tsc|unittest|vitest)\b|\bnode\s+--(?:check|test)\b|\bgit\s+diff\s+--check\b|(?:^|[^A-Za-z0-9-])(?:build|check|compile|fmt|format|lint|smoke|test|tests|typecheck|type-check|validate|verify)(?:$|[^A-Za-z0-9]))/i;
const COMMAND_START =
  /^(?:(?:[A-Za-z_][A-Za-z0-9_]*=(?:"[^"]*"|'[^']*'|\S+))\s+)*(?:env\s+)?(?:\.{0,2}[/\\][^\s]+|bash|bazel|buck2?|bun|bundle|cargo|cmake|cmd|composer|deno|docker|dotnet|eslint|git|go|gradle|java|just|make|maven|mise|mix|mvnw?|node|nox|npm|npx|nx|php|pnpm|poetry|powershell|prettier|pwsh|py|pytest|python(?:3(?:\.\d+)?)?|rake|ruby|ruff|shellcheck|sh|swift|task|tox|tsc|turbo|uv|vitest|xcodebuild|yarn|zsh)(?:\s|$)/i;
const FENCE = /^\s*(`{3,}|~{3,})(.*?)[ \t]*$/;
const COMMAND_FENCE_LANGUAGES = new Set([
  '',
  'bash',
  'batch',
  'cmd',
  'console',
  'powershell',
  'pwsh',
  'sh',
  'shell',
  'text',
  'txt',
  'zsh',
]);
const MARKDOWN_LINK = /(?<!!)\[[^\]]+\]\(([^)]+)\)/g;
const INSTRUCTION_IMPORT =
  /(?<![A-Za-z0-9_])@((?:~[/\\]|\.{0,2}[/\\]|[/\\])?[^\s`"'<>]+)/g;
const HEADING = /^(#{1,6})\s+(.+?)\s*$/;
const MAKE_TARGET = /^([A-Za-z0-9_.-]+)\s*:(?![=])/;
const JUST_TARGET = /^([A-Za-z_][A-Za-z0-9_-]*)(?:\s+[^:=]+)?\s*:(?![=])/;
const SENSITIVE_NAME =
  '(?:[A-Za-z0-9]+[_-])*(?:api[_-]?key|access[_-]?key|access[_-]?token|auth[_-]?token|authorization|client[_-]?secret|private[_-]?key|refresh[_-]?token|session[_-]?token|pat|token|password|passwd|secret|credential)s?(?:[_-][A-Za-z0-9]+)*';
const SENSITIVE_ASSIGNMENT = new RegExp(
  "\\b(" +
    SENSITIVE_NAME +
    ")\\s*=\\s*(?:\"[^\"]*\"|'[^']*'|[^\\s]+)",
  'gi',
);
const SENSITIVE_OPTION = new RegExp(
  "(--" +
    SENSITIVE_NAME +
    ")(?:\\s+)(?:\"[^\"]*\"|'[^']*'|[^\\s]+)",
  'gi',
);
const BASIC_AUTH_URL =
  /([A-Za-z][A-Za-z0-9+.-]*:\/\/)[^/\s:@]+:[^@\s/]+@/gi;
const BEARER_CREDENTIAL =
  /\b(Bearer)\s+(?:"[^"]*"|'[^']*'|[^\s"']+)/gi;

function rawCompare(left, right) {
  return Buffer.compare(Buffer.from(left, 'utf8'), Buffer.from(right, 'utf8'));
}

function asciiFold(value) {
  return value.replace(/[A-Z]/g, (character) => character.toLowerCase());
}

function portableNameCompare(left, right) {
  const folded = rawCompare(asciiFold(left), asciiFold(right));
  return folded || rawCompare(left, right);
}

function redactSensitiveText(value) {
  return value
    .replace(SENSITIVE_ASSIGNMENT, '$1=<redacted>')
    .replace(SENSITIVE_OPTION, '$1 <redacted>')
    .replace(BASIC_AUTH_URL, '$1<redacted>@')
    .replace(BEARER_CREDENTIAL, '$1 <redacted>');
}

function markdownProseLines(text) {
  const prose = [];
  let fenceCharacter = null;
  let fenceLength = 0;
  let inHtmlComment = false;

  for (const rawLine of splitLines(text)) {
    const stripped = rawLine.trim();
    if (fenceCharacter !== null) {
      const closingPrefix = fenceCharacter.repeat(fenceLength);
      if (
        stripped.startsWith(closingPrefix) &&
        Array.from(stripped).every(
          (character) => character === fenceCharacter,
        )
      ) {
        fenceCharacter = null;
        fenceLength = 0;
      }
      prose.push('');
      continue;
    }

    const pieces = [];
    let cursor = 0;
    while (cursor < rawLine.length) {
      if (inHtmlComment) {
        const end = rawLine.indexOf('-->', cursor);
        if (end < 0) {
          cursor = rawLine.length;
          break;
        }
        cursor = end + 3;
        inHtmlComment = false;
        continue;
      }
      const start = rawLine.indexOf('<!--', cursor);
      if (start < 0) {
        pieces.push(rawLine.slice(cursor));
        break;
      }
      pieces.push(rawLine.slice(cursor, start));
      cursor = start + 4;
      inHtmlComment = true;
    }

    const line = pieces.join('');
    const fence = FENCE.exec(line);
    if (fence) {
      fenceCharacter = fence[1][0];
      fenceLength = fence[1].length;
      prose.push('');
      continue;
    }
    prose.push(line.replace(/`+[^`]*`+/g, ''));
  }
  return prose;
}

function documentedVerificationCommands(value) {
  const commands = [];
  const allCommands = [];
  let fenceCharacter = null;
  let fenceLength = 0;
  let inspectFence = false;
  let pendingCommand = null;
  let pendingLine = 0;

  function hasContinuation(candidate) {
    const match = candidate.trimEnd().match(/\\+$/);
    return match !== null && match[0].length % 2 === 1;
  }

  for (const [index, line] of splitLines(value).entries()) {
    const stripped = line.trim();
    if (fenceCharacter === null) {
      const match = FENCE.exec(line);
      if (!match) {
        continue;
      }
      fenceCharacter = match[1][0];
      fenceLength = match[1].length;
      const info = (match[2] || '').trim();
      const language = (info.split(/\s+/, 1)[0] || '').replace(/^[{.]+|[}]+$/g, '');
      inspectFence = COMMAND_FENCE_LANGUAGES.has(language.toLowerCase());
      continue;
    }

    const closingPrefix = fenceCharacter.repeat(fenceLength);
    if (
      stripped.startsWith(closingPrefix) &&
      Array.from(stripped).every((character) => character === fenceCharacter)
    ) {
      fenceCharacter = null;
      fenceLength = 0;
      inspectFence = false;
      pendingCommand = null;
      pendingLine = 0;
      continue;
    }
    if (!inspectFence) {
      continue;
    }

    let candidate = stripped;
    if (candidate.startsWith('$ ') || candidate.startsWith('> ')) {
      candidate = candidate.slice(2).trimStart();
    }
    if (
      !candidate ||
      candidate.startsWith('#') ||
      candidate.startsWith('//') ||
      candidate.startsWith('- ') ||
      candidate.startsWith('* ')
    ) {
      pendingCommand = null;
      pendingLine = 0;
      continue;
    }

    const commandLine = pendingLine || index + 1;
    if (pendingCommand !== null) {
      candidate = pendingCommand + ' ' + candidate;
    }

    if (hasContinuation(candidate)) {
      pendingCommand = candidate.trimEnd().slice(0, -1).trimEnd();
      pendingLine = commandLine;
      if (pendingCommand.length > 1000) {
        pendingCommand = null;
        pendingLine = 0;
      }
      continue;
    }

    pendingCommand = null;
    pendingLine = 0;
    if (
      candidate.length > 1000 ||
      !COMMAND_START.test(candidate) ||
      !VERIFICATION_COMMAND.test(candidate)
    ) {
      continue;
    }
    const command = {
      line: commandLine,
      definition: redactSensitiveText(candidate),
    };
    if (commands.length < MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION) {
      commands.push(command);
    }
    allCommands.push(command);
  }
  return { reported: commands, all: allCommands };
}

function sortedUnique(values, limit = undefined) {
  const sorted = Array.from(new Set(values)).sort(rawCompare);
  return limit === undefined ? sorted : sorted.slice(0, limit);
}

function relativePath(target, root) {
  return path.relative(root, target).split(path.sep).join('/');
}

function relativeParts(relative) {
  return relative.split('/').filter(Boolean);
}

function basename(relative) {
  const parts = relativeParts(relative);
  return parts.length ? parts[parts.length - 1] : '';
}

function suffix(relative) {
  return path.posix.extname(relative);
}

function isWithinRoot(target, root) {
  const relative = path.relative(root, target);
  return (
    relative === '' ||
    (!relative.startsWith('..' + path.sep) &&
      relative !== '..' &&
      !path.isAbsolute(relative))
  );
}

function resolveWithExistingAncestors(target) {
  const absolute = path.resolve(target);
  const missingParts = [];
  let current = absolute;
  while (true) {
    try {
      return path.join(fs.realpathSync(current), ...missingParts);
    } catch {
      const parent = path.dirname(current);
      if (parent === current) {
        return absolute;
      }
      missingParts.unshift(path.basename(current));
      current = parent;
    }
  }
}

function canonicalPathKey(target) {
  return process.platform === 'win32' ? target.toLowerCase() : target;
}

function pathIdentity(target) {
  try {
    const metadata = fs.statSync(target, { bigint: true });
    return metadata.dev.toString() + ':' + metadata.ino.toString();
  } catch {
    return null;
  }
}

function isSameOrDescendantExisting(candidate, ancestor) {
  const ancestorIdentity = pathIdentity(ancestor);
  if (ancestorIdentity === null) {
    return false;
  }
  let current = candidate;
  while (true) {
    if (pathIdentity(current) === ancestorIdentity) {
      return true;
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return false;
    }
    current = parent;
  }
}

function normalizeExcludedPaths(root, values) {
  const candidates = new Map();
  for (const value of values) {
    const expanded = expandUser(value);
    const candidate = path.isAbsolute(expanded)
      ? expanded
      : path.join(root, expanded);
    let resolved;
    try {
      resolved = fs.realpathSync(candidate);
    } catch (error) {
      throw new Error('Excluded path does not exist: ' + candidate);
    }
    if (!isWithinRoot(resolved, root)) {
      throw new Error(
        'Excluded path is outside the repository root: ' + resolved,
      );
    }
    const identity = pathIdentity(resolved);
    if (
      canonicalPathKey(resolved) === canonicalPathKey(root) ||
      identity === pathIdentity(root)
    ) {
      throw new Error('Repository root cannot be excluded');
    }
    if (identity === null) {
      throw new Error('Excluded path cannot be inspected: ' + resolved);
    }
    if (!candidates.has(identity)) {
      candidates.set(identity, resolved);
    }
  }

  const ordered = Array.from(candidates.values()).sort((left, right) => {
    const leftRelative = relativePath(left, root);
    const rightRelative = relativePath(right, root);
    return (
      relativeParts(leftRelative).length - relativeParts(rightRelative).length ||
      portableNameCompare(leftRelative, rightRelative)
    );
  });
  const retained = [];
  for (const candidate of ordered) {
    if (
      retained.some((parent) => isSameOrDescendantExisting(candidate, parent))
    ) {
      continue;
    }
    retained.push(candidate);
  }
  return retained.sort((left, right) =>
    portableNameCompare(relativePath(left, root), relativePath(right, root)),
  );
}

function resolvedTargetIsOutOfScope(
  target,
  root,
  excludedPaths,
  maxDepth,
  includeVendored,
) {
  if (!isWithinRoot(target, root)) {
    return true;
  }
  if (
    excludedPaths.some((excluded) =>
      isSameOrDescendantExisting(target, excluded),
    )
  ) {
    return true;
  }
  const parts = relativeParts(relativePath(target, root));
  const parentParts = parts.slice(0, -1).map((part) => part.toLowerCase());
  if (parentParts.some((part) => IGNORED_DIRECTORIES.has(part))) {
    return true;
  }
  if (
    !includeVendored &&
    parentParts.some((part) => VENDORED_DIRECTORIES.has(part))
  ) {
    return true;
  }
  return parentParts.length > maxDepth;
}

function splitLines(text) {
  if (!text) {
    return [];
  }
  const lines = text.split(/\r\n|[\n\r\v\f\x1c-\x1e\u0085\u2028\u2029]/);
  if (lines.length && lines[lines.length - 1] === '') {
    lines.pop();
  }
  return lines;
}

function walkRepository(
  root,
  maxFiles,
  maxDirectories,
  maxDepth,
  includeVendored,
  excludedPaths,
) {
  const files = [];
  const skipped = new Set();
  const skippedSymlinks = new Set();
  const skippedSpecialFiles = new Set();
  const errors = [];
  const limitReasons = new Set();
  let truncated = false;
  let directoriesSeen = 0;
  let stopScan = false;
  const excludedIdentities = new Set(
    excludedPaths.map(pathIdentity).filter((identity) => identity !== null),
  );

  function walk(current) {
    if (stopScan) {
      return;
    }
    if (directoriesSeen >= maxDirectories) {
      skipped.add(relativePath(current, root));
      truncated = true;
      limitReasons.add('max_directories');
      stopScan = true;
      return;
    }
    const relativeCurrent = relativePath(current, root);
    const depth = relativeCurrent ? relativeParts(relativeCurrent).length : 0;

    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch (error) {
      errors.push('Unable to scan directory: ' + (relativeCurrent || '.'));
      return;
    }
    directoriesSeen += 1;

    entries.sort((left, right) => portableNameCompare(left.name, right.name));
    const directories = [];
    const regularEntries = [];

    for (const entry of entries) {
      const entryPath = path.join(current, entry.name);
      if (excludedIdentities.has(pathIdentity(entryPath))) {
        continue;
      }
      if (entry.isSymbolicLink()) {
        let resolved;
        let targetStat;
        try {
          resolved = fs.realpathSync(entryPath);
          targetStat = fs.statSync(resolved);
        } catch {
          skippedSymlinks.add(relativePath(entryPath, root));
          continue;
        }
        if (targetStat.isDirectory()) {
          skippedSymlinks.add(relativePath(entryPath, root));
          continue;
        }
        if (targetStat.isFile()) {
          if (
            resolvedTargetIsOutOfScope(
              resolved,
              root,
              excludedPaths,
              maxDepth,
              includeVendored,
            )
          ) {
            skippedSymlinks.add(relativePath(entryPath, root));
            continue;
          }
          regularEntries.push(entry);
        } else if (targetStat.isDirectory()) {
          skippedSymlinks.add(relativePath(entryPath, root));
        } else {
          skippedSpecialFiles.add(relativePath(entryPath, root));
        }
      } else if (entry.isDirectory()) {
        const folded = entry.name.toLowerCase();
        const vendored = VENDORED_DIRECTORIES.has(folded);
        if (
          IGNORED_DIRECTORIES.has(folded) ||
          (vendored && !includeVendored)
        ) {
          skipped.add(relativePath(entryPath, root));
          continue;
        }
        directories.push(entry);
      } else if (entry.isFile()) {
        regularEntries.push(entry);
      } else {
        skippedSpecialFiles.add(relativePath(entryPath, root));
      }
    }

    let descend = true;
    if (depth >= maxDepth && directories.length) {
      for (const entry of directories) {
        skipped.add(relativePath(path.join(current, entry.name), root));
      }
      truncated = true;
      limitReasons.add('max_depth');
      descend = false;
    }

    for (const entry of regularEntries) {
      if (files.length >= maxFiles) {
        truncated = true;
        limitReasons.add('max_files');
        stopScan = true;
        return;
      }
      files.push(path.join(current, entry.name));
    }

    if (!descend) {
      return;
    }

    for (const entry of directories) {
      walk(path.join(current, entry.name));
      if (stopScan) {
        return;
      }
    }
  }

  walk(root);
  return {
    files,
    skipped: sortedUnique(skipped),
    skippedSymlinks: sortedUnique(skippedSymlinks),
    skippedSpecialFiles: sortedUnique(skippedSpecialFiles),
    warnings: errors,
    truncated,
    directoriesSeen,
    limitReasons: sortedUnique(limitReasons),
  };
}

function isCiPath(relative) {
  const parts = relativeParts(relative).map((part) => part.toLowerCase());
  const name = basename(relative).toLowerCase();
  const extension = suffix(relative).toLowerCase();
  return (
    (parts.length === 3 &&
      parts[0] === '.github' &&
      parts[1] === 'workflows' &&
      new Set(['.yaml', '.yml']).has(extension)) ||
    (parts.length === 2 &&
      parts[0] === '.circleci' &&
      new Set(['config.yaml', 'config.yml']).has(parts[1])) ||
    (parts.length >= 2 &&
      new Set(['.buildkite', '.gitlab']).has(parts[0]) &&
      new Set(['.json', '.yaml', '.yml']).has(extension)) ||
    (parts.length === 1 &&
      new Set([
        '.gitlab-ci.yml',
        'azure-pipelines.yml',
        'bitbucket-pipelines.yml',
        'jenkinsfile',
      ]).has(name))
  );
}

function isTestPath(relative) {
  const parts = new Set(
    relativeParts(relative)
      .slice(0, -1)
      .map((part) => part.toLowerCase()),
  );
  const name = basename(relative).toLowerCase();
  return (
    Array.from(TEST_DIRECTORY_NAMES).some((part) => parts.has(part)) ||
    /(?:^|[._-])(test|spec)(?:[._-]|$)/.test(name)
  );
}

function isHighSignalDoc(relative) {
  const extension = suffix(relative).toLowerCase();
  if (!new Set(['.md', '.mdx', '.rst']).has(extension)) {
    return false;
  }
  const name = basename(relative).toLowerCase();
  if (DOC_BASENAMES.has(name) || name.startsWith('readme.')) {
    return true;
  }
  const parts = new Set(relativeParts(relative).map((part) => part.toLowerCase()));
  const signalWords = new Set(
    relativeParts(relative).flatMap((part) => part.toLowerCase().split(/[-_.]/)),
  );
  return (
    (relativeParts(relative).length === 1 || parts.has('docs')) &&
    Array.from(signalWords).some((word) => HIGH_SIGNAL_DOC_WORDS.has(word))
  );
}

function hasArchitectureOrTestingSignal(relative) {
  return relativeParts(relative)
    .flatMap((part) => part.toLowerCase().split(/[-_.]/))
    .some((word) => HIGH_SIGNAL_DOC_WORDS.has(word));
}

function containsPathPair(parts, first, second) {
  return parts.some(
    (part, index) => part === first && parts[index + 1] === second,
  );
}

function instructionKind(relative) {
  const name = basename(relative);
  const parts = relativeParts(relative);
  const foldedParts = parts.map((part) => part.toLowerCase());
  if (
    name === 'AGENTS.md' &&
    foldedParts[foldedParts.length - 2] === '.kimi'
  ) {
    return 'kimi';
  }
  if (name === 'agents.md') {
    return 'kimi';
  }
  if (INSTRUCTION_FILES.has(name)) {
    if (
      name === 'copilot-instructions.md' &&
      !relativeParts(relative).includes('.github')
    ) {
      return null;
    }
    if (name === 'REVIEW.md' && relativeParts(relative).length !== 1) {
      return null;
    }
    return INSTRUCTION_FILES.get(name);
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    foldedParts.length >= 3 &&
    foldedParts[0] === '.claude' &&
    foldedParts[1] === 'rules'
  ) {
    return 'claude-rule';
  }
  if (
    name.toLowerCase().endsWith('.instructions.md') &&
    foldedParts.length >= 3 &&
    foldedParts[0] === '.github' &&
    foldedParts[1] === 'instructions'
  ) {
    return 'copilot-path';
  }
  if (
    suffix(relative).toLowerCase() === '.mdc' &&
    containsPathPair(foldedParts, '.cursor', 'rules')
  ) {
    return 'cursor';
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    containsPathPair(foldedParts, '.windsurf', 'rules')
  ) {
    return 'windsurf-rule';
  }
  if (
    name.toLowerCase() === 'bugbot.md' &&
    parts.length >= 2 &&
    parts[parts.length - 2].toLowerCase() === '.cursor'
  ) {
    return 'cursor-review';
  }
  return null;
}

function agentDefinitionKind(relative) {
  const parts = relativeParts(relative).map((part) => part.toLowerCase());
  if (suffix(relative).toLowerCase() === '.md' && parts.length >= 3) {
    if (parts[0] === '.claude' && parts[1] === 'agents') {
      return 'claude';
    }
    if (parts[0] === '.gemini' && parts[1] === 'agents') {
      return 'gemini';
    }
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    parts.length >= 3 &&
    parts[0] === '.github' &&
    parts[1] === 'agents'
  ) {
    return 'copilot';
  }
  return null;
}

function promptKind(relative) {
  const name = basename(relative).toLowerCase();
  const parts = relativeParts(relative).map((part) => part.toLowerCase());
  if (parts.length < 3) {
    return null;
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    parts[0] === '.claude' &&
    parts[1] === 'commands'
  ) {
    return 'claude';
  }
  if (
    name.endsWith('.prompt.md') &&
    parts[0] === '.github' &&
    parts[1] === 'prompts'
  ) {
    return 'copilot';
  }
  if (
    suffix(relative).toLowerCase() === '.toml' &&
    parts[0] === '.gemini' &&
    parts[1] === 'commands'
  ) {
    return 'gemini';
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    parts[0] === '.cursor' &&
    parts[1] === 'commands'
  ) {
    return 'cursor';
  }
  if (
    suffix(relative).toLowerCase() === '.md' &&
    containsPathPair(parts, '.windsurf', 'workflows')
  ) {
    return 'windsurf';
  }
  return null;
}

function isSkillPath(relative) {
  const parts = relativeParts(relative);
  return (
    basename(relative) === 'SKILL.md' &&
    (parts.length === 1 ||
      parts.slice(0, -1).some((part) => part.toLowerCase() === 'skills'))
  );
}

function isAgentConfig(relative) {
  const parts = relativeParts(relative);
  if (!parts.length) {
    return false;
  }
  const first = parts[0].toLowerCase();
  if (
    !new Set([
      '.agents',
      '.claude',
      '.codex',
      '.cursor',
      '.gemini',
      '.kimi',
      '.windsurf',
      'agents',
    ]).has(first)
  ) {
    return false;
  }
  return (
    AGENT_CONFIG_NAMES.has(basename(relative)) ||
    new Set(['.rules', '.toml']).has(suffix(relative).toLowerCase())
  );
}

function readText(target, root, maxBytes = 1000000) {
  let descriptor = null;
  try {
    const resolved = fs.realpathSync(target);
    if (!isWithinRoot(resolved, root)) {
      return {
        text: null,
        warning:
          'Skipped ' +
          path.basename(target) +
          ': path resolves outside repository',
      };
    }
    const metadata = fs.statSync(resolved);
    if (!metadata.isFile()) {
      return {
        text: null,
        warning: 'Skipped ' + path.basename(target) + ': not a regular file',
      };
    }
    const size = metadata.size;
    if (size > maxBytes) {
      return {
        text: null,
        warning:
          'Skipped ' +
          path.basename(target) +
          ': file is larger than ' +
          maxBytes +
          ' bytes',
      };
    }
    descriptor = fs.openSync(
      resolved,
      fs.constants.O_RDONLY | (fs.constants.O_NONBLOCK || 0),
    );
    if (!fs.fstatSync(descriptor).isFile()) {
      return {
        text: null,
        warning: 'Skipped ' + path.basename(target) + ': not a regular file',
      };
    }
    const chunks = [];
    let bytesRead = 0;
    while (bytesRead <= maxBytes) {
      const buffer = Buffer.alloc(Math.min(65536, maxBytes + 1 - bytesRead));
      const count = fs.readSync(descriptor, buffer, 0, buffer.length, null);
      if (count === 0) {
        break;
      }
      chunks.push(buffer.subarray(0, count));
      bytesRead += count;
    }
    if (bytesRead > maxBytes) {
      return {
        text: null,
        warning:
          'Skipped ' +
          path.basename(target) +
          ': file is larger than ' +
          maxBytes +
          ' bytes',
      };
    }
    let text = Buffer.concat(chunks, bytesRead).toString('utf8');
    if (text.startsWith('\uFEFF')) {
      text = text.slice(1);
    }
    return { text, warning: null };
  } catch (error) {
    return {
      text: null,
      warning: 'Unable to read ' + target + ': ' + (error.message || String(error)),
    };
  } finally {
    if (descriptor !== null) {
      try {
        fs.closeSync(descriptor);
      } catch {
        // Preserve the scan result; close failures do not change the evidence.
      }
    }
  }
}

function extractMarkdownTarget(rawTarget) {
  let target = rawTarget.trim();
  if (target.startsWith('<') && target.includes('>')) {
    target = target.slice(1, target.indexOf('>'));
  } else {
    target = target.split(/\s+/, 1)[0];
  }
  try {
    target = decodeURIComponent(target);
  } catch {
    // Keep malformed percent escapes as literal text, matching a tolerant scan.
  }
  target = target.trim();
  if (
    !target ||
    target.startsWith('#') ||
    /^[A-Za-z][A-Za-z0-9+.-]*:/.test(target) ||
    target.startsWith('//')
  ) {
    return null;
  }
  return target.split('#', 1)[0].split('?', 1)[0];
}

function instructionImportTargets(text) {
  const targets = [];
  for (const line of markdownProseLines(text)) {
    INSTRUCTION_IMPORT.lastIndex = 0;
    let match;
    while ((match = INSTRUCTION_IMPORT.exec(line)) !== null) {
      const target = match[1].replace(/[.,;:!?\)\]\}]+$/, '');
      if (target) {
        targets.push(target);
      }
    }
  }
  return targets;
}

function resolveInstructionTarget(source, target) {
  const normalized = target.replace(/[\\/]/g, path.sep);
  let candidate;
  if (normalized === '~' || normalized.startsWith('~' + path.sep)) {
    candidate = expandUser(normalized);
  } else if (path.isAbsolute(normalized)) {
    candidate = normalized;
  } else {
    candidate = path.join(path.dirname(source), normalized);
  }
  return resolveWithExistingAncestors(candidate);
}

function looksLikeInstructionImport(target, candidate) {
  const normalized = target.replace(/\\/g, '/');
  if (
    normalized.startsWith('./') ||
    normalized.startsWith('../') ||
    normalized.startsWith('~/') ||
    normalized.startsWith('/') ||
    /^[A-Za-z]:\//.test(normalized)
  ) {
    return true;
  }
  try {
    if (fs.existsSync(candidate)) {
      return true;
    }
  } catch {
    // Continue with the conservative lexical check below.
  }
  const parts = normalized.replace(/\/+$/, '').split('/');
  const leaf = parts[parts.length - 1] || '';
  return leaf !== '.' && leaf !== '..' && leaf.includes('.');
}

function summarizeInstruction(target, root, kind) {
  const warnings = [];
  let size = -1;
  try {
    size = fs.lstatSync(target).size;
  } catch {
    size = -1;
  }

  const read = readText(target, root, 512000);
  if (read.warning) {
    warnings.push(read.warning);
  }
  const headings = [];
  const brokenLinks = [];
  const outsideLinks = [];
  let imports = [];
  const brokenImports = [];
  const outsideImports = [];
  const lines = read.text === null ? [] : splitLines(read.text);
  const documentedCommandResult =
    read.text === null
      ? { reported: [], all: [] }
      : documentedVerificationCommands(read.text);
  const documentedCommands = documentedCommandResult.reported;
  let headingCount = 0;
  let relativeLinkTargetCount = 0;

  if (read.text !== null) {
    const proseLines = markdownProseLines(read.text);
    const proseText = proseLines.join('\n');
    for (const line of proseLines) {
      const match = HEADING.exec(line);
      if (match) {
        headingCount += 1;
        if (headings.length < MAX_INSTRUCTION_HEADINGS) {
          headings.push(redactSensitiveText(match[2].trim()));
        }
      }
    }

    MARKDOWN_LINK.lastIndex = 0;
    let match;
    const linkMatches = Array.from(proseText.matchAll(MARKDOWN_LINK));
    relativeLinkTargetCount = linkMatches.length;
    for (match of linkMatches.slice(0, MAX_INSTRUCTION_REFERENCES)) {
      const linkTarget = extractMarkdownTarget(match[1]);
      if (!linkTarget) {
        continue;
      }
      const candidate = resolveWithExistingAncestors(
        path.resolve(path.dirname(target), linkTarget),
      );
      if (!isWithinRoot(candidate, root)) {
        outsideLinks.push(linkTarget);
      } else if (!fs.existsSync(candidate)) {
        brokenLinks.push(linkTarget);
      }
    }
    if (
      kind === 'shared' ||
      kind === 'claude' ||
      kind === 'gemini' ||
      kind === 'copilot'
    ) {
      for (const importTarget of sortedUnique(instructionImportTargets(read.text))) {
        const candidate = resolveInstructionTarget(target, importTarget);
        if (!looksLikeInstructionImport(importTarget, candidate)) {
          continue;
        }
        imports.push(importTarget);
        if (!isWithinRoot(candidate, root)) {
          outsideImports.push(importTarget);
        } else if (!fs.existsSync(candidate)) {
          brokenImports.push(importTarget);
        }
      }
    }
  }

  return {
    summary: {
      path: relativePath(target, root),
      kind,
      bytes: size,
      lines: lines.length,
      symlink: fs.lstatSync(target).isSymbolicLink(),
      headings,
      documented_verification_commands: documentedCommands,
      broken_relative_links: sortedUnique(
        brokenLinks,
        MAX_INSTRUCTION_LINK_RESULTS,
      ),
      relative_links_outside_repository: sortedUnique(
        outsideLinks,
        MAX_INSTRUCTION_LINK_RESULTS,
      ),
      imports: imports.slice(0, MAX_INSTRUCTION_REFERENCES),
      broken_imports: sortedUnique(brokenImports, MAX_INSTRUCTION_REFERENCES),
      imports_outside_repository: sortedUnique(
        outsideImports,
        MAX_INSTRUCTION_REFERENCES,
      ),
      headings_total: headingCount,
      documented_verification_commands_total:
        documentedCommandResult.all.length,
      relative_link_targets_total: relativeLinkTargetCount,
      broken_relative_links_total: new Set(brokenLinks).size,
      relative_links_outside_repository_total: new Set(outsideLinks).size,
      imports_total: imports.length,
      broken_imports_total: new Set(brokenImports).size,
      imports_outside_repository_total: new Set(outsideImports).size,
      _all_documented_verification_commands: documentedCommandResult.all,
    },
    warnings,
  };
}

function parsePackageScripts(target, root, scannedLockfiles) {
  const read = readText(target, root, 2000000);
  if (read.warning) {
    return { parsed: null, warning: read.warning };
  }
  let data;
  try {
    data = JSON.parse(read.text || '{}');
  } catch {
    return {
      parsed: null,
      warning:
        'Unable to parse ' +
        relativePath(target, root) +
        ': invalid JSON',
    };
  }
  if (
    !data ||
    typeof data !== 'object' ||
    Array.isArray(data) ||
    !data.scripts ||
    typeof data.scripts !== 'object' ||
    Array.isArray(data.scripts)
  ) {
    return { parsed: null, warning: null };
  }
  const allScripts = {};
  for (const name of Object.keys(data.scripts).sort(rawCompare)) {
    if (typeof data.scripts[name] === 'string') {
      allScripts[name] = redactSensitiveText(data.scripts[name]);
    }
  }
  const scripts = {};
  for (const name of Object.keys(allScripts).slice(0, MAX_MANIFEST_COMMANDS)) {
    scripts[name] = allScripts[name];
  }
  return {
    parsed: {
      source: relativePath(target, root),
      package_manager: detectPackageManager(
        path.dirname(target),
        root,
        scannedLockfiles,
      ),
      scripts,
      scripts_total: Object.keys(allScripts).length,
      _all_scripts: allScripts,
    },
    warning: null,
  };
}

function detectPackageManager(directory, root, scannedLockfiles) {
  let current = directory;
  while (true) {
    for (const [name, manager] of [
      ['pnpm-lock.yaml', 'pnpm'],
      ['yarn.lock', 'yarn'],
      ['bun.lock', 'bun'],
      ['bun.lockb', 'bun'],
      ['package-lock.json', 'npm'],
    ]) {
      if (scannedLockfiles.has(relativePath(path.join(current, name), root))) {
        return manager;
      }
    }
    if (current === root) {
      break;
    }
    const parent = path.dirname(current);
    if (!isWithinRoot(parent, root)) {
      break;
    }
    current = parent;
  }
  return null;
}

function parseTaskfileTargets(text) {
  const targets = new Set();
  let inTasks = false;
  let targetIndent = null;

  for (const line of splitLines(text)) {
    const stripped = line.trim();
    if (!inTasks) {
      if (line === line.trimStart() && /^tasks\s*:\s*(?:#.*)?$/.test(line)) {
        inTasks = true;
      }
      continue;
    }
    if (!stripped || stripped.startsWith('#')) {
      continue;
    }
    if (line.startsWith('\t') || line === line.trimStart()) {
      break;
    }

    const indent = line.length - line.trimStart().length;
    if (targetIndent === null) {
      targetIndent = indent;
    }
    const match = /^ +([A-Za-z0-9_.-]+)\s*:/.exec(line);
    if (!match) {
      continue;
    }
    if (indent === targetIndent) {
      targets.add(match[1]);
    }
  }
  return sortedUnique(targets);
}

function parseTaskTargets(target, root) {
  const read = readText(target, root);
  if (read.warning) {
    return { parsed: null, warning: read.warning };
  }
  const name = path.basename(target).toLowerCase();
  let runner;
  let targets;
  if (TASKFILE_NAMES.has(name)) {
    runner = 'task';
    targets = parseTaskfileTargets(read.text || '');
  } else {
    runner = name === 'justfile' ? 'just' : 'make';
    const pattern = runner === 'just' ? JUST_TARGET : MAKE_TARGET;
    const targetSet = new Set();
    for (const line of splitLines(read.text || '')) {
      if (line.startsWith(' ') || line.startsWith('\t') || line.startsWith('#')) {
        continue;
      }
      const match = pattern.exec(line);
      if (match && !match[1].startsWith('.')) {
        targetSet.add(match[1]);
      }
    }
    targets = sortedUnique(targetSet);
  }
  if (!targets.length) {
    return { parsed: null, warning: null };
  }
  return {
    parsed: {
      source: relativePath(target, root),
      runner,
      targets: targets.slice(0, MAX_TASK_TARGETS),
      targets_total: targets.length,
      _all_targets: targets,
    },
    warning: null,
  };
}

function stripTomlComment(line) {
  let quote = null;
  let escaped = false;
  for (let index = 0; index < line.length; index += 1) {
    const character = line[index];
    if (quote === '"') {
      if (escaped) {
        escaped = false;
      } else if (character === '\\') {
        escaped = true;
      } else if (character === '"') {
        quote = null;
      }
    } else if (quote === "'") {
      if (character === "'") {
        quote = null;
      }
    } else if (character === '"' || character === "'") {
      quote = character;
    } else if (character === '#') {
      return line.slice(0, index).trim();
    }
  }
  return line.trim();
}

function parseTomlString(raw) {
  const value = raw.trim();
  if (value.length >= 2 && value.startsWith('"') && value.endsWith('"')) {
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }
  if (value.length >= 2 && value.startsWith("'") && value.endsWith("'")) {
    return value.slice(1, -1);
  }
  return null;
}

function parseTomlKey(raw) {
  const key = raw.trim();
  if (/^[A-Za-z0-9_-]+$/.test(key)) {
    return key;
  }
  return parseTomlString(key);
}

function parsePythonScripts(target, root) {
  const read = readText(target, root, 2000000);
  if (read.warning) {
    return { parsed: null, warning: read.warning };
  }

  const scripts = {};
  let inScripts = false;
  let sawScripts = false;
  for (const originalLine of splitLines(read.text || '')) {
    const line = stripTomlComment(originalLine);
    if (!line) {
      continue;
    }
    const table = /^\[\s*([^\]]+?)\s*\]$/.exec(line);
    if (table) {
      inScripts = table[1].trim() === 'project.scripts';
      sawScripts = sawScripts || inScripts;
      continue;
    }
    if (!inScripts) {
      continue;
    }
    const assignment = /^(.+?)\s*=\s*(.+)$/.exec(line);
    if (!assignment) {
      return {
        parsed: null,
        warning:
          'Unable to parse ' +
          relativePath(target, root) +
          ': unsupported project.scripts entry',
      };
    }
    const key = parseTomlKey(assignment[1]);
    const value = parseTomlString(assignment[2]);
    if (key === null || value === null) {
      return {
        parsed: null,
        warning:
          'Unable to parse ' +
          relativePath(target, root) +
          ': unsupported project.scripts entry',
      };
    }
    scripts[key] = redactSensitiveText(value);
  }

  if (!sawScripts || !Object.keys(scripts).length) {
    return { parsed: null, warning: null };
  }
  const sortedScripts = {};
  for (const name of Object.keys(scripts).sort(rawCompare)) {
    sortedScripts[name] = scripts[name];
  }
  const reportedScripts = {};
  for (const name of Object.keys(sortedScripts).slice(0, MAX_MANIFEST_COMMANDS)) {
    reportedScripts[name] = sortedScripts[name];
  }
  return {
    parsed: {
      source: relativePath(target, root),
      scripts: reportedScripts,
      scripts_total: Object.keys(sortedScripts).length,
      _all_scripts: sortedScripts,
    },
    warning: null,
  };
}

function resolveGitExecutable(root) {
  const pathValue = process.env.PATH || process.env.Path || '';
  const extensions =
    process.platform === 'win32'
      ? (process.env.PATHEXT || '.COM;.EXE;.BAT;.CMD')
          .split(';')
          .filter(Boolean)
      : [''];
  for (const directory of pathValue.split(path.delimiter)) {
    const base = directory || process.cwd();
    for (const extension of extensions) {
      const candidate = path.resolve(base, 'git' + extension);
      try {
        const metadata = fs.statSync(candidate);
        fs.accessSync(candidate, fs.constants.X_OK);
        if (!metadata.isFile()) {
          continue;
        }
        const resolved = fs.realpathSync(candidate);
        if (isWithinRoot(resolved, root)) {
          return {
            executable: null,
            failureReason: 'git_executable_inside_target',
          };
        }
        return { executable: resolved, failureReason: null };
      } catch {
        // Continue with the next executable suffix or PATH entry.
      }
    }
  }
  return { executable: null, failureReason: 'git_executable_unavailable' };
}

function runGit(root, args, resolution) {
  if (resolution.executable === null) {
    return {
      returncode: 127,
      stdout: '',
      stderr: resolution.failureReason || '',
      failure_reason: resolution.failureReason || 'git_executable_unavailable',
    };
  }
  const environment = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (!key.toUpperCase().startsWith('GIT_') && value !== undefined) {
      environment[key] = value;
    }
  }
  environment.GIT_OPTIONAL_LOCKS = '0';
  environment.GIT_TERMINAL_PROMPT = '0';
  environment.GIT_PAGER = 'cat';
  const result = spawnSync(
    resolution.executable,
    [
      '-c',
      'core.fsmonitor=false',
      '-c',
      'core.untrackedCache=false',
      '-C',
      root,
      ...args,
    ],
    {
      encoding: 'utf8',
      env: environment,
      timeout: 5000,
      windowsHide: true,
    },
  );
  let failureReason = null;
  if (result.error && result.error.code === 'ENOENT') {
    failureReason = 'git_executable_unavailable';
  } else if (result.error && result.error.code === 'ETIMEDOUT') {
    failureReason = 'git_identity_query_timed_out';
  } else if (result.error) {
    failureReason = 'git_identity_query_failed';
  }
  return {
    returncode: typeof result.status === 'number' ? result.status : 1,
    stdout: result.stdout || '',
    stderr:
      result.stderr ||
      (result.error ? result.error.message || String(result.error) : ''),
    failure_reason: failureReason,
  };
}

function hasGitMarker(root) {
  let current = root;
  while (true) {
    try {
      fs.lstatSync(path.join(current, '.git'));
      return true;
    } catch (error) {
      if (!error || error.code !== 'ENOENT') {
        return true;
      }
    }
    const parent = path.dirname(current);
    if (parent === current) {
      return false;
    }
    current = parent;
  }
}

function gitMetadata(root) {
  const gitResolution = resolveGitExecutable(root);
  const topLevel = runGit(
    root,
    ['rev-parse', '--show-toplevel'],
    gitResolution,
  );
  if (topLevel.returncode !== 0) {
    if (hasGitMarker(root)) {
      return {
        is_repository: null,
        repository_state: 'unverified',
        repository_state_reason:
          topLevel.failure_reason || 'git_identity_query_failed',
        worktree_state: 'unverified',
        worktree_state_reason: 'repository_identity_unverified',
        dirty_path_count: null,
        dirty_paths: [],
        dirty_paths_truncated: null,
      };
    }
    return {
      is_repository: false,
      repository_state: 'not_repository',
      worktree_state: 'not_applicable',
      dirty_path_count: null,
      dirty_paths: [],
      dirty_paths_truncated: null,
    };
  }

  let gitRoot;
  try {
    gitRoot = fs.realpathSync(topLevel.stdout.trim());
  } catch {
    gitRoot = path.resolve(topLevel.stdout.trim());
  }
  if (!isWithinRoot(root, gitRoot)) {
    return {
      is_repository: null,
      repository_state: 'unverified',
      repository_state_reason: 'git_root_outside_target_scope',
      worktree_state: 'unverified',
      worktree_state_reason: 'git_root_outside_target_scope',
      dirty_path_count: null,
      dirty_paths: [],
      dirty_paths_truncated: null,
    };
  }
  let branch = runGit(
    root,
    ['symbolic-ref', '--quiet', '--short', 'HEAD'],
    gitResolution,
  );
  if (branch.returncode !== 0) {
    branch = runGit(root, ['rev-parse', '--short', 'HEAD'], gitResolution);
  }
  return {
    is_repository: true,
    repository_state: 'verified',
    root: gitRoot,
    target_matches_git_root: gitRoot === root,
    branch_or_commit:
      branch.returncode === 0 ? branch.stdout.trim() || null : null,
    worktree_state: 'unverified',
    worktree_state_reason: 'content_comparison_skipped_to_avoid_git_filters',
    dirty_path_count: null,
    dirty_paths: [],
    dirty_paths_truncated: null,
  };
}

function ecosystemsFor(paths) {
  const names = new Set(paths.map((item) => basename(item)));
  const ecosystems = [];
  const rules = [
    ['Node.js', ['package.json']],
    ['Python', ['pyproject.toml', 'requirements.txt']],
    ['Rust', ['Cargo.toml']],
    ['Go', ['go.mod']],
    ['Java/JVM', ['pom.xml', 'build.gradle', 'build.gradle.kts']],
    ['Ruby', ['Gemfile']],
    ['PHP', ['composer.json']],
    ['Elixir', ['mix.exs']],
    ['Swift', ['Package.swift']],
    ['Deno', ['deno.json', 'deno.jsonc']],
  ];
  for (const [ecosystem, markers] of rules) {
    if (markers.some((marker) => names.has(marker))) {
      ecosystems.push(ecosystem);
    }
  }
  return ecosystems.sort(rawCompare);
}

function buildReport(
  root,
  maxFiles,
  maxDirectories,
  maxDepth,
  includeVendored,
  excludedPaths,
) {
  const walked = walkRepository(
    root,
    maxFiles,
    maxDirectories,
    maxDepth,
    includeVendored,
    excludedPaths,
  );
  const files = walked.files;
  const relatives = files.map((target) => relativePath(target, root));
  const reportTruncatedSections = [];

  function recordReportLimit(section, total, reported) {
    if (total > reported) {
      reportTruncatedSections.push({
        path: section,
        total,
        reported,
      });
    }
  }

  function capPaths(values, section, limit = MAX_REPORTED_PATHS) {
    const ordered = sortedUnique(values);
    const reported = ordered.slice(0, limit);
    recordReportLimit(section, ordered.length, reported.length);
    return reported;
  }

  const languageCounts = new Map();
  for (const target of files) {
    const language = LANGUAGE_EXTENSIONS.get(path.extname(target).toLowerCase());
    if (language) {
      languageCounts.set(language, (languageCounts.get(language) || 0) + 1);
    }
  }

  const allManifests = sortedUnique(
    relatives.filter((relative) => MANIFEST_NAMES.has(basename(relative))),
  );
  const manifests = capPaths(allManifests, 'project.manifests');
  const allLockfiles = relatives.filter((relative) =>
    LOCKFILE_NAMES.has(basename(relative)),
  );
  const lockfiles = capPaths(allLockfiles, 'project.lockfiles');
  const allTaskRunners = sortedUnique(
    relatives.filter((relative) => TASK_RUNNER_NAMES.has(basename(relative))),
  );
  const taskRunners = capPaths(allTaskRunners, 'project.task_runners');
  const allCiFiles = relatives.filter(isCiPath);
  const ciFiles = capPaths(allCiFiles, 'automation.ci_files');
  const qualityConfigs = capPaths(
    relatives.filter((relative) => QUALITY_CONFIG_NAMES.has(basename(relative))),
    'automation.quality_configs',
  );
  const allHighSignalDocs = relatives.filter(isHighSignalDoc);
  const docs = capPaths(allHighSignalDocs, 'documentation.high_signal_files');
  const testPaths = capPaths(
    relatives.filter(isTestPath),
    'verification.test_paths',
  );
  const skills = capPaths(
    relatives.filter(isSkillPath),
    'agent_surface.skills',
  );
  const allAgentDefinitions = relatives
    .map((relative) => {
      const kind = agentDefinitionKind(relative);
      return kind ? { path: relative, kind } : null;
    })
    .filter((item) => item !== null)
    .sort((left, right) => rawCompare(left.path, right.path));
  const agentDefinitions = allAgentDefinitions.slice(0, MAX_REPORTED_PATHS);
  recordReportLimit(
    'agent_surface.agent_definitions',
    allAgentDefinitions.length,
    agentDefinitions.length,
  );
  const allPrompts = relatives
    .map((relative) => {
      const kind = promptKind(relative);
      return kind ? { path: relative, kind } : null;
    })
    .filter((item) => item !== null)
    .sort((left, right) => rawCompare(left.path, right.path));
  const prompts = allPrompts.slice(0, MAX_REPORTED_PATHS);
  recordReportLimit('agent_surface.prompts', allPrompts.length, prompts.length);
  const agentConfigs = capPaths(
    relatives.filter(
      (relative) =>
        isAgentConfig(relative) &&
        instructionKind(relative) === null &&
        agentDefinitionKind(relative) === null &&
        promptKind(relative) === null,
    ),
    'agent_surface.config',
  );

  const warnings = [...walked.warnings];
  let verificationEvidenceIncomplete = false;
  const instructionSummaries = [];
  const instructionCandidates = [];
  for (let index = 0; index < files.length; index += 1) {
    const kind = instructionKind(relatives[index]);
    if (kind) {
      instructionCandidates.push({
        target: files[index],
        relative: relatives[index],
        kind,
      });
    }
  }
  instructionCandidates.sort(
    (left, right) =>
      relativeParts(left.relative).length -
        relativeParts(right.relative).length ||
      portableNameCompare(left.relative, right.relative),
  );
  recordReportLimit(
    'agent_surface.instructions',
    instructionCandidates.length,
    Math.min(instructionCandidates.length, MAX_REPORTED_PATHS),
  );
  for (const candidate of instructionCandidates.slice(0, MAX_REPORTED_PATHS)) {
    const summarized = summarizeInstruction(
      candidate.target,
      root,
      candidate.kind,
    );
    instructionSummaries.push(summarized.summary);
    warnings.push(...summarized.warnings);
    verificationEvidenceIncomplete =
      verificationEvidenceIncomplete || summarized.warnings.length > 0;
    for (const [field, totalField] of [
      ['headings', 'headings_total'],
      [
        'documented_verification_commands',
        'documented_verification_commands_total',
      ],
      ['relative_link_targets_inspected', 'relative_link_targets_total'],
      ['broken_relative_links', 'broken_relative_links_total'],
      [
        'relative_links_outside_repository',
        'relative_links_outside_repository_total',
      ],
      ['imports', 'imports_total'],
      ['broken_imports', 'broken_imports_total'],
      ['imports_outside_repository', 'imports_outside_repository_total'],
    ]) {
      const reported =
        field === 'relative_link_targets_inspected'
          ? Math.min(
              summarized.summary[totalField],
              MAX_INSTRUCTION_REFERENCES,
            )
          : summarized.summary[field].length;
      recordReportLimit(
        'agent_surface.instructions[' + candidate.relative + '].' + field,
        summarized.summary[totalField],
        reported,
      );
    }
  }
  instructionSummaries.sort((left, right) => rawCompare(left.path, right.path));

  const packageScripts = [];
  const pythonScripts = [];
  const taskTargets = [];
  const pathByRelative = new Map();
  for (let index = 0; index < relatives.length; index += 1) {
    pathByRelative.set(relatives[index], files[index]);
  }
  const packageManifestCandidates = allManifests.filter(
    (relative) => basename(relative) === 'package.json',
  );
  const pythonManifestCandidates = allManifests.filter(
    (relative) => basename(relative) === 'pyproject.toml',
  );
  recordReportLimit(
    'verification.package_script_manifests_inspected',
    packageManifestCandidates.length,
    Math.min(packageManifestCandidates.length, MAX_PARSED_MANIFESTS),
  );
  recordReportLimit(
    'verification.python_entrypoint_manifests_inspected',
    pythonManifestCandidates.length,
    Math.min(pythonManifestCandidates.length, MAX_PARSED_MANIFESTS),
  );
  recordReportLimit(
    'verification.task_runner_files_inspected',
    allTaskRunners.length,
    Math.min(allTaskRunners.length, MAX_PARSED_MANIFESTS),
  );
  for (const relative of packageManifestCandidates.slice(
    0,
    MAX_PARSED_MANIFESTS,
  )) {
    const target = pathByRelative.get(relative);
    const result = parsePackageScripts(target, root, new Set(allLockfiles));
    if (result.parsed) {
      packageScripts.push(result.parsed);
      recordReportLimit(
        'verification.package_scripts[' + relative + '].scripts',
        result.parsed.scripts_total,
        Object.keys(result.parsed.scripts).length,
      );
    }
    if (result.warning) {
      warnings.push(result.warning);
      verificationEvidenceIncomplete = true;
    }
  }
  for (const relative of pythonManifestCandidates.slice(
    0,
    MAX_PARSED_MANIFESTS,
  )) {
    const result = parsePythonScripts(pathByRelative.get(relative), root);
    if (result.parsed) {
      pythonScripts.push(result.parsed);
      recordReportLimit(
        'verification.python_entrypoints[' + relative + '].scripts',
        result.parsed.scripts_total,
        Object.keys(result.parsed.scripts).length,
      );
    }
    if (result.warning) {
      warnings.push(result.warning);
      verificationEvidenceIncomplete = true;
    }
  }
  for (const relative of allTaskRunners.slice(0, MAX_PARSED_MANIFESTS)) {
    const result = parseTaskTargets(pathByRelative.get(relative), root);
    if (result.parsed) {
      taskTargets.push(result.parsed);
      recordReportLimit(
        'verification.task_targets[' + relative + '].targets',
        result.parsed.targets_total,
        result.parsed.targets.length,
      );
    }
    if (result.warning) {
      warnings.push(result.warning);
      verificationEvidenceIncomplete = true;
    }
  }

  const verificationCommands = [];
  for (const packageInfo of packageScripts) {
    for (const [name, command] of Object.entries(packageInfo._all_scripts)) {
      if (VERIFICATION_NAME.test(name)) {
        verificationCommands.push({
          source: packageInfo.source,
          name,
          definition: command,
        });
      }
    }
  }
  for (const runner of taskTargets) {
    for (const target of runner._all_targets) {
      if (VERIFICATION_NAME.test(target)) {
        verificationCommands.push({
          source: runner.source,
          name: target,
          definition: runner.runner,
        });
      }
    }
  }
  for (const instruction of instructionSummaries) {
    for (const command of instruction._all_documented_verification_commands) {
      verificationCommands.push({
        source: instruction.path,
        name: 'documented:L' + command.line,
        definition: command.definition,
      });
    }
  }
  for (const packageInfo of packageScripts) {
    delete packageInfo._all_scripts;
  }
  for (const entrypoint of pythonScripts) {
    delete entrypoint._all_scripts;
  }
  for (const runner of taskTargets) {
    delete runner._all_targets;
  }
  for (const instruction of instructionSummaries) {
    delete instruction._all_documented_verification_commands;
  }
  const allVerificationCommands = verificationCommands;
  const reportedVerificationCommands = allVerificationCommands.slice(
    0,
    MAX_DECLARED_COMMANDS,
  );
  recordReportLimit(
    'verification.declared_commands',
    allVerificationCommands.length,
    reportedVerificationCommands.length,
  );

  const rootInstructions = instructionSummaries.filter(
    (item) =>
      (!item.path.includes('/') || item.path.toLowerCase() === '.kimi/agents.md') &&
      item.kind !== 'claude-review',
  );
  const brokenLinkCount = instructionSummaries.reduce(
    (total, item) => total + item.broken_relative_links.length,
    0,
  );
  const brokenImportCount = instructionSummaries.reduce(
    (total, item) => total + item.broken_imports.length,
    0,
  );
  const outsideImportCount = instructionSummaries.reduce(
    (total, item) => total + item.imports_outside_repository.length,
    0,
  );
  const versionControl = gitMetadata(root);
  let topLevel = [];
  try {
    const excludedIdentities = new Set(
      excludedPaths.map(pathIdentity).filter((identity) => identity !== null),
    );
    const allTopLevel = fs
      .readdirSync(root)
      .filter((entry) =>
        !excludedIdentities.has(pathIdentity(path.join(root, entry))),
      )
      .sort(portableNameCompare);
    topLevel = allTopLevel.slice(0, MAX_REPORTED_PATHS);
    recordReportLimit(
      'project.top_level_entries',
      allTopLevel.length,
      topLevel.length,
    );
  } catch (error) {
    warnings.push(
      'Unable to list repository root: ' + (error.message || String(error)),
    );
  }

  const allLanguages = Array.from(languageCounts.entries())
    .map(([name, filesCount], index) => ({ name, files: filesCount, index }))
    .sort((left, right) => right.files - left.files || left.index - right.index)
    .map(({ name, files: filesCount }) => ({ name, files: filesCount }));
  const languages = allLanguages.slice(0, MAX_REPORTED_LANGUAGES);
  recordReportLimit('project.languages', allLanguages.length, languages.length);

  const skippedDirectories = walked.skipped.slice(0, MAX_REPORTED_PATHS);
  const skippedSymlinks = walked.skippedSymlinks.slice(0, MAX_REPORTED_PATHS);
  const skippedSpecialFiles = walked.skippedSpecialFiles.slice(
    0,
    MAX_REPORTED_PATHS,
  );
  recordReportLimit(
    'scan.skipped_directories',
    walked.skipped.length,
    skippedDirectories.length,
  );
  recordReportLimit(
    'scan.skipped_symlinks',
    walked.skippedSymlinks.length,
    skippedSymlinks.length,
  );
  recordReportLimit(
    'scan.skipped_special_files',
    walked.skippedSpecialFiles.length,
    skippedSpecialFiles.length,
  );

  const warningValues = sortedUnique(warnings);
  const reportedWarnings = warningValues.slice(0, MAX_REPORTED_WARNINGS);
  recordReportLimit('scan.warnings', warningValues.length, reportedWarnings.length);

  const diagnostics = [];
  const traversalDetectionIncomplete =
    walked.limitReasons.length > 0 || walked.warnings.length > 0;
  if (!files.length) {
    diagnostics.push(
      traversalDetectionIncomplete
        ? 'repository_inventory_incomplete'
        : 'empty_repository',
    );
  }
  if (!instructionCandidates.length) {
    diagnostics.push(
      traversalDetectionIncomplete
        ? 'agent_instruction_surface_detection_incomplete'
        : 'no_agent_instruction_surface_detected',
    );
  } else if (!rootInstructions.length) {
    diagnostics.push('no_root_instruction_entrypoint_detected');
  } else if (!rootInstructions.some((item) => item.kind === 'shared')) {
    diagnostics.push('provider_specific_root_instructions_only');
  }
  if (rootInstructions.length > 1) {
    diagnostics.push('multiple_root_instruction_surfaces_require_reconciliation');
  }
  if (rootInstructions.some((item) => item.bytes > 32000)) {
    diagnostics.push('large_root_instruction_file_may_need_routing');
  }
  if (brokenLinkCount) {
    diagnostics.push('broken_relative_links_in_agent_instructions');
  }
  if (brokenImportCount) {
    diagnostics.push('broken_imports_in_agent_instructions');
  }
  if (outsideImportCount) {
    diagnostics.push('instruction_imports_outside_repository');
  }
  const incompleteVerificationSections = new Set([
    'agent_surface.instructions',
    'verification.package_script_manifests_inspected',
    'verification.python_entrypoint_manifests_inspected',
    'verification.task_runner_files_inspected',
  ]);
  const verificationDetectionIncomplete =
    traversalDetectionIncomplete ||
    verificationEvidenceIncomplete ||
    reportTruncatedSections.some(
      (item) =>
        incompleteVerificationSections.has(item.path) ||
        item.path.endsWith('.documented_verification_commands') ||
        item.path.endsWith('.scripts') ||
        item.path.endsWith('.targets'),
    );
  if (!allVerificationCommands.length) {
    diagnostics.push(
      verificationDetectionIncomplete
        ? 'declared_verification_command_detection_incomplete'
        : 'no_declared_verification_command_detected',
    );
  }
  if (!allCiFiles.length) {
    diagnostics.push(
      traversalDetectionIncomplete
        ? 'ci_configuration_detection_incomplete'
        : 'no_ci_configuration_detected',
    );
  }
  if (
    files.length >= 100 &&
    !allHighSignalDocs.some(hasArchitectureOrTestingSignal)
  ) {
    diagnostics.push(
      traversalDetectionIncomplete
        ? 'high_signal_architecture_or_testing_doc_detection_incomplete'
        : 'no_high_signal_architecture_or_testing_doc_detected',
    );
  }
  if (walked.limitReasons.includes('max_files')) {
    diagnostics.push('scan_truncated_at_file_limit');
  }
  if (walked.limitReasons.includes('max_directories')) {
    diagnostics.push('scan_truncated_at_directory_limit');
  }
  if (walked.limitReasons.includes('max_depth')) {
    diagnostics.push('scan_truncated_at_depth_limit');
  }
  if (reportTruncatedSections.length) {
    diagnostics.push('report_fields_truncated');
  }
  if (versionControl.worktree_state === 'unverified') {
    diagnostics.push('git_worktree_state_unverified');
  }
  if (versionControl.repository_state === 'unverified') {
    diagnostics.push('git_repository_identity_unverified');
  }

  return {
    schema_version: SCHEMA_VERSION,
    root,
    scan: {
      implementation: 'node',
      files_seen: files.length,
      directories_seen: walked.directoriesSeen,
      max_files: maxFiles,
      max_directories: maxDirectories,
      max_depth: maxDepth,
      truncated: walked.truncated,
      traversal_incomplete: traversalDetectionIncomplete,
      limit_reasons: walked.limitReasons,
      report_truncated: reportTruncatedSections.length > 0,
      report_truncated_sections: reportTruncatedSections,
      report_limits: {
        max_reported_paths: MAX_REPORTED_PATHS,
        max_reported_warnings: MAX_REPORTED_WARNINGS,
        max_parsed_manifests: MAX_PARSED_MANIFESTS,
        max_declared_commands: MAX_DECLARED_COMMANDS,
        max_reported_languages: MAX_REPORTED_LANGUAGES,
        max_instruction_headings: MAX_INSTRUCTION_HEADINGS,
        max_instruction_references: MAX_INSTRUCTION_REFERENCES,
        max_instruction_link_results: MAX_INSTRUCTION_LINK_RESULTS,
        max_documented_commands_per_instruction:
          MAX_DOCUMENTED_COMMANDS_PER_INSTRUCTION,
        max_manifest_commands: MAX_MANIFEST_COMMANDS,
        max_task_targets: MAX_TASK_TARGETS,
      },
      include_vendored: includeVendored,
      excluded_paths: excludedPaths.map((target) => relativePath(target, root)),
      skipped_directories: skippedDirectories,
      skipped_symlinks: skippedSymlinks,
      skipped_special_files: skippedSpecialFiles,
      warnings: reportedWarnings,
    },
    version_control: versionControl,
    project: {
      top_level_entries: topLevel,
      ecosystems: ecosystemsFor(allManifests),
      languages,
      manifests,
      lockfiles,
      task_runners: taskRunners,
    },
    agent_surface: {
      instructions: instructionSummaries,
      skills,
      agent_definitions: agentDefinitions,
      prompts,
      config: agentConfigs,
    },
    documentation: { high_signal_files: docs },
    automation: {
      ci_files: ciFiles,
      quality_configs: qualityConfigs,
    },
    verification: {
      test_paths: testPaths,
      package_scripts: packageScripts,
      python_entrypoints: pythonScripts,
      task_targets: taskTargets,
      declared_commands: reportedVerificationCommands,
    },
    diagnostic_hints: diagnostics,
  };
}

function markdownCode(value) {
  const escaped = Array.from(String(value), (character) => {
    const code = character.codePointAt(0);
    return character === '`' || code < 32 || code === 127
      ? '\\u' + code.toString(16).padStart(4, '0')
      : character;
  }).join('');
  return '`' + escaped + '`';
}

function markdownCodeList(values) {
  const rendered = Array.from(values, markdownCode);
  return rendered.length ? rendered.join(', ') : 'none';
}

function renderMarkdown(report) {
  const project = report.project;
  const agentSurface = report.agent_surface;
  const verification = report.verification;
  const repositoryDisplay =
    report.version_control.is_repository === null
      ? 'Unverified'
      : report.version_control.is_repository
        ? 'True'
        : 'False';
  const traversalIncomplete = report.scan.traversal_incomplete;
  const instructionDetectionIncomplete = report.diagnostic_hints.includes(
    'agent_instruction_surface_detection_incomplete',
  );
  const verificationDetectionIncomplete = report.diagnostic_hints.includes(
    'declared_verification_command_detection_incomplete',
  );
  const ecosystemsDisplay =
    project.ecosystems.join(', ') ||
    (traversalIncomplete
      ? 'unverified (traversal incomplete)'
      : 'none detected');
  const lines = [
    '# Agentize Skill repository inventory',
    '',
    '- Root: ' + markdownCode(report.root),
    '- Files scanned: ' + report.scan.files_seen,
    '- Traversal truncated: ' +
      (report.scan.truncated ? 'True' : 'False') +
      ' (' +
      (report.scan.limit_reasons.join(', ') || 'no limit reached') +
      ')',
    '- Traversal incomplete: ' +
      (report.scan.traversal_incomplete ? 'True' : 'False'),
    '- Report fields truncated: ' +
      markdownCodeList(
        report.scan.report_truncated_sections.map((item) => item.path),
      ),
    '- Excluded paths: ' + markdownCodeList(report.scan.excluded_paths),
    '- Ecosystems: ' + ecosystemsDisplay,
    '- Git repository: ' + repositoryDisplay,
    '- Git worktree state: ' +
      (report.version_control.worktree_state || 'unverified'),
    '',
    '## Agent surfaces',
    '',
  ];

  if (agentSurface.instructions.length) {
    for (const instruction of agentSurface.instructions) {
      let details = instruction.lines + ' lines, ' + instruction.kind;
      if (instruction.broken_relative_links.length) {
        details +=
          ', ' + instruction.broken_relative_links.length + ' broken link(s)';
      }
      if (instruction.broken_imports.length) {
        details +=
          ', ' + instruction.broken_imports.length + ' broken import(s)';
      }
      lines.push(
        '- ' + markdownCode(instruction.path) + ' (' + details + ')',
      );
    }
  } else {
    lines.push(
      instructionDetectionIncomplete
        ? '- No recognized instruction file detected in the scanned files; detection was incomplete.'
        : '- No recognized instruction file detected.',
    );
  }

  lines.push('', '## Verification signals', '');
  if (verification.declared_commands.length) {
    for (const command of verification.declared_commands.slice(0, 40)) {
      lines.push(
        '- ' +
          markdownCode(command.name) +
          ' from ' +
          markdownCode(command.source) +
          ': ' +
          markdownCode(command.definition),
      );
    }
  } else {
    lines.push(
      verificationDetectionIncomplete
        ? '- Declared verification-command detection is incomplete.'
        : '- No declared verification command detected.',
    );
  }

  lines.push('', '## Other evidence', '');
  lines.push(
    '- Skills: ' +
      agentSurface.skills.length +
      '; agent definitions: ' +
      agentSurface.agent_definitions.length +
      '; prompts: ' +
      agentSurface.prompts.length +
      '; CI files: ' +
      report.automation.ci_files.length +
      '; test paths: ' +
      verification.test_paths.length,
  );
  lines.push(
    '- High-signal docs: ' +
      markdownCodeList(report.documentation.high_signal_files.slice(0, 20)),
  );

  lines.push('', '## Diagnostic hints', '');
  if (report.diagnostic_hints.length) {
    for (const hint of report.diagnostic_hints) {
      lines.push('- ' + markdownCode(hint));
    }
  } else {
    lines.push('- No automatic hints. Human assessment is still required.');
  }

  if (report.scan.warnings.length) {
    lines.push('', '## Scanner warnings', '');
    for (const warning of report.scan.warnings) {
      lines.push('- ' + markdownCode(warning));
    }
  }
  return lines.join('\n') + '\n';
}

function usage() {
  return [
    'usage: scan_repo.cjs [--root PATH] [--format json|markdown]',
    '                     [--max-files NUMBER] [--max-directories NUMBER]',
    '                     [--max-depth NUMBER] [--include-vendored]',
    '                     [--exclude-path PATH]...',
    '',
    'Read a repository and report coding-agent workflow signals.',
  ].join('\n');
}

function parseArguments(argumentsList) {
  const options = {
    root: '.',
    format: 'json',
    maxFiles: DEFAULT_MAX_FILES,
    maxDirectories: DEFAULT_MAX_DIRECTORIES,
    maxDepth: DEFAULT_MAX_DEPTH,
    includeVendored: false,
    excludePaths: [],
  };
  for (let index = 0; index < argumentsList.length; index += 1) {
    const argument = argumentsList[index];
    if (argument === '--root') {
      index += 1;
      if (index >= argumentsList.length) {
        throw new Error('--root requires a value');
      }
      options.root = argumentsList[index];
    } else if (argument === '--format') {
      index += 1;
      if (
        index >= argumentsList.length ||
        !new Set(['json', 'markdown']).has(argumentsList[index])
      ) {
        throw new Error('--format must be json or markdown');
      }
      options.format = argumentsList[index];
    } else if (argument === '--max-files') {
      index += 1;
      if (index >= argumentsList.length) {
        throw new Error('--max-files requires a value');
      }
      options.maxFiles = Number(argumentsList[index]);
    } else if (argument === '--max-directories') {
      index += 1;
      if (index >= argumentsList.length) {
        throw new Error('--max-directories requires a value');
      }
      options.maxDirectories = Number(argumentsList[index]);
    } else if (argument === '--max-depth') {
      index += 1;
      if (index >= argumentsList.length) {
        throw new Error('--max-depth requires a value');
      }
      options.maxDepth = Number(argumentsList[index]);
    } else if (argument === '--include-vendored') {
      options.includeVendored = true;
    } else if (argument === '--exclude-path') {
      index += 1;
      if (index >= argumentsList.length) {
        throw new Error('--exclude-path requires a value');
      }
      options.excludePaths.push(argumentsList[index]);
    } else if (argument === '--help' || argument === '-h') {
      process.stdout.write(usage() + '\n');
      process.exit(0);
    } else {
      throw new Error('unknown argument: ' + argument);
    }
  }
  return options;
}

function expandUser(input) {
  if (input === '~') {
    return os.homedir();
  }
  if (input.startsWith('~' + path.sep)) {
    return path.join(os.homedir(), input.slice(2));
  }
  return input;
}

function declaresAgentizeSkill(packageRoot) {
  const read = readText(path.join(packageRoot, 'SKILL.md'), packageRoot, 32000);
  if (read.warning || read.text === null) {
    return false;
  }
  const lines = splitLines(read.text);
  if (!lines.length || lines[0].trim() !== '---') {
    return false;
  }
  for (const line of lines.slice(1, 101)) {
    if (line.trim() === '---') {
      return false;
    }
    const match = /^\s*name\s*:\s*(.*?)\s*$/.exec(line);
    if (match) {
      const value = match[1].trim().replace(/^['"]|['"]$/g, '');
      return value === 'agentize-skill';
    }
  }
  return false;
}

function main(argumentsList) {
  let options;
  try {
    options = parseArguments(argumentsList);
  } catch (error) {
    process.stderr.write((error.message || String(error)) + '\n');
    return 2;
  }
  if (!Number.isInteger(options.maxFiles) || options.maxFiles < 1) {
    process.stderr.write('--max-files must be positive\n');
    return 2;
  }
  if (
    !Number.isInteger(options.maxDirectories) ||
    options.maxDirectories < 1
  ) {
    process.stderr.write('--max-directories must be positive\n');
    return 2;
  }
  if (!Number.isInteger(options.maxDepth) || options.maxDepth < 0) {
    process.stderr.write('--max-depth must be zero or positive\n');
    return 2;
  }

  let root;
  try {
    root = fs.realpathSync(path.resolve(expandUser(options.root)));
  } catch {
    process.stderr.write(
      'Repository root is not a directory: ' +
        path.resolve(expandUser(options.root)) +
        '\n',
    );
    return 2;
  }
  try {
    if (!fs.statSync(root).isDirectory()) {
      process.stderr.write('Repository root is not a directory: ' + root + '\n');
      return 2;
    }
  } catch {
    process.stderr.write('Repository root is not a directory: ' + root + '\n');
    return 2;
  }

  const requestedExclusions = [...options.excludePaths];
  const scannerPackage = fs.realpathSync(path.resolve(__dirname, '..'));
  if (
    canonicalPathKey(scannerPackage) !== canonicalPathKey(root) &&
    isWithinRoot(scannerPackage, root) &&
    declaresAgentizeSkill(scannerPackage)
  ) {
    requestedExclusions.push(scannerPackage);
  }
  let excludedPaths;
  try {
    excludedPaths = normalizeExcludedPaths(root, requestedExclusions);
  } catch (error) {
    process.stderr.write((error.message || String(error)) + '\n');
    return 2;
  }

  const report = buildReport(
    root,
    options.maxFiles,
    options.maxDirectories,
    options.maxDepth,
    options.includeVendored,
    excludedPaths,
  );
  if (options.format === 'markdown') {
    process.stdout.write(renderMarkdown(report));
  } else {
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  }
  return 0;
}

process.exitCode = main(process.argv.slice(2));
