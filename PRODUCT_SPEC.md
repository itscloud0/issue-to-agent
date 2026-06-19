# PRODUCT_SPEC: issue-to-agent

## User Persona

Open-source maintainers and AI software engineers who want to hand a GitHub issue to Codex, Claude Code, Cursor, or another coding agent without manually gathering repo context first.

## Painful Problem

Issue triage for coding agents is still manual. A maintainer reads the issue, searches the repo, finds likely files, remembers test commands, copies project instructions, and writes a prompt. That takes time and the quality varies by maintainer.

## Current Bad Workflow

1. Open a GitHub issue.
2. Search the repo by keyword.
3. Guess relevant source and test files.
4. Open `AGENTS.md`, README, package metadata, and CI config.
5. Paste an improvised prompt into a coding agent.
6. Repair missing context after the agent starts in the wrong area.

## Proposed Better Workflow

Run one command, invoke an Agent Skill, or label an issue `agent-ready`. The tool produces a compact agent task pack with:

- issue summary
- relevant files ranked with reasons
- project instructions
- likely test/install commands
- acceptance criteria
- risks and open questions
- a ready-to-paste prompt
- optional HTML report for maintainers

## 20-Second Demo

```bash
issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --output ISSUE_AGENT_PACK.md

issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --format html \
  --output issue-agent-pack.html
```

Open the Markdown or HTML output and paste the task prompt into Codex, Claude Code, or Cursor.

Agent-native demo:

```text
/issue-to-agent OWNER/REPO#123 --repo .
$issue-to-agent turn OWNER/REPO#123 into an agent task pack
```

GitHub Action demo:

```text
label issue: agent-ready
download artifact: ISSUE_AGENT_TASK.md
```

## Core v0.1 Feature Set

- Load issue input from a local Markdown/text file, stdin, GitHub issue URL, or `owner/repo#123` via `gh`.
- Scan a local repo while ignoring build, cache, dependency, and VCS directories.
- Detect agent instructions from `AGENTS.md`, `CLAUDE.md`, and common editor instruction files.
- Detect common install, test, lint, and build commands from Python, Node, Make, Just, and GitHub Actions metadata.
- Rank likely relevant files using issue terms, path matches, content matches, and test/source heuristics.
- Render Markdown, JSON, or standalone HTML.
- Ship repo-local Agent Skills for Codex, Claude Code, and GitHub Copilot / VS Code.
- Ship a composite GitHub Action and an `agent-ready` issue-label workflow.
- Include generated demo HTML and a real-repo smoke record.
- Include useful failure messages when the repo, issue source, or GitHub CLI input is invalid.

## Non-Goals

- No autonomous code changes.
- No LLM calls.
- No hosted backend.
- No perfect semantic code search.
- No replacement for full repo packers like Repomix.
- No automatic GitHub comments outside the explicit `agent-ready` workflow.

## Alternatives

- Repomix and Gitingest package broad repo context but do not turn one issue into a scoped task pack.
- Aider, Codex, Claude Code, and SWE-agent can work on issues, but the maintainer still needs to provide the right local context or run a heavier agent workflow.
- Manual prompts are flexible but inconsistent and slow.

## Why This Is Valuable

The tool removes the repetitive context-gathering step before using a coding agent. It is local-first, deterministic, and useful even without API keys. It gives maintainers a repeatable handoff artifact for bug fixes, docs changes, and small feature requests.

## Why This Strengthens Ilia's Profile

It shows taste in AI SWE workflows: not another model wrapper, but practical tooling around the real bottleneck of agent effectiveness. It combines repo analysis, GitHub workflow awareness, Agent Skills distribution, GitHub Actions automation, CLI UX, and launch-ready docs.

## Publish Criteria

- README value is clear in 10 seconds.
- CLI quickstart works from a clean checkout.
- Markdown, JSON, and HTML renderers are tested.
- Realistic example repo and issue are included.
- CI passes.
- Skill metadata tests pass.
- GitHub Action sanity checks pass.
- Safety scan finds no secrets, env files, generated caches, or placeholder metadata.
- Demand evidence, product fit, validation, usability, engineering, and distribution gates are recorded as `PASS`, `FAIL`, or `UNKNOWN`.
- Any `PASS` gate cites concrete evidence instead of an internal score.
- Known failures and stop/reposition criteria are documented before stronger claims are made.
