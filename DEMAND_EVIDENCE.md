# Demand Evidence

Current status: `UNKNOWN`.

This project has category evidence and early public interest, but it does not yet have enough independent usage evidence to claim repeated demand. Treat this file as the demand ledger, not as launch copy.

## Target User

Open-source maintainers and AI software engineers who already use coding agents and need a repeatable way to prepare GitHub issues for implementation.

## Painful Workflow

Before assigning an issue to a coding agent, a maintainer usually has to:

- read the issue
- search the repository for likely files
- find repo instructions
- remember install, test, and build commands
- define acceptance criteria
- paste a structured prompt into the agent

`issue-to-agent` targets that handoff step. It does not replace the coding agent.

## Current Evidence

| Signal | Source | Evidence | Status |
| --- | --- | --- | --- |
| Adjacent repo-context demand | https://github.com/yamadashy/repomix | `repomix` had strong public adoption at discovery time, showing demand for repo-to-LLM context packaging. | Category evidence only |
| Adjacent repo-context demand | https://github.com/coderamp-labs/gitingest | `gitingest` had strong public adoption at discovery time, showing demand for fast repository context extraction. | Category evidence only |
| Coding-agent workflow demand | https://github.com/openai/codex | Coding-agent repos had strong public adoption at discovery time. | Category evidence only |
| Coding-agent workflow demand | https://github.com/Aider-AI/aider | Agentic coding CLI adoption supports the target workflow area. | Category evidence only |
| Issue-to-agent contribution signal | https://github.com/itscloud0/issue-to-agent/pull/7 | External contributor added prompt-only output; merged after maintainer cleanup and passing CI. | Early project signal |
| Issue-to-agent contribution signal | https://github.com/itscloud0/issue-to-agent/pull/8 | External contributor attempted a Rust smoke fixture; closed as superseded because artifacts were incomplete. | Early project signal |
| Post-launch traffic | GitHub traffic API for `itscloud0/issue-to-agent` | 62 views / 3 unique viewers and 69 clones / 37 unique cloners as of 2026-06-19 12:04 MSK. | Awareness only |
| Same-shape competition check | https://github.com/tomasmach/pr-context-pack | Low public activity in a similar named area at discovery time suggested no dominant same-shape project. | Gap hint only |

## Clear Gap

Broad repo packers help users send code context to an LLM. Coding agents can edit code once they have enough context. The gap is the issue-specific handoff in between:

- likely files ranked for one issue
- repo instructions
- project commands
- acceptance criteria
- risk notes
- ready-to-paste agent prompt

## Why Not Upstream First

This is a workflow that spans repo scanning, issue parsing, CLI usage, Agent Skills, and an optional GitHub Action. Existing repo packers and coding agents own adjacent parts of the workflow, but not the full handoff artifact. That makes a small standalone tool reasonable to validate.

## What Is Not Proven Yet

- Repeated independent user demand is not proven.
- Traffic and clones do not prove successful usage.
- The project has one merged external PR, but no confirmed external production workflow.
- Demand should remain `UNKNOWN` until external issues, usage reports, package installs, repeated stars/forks, or independent mentions show real adoption.

## Next Evidence To Collect

- 72-hour, 7-day, and 14-day GitHub traffic/adoption reviews.
- External issues or discussions showing onboarding failures or requested workflows.
- Package/download data if a package is published.
- More real issue-to-agent use cases from unrelated repositories.
