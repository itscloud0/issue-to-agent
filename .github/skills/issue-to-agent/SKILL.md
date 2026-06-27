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

From a local issue file:

```bash
issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --output ISSUE_AGENT_TASK.md
```

For a screenshot-ready report:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format html --output issue-agent-task.html
```

For automation:

```bash
issue-to-agent OWNER/REPO#123 --repo . --format json --output ISSUE_AGENT_TASK.json
```

## Cursor Workflow

When Cursor is the implementation agent:

1. Generate `ISSUE_AGENT_TASK.md` before editing.
2. Read the task pack and confirm the likely files match the issue.
3. If the user asks for a reviewable artifact, generate HTML:

   ```bash
   issue-to-agent OWNER/REPO#123 \
     --repo . \
     --format html \
     --output issue-agent-task.html
   ```

4. If another tool will consume the output, generate JSON and parse-check it:

   ```bash
   issue-to-agent OWNER/REPO#123 \
     --repo . \
     --format json \
     --output ISSUE_AGENT_TASK.json
   python -m json.tool ISSUE_AGENT_TASK.json >/dev/null
   ```

5. Implement only the acceptance criteria after the task pack looks plausible.

Useful Cursor prompt:

```text
Read ISSUE_AGENT_TASK.md. Use it as implementation guidance, but verify file
ranking with repository search before editing.
```

## Copilot Workflow

When GitHub Copilot, VS Code agent mode, Copilot CLI, or Copilot cloud agent is
the handoff target, ask it for one of these concrete outputs:

```text
Use issue-to-agent with OWNER/REPO#123 and repo . Write ISSUE_AGENT_TASK.md.
```

```text
Use issue-to-agent with examples/issue-checkout-timeout.md and repo examples/mini-repo.
Write ISSUE_AGENT_TASK.md, then summarize likely files, commands, risks, and acceptance criteria.
```

```text
Use issue-to-agent with OWNER/REPO#123 and repo . Generate issue-agent-task.html
for maintainer review.
```

```text
Use issue-to-agent with OWNER/REPO#123 and repo . Generate ISSUE_AGENT_TASK.json
for automation and verify that the JSON parses.
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
