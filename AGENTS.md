# Agentize Skill repository guidance

Agentize Skill is a reusable coding-agent skill. It audits and reconciles the durable
workflow inside another repository; it must not become a runtime dependency of
that repository.

## Source map

- `SKILL.md`: activation, safety, coordination, and handoff boundary.
- `references/assessment.md`: evidence and capability classification.
- `references/delivery-workflow.md`: normative context/evidence lifecycle, development-stage, and return-loop contract.
- `references/artifacts.md`: adaptive repository output selection and contents.
- `references/compatibility.md`: multi-host and provider-specific reconciliation.
- `scripts/scan_repo.py` and `scripts/scan_repo.cjs`: dependency-free, read-only repository inventory implementations with one shared contract.
- `docs/workflow.en.png` and `docs/workflow.png`: English and Chinese illustrations of the ideal workflow described by the README and delivery reference.
- `tests/test_scanners.py`: deterministic scanner safety, boundary, and cross-runtime parity regressions.
- `tests/test_package_identity.py`: canonical Skill name, display name, selector, and installation-path regression.
- `.github/workflows/ci.yml`: read-only GitHub CI for tests, scanner execution, syntax, and package validation.
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
git diff --check
```

Also run an Agent Skills validator available in the current development environment. In a Codex source checkout, use the installed `skill-creator` validator. Its absolute path and Python environment are host-specific development details, not Agentize Skill runtime dependencies; do not add them to portable scripts or CI.

GitHub CI runs the deterministic suite with Python and Node.js and validates the package with a pinned revision of the upstream `skills-ref` reference validator. This is development-only tooling; the installed Skill and both scanners remain dependency-free.

When changing either scanner, add or update a scanner regression and preserve cross-runtime parity. When changing the workflow boundary, update its single owning reference and keep `SKILL.md` plus README claims consistent.
