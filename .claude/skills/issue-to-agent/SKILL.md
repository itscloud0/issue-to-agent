---
name: issue-to-agent
description: Use /issue-to-agent to turn a GitHub issue and local checkout into a scoped task pack for Claude Code or another coding agent.
---

# /issue-to-agent

Invoke this skill directly with `/issue-to-agent` when you want Claude Code to prepare an implementation handoff from an issue before editing code.

## Usage

```text
/issue-to-agent ISSUE_SOURCE [--repo PATH]
```

Examples:

```text
/issue-to-agent https://github.com/OWNER/REPO/issues/123 --repo .
/issue-to-agent OWNER/REPO#123 --repo .
/issue-to-agent examples/issue-checkout-timeout.md --repo examples/mini-repo
```

## Procedure

1. Resolve the issue source and repository path.
2. Prefer the CLI if available:

   ```bash
   issue-to-agent ISSUE_SOURCE --repo REPO_PATH --output ISSUE_AGENT_TASK.md
   ```

3. If the CLI is not installed but this repository is checked out, install it locally:

   ```bash
   python -m pip install .
   ```

4. Generate HTML when the user asks for a report or screenshot-ready demo:

   ```bash
   issue-to-agent ISSUE_SOURCE --repo REPO_PATH --format html --output issue-agent-task.html
   ```

5. Read the generated Markdown before answering. Use it to produce a concise implementation task pack for the user.

## Output Contract

Return:

- generated file path
- likely files and why they matter
- commands to run
- acceptance criteria
- risks and boundaries
- whether the task is ready for an implementation agent

## Boundaries

- Do not start implementation unless the user explicitly asks.
- Do not create GitHub comments or labels from this skill.
- Do not use paid APIs, LLM keys, or hosted services.
- Escalate auth, billing, migration, destructive, or security-sensitive issues for human review.
