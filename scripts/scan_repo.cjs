#!/usr/bin/env node
'use strict';

// Produce the same bounded, read-only repository inventory as scan_repo.py
// without requiring Python or third-party Node.js packages.

const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const SCHEMA_VERSION = 4;
const DEFAULT_MAX_FILES = 50000;
const MAX_REPORTED_PATHS = 200;

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
  'CHANGELOG.md',
  'CONTRIBUTING.md',
  'DEVELOPMENT.md',
  'README.md',
  'SECURITY.md',
]);

const HIGH_SIGNAL_DOC_WORDS = new Set([
  'adr',
  'architecture',
  'decisions',
  'design',
  'development',
  'domain',
  'glossary',
  'invariants',
  'operations',
  'runbook',
  'testing',
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
const FENCE = /^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_-]*)\s*$/;
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

function documentedVerificationCommands(value) {
  const commands = [];
  let fenceCharacter = null;
  let fenceLength = 0;
  let inspectFence = false;

  for (const [index, line] of splitLines(value).entries()) {
    const stripped = line.trim();
    if (fenceCharacter === null) {
      const match = FENCE.exec(line);
      if (!match) {
        continue;
      }
      fenceCharacter = match[1][0];
      fenceLength = match[1].length;
      inspectFence = COMMAND_FENCE_LANGUAGES.has(match[2].toLowerCase());
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
      continue;
    }
    if (!inspectFence || commands.length >= 50) {
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
      candidate.startsWith('* ') ||
      candidate.length > 1000 ||
      !COMMAND_START.test(candidate) ||
      !VERIFICATION_COMMAND.test(candidate)
    ) {
      continue;
    }
    commands.push({
      line: index + 1,
      definition: redactSensitiveText(candidate),
    });
  }
  return commands;
}

function sortedUnique(values, limit = undefined) {
  const sorted = Array.from(new Set(values)).sort(rawCompare);
  return limit === undefined ? sorted : sorted.slice(0, limit);
}

