# Agentize repository guidance

Agentize is a reusable coding-agent skill. It audits and reconciles the durable
workflow inside another repository; it must not become a runtime dependency of
that repository.

## Source map

- `SKILL.md`: activation boundary and end-to-end workflow.
- `DESIGN.md`: proposed architecture, runtime fallback, safety, and acceptance criteria.
- `references/`: conditional decision guidance loaded by the skill.
- `scripts/scan_repo.py` and `scripts/scan_repo.cjs`: dependency-free,
  read-only repository inventory implementations with one shared contract.
- `tests/`: deterministic scanner and structural tests plus behavioral cases.
- `tests/forward-evidence/`: bounded host/model run records; one record never
  implies general host support.
- `agents/openai.yaml`: Codex and ChatGPT UI metadata.

Keep the entrypoint concise. Put conditional detail in one linked reference and
keep each fact in one place. The workflow must adapt to empty, partial,
conflicting, and already mature repositories without forcing a fixed scaffold.

## Validation

Run these commands from the repository root after changes:

```text
python -m unittest discover -s tests -v
node scripts/scan_repo.cjs --root . --format markdown
python scripts/scan_repo.py --root . --format markdown
uv run --offline --with pyyaml python \
  /Users/bin/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
```

The skill-creator validator path and its Python environment are environment-
specific; use the installed path or an existing interpreter with PyYAML when
they differ. This development validator dependency is not an Agentize scanner
runtime dependency. Do not add the local path to portable scripts or CI.

When changing either scanner, add or update a behavioral test and preserve
cross-runtime parity. When changing the workflow boundary, update
`tests/behavior-cases.md` and keep README claims consistent with the skill.
