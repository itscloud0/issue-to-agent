from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from issue_to_agent.cli import main
from issue_to_agent.issue import parse_github_issue_ref, parse_issue_text
from issue_to_agent.pack import build_task_pack
from issue_to_agent.render import render_html, render_json, render_markdown
from issue_to_agent.repo import scan_repository


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_REPO = ROOT / "examples" / "mini-repo"
EXAMPLE_ISSUE = ROOT / "examples" / "issue-checkout-timeout.md"


class IssueToAgentTests(unittest.TestCase):
    def test_parse_issue_text_uses_heading_as_title(self):
        issue = parse_issue_text("# Payment bug\n\nBody here", source="test")

        self.assertEqual(issue.title, "Payment bug")
        self.assertEqual(issue.body, "Body here")

    def test_parse_github_issue_refs(self):
        self.assertEqual(
            parse_github_issue_ref("https://github.com/owner/repo/issues/123"),
            ("owner", "repo", "123"),
        )
        self.assertEqual(parse_github_issue_ref("owner/repo#45"), ("owner", "repo", "45"))

    def test_build_task_pack_ranks_checkout_files(self):
        issue = parse_issue_text(EXAMPLE_ISSUE.read_text(encoding="utf-8"), source="fixture")

        pack = build_task_pack(issue, EXAMPLE_REPO, max_files=4)

        paths = [hit.path for hit in pack.relevant_files]
        self.assertIn("src/shop/checkout.py", paths)
        self.assertIn("tests/test_checkout.py", paths)
        self.assertIn("python -m pip install .", pack.repository.commands)
        self.assertIn("python -m unittest discover -s tests", pack.repository.commands)
        self.assertTrue(pack.repository.instructions)
        self.assertIn("timeout", pack.prompt.lower())

    def test_build_task_pack_ignores_generic_issue_prose_for_typescript_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "source" / "types").mkdir(parents=True)
            (repo / "test").mkdir()
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "ava", "build": "tsc"}}),
                encoding="utf-8",
            )
            (repo / "readme.md").write_text(
                "\n".join(["hello got property way response"] * 10),
                encoding="utf-8",
            )
            (repo / "source" / "types" / "hooks.ts").write_text(
                "export type BeforeErrorState = { error: Error };\n"
                "export type BeforeErrorHook = (state: BeforeErrorState) => Error;\n",
                encoding="utf-8",
            )
            (repo / "source" / "errors.ts").write_text(
                "export class HTTPError extends Error { response?: Response }\n",
                encoding="utf-8",
            )
            (repo / "test" / "hooks.ts").write_text(
                "test('hello response', () => {});\n",
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# BeforeErrorHook: Property 'response' does not exist on type 'Error'\n\n"
                "Hello everyone, I got a TypeScript error when trying to use "
                "`beforeErrorState.error.response`. The property exists at runtime, "
                "but it is typed the wrong way.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=4)

            paths = [hit.path for hit in pack.relevant_files]
            self.assertEqual(paths[0], "source/types/hooks.ts")
            self.assertIn("npm run test", pack.repository.commands)
            self.assertIn("npm run build", pack.repository.commands)

    def test_detects_go_and_rust_verification_commands(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "go.mod").write_text(
                "module example.com/agentdemo\n\ngo 1.22\n",
                encoding="utf-8",
            )
            (repo / "main.go").write_text(
                "package main\n\nfunc main() {}\n",
                encoding="utf-8",
            )
            (repo / "Cargo.toml").write_text(
                "[package]\nname = \"agentdemo\"\nversion = \"0.1.0\"\nedition = \"2021\"\n",
                encoding="utf-8",
            )
            (repo / "src").mkdir()
            (repo / "src" / "lib.rs").write_text(
                "pub fn answer() -> u8 { 42 }\n",
                encoding="utf-8",
            )

            profile = scan_repository(repo)

            self.assertIn("go test ./...", profile.commands)
            self.assertIn("cargo test", profile.commands)
            self.assertIn("cargo build", profile.commands)

    def test_renderers_include_prompt_and_structured_data(self):
        issue = parse_issue_text(EXAMPLE_ISSUE.read_text(encoding="utf-8"), source="fixture")
        pack = build_task_pack(issue, EXAMPLE_REPO, max_files=3)

        markdown = render_markdown(pack)
        payload = json.loads(render_json(pack))
        html = render_html(pack)

        self.assertIn("Ready-To-Paste Agent Prompt", markdown)
        self.assertEqual(payload["issue"]["title"], issue.title)
        self.assertIn("<!doctype html>", html)
        for section in (
            "Issue summary",
            "Likely files",
            "Commands",
            "Acceptance criteria",
            "Risk areas",
            "Agent-ready prompt",
        ):
            self.assertIn(section, html)

    def test_cli_writes_json_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "pack.json"

            exit_code = main(
                [
                    str(EXAMPLE_ISSUE),
                    "--repo",
                    str(EXAMPLE_REPO),
                    "--format",
                    "json",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["issue"]["title"], "Checkout retry fails after payment timeout")

    def test_cli_rejects_bad_max_files(self):
        stderr = StringIO()
        with redirect_stderr(stderr), self.assertRaises(SystemExit):
            main([str(EXAMPLE_ISSUE), "--repo", str(EXAMPLE_REPO), "--max-files", "0"])
        self.assertIn("--max-files must be at least 1", stderr.getvalue())

    def test_agent_skill_files_have_valid_metadata(self):
        skill_paths = [
            ROOT / ".agents" / "skills" / "issue-to-agent" / "SKILL.md",
            ROOT / ".claude" / "skills" / "issue-to-agent" / "SKILL.md",
            ROOT / ".github" / "skills" / "issue-to-agent" / "SKILL.md",
        ]

        for path in skill_paths:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"), path)
            self.assertIn("name: issue-to-agent", text)
            self.assertIn("description:", text)

        self.assertIn(
            "Workflow",
            (ROOT / ".agents" / "skills" / "issue-to-agent" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        self.assertIn(
            "/issue-to-agent",
            (ROOT / ".claude" / "skills" / "issue-to-agent" / "SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        github_skill = (
            ROOT / ".github" / "skills" / "issue-to-agent" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Task Trigger", github_skill)
        self.assertIn("Boundaries", github_skill)

    def test_github_action_and_issue_workflow_are_wired(self):
        action = (ROOT / "action.yml").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "issue-agent-task.yml").read_text(
            encoding="utf-8"
        )

        self.assertIn("using: composite", action)
        self.assertIn("issue-title:", action)
        self.assertIn("Generate task pack", action)
        self.assertIn("issues:", workflow)
        self.assertIn("agent-ready", workflow)
        self.assertIn("actions/upload-artifact@v5", workflow)
        self.assertIn("gh issue comment", workflow)

    def test_docs_link_agent_skill_and_demo_surfaces(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(
            "Turn a GitHub issue into a ready-to-run task pack for Codex, Claude Code, Cursor, or Copilot agents.",
            readme,
        )
        self.assertIn("AGENT_SKILLS.md", readme)
        self.assertIn("demo/issue-checkout-timeout.html", readme)
        self.assertIn("demo/real-ky-863.html", readme)
        self.assertIn("agent-ready", readme)


if __name__ == "__main__":
    unittest.main()
