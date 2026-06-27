# issue-to-agent

Turn a GitHub issue into a ready-to-run task pack for Codex, Claude Code, Cursor, or Copilot agents.

Maintainers waste time translating issues into agent-ready prompts: find the likely files, remember test commands, copy repo instructions, define acceptance criteria, and warn the agent about risky areas. `issue-to-agent` makes that handoff repeatable.

It ships as:

- local CLI
- Codex Agent Skill
- Claude Code Skill with `/issue-to-agent`
- GitHub Copilot / VS Code Agent Skill
- GitHub Action for `agent-ready` issues
- Markdown, JSON, and screenshot-ready HTML reports

## 30-Second Quickstart

```bash
python -m pip install .
issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --output ISSUE_AGENT_TASK.md
```

Open the generated task pack and paste the agent-ready prompt into Codex, Claude Code, Cursor, or Copilot.

```text
Likely relevant files:
- tests/test_checkout.py
- src/shop/checkout.py

Suggested commands:
- python -m pip install .
- python -m unittest discover -s tests
```

## HTML Demo

Generated demo reports:

- `demo/issue-checkout-timeout.html`
- `demo/real-click-3571.html`
- `demo/real-ky-863.html`
- `demo/real-ripgrep-3419.html`

Create a fresh HTML report:

```bash
issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --format html \
  --output demo/issue-checkout-timeout.html
```

## Real-Repo Smoke

This repo includes real smoke tests against `pallets/click#3571`, `sindresorhus/ky#863`, and `BurntSushi/ripgrep#3419`:

- record: `examples/real-repo-smoke.md`
- generated Markdown: `examples/real-click-3571-task.md`
- generated Markdown: `examples/real-ky-863-task.md`
- generated Markdown: `examples/real-ripgrep-3419-task.md`
- generated HTML: `demo/real-click-3571.html`
- generated HTML: `demo/real-ky-863.html`
- generated HTML: `demo/real-ripgrep-3419.html`

The Click smoke found plausible files first: `src/click/termui.py`, `src/click/_termui_impl.py`, and `tests/test_termui.py`. The ky smoke found `source/types/hooks.ts` first for a TypeScript hook typing issue.
The ripgrep smoke found `crates/ignore/src/walk.rs` first for a Rust parallel-walk nondeterminism bug.

## Evidence

- `BENCHMARK.md` compares file ranking against a filename/path keyword baseline on 15 closed issues from Click, ky, and ripgrep.
- `EVALUATION_PLAN.md` documents the metrics, baseline, known weaknesses, and stop criteria.
- `DEMAND_EVIDENCE.md` documents current demand signals and marks demand as `UNKNOWN` until independent usage is proven.

## Installation

From a checkout:

```bash
python -m pip install .
```

After publication:

```bash
python -m pip install git+https://github.com/itscloud0/issue-to-agent.git
```

## CLI Usage

Local issue file:

```bash
issue-to-agent examples/issue-checkout-timeout.md --repo .
```

GitHub issue through `gh`:

```bash
issue-to-agent https://github.com/OWNER/REPO/issues/123 --repo .
issue-to-agent OWNER/REPO#123 --repo .
```

Pasted issue text:

```bash
pbpaste | issue-to-agent - --repo .
```

JSON for automation:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format json --output ISSUE_AGENT_TASK.json
```

Include tracked work-in-progress changes:

```bash
issue-to-agent OWNER/REPO#123 --repo . --include-diff --output ISSUE_AGENT_TASK.md
```

Use repo-specific config:

```bash
issue-to-agent OWNER/REPO#123 --repo . --config .issue-to-agent.json
```

HTML for maintainers:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format html --output issue-agent-task.html
```

Prompt-only output for direct agent handoff:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format prompt --output agent-prompt.txt
```

## Agent Skills

See `AGENT_SKILLS.md`.

Repo-local skill files are included:

```text
.agents/skills/issue-to-agent/SKILL.md
.claude/skills/issue-to-agent/SKILL.md
.github/skills/issue-to-agent/SKILL.md
```

Codex:

```text
$issue-to-agent turn OWNER/REPO#123 into an agent task pack
```

Claude Code:

```text
/issue-to-agent OWNER/REPO#123 --repo .
```

GitHub Copilot / VS Code:

```text
Use issue-to-agent to prepare OWNER/REPO#123 for an implementation agent.
```

## GitHub Action

The workflow in `.github/workflows/issue-agent-task.yml` runs when an issue is labeled:

```text
agent-ready
```

It checks out the repo, generates `ISSUE_AGENT_TASK.md`, uploads it as an artifact, and comments on the issue with the generated task pack. It does not require paid APIs or LLM keys.

You can also reuse the composite action directly:

```yaml
- uses: ./
  with:
    issue-title: ${{ github.event.issue.title }}
    issue-body: ${{ github.event.issue.body }}
    issue-url: ${{ github.event.issue.html_url }}
    issue-number: ${{ github.event.issue.number }}
    config-path: .issue-to-agent.json
    output-path: ISSUE_AGENT_TASK.md
```

## Project Config

Config is optional. With no config file, `issue-to-agent` keeps its built-in defaults.

The CLI auto-discovers `.issue-to-agent.json` or `issue-to-agent.json` in `--repo`. Use `--config` or the composite action `config-path` input to pass a specific file.

```json
{
  "ignored_paths": ["docs/**", "generated/**"],
  "command_preferences": ["uv run pytest", "make test"],
  "ranking_boosts": {
    "src/**": 12,
    "tests/**": 8
  }
}
```

- `ignored_paths` excludes matching files from relevance ranking.
- `command_preferences` puts exact commands first in the suggested command list.
- `ranking_boosts` adds a non-negative integer score to already-matched files whose path matches a glob.

## What It Detects

- `AGENTS.md`, `CLAUDE.md`, `.github/copilot-instructions.md`, and `.cursor/rules`
- Python install/test commands from `pyproject.toml` and `tests/`
- Node scripts from `package.json`
- Go verification commands from `go.mod`
- Rust verification commands from `Cargo.toml`
- Make and Just targets
- likely source, test, docs, config, and workflow files
- checklist items in the issue body as acceptance criteria
- sensitive keywords such as auth, billing, payment, migration, secret, and token
- optional tracked git diff context when `--include-diff` is passed
- optional project config for ignored paths, command preferences, and ranking boosts

## When To Use It

- triaging GitHub issues for coding agents
- preparing a focused handoff for a teammate
- converting bug reports into repeatable repair prompts
- generating artifacts for issues labeled `agent-ready`

## When Not To Use It

- you need full semantic code search
- the issue is too vague for implementation
- the change is security-sensitive, billing-sensitive, or migration-heavy and needs human planning first
- you expect the tool to execute the implementation

## Comparison

- Repomix and Gitingest package broad repository context for LLMs. `issue-to-agent` creates a narrow issue-specific task pack.
- Aider, Codex, Claude Code, Cursor, and Copilot can edit code. `issue-to-agent` prepares the handoff before the agent edits.
- Manual prompts are flexible. This tool makes the context gathering consistent.

## Limitations

- Ranking is lexical, not semantic.
- GitHub issue loading requires the `gh` CLI and whatever auth the target repo requires.
- The GitHub Action comments on issues only when the `agent-ready` label is applied.
- The tool does not execute tests or change source files.

## Roadmap

- Add more real-repo fixtures for Go.
- Add more package-manager and monorepo workflow examples.

## Contributing

See `CONTRIBUTING.md`. Good first issues are listed in `launch.md`.

## License

MIT. See `LICENSE`.
