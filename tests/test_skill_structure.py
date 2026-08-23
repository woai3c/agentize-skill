from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


class SkillStructureTests(unittest.TestCase):
    def test_skill_frontmatter_and_supporting_files(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(skill.startswith("---\n"))
        self.assertRegex(skill, r"(?m)^name: agentize$")
        self.assertRegex(skill, r"(?m)^description: .+")

        local_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", skill)
        self.assertGreaterEqual(len(local_links), 3)
        for relative in local_links:
            with self.subTest(relative=relative):
                self.assertTrue((REPOSITORY_ROOT / relative).is_file())

    def test_ui_metadata_mentions_the_skill(self) -> None:
        metadata = (REPOSITORY_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn('display_name: "Agentize"', metadata)
        self.assertIn("$agentize", metadata)

    def test_documented_portable_commands_exist(self) -> None:
        self.assertTrue((REPOSITORY_ROOT / "scripts" / "scan_repo.cjs").is_file())
        self.assertTrue((REPOSITORY_ROOT / "scripts" / "scan_repo.py").is_file())
        self.assertTrue((REPOSITORY_ROOT / "tests" / "behavior-cases.md").is_file())
        self.assertTrue(
            (
                REPOSITORY_ROOT
                / "tests"
                / "forward-evidence"
                / "audit-only-codex-2026-08-23.md"
            ).is_file()
        )

    def test_target_binding_and_static_audit_boundary_are_explicit(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertNotIn("--root .", skill)
        self.assertGreaterEqual(skill.count("--root <target-directory>"), 2)
        self.assertIn(
            "Use it for every scan, read, Git\n  query, command working directory, and write.",
            skill,
        )
        self.assertIn(
            "Treat an audit-only, report-only, review-only, or `do not modify` request as a\n"
            "static assessment by default.",
            skill,
        )
        self.assertIn(
            "Audit-only runs use the static boundary above and do not\ninherit "
            "these command-execution steps.",
            skill,
        )
        self.assertIn(
            "Treat `worktree_state: unverified` as unknown,\n  never clean.", skill
        )
        self.assertIn(
            "Do not run a content-comparing Git\n  command merely to fill this gap "
            "during a static audit.",
            skill,
        )

    def test_non_audit_no_change_outcomes_still_use_verification(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "This section governs non-audit coordination runs, including deliberate\n"
            "no-change outcomes.",
            skill,
        )


if __name__ == "__main__":
    unittest.main()