function capped(values, limit = MAX_REPORTED_PATHS) {
  return sortedUnique(values, limit);
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

function stem(relative) {
  const name = basename(relative);
  const extension = path.posix.extname(name);
  return extension ? name.slice(0, -extension.length) : name;
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

function walkRepository(root, maxFiles, includeVendored) {
  const files = [];
  const skipped = new Set();
  const skippedSymlinks = new Set();
  const errors = [];
  let truncated = false;

  function walk(current) {
    if (truncated) {
      return;
    }

    let entries;
    try {
      entries = fs.readdirSync(current, { withFileTypes: true });
    } catch (error) {
      errors.push(
        'Unable to scan ' + current + ': ' + (error.message || String(error)),
      );
      return;
    }

    entries.sort((left, right) => portableNameCompare(left.name, right.name));
    const directories = [];
    const regularEntries = [];

    for (const entry of entries) {
      const entryPath = path.join(current, entry.name);
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
        if (targetStat.isDirectory() || !isWithinRoot(resolved, root)) {
          skippedSymlinks.add(relativePath(entryPath, root));
          continue;
        }
        regularEntries.push(entry);
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
      } else {
        regularEntries.push(entry);
      }
    }

    for (const entry of regularEntries) {
      if (files.length >= maxFiles) {
        truncated = true;
        return;
      }
      files.push(path.join(current, entry.name));
    }

    for (const entry of directories) {
      walk(path.join(current, entry.name));
      if (truncated) {
        return;
      }
    }
  }

  walk(root);
  return {
    files,
    skipped: sortedUnique(skipped),
    skippedSymlinks: sortedUnique(skippedSymlinks),
    warnings: errors,
    truncated,
  };
}

function isCiPath(relative) {
  const lowered = relative.toLowerCase();
  const name = basename(relative).toLowerCase();
  return (
    lowered.startsWith('.github/workflows/') ||
    lowered.startsWith('.circleci/') ||
    lowered.startsWith('.buildkite/') ||
    new Set([
      '.gitlab-ci.yml',
      'azure-pipelines.yml',
      'bitbucket-pipelines.yml',
      'jenkinsfile',
    ]).has(name)
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
  if (DOC_BASENAMES.has(basename(relative))) {
    return true;
  }
  const parts = new Set(relativeParts(relative).map((part) => part.toLowerCase()));
  const stemWords = stem(relative).toLowerCase().split(/[-_.]/);
  return (
    parts.has('docs') &&
    [...parts, ...stemWords].some((word) => HIGH_SIGNAL_DOC_WORDS.has(word))
  );
}

function instructionKind(relative) {
  const name = basename(relative);
  if (INSTRUCTION_FILES.has(name)) {
    if (
      name === 'copilot-instructions.md' &&
      !relativeParts(relative).includes('.github')
    ) {
      return null;
    }
    return INSTRUCTION_FILES.get(name);
  }
  const parts = relativeParts(relative);
  if (
    suffix(relative).toLowerCase() === '.mdc' &&
    parts.length >= 2 &&
    parts[0].toLowerCase() === '.cursor' &&
    parts[1].toLowerCase() === 'rules'
  ) {
    return 'cursor';
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
    const size = fs.statSync(resolved).size;
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
    let text = fs.readFileSync(resolved).toString('utf8');
    if (text.startsWith('\uFEFF')) {
      text = text.slice(1);
    }
    return { text, warning: null };
  } catch (error) {
    return {
      text: null,
      warning: 'Unable to read ' + target + ': ' + (error.message || String(error)),
    };
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
  const lines = read.text === null ? [] : splitLines(read.text);
  const documentedCommands =
    read.text === null ? [] : documentedVerificationCommands(read.text);

  if (read.text !== null) {
    for (const line of lines) {
      const match = HEADING.exec(line);
      if (match && headings.length < 50) {
        headings.push(redactSensitiveText(match[2].trim()));
      }
    }

    MARKDOWN_LINK.lastIndex = 0;
    let count = 0;
    let match;
    while (
      count < 100 &&
      (match = MARKDOWN_LINK.exec(read.text)) !== null
    ) {
      count += 1;
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
      broken_relative_links: sortedUnique(brokenLinks, 20),
      relative_links_outside_repository: sortedUnique(outsideLinks, 20),
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
  const scripts = {};
  for (const name of Object.keys(data.scripts).sort(rawCompare).slice(0, 100)) {
    if (typeof data.scripts[name] === 'string') {
      scripts[name] = redactSensitiveText(data.scripts[name]);
    }
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
    },
    warning: null,
  };
}

function detectPackageManager(directory, root, scannedLockfiles) {
  for (const [name, manager] of [
    ['pnpm-lock.yaml', 'pnpm'],
    ['yarn.lock', 'yarn'],
    ['bun.lock', 'bun'],
    ['bun.lockb', 'bun'],
    ['package-lock.json', 'npm'],
  ]) {
    if (scannedLockfiles.has(relativePath(path.join(directory, name), root))) {
      return manager;
    }
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
  return sortedUnique(targets, 200);
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
    targets = sortedUnique(targetSet, 200);
  }
  if (!targets.length) {
    return { parsed: null, warning: null };
  }
  return {
    parsed: {
      source: relativePath(target, root),
      runner,
      targets,
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
  return {
    parsed: {
      source: relativePath(target, root),
      scripts: sortedScripts,
    },
    warning: null,
  };
}

function runGit(root, args) {
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
    'git',
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
  const topLevel = runGit(root, ['rev-parse', '--show-toplevel']);
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
  let branch = runGit(root, ['symbolic-ref', '--quiet', '--short', 'HEAD']);
  if (branch.returncode !== 0) {
    branch = runGit(root, ['rev-parse', '--short', 'HEAD']);
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

function buildReport(root, maxFiles, includeVendored) {
  const walked = walkRepository(root, maxFiles, includeVendored);
  const files = walked.files;
  const relatives = files.map((target) => relativePath(target, root));
  const languageCounts = new Map();
  for (const target of files) {
    const language = LANGUAGE_EXTENSIONS.get(path.extname(target).toLowerCase());
    if (language) {
      languageCounts.set(language, (languageCounts.get(language) || 0) + 1);
    }
  }

  const manifests = capped(
    relatives.filter((relative) => MANIFEST_NAMES.has(basename(relative))),
  );
  const lockfiles = capped(
    relatives.filter((relative) => LOCKFILE_NAMES.has(basename(relative))),
  );
  const taskRunners = capped(
    relatives.filter((relative) => TASK_RUNNER_NAMES.has(basename(relative))),
  );
  const ciFiles = capped(relatives.filter(isCiPath));
  const qualityConfigs = capped(
    relatives.filter((relative) => QUALITY_CONFIG_NAMES.has(basename(relative))),
  );
  const docs = capped(relatives.filter(isHighSignalDoc));
  const testPaths = capped(relatives.filter(isTestPath));
  const skills = capped(relatives.filter(isSkillPath));
  const agentConfigs = capped(relatives.filter(isAgentConfig));

  const warnings = [...walked.warnings];
  const instructionSummaries = [];
  for (let index = 0; index < files.length; index += 1) {
    const kind = instructionKind(relatives[index]);
    if (!kind) {
      continue;
    }
    const summarized = summarizeInstruction(files[index], root, kind);
    instructionSummaries.push(summarized.summary);
    warnings.push(...summarized.warnings);
  }
  instructionSummaries.sort((left, right) => rawCompare(left.path, right.path));

  const packageScripts = [];
  const pythonScripts = [];
  const taskTargets = [];
  const pathByRelative = new Map();
  for (let index = 0; index < relatives.length; index += 1) {
    pathByRelative.set(relatives[index], files[index]);
  }
  for (const relative of manifests) {
    const target = pathByRelative.get(relative);
    if (basename(relative) === 'package.json' && packageScripts.length < 50) {
      const result = parsePackageScripts(target, root, new Set(lockfiles));
      if (result.parsed) {
        packageScripts.push(result.parsed);
      }
      if (result.warning) {
        warnings.push(result.warning);
      }
    } else if (
      basename(relative) === 'pyproject.toml' &&
      pythonScripts.length < 50
    ) {
      const result = parsePythonScripts(target, root);
      if (result.parsed) {
        pythonScripts.push(result.parsed);
      }
      if (result.warning) {
        warnings.push(result.warning);
      }
    }
  }
  for (const relative of taskRunners.slice(0, 50)) {
    const result = parseTaskTargets(pathByRelative.get(relative), root);
    if (result.parsed) {
      taskTargets.push(result.parsed);
    }
    if (result.warning) {
      warnings.push(result.warning);
    }
  }

  const verificationCommands = [];
  for (const packageInfo of packageScripts) {
    for (const [name, command] of Object.entries(packageInfo.scripts)) {
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
    for (const target of runner.targets) {
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
    for (const command of instruction.documented_verification_commands) {
      verificationCommands.push({
        source: instruction.path,
        name: 'documented:L' + command.line,
        definition: command.definition,
      });
    }
  }

  const rootInstructions = instructionSummaries.filter(
    (item) => !item.path.includes('/'),
  );
  const brokenLinkCount = instructionSummaries.reduce(
    (total, item) => total + item.broken_relative_links.length,
    0,
  );
  const versionControl = gitMetadata(root);
  const diagnostics = [];
  if (!files.length) {
    diagnostics.push('empty_repository');
  }
  if (!instructionSummaries.length) {
    diagnostics.push('no_agent_instruction_surface_detected');
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
  if (!verificationCommands.length) {
    diagnostics.push('no_declared_verification_command_detected');
  }
  if (!ciFiles.length) {
    diagnostics.push('no_ci_configuration_detected');
  }
  if (
    files.length >= 100 &&
    !docs.some((document) =>
      stem(document)
        .toLowerCase()
        .split(/[-_.]/)
        .some((word) => HIGH_SIGNAL_DOC_WORDS.has(word)),
    )
  ) {
    diagnostics.push('no_high_signal_architecture_or_testing_doc_detected');
  }
  if (walked.truncated) {
    diagnostics.push('scan_truncated_at_file_limit');
  }
  if (versionControl.worktree_state === 'unverified') {
    diagnostics.push('git_worktree_state_unverified');
  }
  if (versionControl.repository_state === 'unverified') {
    diagnostics.push('git_repository_identity_unverified');
  }

  let topLevel = [];
  try {
    topLevel = fs
      .readdirSync(root)
      .sort(portableNameCompare)
      .slice(0, 200);
  } catch (error) {
    warnings.push(
      'Unable to list repository root: ' + (error.message || String(error)),
    );
  }

  const languages = Array.from(languageCounts.entries())
    .map(([name, filesCount], index) => ({ name, files: filesCount, index }))
    .sort((left, right) => right.files - left.files || left.index - right.index)
    .slice(0, 20)
    .map(({ name, files: filesCount }) => ({ name, files: filesCount }));

  return {
    schema_version: SCHEMA_VERSION,
    root,
    scan: {
      implementation: 'node',
      files_seen: files.length,
      max_files: maxFiles,
      truncated: walked.truncated,
      include_vendored: includeVendored,
      skipped_directories: walked.skipped.slice(0, MAX_REPORTED_PATHS),
      skipped_symlinks: walked.skippedSymlinks.slice(0, MAX_REPORTED_PATHS),
      warnings: sortedUnique(warnings, 100),
    },
    version_control: versionControl,
    project: {
      top_level_entries: topLevel,
      ecosystems: ecosystemsFor(manifests),
      languages,
      manifests,
      lockfiles,
      task_runners: taskRunners,
    },
    agent_surface: {
      instructions: instructionSummaries,
      skills,
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
      declared_commands: verificationCommands.slice(0, 250),
    },
    diagnostic_hints: diagnostics,
  };
}

function renderMarkdown(report) {
  const project = report.project;
  const agentSurface = report.agent_surface;
  const verification = report.verification;
  const tick = String.fromCharCode(96);
  const repositoryDisplay =
    report.version_control.is_repository === null
      ? 'Unverified'
      : report.version_control.is_repository
        ? 'True'
        : 'False';
  const lines = [
    '# Agentize repository inventory',
    '',
    '- Root: ' + tick + report.root + tick,
    '- Files scanned: ' + report.scan.files_seen,
    '- Ecosystems: ' + (project.ecosystems.join(', ') || 'none detected'),
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
      lines.push(
        '- ' + tick + instruction.path + tick + ' (' + details + ')',
      );
    }
  } else {
    lines.push('- No recognized instruction file detected.');
  }

  lines.push('', '## Verification signals', '');
  if (verification.declared_commands.length) {
    for (const command of verification.declared_commands.slice(0, 40)) {
      lines.push(
        '- ' +
          tick +
          command.name +
          tick +
          ' from ' +
          tick +
          command.source +
          tick +
          ': ' +
          tick +
          command.definition +
          tick,
      );
    }
  } else {
    lines.push('- No declared verification command detected.');
  }

  lines.push('', '## Other evidence', '');
  lines.push(
    '- Skills: ' +
      agentSurface.skills.length +
      '; CI files: ' +
      report.automation.ci_files.length +
      '; test paths: ' +
      verification.test_paths.length,
  );
  lines.push(
    '- High-signal docs: ' +
      (report.documentation.high_signal_files.slice(0, 20).join(', ') ||
        'none'),
  );

  lines.push('', '## Diagnostic hints', '');
  if (report.diagnostic_hints.length) {
    for (const hint of report.diagnostic_hints) {
      lines.push('- ' + tick + hint + tick);
    }
  } else {
    lines.push('- No automatic hints. Human assessment is still required.');
  }

  if (report.scan.warnings.length) {
    lines.push('', '## Scanner warnings', '');
    for (const warning of report.scan.warnings) {
      lines.push('- ' + warning);
    }
  }
  return lines.join('\n') + '\n';
}

function usage() {
  return [
    'usage: scan_repo.cjs [--root PATH] [--format json|markdown]',
    '                     [--max-files NUMBER] [--include-vendored]',
    '',
    'Read a repository and report coding-agent workflow signals.',
  ].join('\n');
}

function parseArguments(argumentsList) {
  const options = {
    root: '.',
    format: 'json',
    maxFiles: DEFAULT_MAX_FILES,
    includeVendored: false,
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
    } else if (argument === '--include-vendored') {
      options.includeVendored = true;
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

  const report = buildReport(root, options.maxFiles, options.includeVendored);
  if (options.format === 'markdown') {
    process.stdout.write(renderMarkdown(report));
  } else {
    process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  }
  return 0;
}

process.exitCode = main(process.argv.slice(2));
