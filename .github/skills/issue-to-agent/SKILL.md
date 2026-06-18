---
name: issue-to-agent
description: Generate a ready-to-run implementation task pack from a GitHub issue and repository context for Copilot agents.
license: MIT
---

# issue-to-agent

## Task Trigger

Use this skill when a user asks GitHub Copilot, VS Code agent mode, Copilot CLI, or Copilot cloud agent to:

- prepare a GitHub issue for a coding agent
- convert an issue into an implementation task
- identify likely files and commands for an issue
- create a task pack before assigning an `agent-ready` issue

## What This Skill Does

It turns issue text plus the local repository into a scoped task pack containing:

- issue summary
- likely files
- verification commands
- acceptance criteria
- risk areas
- agent-ready prompt

## Usage

From a local checkout:

```bash
python -m pip install .
issue-to-agent OWNER/REPO#123 --repo . --output ISSUE_AGENT_TASK.md
```

For a screenshot-ready report:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format html --output issue-agent-task.html
```

For automation:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format json --output ISSUE_AGENT_TASK.json
```

## Agent Instructions

1. Prefer generating the task pack before editing code.
2. Read the generated pack and verify that the ranked files are plausible.
3. If the ranked files look wrong, search the repository manually and mention the uncertainty.
4. Use the suggested commands as verification guidance, not proof that the task is solved.
5. Keep any follow-up implementation diff scoped to the acceptance criteria.

## Boundaries

- This skill does not call an LLM or hosted service.
- This skill does not execute the implementation.
- This skill does not publish, push, or comment on GitHub unless a workflow explicitly does so.
- Treat auth, billing, secret handling, migrations, and destructive operations as human-review-required.
