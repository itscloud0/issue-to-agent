from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

from issue_to_agent.cli import main
from issue_to_agent.issue import parse_github_issue_ref, parse_issue_text
from issue_to_agent.pack import build_task_pack, extract_acceptance_criteria
from issue_to_agent.render import render_html, render_json, render_markdown, render_prompt
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

    def test_acceptance_criteria_ignores_template_confirmation_checkbox(self):
        issue = parse_issue_text(
            "# Repro bug\n\n"
            "### Please tick this box to confirm you have reviewed the above.\n\n"
            "- [x] I have a different issue.\n"
            "- [ ] Add a regression test for the repro.\n",
            source="fixture",
        )

        self.assertEqual(
            extract_acceptance_criteria(issue),
            ["Add a regression test for the repro."],
        )

    def test_acceptance_criteria_falls_back_when_only_template_confirmation_exists(self):
        issue = parse_issue_text(
            "# Parallel walk is nondeterministic\n\n"
            "- [x] I have a different issue.\n",
            source="fixture",
        )

        criteria = extract_acceptance_criteria(issue)

        self.assertIn(
            "Resolve the behavior described by: Parallel walk is nondeterministic.",
            criteria,
        )

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

    def test_ranks_file_type_registry_for_short_extension_request(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / ".github" / "ISSUE_TEMPLATE").mkdir(parents=True)
            (repo / "crates" / "core").mkdir(parents=True)
            (repo / "crates" / "ignore" / "src").mkdir(parents=True)
            (repo / "Cargo.toml").write_text(
                "[package]\nname = \"rgdemo\"\nversion = \"0.1.0\"\nedition = \"2021\"\n",
                encoding="utf-8",
            )
            (repo / ".github" / "ISSUE_TEMPLATE" / "feature_request.md").write_text(
                "describe feature request support want your issue\n" * 8,
                encoding="utf-8",
            )
            (repo / "crates" / "core" / "app.rs").write_text(
                "support exclude feature request alias want possibly\n" * 8,
                encoding="utf-8",
            )
            (repo / "crates" / "ignore" / "src" / "default_types.rs").write_text(
                "pub const DEFAULT_TYPES: &[(&[&str], &[&str])] = &[];\n"
                "// default file types shipped with ripgrep\n",
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# Add support for pofile (.po)?\n\n"
                "I want to exclude files matching `*.po`, which is a Gettext PO file type.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=5)

            paths = [hit.path for hit in pack.relevant_files]
            self.assertLess(
                paths.index("crates/ignore/src/default_types.rs"),
                paths.index("crates/core/app.rs"),
            )

    def test_preserves_identifier_terms_for_config_path_ranking(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "crates" / "core").mkdir(parents=True)
            (repo / "Cargo.toml").write_text(
                "[package]\nname = \"rgdemo\"\nversion = \"0.1.0\"\nedition = \"2021\"\n",
                encoding="utf-8",
            )
            (repo / "GUIDE.md").write_text(
                "warning message user shell config file problem path\n" * 12,
                encoding="utf-8",
            )
            (repo / "crates" / "core" / "config.rs").write_text(
                "fn config_path() { let _ = \"RIPGREP_CONFIG_PATH\"; }\n",
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# Improve error message when RIPGREP_CONFIG_PATH refers to a nonexistent file\n\n"
                "When `RIPGREP_CONFIG_PATH` points at a missing ripgreprc, explain that the config path is from the environment variable.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=3)

            self.assertEqual(pack.relevant_files[0].path, "crates/core/config.rs")

    def test_ranks_core_search_for_searched_decompression_issue(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "crates" / "cli" / "src").mkdir(parents=True)
            (repo / "crates" / "core").mkdir(parents=True)
            (repo / "Cargo.toml").write_text(
                "[package]\nname = \"rgdemo\"\nversion = \"0.1.0\"\nedition = \"2021\"\n",
                encoding="utf-8",
            )
            (repo / "crates" / "cli" / "src" / "decompress.rs").write_text(
                "gzip bzip2 xz lz4 brotli zstd executable decompress decompression\n" * 5,
                encoding="utf-8",
            )
            (repo / "crates" / "core" / "search.rs").write_text(
                "search worker controls when decompression preprocessors are used\n",
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# decompression binaries are searched for even when they will never be used\n\n"
                "Repeated `rg --passthru` runs check gzip and bzip2 executables before the search needs decompression.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=5)

            paths = [hit.path for hit in pack.relevant_files]
            self.assertIn("crates/core/search.rs", paths)

    def test_ranks_source_file_for_exact_code_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "src" / "click").mkdir(parents=True)
            (repo / "tests").mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname = \"clickdemo\"\n", encoding="utf-8")
            (repo / "src" / "click" / "formatting.py").write_text(
                "class HelpFormatter:\n"
                "    def write_usage(self, prog, args='', prefix='Usage: '):\n"
                "        return f'{prefix}{prog} {args}'\n",
                encoding="utf-8",
            )
            (repo / "tests" / "test_formatting.py").write_text(
                "def test_usage_line_for_empty_args():\n"
                "    assert 'Usage:'\n",
                encoding="utf-8",
            )
            (repo / "tests" / "test_options.py").write_text(
                "actual argument cli empty exception exit internal passed\n" * 5,
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# Empty output from `HelpFormatter.write_usage` for a program without arguments\n\n"
                "If no args are passed to HelpFormatter.write_usage, the Usage line is not printed.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=3)

            paths = [hit.path for hit in pack.relevant_files]
            self.assertIn("src/click/formatting.py", paths)
            self.assertIn("tests/test_formatting.py", paths)

    def test_ranks_test_companion_for_matched_source_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            repo = Path(tmpdir)
            (repo / "src" / "click").mkdir(parents=True)
            (repo / "tests").mkdir()
            (repo / "pyproject.toml").write_text("[project]\nname = \"clickdemo\"\n", encoding="utf-8")
            (repo / "src" / "click" / "types.py").write_text(
                "class FuncParamType:\n"
                "    def convert(self, value, param, ctx):\n"
                "        try:\n"
                "            return self.func(value)\n"
                "        except ValueError as e:\n"
                "            self.fail(str(e), param, ctx)\n",
                encoding="utf-8",
            )
            (repo / "tests" / "test_types.py").write_text(
                "def test_type_conversion_error_message():\n"
                "    assert 'message'\n",
                encoding="utf-8",
            )
            (repo / "tests" / "test_options.py").write_text(
                "callable cls convert dict fix give info input message test\n" * 5,
                encoding="utf-8",
            )
            issue = parse_issue_text(
                "# `FuncParamType` should use `ValueError` for `self.fail(message)`\n\n"
                "FuncParamType should pass str(error) instead of the input value.",
                source="fixture",
            )

            pack = build_task_pack(issue, repo, max_files=3)

            paths = [hit.path for hit in pack.relevant_files]
            self.assertIn("src/click/types.py", paths)
            self.assertIn("tests/test_types.py", paths)

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
        prompt_only = render_prompt(pack)
        self.assertIn("Ready-To-Paste Agent Prompt", markdown)
        self.assertEqual(payload["issue"]["title"], issue.title)
        self.assertIn("<!doctype html>", html)
        self.assertEqual(prompt_only, pack.prompt)
        self.assertNotIn("Ready-To-Paste Agent Prompt", prompt_only)
        self.assertIn("Issue:", prompt_only)
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
    def test_cli_writes_prompt_only_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "prompt.txt"

            exit_code = main(
                [
                    str(EXAMPLE_ISSUE),
                    "--repo",
                    str(EXAMPLE_REPO),
                    "--format",
                    "prompt",
                    "--output",
                    str(output),
                ]
            )

            self.assertEqual(exit_code, 0)
            content = output.read_text(encoding="utf-8")
            self.assertNotIn("Ready-To-Paste Agent Prompt", content)
            self.assertIn("Checkout retry fails after payment timeout", content)

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

    def test_benchmark_fixtures_cover_migration_scope(self):
        payload = json.loads(
            (ROOT / "benchmark" / "fixtures" / "issues.json").read_text(
                encoding="utf-8"
            )
        )
        fixtures = payload["fixtures"]

        self.assertGreaterEqual(len(fixtures), 15)
        self.assertGreaterEqual(len({fixture["repo"] for fixture in fixtures}), 3)
        self.assertGreaterEqual(len({fixture["language"] for fixture in fixtures}), 2)

        for fixture in fixtures:
            self.assertIn("github.com", fixture["issue_url"])
            self.assertIn("github.com", fixture["closing_pr_url"])
            self.assertTrue(fixture["pr_base_ref"])
            self.assertTrue(fixture["changed_files"])


if __name__ == "__main__":
    unittest.main()
