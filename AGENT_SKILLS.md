# Agent Skills

`issue-to-agent` ships as a CLI and as portable Agent Skills for Codex, Claude Code, and GitHub Copilot-compatible agents.

## What Agent Skills Are

Agent Skills are small folders that contain a `SKILL.md` file with metadata and task-specific instructions. Agents load the skill only when the task matches, so repeatable workflows can be reused without pasting the same prompt every time.

The skill format is intentionally simple:

```text
skills/
  issue-to-agent/
    SKILL.md
```

## Install In Codex

For repo-local use, keep this checked in:

```text
.agents/skills/issue-to-agent/SKILL.md
```

From Codex, invoke it by mentioning the skill or asking for an issue task pack:

```text
$issue-to-agent turn OWNER/REPO#123 into an agent task pack
```

Codex can also discover the skill automatically when the task matches the skill description.

## Install In Claude Code

For repo-local use, keep this checked in:

```text
.claude/skills/issue-to-agent/SKILL.md
```

Invoke it directly:

```text
/issue-to-agent OWNER/REPO#123 --repo .
```

Claude Code skills can be called by slash command using the skill name.

## Use From Cursor

Cursor can use the CLI directly from an agent chat or terminal. Generate the
pack first, inspect it, then decide whether the implementation is scoped enough
for an agent edit.

Local issue file:

```bash
issue-to-agent examples/issue-checkout-timeout.md \
  --repo examples/mini-repo \
  --output ISSUE_AGENT_TASK.md
```

GitHub issue reference:

```bash
issue-to-agent OWNER/REPO#123 --repo . --output ISSUE_AGENT_TASK.md
```

HTML report for review:

```bash
issue-to-agent OWNER/REPO#123 \
  --repo . \
  --format html \
  --output issue-agent-task.html
```

JSON output for a Cursor rule, script, or downstream automation:

```bash
issue-to-agent OWNER/REPO#123 \
  --repo . \
  --format json \
  --output ISSUE_AGENT_TASK.json
```

Suggested Cursor prompt after generation:

```text
Read ISSUE_AGENT_TASK.md. Check whether the likely files and commands are plausible.
If they are, implement only the acceptance criteria and verify with the suggested commands.
```

## Use From VS Code Or GitHub Copilot

For GitHub Copilot, VS Code agent mode, Copilot CLI, or Copilot cloud agent, keep this checked in:

```text
.github/skills/issue-to-agent/SKILL.md
```

In chat or agent mode, ask:

```text
Use issue-to-agent to prepare this issue for an implementation agent: OWNER/REPO#123
```

Local issue file:

```text
Use issue-to-agent with examples/issue-checkout-timeout.md and repo examples/mini-repo.
Write the Markdown task pack to ISSUE_AGENT_TASK.md.
```

GitHub issue reference:

```text
Use issue-to-agent to prepare OWNER/REPO#123 from this checkout.
Write ISSUE_AGENT_TASK.md, then summarize likely files, commands, risks, and acceptance criteria.
```

HTML output:

```text
Use issue-to-agent to prepare OWNER/REPO#123 from this checkout.
Generate an HTML report at issue-agent-task.html for maintainer review.
```

JSON output:

```text
Use issue-to-agent to prepare OWNER/REPO#123 from this checkout.
Generate ISSUE_AGENT_TASK.json for automation and check that it parses before continuing.
```

## CLI Vs Skill Vs GitHub Action

Use the CLI when:

- you are local in a repo
- you want Markdown, JSON, or HTML output
- you want full control over paths and output files

Use an Agent Skill when:

- you are already working inside Codex, Claude Code, Cursor, or Copilot
- you want the agent to generate and inspect the task pack before editing
- you want repeatable handoff behavior without re-pasting instructions

Use the GitHub Action when:

- maintainers label issues as `agent-ready`
- you want an `ISSUE_AGENT_TASK.md` artifact
- you want an automatic issue comment with a scoped agent prompt

## Boundaries

- No paid APIs are required.
- No LLM keys are required.
- GitHub issue input uses the local `gh` CLI or GitHub Actions event payload.
- Review generated packs before assigning sensitive issues to an agent.
