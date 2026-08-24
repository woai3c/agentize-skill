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
                file_part = relative.split("#", 1)[0]
                self.assertTrue((REPOSITORY_ROOT / file_part).is_file())

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
            "Treat an unverified repository identity as\n"
            "  unknown rather than “not a repository,”",
            skill,
        )
        self.assertIn(
            "treat `worktree_state: unverified`\n  as unknown, never clean.", skill
        )
        self.assertRegex(
            skill,
            r"Do not run a\s+content-comparing Git command merely to fill this gap "
            r"during a static audit\.",
        )

    def test_non_audit_no_change_outcomes_still_use_verification(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "This section governs non-audit coordination runs, including deliberate\n"
            "no-change outcomes.",
            skill,
        )

    def test_long_lived_harness_contract_is_consistent(self) -> None:
        workflow = (
            "Specify -> Explore -> Plan <-> Human Plan Review -> Execute <-> "
            "Fast Verification -> Targeted Browser Verification -> MR/PR <-> "
            "AI Review + Full CI -> Human Validate -> Merge -> Post-Merge "
            "Knowledge Audit -> Improve Harness"
        )
        surfaces = [
            REPOSITORY_ROOT / "SKILL.md",
            REPOSITORY_ROOT / "DESIGN.md",
            REPOSITORY_ROOT / "README.md",
            REPOSITORY_ROOT / "README.zh-CN.md",
            REPOSITORY_ROOT / "references" / "delivery-workflow.md",
        ]

        for path in surfaces:
            with self.subTest(path=path.name):
                self.assertIn(workflow, path.read_text(encoding="utf-8"))

    def test_skill_leaves_a_repository_owned_learning_loop(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")
        delivery = (
            REPOSITORY_ROOT / "references" / "delivery-workflow.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Agentize should leave behind the system, not become\nthe system.", skill
        )
        for knowledge_state in ("`Observed`", "`Inferred`", "`Unknown`"):
            self.assertIn(knowledge_state, skill)
            self.assertIn(knowledge_state, delivery)
        self.assertIn("separate knowledge MR/PR", delivery)
        self.assertRegex(delivery, r"must not commit\s+directly to the default branch")
        self.assertRegex(
            skill, r"must not\s+call, require, or remain coupled to Agentize"
        )

    def test_browser_and_review_evidence_remain_distinct(self) -> None:
        delivery = (
            REPOSITORY_ROOT / "references" / "delivery-workflow.md"
        ).read_text(encoding="utf-8")

        self.assertIn(
            "Browser verification is not E2E", delivery
        )
        self.assertRegex(delivery, r"The\s+implementing Agent's self-review")
        self.assertRegex(delivery, r"is not\s+independent")
        self.assertIn("AI review remains machine evidence", delivery)

    def test_capability_readiness_and_task_outcomes_are_distinct(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")
        assessment = (
            REPOSITORY_ROOT / "references" / "assessment.md"
        ).read_text(encoding="utf-8")
        artifacts = (
            REPOSITORY_ROOT / "references" / "artifacts.md"
        ).read_text(encoding="utf-8")

        for status in (
            "`READY`",
            "`PARTIAL`",
            "`SETUP REQUIRED`",
            "`NOT AVAILABLE`",
            "`UNVERIFIED`",
            "`NOT APPLICABLE`",
        ):
            self.assertIn(status, skill)
            self.assertIn(status, assessment)
        for outcome in ("`PASSED`", "`FAILED`", "`NOT EXECUTED`"):
            self.assertIn(outcome, skill)
            self.assertIn(outcome, assessment)
        self.assertIn("Harness Capability Report", artifacts)
        self.assertIn("Setup guides and human-owned TODOs", artifacts)
        self.assertIn("Capability status is not a task result", assessment)

    def test_learning_is_continuous_with_post_merge_as_fallback(self) -> None:
        skill = (REPOSITORY_ROOT / "SKILL.md").read_text(encoding="utf-8")
        delivery = (
            REPOSITORY_ROOT / "references" / "delivery-workflow.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Continuous Knowledge Capture", skill)
        self.assertIn("Knowledge capture runs throughout the task", delivery)
        self.assertIn("same feature branch or MR/PR", delivery)
        self.assertIn("post-merge audit is a fallback", delivery)
        self.assertIn('An instruction saying "audit after merge" cannot trigger', delivery)

    def test_fast_verification_does_not_claim_full_e2e(self) -> None:
        delivery = (
            REPOSITORY_ROOT / "references" / "delivery-workflow.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Do not put the full E2E suite in every edit loop", delivery)
        self.assertIn("Full E2E is regression evidence", delivery)
        self.assertIn("Framework or tool presence alone is not `READY`", delivery)

    def test_high_integrity_evidence_contracts_are_explicit(self) -> None:
        delivery = (
            REPOSITORY_ROOT / "references" / "delivery-workflow.md"
        ).read_text(encoding="utf-8")
        behavior = (REPOSITORY_ROOT / "tests" / "behavior-cases.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("### Browser evidence chain", delivery)
        self.assertIn("tested commit or other trusted change identity", delivery)
        self.assertIn("A fixed delay may pace an interaction but is not proof", delivery)
        self.assertIn("### Required-gate accounting", delivery)
        self.assertRegex(
            delivery,
            r"failed, timed-out, cancelled, or unexpectedly\nskipped required job",
        )
        self.assertIn(
            "### Adoption evidence for feedback-derived knowledge", delivery
        )
        self.assertIn("is a candidate signal, not proof", delivery)
        self.assertIn("## Required-gate accounting prevents false green", behavior)
        self.assertIn(
            "screenshot without provenance cannot establish success", behavior
        )
        self.assertIn(
            "resolved state, same-file edit, and merge do not prove adoption",
            behavior,
        )


if __name__ == "__main__":
    unittest.main()
