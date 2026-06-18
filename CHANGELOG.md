# Changelog

## Unreleased

- Add `--format prompt` for writing only the ready-to-paste agent prompt.
- Improve Rust/source-path ranking using identifier, extension, and title-term signals.
- Improve code-reference and source/test companion ranking for issue-localization.
- Add a reproducible benchmark over 15 closed issues from Click, ky, and ripgrep.

## v0.1.0 - 2026-06-17

- Initial local CLI.
- Load issues from files, stdin, GitHub issue URLs, or `owner/repo#123`.
- Scan local repos for agent instructions, likely commands, and relevant files.
- Render Markdown, JSON, and standalone HTML task packs.
- Include realistic mini repo and checkout timeout example.
- Add Codex, Claude Code, and GitHub Copilot / VS Code Agent Skill files.
- Add composite GitHub Action plus `agent-ready` issue-label workflow.
- Add screenshot-ready HTML demos under `demo/`.
- Add real-repo smoke output for `pallets/click#3571`.
- Add real-repo smoke output for `sindresorhus/ky#863`.
- Improve ranking for TypeScript/API issues by filtering generic issue prose and recognizing `source/` trees.
- Detect Go and Rust verification commands from `go.mod` and `Cargo.toml`.
