# Agentize repository guidance

Agentize is a reusable coding-agent skill. It audits and reconciles the durable
workflow inside another repository; it must not become a runtime dependency of
that repository.

## Source map

- `SKILL.md`: activation boundary and end-to-end workflow.
- `DESIGN.md`: proposed architecture, runtime fallback, safety, and acceptance criteria.
- `references/`: conditional decision guidance loaded by the skill.
- `scripts/scan_repo.py`: dependency-free, read-only repository inventory.
- `tests/`: scanner tests and behavioral cases.
- `agents/openai.yaml`: Codex and ChatGPT UI metadata.

Keep the entrypoint concise. Put conditional detail in one linked reference and
keep each fact in one place. The workflow must adapt to empty, partial,
conflicting, and already mature repositories without forcing a fixed scaffold.

## Validation

Run these commands from the repository root after changes:

```text
python -m unittest discover -s tests -v
python scripts/scan_repo.py --root . --format markdown
python C:/Users/bin/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
git diff --check
```

The third command is environment-specific; use the installed skill creator's
validator path when it differs. Do not add that path to portable scripts or CI.

When changing `scan_repo.py`, add or update a behavioral test. When changing
the workflow boundary, update `tests/behavior-cases.md` and keep README claims
consistent with the skill.
