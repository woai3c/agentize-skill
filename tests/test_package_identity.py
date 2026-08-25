from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
MACHINE_NAME = "agentize-skill"
DISPLAY_NAME = "Agentize Skill"


class PackageIdentityTests(unittest.TestCase):
    def test_skill_and_ui_metadata_use_canonical_identity(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")
        metadata = (REPOSITORY_ROOT / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )

        self.assertRegex(skill, rf"(?m)^name: {re.escape(MACHINE_NAME)}$")
        self.assertIn(f'display_name: "{DISPLAY_NAME}"', metadata)
        self.assertIn(f"${MACHINE_NAME}", metadata)
        self.assertIsNone(re.search(r"\$agentize(?!-skill)", metadata))

    def test_readmes_use_canonical_install_directory_and_selector(self) -> None:
        for filename in ("README.md", "README.zh-CN.md"):
            with self.subTest(filename=filename):
                readme = (REPOSITORY_ROOT / filename).read_text(encoding="utf-8")
                self.assertIn(
                    f"https://github.com/woai3c/{MACHINE_NAME}", readme
                )
                self.assertIn(f"~/.agents/skills/{MACHINE_NAME}/", readme)
                self.assertIn(f"<repository>/.agents/skills/{MACHINE_NAME}/", readme)
                self.assertIn(f"${MACHINE_NAME}", readme)
                self.assertIsNone(re.search(r"\$agentize(?!-skill)", readme))


if __name__ == "__main__":
    unittest.main()
