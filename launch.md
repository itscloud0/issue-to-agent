# Launch Plan: issue-to-agent

## Positioning

`issue-to-agent` is not just a CLI. It is an agent-native handoff system:

- local CLI
- Codex Agent Skill
- Claude Code Skill
- GitHub Copilot / VS Code Agent Skill
- GitHub Action for `agent-ready` issues
- Markdown, JSON, and HTML reports

## GitHub Repo Name

`issue-to-agent`

## GitHub Description

Turn GitHub issues into ready-to-run task packs for Codex, Claude Code, Cursor, and Copilot agents.

## GitHub Topics

- coding-agents
- agent-skills
- ai-engineering
- github-issues
- github-actions
- developer-tools
- repo-analysis
- codex
- claude-code
- copilot

## README Hero Tagline

Turn a GitHub issue into a ready-to-run task pack for Codex, Claude Code, Cursor, or Copilot agents.

## X/Twitter Post

I built `issue-to-agent`: an agent-native handoff tool for maintainers.

It turns a GitHub issue + local repo into a ready-to-run task pack for Codex, Claude Code, Cursor, or Copilot agents.

Ships as:
- CLI
- Codex skill
- Claude Code `/issue-to-agent` skill
- Copilot / VS Code skill
- GitHub Action for `agent-ready` issues
- HTML report

No LLM key. No paid API. Just better inputs before an agent edits code.

## LinkedIn Post

Maintainers still do a lot of manual work before assigning a GitHub issue to a coding agent: find likely files, copy repo instructions, remember test commands, define acceptance criteria, and warn about risky areas.

I built `issue-to-agent` to make that handoff repeatable.

It turns a GitHub issue and a local checkout into a ready-to-run task pack for Codex, Claude Code, Cursor, or GitHub Copilot agents. It ships as a CLI, three Agent Skills, a GitHub Action for `agent-ready` issues, and a screenshot-ready HTML report.

The tool does not call an LLM. It prepares better context for the agent you already use.

## Hacker News Title

Show HN: issue-to-agent - Agent Skills + CLI for turning GitHub issues into task packs

## Reddit Post

Title: I built an Agent Skills + CLI workflow for turning GitHub issues into coding-agent task packs

Body:

I use coding agents a lot, but assigning a GitHub issue still starts with manual context gathering: likely files, repo instructions, commands, acceptance criteria, and risk notes.

`issue-to-agent` turns an issue plus a local checkout into a ready-to-run task pack for Codex, Claude Code, Cursor, or Copilot agents.

It ships as a local CLI, Codex skill, Claude Code skill, Copilot / VS Code skill, GitHub Action for `agent-ready` issues, and static HTML report. It does not call an LLM or require paid APIs.

I included real smokes against `pallets/click#3571` and `sindresorhus/ky#863`; feedback on ranking heuristics and skill formats would be useful.

## Demo Captions

1. Label an issue `agent-ready`; get an `ISSUE_AGENT_TASK.md` artifact.
2. Invoke `/issue-to-agent OWNER/REPO#123` in Claude Code.
3. Use `$issue-to-agent` in Codex before implementation.
4. Review likely files and commands in a static HTML report.
5. Run the CLI locally without any LLM key.

## Good First Issues

1. Add a Go or Rust real-repo smoke fixture with generated HTML output.
2. Detect test commands from `tox.ini`, `noxfile.py`, and `uv` projects.
3. Add `--print-prompt-only` for clipboard workflows.

## Roadmap Issues

1. Add config file support for ignored paths, command preferences, and ranking boosts.
2. Add optional `git diff` context for issues with a work-in-progress branch.
3. Add more skill examples for Cursor and Copilot CLI workflows.

## Suggested First Release Title

`issue-to-agent v0.1.0`

## Maintainer Note

Keep this project focused on preparing high-quality issue handoffs. It should not become an autonomous agent, hosted service, or broad repo-packaging clone.
