---
name: issue-to-agent
description: Turn a GitHub issue plus the current local repository into a scoped implementation task pack for Codex.
---

# issue-to-agent

Use this skill when the user asks Codex to prepare an implementation plan, task pack, or agent handoff from a GitHub issue, issue URL, `OWNER/REPO#123`, pasted issue text, or local issue file.

## Goal

Create a compact, actionable task pack that a coding agent can execute without rediscovering basic context.

## Required Inputs

- Issue source: local issue file, pasted issue text, stdin, GitHub issue URL, or `OWNER/REPO#123`.
- Local repository path. Default to the current working directory if the user does not specify one.

## Workflow

1. Confirm you are in the intended repository or ask for the repo path only if it cannot be inferred.
2. If the CLI is installed, run:

   ```bash
   issue-to-agent ISSUE_SOURCE --repo REPO_PATH --output ISSUE_AGENT_TASK.md
   ```

3. If the user needs automation output, also run:

   ```bash
   issue-to-agent ISSUE_SOURCE --repo REPO_PATH --format json --output ISSUE_AGENT_TASK.json
   ```

4. If the user needs a maintainer-readable report, run:

   ```bash
   issue-to-agent ISSUE_SOURCE --repo REPO_PATH --format html --output issue-agent-task.html
   ```

5. Read the generated task pack before presenting it. Check that likely files, commands, acceptance criteria, and risks make sense.
6. If file ranking looks weak, use repo search to inspect likely terms and call out the weakness. Do not pretend the packet is authoritative.
7. Return the generated pack path and summarize:
   - issue summary
   - likely files
   - suggested commands
   - acceptance criteria
   - risk areas
   - remaining open questions

## Boundaries

- Do not implement the issue unless the user explicitly asks.
- Do not publish, push, or comment on GitHub unless asked.
- Do not call an LLM or external service. `issue-to-agent` is local-first; GitHub issue loading only uses the local `gh` CLI.
- Treat security, auth, billing, and migration issues as high-risk and recommend human review before agent execution.

## Good Output Shape

```text
Created ISSUE_AGENT_TASK.md.

Likely files:
- src/...
- tests/...

Run:
- ...

Risk:
- ...
```
