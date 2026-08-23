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
        self.assertTrue((REPOSITORY_ROOT / "scripts" / "scan_repo.py").is_file())
        self.assertTrue((REPOSITORY_ROOT / "tests" / "behavior-cases.md").is_file())


if __name__ == "__main__":
    unittest.main()
